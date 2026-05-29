"""
test_holdout.py — Time-split holdout: uji filter waktu di TRAIN (60% awal) lalu di
HOLDOUT (40% akhir, belum tersentuh). Edge nyata = menang di HOLDOUT, bukan cuma train.

Usage: python3 test_holdout.py --symbols USDJPY,XAUUSD,AUDJPY
"""
from __future__ import annotations
import argparse, datetime as dt
from mt5_scalper import MT5Api
from backtest_lab import make_trend, run_backtest, fetch_bars


def bt(bars, st, si, bal=10000):
    return run_backtest(bars, st, si, balance=bal, risk_pct=1.0, max_risk_pct=6.0,
                        min_atr=0.0, max_spread_pct=12.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="USDJPY,XAUUSD,AUDJPY")
    ap.add_argument("--bt-days", type=int, default=1825)
    ap.add_argument("--api", default="http://192.168.0.116:8000")
    args = ap.parse_args()
    api = MT5Api(args.api, timeout=180)
    syms = [s.strip() for s in args.symbols.split(",")]

    variants = [
        ("base", make_trend()),
        ("London-only 7-9", make_trend(allow_hours={7, 8, 9})),
        ("skip-NY 14-17", make_trend(block_hours={14, 15, 16, 17})),
    ]
    for sym in syms:
        try:
            si = api.symbol_info(sym)
            bars, _ = fetch_bars(api, sym, "H1", args.bt_days, 2000)
        except Exception as e:
            print(f"\n{sym}: err {str(e)[:60]}"); continue
        if len(bars) < 3000:
            print(f"\n{sym}: data kurang ({len(bars)} bar)"); continue
        sp = int(len(bars) * 0.6)
        train, hold = bars[:sp], bars[sp:]
        t0 = dt.datetime.fromtimestamp(train[0]['time']).strftime('%y-%m')
        t1 = dt.datetime.fromtimestamp(train[-1]['time']).strftime('%y-%m')
        h0 = dt.datetime.fromtimestamp(hold[0]['time']).strftime('%y-%m')
        h1 = dt.datetime.fromtimestamp(hold[-1]['time']).strftime('%y-%m')
        print(f"\n{'='*78}\n{sym} H1 | TRAIN {t0}→{t1} ({len(train)}bar) | HOLDOUT {h0}→{h1} ({len(hold)}bar)\n{'='*78}")
        print(f"{'varian':18} | {'TRAIN ret%':>10} {'PF':>5} {'DD%':>6} | {'HOLDOUT ret%':>12} {'PF':>5} {'DD%':>6}")
        print("-"*78)
        base_hold = None
        for name, st in variants:
            rt = bt(train, st, si); rh = bt(hold, st, si)
            if name == "base":
                base_hold = rh.ret_pct
            print(f"{name:18} | {rt.ret_pct:>+10.1f} {rt.pf:>5.2f} {rt.max_dd_pct:>6.1f} | "
                  f"{rh.ret_pct:>+12.1f} {rh.pf:>5.2f} {rh.max_dd_pct:>6.1f}")
        # verdict
        print(f"\n  → Edge filter NYATA hanya jika ret% HOLDOUT-nya > base holdout ({base_hold:+.1f}%) DAN PF>1.")
    print("\nKalau filter menang di TRAIN tapi kalah/tipis di HOLDOUT = OVERFIT (curve-fit ke masa lalu).\n")


if __name__ == "__main__":
    main()
