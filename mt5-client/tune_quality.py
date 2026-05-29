"""
tune_quality.py — Cari kombinasi filter MAOSC-Quality terbaik (part a), lalu
validasi kombinasi terpilih ke banyak pair (part b, out-of-sample).

Usage:
  python3 tune_quality.py combos --symbol USDJPY            # part a
  python3 tune_quality.py pairs --macd --adx 25             # part b: combo ke banyak pair
"""
from __future__ import annotations
import argparse, statistics
from mt5_scalper import MT5Api
from backtest_lab import make_maosc_quality, run_backtest, fetch_bars

PAIRS = ["USDJPY", "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "EURJPY", "USDCAD", "XAGUSD", "XAUUSD"]

COMBOS = [
    ("base (no filter)",       dict(use_macd=False, adx_min=0,  skip_stoch_low=False, skip_london=False)),
    ("MACD only",              dict(use_macd=True,  adx_min=0,  skip_stoch_low=False, skip_london=False)),
    ("ADX>25 only",            dict(use_macd=False, adx_min=25, skip_stoch_low=False, skip_london=False)),
    ("noStoch<20 only",        dict(use_macd=False, adx_min=0,  skip_stoch_low=True,  skip_london=False)),
    ("noLondon only",          dict(use_macd=False, adx_min=0,  skip_stoch_low=False, skip_london=True)),
    ("MACD+ADX",               dict(use_macd=True,  adx_min=25, skip_stoch_low=False, skip_london=False)),
    ("MACD+ADX+noStoch",       dict(use_macd=True,  adx_min=25, skip_stoch_low=True,  skip_london=False)),
    ("MACD+ADX+noLondon",      dict(use_macd=True,  adx_min=25, skip_stoch_low=False, skip_london=True)),
    ("ALL 4 filter",           dict(use_macd=True,  adx_min=25, skip_stoch_low=True,  skip_london=True)),
]


def bt(bars, strat, si, bal=10000):
    return run_backtest(bars, strat, si, balance=bal, risk_pct=1.0, max_risk_pct=6.0,
                        min_atr=0.0, max_spread_pct=12.0)


def wf(bars, strat, si, K=10, bal=10000):
    w = len(bars) // K; rets = []
    for k in range(K):
        seg = bars[k*w:(k+1)*w] if k < K-1 else bars[k*w:]
        rets.append(bt(seg, strat, si, bal).ret_pct)
    pos = sum(1 for x in rets if x > 0)
    comp = 1.0
    for x in rets: comp *= (1 + x/100)
    return pos, K, statistics.mean(rets), min(rets), (comp-1)*100


def cmd_combos(args):
    api = MT5Api(args.api, timeout=180); si = api.symbol_info(args.symbol)
    bars, _ = fetch_bars(api, args.symbol, "H1", args.bt_days, 2000)
    print(f"\nTUNING FILTER | {args.symbol} H1 | {len(bars)} bar (~{args.bt_days//365}thn) | $10000")
    print(f"{'kombinasi':22} {'trade':>6} {'WR%':>6} {'ret%':>7} {'PF':>5} {'DD%':>6} {'ret/DD':>7} {'WF pos':>7} {'WFworst%':>9}")
    print("-"*90)
    for name, kw in COMBOS:
        s = make_maosc_quality(**kw)
        r = bt(bars, s, si)
        pos, K, mean, worst, comp = wf(bars, s, si)
        rdd = r.ret_pct / r.max_dd_pct if r.max_dd_pct else 0
        print(f"{name:22} {r.trades:>6} {r.win_rate:6.1f} {r.ret_pct:+7.1f} {r.pf:5.2f} "
              f"{r.max_dd_pct:6.1f} {rdd:7.2f} {pos:>4}/{K} {worst:+9.1f}")
    print("\nSweet spot = ret/DD tinggi + trade cukup (≥150) + WF konsisten + worst-window kecil.")


def cmd_pairs(args):
    api = MT5Api(args.api, timeout=180)
    kw = dict(use_macd=args.macd, adx_min=args.adx, skip_stoch_low=args.stoch, skip_london=args.london)
    label = f"MACD={args.macd} ADX>{args.adx} noStoch={args.stoch} noLondon={args.london}"
    print(f"\nVALIDASI OUT-OF-SAMPLE ke {len(PAIRS)} pair | filter: {label}")
    print(f"{'pair':9} {'trade':>6} {'WR%':>6} {'ret%':>7} {'PF':>5} {'DD%':>6} {'ret/DD':>7} {'WF pos':>7}")
    print("-"*64)
    base_better = qual_better = 0
    for sym in PAIRS:
        try:
            si = api.symbol_info(sym)
            bars, _ = fetch_bars(api, sym, "H1", args.bt_days, 2000)
            if len(bars) < 1000:
                print(f"{sym:9} data kurang"); continue
            sq = make_maosc_quality(**kw)
            sb = make_maosc_quality(use_macd=False, adx_min=0, skip_stoch_low=False, skip_london=False)
            rq = bt(bars, sq, si); rb = bt(bars, sb, si)
            pos, K, mean, worst, comp = wf(bars, sq, si)
            rdd = rq.ret_pct/rq.max_dd_pct if rq.max_dd_pct else 0
            rdd_b = rb.ret_pct/rb.max_dd_pct if rb.max_dd_pct else 0
            if rdd > rdd_b: qual_better += 1
            else: base_better += 1
            mark = " ✅" if rdd > rdd_b else ""
            print(f"{sym:9} {rq.trades:>6} {rq.win_rate:6.1f} {rq.ret_pct:+7.1f} {rq.pf:5.2f} "
                  f"{rq.max_dd_pct:6.1f} {rdd:7.2f} {pos:>4}/{K}{mark}")
        except Exception as e:
            print(f"{sym:9} err: {str(e)[:50]}")
    print(f"\nFilter unggul (ret/DD) di {qual_better}/{qual_better+base_better} pair vs base.")
    print("✅ = filter naikkan risk-adjusted di pair itu (bukti pola umum, bukan overfit USDJPY).")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("combos"); c.add_argument("--symbol", default="USDJPY")
    c.add_argument("--bt-days", type=int, default=1825); c.add_argument("--api", default="http://192.168.0.116:8000")
    c.set_defaults(fn=cmd_combos)
    p = sub.add_parser("pairs")
    p.add_argument("--macd", action="store_true"); p.add_argument("--adx", type=int, default=0)
    p.add_argument("--stoch", action="store_true"); p.add_argument("--london", action="store_true")
    p.add_argument("--bt-days", type=int, default=1825); p.add_argument("--api", default="http://192.168.0.116:8000")
    p.set_defaults(fn=cmd_pairs)
    args = ap.parse_args(); args.fn(args)


if __name__ == "__main__":
    main()
