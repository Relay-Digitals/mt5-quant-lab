"""
journal.py — Trade journal di TimescaleDB (tf-postgres), DB terpisah `mt5_research`.
Isolasi penuh dari skema app TradeForge (tidak menyentuh tabel paper_*).

Koneksi via env libpq (PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE) — di-load dari
/opt/mt5-quant/.env oleh _load_env(). Tabel: runs + trades (hypertable di entry_time).

API sama spt versi lama: init / log_run / log_trades / upsert_live_trade / conn.
"""
from __future__ import annotations

import json
import os
import time
import datetime as dt
from typing import Optional

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


def _load_env():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id        TEXT PRIMARY KEY,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    source        TEXT, strategy TEXT, symbol TEXT, timeframe TEXT,
    params        JSONB,
    start_balance DOUBLE PRECISION, end_balance DOUBLE PRECISION,
    trades        INTEGER, wins INTEGER, losses INTEGER,
    win_rate      DOUBLE PRECISION, ret_pct DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION, max_dd_pct DOUBLE PRECISION,
    period_from   TIMESTAMPTZ, period_to TIMESTAMPTZ, notes TEXT
);
CREATE TABLE IF NOT EXISTS trades (
    id            BIGSERIAL,
    run_id        TEXT,
    source        TEXT, strategy TEXT, symbol TEXT, timeframe TEXT, side TEXT,
    entry_time    TIMESTAMPTZ NOT NULL,
    entry_price   DOUBLE PRECISION, exit_time TIMESTAMPTZ, exit_price DOUBLE PRECISION,
    lot           DOUBLE PRECISION, sl DOUBLE PRECISION, tp DOUBLE PRECISION,
    result        TEXT, net DOUBLE PRECISION, balance_after DOUBLE PRECISION,
    ticket        BIGINT, magic BIGINT,
    features      JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

POST_SCHEMA = [
    "ALTER TABLE trades ADD COLUMN IF NOT EXISTS features JSONB",
    "SELECT create_hypertable('trades','entry_time',if_not_exists=>TRUE,migrate_data=>TRUE)",
    "CREATE INDEX IF NOT EXISTS ix_trades_run    ON trades(run_id)",
    "CREATE INDEX IF NOT EXISTS ix_trades_sym    ON trades(symbol)",
    "CREATE INDEX IF NOT EXISTS ix_trades_strat  ON trades(strategy)",
    "CREATE INDEX IF NOT EXISTS ix_trades_ticket ON trades(ticket)",
    "CREATE INDEX IF NOT EXISTS ix_runs_strat    ON runs(strategy)",
]


def conn():
    return psycopg.connect(row_factory=dict_row)  # pakai env PG*


def init() -> None:
    with conn() as c:
        c.execute(SCHEMA)
        for stmt in POST_SCHEMA:
            try:
                c.execute(stmt)
            except Exception:
                c.rollback()
        c.commit()


def make_run_id(source, strategy, symbol, tf) -> str:
    return f"{source}-{strategy}-{symbol}-{tf}-{int(time.time()*1000)}"


def log_run(*, source, strategy, symbol, timeframe, params, start_balance, end_balance,
            trades, wins, losses, win_rate, ret_pct, profit_factor, max_dd_pct,
            period_from=None, period_to=None, notes=None, run_id=None) -> str:
    rid = run_id or make_run_id(source, strategy, symbol, timeframe)
    with conn() as c:
        c.execute("""INSERT INTO runs
            (run_id,source,strategy,symbol,timeframe,params,start_balance,end_balance,
             trades,wins,losses,win_rate,ret_pct,profit_factor,max_dd_pct,
             period_from,period_to,notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (run_id) DO UPDATE SET
              end_balance=EXCLUDED.end_balance, ret_pct=EXCLUDED.ret_pct,
              notes=EXCLUDED.notes""",
            (rid, source, strategy, symbol, timeframe, Jsonb(params), start_balance,
             end_balance, trades, wins, losses, win_rate, ret_pct, profit_factor,
             max_dd_pct, period_from, period_to, notes))
        c.commit()
    return rid


def log_trades(run_id: Optional[str], source: str, strategy: str, symbol: str,
               timeframe: str, trade_log: list[dict]) -> int:
    if not trade_log:
        return 0
    rows = [(run_id, source, strategy, symbol, timeframe, t.get("side"),
             t.get("entry_time"), t.get("entry_price"), t.get("exit_time"),
             t.get("exit_price"), t.get("lot"), t.get("sl"), t.get("tp"),
             t.get("result"), t.get("net"), t.get("balance_after"),
             t.get("ticket"), t.get("magic"),
             Jsonb(t["features"]) if t.get("features") else None) for t in trade_log]
    with conn() as c:
        c.cursor().executemany("""INSERT INTO trades
            (run_id,source,strategy,symbol,timeframe,side,entry_time,entry_price,
             exit_time,exit_price,lot,sl,tp,result,net,balance_after,ticket,magic,features)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", rows)
        c.commit()
    return len(rows)


def log_live_entry(ticket: int, *, strategy, symbol, timeframe, side, entry_time,
                   entry_price, lot, sl, tp, magic, features) -> None:
    """Rekam ENTRY live + snapshot indikator (dipanggil live_trader saat order masuk).
    Idempoten by ticket. sync_live nanti mengisi exit/net (fitur tetap terjaga)."""
    init()
    with conn() as c:
        ex = c.execute("SELECT id FROM trades WHERE ticket=%s AND source='forward'",
                       (ticket,)).fetchone()
        if ex:
            return
        c.execute("""INSERT INTO trades
            (run_id,source,strategy,symbol,timeframe,side,entry_time,entry_price,lot,sl,tp,
             ticket,magic,features)
            VALUES (NULL,'forward',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (strategy, symbol, timeframe, side, entry_time, entry_price, lot, sl, tp,
             ticket, magic, Jsonb(features) if features else None))
        c.commit()


def upsert_live_trade(ticket: int, **f) -> None:
    f["ticket"] = ticket
    with conn() as c:
        ex = c.execute("SELECT id FROM trades WHERE ticket=%s AND source='forward'",
                       (ticket,)).fetchone()
        if ex:
            cols = [k for k in f if k != "ticket"]
            sets = ",".join(f"{k}=%s" for k in cols)
            c.execute(f"UPDATE trades SET {sets} WHERE id=%s",
                      [f[k] for k in cols] + [ex["id"]])
        else:
            f.setdefault("source", "forward")
            f.setdefault("entry_time", dt.datetime.now())
            cols = list(f.keys())
            ph = ",".join(["%s"] * len(cols))
            c.execute(f"INSERT INTO trades ({','.join(cols)}) VALUES ({ph})",
                      [f[k] for k in cols])
        c.commit()


if __name__ == "__main__":
    init()
    with conn() as c:
        print(f"Journal Postgres siap @ {os.getenv('PGHOST')}/{os.getenv('PGDATABASE')}")
        for t in ("runs", "trades"):
            n = c.execute(f"SELECT COUNT(*) n FROM {t}").fetchone()["n"]
            print(f"  {t}: {n} baris")
