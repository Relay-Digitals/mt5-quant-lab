#!/usr/bin/env python3
"""idx_ara_guard.py — REAL-TIME bearish-ignition exit guard untuk portfolio ARA paper-trade.
Loop tiap POLL detik, jam market (02:00-08:40 UTC = 09:00-15:40 WIB), per posisi status==open:
  - harga & %chg live dari orderbook (responsif)
  - konfirmasi volume-ignition: vr = vol-hari-ini / avg20d (dari bar harian, unit konsisten)
  - deteksi ARB-lock (auto-reject-bawah): bid kosong / harga di batas bawah -> TIDAK fake exit, warn 'TERJEBAK'
Profil AGRESIF (override via /opt/idx-quant/ara_guard.env):
  FAST_SL=-0.04  IGN_DROP=-0.02  IGN_VR=2.0  TRAIL_PEAK=0.03  POLL=90
Exit ditulis balik ke ara_paper.json (status=closed, result=faststop/ignition/trail) -> report 18:30 ikut.
WA hemat: hanya saat exit/trap + 1 pesan 'armed' pagi. CT=UTC."""
import os, sys, json, time, datetime as dt, requests
import stockbit_history as sh
EX = sh.EXODUS
DIR = "/opt/idx-quant"; DATA = f"{DIR}/data"
STATE = f"{DATA}/ara_paper.json"          # portfolio (dibagi dgn idx_ara_paper.py)
GSTATE = f"{DATA}/ara_guard.json"         # state guard (peak/warned/armed)
ENVF = f"{DIR}/ara_guard.env"

# ---- config (env-overridable) ----
def _cfg():
    c = dict(FAST_SL=-0.04, IGN_DROP=-0.02, IGN_VR=2.0, TRAIL_PEAK=0.03,
             POLL=90, OPEN_UTC=120, CLOSE_UTC=520, LOT=100)  # 120m=02:00UTC, 520m=08:40UTC
    if os.path.exists(ENVF):
        for ln in open(ENVF):
            ln = ln.strip()
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.split("=", 1); k = k.strip()
                if k in c:
                    try: c[k] = type(c[k])(float(v)) if isinstance(c[k], (int, float)) else v.strip()
                    except: pass
    return c
CFG = _cfg()

def log(m): print(f"[guard {dt.datetime.utcnow():%H:%M:%S}] {m}", flush=True)
def jload(p, d=None):
    try: return json.load(open(p))
    except: return d
def jsave(p, s): os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(s, open(p, "w"), indent=1)
def num(x):
    try: return float(str(x).replace(",", "")) if x not in (None, "", "-") else 0.0
    except: return 0.0
def rp(x): return ("+" if x >= 0 else "-") + "Rp" + f"{abs(x):,.0f}".replace(",", ".")

# ---- WAHA ----
def _waenv():
    e = {}
    for p in (f"{DIR}/waha.env", "/opt/mt5-quant/waha.env"):
        if os.path.exists(p):
            for ln in open(p):
                ln = ln.strip()
                if "=" in ln and not ln.startswith("#"):
                    k, v = ln.split("=", 1); e[k.strip()] = v.strip().strip('"')
    return e
def wa_send(text):
    e = _waenv()
    if not all(e.get(k) for k in ("WAHA_URL", "WAHA_KEY", "WA_CHATID")):
        log("[wa] config kurang"); return
    try:
        r = requests.post(f"{e['WAHA_URL']}/api/sendText",
                          headers={"X-Api-Key": e["WAHA_KEY"], "Content-Type": "application/json"},
                          json={"session": "default", "chatId": e["WA_CHATID"], "text": text}, timeout=15)
        log(f"[wa] status={r.status_code}")
    except Exception as ex:
        log(f"[wa] err {str(ex)[:60]}")

# ---- data ----
def orderbook(c):
    try:
        j = sh._get(f"{EX}/orderbook/companies/{c}", {"with_full_price_tick": "true"})
        return (j if isinstance(j, dict) else j.json()).get("data", {})
    except Exception as ex:
        return {"_err": str(ex)[:50]}
def g(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, ""): return d[k]
    return None
def bid_total(d):
    """total volume di sisi bid; None kalau tak bisa diparse."""
    for key in ("bid", "bids", "buy", "buy_queue", "bid_queue"):
        arr = d.get(key)
        if isinstance(arr, list) and arr:
            tot = 0; ok = False
            for row in arr:
                if isinstance(row, dict):
                    v = num(g(row, "volume", "qty", "lot", "value")); tot += v; ok = True
            if ok: return tot
    return None
def arb_pct(price):
    if price < 200: return 0.35
    if price <= 5000: return 0.25
    return 0.20
def vol_ratio(c):
    """vr = vol hari-ini / avg20d, dari bar harian (unit konsisten). 0 kalau gagal."""
    try:
        b = sh.historical(c, 0.25) or []
        if len(b) < 6: return 0.0, ""
        L = b[-1]; d = str(L.get("date") or "")[:10]
        vol = num(L.get("volume")); prior = [num(x.get("volume")) for x in b[-21:-1]]
        av = sum(prior) / len(prior) if prior else 0
        return (vol / av if av else 0.0), d
    except: return 0.0, ""

# ---- market window ----
def market_open(now):
    if now.weekday() >= 5: return False           # Sab/Min
    m = now.hour * 60 + now.minute
    return CFG["OPEN_UTC"] <= m <= CFG["CLOSE_UTC"]

# ---- core check ----
def check_once():
    port = jload(STATE)
    if not port: return None
    pos = port.get("positions", {})
    opens = {c: p for c, p in pos.items() if p.get("status") == "open"}
    today = f"{dt.datetime.utcnow():%Y-%m-%d}"
    gs = jload(GSTATE, {}) or {}
    if gs.get("date") != today:
        gs = {"date": today, "armed": False, "peak": {}, "warned_arb": [], "exited": []}
    if not opens:
        if gs.get("date") == today and not gs.get("idle_logged"):
            gs["idle_logged"] = True; jsave(GSTATE, gs)
        log("tidak ada posisi open — idle")
        return gs
    # armed message (sekali per hari)
    if not gs.get("armed"):
        names = ", ".join(opens.keys())
        wa_send(f"🛡️ ARA-Guard AKTIF jaga {len(opens)} posisi: {names}\n"
                f"Auto-close bila bearish ignition / fast-stop {CFG['FAST_SL']*100:.0f}% "
                f"(tak nunggu SL lama). Poll {int(CFG['POLL'])}s.")
        gs["armed"] = True; jsave(GSTATE, gs)

    changed = False
    for c, p in opens.items():
        if c in gs["exited"]:
            continue
        d = orderbook(c)
        if d.get("_err"):
            log(f"{c}: ob err {d['_err']}"); continue
        last = num(g(d, "lastprice", "close", "last"))
        prev = num(g(d, "previous", "prev_price", "close_yesterday")) or num(p.get("entry"))
        if not last: continue
        entry = num(p.get("entry")); shares = int(p.get("shares") or 0)
        pnl = last / entry - 1 if entry else 0
        intc = last / prev - 1 if prev else 0
        vr, vd = vol_ratio(c)
        # peak tracking
        pk = gs["peak"].get(c, pnl); pk = max(pk, pnl); gs["peak"][c] = pk
        # --- ARB-lock detection ---
        floor = prev * (1 - arb_pct(prev))
        bt = bid_total(d)
        at_floor = last <= floor * 1.002
        locked = at_floor and (bt == 0 or (bt is None and intc <= -arb_pct(prev) * 0.95))
        if locked:
            if c not in gs["warned_arb"]:
                wa_send(f"⛔ {c} TERJEBAK ARB-LOCK (auto-reject bawah)\n"
                        f"Harga {last:.0f} ({intc*100:+.1f}%) — bid kosong, TAK BISA jual.\n"
                        f"Posisi nyangkut; pantau pembukaan lock. uPL {rp((last-entry)*shares)}")
                gs["warned_arb"].append(c); jsave(GSTATE, gs)
            log(f"{c}: ARB-LOCK trapped, last={last:.0f} pnl={pnl*100:.1f}%")
            continue
        # --- exit triggers (prioritas) ---
        reason = None
        if pnl <= CFG["FAST_SL"]:
            reason = "faststop"
        elif pnl <= CFG["IGN_DROP"] and vr >= CFG["IGN_VR"]:
            reason = "ignition"
        elif pk >= CFG["TRAIL_PEAK"] and pnl <= 0:
            reason = "trail_peak"
        if reason:
            exitp = num(g(d, "bid_price", "best_bid")) or last  # fill di bid kalau ada
            net = (exitp - entry) * shares
            p.update(status="closed", exit=exitp, cur=last,
                     exit_date=f"{dt.datetime.utcnow():%Y-%m-%d %H:%M}UTC",
                     result=reason, net=net)
            gs["exited"].append(c); changed = True
            emoji = {"faststop": "🛑", "ignition": "🔴", "trail_peak": "🟡"}[reason]
            wa_send(f"{emoji} ARA-Guard CLOSE {c} [{reason}]\n"
                    f"entry {entry:.0f} → exit {exitp:.0f} ({pnl*100:+.1f}%)  vr {vr:.1f}×\n"
                    f"P/L {rp(net)}  | sisa {len([x for x in opens if x not in gs['exited']])} posisi")
            log(f"{c}: EXIT {reason} pnl={pnl*100:.1f}% vr={vr:.1f} net={net:.0f}")
        else:
            log(f"{c}: hold pnl={pnl*100:+.1f}% intc={intc*100:+.1f}% vr={vr:.1f} pk={pk*100:+.1f}%")
    if changed:
        jsave(STATE, port)
    jsave(GSTATE, gs)
    return gs

def loop():
    log(f"start. cfg={CFG}")
    while True:
        now = dt.datetime.utcnow()
        if market_open(now):
            try: check_once()
            except Exception as ex: log(f"err {str(ex)[:120]}")
            time.sleep(int(CFG["POLL"]))
        else:
            log("market tutup — sleep 300s"); time.sleep(300)

if __name__ == "__main__":
    if "--once" in sys.argv:
        print(json.dumps(check_once() or {}, indent=1, default=str))
    else:
        loop()
