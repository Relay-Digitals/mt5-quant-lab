"""
stockbit_client.py — Client data saham Indonesia via Stockbit API (exodus.stockbit.com).
TERPISAH dari kode forex (mt5-client/). Ambil candlestick OHLC harian.

Auth: token dari ../stockbit-docs/stockbit_token.env (STOCKBIT_ACCESS_TOKEN).
Candlestick: charts/{symbol}/daily?timeframe=1Y&chart_type=PRICE_CHART_TYPE_CANDLE
  → ~92 candle harian (≈5 bulan, batas history Stockbit). OHLC+volume.
"""
from __future__ import annotations

import os
import requests

_DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stockbit-docs")


def _load_token() -> tuple[str, str]:
    env = os.path.join(_DOCS, "stockbit_token.env")
    tok = base = None
    for line in open(env):
        if line.startswith("STOCKBIT_ACCESS_TOKEN="):
            tok = line.split("=", 1)[1].strip()
        elif line.startswith("STOCKBIT_BASE_URL="):
            base = line.split("=", 1)[1].strip()
    return tok, (base or "https://exodus.stockbit.com")


class Stockbit:
    def __init__(self):
        self.token, self.base = _load_token()
        self.h = {
            "User-Agent": "okhttp/4.12.0",           # WAJIB (Cloudflare 1010 tanpa ini)
            "Authorization": f"Bearer {self.token}",
            "X-AppVersion": "3.21.0",
            "X-Platform": "android",
            "Accept-Language": "id",
        }
        self.s = requests.Session()

    def candles(self, symbol: str, timeframe: str = "1Y") -> list[dict]:
        """Candlestick harian OHLC. Return list dict {date(unix s), date_str, open, high, low, close, volume}."""
        url = f"{self.base}/charts/{symbol}/daily"
        r = self.s.get(url, headers=self.h, timeout=20,
                       params={"timeframe": timeframe, "chart_type": "PRICE_CHART_TYPE_CANDLE"})
        r.raise_for_status()
        prices = r.json().get("data", {}).get("prices", [])
        out = []
        for p in prices:
            if not p.get("open"):       # skip non-OHLC point
                continue
            try:
                out.append({
                    "time": int(p["date"]) // 1000,
                    "date": p.get("formatted_date", ""),
                    "open": float(p["open"]), "high": float(p["high"]),
                    "low": float(p["low"]), "close": float(p["value"]),
                    "volume": float(p.get("volume") or 0),
                })
            except (ValueError, KeyError, TypeError):
                continue
        return out


if __name__ == "__main__":
    import sys
    sb = Stockbit()
    sym = sys.argv[1] if len(sys.argv) > 1 else "BBCA"
    c = sb.candles(sym)
    print(f"{sym}: {len(c)} candle | {c[0]['date']} → {c[-1]['date']}")
    print("last 3:")
    for x in c[-3:]:
        print(f"  {x['date']}  O{x['open']:.0f} H{x['high']:.0f} L{x['low']:.0f} C{x['close']:.0f} vol{x['volume']:.0f}")
