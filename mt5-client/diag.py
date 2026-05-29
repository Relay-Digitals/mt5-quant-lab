"""
diag.py — Bedah kenapa TREND profit di pair A tapi rugi di pair B.
Pisahkan biaya spread (gross vs net) + struktur TP/SL + avg win/loss.

Usage: python3 diag.py --symbols XAUUSD,XAGUSD,USDJPY
"""
from __future__ import annotations
import argparse
from mt5_scalper import MT5Api
from backtest_lab import make_trend, run_backtest, fetch_bars


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="XAUUSD,XAGUSD,USDJPY")
    ap.add_argument("--bt-days", type=int, default=1825)
    ap.add_argument("--api", default="http://192.168.0.116:8000")
    args = ap.parse_args()
    api = MT5Api(args.api, timeout=180)

    print(f"\nDIAGNOSTIK TREND 5thn | $10000 | gross=tanpa spread, net=dgn spread")
    print(f"{'pair':9} {'trade':>6} {'WR%':>6} {'TP':>5} {'SL':>5} {'avgWin$':>9} {'avgLoss$':>9} "
          f"{'gross%':>8} {'net%':>8} {'spreadDrag%':>11}")
    print("-" * 92)
    for sym in [s.strip() for s in args.symbols.split(",")]:
        try:
            si = api.symbol_info(sym)
            bars, _ = fetch_bars(api, sym, "H1", args.bt_days, 2000)
        except Exception as e:
            print(f"{sym:9} err {str(e)[:50]}"); continue
        rn = run_backtest(bars, make_trend(), si, balance=10000, risk_pct=1.0,
                          max_risk_pct=6.0, min_atr=0.0, max_spread_pct=99.0)
        bars0 = [{**b, "spread": 0} for b in bars]
        rg = run_backtest(bars0, make_trend(), si, balance=10000, risk_pct=1.0,
                          max_risk_pct=6.0, min_atr=0.0, max_spread_pct=99.0)
        tl = rn.trade_log or []
        tp = sum(1 for t in tl if t["result"] == "TP")
        sl = sum(1 for t in tl if t["result"] == "SL")
        wins = [t["net"] for t in tl if t["net"] > 0]
        loss = [t["net"] for t in tl if t["net"] <= 0]
        aw = sum(wins) / len(wins) if wins else 0
        al = sum(loss) / len(loss) if loss else 0
        drag = rg.ret_pct - rn.ret_pct
        print(f"{sym:9} {rn.trades:>6} {rn.win_rate:6.1f} {tp:>5} {sl:>5} {aw:>9.2f} {al:>9.2f} "
              f"{rg.ret_pct:>+8.1f} {rn.ret_pct:>+8.1f} {drag:>11.1f}")
    print("\nKalau gross% juga NEGATIF → masalah STRATEGI (whipsaw/no-follow-through), bukan spread.")
    print("Kalau gross% positif tapi net% negatif → masalah SPREAD/biaya.")
    print("avgWin/avgLoss + TP:SL menunjukkan apakah winner cukup besar menutup banyak loss.\n")


if __name__ == "__main__":
    main()
