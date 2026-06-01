"""
idx_backtest.py — Backtest saham Indonesia (EMA-cross & Mean-Reversion).
Metode SAMA dgn forex: 1 posisi, SL/TP=ATR, sizing risk%, + biaya transaksi ID (~0.2%/sisi).
Data dari Stockbit (daily OHLC ~92 candle). Long+short (ID retail realistis long-only — flag).

Usage:
  python3 idx_backtest.py                       # basket likuid, kedua strategi
  python3 idx_backtest.py --symbols BBCA,TLKM --long-only
"""
from __future__ import annotations
import argparse, math
from stockbit_client import Stockbit
import yahoo_client
import stockbit_history
import idx_indicators as ind

BASKET = ["BBCA","BBRI","BMRI","BBNI","TLKM","ASII","UNVR","ICBP","ADRO","ANTM"]
FEE_PCT = 0.2          # biaya per sisi (~0.4% round-trip, fee+pajak broker ID)
LOT = 100              # 1 lot = 100 lembar


def sig_ema(i, I, bars):
    e9,e21,e50 = I["ema9"],I["ema21"],I["ema50"]; c = bars[i]["close"]
    if any(math.isnan(x) for x in (e9[i],e9[i-1],e21[i],e21[i-1],e50[i])): return None
    if e9[i-1] <= e21[i-1] and e9[i] > e21[i] and c > e50[i]: return "buy"
    if e9[i-1] >= e21[i-1] and e9[i] < e21[i] and c < e50[i]: return "sell"
    return None

def sig_meanrev(i, I, bars):
    bpb,r = I["bb_pctb"],I["rsi14"];
    if math.isnan(bpb[i]) or math.isnan(r[i]): return None
    if bpb[i] < 0.15 and r[i] < 40: return "buy"
    if bpb[i] > 0.85 and r[i] > 60: return "sell"
    return None

STRATS = {"EMA-CROSS": (sig_ema, 1.5, 2.5), "MEANREV": (sig_meanrev, 1.5, 1.5)}


def backtest(bars, I, sig_fn, sl_atr, tp_atr, bal0=100_000_000, risk=1.0, long_only=False):
    atr = I["atr14"]; warm = 52
    bal = bal0; peak = bal; mdd = 0.0; pos = None; trades = []
    for i in range(warm, len(bars)):
        bar = bars[i]
        if pos:
            hit = None
            if pos["side"] == "buy":
                if bar["low"] <= pos["sl"]: hit = pos["sl"]
                elif bar["high"] >= pos["tp"]: hit = pos["tp"]
            else:
                if bar["high"] >= pos["sl"]: hit = pos["sl"]
                elif bar["low"] <= pos["tp"]: hit = pos["tp"]
            if hit is not None:
                gross = (hit-pos["entry"])*pos["sh"] if pos["side"]=="buy" else (pos["entry"]-hit)*pos["sh"]
                fee = FEE_PCT/100*(pos["entry"]+hit)*pos["sh"]
                net = gross-fee; bal += net; peak = max(peak,bal); mdd = max(mdd,(peak-bal)/peak*100)
                trades.append({"net":net,"side":pos["side"],"feat":pos["feat"],"result":"TP" if hit==pos["tp"] else "SL"})
                pos = None
        if pos: continue
        a = atr[i]
        if a is None or math.isnan(a) or a <= 0: continue
        side = sig_fn(i, I, bars)
        if not side or (long_only and side == "sell"): continue
        sl_d = sl_atr*a; tp_d = tp_atr*a; entry = bar["close"]
        sh_risk = (bal*risk/100)/sl_d        # lembar dari risk 1%
        sh_cash = (bal*0.999)/entry          # cap MODAL: posisi ≤ kas (no leverage, sisakan fee)
        sh = int(min(sh_risk, sh_cash) // LOT) * LOT
        if sh < LOT: continue
        feat = {k: I[k][i] for k in I if not math.isnan(I[k][i])} if False else {}  # fitur ringan
        pos = dict(side=side, entry=entry, sh=sh, feat=feat,
                   sl=entry-sl_d if side=="buy" else entry+sl_d,
                   tp=entry+tp_d if side=="buy" else entry-tp_d)
    wins = [t for t in trades if t["net"] > 0]
    ret = (bal-bal0)/bal0*100
    gl = -sum(t["net"] for t in trades if t["net"] <= 0)
    pf = (sum(t["net"] for t in wins)/gl) if gl else (999 if wins else 0)
    return dict(trades=len(trades), wr=len(wins)/len(trades)*100 if trades else 0,
                ret=ret, pf=pf, dd=mdd, net=bal-bal0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default=",".join(BASKET))
    ap.add_argument("--long-only", action="store_true")
    ap.add_argument("--source", default="sbhist", choices=["sbhist", "yahoo", "stockbit"],
                    help="sbhist=Stockbit native s/d 10thn (default), yahoo=5thn, stockbit=~92hr")
    ap.add_argument("--years", type=float, default=10.0, help="kedalaman history (sbhist)")
    ap.add_argument("--range", default="5y", help="range Yahoo")
    args = ap.parse_args()
    sb = Stockbit() if args.source == "stockbit" else None
    if args.source == "sbhist":
        get_bars = lambda s: stockbit_history.historical(s, args.years)
        src_lbl = f"Stockbit native {args.years:.0f}thn (paginasi)"
    elif args.source == "yahoo":
        get_bars = lambda s: yahoo_client.candles(s, args.range)
        src_lbl = f"Yahoo {args.range}"
    else:
        get_bars = lambda s: sb.candles(s); src_lbl = "Stockbit ~92 candle"
    syms = [s.strip() for s in args.symbols.split(",")]
    print(f"BACKTEST SAHAM ID | {src_lbl} | modal Rp100jt | fee {FEE_PCT}%/sisi | "
          f"{'LONG-ONLY' if args.long_only else 'long+short'}")
    for sname, (fn, sl, tp) in STRATS.items():
        print(f"\n=== {sname} (SL {sl}×ATR, TP {tp}×ATR) ===")
        print(f"{'saham':7}{'trade':>6}{'WR%':>6}{'return%':>8}{'PF':>6}{'DD%':>6}{'net(Rp)':>14}")
        agg_net = 0; agg_tr = 0
        for s in syms:
            try:
                bars = get_bars(s)
                if len(bars) < 55: print(f"{s:7} data kurang ({len(bars)})"); continue
                I = ind.compute(bars)
                r = backtest(bars, I, fn, sl, tp, long_only=args.long_only)
                agg_net += r["net"]; agg_tr += r["trades"]
                print(f"{s:7}{r['trades']:>6}{r['wr']:>6.0f}{r['ret']:>+8.1f}{r['pf']:>6.2f}{r['dd']:>6.1f}{r['net']:>+14,.0f}")
            except Exception as e:
                print(f"{s:7} err: {str(e)[:50]}")
        print(f"{'TOTAL':7}{agg_tr:>6}{'':>6}{'':>8}{'':>6}{'':>6}{agg_net:>+14,.0f}")
    print("\nCatatan: Yahoo 5thn daily. Hasil mentah negatif (fee+choppy) — langkah lanjut: filter loss-prone + holdout (spt forex).")


if __name__ == "__main__":
    main()
