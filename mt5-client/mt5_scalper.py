"""
mt5_scalper.py — EMA Scalping algo untuk MT5 (lewat REST API CT 132).

Strategi: EMA-cross scalping dengan trend filter + ATR-based SL/TP + 1% risk sizing.

  • Timeframe default : M1 (scalping)
  • Sinyal BUY  : EMA_fast cross-UP   EMA_slow  DAN  close > EMA_trend
  • Sinyal SELL : EMA_fast cross-DOWN EMA_slow  DAN  close < EMA_trend
  • SL          : entry ∓ (sl_atr × ATR)         (ketat — konservatif)
  • TP          : entry ± (tp_atr × ATR)
  • Lot         : dihitung dinamis supaya risiko = risk_pct × balance (default 1%)
  • Guard       : maksimum 1 posisi (per magic), filter spread, filter ATR minimum

Aliran data:
  script (Mac) → HTTP → REST API 192.168.0.116:8000 → mt5linux RPyC → MT5 (Exness)

SAFETY: default DRY-RUN (paper). Order BENAR-BENAR dikirim hanya dengan flag --live.

Usage:
  python3 mt5_scalper.py                      # paper, loop, M1 XAUUSD
  python3 mt5_scalper.py --once               # evaluasi 1x lalu keluar (paper)
  python3 mt5_scalper.py --live               # LIVE — kirim order sungguhan
  python3 mt5_scalper.py --symbol XAUUSD --tf M5 --risk 1.0 --sl-atr 1.2 --tp-atr 1.8
  python3 mt5_scalper.py --backtest --bt-bars 1500   # backtest cepat di bar historis
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
from dataclasses import dataclass
from typing import Optional

import requests

API_BASE = "http://192.168.0.116:8000"
MAGIC = 770001  # penanda posisi milik algo ini (beda dari mt5-api default 123456)


# ───────────────────────────────── config ──────────────────────────────────

@dataclass
class Config:
    symbol: str = "XAUUSD"
    timeframe: str = "M1"
    ema_fast: int = 9
    ema_slow: int = 21
    ema_trend: int = 50          # filter arah tren (0 = matikan filter)
    atr_period: int = 14
    sl_atr: float = 1.2          # SL = 1.2 × ATR  (ketat)
    tp_atr: float = 1.8          # TP = 1.8 × ATR  (R:R = 1.5)
    risk_pct: float = 1.0        # % balance per trade (target sizing)
    max_risk_pct: float = 3.0    # HARD CAP: skip entry kalau risk min-lot > ini
    max_spread_atr_pct: float = 8.0  # skip kalau spread > ini % dari ATR (adaptif)
    max_spread_points: int = 600 # ceiling absolut spread (safety)
    min_atr_price: float = 1.0   # skip kalau ATR < ini (dalam HARGA/$, = nilai di indikator)
    breakeven_atr: float = 1.0   # geser SL ke entry saat profit ≥ 1.0×ATR (0 = off)
    poll_seconds: int = 5        # interval cek bar baru
    deviation: int = 30
    live: bool = False
    comment: str = "ema-scalper"


# ─────────────────────────────── API client ────────────────────────────────

class MT5Api:
    def __init__(self, base: str = API_BASE, timeout: int = 15):
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.s = requests.Session()

    def _get(self, path: str, **params):
        r = self.s.get(self.base + path, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, body: dict):
        r = self.s.post(self.base + path, json=body, timeout=self.timeout)
        if r.status_code >= 400:
            raise RuntimeError(f"{path} → {r.status_code}: {r.text}")
        return r.json()

    def account(self) -> dict:
        return self._get("/api/account")

    def symbol_info(self, symbol: str) -> dict:
        return self._get(f"/api/symbols/{symbol}")

    def tick(self, symbol: str) -> dict:
        return self._get(f"/api/symbols/{symbol}/tick")

    def bars(self, symbol: str, timeframe: str, count: int) -> list[dict]:
        d = self._get(f"/api/symbols/{symbol}/bars", timeframe=timeframe, count=count)
        return d["bars"]

    def positions(self, symbol: str) -> list[dict]:
        return self._get("/api/positions", symbol=symbol)["items"]

    def order_send(self, symbol: str, side: str, volume: float,
                   sl: float, tp: float, deviation: int, comment: str) -> dict:
        body = dict(symbol=symbol, side=side, volume=volume, sl=sl, tp=tp,
                    deviation=deviation, magic=MAGIC, comment=comment)
        return self._post("/api/orders/send", body)

    def order_check(self, symbol: str, side: str, volume: float,
                    sl: float, tp: float, deviation: int, comment: str) -> dict:
        body = dict(symbol=symbol, side=side, volume=volume, sl=sl, tp=tp,
                    deviation=deviation, magic=MAGIC, comment=comment)
        return self._post("/api/orders/check", body)

    def position_modify(self, ticket: int, sl: float, tp: float) -> dict:
        return self._post("/api/positions/modify", dict(ticket=ticket, sl=sl, tp=tp))


# ─────────────────────────────── indikator ─────────────────────────────────

def ema(values: list[float], period: int) -> list[float]:
    """EMA penuh; out[i] = EMA sampai bar ke-i. Seed = SMA periode pertama."""
    if len(values) < period:
        return []
    k = 2 / (period + 1)
    out: list[float] = []
    seed = sum(values[:period]) / period
    out.append(seed)
    prev = seed
    for v in values[period:]:
        prev = v * k + prev * (1 - k)
        out.append(prev)
    # pad depan supaya index sejajar dgn values
    return [float("nan")] * (period - 1) + out


def atr(bars: list[dict], period: int) -> float:
    """ATR (Wilder) dari list bar OHLC. Return nilai ATR terakhir (harga)."""
    if len(bars) < period + 1:
        return 0.0
    trs: list[float] = []
    for i in range(1, len(bars)):
        h, l = bars[i]["high"], bars[i]["low"]
        pc = bars[i - 1]["close"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    # Wilder smoothing
    a = sum(trs[:period]) / period
    for tr in trs[period:]:
        a = (a * (period - 1) + tr) / period
    return a


# ─────────────────────────────── sinyal ────────────────────────────────────

@dataclass
class Signal:
    side: Optional[str]          # "buy" | "sell" | None
    reason: str
    ema_fast: float = 0.0
    ema_slow: float = 0.0
    ema_trend: float = 0.0
    atr: float = 0.0
    close: float = 0.0


def evaluate(bars: list[dict], cfg: Config) -> Signal:
    """Evaluasi sinyal pada bar TERAKHIR YANG SUDAH CLOSE (bars[-1])."""
    closes = [b["close"] for b in bars]
    need = max(cfg.ema_slow, cfg.ema_trend, cfg.atr_period) + 2
    if len(closes) < need:
        return Signal(None, f"data kurang ({len(closes)}/{need})")

    ef = ema(closes, cfg.ema_fast)
    es = ema(closes, cfg.ema_slow)
    et = ema(closes, cfg.ema_trend) if cfg.ema_trend > 0 else None
    a = atr(bars, cfg.atr_period)
    c = closes[-1]

    ef0, ef1 = ef[-2], ef[-1]
    es0, es1 = es[-2], es[-1]
    trend = et[-1] if et else c

    cross_up = ef0 <= es0 and ef1 > es1
    cross_dn = ef0 >= es0 and ef1 < es1

    sig = Signal(None, "no cross", ef1, es1, trend, a, c)

    if cross_up:
        if cfg.ema_trend == 0 or c > trend:
            sig.side, sig.reason = "buy", "EMA cross-up + tren naik"
        else:
            sig.reason = "cross-up tapi di bawah EMA tren (skip)"
    elif cross_dn:
        if cfg.ema_trend == 0 or c < trend:
            sig.side, sig.reason = "sell", "EMA cross-down + tren turun"
        else:
            sig.reason = "cross-down tapi di atas EMA tren (skip)"
    return sig


# ───────────────────────────── lot sizing & order ──────────────────────────

def round_step(vol: float, step: float, vmin: float, vmax: float) -> float:
    if step <= 0:
        step = 0.01
    v = round(round(vol / step) * step, 8)
    # floor ke step utk konservatif
    v = round((int(vol / step)) * step, 8)
    return max(vmin, min(vmax, v))


def calc_lot(risk_money: float, sl_distance: float, sinfo: dict) -> tuple[float, float]:
    """Hitung lot supaya potensi loss di SL ≈ risk_money.

    loss_per_lot = (sl_distance / tick_size) * tick_value
    Return (lot_dibulatkan_ke_step, estimasi_loss_pakai_lot_itu).
    """
    tick_size = sinfo.get("trade_tick_size") or sinfo["point"]
    tick_value = sinfo.get("trade_tick_value") or 1.0
    vmin = sinfo["volume_min"]; vmax = sinfo["volume_max"]; vstep = sinfo["volume_step"]

    loss_per_lot = (sl_distance / tick_size) * tick_value
    if loss_per_lot <= 0:
        return vmin, 0.0
    raw_lot = risk_money / loss_per_lot
    lot = round_step(raw_lot, vstep, vmin, vmax)
    est_loss = lot * loss_per_lot
    return lot, est_loss


# ─────────────────────────────── runner ────────────────────────────────────

def log(msg: str) -> None:
    ts = dt.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def manage_breakeven(api: MT5Api, cfg: Config, sinfo: dict) -> None:
    """Geser SL ke break-even saat profit ≥ breakeven_atr × ATR."""
    if cfg.breakeven_atr <= 0:
        return
    poss = [p for p in api.positions(cfg.symbol) if p.get("magic") == MAGIC]
    if not poss:
        return
    bars = api.bars(cfg.symbol, cfg.timeframe, cfg.atr_period + 5)
    a = atr(bars, cfg.atr_period)
    tick = api.tick(cfg.symbol)
    for p in poss:
        entry = p["price_open"]
        is_buy = p["type"] == 0
        cur = tick["bid"] if is_buy else tick["ask"]
        moved = (cur - entry) if is_buy else (entry - cur)
        if moved >= cfg.breakeven_atr * a:
            be = entry  # break-even
            already = (is_buy and p["sl"] >= entry) or ((not is_buy) and 0 < p["sl"] <= entry)
            if already:
                continue
            log(f"→ break-even: geser SL ticket {p['ticket']} ke {be:.{sinfo['digits']}f}")
            if cfg.live:
                api.position_modify(p["ticket"], sl=round(be, sinfo["digits"]), tp=p["tp"])


def step_once(api: MT5Api, cfg: Config, sinfo: dict, state: dict) -> None:
    bars = api.bars(cfg.symbol, cfg.timeframe, 200)
    # bars[-1] dari copy_rates_from_pos = bar berjalan (belum close).
    # Pakai bar yang SUDAH close → buang bar terakhir.
    closed = bars[:-1]
    last_closed_time = closed[-1]["time"]

    # break-even management tiap cycle
    try:
        manage_breakeven(api, cfg, sinfo)
    except Exception as e:
        log(f"(breakeven skip: {type(e).__name__}: {e})")

    # hanya evaluasi sinyal sekali per bar baru
    if state.get("last_bar") == last_closed_time:
        return
    state["last_bar"] = last_closed_time

    sig = evaluate(closed, cfg)
    digits = sinfo["digits"]
    point = sinfo["point"]
    spread_pts = int(round((api.tick(cfg.symbol)["ask"] - api.tick(cfg.symbol)["bid"]) / point))

    bar_iso = dt.datetime.fromtimestamp(last_closed_time).strftime("%m-%d %H:%M")
    log(f"bar {bar_iso} | close={sig.close:.{digits}f} EMA{cfg.ema_fast}={sig.ema_fast:.{digits}f} "
        f"EMA{cfg.ema_slow}={sig.ema_slow:.{digits}f} ATR={sig.atr:.{digits}f} "
        f"spread={spread_pts}p | {sig.reason}")

    if sig.side is None:
        return

    # ── filter ──
    spread_price = spread_pts * point
    # 1) ATR minimum (satuan HARGA/$, sama dgn indikator MT5)
    if sig.atr < cfg.min_atr_price:
        log(f"✗ SKIP: ATR ${sig.atr:.{digits}f} < min ${cfg.min_atr_price:.2f} (pasar sepi)")
        return
    # 2) spread relatif ATR (adaptif tiap TF) + ceiling absolut
    spread_ratio = (spread_price / sig.atr * 100) if sig.atr else 999
    if spread_ratio > cfg.max_spread_atr_pct:
        log(f"✗ SKIP: spread ${spread_price:.{digits}f} = {spread_ratio:.1f}% dari ATR "
            f"> max {cfg.max_spread_atr_pct:.0f}% (biaya terlalu mahal)")
        return
    if spread_pts > cfg.max_spread_points:
        log(f"✗ SKIP: spread {spread_pts}p > ceiling {cfg.max_spread_points}p")
        return

    # ── guard: sudah ada posisi algo ini? ──
    poss = [p for p in api.positions(cfg.symbol) if p.get("magic") == MAGIC]
    if poss:
        log(f"✗ SKIP: sudah ada {len(poss)} posisi algo (max 1)")
        return

    # ── hitung SL/TP & lot ──
    tick = api.tick(cfg.symbol)
    entry = tick["ask"] if sig.side == "buy" else tick["bid"]
    sl_dist = cfg.sl_atr * sig.atr
    tp_dist = cfg.tp_atr * sig.atr
    if sig.side == "buy":
        sl = round(entry - sl_dist, digits); tp = round(entry + tp_dist, digits)
    else:
        sl = round(entry + sl_dist, digits); tp = round(entry - tp_dist, digits)

    acc = api.account()
    risk_money = acc["balance"] * cfg.risk_pct / 100.0
    lot, est_loss = calc_lot(risk_money, sl_dist, sinfo)

    rr = tp_dist / sl_dist if sl_dist else 0
    log(f"➤ SINYAL {sig.side.upper()} {cfg.symbol} @ {entry:.{digits}f} | "
        f"SL {sl:.{digits}f} (−{sl_dist:.{digits}f}) TP {tp:.{digits}f} (+{tp_dist:.{digits}f}) "
        f"R:R={rr:.2f}")
    log(f"   lot={lot} | est.risk=${est_loss:.2f} (target ${risk_money:.2f} = {cfg.risk_pct}%) "
        f"| balance=${acc['balance']:.2f}")

    # HARD CAP: lindungi akun kecil — lot minimum bisa memaksa risk > target
    max_risk_money = acc["balance"] * cfg.max_risk_pct / 100.0
    if est_loss > max_risk_money:
        log(f"   ✗ SKIP: est.risk ${est_loss:.2f} ({est_loss/acc['balance']*100:.1f}%) "
            f"> hard-cap {cfg.max_risk_pct}% (${max_risk_money:.2f}). "
            f"Lot min {sinfo['volume_min']} terlalu besar utk SL ${sl_dist:.{digits}f} di balance ini.")
        return
    if est_loss > risk_money * 1.5:
        log(f"   ⚠ est.risk ${est_loss:.2f} = {est_loss/acc['balance']*100:.1f}% "
            f"(target {cfg.risk_pct}%, masih di bawah cap {cfg.max_risk_pct}%).")

    if not cfg.live:
        # dry-run: validasi lewat order_check tapi TIDAK kirim
        try:
            chk = api.order_check(cfg.symbol, sig.side, lot, sl, tp, cfg.deviation, cfg.comment)
            res = chk.get("result", {})
            log(f"   [PAPER] order_check retcode={res.get('retcode')} ({res.get('comment')}) "
                f"margin_free_after={res.get('margin_free')}")
        except Exception as e:
            log(f"   [PAPER] order_check error: {e}")
        log("   [PAPER] order TIDAK dikirim. Jalankan dgn --live untuk eksekusi nyata.")
        return

    # ── LIVE ──
    try:
        out = api.order_send(cfg.symbol, sig.side, lot, sl, tp, cfg.deviation, cfg.comment)
        res = out.get("result", {})
        log(f"   ✓ LIVE order_send retcode={res.get('retcode')} deal={res.get('deal')} "
            f"order={res.get('order')} price={res.get('price')} vol={res.get('volume')}")
    except Exception as e:
        log(f"   ✗ LIVE order_send GAGAL: {e}")


# ─────────────────────────────── backtest ──────────────────────────────────

def backtest(api: MT5Api, cfg: Config, sinfo: dict, n_bars: int,
             start_balance: float = 100.0, days: Optional[int] = None) -> None:
    point = sinfo["point"]
    tick_size = sinfo.get("trade_tick_size") or point
    tick_value = sinfo.get("trade_tick_value") or 1.0
    # $ untuk gerak harga d pada lot tertentu
    money = lambda d, lot: (d / tick_size) * tick_value * lot

    # ── ambil data ──
    if days:
        end = dt.datetime.now(); start = end - dt.timedelta(days=days)
        d = api._get(f"/api/symbols/{cfg.symbol}/bars/range", timeframe=cfg.timeframe,
                     from_time=str(int(start.timestamp())), to_time=str(int(end.timestamp())))
        bars = d["bars"]
        period = f"{days} hari ({start:%Y-%m-%d} → {end:%Y-%m-%d %H:%M})"
    else:
        bars = api.bars(cfg.symbol, cfg.timeframe, min(n_bars, 10000))
        period = f"{len(bars)} bar"

    log(f"=== BACKTEST {cfg.symbol} {cfg.timeframe} | {period} ===")
    log(f"    EMA{cfg.ema_fast}/{cfg.ema_slow}/trend{cfg.ema_trend} | SL {cfg.sl_atr}×ATR TP {cfg.tp_atr}×ATR "
        f"| risk {cfg.risk_pct}% (cap {cfg.max_risk_pct}%) | ATR≥${cfg.min_atr_price} spread≤{cfg.max_spread_atr_pct}%")
    log(f"    Start balance: ${start_balance:.2f}")

    warm = max(cfg.ema_slow, cfg.ema_trend, cfg.atr_period) + 5
    if len(bars) <= warm:
        log(f"Data kurang ({len(bars)} bar, butuh > {warm}).")
        return

    balance = start_balance
    peak = balance
    max_dd = 0.0; max_dd_pct = 0.0
    trades: list[dict] = []
    skips = {"atr": 0, "spread": 0, "riskcap": 0}
    pos = None

    for i in range(warm, len(bars)):
        window = bars[: i + 1]
        bar = bars[i]
        # kelola posisi terbuka: cek SL/TP kena di bar ini (pakai high/low)
        if pos:
            hit = None
            if pos["side"] == "buy":
                if bar["low"] <= pos["sl"]:    hit = ("SL", pos["sl"])
                elif bar["high"] >= pos["tp"]: hit = ("TP", pos["tp"])
            else:
                if bar["high"] >= pos["sl"]:   hit = ("SL", pos["sl"])
                elif bar["low"] <= pos["tp"]:  hit = ("TP", pos["tp"])
            if hit:
                _, exitp = hit
                plp = (exitp - pos["entry"]) if pos["side"] == "buy" else (pos["entry"] - exitp)
                gross = money(plp, pos["lot"])
                cost = money(pos["spread_price"], pos["lot"])  # biaya spread 1× (round-turn approx)
                net = gross - cost
                balance += net
                peak = max(peak, balance)
                dd = peak - balance
                if dd > max_dd:
                    max_dd = dd; max_dd_pct = dd / peak * 100
                trades.append({**pos, "exit": exitp, "net": net, "result": hit[0], "balance": balance})
                pos = None
        if pos:
            continue

        sig = evaluate(window, cfg)
        if not (sig.side and sig.atr > 0):
            continue
        # filter sama seperti live
        if sig.atr < cfg.min_atr_price:
            skips["atr"] += 1; continue
        spread_price = bar["spread"] * point
        if sig.atr and spread_price / sig.atr * 100 > cfg.max_spread_atr_pct:
            skips["spread"] += 1; continue
        # sizing + hard cap
        sl_d = cfg.sl_atr * sig.atr; tp_d = cfg.tp_atr * sig.atr
        risk_money = balance * cfg.risk_pct / 100
        lot, est_loss = calc_lot(risk_money, sl_d, sinfo)
        if est_loss > balance * cfg.max_risk_pct / 100:
            skips["riskcap"] += 1; continue
        entry = bar["close"]
        side = sig.side
        pos = dict(side=side, entry=entry, lot=lot, spread_price=spread_price,
                   sl=entry - sl_d if side == "buy" else entry + sl_d,
                   tp=entry + tp_d if side == "buy" else entry - tp_d)

    # ── laporan ──
    if not trades:
        log(f"Tidak ada trade. Sinyal di-skip → ATR:{skips['atr']} spread:{skips['spread']} "
            f"risk-cap:{skips['riskcap']}")
        return
    wins = [t for t in trades if t["net"] > 0]
    losses = [t for t in trades if t["net"] <= 0]
    wr = len(wins) / len(trades) * 100
    net_total = balance - start_balance
    ret = net_total / start_balance * 100
    gross_win = sum(t["net"] for t in wins)
    gross_loss = -sum(t["net"] for t in losses)
    pf = gross_win / gross_loss if gross_loss else float("inf")
    avg_lot = sum(t["lot"] for t in trades) / len(trades)

    log("─" * 52)
    log(f"Total trade   : {len(trades)}   (Win {len(wins)} / Loss {len(losses)})   Win-rate {wr:.1f}%")
    log(f"Sinyal skip   : ATR {skips['atr']} | spread {skips['spread']} | risk-cap {skips['riskcap']}")
    log(f"Balance       : ${start_balance:.2f}  →  ${balance:.2f}   ({ret:+.2f}%)")
    log(f"Net P/L       : ${net_total:+.2f}   (sudah dikurangi biaya spread)")
    log(f"Profit factor : {pf:.2f}")
    log(f"Max drawdown  : ${max_dd:.2f}  ({max_dd_pct:.1f}%)")
    if wins:   log(f"Avg win       : ${gross_win/len(wins):+.2f}")
    if losses: log(f"Avg loss      : ${-gross_loss/len(losses):+.2f}")
    log(f"Avg lot       : {avg_lot:.3f}   (min broker {sinfo['volume_min']})")
    log("─" * 52)
    log("Catatan: eksekusi di harga CLOSE bar; biaya spread per-bar SUDAH dihitung; "
        "slippage & swap diabaikan. Untuk scalping, tick-level lebih akurat.")


# ─────────────────────────────────── main ──────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="EMA Scalping algo untuk MT5 (REST API)")
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--tf", default="M1")
    p.add_argument("--ema-fast", type=int, default=9)
    p.add_argument("--ema-slow", type=int, default=21)
    p.add_argument("--ema-trend", type=int, default=50)
    p.add_argument("--atr-period", type=int, default=14)
    p.add_argument("--sl-atr", type=float, default=1.2)
    p.add_argument("--tp-atr", type=float, default=1.8)
    p.add_argument("--risk", type=float, default=1.0, help="%% balance per trade (target)")
    p.add_argument("--max-risk", type=float, default=3.0, help="%% hard-cap, skip kalau lebih")
    p.add_argument("--min-atr", type=float, default=1.0, help="ATR minimum dlm $ (nilai indikator)")
    p.add_argument("--max-spread-pct", type=float, default=8.0, help="max spread sbg %% ATR")
    p.add_argument("--max-spread", type=int, default=600, help="ceiling spread absolut (points)")
    p.add_argument("--breakeven-atr", type=float, default=1.0, help="0 = matikan break-even")
    p.add_argument("--poll", type=int, default=5)
    p.add_argument("--live", action="store_true", help="kirim order SUNGGUHAN (default paper)")
    p.add_argument("--once", action="store_true", help="evaluasi 1x lalu keluar")
    p.add_argument("--backtest", action="store_true")
    p.add_argument("--bt-bars", type=int, default=1500)
    p.add_argument("--bt-days", type=int, default=None, help="backtest pakai N hari terakhir (range)")
    p.add_argument("--balance", type=float, default=100.0, help="start balance simulasi backtest")
    p.add_argument("--api", default=API_BASE)
    args = p.parse_args()

    cfg = Config(
        symbol=args.symbol, timeframe=args.tf,
        ema_fast=args.ema_fast, ema_slow=args.ema_slow, ema_trend=args.ema_trend,
        atr_period=args.atr_period, sl_atr=args.sl_atr, tp_atr=args.tp_atr,
        risk_pct=args.risk, max_risk_pct=args.max_risk,
        max_spread_atr_pct=args.max_spread_pct, max_spread_points=args.max_spread,
        min_atr_price=args.min_atr,
        breakeven_atr=args.breakeven_atr, poll_seconds=args.poll, live=args.live,
    )

    api = MT5Api(args.api)
    try:
        sinfo = api.symbol_info(cfg.symbol)
        acc = api.account()
    except Exception as e:
        sys.exit(f"Gagal konek REST API ({args.api}): {e}\n"
                 f"Cek MT5 terminal sudah login broker (http://192.168.0.116:3000).")

    log(f"Akun {acc['login']} | {acc.get('server','?')} | balance=${acc['balance']:.2f} "
        f"equity=${acc['equity']:.2f} | {cfg.symbol} {cfg.timeframe}")
    log(f"Strategi EMA{cfg.ema_fast}/{cfg.ema_slow}/trend{cfg.ema_trend} | "
        f"SL {cfg.sl_atr}×ATR  TP {cfg.tp_atr}×ATR | "
        f"MODE: {'🔴 LIVE' if cfg.live else '🟢 PAPER (dry-run)'}")
    log(f"Filter: risk {cfg.risk_pct}% (cap {cfg.max_risk_pct}%) | ATR≥${cfg.min_atr_price} | "
        f"spread≤{cfg.max_spread_atr_pct}% ATR")

    if args.backtest:
        backtest(api, cfg, sinfo, args.bt_bars, start_balance=args.balance, days=args.bt_days)
        return

    state: dict = {}
    if args.once:
        step_once(api, cfg, sinfo, state)
        return

    log(f"Loop tiap {cfg.poll_seconds}s — Ctrl+C utk berhenti.")
    try:
        while True:
            try:
                step_once(api, cfg, sinfo, state)
            except requests.RequestException as e:
                log(f"(network: {type(e).__name__}: {e})")
            except Exception as e:
                log(f"(error: {type(e).__name__}: {e})")
            time.sleep(cfg.poll_seconds)
    except KeyboardInterrupt:
        log("Berhenti.")


if __name__ == "__main__":
    main()
