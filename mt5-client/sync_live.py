"""
sync_live.py — Sinkronkan trade FORWARD TEST dari deal-history broker (MT5) ke journal.

Otoritatif: ambil deals dari MT5, kelompokkan per position_id, rekonstruksi trade
(entry+exit, realized P/L termasuk swap & komisi). Idempoten (upsert by ticket).
Jalankan berkala (cron) di CT supaya journal selalu update dgn hasil live nyata.

Usage:
  python3 sync_live.py --days 30
"""
from __future__ import annotations

import argparse
import datetime as dt

from mt5_scalper import MT5Api
import journal

# magic → strategi (sesuai live runner)
MAGIC_STRAT = {770001: "EMA", 770002: "MAOSC", 770003: "TREND", 770004: "MEANREV", 770005: "MAOSCQ"}


def main():
    ap = argparse.ArgumentParser(description="Sync live deals → journal")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--api", default="http://192.168.0.116:8000")
    args = ap.parse_args()

    api = MT5Api(args.api, timeout=60)
    d = api._get("/api/deals", days=args.days)
    deals = d.get("items", [])
    # kelompokkan per posisi
    by_pos: dict[int, list] = {}
    for dl in deals:
        mg = dl.get("magic")
        if mg not in MAGIC_STRAT:
            continue
        pid = dl.get("position_id") or dl.get("position") or dl.get("ticket")
        by_pos.setdefault(pid, []).append(dl)

    journal.init()
    n_closed = 0
    for pid, dls in by_pos.items():
        dls.sort(key=lambda x: x.get("time", 0))
        ins = [x for x in dls if x.get("entry") == 0]   # DEAL_ENTRY_IN
        outs = [x for x in dls if x.get("entry") == 1]  # DEAL_ENTRY_OUT
        if not ins:
            continue
        d_in = ins[0]
        mg = d_in.get("magic")
        strat = MAGIC_STRAT.get(mg, "?")
        sym = d_in.get("symbol")
        side = "buy" if d_in.get("type") == 0 else "sell"
        lot = d_in.get("volume")
        entry_price = d_in.get("price")
        entry_time = dt.datetime.fromtimestamp(d_in.get("time", 0)).isoformat()

        if outs:  # posisi sudah ditutup
            net = sum((x.get("profit", 0) or 0) + (x.get("swap", 0) or 0) +
                      (x.get("commission", 0) or 0) for x in outs)
            exit_price = outs[-1].get("price")
            exit_time = dt.datetime.fromtimestamp(outs[-1].get("time", 0)).isoformat()
            result = "win" if net > 0 else "loss"
            journal.upsert_live_trade(
                int(pid), source="forward", strategy=strat, symbol=sym, timeframe="",
                side=side, entry_time=entry_time, entry_price=entry_price,
                exit_time=exit_time, exit_price=exit_price, lot=lot,
                result=result, net=round(net, 2), magic=mg)
            n_closed += 1

    print(f"Sync selesai: {len(by_pos)} posisi diproses, {n_closed} trade closed di-upsert ke journal.")
    # ringkasan live per strategi
    with journal.conn() as c:
        rows = c.execute("""SELECT strategy, COUNT(*) n, ROUND(SUM(net)::numeric,2) pnl,
            SUM(CASE WHEN net>0 THEN 1 ELSE 0 END) w FROM trades
            WHERE source='forward' GROUP BY strategy""").fetchall()
    for r in rows:
        print(f"  {r['strategy']:8}: {r['n']} trade | net ${r['pnl'] or 0:+.2f} | "
              f"menang {r['w']}/{r['n']}")
    # index trade live (+ fitur) ke RAG
    try:
        import rag
        print(f"  RAG: {rag.reindex_trades()} trade live ter-index ke Meili.")
    except Exception as e:
        print(f"  (reindex trades gagal: {e})")


if __name__ == "__main__":
    main()
