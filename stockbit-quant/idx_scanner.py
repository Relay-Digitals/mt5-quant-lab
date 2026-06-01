"""
idx_scanner.py — Live EOD signal scanner saham ID (paper-trade + siap eksekusi riil).
Jalan tiap sore setelah IDX tutup (~16:30 WIB). Untuk tiap saham di universe:
  - cek EXIT posisi terbuka (MEANREV: SL/TP kena hari ini; FOREIGN: Σnf60 flip <=0)
  - cek ENTRY bila flat (MEANREV deep-oversold / FOREIGN regime cross>0)
State paper (kas, posisi, jurnal) persist di idx_state.json. Adapter eksekusi: PaperBroker (aktif),
StockbitBroker (stub — order/v2/buy|sell, butuh Authorization-Carina + body schema, BELUM aktif).

Usage:
  python3 idx_scanner.py                 # scan hari ini, update paper state, cetak laporan
  python3 idx_scanner.py --status        # tampilkan portfolio & jurnal terakhir, tanpa scan
  python3 idx_scanner.py --init 100000000 # reset state, modal awal
"""
from __future__ import annotations
import argparse, json, math, os, datetime as dt
import stockbit_history
import idx_indicators as ind
try:
    import idx_rag                       # RAG opsional (PG+Meili di CT 108)
except Exception:
    idx_rag = None

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "idx_state.json")
MEANREV_SYMS = ["BMRI", "BBCA", "ICBP", "ASII", "UNTR", "TKIM"]                  # bank/consumer/industri
FOREIGN_SYMS = ["ADRO", "MEDC", "ANTM", "INCO", "TOBA", "TINS", "BRMS", "DSNG"]   # komoditas/energi
FEE = 0.2; LOT = 100; NF_WIN = 60
MAX_POS_FRAC = 15.0       # cap %% equity per posisi (holdout 14-saham: DD 25.8% <30% target)
RISK_FRAC = 1.0           # risk %% modal awal utk MEANREV (sizing via SL)


# ---------- execution adapters ----------
class PaperBroker:
    """Eksekusi simulasi di state JSON (default)."""
    name = "PAPER"
    def buy(self, sym, sh, px, reason): return dict(ok=True, fill=px, sh=sh)
    def sell(self, sym, sh, px, reason): return dict(ok=True, fill=px, sh=sh)

class StockbitBroker:
    """STUB eksekusi riil. order/v2/buy|sell @ carina.stockbit.com butuh header
    `Authorization-Carina: Bearer <token-sekuritas>` (BEDA dari token data) + body schema
    (qty,price,symbol,...) yg belum terdokumentasi. Aktifkan setelah kredensial & schema dikonfirmasi."""
    name = "STOCKBIT-REAL"
    def __init__(self): raise NotImplementedError(
        "Eksekusi riil belum aktif: perlu Authorization-Carina (token sekuritas) & body order/v2/buy. "
        "Lihat stockbit-docs 06_full_endpoint_reference.md baris 392-431.")


# ---------- state ----------
def load_state():
    if not os.path.exists(STATE):
        return None
    return json.load(open(STATE))

def save_state(s):
    json.dump(s, open(STATE, "w"), indent=1, ensure_ascii=False)

def init_state(capital):
    s = dict(capital0=capital, cash=capital, peak=capital, positions={}, journal=[],
             created=dt.date.today().isoformat())
    save_state(s); return s


# ---------- signals (selaras idx_portfolio) ----------
def sig_for(sym, method):
    bars = stockbit_history.historical(sym, 1.2)        # ~1.2thn cukup utk nf60 + warmup
    if len(bars) < 70: raise RuntimeError(f"{sym}: data kurang ({len(bars)})")
    I = ind.compute(bars)
    i = len(bars) - 1; bar = bars[i]
    out = dict(sym=sym, method=method, date=bar["date"], close=bar["close"],
               high=bar["high"], low=bar["low"], entry=False, sl=None, tp=None,
               exit_flip=False)
    if method == "MR":
        bpb, r, mfi, sd, atr = I["bb_pctb"][i], I["rsi14"][i], I["mfi14"][i], I["stoch_d"][i], I["atr14"][i]
        vals = (bpb, r, mfi, sd, atr)
        if not any(v is None or (isinstance(v, float) and math.isnan(v)) for v in vals) and atr > 0:
            out["atr"] = atr
            if bpb < 0.15 and r < 40 and mfi <= 33 and sd <= 18:
                out["entry"] = True; out["sl"] = bar["close"] - 1.5 * atr; out["tp"] = bar["close"] + 1.5 * atr
    else:
        nf = [b.get("net_foreign", 0) for b in bars]
        nfsum_now = sum(nf[i - NF_WIN + 1:i + 1]); nfsum_prev = sum(nf[i - NF_WIN:i])
        out["nfsum"] = nfsum_now
        out["entry"] = nfsum_now > 0 and nfsum_prev <= 0
        out["exit_flip"] = nfsum_now <= 0
    return out


def equity(s, prices):
    return s["cash"] + sum(p["sh"] * prices.get(sym, p["entry"]) for sym, p in s["positions"].items())


def scan(broker):
    s = load_state()
    if s is None:
        print("State belum ada. Jalankan: python3 idx_scanner.py --init 100000000"); return
    universe = [(x, "MR") for x in MEANREV_SYMS] + [(x, "FX") for x in FOREIGN_SYMS]
    sigs = {}
    for sym, m in universe:
        try: sigs[sym] = sig_for(sym, m)
        except Exception as e: print(f"  ! {sym}: {str(e)[:50]}")
    prices = {sym: g["close"] for sym, g in sigs.items()}
    today = dt.date.today().isoformat()
    actions = []; rag_recs = []

    # ---- EXITS ----
    for sym in list(s["positions"].keys()):
        if sym not in sigs: continue
        p = s["positions"][sym]; g = sigs[sym]; px = None; why = ""
        if p["method"] == "MR":
            if g["low"] <= p["sl"]: px, why = p["sl"], "SL kena"
            elif g["high"] >= p["tp"]: px, why = p["tp"], "TP kena"
        else:
            if g["exit_flip"]: px, why = g["close"], "asing distribusi (Σnf60<=0)"
        if px is not None:
            r = broker.sell(sym, p["sh"], px, why)
            fill = r["fill"]; proceeds = p["sh"] * fill - FEE / 100 * fill * p["sh"]
            net = (fill - p["entry"]) * p["sh"] - FEE / 100 * (p["entry"] + fill) * p["sh"]
            s["cash"] += proceeds
            s["journal"].append(dict(date=today, sym=sym, action="SELL", px=fill, sh=p["sh"],
                                     net=round(net), reason=why))
            actions.append(f"JUAL {sym} {p['sh']}@{fill:,.0f} ({why}) net Rp{net:+,.0f}")
            rag_recs.append(dict(id=f"{today}_{sym}_SELL", trade_date=today, action="SELL",
                                 symbol=sym, method=p["method"], price=fill, shares=p["sh"],
                                 value=p["sh"]*fill, net=round(net), sl=p.get("sl"), tp=p.get("tp"),
                                 reason=why, features=dict(entry=p["entry"], held_since=p.get("date"))))
            del s["positions"][sym]

    # ---- ENTRIES ----
    eq = equity(s, prices)
    for sym, m in universe:
        if sym in s["positions"] or sym not in sigs: continue
        g = sigs[sym]
        if not g["entry"]: continue
        c = g["close"]
        cap_sh = (eq * MAX_POS_FRAC / 100) / c
        cash_sh = (s["cash"] * 0.999) / c
        cands = [cap_sh, cash_sh]
        if m == "MR": cands.append((s["capital0"] * RISK_FRAC / 100) / (1.5 * g["atr"]))
        sh = int(min(cands) // LOT) * LOT
        cost = sh * c + FEE / 100 * c * sh
        if sh < LOT or cost > s["cash"]: continue
        reason = ("MEANREV deep-oversold" if m == "MR" else "FOREIGN regime cross>0")
        broker.buy(sym, sh, c, reason)
        s["cash"] -= cost
        s["positions"][sym] = dict(method=m, entry=c, sh=sh, sl=g.get("sl"), tp=g.get("tp"),
                                   date=today, reason=reason)
        actions.append(f"BELI {sym} {sh}@{c:,.0f} ({reason}) Rp{cost:,.0f}")
        rag_recs.append(dict(id=f"{today}_{sym}_BUY", trade_date=today, action="BUY",
                             symbol=sym, method=m, price=c, shares=sh, value=cost, net=None,
                             sl=g.get("sl"), tp=g.get("tp"), reason=reason, features={}))

    eq = equity(s, prices)
    s["peak"] = max(s.get("peak", s["capital0"]), eq)
    save_state(s)
    # ---- store report tiap aksi ke RAG (PG + Meili), best-effort ----
    if idx_rag and rag_recs:
        ret = (eq - s["capital0"]) / s["capital0"] * 100
        dd = (s["peak"] - eq) / s["peak"] * 100
        for r in rag_recs:
            r.update(equity=eq, return_pct=ret, dd_pct=dd)
            idx_rag.log_trade(r)
    _print_report(s, sigs, actions, eq, broker)


def _print_report(s, sigs, actions, eq, broker):
    dd = (s["peak"] - eq) / s["peak"] * 100
    print(f"\n=== IDX SCANNER {dt.date.today().isoformat()} | broker={broker.name} ===")
    print(f"Equity Rp{eq:,.0f} | kas Rp{s['cash']:,.0f} | return {(eq-s['capital0'])/s['capital0']*100:+.1f}% | DD {dd:.1f}%")
    print("\nAKSI HARI INI:" if actions else "\nAKSI HARI INI: (tidak ada sinyal)")
    for a in actions: print("  • " + a)
    print("\nPOSISI TERBUKA:")
    if not s["positions"]: print("  (kosong)")
    for sym, p in s["positions"].items():
        cur = sigs.get(sym, {}).get("close", p["entry"]); upl = (cur - p["entry"]) * p["sh"]
        ext = f" SL{p['sl']:,.0f}/TP{p['tp']:,.0f}" if p["method"] == "MR" else ""
        print(f"  {sym}({p['method']}) {p['sh']}@{p['entry']:,.0f} now {cur:,.0f} uPL Rp{upl:+,.0f}{ext}")
    print("\nWATCHLIST sinyal:")
    for sym, g in sigs.items():
        tag = "ENTRY✅" if g["entry"] else ("exit-flip" if g.get("exit_flip") else "-")
        extra = (f"nf60={g['nfsum']/1e9:+.1f}M" if g["method"] == "FX" else
                 f"bb%b? rsi/mfi/stoch")
        print(f"  {sym:5}{g['method']:3} c={g['close']:,.0f} {tag}")


def cmd_status():
    s = load_state()
    if s is None: print("State belum ada."); return
    print(f"Modal awal Rp{s['capital0']:,.0f} | kas Rp{s['cash']:,.0f} | posisi {len(s['positions'])} | trade {len(s['journal'])}")
    for sym, p in s["positions"].items():
        print(f"  {sym}({p['method']}) {p['sh']}@{p['entry']:,.0f} sejak {p['date']} — {p['reason']}")
    print("Jurnal 10 terakhir:")
    for j in s["journal"][-10:]:
        print(f"  {j['date']} {j['action']:4} {j['sym']:5} {j['sh']}@{j['px']:,.0f} net Rp{j.get('net',0):+,} — {j['reason']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", type=float, metavar="MODAL", help="reset state dgn modal awal")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--real", action="store_true", help="pakai StockbitBroker (belum aktif)")
    a = ap.parse_args()
    if a.init: init_state(a.init); print(f"State direset, modal Rp{a.init:,.0f} → {STATE}"); return
    if a.status: cmd_status(); return
    broker = StockbitBroker() if a.real else PaperBroker()
    scan(broker)


if __name__ == "__main__":
    main()
