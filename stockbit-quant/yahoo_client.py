"""
yahoo_client.py — History OHLC dalam (5thn+) saham Indonesia via Yahoo Finance (.JK).
Untuk BACKTEST (Stockbit cuma ~92 candle; Yahoo ~1200 = 5thn). Gratis, tanpa auth.
Format bar sama dgn stockbit_client (interop dgn idx_indicators/idx_backtest).
"""
from __future__ import annotations
import requests


def candles(symbol: str, rng: str = "5y", interval: str = "1d") -> list[dict]:
    """symbol tanpa .JK (mis 'BBCA') — otomatis ditambah .JK. Return list bar OHLCV."""
    sj = symbol if symbol.endswith(".JK") else f"{symbol}.JK"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sj}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"},
                     params={"range": rng, "interval": interval}, timeout=20)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    ts = res["timestamp"]; q = res["indicators"]["quote"][0]
    import datetime as dt
    out = []
    for i, t in enumerate(ts):
        o, h, l, c, v = q["open"][i], q["high"][i], q["low"][i], q["close"][i], q["volume"][i]
        if None in (o, h, l, c):
            continue
        out.append({"time": int(t), "date": dt.datetime.fromtimestamp(t).strftime("%Y-%m-%d"),
                    "open": float(o), "high": float(h), "low": float(l), "close": float(c),
                    "volume": float(v or 0)})
    return out


if __name__ == "__main__":
    import sys
    s = sys.argv[1] if len(sys.argv) > 1 else "BBCA"
    c = candles(s)
    print(f"{s}.JK: {len(c)} candle | {c[0]['date']} → {c[-1]['date']}")
