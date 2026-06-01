"""
idx_monthly.py — Distribusi P&L BULANAN portofolio IDX (14 saham, cap 15%).
Jawab: rata-rata UNTUNG vs RUGI per bulan, bulan terburuk, % bulan rugi, losing-streak.
Pakai engine & universe idx_portfolio (1 kas, compounding). Full 10thn + holdout 4thn.

Usage: python3 idx_monthly.py [--capital 100000000] [--max-pos 15]
"""
from __future__ import annotations
import argparse, statistics
import idx_portfolio as P


def monthly_pnl(eq_curve, capital):
    """eq_curve=[(date,equity)] harian → P&L tiap bulan kalender (delta equity akhir-bulan)."""
    by_month = {}
    for d, e in eq_curve:
        by_month[d[:7]] = e               # equity terakhir tiap bulan (YYYY-MM)
    months = sorted(by_month)
    pnl = {}; prev = capital
    for m in months:
        pnl[m] = by_month[m] - prev; prev = by_month[m]
    return pnl


def stats(pnl, label):
    vals = list(pnl.values())
    wins = [v for v in vals if v > 0]; loss = [v for v in vals if v < 0]; flat = [v for v in vals if v == 0]
    worst_m = min(pnl, key=pnl.get); best_m = max(pnl, key=pnl.get)
    # losing streak terpanjang
    streak = mx = 0
    for m in sorted(pnl):
        if pnl[m] < 0: streak += 1; mx = max(mx, streak)
        else: streak = 0
    print(f"\n=== {label} === {len(vals)} bulan")
    print(f"  bulan UNTUNG : {len(wins):>3} ({len(wins)/len(vals)*100:.0f}%)  rata2 +Rp{statistics.mean(wins) if wins else 0:,.0f}")
    print(f"  bulan RUGI   : {len(loss):>3} ({len(loss)/len(vals)*100:.0f}%)  rata2 -Rp{abs(statistics.mean(loss)) if loss else 0:,.0f}")
    print(f"  bulan DATAR  : {len(flat):>3} ({len(flat)/len(vals)*100:.0f}%)  (tak ada posisi/trade)")
    print(f"  rata2 SEMUA bulan : Rp{statistics.mean(vals):+,.0f}")
    print(f"  bulan TERBURUK    : {worst_m}  Rp{pnl[worst_m]:+,.0f}")
    print(f"  bulan TERBAIK     : {best_m}  Rp{pnl[best_m]:+,.0f}")
    print(f"  rugi beruntun max : {mx} bulan")
    if loss:
        med = statistics.median([abs(v) for v in loss])
        print(f"  median bulan rugi : -Rp{med:,.0f}  (separuh bulan rugi < ini)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capital", type=float, default=100_000_000)
    ap.add_argument("--max-pos", type=float, default=15)
    a = ap.parse_args()

    print(f"Memuat data 10thn ({len(P.MEANREV_SYMS)+len(P.FOREIGN_SYMS)} saham)...")
    data = {}; all_dates = set()
    for sym, m in [(s, "MR") for s in P.MEANREV_SYMS] + [(s, "FX") for s in P.FOREIGN_SYMS]:
        bars, I, nfsum = P.load(sym)
        d2i = {b["date"]: k for k, b in enumerate(bars)}
        data[sym] = (bars, I, nfsum, d2i, m); all_dates |= set(d2i.keys())
    dates = sorted(all_dates); split = dates[int(len(dates) * 0.6)]
    print(f"Timeline {dates[0]} -> {dates[-1]} | cap {a.max_pos:.0f}%/posisi | modal Rp{a.capital:,.0f}")

    rf = P.run(data, dates, dates[0], dates[-1] + "z", a.capital, a.max_pos)
    rh = P.run(data, dates, split, dates[-1] + "z", a.capital, a.max_pos)
    stats(monthly_pnl(rf["eq"], a.capital), "FULL 10thn — P&L bulanan")
    stats(monthly_pnl(rh["eq"], a.capital), "HOLDOUT 4thn — P&L bulanan")
    print("\nCatatan: 'rugi' = bulan dgn equity turun. Compounding → bln belakangan basis lebih besar.")


if __name__ == "__main__":
    main()
