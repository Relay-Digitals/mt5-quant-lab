"""
idx_perstock.py — Performa PER SAHAM (standalone Rp100jt, compounding, metode tervalidasi).
Hitung: total return, CAGR %/tahun, rata-rata untung Rp/tahun & Rp/bulan, + rincian P&L per tahun kalender.

MEANREV (bank/consumer/industri): bb<0.15 & rsi<40 & mfi<33 & stochD<18, SL/TP 1.5ATR.
FOREIGN  (komoditas/energi):       Σnet_foreign 60hr cross>0 masuk, <=0 keluar.

Usage: python3 idx_perstock.py   (semua 14 saham)  |  --symbols BMRI,ADRO
"""
from __future__ import annotations
import argparse, math, datetime as dt
import stockbit_history
import idx_indicators as ind

MEANREV_SYMS = ["BMRI", "BBCA", "ICBP", "ASII", "UNTR", "TKIM"]
FOREIGN_SYMS = ["ADRO", "MEDC", "ANTM", "INCO", "TOBA", "TINS", "BRMS", "DSNG"]
METHOD = {**{s: "MR" for s in MEANREV_SYMS}, **{s: "FX" for s in FOREIGN_SYMS}}
FEE = 0.2; LOT = 100; NF_WIN = 60; BAL0 = 100_000_000


def backtest(bars, I, method, lo=0, hi=None):
    """Return (trades[{date,net}], saldo_akhir). Compounding Rp100jt. Sizing TERVALIDASI:
    MEANREV = risk1%/SL + cap kas; FOREIGN = band ~20% notional (sama spt screening idx_foreign)."""
    n = len(bars); hi = hi if hi is not None else n; atr = I["atr14"]
    nf = [b.get("net_foreign", 0) for b in bars]
    nfsum = [sum(nf[max(0, i - NF_WIN + 1):i + 1]) for i in range(n)]
    bal = BAL0; pos = None; trades = []
    for i in range(max(lo, 60), hi):
        bar = bars[i]; c = bar["close"]
        if pos:
            ex = None
            if method == "MR":
                if bar["low"] <= pos["sl"]: ex = pos["sl"]
                elif bar["high"] >= pos["tp"]: ex = pos["tp"]
            else:
                if nfsum[i] <= 0: ex = c
            if ex is not None:
                net = (ex - pos["entry"]) * pos["sh"] - FEE / 100 * (pos["entry"] + ex) * pos["sh"]
                hold = (dt.datetime.strptime(bar["date"], "%Y-%m-%d") - pos["edate"]).days
                bal += net; trades.append({"date": bar["date"], "net": net, "hold": hold}); pos = None
        if pos: continue
        sig = False; sl = tp = None
        if method == "MR":
            a = atr[i]; bpb, r, mfi, sd = I["bb_pctb"][i], I["rsi14"][i], I["mfi14"][i], I["stoch_d"][i]
            if a and not any(x is None or (isinstance(x, float) and math.isnan(x)) for x in (a, bpb, r, mfi, sd)) and a > 0:
                if bpb < 0.15 and r < 40 and mfi <= 33 and sd <= 18:
                    sig = True; sl = c - 1.5 * a; tp = c + 1.5 * a
                    sh = int(min((bal * 0.01) / (1.5 * a), (bal * 0.999) / c) // LOT) * LOT
        else:
            if i >= 1 and nfsum[i] > 0 and nfsum[i - 1] <= 0:
                sig = True
                sh = int(min((bal / 100) / (c * 0.05), (bal * 0.999) / c) // LOT) * LOT  # band ~20%
        if not sig or sh < LOT or sh * c + FEE / 100 * c * sh > bal: continue
        pos = dict(entry=c, sh=sh, sl=sl, tp=tp, edate=dt.datetime.strptime(bar["date"], "%Y-%m-%d"))
    if pos:  # likuidasi akhir periode
        c = bars[hi - 1]["close"]; net = (c - pos["entry"]) * pos["sh"] - FEE / 100 * (pos["entry"] + c) * pos["sh"]
        hold = (dt.datetime.strptime(bars[hi - 1]["date"], "%Y-%m-%d") - pos["edate"]).days
        bal += net; trades.append({"date": bars[hi - 1]["date"], "net": net, "hold": hold})
    return trades, bal


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--symbols")
    syms = (ap.parse_args().symbols or "").split(",") if ap.parse_args().symbols else (MEANREV_SYMS + FOREIGN_SYMS)
    rows = []; year_pnl = {}; years_all = set()
    for s in syms:
        m = METHOD.get(s, "MR")
        bars = stockbit_history.historical(s, 10); I = ind.compute(bars)
        if len(bars) < 70: print(f"{s}: data kurang"); continue
        d0 = dt.datetime.strptime(bars[0]["date"], "%Y-%m-%d"); d1 = dt.datetime.strptime(bars[-1]["date"], "%Y-%m-%d")
        yrs = (d1 - d0).days / 365.25
        tr, bal = backtest(bars, I, m)
        net = bal - BAL0; cagr = ((bal / BAL0) ** (1 / yrs) - 1) * 100 if bal > 0 else -100
        wins = [t for t in tr if t["net"] > 0]; gl = -sum(t["net"] for t in tr if t["net"] <= 0)
        pf = (sum(t["net"] for t in wins) / gl) if gl else (9.99 if wins else 0)
        wr = len(wins) / len(tr) * 100 if tr else 0
        holds = [t["hold"] for t in tr if "hold" in t]
        avg_hold = sum(holds) / len(holds) if holds else 0
        # holdout 40% terakhir (regime terkini)
        sp = int(len(bars) * 0.6); yrs_h = (d1 - dt.datetime.strptime(bars[sp]["date"], "%Y-%m-%d")).days / 365.25
        trh, balh = backtest(bars, I, m, lo=sp, hi=len(bars))
        net_h = balh - BAL0; ret_h = net_h / BAL0 * 100
        rows.append((s, m, yrs, len(tr), wr, pf, net / BAL0 * 100, cagr, net / yrs, net / (yrs * 12), ret_h, net_h / yrs_h, net_h / (yrs_h * 12), avg_hold, bal, balh))
        yp = {}
        for t in tr:
            y = t["date"][:4]; yp[y] = yp.get(y, 0) + t["net"]; years_all.add(y)
        year_pnl[s] = yp

    print(f"\n{'='*108}\nPERFORMA PER SAHAM — standalone Rp100jt, compounding, sizing tervalidasi ({len(rows)} saham)\n{'='*108}")
    print(f"{'saham':6}{'mtd':4}{'tr':>4}{'WR%':>5}{'PF':>6}{'holdHr':>7}|{'--- FULL 10thn ---':^34}|{'--- HOLDOUT 4thn ---':^30}")
    print(f"{'':32}{'CAGR%/th':>10}{'Rp/tahun':>13}{'Rp/bulan':>11}{'ret%':>9}{'Rp/tahun':>13}{'Rp/bulan':>11}")
    print("-" * 115)
    for s, m, yrs, n, wr, pf, totret, cagr, py, pm, reth, pyh, pmh, hold, bal, balh in sorted(rows, key=lambda x: -x[11]):
        print(f"{s:6}{m:4}{n:>4}{wr:>5.0f}{pf:>6.2f}{hold:>6.0f}d|{cagr:>+10.1f}{py:>+13,.0f}{pm:>+11,.0f}|{reth:>+9.1f}{pyh:>+13,.0f}{pmh:>+11,.0f}")
    print("-" * 115)
    tf = sum(r[8] for r in rows); th = sum(r[11] for r in rows)
    print(f"{'TOTAL (14× Rp100jt)':32}{'':10}{tf:>+13,.0f}{tf/12:>+11,.0f}|{'':9}{th:>+13,.0f}{th/12:>+11,.0f}")
    print("holdHr=rata2 hari tahan/trade. FULL=rata2 10thn (termasuk tahun jelek awal). HOLDOUT=regime 4thn terakhir.")

    # ---- pertumbuhan kas 10thn dari Rp100jt/saham ----
    print(f"\n{'='*70}\nPERTUMBUHAN KAS 10thn — Rp100jt/saham → saldo akhir (compounding)\n{'='*70}")
    print(f"{'saham':6}{'mtd':4}{'saldo akhir':>18}{'×lipat':>9}{'CAGR%/th':>10}")
    print("-" * 70)
    tot_bal = 0
    for s, m, yrs, n, wr, pf, totret, cagr, py, pm, reth, pyh, pmh, hold, bal, balh in sorted(rows, key=lambda x: -x[14]):
        tot_bal += bal
        print(f"{s:6}{m:4}{bal:>18,.0f}{bal/BAL0:>8.2f}x{cagr:>+10.1f}")
    print("-" * 70)
    print(f"{'TOTAL 14 saham':10}{14*BAL0:>0,.0f} → {tot_bal:>,.0f}  ({tot_bal/(14*BAL0):.2f}x, dari Rp1,4M jadi Rp{tot_bal/1e9:.2f}M)")

    # rincian P&L per tahun kalender
    yrs_sorted = sorted(years_all)
    print(f"\n{'='*96}\nP&L PER TAHUN KALENDER (Rp juta) — net realisasi tiap tahun\n{'='*96}")
    print(f"{'saham':6}" + "".join(f"{y[2:]:>8}" for y in yrs_sorted))
    print("-" * (6 + 8 * len(yrs_sorted)))
    for s in [r[0] for r in sorted(rows, key=lambda x: -x[7])]:
        yp = year_pnl[s]
        print(f"{s:6}" + "".join(f"{yp.get(y,0)/1e6:>+8.1f}" if y in yp else f"{'·':>8}" for y in yrs_sorted))


if __name__ == "__main__":
    main()
