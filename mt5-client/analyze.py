"""
analyze.py — Antarmuka analisis trade journal.

Kuantitatif (SQL, akurat):
  python3 analyze.py summary                 # agregat per strategi×symbol
  python3 analyze.py runs [--source backtest]
  python3 analyze.py trades --symbol USDJPY --limit 20
  python3 analyze.py best                     # run terbaik per symbol

Semantik (RAG):
  python3 analyze.py reindex                  # bangun ulang embedding run
  python3 analyze.py ask "strategi mana paling stabil di FX?"
"""
from __future__ import annotations

import argparse

import journal


def _q(sql, params=()):
    journal.init()
    with journal.conn() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]


def cmd_summary(args):
    src = f"WHERE source='{args.source}'" if args.source else ""
    rows = _q(f"""
        SELECT strategy, symbol, source, COUNT(*) n,
               SUM(trades) trades, SUM(wins) wins,
               ROUND(AVG(win_rate)::numeric,1) wr, ROUND(AVG(ret_pct)::numeric,2) avg_ret,
               ROUND(AVG(profit_factor)::numeric,2) pf, ROUND(AVG(max_dd_pct)::numeric,1) dd
        FROM runs {src}
        GROUP BY strategy, symbol, source
        ORDER BY avg_ret DESC""")
    if not rows:
        print("(journal kosong — jalankan backtest dgn --journal dulu)"); return
    print(f"{'STRAT':9} {'SYMBOL':9} {'src':9} {'#run':>5} {'WR%':>6} {'avgRet%':>8} {'PF':>5} {'DD%':>6}")
    print("-" * 66)
    for r in rows:
        print(f"{r['strategy']:9} {r['symbol']:9} {r['source']:9} {r['n']:>5} "
              f"{r['wr'] or 0:6.1f} {r['avg_ret'] or 0:+8.2f} {r['pf'] or 0:5.2f} {r['dd'] or 0:6.1f}")


def cmd_runs(args):
    src = f"WHERE source='{args.source}'" if args.source else ""
    rows = _q(f"SELECT * FROM runs {src} ORDER BY created_at DESC LIMIT %s", (args.limit,))
    for r in rows:
        print(f"{r['created_at'][:19]} | {r['source']:9} {r['strategy']:8} {r['symbol']:8} "
              f"{r['timeframe']:4} | ret {r['ret_pct']:+6.2f}% PF {r['profit_factor']:.2f} "
              f"({r['trades']}tr WR{r['win_rate']:.0f}%) | {r['run_id']}")


def cmd_trades(args):
    w = []
    pr = []
    if args.symbol: w.append("symbol=%s"); pr.append(args.symbol)
    if args.strategy: w.append("strategy=%s"); pr.append(args.strategy.upper())
    if args.source: w.append("source=%s"); pr.append(args.source)
    where = ("WHERE " + " AND ".join(w)) if w else ""
    rows = _q(f"SELECT * FROM trades {where} ORDER BY id DESC LIMIT %s", (*pr, args.limit))
    tot = _q(f"SELECT COUNT(*) n, ROUND(SUM(net)::numeric,2) pnl, "
             f"SUM(CASE WHEN net>0 THEN 1 ELSE 0 END) w FROM trades {where}", tuple(pr))[0]
    for r in rows:
        et = (r['entry_time'] or '')[:16]
        print(f"{et} {r['strategy']:8} {r['symbol']:8} {r['side'] or '?':4} "
              f"lot {r['lot'] or 0:.2f} {r['result'] or '':6} net ${r['net'] or 0:+7.2f}")
    if tot['n']:
        print(f"\nTotal {tot['n']} trade | net ${tot['pnl'] or 0:+.2f} | "
              f"menang {tot['w']}/{tot['n']} ({tot['w']/tot['n']*100:.1f}%)")


def cmd_best(args):
    rows = _q("""SELECT DISTINCT ON (symbol) symbol, strategy, timeframe, ret_pct,
                        profit_factor, max_dd_pct
                 FROM runs ORDER BY symbol, ret_pct DESC""")
    rows.sort(key=lambda r: r["ret_pct"] or -999, reverse=True)
    print(f"{'SYMBOL':9} {'best strat':10} {'TF':4} {'return%':>8} {'PF':>5} {'DD%':>6}")
    print("-" * 46)
    for r in rows:
        print(f"{r['symbol']:9} {r['strategy']:10} {r['timeframe'] or '':4} "
              f"{r['ret_pct']:+8.2f} {r['profit_factor'] or 0:5.2f} {r['max_dd_pct'] or 0:6.1f}")


BUCKETS = {
    "rsi14": [("<30 oversold", lambda x: x < 30), ("30-50", lambda x: 30 <= x < 50),
              ("50-70", lambda x: 50 <= x < 70), (">70 overbought", lambda x: x >= 70)],
    "adx14": [("<20 lemah", lambda x: x < 20), ("20-25", lambda x: 20 <= x < 25),
              (">25 tren kuat", lambda x: x >= 25)],
    "macd_hist": [("<0 bearish", lambda x: x < 0), (">=0 bullish", lambda x: x >= 0)],
    "bb_pctb": [("<0.2 bawah", lambda x: x < 0.2), ("0.2-0.8 tengah", lambda x: 0.2 <= x <= 0.8),
                (">0.8 atas", lambda x: x > 0.8)],
    "stoch_k": [("<20", lambda x: x < 20), ("20-80", lambda x: 20 <= x <= 80), (">80", lambda x: x > 80)],
    "dist_ema50_atr": [("<-1 jauh bawah", lambda x: x < -1), ("-1..1 dekat", lambda x: -1 <= x <= 1),
                       (">1 jauh atas", lambda x: x > 1)],
    "cci20": [("<-100", lambda x: x < -100), ("-100..100", lambda x: -100 <= x <= 100), (">100", lambda x: x > 100)],
    "vol_ratio": [("<1 sepi", lambda x: x < 1), ("1-1.5", lambda x: 1 <= x <= 1.5), (">1.5 ramai", lambda x: x > 1.5)],
    "mfi14": [("<20", lambda x: x < 20), ("20-80", lambda x: 20 <= x <= 80), (">80", lambda x: x > 80)],
    "hour": [("00-07", lambda x: 0 <= x < 8), ("08-12 London", lambda x: 8 <= x < 13),
             ("13-17 NY", lambda x: 13 <= x < 18), ("18-23", lambda x: 18 <= x < 24)],
}


def cmd_quality(args):
    w = ["features IS NOT NULL"]; pr = []
    if args.symbol: w.append("symbol=%s"); pr.append(args.symbol)
    if args.strategy: w.append("strategy=%s"); pr.append(args.strategy.upper())
    rows = _q(f"SELECT net, features FROM trades WHERE {' AND '.join(w)}", tuple(pr))
    if not rows:
        print("(belum ada trade ber-fitur — jalankan backtest --features --journal dulu)"); return
    n = len(rows)
    base = sum(1 for r in rows if (r["net"] or 0) > 0) / n * 100
    flt = (f" [{args.symbol or 'semua'}/{args.strategy or 'semua'}]")
    print(f"ANALISIS KUALITAS ENTRY{flt} | {n} trade ber-fitur | baseline win-rate {base:.1f}%")
    print("Cari kondisi dgn WR jauh di atas baseline = setup berkualitas.\n")
    for feat, buckets in BUCKETS.items():
        line = f"── {feat} ──\n"
        any_row = False
        for label, fn in buckets:
            sub = [r for r in rows if r["features"] and r["features"].get(feat) is not None
                   and fn(r["features"][feat])]
            if not sub:
                continue
            any_row = True
            wn = sum(1 for r in sub if (r["net"] or 0) > 0)
            wr = wn / len(sub) * 100
            avg = sum((r["net"] or 0) for r in sub) / len(sub)
            tot = sum((r["net"] or 0) for r in sub)
            flag = " ★" if (wr >= base + 5 and len(sub) >= 20) else \
                   (" ✗" if (wr <= base - 5 and len(sub) >= 20) else "")
            line += f"   {label:18} n={len(sub):4} WR {wr:5.1f}% avgNet ${avg:+7.2f} total ${tot:+9.0f}{flag}\n"
        if any_row:
            print(line)
    print("★ = win-rate ≥5% di ATAS baseline (setup bagus, n≥20) | ✗ = ≥5% di BAWAH (hindari)")


def cmd_freq(args):
    src = args.source or "backtest"
    rows = _q("""
        WITH rc AS (
          SELECT run_id, symbol, strategy, COUNT(*) n,
                 EXTRACT(EPOCH FROM (MAX(entry_time)-MIN(entry_time)))/86400.0 days
          FROM trades WHERE source=%s GROUP BY run_id, symbol, strategy
        ), best AS (
          SELECT DISTINCT ON (symbol,strategy) symbol, strategy, n, days
          FROM rc ORDER BY symbol, strategy, n DESC
        )
        SELECT symbol, strategy, n, ROUND(days::numeric,0) days,
          ROUND((n/NULLIF(days,0))::numeric,2) per_day,
          ROUND((n/NULLIF(days,0)*7)::numeric,1) per_week,
          ROUND((n/NULLIF(days,0)*30.4)::numeric,1) per_month
        FROM best ORDER BY n DESC""", (src,))
    if not rows:
        print("(belum ada trade)"); return
    print(f"FREKUENSI TRADE per pair (sumber: {src}, dari run terbesar tiap pair)")
    print(f"{'pair':9} {'strat':8} {'total':>6} {'span(hari)':>10} {'/hari':>7} {'/minggu':>8} {'/bulan':>8}")
    print("-" * 60)
    for r in rows:
        print(f"{r['symbol']:9} {r['strategy']:8} {r['n']:>6} {int(r['days'] or 0):>9} "
              f"{r['per_day'] or 0:>7.2f} {r['per_week'] or 0:>8.1f} {r['per_month'] or 0:>8.1f}")


DOW = {0: "Min", 1: "Sen", 2: "Sel", 3: "Rab", 4: "Kam", 5: "Jum", 6: "Sab"}


def cmd_when(args):
    src = args.source or "backtest"
    f = ["source=%s"]; pr = [src]
    if args.symbol: f.append("symbol=%s"); pr.append(args.symbol)
    if args.strategy: f.append("strategy=%s"); pr.append(args.strategy.upper())
    cond = " AND ".join(f)
    # pilih run terbesar per (symbol,strategy) → hindari double-count antar-run
    base = f"""
        WITH rc AS (SELECT run_id, symbol, strategy, COUNT(*) n FROM trades WHERE {cond}
                    GROUP BY run_id,symbol,strategy),
             best AS (SELECT DISTINCT ON (symbol,strategy) run_id FROM rc ORDER BY symbol,strategy,n DESC)
        SELECT {{grp}} g, COUNT(*) n,
               SUM(CASE WHEN net>0 THEN 1 ELSE 0 END) w,
               ROUND(AVG(net)::numeric,2) avg, ROUND(SUM(net)::numeric,0) tot
        FROM trades WHERE run_id IN (SELECT run_id FROM best) AND {cond}
        GROUP BY g ORDER BY g"""
    lbl = f"[{args.symbol or 'semua'}/{args.strategy or 'semua'}]"
    base_rows = _q(base.format(grp="EXTRACT(HOUR FROM entry_time)::int"), tuple(pr) + tuple(pr))
    tot_n = sum(r["n"] for r in base_rows) or 1
    base_wr = sum(r["w"] for r in base_rows) / tot_n * 100

    print(f"DISTRIBUSI per JAM (UTC) {lbl} | {tot_n} trade | baseline WR {base_wr:.1f}%")
    print(f"  {'jam':4} {'n':>5} {'WR%':>6} {'avgNet$':>8} {'totalNet$':>10}  bar")
    mx = max((r["n"] for r in base_rows), default=1)
    for r in base_rows:
        wr = r["w"] / r["n"] * 100
        bar = "█" * int(r["n"] / mx * 20)
        flag = "★" if wr >= base_wr + 5 else ("✗" if wr <= base_wr - 5 else " ")
        print(f"  {r['g']:>2}:00 {r['n']:>5} {wr:>6.1f} {r['avg'] or 0:>8.2f} {r['tot'] or 0:>10.0f} {flag}{bar}")

    dow_rows = _q(base.format(grp="EXTRACT(DOW FROM entry_time)::int"), tuple(pr) + tuple(pr))
    print(f"\nDISTRIBUSI per HARI {lbl}")
    print(f"  {'hari':5} {'n':>5} {'WR%':>6} {'avgNet$':>8} {'totalNet$':>10}")
    for r in dow_rows:
        wr = r["w"] / r["n"] * 100
        flag = "★" if wr >= base_wr + 5 else ("✗" if wr <= base_wr - 5 else " ")
        print(f"  {DOW.get(r['g'], r['g']):5} {r['n']:>5} {wr:>6.1f} {r['avg'] or 0:>8.2f} {r['tot'] or 0:>10.0f} {flag}")
    print("\n★ = WR ≥5% di atas baseline | ✗ = di bawah. Jam UTC (London ~7-16, NY ~12-21).")


def cmd_whenyr(args):
    src = args.source or "backtest"
    f = ["source=%s"]; pr = [src]
    if args.symbol: f.append("symbol=%s"); pr.append(args.symbol)
    if args.strategy: f.append("strategy=%s"); pr.append(args.strategy.upper())
    cond = " AND ".join(f)
    best_cte = f"""
        WITH rc AS (SELECT run_id, symbol, strategy, COUNT(*) n FROM trades WHERE {cond}
                    GROUP BY run_id,symbol,strategy),
             best AS (SELECT DISTINCT ON (symbol,strategy) run_id FROM rc ORDER BY symbol,strategy,n DESC)"""
    lbl = f"[{args.symbol or 'semua'}/{args.strategy or 'semua'}]"

    # sesi per tahun (net $)
    SESS = [("Asia 0-6", "h<7"), ("Lon-open 7-9", "h>=7 AND h<10"),
            ("Lon-mid 10-13", "h>=10 AND h<14"), ("NY 14-17", "h>=14 AND h<18"),
            ("Late 18-23", "h>=18")]
    case = " ".join(f"WHEN {c} THEN '{n}'" for n, c in SESS)
    rows = _q(f"""{best_cte}
        SELECT EXTRACT(YEAR FROM entry_time)::int yr,
          CASE {case} END sess, ROUND(SUM(net)::numeric,0)::int net
        FROM (SELECT entry_time, net, EXTRACT(HOUR FROM entry_time)::int h FROM trades
              WHERE run_id IN (SELECT run_id FROM best) AND {cond}) t
        GROUP BY yr, sess""", tuple(pr) + tuple(pr))
    if not rows:
        print("(tak ada data)"); return
    yrs = sorted({r["yr"] for r in rows}); cols = [n for n, _ in SESS]
    piv = {(r["yr"], r["sess"]): r["net"] for r in rows}
    print(f"KONSISTENSI per SESI per TAHUN (net $) {lbl}")
    print("  " + f"{'tahun':6}" + "".join(f"{c:>14}" for c in cols))
    for y in yrs:
        line = f"  {y:<6}"
        for c in cols:
            v = piv.get((y, c), 0); line += f"{v:>+14}"
        print(line)
    print("  " + "-"*6 + "consistency: berapa tahun POSITIF per sesi")
    line = "  " + f"{'pos':6}"
    for c in cols:
        p = sum(1 for y in yrs if piv.get((y, c), 0) > 0)
        line += f"{str(p)+'/'+str(len(yrs)):>14}"
    print(line)

    # dow per tahun
    rows2 = _q(f"""{best_cte}
        SELECT EXTRACT(YEAR FROM entry_time)::int yr, EXTRACT(DOW FROM entry_time)::int d,
          ROUND(SUM(net)::numeric,0)::int net
        FROM trades WHERE run_id IN (SELECT run_id FROM best) AND {cond}
        GROUP BY yr, d""", tuple(pr) + tuple(pr))
    piv2 = {(r["yr"], r["d"]): r["net"] for r in rows2}
    days = [1, 2, 3, 4, 5]
    print(f"\nKONSISTENSI per HARI per TAHUN (net $) {lbl}")
    print("  " + f"{'tahun':6}" + "".join(f"{DOW[d]:>10}" for d in days))
    for y in yrs:
        line = f"  {y:<6}"
        for d in days:
            line += f"{piv2.get((y, d), 0):>+10}"
        print(line)
    line = "  " + f"{'pos':6}"
    for d in days:
        p = sum(1 for y in yrs if piv2.get((y, d), 0) > 0)
        line += f"{str(p)+'/'+str(len(yrs)):>10}"
    print(line)
    print("\nKonsisten = sesi/hari yg POSITIF di mayoritas tahun (bukan didominasi 1 tahun).")


CMP_FEATS = ["rsi14", "adx14", "plus_di", "minus_di", "stoch_k", "stoch_d", "cci20",
             "willr14", "mfi14", "bb_pctb", "bb_width", "dist_ema50_atr", "dist_ema200_atr",
             "mom10", "roc10", "vol_ratio", "body_pct", "range_atr", "macd_hist", "hour"]


def cmd_compare(args):
    import statistics as st
    w = ["features IS NOT NULL"]; pr = []
    if args.symbol: w.append("symbol=%s"); pr.append(args.symbol)
    if args.strategy: w.append("strategy=%s"); pr.append(args.strategy.upper())
    if args.timeframe: w.append("timeframe=%s"); pr.append(args.timeframe)
    rows = _q(f"SELECT net, features FROM trades WHERE {' AND '.join(w)}", tuple(pr))
    win = [r["features"] for r in rows if (r["net"] or 0) > 0]
    los = [r["features"] for r in rows if (r["net"] or 0) <= 0]
    if len(win) < 20 or len(los) < 20:
        print(f"(sampel kurang: win {len(win)} loss {len(los)})"); return
    lbl = f"[{args.symbol or 'all'}/{args.strategy or 'all'}/{args.timeframe or 'allTF'}]"
    print(f"PROFIT vs NON-PROFIT — perbandingan indikator {lbl}")
    print(f"Menang: {len(win)} | Kalah: {len(los)} | WR {len(win)/(len(win)+len(los))*100:.1f}%")
    print(f"\n  {'indikator':16} {'mean(MENANG)':>13} {'mean(KALAH)':>12} {'selisih':>9} {'effect':>7}")
    print("  " + "-"*62)
    res = []
    for f in CMP_FEATS:
        wv = [d[f] for d in win if d.get(f) is not None]
        lv = [d[f] for d in los if d.get(f) is not None]
        if len(wv) < 20 or len(lv) < 20:
            continue
        mw, ml = st.mean(wv), st.mean(lv)
        try:
            sd = (st.pstdev(wv + lv)) or 1
        except Exception:
            sd = 1
        eff = (mw - ml) / sd
        res.append((f, mw, ml, mw - ml, eff))
    res.sort(key=lambda x: abs(x[4]), reverse=True)
    for f, mw, ml, diff, eff in res:
        flag = " ★" if abs(eff) >= 0.2 else ""
        print(f"  {f:16} {mw:>13.2f} {ml:>12.2f} {diff:>+9.2f} {eff:>+7.2f}{flag}")
    print("\neffect = (mean_menang − mean_kalah)/std. |effect|≥0,2 (★) = indikator paling membedakan.")
    print("Pakai ini utk rancang filter: hindari zona indikator yg condong ke KALAH.")


def cmd_reindex(args):
    import rag
    n = rag.reindex_runs()
    print(f"✓ Reindexed {n} run ke RAG.")


def cmd_ask(args):
    import rag
    q = " ".join(args.query)
    hits = rag.search(q, k=args.k)
    if not hits:
        print("(RAG kosong — jalankan 'analyze.py reindex' dulu)"); return
    print(f"🔎 Top {len(hits)} run relevan untuk: \"{q}\"\n")
    for h in hits:
        print(f"[{h['score']:.3f}] {h['text']}\n")
    print("— Pakai konteks di atas untuk menyimpulkan. Untuk angka presisi gunakan 'summary'/'trades'.")


def main():
    ap = argparse.ArgumentParser(description="Analisis trade journal")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("summary"); s.add_argument("--source"); s.set_defaults(fn=cmd_summary)
    s = sub.add_parser("runs"); s.add_argument("--source"); s.add_argument("--limit", type=int, default=20); s.set_defaults(fn=cmd_runs)
    s = sub.add_parser("trades"); s.add_argument("--symbol"); s.add_argument("--strategy"); s.add_argument("--source"); s.add_argument("--limit", type=int, default=20); s.set_defaults(fn=cmd_trades)
    s = sub.add_parser("best"); s.set_defaults(fn=cmd_best)
    s = sub.add_parser("quality"); s.add_argument("--symbol"); s.add_argument("--strategy"); s.set_defaults(fn=cmd_quality)
    s = sub.add_parser("freq"); s.add_argument("--source"); s.set_defaults(fn=cmd_freq)
    s = sub.add_parser("when"); s.add_argument("--symbol"); s.add_argument("--strategy"); s.add_argument("--source"); s.set_defaults(fn=cmd_when)
    s = sub.add_parser("whenyr"); s.add_argument("--symbol"); s.add_argument("--strategy"); s.add_argument("--source"); s.set_defaults(fn=cmd_whenyr)
    s = sub.add_parser("compare"); s.add_argument("--symbol"); s.add_argument("--strategy"); s.add_argument("--timeframe"); s.set_defaults(fn=cmd_compare)
    s = sub.add_parser("reindex"); s.set_defaults(fn=cmd_reindex)
    s = sub.add_parser("ask"); s.add_argument("query", nargs="+"); s.add_argument("--k", type=int, default=5); s.set_defaults(fn=cmd_ask)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
