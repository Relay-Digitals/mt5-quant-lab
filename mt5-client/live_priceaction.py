"""
live_priceaction.py — LIVE runner untuk strategi pure price-action (engulf+trend H4).

Strategi identik dengan backtest (bt_priceaction.make_pa) → tidak ada logic-drift
antara hasil walk-forward dan live. Default operating-point hasil riset:
  XAUUSD H4, engulfing + swing-trend filter, SL 2.0×ATR / TP 2.0×ATR, risk 0.5%.
  (PF 1.33, DD 3.8%, 6/8 fold positif — lihat memory priceaction-engulf-h4.)

Eksekusi pada BAR CLOSE (pakai bars[:-1], buang bar berjalan) — sama dgn backtest.
1 posisi per magic (anti-tumpuk). SL/TP dikirim ke broker → proteksi sisi broker.

SAFETY:
  • Default DRY-RUN (paper). Order nyata HANYA dengan --live.
  • --live menampilkan trade_mode akun (DEMO/REAL) dan MENOLAK jalan di akun REAL
    kecuali ditambah --allow-real (gerbang ganda biar tak sengaja di akun real).

Usage:
  python3 live_priceaction.py --once                         # cek 1x (paper)
  python3 live_priceaction.py                                # loop (paper)
  python3 live_priceaction.py --live                         # LIVE (tolak jika akun REAL)
  python3 live_priceaction.py --live --allow-real            # LIVE termasuk akun REAL
"""
from __future__ import annotations

import argparse
import datetime as dt
import time

import requests

from mt5_scalper import MT5Api, calc_lot
from backtest_lab import atr_series
from bt_priceaction import make_pa

MAGIC = 770020          # PA engulf+trend (beda dari 770001-5 scalper, 770012 SRCONFDIV)


def log(msg: str) -> None:
    print(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def step(api, strat, cfg, sinfo, state):
    sym = cfg["symbol"]; tf = cfg["timeframe"]
    digits = sinfo["digits"]; point = sinfo["point"]
    bars = api.bars(sym, tf, cfg["lookback"])
    closed = bars[:-1]                       # buang bar berjalan → eksekusi di bar close
    if len(closed) < strat.warmup + cfg["atr_period"] + 2:
        log("✗ bar tidak cukup untuk warmup"); return
    i = len(closed) - 1
    last_t = closed[i]["time"]

    pre = strat.prepare(closed)
    atr_arr = atr_series(closed, cfg["atr_period"])
    a = atr_arr[i]

    new_bar = state.get("last_bar") != last_t
    state["last_bar"] = last_t

    side = strat.signal(i, closed, pre)
    if new_bar:
        bar_iso = dt.datetime.fromtimestamp(last_t).strftime("%m-%d %H:%M")
        a_str = f"{a:.{digits}f}" if a == a else "nan"
        log(f"bar {bar_iso} close={closed[i]['close']:.{digits}f} ATR={a_str} "
            f"signal={side or 'none'}")
    if not new_bar:
        return                               # sudah diproses bar ini
    if not side or not (a == a) or a <= 0:
        return

    tick = api.tick(sym)
    spread_price = tick["ask"] - tick["bid"]
    if spread_price / a * 100 > cfg["max_spread_pct"]:
        log(f"✗ SKIP: spread {spread_price/a*100:.1f}% > {cfg['max_spread_pct']}% ATR"); return

    poss = [p for p in api.positions(sym) if p.get("magic") == MAGIC]
    if poss:
        log(f"✗ SKIP: sudah ada {len(poss)} posisi PA (magic {MAGIC})"); return

    entry = tick["ask"] if side == "buy" else tick["bid"]
    sl_d = strat.sl_atr * a; tp_d = strat.tp_atr * a
    sl = round(entry - sl_d if side == "buy" else entry + sl_d, digits)
    tp = round(entry + tp_d if side == "buy" else entry - tp_d, digits)
    acc = api.account()
    lot, est_loss = calc_lot(acc["balance"] * cfg["risk"] / 100, sl_d, sinfo)

    log(f"➤ {side.upper()} {sym} @ {entry:.{digits}f} | SL {sl} TP {tp} "
        f"R:R={tp_d/sl_d:.2f} | lot={lot} est.risk=${est_loss:.2f} "
        f"({est_loss/acc['balance']*100:.1f}%) bal=${acc['balance']:.2f}")

    if est_loss > acc["balance"] * cfg["max_risk"] / 100:
        log(f"✗ SKIP: risk ${est_loss:.2f} > cap {cfg['max_risk']}%"); return

    if not cfg["live"]:
        try:
            chk = api.order_check(sym, side, lot, sl, tp, cfg["deviation"], "PA_engulf_trend")
            res = chk.get("result", {})
            log(f"   [PAPER] order_check retcode={res.get('retcode')} ({res.get('comment')})")
        except Exception as e:
            log(f"   [PAPER] order_check error: {e}")
        log("   [PAPER] tidak dikirim (pakai --live untuk eksekusi nyata).")
        return

    try:
        out = api._post("/api/orders/send", dict(
            symbol=sym, side=side, volume=lot, sl=sl, tp=tp,
            deviation=cfg["deviation"], magic=MAGIC, comment="PA_engulf_trend"))
        res = out.get("result", {})
        log(f"   ✓ LIVE retcode={res.get('retcode')} deal={res.get('deal')} "
            f"price={res.get('price')} vol={res.get('volume')}")
    except Exception as e:
        log(f"   ✗ LIVE order GAGAL: {e}")


def main():
    ap = argparse.ArgumentParser(description="Live runner PA engulf+trend")
    ap.add_argument("--symbol", default="XAUUSD")
    ap.add_argument("--tf", default="H4")
    ap.add_argument("--risk", type=float, default=0.5)
    ap.add_argument("--max-risk", type=float, default=6.0)
    ap.add_argument("--max-spread-pct", type=float, default=8.0)
    ap.add_argument("--atr-period", type=int, default=14)
    ap.add_argument("--sl", type=float, default=2.0)
    ap.add_argument("--tp", type=float, default=2.0)
    ap.add_argument("--left", type=int, default=2)
    ap.add_argument("--right", type=int, default=2)
    ap.add_argument("--trend-lb", type=int, default=2)
    ap.add_argument("--lookback", type=int, default=400)
    ap.add_argument("--deviation", type=int, default=30)
    ap.add_argument("--poll", type=int, default=30)
    ap.add_argument("--live", action="store_true", help="kirim order nyata")
    ap.add_argument("--allow-real", action="store_true", help="izinkan jalan di akun REAL")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--api", default="http://192.168.0.111:8000")
    args = ap.parse_args()

    api = MT5Api(args.api, timeout=30)
    sinfo = api.symbol_info(args.symbol)
    acc = api.account()
    strat = make_pa("engulf", "trend", sl_atr=args.sl, tp_atr=args.tp,
                    left=args.left, right=args.right, trend_lookback=args.trend_lb)

    # trade_mode: 0=demo, 1=contest, 2=real (enum MT5). Tampilkan & gerbang akun real.
    tmode = acc.get("trade_mode")
    tmode_str = {0: "DEMO", 1: "CONTEST", 2: "REAL"}.get(tmode, f"?({tmode})")
    cfg = dict(symbol=args.symbol, timeframe=args.tf, risk=args.risk, max_risk=args.max_risk,
               max_spread_pct=args.max_spread_pct, atr_period=args.atr_period,
               lookback=args.lookback, deviation=args.deviation, live=args.live)

    log(f"Akun {acc.get('login')} | {acc.get('server')} | {acc.get('company')} | "
        f"trade_mode={tmode_str} | bal=${acc['balance']:.2f} eq=${acc['equity']:.2f}")
    log(f"PA engulf+trend | {args.symbol} {args.tf} | SL {args.sl}×ATR TP {args.tp}×ATR | "
        f"risk {args.risk}% cap {args.max_risk}% | magic {MAGIC} | "
        f"{'🔴 LIVE' if args.live else '🟢 PAPER'}")

    if args.live and tmode_str == "REAL" and not args.allow_real:
        log("⛔ BERHENTI: akun REAL-money. Tambahkan --allow-real kalau memang disengaja.")
        return

    state = {}
    if args.once:
        step(api, strat, cfg, sinfo, state); return
    log(f"Loop tiap {args.poll}s — Ctrl+C berhenti.")
    try:
        while True:
            try:
                step(api, strat, cfg, sinfo, state)
            except requests.RequestException as e:
                log(f"(network: {type(e).__name__})")
            except Exception as e:
                log(f"(error: {type(e).__name__}: {e})")
            time.sleep(args.poll)
    except KeyboardInterrupt:
        log("Berhenti.")


if __name__ == "__main__":
    main()
