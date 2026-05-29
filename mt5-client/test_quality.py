"""
test_quality.py — Bandingkan MAOSC base vs MAOSC-Quality (dgn filter indikator).
Single 5thn + walk-forward (anti-overfit). Membuktikan apakah filter menaikkan PF & konsistensi.

Usage: python3 test_quality.py --symbol USDJPY --tf H1 --bt-days 1825 --windows 10
"""
from __future__ import annotations
import argparse, datetime as dt, statistics
from mt5_scalper import MT5Api
from backtest_lab import make_maosc, make_maosc_quality, run_backtest, fetch_bars


def bt(bars, strat, si, bal=10000):
    return run_backtest(bars, strat, si, balance=bal, risk_pct=1.0, max_risk_pct=6.0,
                        min_atr=0.0, max_spread_pct=12.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="USDJPY")
    ap.add_argument("--tf", default="H1")
    ap.add_argument("--bt-days", type=int, default=1825)
    ap.add_argument("--windows", type=int, default=10)
    ap.add_argument("--balance", type=float, default=10000)
    ap.add_argument("--api", default="http://192.168.0.116:8000")
    args = ap.parse_args()
    api = MT5Api(args.api, timeout=180)
    si = api.symbol_info(args.symbol)
    bars, _ = fetch_bars(api, args.symbol, args.tf, args.bt_days, 2000)
    variants = [("MAOSC base", make_maosc()), ("MAOSC-Quality", make_maosc_quality())]

    print(f"\n{'='*72}\n{args.symbol} {args.tf} | {len(bars)} bar (~{args.bt_days//365}thn) | ${args.balance:.0f}\n{'='*72}")
    print("\n── SINGLE (5 tahun kontinu) ──")
    print(f"{'varian':16} {'trade':>6} {'WR%':>6} {'return%':>8} {'PF':>5} {'maxDD%':>7}")
    for name, strat in variants:
        r = bt(bars, strat, si, args.balance)
        print(f"{name:16} {r.trades:>6} {r.win_rate:6.1f} {r.ret_pct:+8.2f} {r.pf:5.2f} {r.max_dd_pct:7.1f}")

    K = args.windows; w = len(bars) // K
    print(f"\n── WALK-FORWARD ({K} window, tiap window reset ${args.balance:.0f}) ──")
    print(f"{'varian':16} {'pos':>5} {'mean%':>7} {'median%':>8} {'worst%':>7} {'best%':>6} {'compound%':>10}")
    for name, strat in variants:
        rets = []
        for k in range(K):
            seg = bars[k*w:(k+1)*w] if k < K-1 else bars[k*w:]
            rets.append(bt(seg, strat, si, args.balance).ret_pct)
        pos = sum(1 for x in rets if x > 0)
        comp = 1.0
        for x in rets: comp *= (1 + x/100)
        print(f"{name:16} {pos:>3}/{K} {statistics.mean(rets):+7.2f} "
              f"{statistics.median(rets):+8.2f} {min(rets):+7.2f} {max(rets):+6.2f} {(comp-1)*100:+10.2f}")
    print("\nFilter naik kualitas kalau: PF & win-rate naik, drawdown turun, konsistensi (pos/K) naik.")
    print("Trade-off wajar: jumlah trade turun (lebih selektif).\n")


if __name__ == "__main__":
    main()
