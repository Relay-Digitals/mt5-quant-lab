"""
idx_curve.py — Kurva pertumbuhan kas AKUN MODAL BERSAMA (portofolio 14 saham) 10thn.
1 akun Rp100jt, modal dirotasi lintas saham (MEANREV+FOREIGN), compounding. Cap 15%/posisi.
Tampilkan equity akhir TIAP TAHUN + return tahunan + ×lipat dari awal.

Usage: python3 idx_curve.py [--capital 100000000] [--max-pos 15]
"""
from __future__ import annotations
import argparse
import idx_portfolio as P


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
    dates = sorted(all_dates)
    r = P.run(data, dates, dates[0], dates[-1] + "z", a.capital, a.max_pos)

    # equity akhir tiap tahun kalender
    eoy = {}
    for d, e in r["eq"]:
        eoy[d[:4]] = (d, e)              # tanggal & equity terakhir tiap tahun
    years = sorted(eoy)
    print(f"\n{'='*72}\nKURVA KAS AKUN BERSAMA — modal Rp{a.capital:,.0f}, cap {a.max_pos:.0f}%/posisi\n{'='*72}")
    print(f"{'tahun':6}{'tgl terakhir':>14}{'equity akhir':>18}{'return th':>11}{'×dari awal':>12}")
    print("-" * 72)
    prev = a.capital
    for y in years:
        d, e = eoy[y]
        yr_ret = (e - prev) / prev * 100
        print(f"{y:6}{d:>14}{e:>18,.0f}{yr_ret:>+10.1f}%{e/a.capital:>11.2f}x")
        prev = e
    fin = eoy[years[-1]][1]
    print("-" * 72)
    print(f"AKHIR: Rp{a.capital:,.0f} → Rp{fin:,.0f}  ({fin/a.capital:.2f}x, "
          f"return total {(fin-a.capital)/a.capital*100:+.0f}%, maxDD {r['mdd']:.1f}%)")
    cagr = ((fin / a.capital) ** (1 / 10.17) - 1) * 100
    print(f"CAGR ~{cagr:+.1f}%/tahun (basis 10,17thn). Catatan: tahun terakhir (berjalan) belum penuh.")


if __name__ == "__main__":
    main()
