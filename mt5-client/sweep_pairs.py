"""
sweep_pairs.py — Sapu 3 strategi research-backed ke banyak pair broker (data dari MT5 API).

Untuk tiap pair: jalankan TREND / MAOSC / MEANREV, ambil yang terbaik, lalu ranking
semua pair berdasar return strategi terbaiknya. Sizing benar per-instrumen (pakai
symbol_info masing-masing: point, tick_value, volume_min).

Usage:
  python3 sweep_pairs.py --tf H1 --bt-days 300 --balance 3000
  python3 sweep_pairs.py --tf M15 --bt-days 60 --balance 1000 --preset forex
  python3 sweep_pairs.py --symbols EURUSD,XAUUSD,BTCUSD --tf H1 --bt-days 200
"""
from __future__ import annotations

import argparse

from mt5_scalper import MT5Api
from backtest_lab import (make_trend, make_maosc, make_meanrev, run_backtest, fetch_bars)

PRESETS = {
    "forex": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
              "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURAUD", "CHFJPY", "AUDNZD"],
    "metals": ["XAUUSD", "XAGUSD"],
    "energy": ["USOIL", "UKOIL", "XNGUSD"],
    "crypto": ["BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "SOLUSD", "BNBUSD"],
    "index": ["US30", "USTEC", "US500", "DE40", "UK100", "JP225", "USTEC.cash"],
}


def main():
    p = argparse.ArgumentParser(description="Sweep 3 strategi ke banyak pair")
    p.add_argument("--tf", default="H1")
    p.add_argument("--bt-days", type=int, default=300)
    p.add_argument("--balance", type=float, default=3000.0)
    p.add_argument("--risk", type=float, default=1.0)
    p.add_argument("--max-risk", type=float, default=6.0)
    p.add_argument("--max-spread-pct", type=float, default=12.0)
    p.add_argument("--atr-period", type=int, default=14)
    p.add_argument("--preset", default="all", help="forex|metals|energy|crypto|index|all")
    p.add_argument("--symbols", default=None, help="daftar manual, pisah koma")
    p.add_argument("--api", default="http://192.168.0.116:8000")
    args = p.parse_args()

    api = MT5Api(args.api, timeout=180)

    # daftar pair yang benar-benar ada di broker
    avail = {s["name"] for s in api._get("/api/symbols", limit=10000)["items"]}

    if args.symbols:
        wanted = [s.strip() for s in args.symbols.split(",")]
    elif args.preset == "all":
        wanted = sum((PRESETS[k] for k in ["forex", "metals", "energy", "crypto", "index"]), [])
    else:
        wanted = PRESETS.get(args.preset, [])
    symbols = [s for s in wanted if s in avail]
    missing = [s for s in wanted if s not in avail]

    strat_makers = [make_trend, make_maosc, make_meanrev]

    print(f"\n{'='*92}")
    print(f"SWEEP {len(symbols)} pair | {args.tf} | {args.bt_days} hari | balance ${args.balance:.0f} "
          f"| risk {args.risk}% cap {args.max_risk}% | spread≤{args.max_spread_pct}%")
    if missing:
        print(f"(tidak tersedia di broker, dilewati: {', '.join(missing)})")
    print('='*92)

    rows = []  # (symbol, best_name, best_ret, all_results_dict)
    for sym in symbols:
        try:
            sinfo = api.symbol_info(sym)
            bars, _ = fetch_bars(api, sym, args.tf, args.bt_days, 2000)
            if len(bars) < 200:
                print(f"  {sym:12} data kurang ({len(bars)} bar), skip")
                continue
            res = {}
            for mk in strat_makers:
                s = mk()
                r = run_backtest(bars, s, sinfo, balance=args.balance, atr_period=args.atr_period,
                                 risk_pct=args.risk, max_risk_pct=args.max_risk,
                                 min_atr=0.0, max_spread_pct=args.max_spread_pct)
                res[s.name] = r
            best = max(res.values(), key=lambda r: r.ret_pct)
            best_name = [k for k, v in res.items() if v is best][0]
            rows.append((sym, best_name, best.ret_pct, res, len(bars)))
            print(f"  ✓ {sym:12} ({len(bars)} bar) best={best_name} {best.ret_pct:+.2f}%")
        except Exception as e:
            print(f"  ✗ {sym:12} error: {str(e)[:70]}")

    # ── ranking ──
    rows.sort(key=lambda x: x[2], reverse=True)
    print(f"\n{'='*92}")
    print("RANKING (per pair: return strategi TERBAIK)")
    print('='*92)
    hdr = (f"{'PAIR':12} {'best':8} {'ret%':>8} {'WR%':>6} {'PF':>5} {'DD%':>6} "
           f"| {'TREND%':>8} {'MAOSC%':>8} {'MEANREV%':>9}")
    print(hdr); print("-" * len(hdr))
    for sym, bn, br, res, nb in rows:
        t, m, mr = res["TREND"], res["MAOSC"], res["MEANREV"]
        b = res[bn]
        print(f"{sym:12} {bn:8} {br:+8.2f} {b.win_rate:6.1f} {b.pf:5.2f} {b.max_dd_pct:6.1f} "
              f"| {t.ret_pct:+8.2f} {m.ret_pct:+8.2f} {mr.ret_pct:+9.2f}")

    # ── agregat per strategi ──
    print(f"\n{'='*92}")
    print("AGREGAT per strategi (rata-rata semua pair)")
    print('='*92)
    for name in ["TREND", "MAOSC", "MEANREV"]:
        rs = [res[name] for _, _, _, res, _ in rows]
        if not rs:
            continue
        avg_ret = sum(r.ret_pct for r in rs) / len(rs)
        avg_pf = sum(r.pf for r in rs if r.pf != float("inf")) / max(1, len(rs))
        avg_dd = sum(r.max_dd_pct for r in rs) / len(rs)
        wins = sum(1 for r in rs if r.ret_pct > 0)
        print(f"  {name:9} avg return {avg_ret:+6.2f}% | avg PF {avg_pf:.2f} | "
              f"avg maxDD {avg_dd:.1f}% | profitable di {wins}/{len(rs)} pair")
    print("\nCatatan: bar-level, biaya spread dihitung, slippage/swap diabaikan. "
          "Param DEFAULT (belum dioptimasi). Sampel terbatas history broker.\n")


if __name__ == "__main__":
    main()
