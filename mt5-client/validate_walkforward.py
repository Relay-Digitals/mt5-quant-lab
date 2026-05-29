"""
validate_walkforward.py — Validasi out-of-sample kandidat top dari sweep.

Tarik history H1 sedalam mungkin (≤10.000 bar) per pair, pecah jadi K window
berurutan, jalankan KETIGA strategi di tiap window. Tujuan: cek apakah edge
KONSISTEN antar-waktu (robust) atau cuma hoki di satu sampel (overfit/selection bias).

Pair robust = strategi designated-nya POSITIF di mayoritas window.

Usage:
  python3 validate_walkforward.py --tf H1 --windows 6 --balance 3000
  python3 validate_walkforward.py --symbols XAGUSD,USDJPY --windows 8
"""
from __future__ import annotations

import argparse
import datetime as dt

from mt5_scalper import MT5Api
from backtest_lab import make_trend, make_maosc, make_meanrev, run_backtest

# kandidat top dari sweep + strategi terbaiknya
CANDIDATES = {
    "XAGUSD": "TREND",
    "USDJPY": "MAOSC",
    "EURJPY": "TREND",
    "UK100":  "TREND",
    "NZDUSD": "MAOSC",
}
MAKERS = {"TREND": make_trend, "MAOSC": make_maosc, "MEANREV": make_meanrev}
NAMES = ["TREND", "MAOSC", "MEANREV"]


def main():
    p = argparse.ArgumentParser(description="Walk-forward validation kandidat")
    p.add_argument("--tf", default="H1")
    p.add_argument("--windows", type=int, default=6)
    p.add_argument("--bars", type=int, default=10000)
    p.add_argument("--balance", type=float, default=3000.0)
    p.add_argument("--risk", type=float, default=1.0)
    p.add_argument("--max-risk", type=float, default=6.0)
    p.add_argument("--max-spread-pct", type=float, default=12.0)
    p.add_argument("--symbols", default=None, help="override daftar (pisah koma)")
    p.add_argument("--api", default="http://192.168.0.116:8000")
    args = p.parse_args()

    api = MT5Api(args.api, timeout=180)
    avail = {s["name"] for s in api._get("/api/symbols", limit=10000)["items"]}

    if args.symbols:
        cand = {s.strip(): CANDIDATES.get(s.strip(), "TREND")
                for s in args.symbols.split(",")}
    else:
        cand = CANDIDATES

    K = args.windows
    print(f"\n{'='*94}")
    print(f"WALK-FORWARD VALIDATION | {args.tf} | {K} window | balance ${args.balance:.0f} "
          f"| risk {args.risk}% cap {args.max_risk}% | spread≤{args.max_spread_pct}%")
    print('='*94)

    summary = []  # (sym, designated, pos_count, mean_ret, min_ret)

    for sym, desig in cand.items():
        if sym not in avail:
            print(f"\n{sym}: tidak tersedia di broker, skip")
            continue
        sinfo = api.symbol_info(sym)
        bars = api.bars(sym, args.tf, args.bars)
        n = len(bars)
        if n < K * 200:
            print(f"\n{sym}: data kurang ({n} bar), skip")
            continue
        w = n // K

        print(f"\n── {sym}  (designated: {desig})  |  {n} bar, {K} window ×{w} bar ──")
        hdr = f"  {'window':22} {'TREND%':>9} {'MAOSC%':>9} {'MEANREV%':>10}"
        print(hdr)

        per_strat = {nm: [] for nm in NAMES}
        for k in range(K):
            seg = bars[k * w:(k + 1) * w] if k < K - 1 else bars[k * w:]
            t0 = dt.datetime.fromtimestamp(seg[0]["time"]).strftime("%y-%m-%d")
            t1 = dt.datetime.fromtimestamp(seg[-1]["time"]).strftime("%y-%m-%d")
            rets = {}
            for nm in NAMES:
                r = run_backtest(seg, MAKERS[nm](), sinfo, balance=args.balance,
                                 risk_pct=args.risk, max_risk_pct=args.max_risk,
                                 min_atr=0.0, max_spread_pct=args.max_spread_pct)
                rets[nm] = r.ret_pct
                per_strat[nm].append(r.ret_pct)
            mark = lambda nm: ("*" if nm == desig else " ")
            print(f"  W{k+1} {t0}→{t1:10}  "
                  f"{rets['TREND']:+8.2f}{mark('TREND')}"
                  f"{rets['MAOSC']:+8.2f}{mark('MAOSC')}"
                  f"{rets['MEANREV']:+9.2f}{mark('MEANREV')}")

        # ringkasan per pair
        print(f"  {'-'*52}")
        for nm in NAMES:
            rs = per_strat[nm]
            pos = sum(1 for x in rs if x > 0)
            mean = sum(rs) / len(rs)
            tag = "  ← designated" if nm == desig else ""
            print(f"  {nm:9} mean {mean:+6.2f}% | positif {pos}/{K} | "
                  f"min {min(rs):+.1f}% max {max(rs):+.1f}%{tag}")
        dr = per_strat[desig]
        summary.append((sym, desig, sum(1 for x in dr if x > 0), sum(dr)/len(dr), min(dr)))

    # ── verdict ──
    print(f"\n{'='*94}")
    print("VERDICT (strategi designated tiap pair)")
    print('='*94)
    print(f"  {'PAIR':10} {'strat':8} {'positif':>9} {'mean%':>8} {'worst%':>8}  robust?")
    print("  " + "-" * 60)
    summary.sort(key=lambda x: (x[2], x[3]), reverse=True)
    for sym, desig, pos, mean, mn in summary:
        robust = "✅ ROBUST" if pos >= K * 0.67 and mean > 0 else \
                 ("🟡 mixed" if pos >= K * 0.5 else "❌ rapuh")
        print(f"  {sym:10} {desig:8} {pos:>6}/{K} {mean:+8.2f} {mn:+8.2f}  {robust}")
    print("\nKriteria robust: strategi positif di ≥2/3 window DAN mean > 0.")
    print("Catatan: bar-level, spread per-bar dihitung, slippage/swap diabaikan. "
          "Window berurutan (bukan overlap).\n")


if __name__ == "__main__":
    main()
