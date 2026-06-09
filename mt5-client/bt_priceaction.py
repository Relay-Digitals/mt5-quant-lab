"""
bt_priceaction.py — Pure price-action + candlestick backtest (NO indicators).

Metodologi mengikuti riset MACD sebelumnya (lihat memory macd-divergence-h4 /
macd-rsi-m2-research): test pattern POLOS dulu, baru tambah konteks (trend + S/R),
sweep TF, lalu walk-forward. Hindari overfit — hanya keep filter yang lolos OOS.

"Pure price action" = murni OHLC. Tidak ada MACD/RSI/ADX/MA.
  - Candle patterns : engulfing, pin bar (hammer/shooting star), inside-bar break.
  - Struktur harga  : swing high/low via fractal (NO-LOOKAHEAD: swing baru "ada"
                      setelah `right` bar konfirmasi), trend dari urutan swing,
                      support/resistance dari swing terdekat.

SL/TP tetap ATR-based (ATR cuma untuk sizing & jarak stop, bukan sinyal).
Engine eksekusi = backtest_lab.run_backtest (entry di CLOSE bar sinyal, spread
per-bar dihitung, slippage & swap diabaikan).

Usage:
  python3 bt_priceaction.py --tf H4 --bt-days 1500 --pattern engulf
  python3 bt_priceaction.py --tf H4 --bt-days 1500 --all          # semua pattern x konteks
  python3 bt_priceaction.py --tf H4 --bt-days 2200 --wf 8 --pattern pin --ctx trend_sr
"""
from __future__ import annotations

import argparse
import datetime as dt
import math

from mt5_scalper import MT5Api
from backtest_lab import Strategy, run_backtest, fetch_bars, atr_series

NAN = float("nan")


# ───────────────────────── candle primitives (pure OHLC) ─────────────────────

def _o(b): return b["open"]
def _h(b): return b["high"]
def _l(b): return b["low"]
def _c(b): return b["close"]

def body(b):       return abs(_c(b) - _o(b))
def rng(b):        return _h(b) - _l(b)
def upper_wick(b): return _h(b) - max(_o(b), _c(b))
def lower_wick(b): return min(_o(b), _c(b)) - _l(b)
def is_bull(b):    return _c(b) > _o(b)
def is_bear(b):    return _c(b) < _o(b)


# ───────────────────────── candle pattern detectors ─────────────────────────
# Semua dievaluasi pada bar i yang SUDAH close → entry di close bar i. No lookahead.

def bull_engulf(bars, i):
    if i < 1: return False
    a, b = bars[i - 1], bars[i]
    return (is_bear(a) and is_bull(b)
            and _c(b) >= _o(a) and _o(b) <= _c(a)
            and body(b) > body(a))

def bear_engulf(bars, i):
    if i < 1: return False
    a, b = bars[i - 1], bars[i]
    return (is_bull(a) and is_bear(b)
            and _o(b) >= _c(a) and _c(b) <= _o(a)
            and body(b) > body(a))

def hammer(bars, i):
    """Pin bar bullish: ekor bawah panjang, badan kecil di atas, wick atas pendek."""
    b = bars[i]; r = rng(b)
    if r <= 0: return False
    return (lower_wick(b) >= 2 * body(b)
            and upper_wick(b) <= body(b)
            and lower_wick(b) / r >= 0.5)

def shooting_star(bars, i):
    """Pin bar bearish."""
    b = bars[i]; r = rng(b)
    if r <= 0: return False
    return (upper_wick(b) >= 2 * body(b)
            and lower_wick(b) <= body(b)
            and upper_wick(b) / r >= 0.5)

def inside_break_up(bars, i):
    """Bar i-1 inside bar (di dalam mother i-2), bar i close tembus high mother → buy."""
    if i < 2: return False
    m, inb, cur = bars[i - 2], bars[i - 1], bars[i]
    inside = _h(inb) < _h(m) and _l(inb) > _l(m)
    return inside and _c(cur) > _h(m)

def inside_break_dn(bars, i):
    if i < 2: return False
    m, inb, cur = bars[i - 2], bars[i - 1], bars[i]
    inside = _h(inb) < _h(m) and _l(inb) > _l(m)
    return inside and _c(cur) < _l(m)


PATTERNS = {
    # name: (buy_fn, sell_fn, warmup)
    "engulf": (bull_engulf, bear_engulf, 2),
    "pin":    (hammer, shooting_star, 2),
    "inside": (inside_break_up, inside_break_dn, 3),
}


# ───────────────────────── struktur harga (no-lookahead) ─────────────────────

def swings(bars, left=2, right=2):
    """Fractal swing high/low. Mengembalikan dua array sejajar `bars`:
       sh[i], sl[i] = harga swing high/low yang BARU TERKONFIRMASI pada bar i
       (yaitu swing di bar i-right). NAN kalau bukan. Ini bikin info swing baru
       'tersedia' tepat saat right bar ke kanan sudah close → tanpa lookahead."""
    n = len(bars)
    sh = [NAN] * n; sl = [NAN] * n
    for j in range(left, n - right):
        hj = _h(bars[j]); lj = _l(bars[j])
        is_h = all(hj >= _h(bars[j - k]) for k in range(1, left + 1)) and \
               all(hj >  _h(bars[j + k]) for k in range(1, right + 1))
        is_l = all(lj <= _l(bars[j - k]) for k in range(1, left + 1)) and \
               all(lj <  _l(bars[j + k]) for k in range(1, right + 1))
        conf = j + right                      # bar saat swing j terkonfirmasi
        if conf < n:
            if is_h: sh[conf] = hj
            if is_l: sl[conf] = lj
    return sh, sl


def _last_levels(sh, sl, i):
    """Swing high/low terakhir yang terkonfirmasi SAMPAI bar i (inklusif)."""
    last_h = [x for x in sh[:i + 1] if x == x]
    last_l = [x for x in sl[:i + 1] if x == x]
    return last_h, last_l


# ───────────────────────────── factory strategi ─────────────────────────────

def make_pa(pattern: str, ctx: str = "none", sl_atr=1.5, tp_atr=2.0,
            left=2, right=2, sr_atr=1.0, trend_lookback=2, min_body_atr=0.0) -> Strategy:
    """Strategi pure price-action.
       pattern : 'engulf' | 'pin' | 'inside'
       ctx     : 'none' | 'trend' | 'sr' | 'trend_sr'
                  trend = pattern harus searah trend swing
                  sr    = pattern harus dekat support (buy) / resistance (sell) <= sr_atr*ATR
       min_body_atr : kalau >0, badan candle sinyal harus >= X*ATR (saring engulf lemah).
       Konfirmasi pakai HANYA harga (swing) + ATR untuk jarak (bukan sinyal)."""
    buy_fn, sell_fn, warm = PATTERNS[pattern]
    use_trend = ctx in ("trend", "trend_sr")
    use_sr    = ctx in ("sr", "trend_sr")
    use_body  = min_body_atr > 0

    def prepare(bars):
        d = {}
        if use_trend or use_sr:
            sh, sl = swings(bars, left, right)
            d["sh"], d["sl"] = sh, sl
        if use_sr or use_body:
            d["atr"] = atr_series(bars, 14)
        return d

    def _uptrend(sh, sl, i):
        _, lows = _last_levels(sh, sl, i)
        highs, _ = _last_levels(sh, sl, i)
        if len(lows) < trend_lookback or len(highs) < trend_lookback:
            return None
        rising_lows = all(lows[-k] > lows[-k - 1] for k in range(1, trend_lookback))
        rising_highs = all(highs[-k] > highs[-k - 1] for k in range(1, trend_lookback))
        if rising_lows and rising_highs: return "up"
        falling_lows = all(lows[-k] < lows[-k - 1] for k in range(1, trend_lookback))
        falling_highs = all(highs[-k] < highs[-k - 1] for k in range(1, trend_lookback))
        if falling_lows and falling_highs: return "down"
        return "flat"

    def signal(i, bars, pre):
        side = None
        if buy_fn(bars, i):  side = "buy"
        elif sell_fn(bars, i): side = "sell"
        if not side:
            return None
        c = _c(bars[i])
        if use_body:
            a = pre["atr"][i]
            if math.isnan(a) or a <= 0 or body(bars[i]) < min_body_atr * a:
                return None
        if use_trend:
            tr = _uptrend(pre["sh"], pre["sl"], i)
            if tr is None or tr == "flat":
                return None
            if side == "buy" and tr != "up":   return None
            if side == "sell" and tr != "down": return None
        if use_sr:
            a = pre["atr"][i]
            if math.isnan(a) or a <= 0:
                return None
            highs, lows = _last_levels(pre["sh"], pre["sl"], i)
            if side == "buy":
                below = [x for x in lows if x <= c]
                if not below or (c - max(below)) > sr_atr * a:
                    return None
            else:
                above = [x for x in highs if x >= c]
                if not above or (min(above) - c) > sr_atr * a:
                    return None
        return side

    desc = f"PA {pattern}+{ctx} SL{sl_atr}/TP{tp_atr}"
    return Strategy(f"PA_{pattern}_{ctx}", desc,
                    max(warm, left + right + 1, 16), sl_atr, tp_atr, prepare, signal)


# ───────────────────────────── runner / sweep ───────────────────────────────

def _fmt(r):
    pf = "inf" if r.pf == float("inf") else f"{r.pf:.2f}"
    return (f"{r.name:18} tr{r.trades:4} WR{r.win_rate:5.1f} "
            f"ret{r.ret_pct:+8.2f}% PF{pf:>5} DD{r.max_dd_pct:5.1f}% "
            f"aL{r.avg_lot:.3f}")


def run_one(bars, sinfo, pattern, ctx, args):
    s = make_pa(pattern, ctx, sl_atr=args.sl, tp_atr=args.tp,
                left=args.left, right=args.right, sr_atr=args.sr_atr,
                trend_lookback=args.trend_lb, min_body_atr=args.min_body_atr)
    return run_backtest(bars, s, sinfo, balance=args.balance,
                        risk_pct=args.risk, max_risk_pct=args.max_risk,
                        max_spread_pct=args.max_spread_pct)


def walk_forward(bars, sinfo, pattern, ctx, args, folds=8):
    n = len(bars); fold = n // folds
    print(f"\nWALK-FORWARD {pattern}+{ctx} | {folds} folds | {n} bars")
    print("-" * 60)
    pos = 0
    for k in range(folds):
        seg = bars[k * fold:(k + 1) * fold] if k < folds - 1 else bars[k * fold:]
        if len(seg) < 50:
            continue
        r = run_one(seg, sinfo, pattern, ctx, args)
        t0 = dt.datetime.fromtimestamp(seg[0]["time"]).date()
        t1 = dt.datetime.fromtimestamp(seg[-1]["time"]).date()
        flag = "✓" if r.ret_pct > 0 else "✗"
        if r.ret_pct > 0: pos += 1
        pf = "inf" if r.pf == float("inf") else f"{r.pf:.2f}"
        print(f"  {flag} {t0}→{t1} tr{r.trades:3} WR{r.win_rate:5.1f} "
              f"ret{r.ret_pct:+7.2f}% PF{pf:>5} DD{r.max_dd_pct:4.1f}%")
    print(f"  → {pos}/{folds} folds positif")


def main():
    p = argparse.ArgumentParser(description="Pure price-action + candle backtest")
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--tf", default="H4")
    p.add_argument("--bt-days", type=int, default=1500)
    p.add_argument("--bt-bars", type=int, default=9000)
    p.add_argument("--balance", type=float, default=9299.50)   # balance demo nyata
    p.add_argument("--risk", type=float, default=0.5)
    p.add_argument("--max-risk", type=float, default=6.0)
    p.add_argument("--max-spread-pct", type=float, default=8.0)
    p.add_argument("--sl", type=float, default=1.5)
    p.add_argument("--tp", type=float, default=2.0)
    p.add_argument("--left", type=int, default=2)
    p.add_argument("--right", type=int, default=2)
    p.add_argument("--sr-atr", type=float, default=1.0)
    p.add_argument("--trend-lb", type=int, default=2)
    p.add_argument("--min-body-atr", type=float, default=0.0, help="saring: badan candle sinyal >= X*ATR")
    p.add_argument("--pattern", default="engulf", help="engulf|pin|inside")
    p.add_argument("--ctx", default="none", help="none|trend|sr|trend_sr")
    p.add_argument("--all", action="store_true", help="sweep semua pattern x konteks")
    p.add_argument("--wf", type=int, default=0, help="jumlah fold walk-forward")
    p.add_argument("--api", default="http://192.168.0.111:8000")
    args = p.parse_args()

    api = MT5Api(args.api, timeout=180)
    sinfo = api.symbol_info(args.symbol)
    bars, period = fetch_bars(api, args.symbol, args.tf, args.bt_days, args.bt_bars)
    sp = (f"{dt.datetime.fromtimestamp(bars[0]['time']).date()} → "
          f"{dt.datetime.fromtimestamp(bars[-1]['time']).date()}")
    print(f"\n{'='*72}\nPURE PRICE-ACTION | {args.symbol} {args.tf} | {len(bars)} bar | {sp}")
    print(f"bal ${args.balance:.0f} risk {args.risk}% | SL {args.sl}xATR TP {args.tp}xATR")
    print('='*72)

    if args.wf:
        walk_forward(bars, sinfo, args.pattern, args.ctx, args, folds=args.wf)
        return

    if args.all:
        print(f"\n{'STRATEGI':18} {'trades':>5} {'WR%':>6} {'return':>9} {'PF':>5} {'DD%':>6}")
        print("-" * 60)
        for pat in ("engulf", "pin", "inside"):
            for ctx in ("none", "trend", "sr", "trend_sr"):
                r = run_one(bars, sinfo, pat, ctx, args)
                print(_fmt(r))
            print()
    else:
        r = run_one(bars, sinfo, args.pattern, args.ctx, args)
        print("\n" + _fmt(r))
        print(f"  W{r.wins}/L{r.losses} avgW ${r.avg_win:+.2f} avgL ${r.avg_loss:+.2f} "
              f"skip atr{r.skip_atr}/spr{r.skip_spread}/cap{r.skip_cap}")
    print()


if __name__ == "__main__":
    main()
