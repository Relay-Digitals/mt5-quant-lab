"""
mp_brk_m1.py — LIVE runner: Market-Profile BREAKOUT, XAUUSD M1 (magic 770015).

Rebuilt 2026-07-07 from the persisted spec (memory mt5-api-ip-111) after the
homelab host died; identical logic to the CT108 live version:

  • Rolling 24h volume profile = last 1440 closed M1 bars.
    Typical price (H+L+C)/3 per bar, weighted by tick_volume, binned in $0.20 bins.
    POC = bin with max volume. Value Area = 70% of volume expanded around POC
    (single-bin expansion, larger neighbour first) → VAH (top edge) / VAL (bottom edge).
  • BUY  when the just-closed bar FRESH-crosses ABOVE VAH (prev close ≤ VAH, close > VAH).
    SELL when the just-closed bar FRESH-crosses BELOW VAL (prev close ≥ VAL, close < VAL).
  • SL = 1.5×ATR(14). TP = 1.5×R where R = SL distance (R:R 1.5). Fixed 0.1 lot. Cooldown 0.
  • 1 position per magic (anti-stack). SL/TP sent to broker.

Execution on BAR CLOSE (bars[:-1], drop the forming bar) — no logic-drift vs backtest.

SAFETY:
  • Default DRY-RUN (paper). Real orders ONLY with --live.
  • --live refuses to run on a REAL-money account unless --allow-real is also given.

Usage:
  python3 mp_brk_m1.py --once            # 1 check (paper)
  python3 mp_brk_m1.py                   # loop (paper)
  python3 mp_brk_m1.py --live            # LIVE (refuses REAL account)
  python3 mp_brk_m1.py --api http://127.0.0.1:8000 --live
"""
from __future__ import annotations

import argparse
import datetime as dt
import time

import requests

from mt5_scalper import MT5Api, atr

try:
    import journal            # RAG trade-journal (Postgres). Optional: trading never blocks on it.
    _HAS_JOURNAL = True
except Exception:
    _HAS_JOURNAL = False

MAGIC = 770015          # Market-Profile breakout M1 (per homelab live config)
STRAT = "MPBRKM1"       # RAG strategy tag


def _record_entry(api, sym, side, order_ticket, entry_price, lot, sl, tp):
    """Record entry + 33-indicator snapshot into the RAG journal (best-effort)."""
    if not _HAS_JOURNAL or not order_ticket:
        return
    try:
        snap = api._get(f"/api/symbols/{sym}/indicators", timeframe="M1", count=300)
        snap = snap.get("latest") or snap
        journal.log_live_entry(
            ticket=int(order_ticket), strategy=STRAT, symbol=sym, timeframe="M1",
            side=side, entry_time=dt.datetime.now(), entry_price=entry_price,
            lot=lot, sl=sl, tp=tp, magic=MAGIC, features=snap)
        log(f"   ✓ RAG: entry features recorded (ticket {order_ticket})")
    except Exception as e:
        log(f"   (RAG record skipped: {type(e).__name__}: {e})")


def log(msg: str) -> None:
    print(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def volume_profile(bars: list[dict], bin_size: float, va_frac: float):
    """Return (poc_price, vah, val) from typical-price volume profile.

    bin index k covers price [k*bin_size, (k+1)*bin_size).
    """
    vol: dict[int, float] = {}
    for b in bars:
        tp = (b["high"] + b["low"] + b["close"]) / 3.0
        w = b.get("tick_volume") or 0
        if w <= 0:
            continue
        k = int(tp // bin_size)
        vol[k] = vol.get(k, 0.0) + w
    if not vol:
        return None
    lo_k, hi_k = min(vol), max(vol)
    # dense array over the observed range
    keys = list(range(lo_k, hi_k + 1))
    arr = [vol.get(k, 0.0) for k in keys]
    n = len(arr)
    total = sum(arr)
    if total <= 0:
        return None
    poc = max(range(n), key=lambda i: arr[i])
    target = va_frac * total
    lo = hi = poc
    va = arr[poc]
    while va < target and (lo > 0 or hi < n - 1):
        up = arr[hi + 1] if hi < n - 1 else -1.0
        dn = arr[lo - 1] if lo > 0 else -1.0
        if up >= dn:
            hi += 1
            va += arr[hi]
        else:
            lo -= 1
            va += arr[lo]
    poc_price = (keys[poc] + 0.5) * bin_size
    vah = (keys[hi] + 1) * bin_size      # top edge of highest VA bin
    val = keys[lo] * bin_size            # bottom edge of lowest VA bin
    return poc_price, vah, val


def step(api: MT5Api, cfg: dict, sinfo: dict, state: dict) -> None:
    sym = cfg["symbol"]; digits = sinfo["digits"]
    bars = api.bars(sym, "M1", cfg["window"] + 5)
    closed = bars[:-1]                                   # execute on bar close
    if len(closed) < cfg["window"] // 2 or len(closed) < cfg["atr_period"] + 3:
        log("✗ bar tidak cukup"); return

    last_t = closed[-1]["time"]
    new_bar = state.get("last_bar") != last_t
    state["last_bar"] = last_t

    window = closed[-cfg["window"]:]
    vp = volume_profile(window, cfg["bin_size"], cfg["va_frac"])
    if vp is None:
        log("✗ volume profile kosong"); return
    poc, vah, val = vp
    a = atr(closed, cfg["atr_period"])

    prev_c = closed[-2]["close"]
    cur_c = closed[-1]["close"]

    side = None
    if prev_c <= vah and cur_c > vah:
        side = "buy"                                     # fresh breakout above value area
    elif prev_c >= val and cur_c < val:
        side = "sell"

    if new_bar:
        bar_iso = dt.datetime.fromtimestamp(last_t).strftime("%m-%d %H:%M")
        log(f"bar {bar_iso} close={cur_c:.{digits}f} | POC={poc:.2f} VAH={vah:.2f} "
            f"VAL={val:.2f} ATR={a:.2f} | signal={side or 'none'}")
    if not new_bar:
        return
    if not side or a <= 0:
        return

    poss = [p for p in api.positions(sym) if p.get("magic") == MAGIC]
    if poss:
        log(f"✗ SKIP: sudah ada {len(poss)} posisi mp-brk (magic {MAGIC})"); return

    tick = api.tick(sym)
    entry = tick["ask"] if side == "buy" else tick["bid"]
    sl_d = cfg["sl_atr"] * a                             # SL distance = 1.5×ATR
    tp_d = cfg["tp_r"] * sl_d                            # TP = 1.5×R
    sl = round(entry - sl_d if side == "buy" else entry + sl_d, digits)
    tp = round(entry + tp_d if side == "buy" else entry - tp_d, digits)
    lot = cfg["lot"]

    log(f"➤ {side.upper()} {sym} @ {entry:.{digits}f} | SL {sl} TP {tp} "
        f"R:R={tp_d/sl_d:.2f} | lot={lot} (fixed)")

    if not cfg["live"]:
        try:
            chk = api.order_check(sym, side, lot, sl, tp, cfg["deviation"], "mp_brk_m1")
            res = chk.get("result", {})
            log(f"   [PAPER] order_check retcode={res.get('retcode')} ({res.get('comment')})")
        except Exception as e:
            log(f"   [PAPER] order_check error: {e}")
        log("   [PAPER] tidak dikirim (pakai --live untuk eksekusi nyata).")
        return

    try:
        out = api._post("/api/orders/send", dict(
            symbol=sym, side=side, volume=lot, sl=sl, tp=tp,
            deviation=cfg["deviation"], magic=MAGIC, comment="mp_brk_m1"))
        res = out.get("result", {})
        log(f"   ✓ LIVE retcode={res.get('retcode')} deal={res.get('deal')} "
            f"order={res.get('order')} price={res.get('price')} vol={res.get('volume')}")
        _record_entry(api, sym, side, res.get("order"),
                      res.get("price") or entry, lot, sl, tp)
    except Exception as e:
        log(f"   ✗ LIVE order GAGAL: {e}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Live runner Market-Profile breakout M1")
    ap.add_argument("--symbol", default="XAUUSD")
    ap.add_argument("--window", type=int, default=1440, help="M1 bars for volume profile (24h)")
    ap.add_argument("--bin-size", type=float, default=0.20)
    ap.add_argument("--va-frac", type=float, default=0.70)
    ap.add_argument("--atr-period", type=int, default=14)
    ap.add_argument("--sl-atr", type=float, default=1.5)
    ap.add_argument("--tp-r", type=float, default=1.5)
    ap.add_argument("--lot", type=float, default=0.1)
    ap.add_argument("--deviation", type=int, default=30)
    ap.add_argument("--poll", type=int, default=15)
    ap.add_argument("--live", action="store_true", help="kirim order nyata")
    ap.add_argument("--allow-real", action="store_true", help="izinkan jalan di akun REAL")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--api", default="http://127.0.0.1:8000")
    args = ap.parse_args()

    api = MT5Api(args.api, timeout=30)
    sinfo = api.symbol_info(args.symbol)
    acc = api.account()
    tmode = acc.get("trade_mode")
    tmode_str = {0: "DEMO", 1: "CONTEST", 2: "REAL"}.get(tmode, f"?({tmode})")

    cfg = dict(symbol=args.symbol, window=args.window, bin_size=args.bin_size,
               va_frac=args.va_frac, atr_period=args.atr_period, sl_atr=args.sl_atr,
               tp_r=args.tp_r, lot=args.lot, deviation=args.deviation, live=args.live)

    log(f"Akun {acc.get('login')} | {acc.get('server')} | {acc.get('company')} | "
        f"trade_mode={tmode_str} | bal=${acc['balance']:.2f} eq=${acc['equity']:.2f}")
    log(f"MP breakout | {args.symbol} M1 | window {args.window} bin ${args.bin_size} "
        f"VA {args.va_frac:.0%} | SL {args.sl_atr}×ATR TP {args.tp_r}×R | lot {args.lot} | "
        f"magic {MAGIC} | {'🔴 LIVE' if args.live else '🟢 PAPER'}")

    if args.live and tmode_str == "REAL" and not args.allow_real:
        log("⛔ BERHENTI: akun REAL-money. Tambahkan --allow-real kalau memang disengaja.")
        return

    state: dict = {}
    if args.once:
        step(api, cfg, sinfo, state); return
    log(f"Loop tiap {args.poll}s — Ctrl+C berhenti.")
    try:
        while True:
            try:
                step(api, cfg, sinfo, state)
            except requests.RequestException as e:
                log(f"(network: {type(e).__name__})")
            except Exception as e:
                log(f"(error: {type(e).__name__}: {e})")
            time.sleep(args.poll)
    except KeyboardInterrupt:
        log("Berhenti.")


if __name__ == "__main__":
    main()
