"""
test_timefilter.py — Uji filter waktu (UTC) pada TREND. Base vs skip-NY vs skip-midday
vs London-only. Single 5thn + walk-forward. Hanya pola jam yg lolos uji konsistensi.

Usage: python3 test_timefilter.py --symbol USDJPY
"""
from __future__ import annotations
import argparse, datetime as dt, statistics
from mt5_scalper import MT5Api
from backtest_lab import make_trend, run_backtest, fetch_bars


def bt(bars, st, si, bal=10000):
    return run_backtest(bars, st, si, balance=bal, risk_pct=1.0, max_risk_pct=6.0,
                        min_atr=0.0, max_spread_pct=12.0)


def wf(bars, st, si, K=10, bal=10000):
    w = len(bars)//K; rets=[]
    for k in range(K):
        seg = bars[k*w:(k+1)*w] if k<K-1 else bars[k*w:]
        rets.append(bt(seg, st, si, bal).ret_pct)
    pos = sum(1 for x in rets if x>0); comp=1.0
    for x in rets: comp*=(1+x/100)
    return pos, K, min(rets), (comp-1)*100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="USDJPY")
    ap.add_argument("--bt-days", type=int, default=1825)
    ap.add_argument("--api", default="http://192.168.0.116:8000")
    args = ap.parse_args()
    api = MT5Api(args.api, timeout=180); si = api.symbol_info(args.symbol)
    bars, _ = fetch_bars(api, args.symbol, "H1", args.bt_days, 2000)

    variants = [
        ("base (semua jam)", make_trend()),
        ("skip NY 14-17", make_trend(block_hours={14, 15, 16, 17})),
        ("skip 10-17 (midday+NY)", make_trend(block_hours={10, 11, 12, 13, 14, 15, 16, 17})),
        ("London-only 7-9", make_trend(allow_hours={7, 8, 9})),
    ]
    print(f"\n{'='*82}\nFILTER WAKTU TREND | {args.symbol} H1 | {len(bars)} bar (~{args.bt_days//365}thn) | $10000\n{'='*82}")
    print(f"\n{'varian':24} {'trade':>6} {'WR%':>6} {'ret%':>8} {'PF':>5} {'maxDD%':>7} {'WF pos':>7} {'WFworst%':>9} {'compound%':>10}")
    print("-"*82)
    for name, st in variants:
        r = bt(bars, st, si)
        pos, K, worst, comp = wf(bars, st, si)
        print(f"{name:24} {r.trades:>6} {r.win_rate:6.1f} {r.ret_pct:+8.1f} {r.pf:5.2f} "
              f"{r.max_dd_pct:7.1f} {pos:>4}/{K} {worst:+9.1f} {comp:+10.1f}")
    print("\nFilter bagus = PF & WF-pos naik, maxDD & WF-worst turun, walau trade berkurang.\n")


if __name__ == "__main__":
    main()
