"""
Sweep test untuk semua endpoint MT5 API.

Strategy:
- GET endpoints: hit with sensible defaults
- POST /check / dry-run: safe (no order placed)
- LIVE trading endpoints: place a tiny $0.01 lot EURUSD market order,
  modify SL/TP, then close it. Then place a pending order, modify, cancel.
- Book: subscribe → get → release
- Report pass/fail per endpoint with status code + first 200 chars of body
"""
from __future__ import annotations
import datetime as dt
import json
import sys
import time
import urllib.request
import urllib.error

BASE = "http://192.168.0.116:8000"
TEST_SYMBOL = "EURUSD"
TEST_TIMEFRAME = "M5"

results: list[tuple[str, str, str, int, str]] = []  # (group, op, path, status, summary)


def req(method: str, path: str, body=None, query: str = "") -> tuple[int, dict | str]:
    url = f"{BASE}{path}{query}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    r = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            payload = resp.read().decode(errors="replace")
            try:
                return resp.status, json.loads(payload)
            except json.JSONDecodeError:
                return resp.status, payload
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body
    except Exception as e:
        return 0, f"EXC {type(e).__name__}: {e}"


def record(group: str, label: str, status: int, payload, *, ok_statuses=(200,)) -> None:
    ok = status in ok_statuses
    summary = ""
    if isinstance(payload, dict):
        keys = list(payload.keys())[:5]
        summary = "{" + ", ".join(f"{k}=..." for k in keys) + "}" if keys else "{}"
    elif isinstance(payload, list):
        summary = f"list({len(payload)})"
    else:
        summary = str(payload)[:120].replace("\n", " ")
    results.append((group, label, "PASS" if ok else "FAIL", status, summary))


def run() -> None:
    # ── meta ────────────────────────────────────────────────
    for path in ["/", "/api/version", "/api/last_error", "/api/info", "/api/terminal", "/api/account"]:
        s, p = req("GET", path)
        record("meta", f"GET {path}", s, p)

    # ── symbols ─────────────────────────────────────────────
    record("symbols", "GET /api/symbols/total",      *req("GET", "/api/symbols/total"))
    record("symbols", "GET /api/symbols (paginate)", *req("GET", "/api/symbols", query="?limit=5&filter=USD"))
    record("symbols", f"GET /api/symbols/{TEST_SYMBOL}",   *req("GET", f"/api/symbols/{TEST_SYMBOL}"))
    record("symbols", f"GET /api/symbols/{TEST_SYMBOL}/tick", *req("GET", f"/api/symbols/{TEST_SYMBOL}/tick"))
    record("symbols", f"POST /api/symbols/{TEST_SYMBOL}/select", *req("POST", f"/api/symbols/{TEST_SYMBOL}/select", query="?enable=true"))

    # ── market data ─────────────────────────────────────────
    now = int(time.time())
    yesterday = now - 86400
    record("market-data", "GET /bars (from_pos)",   *req("GET", f"/api/symbols/{TEST_SYMBOL}/bars", query=f"?timeframe={TEST_TIMEFRAME}&count=10"))
    record("market-data", "GET /bars/from",         *req("GET", f"/api/symbols/{TEST_SYMBOL}/bars/from", query=f"?timeframe={TEST_TIMEFRAME}&from_time={now}&count=10"))
    record("market-data", "GET /bars/range",        *req("GET", f"/api/symbols/{TEST_SYMBOL}/bars/range", query=f"?timeframe={TEST_TIMEFRAME}&from_time={yesterday}&to_time={now}"))
    record("market-data", "GET /ticks/from",        *req("GET", f"/api/symbols/{TEST_SYMBOL}/ticks/from", query=f"?from_time={now-300}&count=50"))
    record("market-data", "GET /ticks/range",       *req("GET", f"/api/symbols/{TEST_SYMBOL}/ticks/range", query=f"?from_time={now-600}&to_time={now}"))

    # ── order book ──────────────────────────────────────────
    s, p = req("POST", f"/api/symbols/{TEST_SYMBOL}/book/subscribe")
    record("order-book", "POST /book/subscribe", s, p, ok_statuses=(200, 400))  # 400 acceptable if broker doesn't push DOM for FX
    if s == 200:
        time.sleep(2)  # let DOM populate
        record("order-book", "GET /book",            *req("GET",  f"/api/symbols/{TEST_SYMBOL}/book"), ok_statuses=(200, 400))
        record("order-book", "POST /book/unsubscribe", *req("POST", f"/api/symbols/{TEST_SYMBOL}/book/unsubscribe"))

    # ── positions / orders (read) ───────────────────────────
    record("positions", "GET /api/positions/total", *req("GET", "/api/positions/total"))
    record("positions", "GET /api/positions",       *req("GET", "/api/positions"))
    record("orders",    "GET /api/orders/total",    *req("GET", "/api/orders/total"))
    record("orders",    "GET /api/orders",          *req("GET", "/api/orders"))

    # ── history ─────────────────────────────────────────────
    record("history", "GET /api/deals/total",            *req("GET", "/api/deals/total", query="?days=30"))
    record("history", "GET /api/deals",                  *req("GET", "/api/deals", query="?days=30"))
    record("history", "GET /api/orders/history/total",   *req("GET", "/api/orders/history/total", query="?days=30"))
    record("history", "GET /api/orders/history",         *req("GET", "/api/orders/history", query="?days=30"))

    # ── calculators ─────────────────────────────────────────
    record("calculators", "POST /api/calc/margin", *req("POST", "/api/calc/margin", body={"symbol": TEST_SYMBOL, "volume": 0.01, "side": "buy"}))
    record("calculators", "POST /api/calc/profit", *req("POST", "/api/calc/profit", body={"symbol": TEST_SYMBOL, "volume": 0.01, "side": "buy", "price_open": 1.16, "price_close": 1.17}))

    # ── constants ───────────────────────────────────────────
    record("constants", "GET /api/constants",                  *req("GET", "/api/constants"))
    record("constants", "GET /api/constants/TIMEFRAME",        *req("GET", "/api/constants/TIMEFRAME"))
    record("constants", "GET /api/constants/TRADE_RETCODE",    *req("GET", "/api/constants/TRADE_RETCODE"))
    record("constants", "GET /api/constants/ORDER_FILLING",    *req("GET", "/api/constants/ORDER_FILLING"))

    # ── trading: market check ───────────────────────────────
    market_buy = {"symbol": TEST_SYMBOL, "volume": 0.01, "side": "buy", "comment": "test_all"}
    record("trading", "POST /api/orders/check (market buy)", *req("POST", "/api/orders/check", body=market_buy))

    # ── trading: pending check ──────────────────────────────
    tick_status, tick = req("GET", f"/api/symbols/{TEST_SYMBOL}/tick")
    far_price = round(tick["ask"] - 0.05, 5) if isinstance(tick, dict) else 1.10
    pending_buy = {
        "symbol": TEST_SYMBOL, "volume": 0.01, "order_type": "buy_limit",
        "price": far_price, "comment": "test_all_pending",
    }
    record("trading", "POST /api/orders/pending/check", *req("POST", "/api/orders/pending/check", body=pending_buy))

    # ── trading: live cycle (market buy → modify SL/TP → close) ──
    live_buy = {**market_buy, "comment": "test_all_live"}
    s, p = req("POST", "/api/orders/send", body=live_buy)
    record("trading", "POST /api/orders/send (LIVE market buy)", s, p)
    if s == 200 and isinstance(p, dict):
        # extract position ticket from result
        try:
            order_ticket = p["result"]["order"]
        except (KeyError, TypeError):
            order_ticket = None
        # need to look up the position ticket (different from order ticket sometimes)
        time.sleep(2)
        s_pos, p_pos = req("GET", "/api/positions")
        position_ticket = None
        if isinstance(p_pos, dict) and p_pos.get("items"):
            for it in p_pos["items"]:
                if it.get("comment") == "test_all_live":
                    position_ticket = it.get("ticket")
                    break
            if position_ticket is None:
                position_ticket = p_pos["items"][-1].get("ticket")

        if position_ticket:
            # modify SL/TP on the position
            tick_now_status, tick_now = req("GET", f"/api/symbols/{TEST_SYMBOL}/tick")
            if isinstance(tick_now, dict):
                bid = tick_now["bid"]
                sl = round(bid - 0.01, 5)
                tp = round(bid + 0.01, 5)
                record("trading", "POST /api/positions/modify", *req("POST", "/api/positions/modify", body={"ticket": position_ticket, "sl": sl, "tp": tp}))
                record("trading", f"GET /api/positions/{{ticket}}", *req("GET", f"/api/positions/{position_ticket}"))
            # close it
            record("trading", "POST /api/positions/close", *req("POST", "/api/positions/close", body={"ticket": position_ticket, "comment": "test_all close"}))

    # ── trading: pending lifecycle ──────────────────────────
    s, p = req("POST", "/api/orders/pending/send", body=pending_buy)
    record("trading", "POST /api/orders/pending/send (LIVE pending)", s, p)
    if s == 200 and isinstance(p, dict):
        try:
            pending_ticket = p["result"]["order"]
        except (KeyError, TypeError):
            pending_ticket = None
        if pending_ticket:
            record("trading", "GET /api/orders/{ticket}", *req("GET", f"/api/orders/{pending_ticket}"))
            new_price = round(far_price - 0.01, 5)
            record("trading", "POST /api/orders/modify",
                   *req("POST", "/api/orders/modify", body={"ticket": pending_ticket, "price": new_price}))
            record("trading", "POST /api/orders/cancel",
                   *req("POST", "/api/orders/cancel", body={"ticket": pending_ticket}))

    # ── connection (test login/shutdown last; harmless if same account re-login) ──
    # Skip POST /api/connect/login by default — needs real broker creds
    # We test /shutdown then a subsequent /api/info to verify auto-reinit
    record("connection", "POST /api/connect/shutdown", *req("POST", "/api/connect/shutdown"))
    record("connection", "GET /api/info (post-shutdown reinit)", *req("GET", "/api/info"))


def print_results() -> int:
    pass_n = sum(1 for r in results if r[2] == "PASS")
    fail_n = sum(1 for r in results if r[2] == "FAIL")
    last_group = None
    for grp, op, status, code, summary in results:
        if grp != last_group:
            print(f"\n[{grp}]")
            last_group = grp
        marker = "✓" if status == "PASS" else "✗"
        print(f"  {marker} {status}  {code:3d}  {op:55s}  {summary[:80]}")
    print(f"\n{pass_n} passed / {fail_n} failed / {len(results)} total")
    return 0 if fail_n == 0 else 1


if __name__ == "__main__":
    run()
    sys.exit(print_results())
