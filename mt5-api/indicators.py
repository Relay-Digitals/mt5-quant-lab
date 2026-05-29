"""
indicators.py — Kalkulasi indikator teknikal server-side (formula MT5/standar).

MetaTrader5 Python bridge TIDAK mengekspos buffer indikator native (iRSI dll
hanya ada di MQL5). Modul ini menghitung indikator dari OHLCV bar memakai
formula yang sama dengan MT5 (Wilder smoothing utk RSI/ATR/ADX, EMA utk MACD),
lalu di-publish via endpoint API.

compute(bars) -> dict { 'time':[...], '<indikator>':[...] } selaras index bar.
NaN -> None agar JSON-safe.
"""
from __future__ import annotations

import math
from typing import List, Optional

NAN = float("nan")


# ── helper smoothing ──
def _sma(v: List[float], p: int) -> List[float]:
    out = [NAN] * len(v)
    if len(v) < p:
        return out
    s = sum(v[:p]); out[p - 1] = s / p
    for i in range(p, len(v)):
        s += v[i] - v[i - p]; out[i] = s / p
    return out


def _ema(v: List[float], p: int) -> List[float]:
    out = [NAN] * len(v)
    if len(v) < p:
        return out
    k = 2 / (p + 1)
    seed = sum(v[:p]) / p
    out[p - 1] = seed; prev = seed
    for i in range(p, len(v)):
        prev = v[i] * k + prev * (1 - k); out[i] = prev
    return out


def _ema_skipnan(v: List[float], p: int) -> List[float]:
    """EMA atas list yg punya NaN di depan (utk MACD signal dari MACD line)."""
    out = [NAN] * len(v)
    start = next((i for i, x in enumerate(v) if x == x), None)
    if start is None or len(v) - start < p:
        return out
    seg = v[start:]
    e = _ema(seg, p)
    for i, x in enumerate(e):
        out[start + i] = x
    return out


def _rma(v: List[float], p: int) -> List[float]:
    """Wilder smoothing (SMMA)."""
    out = [NAN] * len(v)
    if len(v) < p:
        return out
    a = sum(v[:p]) / p; out[p - 1] = a
    for i in range(p, len(v)):
        a = (a * (p - 1) + v[i]) / p; out[i] = a
    return out


def _rsi(close: List[float], p: int = 14) -> List[float]:
    n = len(close); out = [NAN] * n
    if n < p + 1:
        return out
    gain = [0.0] * n; loss = [0.0] * n
    for i in range(1, n):
        d = close[i] - close[i - 1]
        gain[i] = max(d, 0.0); loss[i] = max(-d, 0.0)
    ag = sum(gain[1:p + 1]) / p; al = sum(loss[1:p + 1]) / p
    out[p] = 100 - 100 / (1 + (ag / al if al else float("inf")))
    for i in range(p + 1, n):
        ag = (ag * (p - 1) + gain[i]) / p
        al = (al * (p - 1) + loss[i]) / p
        out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def _true_range(bars) -> List[float]:
    tr = [NAN] * len(bars)
    for i in range(1, len(bars)):
        h, l, pc = bars[i]["high"], bars[i]["low"], bars[i - 1]["close"]
        tr[i] = max(h - l, abs(h - pc), abs(l - pc))
    return tr


def _atr(bars, p: int = 14) -> List[float]:
    tr = _true_range(bars)
    return _rma([0.0] + tr[1:], p) if len(bars) > 1 else [NAN] * len(bars)


def _adx(bars, p: int = 14):
    n = len(bars)
    pdm = [0.0] * n; mdm = [0.0] * n; tr = [0.0] * n
    for i in range(1, n):
        up = bars[i]["high"] - bars[i - 1]["high"]
        dn = bars[i - 1]["low"] - bars[i]["low"]
        pdm[i] = up if (up > dn and up > 0) else 0.0
        mdm[i] = dn if (dn > up and dn > 0) else 0.0
        h, l, pc = bars[i]["high"], bars[i]["low"], bars[i - 1]["close"]
        tr[i] = max(h - l, abs(h - pc), abs(l - pc))
    atr = _rma([0.0] + tr[1:], p)
    pdm_s = _rma([0.0] + pdm[1:], p)
    mdm_s = _rma([0.0] + mdm[1:], p)
    pdi = [NAN] * n; mdi = [NAN] * n; dx = [NAN] * n
    for i in range(n):
        a = atr[i]
        if a == a and a:
            pdi[i] = 100 * pdm_s[i] / a
            mdi[i] = 100 * mdm_s[i] / a
            s = pdi[i] + mdi[i]
            dx[i] = 100 * abs(pdi[i] - mdi[i]) / s if s else 0.0
    adx = _rma([x if x == x else 0.0 for x in dx], p)
    # mask warmup
    for i in range(min(2 * p, n)):
        adx[i] = NAN
    return pdi, mdi, adx


def _stoch(bars, k=14, d=3):
    n = len(bars); K = [NAN] * n
    for i in range(k - 1, n):
        win = bars[i - k + 1:i + 1]
        hh = max(b["high"] for b in win); ll = min(b["low"] for b in win)
        K[i] = 100 * (bars[i]["close"] - ll) / (hh - ll) if hh > ll else 50.0
    D = _ema_skipnan(K, d)
    return K, D


def _cci(bars, p=20):
    n = len(bars); out = [NAN] * n
    tp = [(b["high"] + b["low"] + b["close"]) / 3 for b in bars]
    for i in range(p - 1, n):
        win = tp[i - p + 1:i + 1]; ma = sum(win) / p
        md = sum(abs(x - ma) for x in win) / p
        out[i] = (tp[i] - ma) / (0.015 * md) if md else 0.0
    return out


def _willr(bars, p=14):
    n = len(bars); out = [NAN] * n
    for i in range(p - 1, n):
        win = bars[i - p + 1:i + 1]
        hh = max(b["high"] for b in win); ll = min(b["low"] for b in win)
        out[i] = -100 * (hh - bars[i]["close"]) / (hh - ll) if hh > ll else -50.0
    return out


def _mfi(bars, p=14):
    n = len(bars); out = [NAN] * n
    tp = [(b["high"] + b["low"] + b["close"]) / 3 for b in bars]
    rmf = [tp[i] * max(bars[i].get("tick_volume", 0), 0) for i in range(n)]
    for i in range(p, n):
        pos = neg = 0.0
        for j in range(i - p + 1, i + 1):
            if tp[j] > tp[j - 1]: pos += rmf[j]
            elif tp[j] < tp[j - 1]: neg += rmf[j]
        out[i] = 100.0 if neg == 0 else 100 - 100 / (1 + pos / neg)
    return out


def _obv(bars):
    n = len(bars); out = [0.0] * n
    for i in range(1, n):
        v = bars[i].get("tick_volume", 0)
        if bars[i]["close"] > bars[i - 1]["close"]: out[i] = out[i - 1] + v
        elif bars[i]["close"] < bars[i - 1]["close"]: out[i] = out[i - 1] - v
        else: out[i] = out[i - 1]
    return out


def _bollinger(close, p=20, mult=2.0):
    mid = _sma(close, p); up = [NAN] * len(close); lo = [NAN] * len(close)
    pctb = [NAN] * len(close); width = [NAN] * len(close)
    for i in range(p - 1, len(close)):
        win = close[i - p + 1:i + 1]; m = mid[i]
        sd = math.sqrt(sum((x - m) ** 2 for x in win) / p)
        up[i] = m + mult * sd; lo[i] = m - mult * sd
        rng = up[i] - lo[i]
        pctb[i] = (close[i] - lo[i]) / rng if rng else 0.5
        width[i] = rng / m * 100 if m else NAN
    return mid, up, lo, pctb, width


def _j(x):
    return None if (x is None or (isinstance(x, float) and x != x)) else x


def compute(bars) -> dict:
    """Hitung semua indikator. Return dict series selaras index bar (NaN->None)."""
    import datetime as dt
    n = len(bars)
    close = [b["close"] for b in bars]
    times = [b["time"] for b in bars]

    rsi14 = _rsi(close, 14)
    ema12 = _ema(close, 12); ema26 = _ema(close, 26)
    macd_line = [(a - b) if (a == a and b == b) else NAN for a, b in zip(ema12, ema26)]
    macd_sig = _ema_skipnan(macd_line, 9)
    macd_hist = [(l - s) if (l == l and s == s) else NAN for l, s in zip(macd_line, macd_sig)]
    atr14 = _atr(bars, 14)
    pdi, mdi, adx14 = _adx(bars, 14)
    stk, std = _stoch(bars, 14, 3)
    cci20 = _cci(bars, 20)
    willr14 = _willr(bars, 14)
    mfi14 = _mfi(bars, 14)
    obv = _obv(bars)
    ema9 = _ema(close, 9); ema21 = _ema(close, 21)
    ema50 = _ema(close, 50); ema200 = _ema(close, 200)
    sma20 = _sma(close, 20); sma50 = _sma(close, 50)
    bb_mid, bb_up, bb_lo, bb_pctb, bb_width = _bollinger(close, 20, 2.0)

    # turunan per-bar
    dist_ema50 = [NAN] * n; dist_ema200 = [NAN] * n; mom10 = [NAN] * n
    roc10 = [NAN] * n; obv_slope = [NAN] * n; vol_ratio = [NAN] * n
    body_pct = [NAN] * n; range_atr = [NAN] * n; hour = [NAN] * n; dow = [NAN] * n
    volsma = _sma([float(b.get("tick_volume", 0)) for b in bars], 20)
    for i in range(n):
        a = atr14[i]
        if a == a and a:
            if ema50[i] == ema50[i]: dist_ema50[i] = (close[i] - ema50[i]) / a
            if ema200[i] == ema200[i]: dist_ema200[i] = (close[i] - ema200[i]) / a
            range_atr[i] = (bars[i]["high"] - bars[i]["low"]) / a
        if i >= 10:
            mom10[i] = close[i] - close[i - 10]
            roc10[i] = (close[i] / close[i - 10] - 1) * 100 if close[i - 10] else NAN
        if i >= 5:
            obv_slope[i] = obv[i] - obv[i - 5]
        if volsma[i] == volsma[i] and volsma[i]:
            vol_ratio[i] = bars[i].get("tick_volume", 0) / volsma[i]
        rng = bars[i]["high"] - bars[i]["low"]
        body_pct[i] = (close[i] - bars[i]["open"]) / rng if rng else 0.0
        d = dt.datetime.fromtimestamp(times[i])
        hour[i] = d.hour; dow[i] = d.weekday()

    series = {
        "time": times,
        "rsi14": rsi14, "macd_line": macd_line, "macd_signal": macd_sig, "macd_hist": macd_hist,
        "adx14": adx14, "plus_di": pdi, "minus_di": mdi,
        "stoch_k": stk, "stoch_d": std, "cci20": cci20, "willr14": willr14,
        "mfi14": mfi14, "atr14": atr14,
        "ema9": ema9, "ema21": ema21, "ema50": ema50, "ema200": ema200,
        "sma20": sma20, "sma50": sma50,
        "bb_pctb": bb_pctb, "bb_width": bb_width,
        "dist_ema50_atr": dist_ema50, "dist_ema200_atr": dist_ema200,
        "mom10": mom10, "roc10": roc10, "obv_slope": obv_slope, "vol_ratio": vol_ratio,
        "body_pct": body_pct, "range_atr": range_atr, "hour": hour, "dow": dow,
    }
    return {k: [_j(x) for x in v] for k, v in series.items()}


def snapshot(series: dict, i: int) -> dict:
    """Ambil nilai semua indikator pada index bar i (point-in-time)."""
    return {k: v[i] for k, v in series.items() if k != "time"}
