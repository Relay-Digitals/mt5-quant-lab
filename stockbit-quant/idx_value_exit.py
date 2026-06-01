"""
idx_value_exit.py — Uji ATURAN JUAL pada strategi value (Earnings Yield, top-K, rebalance tahunan).
Semua point-in-time, anti-lookahead (NI thn lalu), anti-split. Berbasis HARGA (tanpa dividen)
agar efek aturan-jual murni terlihat. Bandingkan:
  BASELINE   = tahan 1thn penuh (rebalance kalender)
  STOP -X%   = jual ke kas bila turun X% dari entry (sisa tahun cash)
  TRAIL -Y%  = jual bila turun Y% dari puncak harga selama ditahan
  REGIME     = hanya invest bila IHSG > SMA200 di tgl rebalance (else kas setahun)

Usage: python3 idx_value_exit.py [--topk 10] [--stop 20] [--trail 25]
"""
from __future__ import annotations
import argparse, bisect, re, requests
import stockbit_history as H

LQ45 = ["BBCA","BBRI","BMRI","BBNI","BRIS","BBTN","ARTO","TLKM","EXCL","ISAT","TOWR",
        "ASII","UNTR","ADRO","PTBA","ITMG","HRUM","ANTM","INCO","MDKA","TINS","MEDC",
        "PGAS","AKRA","ELSA","SMGR","INTP","INKP","TKIM","BRPT","ESSA","UNVR","ICBP",
        "INDF","MYOR","KLBF","SIDO","CPIN","JPFA","AMRT","ACES","MAPI","JSMR","TPIA"]
BAL0 = 100_000_000
_NI = ["Net Income Attributable To", "Net Income From Continuing Operations", "Net Income", "Net Profit"]
_clean = lambda n: re.sub(r"</?b>", "", n or "", flags=re.I).strip()


def pbig(s):
    if s is None: return None
    s = str(s).strip(); neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace(",", "").strip(); mult = 1
    for suf, m in (("B", 1e9), ("T", 1e12), ("M", 1e6)):
        if s.endswith(suf): mult = m; s = s[:-1].strip(); break
    try: v = float(s) * mult
    except ValueError: return None
    return -v if neg else v


def ni_annual(sym, tok):
    r = requests.get(f"https://exodus.stockbit.com/findata-view/v2/financials/{sym}", headers=H._headers(tok),
                     params={"data_type": 1, "report_type": 1, "statement_type": 2, "is_percentage": "false"}, timeout=20)
    if r.status_code != 200: return {}
    d = r.json().get("data", {}); years = [int(p.split()[-1]) for p in d.get("data_tables", {}).get("periods", [])]
    found = {}
    def w(accs):
        for a in accs:
            nm = _clean(a.get("name"))
            if nm in _NI and a.get("values"): found.setdefault(nm, a["values"])
            w(a.get("accounts", []))
    w(d.get("data_tables", {}).get("accounts", []))
    vals = next((found[k] for k in _NI if k in found), None)
    return {y: pbig(v) for y, v in zip(years, vals)} if vals else {}


def idx_at(dts, t):
    i = bisect.bisect_left(dts, t); return i if i < len(dts) else None


def hold_return(cls, i0, i1, rule, stop, trail):
    """return saham selama [i0,i1] dgn aturan exit intra-tahun. Setelah exit = kas (0%)."""
    entry = cls[i0]; peak = entry
    for i in range(i0 + 1, i1 + 1):
        p = cls[i]; peak = max(peak, p)
        if rule == "stop" and p <= entry * (1 - stop / 100):
            return p / entry - 1
        if rule == "trail" and p <= peak * (1 - trail / 100):
            return p / entry - 1
    return cls[i1] / entry - 1


def run(px, ni, mcap, rebals, topk, rule, stop, trail, ih=None):
    bal = BAL0; hist = []
    ihd, ihc, ihsma = ih if ih else (None, None, None)
    for k in range(len(rebals) - 1):
        t0, t1 = rebals[k], rebals[k + 1]; yp = int(t0[:4]) - 1
        # REGIME: cek IHSG>SMA200 di t0
        if rule == "regime":
            j = idx_at(ihd, t0)
            if j is None or ihsma[j] is None or ihc[j] < ihsma[j]:
                bal *= 1.0; hist.append((t0[:4], 0.0, bal, ["CASH"])); continue
        cand = []
        for s in px:
            if mcap.get(s) is None: continue
            nirec = ni.get(s, {}).get(yp)
            if nirec is None or nirec <= 0: continue
            dts, cls = px[s]; i0 = idx_at(dts, t0)
            if i0 is None: continue
            ey = nirec / (mcap[s] * cls[i0] / cls[-1])
            cand.append((ey, s, i0))
        cand.sort(reverse=True); picks = cand[:topk]
        rets = []
        for ey, s, i0 in picks:
            dts, cls = px[s]; i1 = idx_at(dts, t1)
            if i1 is None: continue
            rets.append(hold_return(cls, i0, i1, rule if rule in ("stop", "trail") else None, stop, trail))
        yr = sum(rets) / len(rets) if rets else 0; bal *= (1 + yr)
        hist.append((t0[:4], yr * 100, bal, [s for _, s, _ in picks]))
    return bal, hist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topk", type=int, default=10); ap.add_argument("--stop", type=float, default=20)
    ap.add_argument("--trail", type=float, default=25); a = ap.parse_args()
    tok = H._read_env()["STOCKBIT_ACCESS_TOKEN"]
    print(f"Memuat {len(LQ45)} saham + IHSG...")
    px = {}; ni = {}; mcap = {}
    for s in LQ45:
        try:
            b = H.historical(s, 10)
            if len(b) < 200: continue
            px[s] = ([x["date"] for x in b], [x["close"] for x in b])
            ni[s] = ni_annual(s, tok)
            mc = requests.get(f"https://exodus.stockbit.com/keystats/ratio/v1/{s}", headers=H._headers(tok), timeout=15).json().get("data", {}).get("stats", {}).get("market_cap")
            mcap[s] = pbig(mc) * 1e9 if mc else None
        except Exception as e:
            print(f"  ! {s}: {str(e)[:40]}")
    ihb = H.historical("IHSG", 10); ihd = [x["date"] for x in ihb]; ihc = [x["close"] for x in ihb]
    ihsma = [None] * len(ihc)
    for i in range(len(ihc)):
        if i >= 199: ihsma[i] = sum(ihc[i - 199:i + 1]) / 200
    rebals = [f"{y}-05-02" for y in range(2017, 2027)]; n = len(rebals) - 1

    V = {"BASELINE": ("base", None), f"STOP -{a.stop:.0f}%": ("stop", None),
         f"TRAIL -{a.trail:.0f}%": ("trail", None), "REGIME IHSG>SMA200": ("regime", (ihd, ihc, ihsma))}
    res = {nm: run(px, ni, mcap, rebals, a.topk, rule, a.stop, a.trail, ih) for nm, (rule, ih) in V.items()}

    print(f"\n{'='*92}\nUJI ATURAN JUAL — value top-{a.topk}, harga saja (tanpa dividen), point-in-time\n{'='*92}")
    print(f"{'thn':5}" + "".join(f"{nm:>19}" for nm in V))
    print("-" * 92)
    for k in range(n):
        print(f"{res['BASELINE'][1][k][0]:5}" + "".join(f"{res[nm][1][k][1]:>+18.1f}%" for nm in V))
    print("-" * 92)
    print(f"{'×':5}" + "".join(f"{res[nm][0]/BAL0:>18.2f}x" for nm in V))
    print(f"{'CAGR':5}" + "".join(f"{((res[nm][0]/BAL0)**(1/n)-1)*100:>+16.1f}%/t" for nm in V))
    print(f"{'NET':5}" + "".join(f"{res[nm][0]-BAL0:>+17,.0f}" for nm in V))
    # fokus tahun krisis 2019
    print("\n2019 (tahun terburuk) per varian:", {nm: f"{res[nm][1][2][1]:+.1f}%" for nm in V})
    print("Catatan: harga saja; dividen (~+5-8%/th value) menambah ~rata ke semua varian.")


if __name__ == "__main__":
    main()
