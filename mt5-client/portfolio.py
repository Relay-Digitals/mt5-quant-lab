"""
portfolio.py — Sintesis: tiap pair pakai strategi TERBAIK-nya (uji 5thn), gabung
jadi 1 equity curve diversifikasi, ukur konsistensi per tahun.

Kandidat strategi per pair: TREND, MAOSC, MAOSCQ (MAOSC + filter noStoch<20).
Pilih yg return 5thn > 0. Alokasi modal rata. Trade semua pair digabung kronologis.

Usage: python3 portfolio.py --capital 10000 --bt-days 1825
"""
from __future__ import annotations
import argparse, datetime as dt
from collections import defaultdict
from mt5_scalper import MT5Api
from backtest_lab import (make_trend, make_maosc, make_maosc_quality, make_meanrev,
                          run_backtest, fetch_bars)

CANDIDATE_PAIRS = ["USDJPY", "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "EURJPY",
                   "USDCAD", "AUDJPY", "EURGBP", "XAUUSD", "XAGUSD", "CHFJPY"]


def strategies():
    return [
        ("TREND", make_trend()),
        ("TREND-LON", make_trend(allow_hours={7, 8, 9})),
        ("MEANREV-EXT", make_meanrev(max_ext_atr=3.0)),
        ("MAOSCQ", make_maosc_quality(use_macd=False, adx_min=0, skip_stoch_low=True, skip_london=False)),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capital", type=float, default=10000)
    ap.add_argument("--bt-days", type=int, default=1825)
    ap.add_argument("--exclude", default="", help="pair dikecualikan, pisah koma")
    ap.add_argument("--api", default="http://192.168.0.116:8000")
    args = ap.parse_args()
    api = MT5Api(args.api, timeout=180)
    excl = {x.strip().upper() for x in args.exclude.split(",") if x.strip()}
    global CANDIDATE_PAIRS
    CANDIDATE_PAIRS = [p for p in CANDIDATE_PAIRS if p not in excl]
    if excl:
        print(f"(dikecualikan: {', '.join(sorted(excl))})")

    print(f"\n{'='*72}\nPORTOFOLIO SINTESIS | modal ${args.capital:.0f} | ~{args.bt_days//365} tahun\n{'='*72}")
    print("\n[1] Pilih strategi terbaik per pair (return 5thn > 0):")
    selected = []
    pair_bars = {}
    for sym in CANDIDATE_PAIRS:
        try:
            si = api.symbol_info(sym)
            bars, _ = fetch_bars(api, sym, "H1", args.bt_days, 2000)
            if len(bars) < 2000:
                print(f"  {sym:8} data kurang, skip"); continue
            pair_bars[sym] = (si, bars)
            best = None
            for nm, st in strategies():
                r = run_backtest(bars, st, si, balance=10000, risk_pct=1.0, max_risk_pct=6.0,
                                 min_atr=0.0, max_spread_pct=12.0)
                if best is None or r.ret_pct > best[2].ret_pct:
                    best = (nm, st, r)
            nm, st, r = best
            ok = r.ret_pct > 0 and r.pf > 1.0
            tag = "✓ MASUK" if ok else "✗ (rugi, skip)"
            print(f"  {sym:8} best={nm:7} ret {r.ret_pct:+7.1f}% PF {r.pf:.2f} DD {r.max_dd_pct:.0f}%  {tag}")
            if ok:
                selected.append((sym, nm, st))
        except Exception as e:
            print(f"  {sym:8} err: {str(e)[:50]}")

    if not selected:
        print("\nTidak ada pair profitable 5thn. Portofolio kosong."); return

    N = len(selected); alloc = args.capital / N
    print(f"\n[2] Portofolio: {N} pair, alokasi ${alloc:.0f}/pair")
    print("    " + ", ".join(f"{s}({n})" for s, n, _ in selected))

    # gabung semua trade kronologis + lacak per-pair
    all_trades = []
    pair_year = defaultdict(lambda: defaultdict(float))   # sym -> year -> pnl
    pair_dd = {}                                          # sym -> maxDD%
    pair_total = {}
    years_set = set()
    for sym, nm, st in selected:
        si, bars = pair_bars[sym]
        r = run_backtest(bars, st, si, balance=alloc, risk_pct=1.0, max_risk_pct=6.0,
                         min_atr=0.0, max_spread_pct=12.0)
        eq = alloc; pk = alloc; dd = 0.0
        for t in (r.trade_log or []):
            all_trades.append((t["exit_time"], t["net"], sym))
            yr = t["exit_time"][:4]; pair_year[sym][yr] += t["net"]; years_set.add(yr)
            eq += t["net"]; pk = max(pk, eq); dd = max(dd, (pk - eq) / pk * 100)
        pair_dd[sym] = dd; pair_total[sym] = eq - alloc
    all_trades.sort(key=lambda x: x[0])

    equity = args.capital; peak = equity; maxdd = 0.0
    yearly = defaultdict(float); yearly_n = defaultdict(int)
    for et, net, sym in all_trades:
        equity += net
        peak = max(peak, equity)
        maxdd = max(maxdd, (peak - equity) / peak * 100)
        yr = et[:4]; yearly[yr] += net; yearly_n[yr] += 1

    print(f"\n[3] Hasil portofolio gabungan ({len(all_trades)} trade):")
    print(f"    {'tahun':6} {'trade':>6} {'profit $':>10} {'return %':>9}")
    base = args.capital
    pos_years = 0
    for yr in sorted(yearly):
        pl = yearly[yr]; ret = pl / base * 100
        if pl > 0: pos_years += 1
        print(f"    {yr:6} {yearly_n[yr]:>6} {pl:>+10.0f} {ret:>+8.1f}%")
    total = equity - args.capital
    print(f"    {'-'*34}")
    print(f"    TOTAL  {len(all_trades):>6} {total:>+10.0f} {total/args.capital*100:>+8.1f}%")
    print(f"\n    Tahun profit: {pos_years}/{len(yearly)} | Max drawdown: {maxdd:.1f}%")
    print(f"    Saldo akhir: ${equity:,.0f} | rata-rata ${total/max(1,len(yearly)):+,.0f}/tahun")

    # ── breakdown per pair per tahun ──
    yrs = sorted(years_set)
    print(f"\n[4] BREAKDOWN per pair per tahun (profit $, alokasi ${alloc:.0f}/pair):")
    hdr = f"    {'pair':14}" + "".join(f"{y:>8}" for y in yrs) + f"{'TOTAL':>9} {'maxDD%':>7}"
    print(hdr); print("    " + "-" * (len(hdr) - 4))
    for sym, nm, st in selected:
        row = f"    {sym+'/'+nm:14}"
        for y in yrs:
            row += f"{pair_year[sym].get(y, 0.0):>+8.0f}"
        row += f"{pair_total[sym]:>+9.0f} {pair_dd[sym]:>7.1f}"
        print(row)
    # ranking penyumbang drawdown
    worst = sorted(selected, key=lambda x: pair_dd[x[0]], reverse=True)
    print("\n    Drawdown terbesar → terkecil:")
    for sym, nm, st in worst:
        neg_yrs = [y for y in yrs if pair_year[sym].get(y, 0) < 0]
        print(f"      {sym:8} maxDD {pair_dd[sym]:5.1f}% | total ${pair_total[sym]:+,.0f} | "
              f"tahun rugi: {', '.join(neg_yrs) if neg_yrs else '-'}")
    print("\nDiversifikasi berhasil kalau: tahun-profit naik & maxDD turun vs single-pair.")
    print("Pair dgn DD besar + total kecil/negatif = kandidat dikeluarkan dari portofolio.\n")


if __name__ == "__main__":
    main()
