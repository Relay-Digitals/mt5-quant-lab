"""
FastAPI REST wrapper untuk MetaTrader 5 — full surface.

Mirrors hampir seluruh MetaTrader5 Python package API (mt5linux RPyC backend).

Swagger UI:  /docs
ReDoc:       /redoc
OpenAPI:     /openapi.json

Env vars:
    MT5_HOST   default 127.0.0.1
    MT5_PORT   default 8001
    API_HOST   default 0.0.0.0
    API_PORT   default 8000
"""
from __future__ import annotations

import datetime as dt
import os
import threading
from contextlib import asynccontextmanager
from typing import Any, Iterable, List, Optional

from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from mt5linux import MetaTrader5

import indicators as _ind

MT5_HOST = os.getenv("MT5_HOST", "127.0.0.1")
MT5_PORT = int(os.getenv("MT5_PORT", "8001"))

_mt5: Optional[MetaTrader5] = None
_mt5_lock = threading.Lock()

# Drop these meta keys when serializing RPyC namedtuple netrefs
_NAMEDTUPLE_META = {"n_fields", "n_sequence_fields", "n_unnamed_fields", "index", "count"}


def get_mt5() -> MetaTrader5:
    """Return live MT5 connection, reconnect on demand."""
    global _mt5
    with _mt5_lock:
        if _mt5 is None:
            m = MetaTrader5(host=MT5_HOST, port=MT5_PORT)
            if not m.initialize():
                err = m.last_error()
                raise HTTPException(
                    status_code=503,
                    detail={
                        "msg": "MT5 not ready (broker login required?)",
                        "last_error": list(err) if err else None,
                        "hint": "Open http://<ct132-ip>:3000 → Connect → File → Login to Trade Account",
                    },
                )
            _mt5 = m
        return _mt5


def _scalarize(v):
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (bytes, bytearray)):
        try:
            return v.decode("utf-8", "replace")
        except Exception:
            return str(v)
    if isinstance(v, (list, tuple)):
        return [_scalarize(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _scalarize(val) for k, val in v.items()}
    fields = getattr(v, "_fields", None)
    if fields:
        return {str(f): _scalarize(getattr(v, f)) for f in fields}
    try:
        attrs = [k for k in dir(v) if not k.startswith("_") and k not in _NAMEDTUPLE_META]
        attrs = [k for k in attrs if not callable(getattr(v, k, None))]
        if attrs:
            return {k: _scalarize(getattr(v, k)) for k in attrs}
    except Exception:
        pass
    return str(v)


def _named(obj) -> Optional[dict]:
    if obj is None:
        return None
    r = _scalarize(obj)
    return r if isinstance(r, dict) else {"value": r}


def _named_list(seq) -> list:
    return [_named(o) for o in (seq or [])]


def _pick_filling_mode(mt5: MetaTrader5, symbol: str) -> int:
    """Bitmask 1=FOK 2=IOC 4=RETURN. FOK works for most brokers (Exness)."""
    info = mt5.symbol_info(symbol)
    mask = getattr(info, "filling_mode", 0) if info else 0
    if mask & 1:
        return mt5.ORDER_FILLING_FOK
    if mask & 2:
        return mt5.ORDER_FILLING_IOC
    if mask & 4:
        return mt5.ORDER_FILLING_RETURN
    return mt5.ORDER_FILLING_FOK


def _tf(mt5: MetaTrader5, tf: str) -> int:
    attr = f"TIMEFRAME_{tf.upper()}"
    if not hasattr(mt5, attr):
        raise HTTPException(400, f"Invalid timeframe '{tf}'. Valid: M1 M2 M3 M4 M5 M6 M10 M12 M15 M20 M30 H1 H2 H3 H4 H6 H8 H12 D1 W1 MN1")
    return getattr(mt5, attr)


def _parse_time(s: str) -> dt.datetime:
    """Accept ISO datetime atau unix-seconds (string)."""
    try:
        return dt.datetime.fromtimestamp(float(s))
    except (ValueError, TypeError):
        pass
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(400, f"Cannot parse time '{s}' — use ISO 8601 or unix seconds")


def _bars_to_list(rates) -> list:
    out = []
    for r in rates:
        t = int(r["time"])
        out.append({
            "time":         t,
            "time_iso":     dt.datetime.fromtimestamp(t).isoformat(),
            "open":         float(r["open"]),
            "high":         float(r["high"]),
            "low":          float(r["low"]),
            "close":        float(r["close"]),
            "tick_volume":  int(r["tick_volume"]),
            "spread":       int(r["spread"]),
            "real_volume":  int(r["real_volume"]),
        })
    return out


def _ticks_to_list(ticks) -> list:
    out = []
    for t in ticks:
        ts = int(t["time"])
        out.append({
            "time":         ts,
            "time_iso":     dt.datetime.fromtimestamp(ts).isoformat(),
            "time_msc":     int(t["time_msc"]),
            "bid":          float(t["bid"]),
            "ask":          float(t["ask"]),
            "last":         float(t["last"]),
            "volume":       int(t["volume"]),
            "volume_real":  float(t["volume_real"]),
            "flags":        int(t["flags"]),
        })
    return out


# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_mt5()
    except HTTPException:
        pass
    yield
    global _mt5
    with _mt5_lock:
        if _mt5 is not None:
            try:
                _mt5.shutdown()
            except Exception:
                pass


app = FastAPI(
    title="MT5 REST API",
    version="2.0.0",
    description=(
        "Full REST wrapper untuk MetaTrader 5 (Wine + Docker di CT 132).\n\n"
        "Backend: `mt5linux` RPyC ke `127.0.0.1:8001`.\n\n"
        "**8 grup endpoint** — buka tab di bawah untuk detail.\n\n"
        "Lihat juga **/redoc** (read-only doc), **/openapi.json** (spec)."
    ),
    lifespan=lifespan,
    openapi_tags=[
        {"name": "meta",         "description": "Health, version, terminal, account, last_error"},
        {"name": "connection",   "description": "Programmatic broker login / shutdown"},
        {"name": "symbols",      "description": "Symbol list, info, MarketWatch select, last tick"},
        {"name": "market-data",  "description": "Historical OHLC bars dan tick streams"},
        {"name": "order-book",   "description": "DOM (Depth of Market) L2 subscription"},
        {"name": "positions",    "description": "Open positions read"},
        {"name": "orders",       "description": "Pending orders read"},
        {"name": "history",      "description": "Past deals dan past orders"},
        {"name": "trading",      "description": "order_check, order_send, modify, close, cancel"},
        {"name": "calculators",  "description": "Margin & profit calculators (broker-side)"},
        {"name": "constants",    "description": "Enum lookup — TIMEFRAME, ORDER_TYPE, RETCODE, dll"},
    ],
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    login:    int = Field(..., examples=[270970358])
    password: str = Field(..., examples=["yourpass"])
    server:   str = Field(..., examples=["Exness-MT5Trial17"])
    timeout:  int = Field(60000, description="ms")


class MarketOrderRequest(BaseModel):
    """Market deal: instant buy/sell at current price."""
    symbol:        str   = Field(..., examples=["EURUSD"])
    volume:        float = Field(..., gt=0, examples=[0.01])
    side:          str   = Field("buy", pattern="^(buy|sell)$")
    sl:            float = 0.0
    tp:            float = 0.0
    deviation:     int   = Field(20, ge=0)
    magic:         int   = 123456
    comment:       str   = "mt5-api"
    type_filling:  Optional[int] = Field(None, description="ORDER_FILLING_* (auto if null)")


class PendingOrderRequest(BaseModel):
    """Pending order: limit / stop / stop-limit."""
    symbol:    str
    volume:    float = Field(..., gt=0)
    order_type: str = Field(
        ...,
        pattern="^(buy_limit|sell_limit|buy_stop|sell_stop|buy_stop_limit|sell_stop_limit)$",
        examples=["buy_limit"],
    )
    price:     float = Field(..., description="Trigger / activation price")
    stoplimit: float = Field(0.0, description="Only for buy_stop_limit / sell_stop_limit")
    sl:        float = 0.0
    tp:        float = 0.0
    deviation: int   = 20
    magic:     int   = 123456
    comment:   str   = "mt5-api"
    expiration: Optional[int] = Field(None, description="Unix timestamp; null = GTC")
    type_filling: Optional[int] = None


class ModifyPositionRequest(BaseModel):
    """Update SL / TP of open position."""
    ticket: int
    sl:     float = 0.0
    tp:     float = 0.0


class ModifyOrderRequest(BaseModel):
    """Update price / SL / TP / expiration of pending order."""
    ticket:    int
    price:     Optional[float] = None
    stoplimit: Optional[float] = None
    sl:        Optional[float] = None
    tp:        Optional[float] = None
    expiration: Optional[int] = None


class CloseRequest(BaseModel):
    ticket:  int
    volume:  Optional[float] = Field(None, description="Partial close (null = full)")
    deviation: int = 20
    comment: str = "mt5-api close"


class CancelRequest(BaseModel):
    ticket: int


class CalcMarginRequest(BaseModel):
    symbol: str
    volume: float = Field(..., gt=0)
    side:   str   = Field("buy", pattern="^(buy|sell)$")
    price:  Optional[float] = Field(None, description="Null = current ask/bid")


class CalcProfitRequest(BaseModel):
    symbol:      str
    volume:      float = Field(..., gt=0)
    side:        str   = Field("buy", pattern="^(buy|sell)$")
    price_open:  float
    price_close: float


class BookSubscribeRequest(BaseModel):
    symbol: str


# ─────────────────────────────────────────────────────────────────────────────
# meta
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", tags=["meta"], summary="Service health")
def root():
    return {
        "service": "MT5 REST API",
        "version": "2.0.0",
        "docs":    "/docs",
        "redoc":   "/redoc",
        "openapi": "/openapi.json",
        "mt5_rpyc_backend": f"{MT5_HOST}:{MT5_PORT}",
    }


@app.get("/api/version", tags=["meta"], summary="MetaTrader 5 build version")
def get_version():
    v = get_mt5().version()
    return {"version": _scalarize(v)}


@app.get("/api/last_error", tags=["meta"], summary="Last MT5 error code")
def get_last_error():
    return {"last_error": list(get_mt5().last_error() or [])}


@app.get("/api/info", tags=["meta"], summary="Combined: version + terminal + account")
def get_info():
    m = get_mt5()
    return {"version": _scalarize(m.version()), "terminal": _named(m.terminal_info()), "account": _named(m.account_info())}


@app.get("/api/terminal", tags=["meta"], summary="Terminal info")
def get_terminal():
    return _named(get_mt5().terminal_info())


@app.get("/api/account", tags=["meta"], summary="Account info")
def get_account():
    a = _named(get_mt5().account_info())
    if a is None:
        raise HTTPException(503, "account_info() returned None — broker not logged in")
    return a


# ─────────────────────────────────────────────────────────────────────────────
# connection
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/connect/login", tags=["connection"], summary="Programmatic broker login")
def post_login(req: LoginRequest):
    """Alternative to GUI login. Saves credentials in MT5 terminal session."""
    m = get_mt5()
    ok = m.login(login=req.login, password=req.password, server=req.server, timeout=req.timeout)
    return {"ok": bool(ok), "last_error": list(m.last_error() or []), "account": _named(m.account_info())}


@app.post("/api/connect/shutdown", tags=["connection"], summary="Disconnect MT5 (force re-init next call)")
def post_shutdown():
    global _mt5
    with _mt5_lock:
        if _mt5 is not None:
            try:
                _mt5.shutdown()
            except Exception:
                pass
            _mt5 = None
    return {"ok": True}


# ─────────────────────────────────────────────────────────────────────────────
# symbols
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/symbols/total", tags=["symbols"], summary="Total number of symbols")
def get_symbols_total():
    return {"total": int(get_mt5().symbols_total())}


@app.get("/api/symbols", tags=["symbols"], summary="List symbols (filter + paginate)")
def list_symbols(
    filter: Optional[str] = Query(None, description="Substring (case-insensitive) on name/description"),
    group:  Optional[str] = Query(None, description="MT5 group mask, e.g. '*USD*' or 'Forex\\\\*'"),
    limit:  int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    m = get_mt5()
    syms = m.symbols_get(group=group) if group else m.symbols_get()
    if filter:
        f = filter.lower()
        syms = [s for s in syms if f in s.name.lower() or f in (s.description or "").lower()]
    total = len(syms)
    page = syms[offset : offset + limit]
    return {
        "total": total, "offset": offset, "limit": limit,
        "items": [{"name": s.name, "description": s.description, "path": s.path,
                   "currency_base": s.currency_base, "currency_profit": s.currency_profit} for s in page],
    }


@app.get("/api/symbols/{symbol}", tags=["symbols"], summary="Full symbol info")
def get_symbol(symbol: str = Path(..., examples=["EURUSD"])):
    m = get_mt5()
    m.symbol_select(symbol, True)
    info = m.symbol_info(symbol)
    if info is None:
        raise HTTPException(404, f"Symbol '{symbol}' not found")
    return _named(info)


@app.post("/api/symbols/{symbol}/select", tags=["symbols"], summary="Add/remove symbol from MarketWatch")
def post_symbol_select(symbol: str, enable: bool = Query(True)):
    ok = bool(get_mt5().symbol_select(symbol, enable))
    return {"symbol": symbol, "enabled": enable, "ok": ok}


@app.get("/api/symbols/{symbol}/tick", tags=["symbols"], summary="Last tick")
def get_tick(symbol: str):
    m = get_mt5()
    m.symbol_select(symbol, True)
    t = m.symbol_info_tick(symbol)
    if t is None:
        raise HTTPException(404, f"No tick for '{symbol}'")
    d = _named(t)
    d["time_iso"] = dt.datetime.fromtimestamp(t.time).isoformat()
    return d


# ─────────────────────────────────────────────────────────────────────────────
# market data — bars
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/symbols/{symbol}/bars", tags=["market-data"], summary="OHLC bars (copy_rates_from_pos)")
def get_bars_pos(
    symbol: str,
    timeframe: str = Query("H1", description="M1 M5 M15 M30 H1 H4 D1 W1 MN1 ..."),
    count: int = Query(100, ge=1, le=10000),
    from_pos: int = Query(0, ge=0),
):
    m = get_mt5()
    m.symbol_select(symbol, True)
    rates = m.copy_rates_from_pos(symbol, _tf(m, timeframe), from_pos, count)
    if rates is None or len(rates) == 0:
        raise HTTPException(404, f"No bars for {symbol} {timeframe}")
    return {"symbol": symbol, "timeframe": timeframe.upper(), "count": len(rates), "bars": _bars_to_list(rates)}


@app.get("/api/symbols/{symbol}/bars/from", tags=["market-data"], summary="OHLC from a specific time backwards (copy_rates_from)")
def get_bars_from(
    symbol: str,
    timeframe: str = Query("H1"),
    from_time: str = Query(..., description="ISO 8601 atau unix seconds"),
    count: int = Query(100, ge=1, le=10000),
):
    m = get_mt5()
    m.symbol_select(symbol, True)
    when = _parse_time(from_time)
    rates = m.copy_rates_from(symbol, _tf(m, timeframe), when, count)
    if rates is None or len(rates) == 0:
        raise HTTPException(404, f"No bars for {symbol} {timeframe} from {from_time}")
    return {"symbol": symbol, "timeframe": timeframe.upper(), "count": len(rates),
            "from": when.isoformat(), "bars": _bars_to_list(rates)}


@app.get("/api/symbols/{symbol}/bars/range", tags=["market-data"], summary="OHLC in time range (copy_rates_range)")
def get_bars_range(
    symbol: str,
    timeframe: str = Query("H1"),
    from_time: str = Query(..., description="ISO 8601 atau unix seconds"),
    to_time:   str = Query(..., description="ISO 8601 atau unix seconds"),
):
    m = get_mt5()
    m.symbol_select(symbol, True)
    a, b = _parse_time(from_time), _parse_time(to_time)
    rates = m.copy_rates_range(symbol, _tf(m, timeframe), a, b)
    if rates is None:
        raise HTTPException(404, f"No bars for {symbol} {timeframe} {a}..{b}")
    return {"symbol": symbol, "timeframe": timeframe.upper(), "from": a.isoformat(), "to": b.isoformat(),
            "count": len(rates), "bars": _bars_to_list(rates)}


# ─────────────────────────────────────────────────────────────────────────────
# indicators — dihitung server-side dari OHLCV (formula MT5/standar)
# ─────────────────────────────────────────────────────────────────────────────

def _indicators_payload(symbol, timeframe, rates, series: bool):
    bars = _bars_to_list(rates)
    if len(bars) < 2:
        raise HTTPException(404, f"Bar tidak cukup untuk indikator {symbol} {timeframe}")
    s = _ind.compute(bars)
    last = len(bars) - 1
    latest = {k: v[last] for k, v in s.items() if k != "time"}
    latest["time"] = bars[last]["time"]
    latest["time_iso"] = dt.datetime.fromtimestamp(bars[last]["time"]).isoformat()
    out = {"symbol": symbol, "timeframe": timeframe.upper(), "count": len(bars),
           "names": [k for k in s.keys() if k != "time"], "latest": latest}
    if series:
        out["indicators"] = s
    return out


@app.get("/api/symbols/{symbol}/indicators", tags=["market-data"],
         summary="Indikator teknikal (RSI/MACD/ADX/Stoch/CCI/BB/ATR/EMA/MFI/OBV dll) dari copy_rates_from_pos")
def get_indicators_pos(
    symbol: str,
    timeframe: str = Query("H1"),
    count: int = Query(300, ge=30, le=10000),
    from_pos: int = Query(0, ge=0),
    series: bool = Query(False, description="True = kembalikan seluruh deret; False = hanya snapshot bar terakhir"),
):
    m = get_mt5()
    m.symbol_select(symbol, True)
    rates = m.copy_rates_from_pos(symbol, _tf(m, timeframe), from_pos, count)
    if rates is None or len(rates) == 0:
        raise HTTPException(404, f"No bars for {symbol} {timeframe}")
    return _indicators_payload(symbol, timeframe, rates, series)


@app.get("/api/symbols/{symbol}/indicators/range", tags=["market-data"],
         summary="Indikator teknikal dalam rentang waktu (copy_rates_range) — untuk backtest")
def get_indicators_range(
    symbol: str,
    timeframe: str = Query("H1"),
    from_time: str = Query(..., description="ISO 8601 atau unix seconds"),
    to_time: str = Query(..., description="ISO 8601 atau unix seconds"),
    series: bool = Query(True),
):
    m = get_mt5()
    m.symbol_select(symbol, True)
    a, b = _parse_time(from_time), _parse_time(to_time)
    rates = m.copy_rates_range(symbol, _tf(m, timeframe), a, b)
    if rates is None or len(rates) == 0:
        raise HTTPException(404, f"No bars for {symbol} {timeframe} {a}..{b}")
    out = _indicators_payload(symbol, timeframe, rates, series)
    out["from"] = a.isoformat(); out["to"] = b.isoformat()
    return out


# ─────────────────────────────────────────────────────────────────────────────
# market data — ticks
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/symbols/{symbol}/ticks/from", tags=["market-data"], summary="Tick stream from time (copy_ticks_from)")
def get_ticks_from(
    symbol: str,
    from_time: str = Query(..., description="ISO 8601 atau unix seconds"),
    count: int = Query(1000, ge=1, le=100000),
    flags: str = Query("ALL", description="ALL | INFO | TRADE"),
):
    m = get_mt5()
    m.symbol_select(symbol, True)
    flag = getattr(m, f"COPY_TICKS_{flags.upper()}", m.COPY_TICKS_ALL)
    ticks = m.copy_ticks_from(symbol, _parse_time(from_time), count, flag)
    if ticks is None:
        raise HTTPException(404, f"No ticks for {symbol}")
    return {"symbol": symbol, "count": len(ticks), "from": from_time, "flags": flags.upper(),
            "ticks": _ticks_to_list(ticks)}


@app.get("/api/symbols/{symbol}/ticks/range", tags=["market-data"], summary="Tick stream in time range (copy_ticks_range)")
def get_ticks_range(
    symbol: str,
    from_time: str = Query(...),
    to_time:   str = Query(...),
    flags: str = Query("ALL", description="ALL | INFO | TRADE"),
):
    m = get_mt5()
    m.symbol_select(symbol, True)
    flag = getattr(m, f"COPY_TICKS_{flags.upper()}", m.COPY_TICKS_ALL)
    a, b = _parse_time(from_time), _parse_time(to_time)
    ticks = m.copy_ticks_range(symbol, a, b, flag)
    if ticks is None:
        raise HTTPException(404, f"No ticks for {symbol} {a}..{b}")
    return {"symbol": symbol, "count": len(ticks), "from": a.isoformat(), "to": b.isoformat(),
            "flags": flags.upper(), "ticks": _ticks_to_list(ticks)}


# ─────────────────────────────────────────────────────────────────────────────
# order book / DOM
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/symbols/{symbol}/book/subscribe", tags=["order-book"], summary="Subscribe to DOM L2 (market_book_add)")
def book_subscribe(symbol: str):
    ok = bool(get_mt5().market_book_add(symbol))
    if not ok:
        raise HTTPException(400, {"msg": "market_book_add failed", "last_error": list(get_mt5().last_error() or [])})
    return {"symbol": symbol, "subscribed": True}


@app.get("/api/symbols/{symbol}/book", tags=["order-book"], summary="Get current DOM snapshot (market_book_get)")
def book_get(symbol: str):
    m = get_mt5()
    rows = m.market_book_get(symbol)
    if rows is None:
        raise HTTPException(400, {"msg": "market_book_get returned None — call subscribe first?",
                                  "last_error": list(m.last_error() or [])})
    return {"symbol": symbol, "depth": len(rows), "items": _named_list(rows)}


@app.post("/api/symbols/{symbol}/book/unsubscribe", tags=["order-book"], summary="Release DOM subscription (market_book_release)")
def book_release(symbol: str):
    ok = bool(get_mt5().market_book_release(symbol))
    return {"symbol": symbol, "released": ok}


# ─────────────────────────────────────────────────────────────────────────────
# positions
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/positions/total", tags=["positions"], summary="Total open positions count")
def positions_total():
    return {"total": int(get_mt5().positions_total())}


@app.get("/api/positions", tags=["positions"], summary="Open positions")
def get_positions(
    symbol: Optional[str] = Query(None),
    group:  Optional[str] = Query(None, description="Mask, e.g. '*USD*'"),
    ticket: Optional[int] = Query(None),
):
    m = get_mt5()
    if ticket is not None:
        poss = m.positions_get(ticket=ticket)
    elif group is not None:
        poss = m.positions_get(group=group)
    elif symbol is not None:
        poss = m.positions_get(symbol=symbol)
    else:
        poss = m.positions_get()
    return {"count": len(poss) if poss else 0, "items": _named_list(poss)}


@app.get("/api/positions/{ticket}", tags=["positions"], summary="Position by ticket")
def get_position_by_ticket(ticket: int):
    poss = get_mt5().positions_get(ticket=ticket)
    if not poss:
        raise HTTPException(404, f"No open position with ticket {ticket}")
    return _named(poss[0])


# ─────────────────────────────────────────────────────────────────────────────
# orders (pending)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/orders/total", tags=["orders"], summary="Total pending orders count")
def orders_total():
    return {"total": int(get_mt5().orders_total())}


@app.get("/api/orders", tags=["orders"], summary="Pending orders")
def get_orders(
    symbol: Optional[str] = Query(None),
    group:  Optional[str] = Query(None),
    ticket: Optional[int] = Query(None),
):
    m = get_mt5()
    if ticket is not None:
        ords = m.orders_get(ticket=ticket)
    elif group is not None:
        ords = m.orders_get(group=group)
    elif symbol is not None:
        ords = m.orders_get(symbol=symbol)
    else:
        ords = m.orders_get()
    return {"count": len(ords) if ords else 0, "items": _named_list(ords)}


# NOTE: /api/orders/{ticket} moved to BOTTOM of the file (after all trading
# routes) — otherwise it shadows /api/orders/history, /api/orders/check, etc.
# See bottom of file.


# ─────────────────────────────────────────────────────────────────────────────
# history
# ─────────────────────────────────────────────────────────────────────────────

def _date_range(days: int, from_time: Optional[str], to_time: Optional[str]):
    if from_time and to_time:
        return _parse_time(from_time), _parse_time(to_time)
    end = dt.datetime.now()
    return end - dt.timedelta(days=days), end


@app.get("/api/deals/total", tags=["history"], summary="Total deals count in range")
def deals_total(
    days: int = Query(7, ge=1, le=3650),
    from_time: Optional[str] = Query(None),
    to_time:   Optional[str] = Query(None),
):
    a, b = _date_range(days, from_time, to_time)
    return {"total": int(get_mt5().history_deals_total(a, b)), "from": a.isoformat(), "to": b.isoformat()}


@app.get("/api/deals", tags=["history"], summary="Deal history (history_deals_get)")
def get_deals(
    days: int = Query(7, ge=1, le=3650),
    from_time: Optional[str] = Query(None),
    to_time:   Optional[str] = Query(None),
    group:  Optional[str] = Query(None, description="Symbol mask, e.g. '*USD*'"),
    ticket: Optional[int] = Query(None),
    position: Optional[int] = Query(None, description="Position ticket"),
):
    m = get_mt5()
    a, b = _date_range(days, from_time, to_time)
    if ticket is not None:
        deals = m.history_deals_get(ticket=ticket)
    elif position is not None:
        deals = m.history_deals_get(position=position)
    elif group is not None:
        deals = m.history_deals_get(a, b, group=group)
    else:
        deals = m.history_deals_get(a, b)
    items = _named_list(deals)
    for it, src in zip(items, (deals or [])):
        if it and hasattr(src, "time"):
            it["time_iso"] = dt.datetime.fromtimestamp(src.time).isoformat()
    return {"count": len(items), "from": a.isoformat(), "to": b.isoformat(), "items": items}


@app.get("/api/orders/history/total", tags=["history"], summary="Total order history count")
def order_history_total(
    days: int = Query(7, ge=1, le=3650),
    from_time: Optional[str] = Query(None),
    to_time:   Optional[str] = Query(None),
):
    a, b = _date_range(days, from_time, to_time)
    return {"total": int(get_mt5().history_orders_total(a, b)), "from": a.isoformat(), "to": b.isoformat()}


@app.get("/api/orders/history", tags=["history"], summary="Past orders (history_orders_get)")
def get_order_history(
    days: int = Query(7, ge=1, le=3650),
    from_time: Optional[str] = Query(None),
    to_time:   Optional[str] = Query(None),
    group:  Optional[str] = Query(None),
    ticket: Optional[int] = Query(None),
    position: Optional[int] = Query(None),
):
    m = get_mt5()
    a, b = _date_range(days, from_time, to_time)
    if ticket is not None:
        orders = m.history_orders_get(ticket=ticket)
    elif position is not None:
        orders = m.history_orders_get(position=position)
    elif group is not None:
        orders = m.history_orders_get(a, b, group=group)
    else:
        orders = m.history_orders_get(a, b)
    return {"count": len(orders) if orders else 0, "from": a.isoformat(), "to": b.isoformat(),
            "items": _named_list(orders)}


# ─────────────────────────────────────────────────────────────────────────────
# trading helpers
# ─────────────────────────────────────────────────────────────────────────────

def _market_request(m: MetaTrader5, req: MarketOrderRequest) -> dict:
    m.symbol_select(req.symbol, True)
    tick = m.symbol_info_tick(req.symbol)
    if tick is None:
        raise HTTPException(404, f"No tick for '{req.symbol}'")
    order_type = m.ORDER_TYPE_BUY if req.side == "buy" else m.ORDER_TYPE_SELL
    price = tick.ask if req.side == "buy" else tick.bid
    filling = req.type_filling if req.type_filling is not None else _pick_filling_mode(m, req.symbol)
    return dict(
        action=m.TRADE_ACTION_DEAL, symbol=req.symbol, volume=req.volume,
        type=order_type, price=price, sl=req.sl, tp=req.tp,
        deviation=req.deviation, magic=req.magic, comment=req.comment,
        type_time=m.ORDER_TIME_GTC, type_filling=filling,
    )


def _pending_request(m: MetaTrader5, req: PendingOrderRequest) -> dict:
    m.symbol_select(req.symbol, True)
    type_map = {
        "buy_limit":  m.ORDER_TYPE_BUY_LIMIT,
        "sell_limit": m.ORDER_TYPE_SELL_LIMIT,
        "buy_stop":   m.ORDER_TYPE_BUY_STOP,
        "sell_stop":  m.ORDER_TYPE_SELL_STOP,
        "buy_stop_limit":  m.ORDER_TYPE_BUY_STOP_LIMIT,
        "sell_stop_limit": m.ORDER_TYPE_SELL_STOP_LIMIT,
    }
    order_type = type_map[req.order_type]
    filling = req.type_filling if req.type_filling is not None else _pick_filling_mode(m, req.symbol)
    type_time = m.ORDER_TIME_SPECIFIED if req.expiration else m.ORDER_TIME_GTC
    return dict(
        action=m.TRADE_ACTION_PENDING, symbol=req.symbol, volume=req.volume,
        type=order_type, price=req.price, stoplimit=req.stoplimit,
        sl=req.sl, tp=req.tp, deviation=req.deviation, magic=req.magic,
        comment=req.comment, type_time=type_time,
        expiration=int(req.expiration) if req.expiration else 0,
        type_filling=filling,
    )


def _send(m: MetaTrader5, request: dict, dry: bool):
    # mt5linux 1.0.3 asymmetry:
    #   order_check NEEDS kwargs   (dict-positional → "Unnamed arguments not allowed")
    #   order_send  NEEDS positional dict  (kwargs → "unexpected keyword argument 'action'")
    if dry:
        check = m.order_check(**request)
        if check is None:
            raise HTTPException(400, {"msg": "order_check returned None", "last_error": list(m.last_error() or []), "request": request})
        return {"request": request, "result": _named(check)}
    result = m.order_send(request)
    if result is None:
        raise HTTPException(400, {"msg": "order_send returned None", "last_error": list(m.last_error() or []), "request": request})
    out = {"request": request, "result": _named(result)}
    if result.retcode != m.TRADE_RETCODE_DONE:
        raise HTTPException(400, {**out, "msg": f"order_send failed retcode={result.retcode}"})
    return out


# ─────────────────────────────────────────────────────────────────────────────
# trading endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/orders/check", tags=["trading"], summary="Dry-run market order (order_check)")
def post_order_check(req: MarketOrderRequest):
    m = get_mt5()
    return _send(m, _market_request(m, req), dry=True)


@app.post("/api/orders/send", tags=["trading"], summary="LIVE market order (order_send) — irreversible")
def post_order_send(req: MarketOrderRequest):
    m = get_mt5()
    return _send(m, _market_request(m, req), dry=False)


@app.post("/api/orders/pending/check", tags=["trading"], summary="Dry-run pending order")
def post_pending_check(req: PendingOrderRequest):
    m = get_mt5()
    return _send(m, _pending_request(m, req), dry=True)


@app.post("/api/orders/pending/send", tags=["trading"], summary="LIVE pending order (limit/stop/stop-limit)")
def post_pending_send(req: PendingOrderRequest):
    m = get_mt5()
    return _send(m, _pending_request(m, req), dry=False)


@app.post("/api/orders/modify", tags=["trading"], summary="Modify pending order (price/SL/TP/expiration)")
def post_modify_order(req: ModifyOrderRequest):
    m = get_mt5()
    ords = m.orders_get(ticket=req.ticket)
    if not ords:
        raise HTTPException(404, f"No pending order with ticket {req.ticket}")
    o = ords[0]
    type_time = m.ORDER_TIME_SPECIFIED if req.expiration else m.ORDER_TIME_GTC
    request = dict(
        action=m.TRADE_ACTION_MODIFY,
        order=o.ticket,
        symbol=o.symbol,
        price=req.price if req.price is not None else o.price_open,
        stoplimit=req.stoplimit if req.stoplimit is not None else o.price_stoplimit,
        sl=req.sl if req.sl is not None else o.sl,
        tp=req.tp if req.tp is not None else o.tp,
        type_time=type_time,
        expiration=int(req.expiration) if req.expiration else 0,
        type_filling=_pick_filling_mode(m, o.symbol),
    )
    return _send(m, request, dry=False)


@app.post("/api/orders/cancel", tags=["trading"], summary="Cancel pending order")
def post_cancel(req: CancelRequest):
    m = get_mt5()
    request = dict(action=m.TRADE_ACTION_REMOVE, order=req.ticket)
    return _send(m, request, dry=False)


@app.post("/api/positions/modify", tags=["trading"], summary="Modify position SL / TP")
def post_modify_position(req: ModifyPositionRequest):
    m = get_mt5()
    poss = m.positions_get(ticket=req.ticket)
    if not poss:
        raise HTTPException(404, f"No open position with ticket {req.ticket}")
    p = poss[0]
    request = dict(
        action=m.TRADE_ACTION_SLTP,
        position=p.ticket,
        symbol=p.symbol,
        sl=req.sl,
        tp=req.tp,
    )
    return _send(m, request, dry=False)


@app.post("/api/positions/close", tags=["trading"], summary="Close position by ticket")
def post_close(req: CloseRequest):
    m = get_mt5()
    poss = m.positions_get(ticket=req.ticket)
    if not poss:
        raise HTTPException(404, f"No open position with ticket {req.ticket}")
    p = poss[0]
    m.symbol_select(p.symbol, True)
    tick = m.symbol_info_tick(p.symbol)
    close_type = m.ORDER_TYPE_SELL if p.type == m.POSITION_TYPE_BUY else m.ORDER_TYPE_BUY
    price = tick.bid if close_type == m.ORDER_TYPE_SELL else tick.ask
    volume = req.volume if req.volume is not None else p.volume
    request = dict(
        action=m.TRADE_ACTION_DEAL, position=p.ticket, symbol=p.symbol, volume=volume,
        type=close_type, price=price, deviation=req.deviation, magic=p.magic,
        comment=req.comment, type_time=m.ORDER_TIME_GTC,
        type_filling=_pick_filling_mode(m, p.symbol),
    )
    return _send(m, request, dry=False)


# ─────────────────────────────────────────────────────────────────────────────
# calculators
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/calc/margin", tags=["calculators"], summary="Required margin for a hypothetical order (order_calc_margin)")
def post_calc_margin(req: CalcMarginRequest):
    m = get_mt5()
    m.symbol_select(req.symbol, True)
    order_type = m.ORDER_TYPE_BUY if req.side == "buy" else m.ORDER_TYPE_SELL
    price = req.price
    if price is None:
        tick = m.symbol_info_tick(req.symbol)
        price = tick.ask if req.side == "buy" else tick.bid
    margin = m.order_calc_margin(order_type, req.symbol, req.volume, price)
    if margin is None:
        raise HTTPException(400, {"msg": "order_calc_margin returned None", "last_error": list(m.last_error() or [])})
    return {"symbol": req.symbol, "volume": req.volume, "side": req.side, "price": price,
            "margin": float(margin), "currency": m.account_info().currency}


@app.post("/api/calc/profit", tags=["calculators"], summary="Hypothetical profit for an order (order_calc_profit)")
def post_calc_profit(req: CalcProfitRequest):
    m = get_mt5()
    m.symbol_select(req.symbol, True)
    order_type = m.ORDER_TYPE_BUY if req.side == "buy" else m.ORDER_TYPE_SELL
    profit = m.order_calc_profit(order_type, req.symbol, req.volume, req.price_open, req.price_close)
    if profit is None:
        raise HTTPException(400, {"msg": "order_calc_profit returned None", "last_error": list(m.last_error() or [])})
    return {"symbol": req.symbol, "volume": req.volume, "side": req.side,
            "price_open": req.price_open, "price_close": req.price_close,
            "profit": float(profit), "currency": m.account_info().currency}


# ─────────────────────────────────────────────────────────────────────────────
# constants — enumeration introspection
# ─────────────────────────────────────────────────────────────────────────────

_CONSTANT_GROUPS = [
    "TIMEFRAME", "ORDER_TYPE", "ORDER_FILLING", "ORDER_TIME", "ORDER_REASON",
    "ORDER_STATE", "TRADE_ACTION", "TRADE_RETCODE",
    "POSITION_TYPE", "POSITION_REASON",
    "DEAL_TYPE", "DEAL_ENTRY", "DEAL_REASON",
    "SYMBOL_CALC_MODE", "SYMBOL_CHART_MODE", "SYMBOL_OPTION_MODE",
    "SYMBOL_OPTION_RIGHT", "SYMBOL_ORDERS", "SYMBOL_SWAP_MODE",
    "SYMBOL_TRADE_EXECUTION", "SYMBOL_TRADE_MODE",
    "BOOK_TYPE", "DAY_OF_WEEK", "COPY_TICKS",
    "ACCOUNT_TRADE_MODE", "ACCOUNT_STOPOUT_MODE", "ACCOUNT_MARGIN_MODE",
]


def _enum_dict(mt5: MetaTrader5, prefix: str) -> dict:
    pre = prefix.upper() + "_"
    out = {}
    for name in dir(mt5):
        if name.startswith(pre):
            try:
                v = getattr(mt5, name)
                if isinstance(v, (int, str)):
                    out[name] = v
            except Exception:
                pass
    return out


@app.get("/api/constants", tags=["constants"], summary="All MT5 enum groups available")
def list_constants():
    return {"groups": _CONSTANT_GROUPS, "hint": "GET /api/constants/{group} untuk value-nya"}


@app.get("/api/constants/{group}", tags=["constants"], summary="Enum values for a single group")
def get_constants(group: str):
    m = get_mt5()
    if group.upper() not in [g.upper() for g in _CONSTANT_GROUPS]:
        # still allow — introspection by any prefix
        pass
    d = _enum_dict(m, group)
    if not d:
        raise HTTPException(404, f"No constants matching prefix '{group}_'")
    return {"group": group.upper(), "count": len(d), "values": d}


# ─────────────────────────────────────────────────────────────────────────────
# greedy path-param routes — registered LAST so specific paths above win
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/orders/{ticket}", tags=["orders"], summary="Pending order by ticket")
def get_order_by_ticket(ticket: int):
    ords = get_mt5().orders_get(ticket=ticket)
    if not ords:
        raise HTTPException(404, f"No pending order with ticket {ticket}")
    return _named(ords[0])


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mt5_api:app", host=os.getenv("API_HOST", "0.0.0.0"),
                port=int(os.getenv("API_PORT", "8000")), log_level="info")
