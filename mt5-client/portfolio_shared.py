"""
portfolio_shared.py — Backtest portofolio di SATU akun bersama (realistis utk 1 akun live).
- Banyak pair bisa punya posisi terbuka BERSAMAAN, maks 1 posisi per pair.
- Sizing tiap entry = risk% dari TOTAL balance saat itu (compounding gabungan).
- Eksposur bisa menumpuk (kalau N pair terbuka, total risk ~ N×risk%).
- Opsional --max-open batasi jumlah posisi simultan.

Bandingkan dgn portfolio.py (sub-akun terpisah). Usage:
  python3 portfolio_shared.py --capital 10000 --risk 1 [--max-open 4]
"""
from __future__ import annotations
import argparse, datetime as dt
from collections import defaultdict
from mt5_scalper import MT5Api, calc_lot
from backtest_lab import (make_trend, make_meanrev, make_maosc_quality,
                          fetch_bars, atr_series)

# strategi terbaik per pair (dari portofolio gabungan tervalidasi)
ASSIGN = {
    "USDJPY": ("TREND-LON", lambda: make_trend(allow_hours={7, 8, 9})),
    "EURUSD": ("TREND-LON", lambda: make_trend(allow_hours={7, 8, 9})),
    "NZDUSD": ("TREND-LON", lambda: make_trend(allow_hours={7, 8, 9})),
    "USDCAD": ("TREND-LON", lambda: make_trend(allow_hours={7, 8, 9})),
    "XAGUSD": ("TREND-LON", lambda: make_trend(allow_hours={7, 8, 9})),
    "EURJPY": ("TREND", lambda: make_trend()),
    "AUDJPY": ("TREND", lambda: make_trend()),
    "AUDUSD": ("MEANREV-EXT", lambda: make_meanrev(max_ext_atr=3.0)),
    "EURGBP": ("MEANREV-EXT", lambda: make_meanrev(max_ext_atr=3.0)),
    "XAUUSD": ("MEANREV-EXT", lambda: make_meanrev(max_ext_atr=3.0)),
    "CHFJPY": ("MAOSCQ", lambda: make_maosc_quality(use_macd=False, adx_min=0, skip_stoch_low=True, skip_london=False)),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capital", type=float, default=10000)
    ap.add_argument("--risk", type=float, default=1.0)
    ap.add_argument("--max-risk", type=float, default=6.0)
    ap.add_argument("--max-spread-pct", type=float, default=12.0)
    ap.add_argument("--max-open", type=int, default=0, help="0 = tak terbatas")
    ap.add_argument("--bt-days", type=int, default=1825)
    ap.add_argument("--api", default="http://192.168.0.116:8000")
    args = ap.parse_args()
    api = MT5Api(args.api, timeout=180)

    print(f"\nPORTFOLIO SHARED-ACCOUNT | ${args.capital:.0f} | risk {args.risk}%/trade dari total "
          f"| maks open: {'∞' if args.max_open == 0 else args.max_open} | 1 posisi/pair")
    print("Precompute sinyal tiap pair...")
    pairs = {}
    for sym, (lbl, mk) in ASSIGN.items():
        try:
            si = api.symbol_info(sym)
            bars, _ = fetch_bars(api, sym, "H1", args.bt_days, 2000)
            if len(bars) < 2000:
                print(f"  {sym}: skip (data {len(bars)})"); continue
            strat = mk()
            pre = strat.prepare(bars)
            atr = atr_series(bars, 14)
            sides = [strat.signal(i, bars, pre) for i in range(len(bars))]
            pairs[sym] = dict(si=si, bars=bars, atr=atr, sides=sides, strat=strat, lbl=lbl)
            print(f"  {sym:8} {lbl:12} {len(bars)} bar")
        except Exception as e:
            print(f"  {sym}: err {str(e)[:40]}")

    # timeline gabungan: (time, sym, idx)
    timeline = []
    for sym, d in pairs.items():
        for i, b in enumerate(d["bars"]):
            timeline.append((b["time"], sym, i))
    timeline.sort(key=lambda x: x[0])

    bal = args.capital; peak = bal; max_dd = 0.0
    openpos = {}  # sym -> pos
    trades = []
    yearly = defaultdict(float); yearly_n = defaultdict(int)
    skips_cap = 0; max_concurrent = 0

    for t, sym, i in timeline:
        d = pairs[sym]; bar = d["bars"][i]; si = d["si"]; point = si["point"]
        # 1. kelola posisi terbuka pair ini
        if sym in openpos:
            p = openpos[sym]; hit = None
            if p["side"] == "buy":
                if bar["low"] <= p["sl"]:   hit = p["sl"]
                elif bar["high"] >= p["tp"]: hit = p["tp"]
            else:
                if bar["high"] >= p["sl"]:   hit = p["sl"]
                elif bar["low"] <= p["tp"]:  hit = p["tp"]
            if hit is not None:
                plp = (hit - p["entry"]) if p["side"] == "buy" else (p["entry"] - hit)
                ts = si.get("trade_tick_size") or point; tv = si.get("trade_tick_value") or 1.0
                net = (plp / ts) * tv * p["lot"] - (p["spread"] / ts) * tv * p["lot"]
                bal += net
                peak = max(peak, bal); max_dd = max(max_dd, (peak - bal) / peak * 100)
                yr = dt.datetime.fromtimestamp(bar["time"]).strftime("%Y")
                yearly[yr] += net; yearly_n[yr] += 1
                trades.append({"sym": sym, "net": net})
                del openpos[sym]
        # 2. sinyal entry (1/pair, cek max-open)
        if sym in openpos:
            continue
        side = d["sides"][i]; a = d["atr"][i]
        if not side or a != a or a <= 0:
            continue
        if args.max_open and len(openpos) >= args.max_open:
            skips_cap += 1; continue
        spread_price = bar["spread"] * point
        if a and spread_price / a * 100 > args.max_spread_pct:
            continue
        sl_d = d["strat"].sl_atr * a; tp_d = d["strat"].tp_atr * a
        lot, est_loss = calc_lot(bal * args.risk / 100, sl_d, si)
        if est_loss > bal * args.max_risk / 100:
            continue
        entry = bar["close"]
        openpos[sym] = dict(side=side, entry=entry, lot=lot, spread=spread_price,
                            sl=entry - sl_d if side == "buy" else entry + sl_d,
                            tp=entry + tp_d if side == "buy" else entry - tp_d)
        max_concurrent = max(max_concurrent, len(openpos))

    # laporan
    net_total = bal - args.capital
    wins = [x for x in trades if x["net"] > 0]
    print(f"\n[HASIL] {len(trades)} trade | balance ${args.capital:.0f} → ${bal:,.0f} "
          f"({net_total/args.capital*100:+.1f}%)")
    print(f"  Win-rate {len(wins)/len(trades)*100:.1f}% | Max drawdown {max_dd:.1f}% | "
          f"maks posisi simultan: {max_concurrent}" + (f" | skip cap-open: {skips_cap}" if skips_cap else ""))
    pos_y = 0
    print(f"\n  {'tahun':6} {'trade':>6} {'profit$':>10} {'return%':>9}")
    for yr in sorted(yearly):
        if yearly[yr] > 0: pos_y += 1
        print(f"  {yr:6} {yearly_n[yr]:>6} {yearly[yr]:>+10.0f} {yearly[yr]/args.capital*100:>+8.1f}%")
    print(f"\n  Tahun profit: {pos_y}/{len(yearly)} | rata-rata ${net_total/max(1,len(yearly)):+,.0f}/tahun")
    # per pair
    pp = defaultdict(float); ppn = defaultdict(int)
    for x in trades:
        pp[x["sym"]] += x["net"]; ppn[x["sym"]] += 1
    print(f"\n  per pair: " + " | ".join(f"{s}:{pp[s]:+.0f}({ppn[s]})" for s in sorted(pp, key=lambda k: -pp[k])))
    print()


if __name__ == "__main__":
    main()
