# MT5 Client (Mac → CT 132)

Python client untuk MT5 yang jalan di CT 132 (192.168.0.116:8001).

## Setup (one-time)

```bash
cd mt5-client
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Pakai

Smoke test (default — cek koneksi + info ringkas):

```bash
./venv/bin/python mt5_client.py
```

Subcommand:

```bash
./venv/bin/python mt5_client.py info               # account + terminal
./venv/bin/python mt5_client.py symbols            # list symbols
./venv/bin/python mt5_client.py tick EURUSD        # last tick
./venv/bin/python mt5_client.py bars EURUSD H1     # OHLC 100 bar
./venv/bin/python mt5_client.py bars XAUUSD M5 --count 500
./venv/bin/python mt5_client.py positions          # open positions
./venv/bin/python mt5_client.py orders             # pending orders
./venv/bin/python mt5_client.py history --days 30  # deal history
./venv/bin/python mt5_client.py buy EURUSD 0.01    # market buy (DRY RUN default)
./venv/bin/python mt5_client.py buy EURUSD 0.01 --no-dry-run   # LIVE buy
./venv/bin/python mt5_client.py sell EURUSD 0.01 --no-dry-run  # LIVE sell
```

## Override host/port

```bash
./venv/bin/python mt5_client.py --host 10.0.0.5 --port 8001 info
```

## Pertama kali jalan

Kalau `initialize()` return `False` + last_error `(-10004, 'No IPC connection')`:

→ MT5 terminal GUI belum login broker. Buka **http://192.168.0.116:3000** di browser, klik **Connect**, lalu **File → Login to Trade Account**. Setelah broker login berhasil, script ini akan dapat semua API.

## Pakai sebagai library

```python
from mt5_client import connect

with connect() as mt5:
    print(mt5.account_info())
    rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M1, 0, 1000)
    # ... seperti MetaTrader5 package native di Windows
```

## 2 hal penting (RPyC + broker quirks)

### 1) `order_check` / `order_send` HARUS kwargs, BUKAN dict positional

mt5linux RPyC bridge tidak bisa transmit dict-positional ke MT5 Windows:

```python
# ❌ TIDAK JALAN: returns None, last_error = (-2, 'Unnamed arguments not allowed')
mt5.order_check({"action": ..., "symbol": ...})

# ✅ JALAN
request = dict(action=mt5.TRADE_ACTION_DEAL, symbol="EURUSD", ...)
mt5.order_check(**request)
mt5.order_send(**request)
```

### 2) Auto-detect filling mode (broker-dependent)

Default `ORDER_FILLING_IOC` ditolak Exness (retcode 10030 "Unsupported filling mode").
Pakai bitmask `symbol_info.filling_mode`:

```python
mask = mt5.symbol_info(symbol).filling_mode
# 1=FOK, 2=IOC, 4=RETURN
filling = mt5.ORDER_FILLING_FOK if mask & 1 else mt5.ORDER_FILLING_IOC
```

Helper `_pick_filling_mode()` di `mt5_client.py` sudah handle ini.
