"""
live_trader.py — Forward test LIVE memakai strategi yang SAMA dengan backtest_lab.

Tujuan: tidak ada logic-drift antara backtest & live. Strategi (TREND/MAOSC/MEANREV)
diambil dari backtest_lab, jadi sinyal live identik dengan yang divalidasi walk-forward.

  • Filter & sizing sama dengan engine backtest (risk%, hard-cap, spread≤X%ATR, ATR min)
  • SL/TP = ATR-based sesuai strategi
  • 1 posisi per (magic) — anti tumpuk
  • Default PAPER (dry-run). Order nyata hanya dengan --live.

Usage:
  python3 live_trader.py --symbol USDJPY --strat MAOSC --tf H1            # paper
  python3 live_trader.py --symbol USDJPY --strat MAOSC --tf H1 --live     # LIVE
  python3 live_trader.py --symbol USDJPY --strat MAOSC --tf H1 --once     # 1x cek
"""
from __future__ import annotations

import argparse
import datetime as dt
import time

import requests

from mt5_scalper import MT5Api, calc_lot
from backtest_lab import make_trend, make_maosc, make_meanrev, make_maosc_quality, atr_series

def _maoscq():
    return make_maosc_quality(use_macd=False, adx_min=0, skip_stoch_low=True, skip_london=False)

MAKERS = {"TREND": make_trend, "MAOSC": make_maosc, "MEANREV": make_meanrev, "MAOSCQ": _maoscq}
# magic per strategi (beda dari EMA scalper 770001)
MAGICS = {"MAOSC": 770002, "TREND": 770003, "MEANREV": 770004, "MAOSCQ": 770005}


def log(msg: str) -> None:
    print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


def step(api, strat, magic, cfg, sinfo, state):
    sym = cfg["symbol"]; tf = cfg["timeframe"]
    digits = sinfo["digits"]; point = sinfo["point"]
    bars = api.bars(sym, tf, 300)
    closed = bars[:-1]                      # buang bar berjalan
    i = len(closed) - 1
    last_t = closed[i]["time"]

    pre = strat.prepare(closed)
    atr_arr = atr_series(closed, cfg["atr_period"])
    a = atr_arr[i]

    if state.get("last_bar") == last_t:
        return
    state["last_bar"] = last_t

    side = strat.signal(i, closed, pre)
    tick = api.tick(sym)
    spread_price = tick["ask"] - tick["bid"]
    bar_iso = dt.datetime.fromtimestamp(last_t).strftime("%m-%d %H:%M")
    a_str = f"{a:.{digits}f}" if a == a else "nan"
    log(f"bar {bar_iso} | close={closed[i]['close']:.{digits}f} ATR={a_str} "
        f"spread={spread_price:.{digits}f} | signal={side or 'none'}")

    if not side or not (a == a) or a <= 0:
        return

    # ── filter (sama dgn backtest) ──
    if a < cfg["min_atr"]:
        log(f"✗ SKIP: ATR {a:.{digits}f} < min {cfg['min_atr']}"); return
    if spread_price / a * 100 > cfg["max_spread_pct"]:
        log(f"✗ SKIP: spread {spread_price/a*100:.1f}% > {cfg['max_spread_pct']}% ATR"); return

    poss = [p for p in api.positions(sym) if p.get("magic") == magic]
    if poss:
        log(f"✗ SKIP: sudah ada {len(poss)} posisi {strat.name}"); return

    # ── SL/TP & sizing ──
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
            chk = api.order_check(sym, side, lot, sl, tp, cfg["deviation"], strat.name)
            res = chk.get("result", {})
            log(f"   [PAPER] order_check retcode={res.get('retcode')} ({res.get('comment')})")
        except Exception as e:
            log(f"   [PAPER] order_check error: {e}")
        log("   [PAPER] tidak dikirim (pakai --live untuk eksekusi nyata).")
        return

    try:
        out = api._post("/api/orders/send", dict(
            symbol=sym, side=side, volume=lot, sl=sl, tp=tp,
            deviation=cfg["deviation"], magic=magic, comment=strat.name))
        res = out.get("result", {})
        log(f"   ✓ LIVE retcode={res.get('retcode')} deal={res.get('deal')} "
            f"price={res.get('price')} vol={res.get('volume')}")
        # rekam snapshot 31 indikator saat entry → journal (utk analisa profit/loss nanti)
        tk = res.get("order") or res.get("deal")
        if tk:
            try:
                import journal
                snap = api._get(f"/api/symbols/{sym}/indicators",
                                timeframe=cfg["timeframe"], count=300).get("latest", {})
                journal.log_live_entry(int(tk), strategy=strat.name, symbol=sym,
                    timeframe=cfg["timeframe"], side=side, entry_time=dt.datetime.now().isoformat(),
                    entry_price=res.get("price"), lot=res.get("volume"), sl=sl, tp=tp,
                    magic=magic, features=snap)
                log(f"   📝 fitur entry direkam (ticket {tk}, {len(snap)} indikator)")
            except Exception as e:
                log(f"   (rekam fitur gagal: {type(e).__name__}: {e})")
    except Exception as e:
        log(f"   ✗ LIVE order GAGAL: {e}")


def main():
    ap = argparse.ArgumentParser(description="Forward test live (strategi = backtest_lab)")
    ap.add_argument("--symbol", default="USDJPY")
    ap.add_argument("--strat", default="MAOSC", choices=["MAOSC", "TREND", "MEANREV", "MAOSCQ"])
    ap.add_argument("--tf", default="H1")
    ap.add_argument("--risk", type=float, default=1.0)
    ap.add_argument("--max-risk", type=float, default=6.0)
    ap.add_argument("--min-atr", type=float, default=0.0)
    ap.add_argument("--max-spread-pct", type=float, default=12.0)
    ap.add_argument("--atr-period", type=int, default=14)
    ap.add_argument("--deviation", type=int, default=20)
    ap.add_argument("--poll", type=int, default=15)
    ap.add_argument("--allow-hours", default=None, help="TREND: HANYA entry jam UTC ini (mis 7,8,9)")
    ap.add_argument("--block-hours", default=None, help="TREND: larang entry jam UTC ini (mis 14,15,16,17)")
    ap.add_argument("--ext-atr", type=float, default=None, help="MEANREV: skip entry >X ATR dari EMA50")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--api", default="http://192.168.0.116:8000")
    args = ap.parse_args()

    api = MT5Api(args.api, timeout=30)
    sinfo = api.symbol_info(args.symbol)
    acc = api.account()
    _hrs = lambda s: {int(x) for x in s.split(",") if x.strip() != ""} if s else None
    if args.strat == "TREND" and (args.allow_hours or args.block_hours):
        from backtest_lab import make_trend
        strat = make_trend(allow_hours=_hrs(args.allow_hours), block_hours=_hrs(args.block_hours))
    elif args.strat == "MEANREV" and args.ext_atr is not None:
        from backtest_lab import make_meanrev
        strat = make_meanrev(max_ext_atr=args.ext_atr)
    else:
        strat = MAKERS[args.strat]()
    magic = MAGICS[args.strat]
    cfg = dict(symbol=args.symbol, timeframe=args.tf, risk=args.risk, max_risk=args.max_risk,
               min_atr=args.min_atr, max_spread_pct=args.max_spread_pct,
               atr_period=args.atr_period, deviation=args.deviation, live=args.live)

    log(f"Akun {acc['login']} | {acc.get('server')} | bal=${acc['balance']:.2f} eq=${acc['equity']:.2f}")
    log(f"{args.strat} ({strat.desc}) | {args.symbol} {args.tf} | SL {strat.sl_atr}×ATR TP {strat.tp_atr}×ATR")
    log(f"risk {args.risk}% cap {args.max_risk}% | ATR≥{args.min_atr} spread≤{args.max_spread_pct}% | "
        f"magic {magic} | {'🔴 LIVE' if args.live else '🟢 PAPER'}")

    state = {}
    if args.once:
        step(api, strat, magic, cfg, sinfo, state); return
    log(f"Loop tiap {args.poll}s — Ctrl+C berhenti.")
    try:
        while True:
            try:
                step(api, strat, magic, cfg, sinfo, state)
            except requests.RequestException as e:
                log(f"(network: {type(e).__name__})")
            except Exception as e:
                log(f"(error: {type(e).__name__}: {e})")
            time.sleep(args.poll)
    except KeyboardInterrupt:
        log("Berhenti.")


if __name__ == "__main__":
    main()
