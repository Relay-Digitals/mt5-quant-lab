"""
walk_forward_optimize.py — Walk-Forward Optimization (WFO) anti-overfit.

Metodologi:
  - Bagi history jadi M segmen berurutan.
  - Tiap FOLD: optimasi param di segmen IN-SAMPLE (train), lalu uji param terbaik
    di segmen OUT-OF-SAMPLE (test) berikutnya yang BELUM dilihat.
  - Performa OOS gabungan = ekspektasi realistis (bukan hasil overfit).
  - Bandingkan vs param DEFAULT untuk lihat apakah optimasi benar2 menambah nilai.

Objektif optimasi: return tertinggi di train DENGAN minimal N trade (hindari hoki sampel kecil).

Usage:
  python3 walk_forward_optimize.py --symbol USDJPY --strat MAOSC --tf H1 --segments 7
"""
from __future__ import annotations

import argparse
import datetime as dt
import itertools

from mt5_scalper import MT5Api
from backtest_lab import make_maosc, make_trend, run_backtest

# ── grid param per strategi ──
GRIDS = {
    "MAOSC": dict(
        fast=[5, 8, 10, 15], slow=[20, 30, 50], rsi_p=[14],
        sl_atr=[1.0, 1.5, 2.0], tp_atr=[1.5, 2.0, 3.0],
    ),
    "TREND": dict(
        don=[10, 20, 30], trend_sma=[50, 100], rsi_p=[0],  # rsi_p dummy
        sl_atr=[1.0, 1.5, 2.0], tp_atr=[2.0, 3.0, 4.0],
    ),
}
DEFAULTS = {
    "MAOSC": dict(fast=10, slow=30, rsi_p=14, sl_atr=1.2, tp_atr=1.8),
    "TREND": dict(don=20, trend_sma=50, sl_atr=1.5, tp_atr=3.0),
}


def build(strat, params):
    if strat == "MAOSC":
        return make_maosc(fast=params["fast"], slow=params["slow"], rsi_p=params["rsi_p"],
                          sl_atr=params["sl_atr"], tp_atr=params["tp_atr"])
    return make_trend(don=params["don"], trend_sma=params["trend_sma"],
                      sl_atr=params["sl_atr"], tp_atr=params["tp_atr"])


def grid_combos(strat):
    g = GRIDS[strat]
    keys = list(g.keys())
    out = []
    for vals in itertools.product(*[g[k] for k in keys]):
        d = dict(zip(keys, vals))
        if strat == "MAOSC" and d["fast"] >= d["slow"]:
            continue
        out.append(d)
    return out


def fmt_params(strat, p):
    if strat == "MAOSC":
        return f"f{p['fast']}/s{p['slow']} SL{p['sl_atr']} TP{p['tp_atr']}"
    return f"don{p['don']}/sma{p['trend_sma']} SL{p['sl_atr']} TP{p['tp_atr']}"


def main():
    ap = argparse.ArgumentParser(description="Walk-forward optimization")
    ap.add_argument("--symbol", default="USDJPY")
    ap.add_argument("--strat", default="MAOSC", choices=["MAOSC", "TREND"])
    ap.add_argument("--tf", default="H1")
    ap.add_argument("--bars", type=int, default=10000)
    ap.add_argument("--segments", type=int, default=7)
    ap.add_argument("--balance", type=float, default=3000.0)
    ap.add_argument("--risk", type=float, default=1.0)
    ap.add_argument("--max-risk", type=float, default=6.0)
    ap.add_argument("--max-spread-pct", type=float, default=12.0)
    ap.add_argument("--min-trades", type=int, default=8, help="min trade train agar param valid")
    ap.add_argument("--api", default="http://192.168.0.116:8000")
    args = ap.parse_args()

    api = MT5Api(args.api, timeout=180)
    sinfo = api.symbol_info(args.symbol)
    bars = api.bars(args.symbol, args.tf, args.bars)
    combos = grid_combos(args.strat)
    M = args.segments
    seg = len(bars) // M

    def bt(segment, params):
        return run_backtest(segment, build(args.strat, params), sinfo, balance=args.balance,
                            risk_pct=args.risk, max_risk_pct=args.max_risk,
                            min_atr=0.0, max_spread_pct=args.max_spread_pct)

    print(f"\n{'='*92}")
    print(f"WALK-FORWARD OPTIMIZATION | {args.symbol} {args.strat} | {args.tf} | "
          f"{len(bars)} bar, {M} segmen ×{seg}")
    print(f"Grid: {len(combos)} kombinasi | balance ${args.balance:.0f} | "
          f"objektif: max return train (≥{args.min_trades} trade)")
    print('='*92)
    print(f"\n{'fold':5} {'train→test (OOS)':24} {'param terbaik (IS)':26} "
          f"{'IS%':>7} {'OOS%':>8} {'OOStr':>6} {'def-OOS%':>9}")
    print("-" * 92)

    oos_opt, oos_def = [], []
    param_pick = []
    for i in range(M - 1):
        train = bars[i * seg:(i + 1) * seg]
        test = bars[(i + 1) * seg:(i + 2) * seg] if i + 2 <= M else bars[(i + 1) * seg:]
        # optimasi di train
        best = None
        for p in combos:
            r = bt(train, p)
            if r.trades < args.min_trades:
                continue
            if best is None or r.ret_pct > best[1].ret_pct:
                best = (p, r)
        if best is None:
            print(f"F{i+1:<4} (train tak ada param valid ≥{args.min_trades} trade)")
            continue
        bp, br = best
        # uji OOS
        ro = bt(test, bp)
        rd = bt(test, DEFAULTS[args.strat])
        oos_opt.append(ro.ret_pct); oos_def.append(rd.ret_pct)
        param_pick.append(bp)
        t0 = dt.datetime.fromtimestamp(test[0]["time"]).strftime("%y-%m-%d")
        t1 = dt.datetime.fromtimestamp(test[-1]["time"]).strftime("%y-%m-%d")
        print(f"F{i+1:<4} {t0}→{t1:14} {fmt_params(args.strat, bp):26} "
              f"{br.ret_pct:+7.2f} {ro.ret_pct:+8.2f} {ro.trades:>6} {rd.ret_pct:+9.2f}")

    # ── ringkasan OOS ──
    print("-" * 92)
    if oos_opt:
        n = len(oos_opt)
        mo = sum(oos_opt) / n; md = sum(oos_def) / n
        po = sum(1 for x in oos_opt if x > 0); pd = sum(1 for x in oos_def if x > 0)
        # compound OOS
        comp = lambda rs: (eval_compound(rs))
        print(f"\nHASIL OUT-OF-SAMPLE ({n} fold):")
        print(f"  OPTIMIZED : mean {mo:+.2f}%/fold | positif {po}/{n} | "
              f"total compound {eval_compound(oos_opt):+.2f}% | worst {min(oos_opt):+.2f}%")
        print(f"  DEFAULT   : mean {md:+.2f}%/fold | positif {pd}/{n} | "
              f"total compound {eval_compound(oos_def):+.2f}% | worst {min(oos_def):+.2f}%")
        verdict = ("✅ optimasi MENAMBAH nilai" if mo > md and po >= pd
                   else "⚠️ optimasi TIDAK lebih baik dari default (kemungkinan overfit)")
        print(f"  → {verdict}")
        # stabilitas param
        print("\nStabilitas param terpilih antar-fold:")
        keys = [k for k in param_pick[0].keys() if k != "rsi_p"]
        for k in keys:
            vals = [p[k] for p in param_pick]
            uniq = {}
            for v in vals:
                uniq[v] = uniq.get(v, 0) + 1
            common = sorted(uniq.items(), key=lambda x: -x[1])
            print(f"  {k:10}: " + ", ".join(f"{v}×{c}" for v, c in common))
        # rekomendasi: param paling sering
        rec = {}
        for k in param_pick[0].keys():
            vals = [p[k] for p in param_pick]
            rec[k] = max(set(vals), key=vals.count)
        print(f"\nRekomendasi param (paling sering terpilih): {fmt_params(args.strat, rec)}")
    print("\nCatatan: OOS = data yang TIDAK dipakai optimasi (ekspektasi realistis). "
          "Bar-level, spread dihitung, slippage/swap diabaikan.\n")


def eval_compound(rets):
    bal = 1.0
    for r in rets:
        bal *= (1 + r / 100)
    return (bal - 1) * 100


if __name__ == "__main__":
    main()
