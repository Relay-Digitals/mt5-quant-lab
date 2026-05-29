"""
MT5 client untuk CT 132 (192.168.0.116:8001).

Usage:
    ./venv/bin/python mt5_client.py                # default: jalankan smoke test
    ./venv/bin/python mt5_client.py info           # account + terminal info
    ./venv/bin/python mt5_client.py symbols        # list semua symbol
    ./venv/bin/python mt5_client.py tick EURUSD    # last tick untuk symbol
    ./venv/bin/python mt5_client.py bars EURUSD H1 # OHLC 100 bar terakhir
    ./venv/bin/python mt5_client.py positions      # open positions
    ./venv/bin/python mt5_client.py orders         # pending orders
    ./venv/bin/python mt5_client.py history        # deal history 7 hari
    ./venv/bin/python mt5_client.py buy EURUSD 0.01 --dry-run   # contoh order (DEFAULT dry-run)
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from contextlib import contextmanager
from typing import Iterator

from mt5linux import MetaTrader5

HOST = "192.168.0.116"
PORT = 8001

TIMEFRAMES = {
    "M1": "TIMEFRAME_M1", "M5": "TIMEFRAME_M5", "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30", "H1": "TIMEFRAME_H1", "H4": "TIMEFRAME_H4",
    "D1": "TIMEFRAME_D1", "W1": "TIMEFRAME_W1", "MN1": "TIMEFRAME_MN1",
}


@contextmanager
def connect(host: str = HOST, port: int = PORT) -> Iterator[MetaTrader5]:
    """Connect ke RPyC, call initialize(), yield mt5, lalu shutdown."""
    mt5 = MetaTrader5(host=host, port=port)
    ok = mt5.initialize()
    if not ok:
        err = mt5.last_error()
        if err and err[0] == -10004:
            sys.exit(
                f"mt5.initialize() returned False (last_error={err}).\n"
                f"MT5 terminal GUI belum login broker. Buka http://{host}:3000 di browser,\n"
                f"klik Connect, lalu File → Login to Trade Account.\n"
                f"Setelah login broker berhasil, jalankan script ini lagi."
            )
        sys.exit(f"mt5.initialize() failed: last_error={err}")
    try:
        yield mt5
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


def cmd_info(mt5: MetaTrader5) -> None:
    print("── terminal_info ──")
    t = mt5.terminal_info()
    for k in ("name", "company", "path", "build", "connected", "trade_allowed", "ping_last"):
        print(f"  {k:18s} = {getattr(t, k, None)}")

    print("\n── account_info ──")
    a = mt5.account_info()
    if a is None:
        print("  (none — broker login required)")
        return
    for k in ("login", "server", "name", "currency", "leverage",
              "balance", "equity", "margin_free", "profit"):
        print(f"  {k:18s} = {getattr(a, k, None)}")

    v = mt5.version()
    print(f"\n  version           = {v}")


def cmd_symbols(mt5: MetaTrader5) -> None:
    total = mt5.symbols_total()
    print(f"symbols_total: {total}")
    syms = mt5.symbols_get()
    # show first 30
    for s in syms[:30]:
        print(f"  {s.name:20s}  {s.description}")
    if len(syms) > 30:
        print(f"  ... and {len(syms) - 30} more")


def cmd_tick(mt5: MetaTrader5, symbol: str) -> None:
    if not mt5.symbol_select(symbol, True):
        sys.exit(f"symbol_select({symbol}) failed: {mt5.last_error()}")
    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)
    print(f"── {symbol} ──")
    print(f"  bid          = {tick.bid}")
    print(f"  ask          = {tick.ask}")
    print(f"  spread       = {info.spread} points  ({(tick.ask - tick.bid):.5f})")
    print(f"  time         = {dt.datetime.fromtimestamp(tick.time)}")
    print(f"  volume_min   = {info.volume_min}")
    print(f"  volume_step  = {info.volume_step}")
    print(f"  digits       = {info.digits}")
    print(f"  trade_mode   = {info.trade_mode}")


def cmd_bars(mt5: MetaTrader5, symbol: str, tf: str = "H1", count: int = 100) -> None:
    tf_attr = TIMEFRAMES.get(tf.upper())
    if not tf_attr:
        sys.exit(f"unknown timeframe '{tf}'. Use one of: {', '.join(TIMEFRAMES)}")
    timeframe = getattr(mt5, tf_attr)

    if not mt5.symbol_select(symbol, True):
        sys.exit(f"symbol_select({symbol}) failed: {mt5.last_error()}")

    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        sys.exit(f"copy_rates_from_pos returned empty: {mt5.last_error()}")

    print(f"── {symbol} {tf} (last {count} bars) ──")
    print(f"  {'time':19s}  {'open':>10s}  {'high':>10s}  {'low':>10s}  {'close':>10s}  {'volume':>10s}")
    show = min(10, len(rates))
    for r in rates[-show:]:
        ts = dt.datetime.fromtimestamp(r['time'])
        print(f"  {ts!s:19s}  {r['open']:10.5f}  {r['high']:10.5f}  {r['low']:10.5f}  "
              f"{r['close']:10.5f}  {r['tick_volume']:>10}")
    if len(rates) > show:
        print(f"  (showing last {show} of {len(rates)})")

    # Optional pandas — convert RPyC netref to native dicts first
    try:
        import pandas as pd
        rows = [{k: r[k] for k in ('time', 'open', 'high', 'low', 'close',
                                    'tick_volume', 'spread', 'real_volume')}
                for r in rates]
        df = pd.DataFrame(rows)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        print(f"\n  → pandas DataFrame shape: {df.shape}, cols: {list(df.columns)}")
    except ImportError:
        pass
    except Exception as e:
        print(f"\n  (pandas conversion skipped: {type(e).__name__}: {e})")


def cmd_positions(mt5: MetaTrader5) -> None:
    poss = mt5.positions_get()
    if not poss:
        print("(no open positions)")
        return
    print(f"── open positions ({len(poss)}) ──")
    for p in poss:
        print(f"  ticket={p.ticket}  {p.symbol}  vol={p.volume}  type={p.type}  "
              f"price_open={p.price_open}  profit={p.profit}")


def cmd_orders(mt5: MetaTrader5) -> None:
    ords = mt5.orders_get()
    if not ords:
        print("(no pending orders)")
        return
    print(f"── pending orders ({len(ords)}) ──")
    for o in ords:
        print(f"  ticket={o.ticket}  {o.symbol}  vol={o.volume_current}  type={o.type}  "
              f"price={o.price_open}")


def cmd_history(mt5: MetaTrader5, days: int = 7) -> None:
    end = dt.datetime.now()
    start = end - dt.timedelta(days=days)
    deals = mt5.history_deals_get(start, end)
    if not deals:
        print(f"(no deals in last {days} days)")
        return
    print(f"── deals last {days} days ({len(deals)}) ──")
    for d in deals[-15:]:
        ts = dt.datetime.fromtimestamp(d.time)
        print(f"  {ts!s:19s}  {d.symbol:10s}  type={d.type}  vol={d.volume}  "
              f"price={d.price}  profit={d.profit}")
    if len(deals) > 15:
        print(f"  (showing last 15 of {len(deals)})")


def _pick_filling_mode(mt5: MetaTrader5, symbol: str):
    """Pilih filling mode yang didukung broker untuk symbol ini.

    symbol_info.filling_mode bitmask: 1=FOK, 2=IOC, 4=RETURN.
    Broker Exness biasanya support FOK + RETURN, BUKAN IOC.
    """
    info = mt5.symbol_info(symbol)
    mask = getattr(info, "filling_mode", 0)
    if mask & 1:
        return mt5.ORDER_FILLING_FOK
    if mask & 2:
        return mt5.ORDER_FILLING_IOC
    if mask & 4:
        return mt5.ORDER_FILLING_RETURN
    return mt5.ORDER_FILLING_FOK  # fallback


def cmd_order(mt5: MetaTrader5, symbol: str, volume: float, side: str, dry_run: bool) -> None:
    """Place market order. DEFAULT dry_run=True — set --no-dry-run untuk benar-benar kirim."""
    if not mt5.symbol_select(symbol, True):
        sys.exit(f"symbol_select({symbol}) failed: {mt5.last_error()}")

    tick = mt5.symbol_info_tick(symbol)
    order_type = mt5.ORDER_TYPE_BUY if side == "buy" else mt5.ORDER_TYPE_SELL
    price = tick.ask if side == "buy" else tick.bid
    filling = _pick_filling_mode(mt5, symbol)

    request = dict(
        action       = mt5.TRADE_ACTION_DEAL,
        symbol       = symbol,
        volume       = volume,
        type         = order_type,
        price        = price,
        deviation    = 20,
        magic        = 123456,
        comment      = "python mt5_client.py",
        type_time    = mt5.ORDER_TIME_GTC,
        type_filling = filling,
    )

    print(f"── ORDER REQUEST ({'DRY RUN' if dry_run else 'LIVE'}) ──")
    for k, v in request.items():
        print(f"  {k:14s} = {v}")

    # IMPORTANT: mt5linux RPyC bridge requires kwargs, NOT dict-positional, untuk
    # order_check/order_send. Dict positional → "(-2, 'Unnamed arguments not allowed')".
    if dry_run:
        check = mt5.order_check(**request)
        print("\n── order_check result ──")
        if check is None:
            err = mt5.last_error()
            print(f"  (None — last_error={err})")
            ti = mt5.terminal_info()
            if ti is not None and not ti.trade_allowed:
                print("  → terminal_info.trade_allowed = False.")
                print("    Toggle 'Algo Trading' di MT5 toolbar (Ctrl+E).")
            return
        print(f"  retcode    = {check.retcode}  ({check.comment})")
        print(f"  balance    = {check.balance}")
        print(f"  equity     = {check.equity}")
        print(f"  margin     = {check.margin}")
        print(f"  margin_free= {check.margin_free}")
        print("\n  (dry-run: NOT sent. add --no-dry-run to actually send.)")
        return

    result = mt5.order_send(**request)
    print("\n── order_send result ──")
    print(f"  retcode    = {result.retcode}  ({result.comment})")
    print(f"  deal       = {result.deal}")
    print(f"  order      = {result.order}")
    print(f"  volume     = {result.volume}")
    print(f"  price      = {result.price}")
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        sys.exit(f"order_send failed: retcode={result.retcode}")


def smoke_test(mt5: MetaTrader5) -> None:
    """Default ketika tidak ada arg: cek koneksi + info ringkas."""
    print(f"✓ Connected to MT5 RPyC at {HOST}:{PORT}\n")
    cmd_info(mt5)
    print()
    n = mt5.symbols_total()
    print(f"symbols_total: {n}")


def main() -> None:
    p = argparse.ArgumentParser(description="MT5 RPyC client for CT 132", add_help=True)
    p.add_argument("--host", default=HOST)
    p.add_argument("--port", type=int, default=PORT)

    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("info",      help="account + terminal info")
    sub.add_parser("symbols",   help="list semua symbol")
    sub.add_parser("positions", help="open positions")
    sub.add_parser("orders",    help="pending orders")

    h = sub.add_parser("history",  help="deal history N hari terakhir")
    h.add_argument("--days", type=int, default=7)

    t = sub.add_parser("tick",     help="last tick for symbol")
    t.add_argument("symbol")

    b = sub.add_parser("bars",     help="OHLC bars")
    b.add_argument("symbol")
    b.add_argument("timeframe", nargs="?", default="H1")
    b.add_argument("--count", type=int, default=100)

    for side in ("buy", "sell"):
        o = sub.add_parser(side, help=f"market {side} (default dry-run)")
        o.add_argument("symbol")
        o.add_argument("volume", type=float)
        o.add_argument("--no-dry-run", dest="dry_run", action="store_false", default=True)

    args = p.parse_args()

    with connect(args.host, args.port) as mt5:
        if args.cmd is None:
            smoke_test(mt5)
        elif args.cmd == "info":
            cmd_info(mt5)
        elif args.cmd == "symbols":
            cmd_symbols(mt5)
        elif args.cmd == "tick":
            cmd_tick(mt5, args.symbol)
        elif args.cmd == "bars":
            cmd_bars(mt5, args.symbol, args.timeframe, args.count)
        elif args.cmd == "positions":
            cmd_positions(mt5)
        elif args.cmd == "orders":
            cmd_orders(mt5)
        elif args.cmd == "history":
            cmd_history(mt5, args.days)
        elif args.cmd in ("buy", "sell"):
            cmd_order(mt5, args.symbol, args.volume, args.cmd, args.dry_run)


if __name__ == "__main__":
    main()
