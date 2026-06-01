"""
idx_value_bt.py — Backtest STRATEGI VALUE 10thn (point-in-time, anti-lookahead) vs IHSG.
Faktor: EARNINGS YIELD = NetIncome(thn lalu) / MarketCap. Rebalance tahunan (awal Mei),
pakai laba tahun SEBELUMNYA (sudah dilaporkan ~Maret) → tanpa lookahead.
MarketCap(t) = mcap_now × harga(t)/harga_now → kebal stock-split (harga sudah adjusted).
Pilih top-K termurah (EY tertinggi) equal-weight, tahan 1 thn, ulang. Bandingkan IHSG buy-hold.

Usage: python3 idx_value_bt.py [--topk 10]
"""
from __future__ import annotations
import argparse, bisect, re
import stockbit_history as H

_NI_NAMES = ["Net Income Attributable To", "Net Income From Continuing Operations",
             "Net Income", "Net Profit"]
def _clean(nm): return re.sub(r"</?b>", "", nm or "", flags=re.I).strip()

LQ45 = ["BBCA","BBRI","BMRI","BBNI","BRIS","BBTN","ARTO","TLKM","EXCL","ISAT","TOWR",
        "ASII","UNTR","ADRO","PTBA","ITMG","HRUM","ANTM","INCO","MDKA","TINS","MEDC",
        "PGAS","AKRA","ELSA","SMGR","INTP","INKP","TKIM","BRPT","ESSA","UNVR","ICBP",
        "INDF","MYOR","KLBF","SIDO","CPIN","JPFA","AMRT","ACES","MAPI","JSMR","TPIA"]
BAL0 = 100_000_000


def pbig(s):
    if s is None: return None
    s = str(s).strip(); neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace(",", "").strip()
    mult = 1
    for suf, m in (("B", 1e9), ("T", 1e12), ("M", 1e6)):
        if s.endswith(suf): mult = m; s = s[:-1].strip(); break
    try: v = float(s) * mult
    except ValueError: return None
    return -v if neg else v


def net_income_annual(sym, tok):
    """{tahun:int -> net_income Rp} dari findata-view income statement annual (12M)."""
    import requests
    r = requests.get(f"https://exodus.stockbit.com/findata-view/v2/financials/{sym}",
                     headers=H._headers(tok),
                     params={"data_type": 1, "report_type": 1, "statement_type": 2, "is_percentage": "false"}, timeout=20)
    if r.status_code != 200: return {}
    d = r.json().get("data", {}); periods = d.get("data_tables", {}).get("periods", [])
    years = [int(p.split()[-1]) for p in periods]
    found = {}
    def walk(accs):
        for a in accs:
            nm = _clean(a.get("name"))
            if nm in _NI_NAMES and a.get("values"):
                found.setdefault(nm, a["values"])
            walk(a.get("accounts", []))
    walk(d.get("data_tables", {}).get("accounts", []))
    vals = next((found[k] for k in _NI_NAMES if k in found), None)
    if not vals: return {}
    out = {}
    for y, v in zip(years, vals):
        pv = pbig(v)
        if pv is not None: out[y] = pv
    return out


def price_on_or_after(bars_dates, bars_close, target):
    i = bisect.bisect_left(bars_dates, target)
    return bars_close[i] if i < len(bars_dates) else None


def idx_at(dts, target):
    i = bisect.bisect_left(dts, target)
    return i if i < len(dts) else None


def run_strategy(px, ni, nf, mcap_now, rebals, topk, gate=None):
    """gate: None | 'mom' (momentum 12bln>0) | 'flow' (Σnf60>0). Return (equity_akhir, hist)."""
    bal = BAL0; hist = []
    for k in range(len(rebals) - 1):
        t0, t1 = rebals[k], rebals[k + 1]; yr_prev = int(t0[:4]) - 1
        t0_1y = f"{int(t0[:4])-1}{t0[4:]}"
        cand = []
        for s in px:
            if mcap_now.get(s) is None: continue
            nirec = ni.get(s, {}).get(yr_prev)
            if nirec is None or nirec <= 0: continue
            dts, cls = px[s]; i0 = idx_at(dts, t0)
            if i0 is None: continue
            p0 = cls[i0]; ey = nirec / (mcap_now[s] * p0 / cls[-1])
            cand.append((ey, s, p0, i0))
        cand.sort(reverse=True)
        # ambil pool 2x topk termurah, lalu gate timing, ambil topk
        pool = cand[:topk * 2] if gate else cand
        picks = []
        for ey, s, p0, i0 in pool:
            if gate == "mom":
                dts, cls = px[s]; j = idx_at(dts, t0_1y)
                if j is None or cls[i0] <= cls[j]: continue        # butuh momentum 12bln positif
            elif gate == "flow":
                nfs = nf.get(s)
                if not nfs or i0 < 60 or sum(nfs[i0-59:i0+1]) <= 0: continue  # asing akumulasi
            picks.append((s, p0))
            if len(picks) >= topk: break
        rets = []
        for s, p0 in picks:
            dts, cls = px[s]; i1 = idx_at(dts, t1)
            if i1 is not None: rets.append(cls[i1] / p0 - 1)
        yr_ret = sum(rets) / len(rets) if rets else 0
        bal *= (1 + yr_ret)
        hist.append((t0[:4], yr_ret * 100, bal, [s for s, _ in picks]))
    return bal, hist


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--topk", type=int, default=10); a = ap.parse_args()
    tok = H._read_env()["STOCKBIT_ACCESS_TOKEN"]
    import requests

    print(f"Memuat {len(LQ45)} saham (harga 10thn + laba tahunan + foreign) + IHSG...")
    px = {}; ni = {}; nf = {}; mcap_now = {}
    for s in LQ45:
        try:
            b = H.historical(s, 10)
            if len(b) < 200: continue
            px[s] = ([x["date"] for x in b], [x["close"] for x in b])
            nf[s] = [x.get("net_foreign", 0) for x in b]
            ni[s] = net_income_annual(s, tok)
            mc = requests.get(f"https://exodus.stockbit.com/keystats/ratio/v1/{s}", headers=H._headers(tok), timeout=15).json().get("data", {}).get("stats", {}).get("market_cap")
            mcap_now[s] = pbig(mc) * 1e9 if mc else None
        except Exception as e:
            print(f"  ! {s}: {str(e)[:40]}")
    ihb = H.historical("IHSG", 10); ih_dates = [x["date"] for x in ihb]; ih_close = [x["close"] for x in ihb]
    rebals = [f"{y}-05-02" for y in range(2017, 2026)]

    variants = {"VALUE murni": None, "VALUE+momentum": "mom", "VALUE+foreign": "flow"}
    res = {name: run_strategy(px, ni, nf, mcap_now, rebals, a.topk, g) for name, g in variants.items()}
    # IHSG
    ih_bal = BAL0; ih_hist = []
    for k in range(len(rebals) - 1):
        i0 = idx_at(ih_dates, rebals[k]); i1 = idx_at(ih_dates, rebals[k + 1])
        r = (ih_close[i1] / ih_close[i0] - 1) if i0 is not None and i1 is not None else 0
        ih_bal *= (1 + r); ih_hist.append((rebals[k][:4], r * 100, ih_bal))

    n = len(rebals) - 1
    print(f"\n{'='*92}\n(c) FUNDAMENTAL + TIMING — top-{a.topk}, rebalance tahunan, point-in-time vs IHSG\n{'='*92}")
    print(f"{'thn':5}" + "".join(f"{nm:>17}" for nm in variants) + f"{'IHSG':>10}")
    print("-" * 92)
    for k in range(n):
        row = f"{ih_hist[k][0]:5}"
        for nm in variants:
            row += f"{res[nm][1][k][1]:>+16.1f}%"
        row += f"{ih_hist[k][1]:>+9.1f}%"
        print(row)
    print("-" * 92)
    print(f"{'AKHIR':5}", end="")
    for nm in variants:
        bal = res[nm][0]; print(f"{bal/BAL0:>15.2f}x ", end="")
    print(f"{ih_bal/BAL0:>8.2f}x")
    print(f"{'CAGR':5}", end="")
    for nm in variants:
        c = (res[nm][0] / BAL0) ** (1 / n) - 1; print(f"{c*100:>+14.1f}%/th", end="")
    print(f"{((ih_bal/BAL0)**(1/n)-1)*100:>+7.1f}%/th")
    print("\nGate timing pilih dari pool 2× termurah lalu saring (momentum 12bln>0 / asing Σnf60>0).")
    print("Catatan: dividen TIDAK dihitung (value/bank yield 5-12% → return riil lebih tinggi).")


if __name__ == "__main__":
    main()
