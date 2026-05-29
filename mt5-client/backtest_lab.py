"""
backtest_lab.py — Backtest & bandingkan 3 strategi research-backed di MT5 data.

Strategi (dipetakan ke riset yang kita temukan):
  1. TREND   = Trend Following  → Donchian breakout (Turtle) + filter SMA tren
  2. MAOSC   = MA/Oscillator    → SMA-cross + filter RSI (studi "497 rules": SMA+oscillator)
  3. MEANREV = Mean Reversion   → Bollinger Band + RSI (beli oversold / jual overbought)

Engine sama untuk semua: balance-aware, lot sizing risk%, hard-cap, biaya spread per-bar,
ATR-based SL/TP, equity curve + max drawdown. Eksekusi di harga CLOSE (bar-level).

Usage:
  python3 backtest_lab.py --tf M15 --bt-days 60 --balance 1000
  python3 backtest_lab.py --tf M5  --bt-days 7  --balance 100
  python3 backtest_lab.py --tf M15 --bt-days 90 --balance 1000 --only TREND
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
from dataclasses import dataclass
from typing import Callable, Optional

from mt5_scalper import MT5Api, calc_lot

NAN = float("nan")


# ───────────────────────────── indikator (series) ──────────────────────────

def sma(values: list[float], period: int) -> list[float]:
    out = [NAN] * len(values)
    if len(values) < period:
        return out
    s = sum(values[:period])
    out[period - 1] = s / period
    for i in range(period, len(values)):
        s += values[i] - values[i - period]
        out[i] = s / period
    return out


def ema_series(values: list[float], period: int) -> list[float]:
    out = [NAN] * len(values)
    if len(values) < period:
        return out
    k = 2 / (period + 1)
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    prev = seed
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def rsi_series(values: list[float], period: int) -> list[float]:
    out = [NAN] * len(values)
    if len(values) < period + 1:
        return out
    gains, losses = [], []
    for i in range(1, len(values)):
        d = values[i] - values[i - 1]
        gains.append(max(d, 0.0)); losses.append(max(-d, 0.0))
    ag = sum(gains[:period]) / period
    al = sum(losses[:period]) / period
    def rsi_val(ag, al):
        if al == 0: return 100.0
        rs = ag / al
        return 100 - 100 / (1 + rs)
    out[period] = rsi_val(ag, al)
    for i in range(period + 1, len(values)):
        ag = (ag * (period - 1) + gains[i - 1]) / period
        al = (al * (period - 1) + losses[i - 1]) / period
        out[i] = rsi_val(ag, al)
    return out


def atr_series(bars: list[dict], period: int) -> list[float]:
    out = [NAN] * len(bars)
    if len(bars) < period + 1:
        return out
    trs = [NAN]
    for i in range(1, len(bars)):
        h, l, pc = bars[i]["high"], bars[i]["low"], bars[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    a = sum(trs[1:period + 1]) / period
    out[period] = a
    for i in range(period + 1, len(bars)):
        a = (a * (period - 1) + trs[i]) / period
        out[i] = a
    return out


def bollinger(values: list[float], period: int, mult: float):
    mid = sma(values, period)
    upper = [NAN] * len(values); lower = [NAN] * len(values)
    for i in range(period - 1, len(values)):
        window = values[i - period + 1:i + 1]
        m = mid[i]
        var = sum((v - m) ** 2 for v in window) / period
        sd = math.sqrt(var)
        upper[i] = m + mult * sd; lower[i] = m - mult * sd
    return mid, upper, lower


def donchian(bars: list[dict], period: int):
    """Upper/lower = high tertinggi / low terendah dari `period` bar SEBELUM bar i."""
    n = len(bars)
    upper = [NAN] * n; lower = [NAN] * n
    for i in range(period, n):
        window = bars[i - period:i]
        upper[i] = max(b["high"] for b in window)
        lower[i] = min(b["low"] for b in window)
    return upper, lower


def crossed_up(a: list[float], b: list[float], i: int) -> bool:
    if i < 1 or math.isnan(a[i]) or math.isnan(a[i-1]) or math.isnan(b[i]) or math.isnan(b[i-1]):
        return False
    return a[i-1] <= b[i-1] and a[i] > b[i]


def crossed_dn(a: list[float], b: list[float], i: int) -> bool:
    if i < 1 or math.isnan(a[i]) or math.isnan(a[i-1]) or math.isnan(b[i]) or math.isnan(b[i-1]):
        return False
    return a[i-1] >= b[i-1] and a[i] < b[i]


# ───────────────────────────── definisi strategi ───────────────────────────

def _rma(v, p):
    out = [NAN] * len(v)
    if len(v) < p:
        return out
    a = sum(v[:p]) / p; out[p - 1] = a
    for i in range(p, len(v)):
        a = (a * (p - 1) + v[i]) / p; out[i] = a
    return out


def macd_hist(closes):
    ef = ema_series(closes, 12); es = ema_series(closes, 26)
    line = [(a - b) if (a == a and b == b) else NAN for a, b in zip(ef, es)]
    start = next((i for i, x in enumerate(line) if x == x), None)
    sig = [NAN] * len(line)
    if start is not None and len(line) - start >= 9:
        e = ema_series(line[start:], 9)
        for i, x in enumerate(e):
            sig[start + i] = x
    return [(l - s) if (l == l and s == s) else NAN for l, s in zip(line, sig)]


def adx_vals(bars, p=14):
    n = len(bars); pdm = [0.0] * n; mdm = [0.0] * n; tr = [0.0] * n
    for i in range(1, n):
        up = bars[i]["high"] - bars[i - 1]["high"]; dn = bars[i - 1]["low"] - bars[i]["low"]
        pdm[i] = up if (up > dn and up > 0) else 0.0
        mdm[i] = dn if (dn > up and dn > 0) else 0.0
        h, l, pc = bars[i]["high"], bars[i]["low"], bars[i - 1]["close"]
        tr[i] = max(h - l, abs(h - pc), abs(l - pc))
    atr = _rma([0.0] + tr[1:], p); pdms = _rma([0.0] + pdm[1:], p); mdms = _rma([0.0] + mdm[1:], p)
    dx = [NAN] * n
    for i in range(n):
        a = atr[i]
        if a == a and a:
            pdi = 100 * pdms[i] / a; mdi = 100 * mdms[i] / a; ss = pdi + mdi
            dx[i] = 100 * abs(pdi - mdi) / ss if ss else 0.0
    adx = _rma([x if x == x else 0.0 for x in dx], p)
    for i in range(min(2 * p, n)):
        adx[i] = NAN
    return adx


def stoch_k(bars, k=14):
    n = len(bars); K = [NAN] * n
    for i in range(k - 1, n):
        win = bars[i - k + 1:i + 1]
        hh = max(b["high"] for b in win); ll = min(b["low"] for b in win)
        K[i] = 100 * (bars[i]["close"] - ll) / (hh - ll) if hh > ll else 50.0
    return K


@dataclass
class Strategy:
    name: str
    desc: str
    warmup: int
    sl_atr: float
    tp_atr: float
    prepare: Callable          # (bars) -> dict precomputed
    signal: Callable           # (i, bars, pre) -> 'buy'|'sell'|None


def make_trend(don=20, trend_sma=50, sl_atr=1.5, tp_atr=3.0,
               block_hours=None, allow_hours=None) -> Strategy:
    """Trend Following: breakout Donchian + searah SMA tren. Win-rate rendah, winner besar.
    block_hours: set jam UTC yg DILARANG entry. allow_hours: kalau diisi, HANYA jam ini."""
    blk = set(block_hours or [])
    alw = set(allow_hours) if allow_hours is not None else None
    def prepare(bars):
        closes = [b["close"] for b in bars]
        up, lo = donchian(bars, don)
        hour = [dt.datetime.fromtimestamp(b["time"]).hour for b in bars] if (blk or alw is not None) else None
        return {"up": up, "lo": lo, "tsma": sma(closes, trend_sma), "hour": hour}
    def signal(i, bars, pre):
        c = bars[i]["close"]; up = pre["up"][i]; lo = pre["lo"][i]; ts = pre["tsma"][i]
        if math.isnan(up) or math.isnan(ts):
            return None
        if pre["hour"] is not None:
            hr = pre["hour"][i]
            if alw is not None and hr not in alw:
                return None
            if hr in blk:
                return None
        if c > up and c > ts:   return "buy"
        if c < lo and c < ts:   return "sell"
        return None
    tag = ""
    if alw is not None: tag = f" allow{sorted(alw)}"
    elif blk: tag = f" skip{sorted(blk)}"
    return Strategy("TREND", f"Donchian({don})+SMA{trend_sma}{tag}",
                    max(don, trend_sma) + 2, sl_atr, tp_atr, prepare, signal)


def make_maosc(fast=10, slow=30, rsi_p=14, sl_atr=1.2, tp_atr=1.8) -> Strategy:
    """MA/Oscillator: SMA-cross dikonfirmasi RSI (tidak entry di kondisi ekstrem)."""
    def prepare(bars):
        closes = [b["close"] for b in bars]
        return {"f": sma(closes, fast), "s": sma(closes, slow), "rsi": rsi_series(closes, rsi_p)}
    def signal(i, bars, pre):
        f, s, r = pre["f"], pre["s"], pre["rsi"][i]
        if math.isnan(r):
            return None
        if crossed_up(f, s, i) and r < 70:  return "buy"
        if crossed_dn(f, s, i) and r > 30:  return "sell"
        return None
    return Strategy("MAOSC", f"SMA{fast}/{slow} cross + RSI{rsi_p} filter",
                    max(slow, rsi_p) + 2, sl_atr, tp_atr, prepare, signal)


def make_meanrev(bb=20, mult=2.0, rsi_p=14, lo_rsi=30, hi_rsi=70,
                 sl_atr=1.5, tp_atr=1.5, max_ext_atr=None) -> Strategy:
    """Mean Reversion: harga tembus band + RSI ekstrem → taruhan balik ke mean.
    max_ext_atr: kalau diisi, SKIP entry yg jarak ke EMA50 > X ATR (anti over-extended)."""
    def prepare(bars):
        closes = [b["close"] for b in bars]
        mid, up, low = bollinger(closes, bb, mult)
        d = {"mid": mid, "up": up, "low": low, "rsi": rsi_series(closes, rsi_p)}
        if max_ext_atr is not None:
            d["ema50"] = ema_series(closes, 50); d["atr"] = atr_series(bars, 14)
        return d
    def signal(i, bars, pre):
        c = bars[i]["close"]; up = pre["up"][i]; low = pre["low"][i]; r = pre["rsi"][i]
        if math.isnan(up) or math.isnan(r):
            return None
        side = None
        if c < low and r < lo_rsi:  side = "buy"
        elif c > up and r > hi_rsi: side = "sell"
        if not side:
            return None
        if max_ext_atr is not None:
            e = pre["ema50"][i]; a = pre["atr"][i]
            if not math.isnan(e) and not math.isnan(a) and a > 0:
                if abs(c - e) / a > max_ext_atr:
                    return None
        return side
    tag = f" ext<{max_ext_atr}" if max_ext_atr is not None else ""
    return Strategy("MEANREV", f"Bollinger({bb},{mult})+RSI{rsi_p}<{lo_rsi}/>{hi_rsi}{tag}",
                    max(bb, rsi_p, 50) + 2, sl_atr, tp_atr, prepare, signal)


def make_maosc_quality(fast=10, slow=30, rsi_p=14, sl_atr=1.2, tp_atr=1.8,
                       use_macd=True, adx_min=25, skip_stoch_low=True, skip_london=True) -> Strategy:
    """MAOSC + filter kualitas dari analisa win-rate per kondisi indikator."""
    import datetime as _dt
    def prepare(bars):
        closes = [b["close"] for b in bars]
        return {"f": sma(closes, fast), "s": sma(closes, slow), "rsi": rsi_series(closes, rsi_p),
                "mh": macd_hist(closes), "adx": adx_vals(bars, 14), "stk": stoch_k(bars, 14),
                "hour": [_dt.datetime.fromtimestamp(b["time"]).hour for b in bars]}
    def signal(i, bars, pre):
        f, s, r = pre["f"], pre["s"], pre["rsi"][i]
        if math.isnan(r):
            return None
        side = None
        if crossed_up(f, s, i) and r < 70:  side = "buy"
        elif crossed_dn(f, s, i) and r > 30: side = "sell"
        if not side:
            return None
        mh, adx, stk, hr = pre["mh"][i], pre["adx"][i], pre["stk"][i], pre["hour"][i]
        if skip_london and 8 <= hr < 13:
            return None
        if adx_min and (math.isnan(adx) or adx < adx_min):
            return None
        if skip_stoch_low and not math.isnan(stk) and stk < 20:
            return None
        if use_macd and not math.isnan(mh):
            if side == "buy" and mh < 0:  return None
            if side == "sell" and mh > 0: return None
        return side
    return Strategy("MAOSCQ", f"MAOSC+filter(MACD,ADX>{adx_min},noStoch<20,noLondon)",
                    max(slow, rsi_p, 30) + 2, sl_atr, tp_atr, prepare, signal)


# ───────────────────────────── engine backtest ─────────────────────────────

@dataclass
class Result:
    name: str
    trades: int
    wins: int
    losses: int
    win_rate: float
    start_bal: float
    end_bal: float
    ret_pct: float
    pf: float
    max_dd_pct: float
    avg_win: float
    avg_loss: float
    avg_lot: float
    skip_atr: int
    skip_spread: int
    skip_cap: int
    bars: int
    trade_log: list = None


def fetch_indicators(api, symbol, tf, days, count):
    """Ambil deret indikator dari MT5 API → dict {bar_time: {indikator: nilai}}."""
    if days:
        end = dt.datetime.now(); start = end - dt.timedelta(days=days)
        d = api._get(f"/api/symbols/{symbol}/indicators/range", timeframe=tf,
                     from_time=str(int(start.timestamp())), to_time=str(int(end.timestamp())),
                     series="true")
    else:
        d = api._get(f"/api/symbols/{symbol}/indicators", timeframe=tf,
                     count=min(count, 10000), series="true")
    ind = d["indicators"]; times = ind["time"]
    names = [k for k in ind if k != "time"]
    return {times[i]: {n: ind[n][i] for n in names} for i in range(len(times))}


def run_backtest(bars, strat: Strategy, sinfo, *, balance=100.0, atr_period=14,
                 risk_pct=1.0, max_risk_pct=6.0, min_atr=0.0, max_spread_pct=8.0,
                 feat_by_time=None) -> Result:
    point = sinfo["point"]
    tick_size = sinfo.get("trade_tick_size") or point
    tick_value = sinfo.get("trade_tick_value") or 1.0
    money = lambda d, lot: (d / tick_size) * tick_value * lot

    pre = strat.prepare(bars)
    atr_arr = atr_series(bars, atr_period)
    warm = max(strat.warmup, atr_period + 2)

    start = balance
    peak = balance; max_dd_pct = 0.0
    trades = []
    skip = {"atr": 0, "spread": 0, "cap": 0}
    pos = None

    for i in range(warm, len(bars)):
        bar = bars[i]
        if pos:
            hit = None
            if pos["side"] == "buy":
                if bar["low"] <= pos["sl"]:    hit = pos["sl"]
                elif bar["high"] >= pos["tp"]: hit = pos["tp"]
            else:
                if bar["high"] >= pos["sl"]:   hit = pos["sl"]
                elif bar["low"] <= pos["tp"]:  hit = pos["tp"]
            if hit is not None:
                plp = (hit - pos["entry"]) if pos["side"] == "buy" else (pos["entry"] - hit)
                net = money(plp, pos["lot"]) - money(pos["spread"], pos["lot"])
                balance += net
                peak = max(peak, balance)
                if peak > 0:
                    dd = (peak - balance) / peak * 100
                    max_dd_pct = max(max_dd_pct, dd)
                trades.append({
                    "net": net, "lot": pos["lot"], "side": pos["side"],
                    "entry_time": pos["entry_time"], "entry_price": pos["entry"],
                    "exit_time": dt.datetime.fromtimestamp(bar["time"]).isoformat(),
                    "exit_price": hit, "sl": pos["sl"], "tp": pos["tp"],
                    "result": "TP" if hit == pos["tp"] else "SL",
                    "balance_after": balance, "features": pos.get("features"),
                })
                pos = None
        if pos:
            continue
        a = atr_arr[i]
        if math.isnan(a) or a <= 0:
            continue
        side = strat.signal(i, bars, pre)
        if not side:
            continue
        if a < min_atr:
            skip["atr"] += 1; continue
        spread_price = bar["spread"] * point
        if spread_price / a * 100 > max_spread_pct:
            skip["spread"] += 1; continue
        sl_d = strat.sl_atr * a; tp_d = strat.tp_atr * a
        lot, est_loss = calc_lot(balance * risk_pct / 100, sl_d, sinfo)
        if est_loss > balance * max_risk_pct / 100:
            skip["cap"] += 1; continue
        entry = bar["close"]
        pos = dict(side=side, entry=entry, lot=lot, spread=spread_price,
                   entry_time=dt.datetime.fromtimestamp(bar["time"]).isoformat(),
                   features=(feat_by_time.get(bar["time"]) if feat_by_time else None),
                   sl=entry - sl_d if side == "buy" else entry + sl_d,
                   tp=entry + tp_d if side == "buy" else entry - tp_d)

    wins = [t for t in trades if t["net"] > 0]
    losses = [t for t in trades if t["net"] <= 0]
    gw = sum(t["net"] for t in wins)
    gl = -sum(t["net"] for t in losses)
    return Result(
        name=strat.name, trades=len(trades), wins=len(wins), losses=len(losses),
        win_rate=len(wins) / len(trades) * 100 if trades else 0.0,
        start_bal=start, end_bal=balance,
        ret_pct=(balance - start) / start * 100,
        pf=(gw / gl) if gl else (float("inf") if gw else 0.0),
        max_dd_pct=max_dd_pct,
        avg_win=gw / len(wins) if wins else 0.0,
        avg_loss=-gl / len(losses) if losses else 0.0,
        avg_lot=sum(t["lot"] for t in trades) / len(trades) if trades else 0.0,
        skip_atr=skip["atr"], skip_spread=skip["spread"], skip_cap=skip["cap"],
        bars=len(bars), trade_log=trades,
    )


# ─────────────────────────────────── main ──────────────────────────────────

def fetch_bars(api, symbol, tf, days, n_bars):
    if days:
        end = dt.datetime.now(); start = end - dt.timedelta(days=days)
        d = api._get(f"/api/symbols/{symbol}/bars/range", timeframe=tf,
                     from_time=str(int(start.timestamp())), to_time=str(int(end.timestamp())))
        return d["bars"], f"{days} hari ({start:%Y-%m-%d} → {end:%m-%d %H:%M})"
    b = api.bars(symbol, tf, min(n_bars, 10000))
    return b, f"{len(b)} bar"


def main():
    p = argparse.ArgumentParser(description="Backtest 3 strategi research-backed")
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--tf", default="M15")
    p.add_argument("--bt-days", type=int, default=None)
    p.add_argument("--bt-bars", type=int, default=2000)
    p.add_argument("--balance", type=float, default=1000.0)
    p.add_argument("--risk", type=float, default=1.0)
    p.add_argument("--max-risk", type=float, default=6.0)
    p.add_argument("--min-atr", type=float, default=0.0)
    p.add_argument("--max-spread-pct", type=float, default=8.0)
    p.add_argument("--atr-period", type=int, default=14)
    p.add_argument("--only", default=None, help="TREND | MAOSC | MEANREV")
    p.add_argument("--journal", action="store_true", help="simpan run+trade ke journal")
    p.add_argument("--features", action="store_true", help="rekam snapshot indikator tiap entry (via MT5 indicator API)")
    p.add_argument("--api", default="http://192.168.0.116:8000")
    args = p.parse_args()

    api = MT5Api(args.api, timeout=120)
    sinfo = api.symbol_info(args.symbol)
    bars, period = fetch_bars(api, args.symbol, args.tf, args.bt_days, args.bt_bars)

    strategies = [make_trend(), make_maosc(), make_meanrev()]
    if args.only:
        strategies = [s for s in strategies if s.name == args.only.upper()]

    print(f"\n{'='*78}")
    print(f"BACKTEST 3 STRATEGI | {args.symbol} {args.tf} | {period} | {len(bars)} bar")
    print(f"Balance ${args.balance:.0f} | risk {args.risk}% (cap {args.max_risk}%) | "
          f"ATR≥${args.min_atr} | spread≤{args.max_spread_pct}%")
    print('='*78)

    pfrom = dt.datetime.fromtimestamp(bars[0]["time"]).isoformat() if bars else None
    pto = dt.datetime.fromtimestamp(bars[-1]["time"]).isoformat() if bars else None

    feat_by_time = None
    if args.features:
        print("Mengambil deret indikator dari MT5 API...")
        feat_by_time = fetch_indicators(api, args.symbol, args.tf, args.bt_days, args.bt_bars)
        print(f"  {len(feat_by_time)} bar ber-indikator.")

    results = []
    for s in strategies:
        r = run_backtest(bars, s, sinfo, balance=args.balance, atr_period=args.atr_period,
                         risk_pct=args.risk, max_risk_pct=args.max_risk,
                         min_atr=args.min_atr, max_spread_pct=args.max_spread_pct,
                         feat_by_time=feat_by_time)
        results.append((s, r))
        if args.journal:
            import journal
            params = dict(desc=s.desc, sl_atr=s.sl_atr, tp_atr=s.tp_atr, risk=args.risk,
                          max_risk=args.max_risk, max_spread_pct=args.max_spread_pct,
                          atr_period=args.atr_period)
            notes = (f"Backtest {args.symbol} {args.tf} {period}. "
                     f"{'PROFITABLE' if r.ret_pct > 0 else 'RUGI'}. "
                     f"PF {r.pf:.2f}, maxDD {r.max_dd_pct:.1f}%, avg lot {r.avg_lot:.3f}.")
            rid = journal.log_run(
                source="backtest", strategy=s.name, symbol=args.symbol, timeframe=args.tf,
                params=params, start_balance=r.start_bal, end_balance=r.end_bal,
                trades=r.trades, wins=r.wins, losses=r.losses, win_rate=r.win_rate,
                ret_pct=r.ret_pct, profit_factor=(r.pf if r.pf != float("inf") else 999),
                max_dd_pct=r.max_dd_pct, period_from=pfrom, period_to=pto, notes=notes)
            journal.log_trades(rid, "backtest", s.name, args.symbol, args.tf, r.trade_log or [])
    if args.journal:
        print(f"\n💾 Tersimpan ke journal: {len(strategies)} run + semua trade.")

    # tabel
    hdr = f"{'STRATEGI':9} {'desk':38} {'trade':>6} {'WR%':>6} {'return%':>8} {'PF':>5} {'maxDD%':>7} {'avglot':>7}"
    print("\n" + hdr); print("-" * len(hdr))
    for s, r in results:
        print(f"{r.name:9} {s.desc[:38]:38} {r.trades:6} {r.win_rate:6.1f} "
              f"{r.ret_pct:+8.2f} {r.pf:5.2f} {r.max_dd_pct:7.1f} {r.avg_lot:7.3f}")
    print()
    for s, r in results:
        skips = r.skip_atr + r.skip_spread + r.skip_cap
        print(f"  {r.name}: ${r.start_bal:.0f}→${r.end_bal:.2f} | "
              f"W{r.wins}/L{r.losses} | avgW ${r.avg_win:+.2f} avgL ${r.avg_loss:+.2f} | "
              f"skip {skips} (atr{r.skip_atr}/spr{r.skip_spread}/cap{r.skip_cap})")
    print("\nCatatan: bar-level (eksekusi di CLOSE), biaya spread per-bar dihitung, "
          "slippage & swap diabaikan. Sampel pendek = belum konklusif.\n")


if __name__ == "__main__":
    main()
