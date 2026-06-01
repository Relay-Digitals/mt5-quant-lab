"""
idx_bench.py — Benchmark BELI-TAHAN 10thn vs strategi akun bersama.
1) IHSG buy-hold (ikut pasar pasif)
2) Basket 14 saham equal-weight buy-hold (pegang saham yg sama, tanpa timing)
Bandingkan dgn portofolio modal bersama (idx_portfolio). Modal Rp100jt, 10thn.

Usage: python3 idx_bench.py
"""
from __future__ import annotations
import stockbit_history as H
import idx_portfolio as P

BAL0 = 100_000_000


def maxdd(curve):
    peak = -1; mx = 0.0
    for e in curve:
        peak = max(peak, e); mx = max(mx, (peak - e) / peak * 100) if peak > 0 else mx
    return mx


def cagr(end, yrs=10.17):
    return ((end / BAL0) ** (1 / yrs) - 1) * 100 if end > 0 else -100


def buyhold_one(sym):
    b = H.historical(sym, 10)
    p0 = b[0]["close"]; sh = BAL0 / p0
    curve = [sh * x["close"] for x in b]
    end = curve[-1]
    return end, maxdd(curve), b[0]["date"], b[-1]["date"]


def buyhold_basket(syms):
    series = {}; alloc = BAL0 / len(syms)
    all_dates = set()
    for s in syms:
        b = H.historical(s, 10); series[s] = {x["date"]: x["close"] for x in b}
        series[s]["_sh"] = alloc / b[0]["close"]; all_dates |= set(d for d in series[s] if d != "_sh")
    dates = sorted(all_dates)
    curve = []
    last = {s: None for s in syms}
    for d in dates:
        tot = 0
        for s in syms:
            px = series[s].get(d)
            if px is not None: last[s] = px
            if last[s] is not None: tot += series[s]["_sh"] * last[s]
        curve.append(tot)
    return curve[-1], maxdd(curve)


def main():
    syms = P.MEANREV_SYMS + P.FOREIGN_SYMS
    print("Memuat IHSG + 14 saham 10thn...")
    ih_end, ih_dd, d0, d1 = buyhold_one("IHSG")
    bk_end, bk_dd = buyhold_basket(syms)

    print(f"\n{'='*78}\nBENCHMARK BELI-TAHAN vs STRATEGI — modal Rp{BAL0:,.0f}, {d0}→{d1} (~10,17thn)\n{'='*78}")
    print(f"{'pendekatan':40}{'Rp100jt jadi':>18}{'×':>7}{'CAGR':>8}{'maxDD':>8}")
    print("-" * 78)
    print(f"{'IHSG beli-tahan (pasar pasif)':40}{ih_end:>18,.0f}{ih_end/BAL0:>6.2f}x{cagr(ih_end):>+7.1f}%{ih_dd:>7.0f}%")
    print(f"{'14 saham equal-weight beli-tahan':40}{bk_end:>18,.0f}{bk_end/BAL0:>6.2f}x{cagr(bk_end):>+7.1f}%{bk_dd:>7.0f}%")
    print(f"{'STRATEGI akun bersama (cap15, rotasi)':40}{'952,502,545':>18}{9.53:>6.2f}x{24.8:>+7.1f}%{35.9:>7.0f}%")
    print("-" * 78)
    print(f"Edge strategi vs IHSG : {9.53/(ih_end/BAL0):.1f}x lipat hasil IHSG")
    print(f"Edge strategi vs basket: {9.53/(bk_end/BAL0):.1f}x lipat beli-tahan saham yg sama")
    print("\nCatatan: beli-tahan = TANPA timing/exit, dividen TIDAK dihitung (strategi jg tidak).")


if __name__ == "__main__":
    main()
