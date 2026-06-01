"""
idx_foreign.py — Strategi FOREIGN FLOW (ikuti aliran asing) saham ID.
Data net_foreign harian dari Stockbit historical (10thn). Smart-money follow:
  LONG saat asing AKUMULASI (Σ net_foreign N-hari > 0), EXIT saat DISTRIBUSI (< 0).
Regime-following (exit on flip), bukan SL/TP scalp. Compounding, fee 0.2%/sisi, lot 100.

Usage:
  python3 idx_foreign.py report                       # basket, full 10thn
  python3 idx_foreign.py holdout --symbols BMRI,BBCA  # train/holdout
  python3 idx_foreign.py report --price-filter        # + konfirmasi harga>SMA20
"""
from __future__ import annotations
import argparse, math
import stockbit_history
import idx_indicators as ind

# Default universe = KOMODITAS/ENERGI (di situ regime foreign-flow tervalidasi OOS).
# Bank/consumer pakai idx_analyze MEANREV deep-oversold (komplementer).
BASKET = ["ADRO","MEDC","ANTM","INCO","BBCA","BBRI","BMRI","ASII","TLKM","PGAS"]
# Lolos holdout nf=60 (train→holdout profit): ADRO +30→+17 PF9.8, MEDC +52→+24 PF4.8,
# ANTM +9→+20 PF3.3, BBCA +17→+0.6 (nf=20:+3.0). Gagal OOS: BBRI/BMRI/ASII/TLKM/PGAS.
VALID = ["ADRO","MEDC","ANTM","INCO"]   # komoditas/energi tervalidasi
FEE = 0.2; LOT = 100


def backtest(bars, lo, hi, nf_win=5, price_filter=False, bal0=100_000_000):
    n = len(bars)
    nf = [b.get("net_foreign", 0) for b in bars]
    nfsum = [None]*n
    for i in range(n):
        if i >= nf_win-1:
            nfsum[i] = sum(nf[i-nf_win+1:i+1])
    sma20 = ind.sma([b["close"] for b in bars], 20)
    bal = bal0; peak = bal; mdd = 0.0; pos = None; trades = []
    for i in range(max(20, lo), hi):
        bar = bars[i]; c = bar["close"]
        # exit: asing distribusi (Σnf <= 0)
        if pos:
            flip = nfsum[i] is not None and nfsum[i] <= 0
            if flip:
                g = (c-pos["entry"])*pos["sh"]; net = g - FEE/100*(pos["entry"]+c)*pos["sh"]
                bal += net; peak = max(peak,bal); mdd = max(mdd,(peak-bal)/peak*100)
                trades.append({"net":net}); pos = None
        if pos: continue
        # entry: asing akumulasi mulai (Σnf cross > 0)
        if nfsum[i] is None or nfsum[i-1] is None: continue
        acc = nfsum[i] > 0 and nfsum[i-1] <= 0
        if not acc: continue
        if price_filter and not (sma20[i] == sma20[i] and c > sma20[i]): continue
        sh = int(min((bal/100)/(c*0.05), bal*0.999/c)//LOT)*LOT   # sizing: risk~ pakai 5% price band, cap kas
        if sh < LOT: continue
        pos = dict(entry=c, sh=sh)
    # exit posisi terbuka di akhir (mark to last close)
    if pos:
        c = bars[hi-1]["close"]; g = (c-pos["entry"])*pos["sh"]
        net = g - FEE/100*(pos["entry"]+c)*pos["sh"]; bal += net; trades.append({"net":net})
    wins = [t for t in trades if t["net"]>0]
    gl = -sum(t["net"] for t in trades if t["net"]<=0)
    pf = (sum(t["net"] for t in wins)/gl) if gl else (9.99 if wins else 0)
    return dict(trades=len(trades), wr=len(wins)/len(trades)*100 if trades else 0,
                ret=(bal-bal0)/bal0*100, pf=pf, dd=mdd, net=bal-bal0)


def cmd_report(args):
    syms = args.symbols.split(",") if args.symbols else BASKET
    print(f"FOREIGN-FLOW strategy 10thn (Σnet_foreign {args.nf}hr) | Rp100jt/saham | "
          f"{'+price>SMA20' if args.price_filter else 'flow saja'}")
    print(f"{'saham':7}{'trade':>6}{'WR%':>6}{'return%':>8}{'PF':>6}{'DD%':>6}{'net(Rp)':>15}")
    tot=0
    for s in syms:
        try:
            bars = stockbit_history.historical(s, args.years)
            if len(bars)<60: print(f"{s:7} data kurang"); continue
            r = backtest(bars, 0, len(bars), args.nf, args.price_filter)
            tot += r["net"]
            print(f"{s:7}{r['trades']:>6}{r['wr']:>6.0f}{r['ret']:>+8.1f}{r['pf']:>6.2f}{r['dd']:>6.1f}{r['net']:>+15,.0f}")
        except Exception as e:
            print(f"{s:7} err: {str(e)[:45]}")
    print("-"*54); print(f"{'TOTAL':7}{'':26}{tot:>+15,.0f}")


def cmd_holdout(args):
    syms = args.symbols.split(",") if args.symbols else BASKET
    print(f"FOREIGN-FLOW holdout (train60/holdout40, Σnf {args.nf}hr) | {'+price' if args.price_filter else 'flow saja'}")
    print(f"{'saham':7}|{'TRAIN ret/PF/tr':>20}|{'HOLDOUT ret/PF/tr':>22}")
    print("-"*52)
    for s in syms:
        bars = stockbit_history.historical(s, args.years); sp = int(len(bars)*0.6)
        t = backtest(bars, 0, sp, args.nf, args.price_filter); h = backtest(bars, sp, len(bars), args.nf, args.price_filter)
        print(f"{s:7}|{t['ret']:>+8.1f}/{t['pf']:.2f}/{t['trades']:>3}{'':5}|{h['ret']:>+9.1f}/{h['pf']:.2f}/{h['trades']:>3}")


# ---- COMBO: MEANREV deep-oversold + GATE foreign flow (beli dip hanya jika asing tak buang) ----
VALID16 = ["BMRI","AKRA","EXCL","BBCA","ASII","ELSA","MEDC","MAPI","ICBP","INCO",
           "TKIM","UNTR","BBRI","TLKM","ANTM","PGAS"]


def _mr_backtest(bars, I, lo, hi, foreign_gate=None, nf_win=5):
    """MEANREV deep-oversold (mfi<33 & stochD<18). foreign_gate: None | 'nonneg' | 'pos'."""
    atr=I["atr14"]; bpb=I["bb_pctb"]; rsi=I["rsi14"]; mfi=I["mfi14"]; sd=I["stoch_d"]
    nf=[b.get("net_foreign",0) for b in bars]; n=len(bars)
    nfsum=[sum(nf[max(0,i-nf_win+1):i+1]) for i in range(n)]
    bal=100_000_000; bal0=bal; pos=None; trades=[]
    for i in range(max(52,lo),hi):
        bar=bars[i]
        if pos:
            hit=None
            if bar["low"]<=pos["sl"]: hit=pos["sl"]
            elif bar["high"]>=pos["tp"]: hit=pos["tp"]
            if hit is not None:
                g=(hit-pos["entry"])*pos["sh"]; net=g-FEE/100*(pos["entry"]+hit)*pos["sh"]
                bal+=net; trades.append({"net":net}); pos=None
        if pos: continue
        a=atr[i]
        if a is None or math.isnan(a) or a<=0: continue
        if math.isnan(bpb[i]) or math.isnan(rsi[i]): continue
        if not (bpb[i]<0.15 and rsi[i]<40): continue            # sinyal MEANREV buy
        if mfi[i]>33 or sd[i]>18: continue                       # filter deep-oversold tervalidasi
        if foreign_gate=="nonneg" and nfsum[i]<0: continue       # asing tak net-jual 5hr
        if foreign_gate=="pos" and nfsum[i]<=0: continue         # asing net-beli 5hr
        entry=bar["close"]; sl_d=1.5*a; tp_d=1.5*a
        sh=int(min((bal/100)/sl_d, bal*0.999/entry)//LOT)*LOT
        if sh<LOT: continue
        pos=dict(entry=entry,sh=sh,sl=entry-sl_d,tp=entry+tp_d)
    wins=[t for t in trades if t["net"]>0]; gl=-sum(t["net"] for t in trades if t["net"]<=0)
    pf=(sum(t["net"] for t in wins)/gl) if gl else (9.99 if wins else 0)
    return dict(trades=len(trades),wr=len(wins)/len(trades)*100 if trades else 0,
                ret=(bal-bal0)/bal0*100,pf=pf,net=bal-bal0)


def cmd_combo(args):
    syms = args.symbols.split(",") if args.symbols else VALID16
    print(f"COMBO MEANREV deep-oversold + GATE FOREIGN ({args.nf}hr) | 10thn Rp100jt/saham")
    print(f"{'saham':7}|{'FILT net/PF/tr':>20}|{'+asing≥0 net/PF/tr':>24}|{'+asing>0 net/PF/tr':>24}")
    print("-"*78)
    tb=tn=tp=0
    for s in syms:
        try:
            bars=stockbit_history.historical(s,args.years); I=ind.compute(bars)
            b=_mr_backtest(bars,I,0,len(bars),None,args.nf)
            g=_mr_backtest(bars,I,0,len(bars),"nonneg",args.nf)
            p=_mr_backtest(bars,I,0,len(bars),"pos",args.nf)
            tb+=b["net"]; tn+=g["net"]; tp+=p["net"]
            print(f"{s:7}|{b['net']:>+13,.0f}/{b['pf']:.1f}/{b['trades']:>3}|"
                  f"{g['net']:>+15,.0f}/{g['pf']:.1f}/{g['trades']:>3}|{p['net']:>+15,.0f}/{p['pf']:.1f}/{p['trades']:>3}")
        except Exception as e:
            print(f"{s:7} err: {str(e)[:40]}")
    print("-"*78)
    print(f"{'TOTAL':7}|{tb:>+13,.0f}{'':9}|{tn:>+15,.0f}{'':9}|{tp:>+15,.0f}")
    print(f"\nFILT(tanpa asing) {tb:+,.0f} | +gate asing≥0 {tn:+,.0f} | +gate asing>0 {tp:+,.0f}")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in [("report", cmd_report), ("holdout", cmd_holdout), ("combo", cmd_combo)]:
        p = sub.add_parser(name); p.add_argument("--symbols"); p.add_argument("--years", type=float, default=10)
        p.add_argument("--nf", type=int, default=60); p.add_argument("--price-filter", action="store_true")
        p.set_defaults(fn=fn)
    a = ap.parse_args(); a.fn(a)


if __name__ == "__main__":
    main()
