"""
idx_analyze.py — Analisa win/loss + filter + holdout untuk saham ID (pipeline = forex).
Capture fitur 31 indikator tiap entry → compare win vs loss → filter → holdout.

Usage:
  python3 idx_analyze.py compare                 # win/loss per indikator (MEANREV basket)
  python3 idx_analyze.py holdout --symbols BMRI,ICBP
"""
from __future__ import annotations
import argparse, math, statistics
import stockbit_history
import idx_indicators as ind

BASKET = ["BBCA","BBRI","BMRI","BBNI","TLKM","ASII","UNVR","ICBP","ADRO","ANTM"]
FEE = 0.2; LOT = 100
CMP = ["rsi14","adx14","plus_di","minus_di","stoch_k","stoch_d","cci20","willr14","mfi14",
       "bb_pctb","bb_width","dist_ema50_atr","mom10","vol_ratio","range_atr","macd_hist"]


def sig_meanrev(i, I, bars):
    bpb, r = I["bb_pctb"], I["rsi14"]
    if math.isnan(bpb[i]) or math.isnan(r[i]): return None
    if bpb[i] < 0.15 and r[i] < 40: return "buy"
    if bpb[i] > 0.85 and r[i] > 60: return "sell"
    return None


def backtest(bars, I, lo, hi, long_only=True, sl_atr=1.5, tp_atr=1.5, cap_feat=True, flt=None):
    """Backtest MEANREV pada index [lo,hi); capture fitur entry. Return (trades, balance_akhir, maxdd)."""
    atr = I["atr14"]; bal = 100_000_000; peak = bal; mdd = 0.0; pos = None; trades = []
    for i in range(max(52, lo), hi):
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
                g = (hit-pos["entry"])*pos["sh"] if pos["side"]=="buy" else (pos["entry"]-hit)*pos["sh"]
                net = g - FEE/100*(pos["entry"]+hit)*pos["sh"]; bal += net
                peak = max(peak,bal); mdd = max(mdd,(peak-bal)/peak*100)
                trades.append({"net":net,"feat":pos["feat"]}); pos = None
        if pos: continue
        a = atr[i]
        if a is None or math.isnan(a) or a <= 0: continue
        side = sig_meanrev(i, I, bars)
        if not side or (long_only and side=="sell"): continue
        if flt and flt(i, I): continue
        sl_d=sl_atr*a; tp_d=tp_atr*a; entry=bar["close"]
        sh=int(min((bal/100)/sl_d, bal*0.999/entry)//LOT)*LOT
        if sh<LOT: continue
        feat={k:I[k][i] for k in CMP if not (I[k][i] is None or math.isnan(I[k][i]))} if cap_feat else {}
        pos=dict(side=side,entry=entry,sh=sh,feat=feat,
                 sl=entry-sl_d if side=="buy" else entry+sl_d, tp=entry+tp_d if side=="buy" else entry-tp_d)
    return trades, bal, mdd


def cmd_compare(args):
    syms = args.symbols.split(",") if args.symbols else BASKET
    allt = []
    for s in syms:
        bars = stockbit_history.historical(s, args.years); I = ind.compute(bars)
        t,_,_ = backtest(bars, I, 0, len(bars), long_only=not args.both)
        allt += t
    win=[t["feat"] for t in allt if t["net"]>0]; los=[t["feat"] for t in allt if t["net"]<=0]
    print(f"COMPARE win/loss MEANREV ID | {len(syms)} saham | menang {len(win)} kalah {len(los)} | WR {len(win)/(len(win)+len(los))*100:.1f}%")
    print(f"\n  {'indikator':16}{'mean(MENANG)':>13}{'mean(KALAH)':>12}{'effect':>8}")
    res=[]
    for f in CMP:
        wv=[d[f] for d in win if f in d]; lv=[d[f] for d in los if f in d]
        if len(wv)<20 or len(lv)<20: continue
        mw,ml=statistics.mean(wv),statistics.mean(lv); sd=statistics.pstdev(wv+lv) or 1
        res.append((f,mw,ml,(mw-ml)/sd))
    for f,mw,ml,e in sorted(res,key=lambda x:abs(x[3]),reverse=True):
        print(f"  {f:16}{mw:>13.2f}{ml:>12.2f}{e:>+8.2f}{'  ★' if abs(e)>=0.2 else ''}")
    print("\neffect = (menang-kalah)/std. |effect|≥0,2 (★) = paling membedakan.")


def _stats(trades, bal0=100_000_000):
    bal = bal0 + sum(t["net"] for t in trades)
    wins = [t for t in trades if t["net"] > 0]
    gl = -sum(t["net"] for t in trades if t["net"] <= 0)
    pf = (sum(t["net"] for t in wins)/gl) if gl else (9.99 if wins else 0)
    return (bal-bal0)/bal0*100, pf, len(trades)


# filter data-driven: wajib oversold lebih dalam (buang loser shallow-oversold)
def _flt_deep(i, I):
    mfi, sd = I["mfi14"][i], I["stoch_d"][i]
    if mfi is not None and not math.isnan(mfi) and mfi > 33: return True
    if sd is not None and not math.isnan(sd) and sd > 18: return True
    return False


def cmd_holdout(args):
    syms = args.symbols.split(",") if args.symbols else ["BMRI","ICBP","BBCA","UNVR"]
    print(f"HOLDOUT MEANREV ID (train60/holdout40) | base vs FILTER(deep-oversold mfi<33&stochD<18)")
    print(f"{'saham':7}{'varian':6}|{'TRAIN ret/PF/tr':>20}|{'HOLDOUT ret/PF/tr':>22}")
    print("-"*56)
    for s in syms:
        bars = stockbit_history.historical(s, args.years); I = ind.compute(bars); sp = int(len(bars)*0.6)
        for lbl, flt in [("base", None), ("FILT", _flt_deep)]:
            tt,_,_ = backtest(bars, I, 0, sp, flt=flt); ht,_,_ = backtest(bars, I, sp, len(bars), flt=flt)
            rt = _stats(tt); rh = _stats(ht)
            print(f"{s:7}{lbl:6}|{rt[0]:>+8.1f}/{rt[1]:.2f}/{rt[2]:>3}{'':5}|{rh[0]:>+9.1f}/{rh[1]:.2f}/{rh[2]:>3}")
    print("\nEdge nyata jika HOLDOUT FILT >= base & profit. Holdout<<train = overfit/regime.")


def cmd_report(args):
    syms = args.symbols.split(",") if args.symbols else BASKET
    print(f"REPORT PROFIT MEANREV 10thn (modal Rp100jt/saham, long-only) | base vs FILTER deep-oversold")
    print(f"{'saham':7}|{'BASE: net Rp':>16}{'ret%':>7}{'PF':>5}{'tr':>4}|{'FILT: net Rp':>16}{'ret%':>7}{'PF':>5}{'tr':>4}")
    print("-"*78)
    tot_b=tot_f=0
    for s in syms:
        bars=stockbit_history.historical(s,args.years); I=ind.compute(bars)
        tb,_,ddb=backtest(bars,I,0,len(bars))
        tf,_,ddf=backtest(bars,I,0,len(bars),flt=_flt_deep)
        rb=_stats(tb); rf=_stats(tf)
        nb=sum(t["net"] for t in tb); nf=sum(t["net"] for t in tf); tot_b+=nb; tot_f+=nf
        print(f"{s:7}|{nb:>+16,.0f}{rb[0]:>+7.1f}{rb[1]:>5.2f}{rb[2]:>4}|{nf:>+16,.0f}{rf[0]:>+7.1f}{rf[1]:>5.2f}{rf[2]:>4}")
    print("-"*78)
    print(f"{'TOTAL':7}|{tot_b:>+16,.0f}{'':19}|{tot_f:>+16,.0f}")
    print(f"\nFilter deep-oversold: total {tot_b:+,.0f} → {tot_f:+,.0f} Rp (selisih {tot_f-tot_b:+,.0f}).")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    rp = sub.add_parser("report"); rp.add_argument("--symbols"); rp.add_argument("--years", type=float, default=10); rp.set_defaults(fn=cmd_report)
    c = sub.add_parser("compare"); c.add_argument("--symbols"); c.add_argument("--years", type=float, default=10)
    c.add_argument("--both", action="store_true"); c.set_defaults(fn=cmd_compare)
    h = sub.add_parser("holdout"); h.add_argument("--symbols"); h.add_argument("--years", type=float, default=10)
    h.set_defaults(fn=cmd_holdout)
    a = ap.parse_args(); a.fn(a)


if __name__ == "__main__":
    main()
