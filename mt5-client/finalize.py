"""
finalize.py — (1) Eksplor mean-reversion untuk XAUUSD (varian param + timeframe),
(2) patenkan USDJPY & AUDJPY (TREND), (3) journal semua + reindex RAG.

Usage: python3 finalize.py
"""
from __future__ import annotations
import datetime as dt
from mt5_scalper import MT5Api
from backtest_lab import make_trend, make_meanrev, run_backtest, fetch_bars
import journal, rag

API = "http://192.168.0.116:8000"


def journal_run(api, sym, tf, strat, label, note_extra=""):
    si = api.symbol_info(sym)
    bars, _ = fetch_bars(api, sym, tf, 1825, 2000)
    if len(bars) < 500:
        print(f"  {sym} {tf} {label}: data kurang"); return None
    r = run_backtest(bars, strat, si, balance=10000, risk_pct=1.0, max_risk_pct=6.0,
                     min_atr=0.0, max_spread_pct=12.0)
    pfrom = dt.datetime.fromtimestamp(bars[0]["time"]).isoformat()
    pto = dt.datetime.fromtimestamp(bars[-1]["time"]).isoformat()
    notes = f"{label}. {note_extra} {'PROFIT' if r.ret_pct>0 else 'RUGI'} PF{r.pf:.2f} DD{r.max_dd_pct:.0f}%."
    rid = journal.log_run(source="backtest", strategy=strat.name, symbol=sym, timeframe=tf,
        params={"label": label, "desc": strat.desc, "sl_atr": strat.sl_atr, "tp_atr": strat.tp_atr},
        start_balance=r.start_bal, end_balance=r.end_bal, trades=r.trades, wins=r.wins,
        losses=r.losses, win_rate=r.win_rate, ret_pct=r.ret_pct,
        profit_factor=(r.pf if r.pf != float("inf") else 999), max_dd_pct=r.max_dd_pct,
        period_from=pfrom, period_to=pto, notes=notes)
    journal.log_trades(rid, "backtest", strat.name, sym, tf, r.trade_log or [])
    print(f"  {sym:8} {tf:3} {label:28} ret {r.ret_pct:+7.1f}% PF {r.pf:.2f} DD {r.max_dd_pct:4.0f}% "
          f"({r.trades}tr WR{r.win_rate:.0f}%)")
    return r.ret_pct


def main():
    api = MT5Api(API, timeout=180)
    journal.init()

    print("\n[1] XAUUSD — eksplor MEAN-REVERSION (cari yg cocok utk karakter choppy gold):")
    xau = [
        ("H1", make_meanrev(), "MR default bb20/2.0 RSI30-70"),
        ("H1", make_meanrev(sl_atr=2.0, tp_atr=1.0), "MR quick-revert SL2/TP1"),
        ("H1", make_meanrev(mult=2.5, lo_rsi=25, hi_rsi=75), "MR tight bb2.5 RSI25-75"),
        ("H4", make_meanrev(), "MR default @H4"),
        ("H4", make_meanrev(sl_atr=2.0, tp_atr=1.0), "MR quick-revert @H4"),
        ("D1", make_meanrev(), "MR default @D1"),
    ]
    best = None
    for tf, st, lbl in xau:
        rp = journal_run(api, "XAUUSD", tf, st, lbl)
        if rp is not None and (best is None or rp > best[1]):
            best = (lbl, rp)
    if best:
        print(f"  → Terbaik XAUUSD MR: {best[0]} ({best[1]:+.1f}%) "
              f"{'✅ ada yg profit' if best[1] > 0 else '❌ semua rugi → gold sulit di H1/H4/D1'}")

    print("\n[2] PATENKAN pemenang TREND (5thn, tervalidasi):")
    journal_run(api, "USDJPY", "H1", make_trend(allow_hours={7, 8, 9}),
                "PATEN USDJPY TREND London-only", "Lolos time-holdout.")
    journal_run(api, "AUDJPY", "H1", make_trend(), "PATEN AUDJPY TREND base", "Portofolio inti.")

    print("\n[3] Reindex RAG (Meilisearch)...")
    n = rag.reindex_runs()
    print(f"  ✓ {n} run ter-index ke RAG (searchable via analyze.py ask).")
    print("\nSelesai. Semua tersimpan di journal (TimescaleDB) + RAG (Meili).\n")


if __name__ == "__main__":
    main()
