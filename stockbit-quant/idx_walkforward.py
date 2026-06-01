"""
idx_walkforward.py — Uji OUT-OF-SAMPLE BERSIH (tanpa hindsight).
1) Seleksi saham HANYA pakai data TRAIN (2016→~2021, 60% awal): syarat train PF & return.
2) Bangun portofolio modal bersama HANYA dari saham terpilih itu.
3) Jalankan di HOLDOUT (2022→2026) yg TAK pernah dilihat saat seleksi → ekspektasi jujur.

Routing metode = sektor (struktural, bukan lookahead): komoditas→FOREIGN, bank/consumer→MEANREV.

Usage: python3 idx_walkforward.py [--capital 100000000] [--max-pos 15] [--pf 1.3]
"""
from __future__ import annotations
import argparse, math
import stockbit_history as H
import idx_indicators as ind
import idx_portfolio as P

FEE = 0.2; LOT = 100; NF_WIN = 60; BAL0 = 100_000_000

# kandidat luas (sektor → metode). TAK ada info holdout dipakai di sini.
FX_CAND = ["ADRO","PTBA","ITMG","HRUM","INDY","BYAN","BUMI","DOID","TOBA","ANTM","INCO",
           "TINS","MDKA","NCKL","BRMS","PSAB","MEDC","ELSA","PGAS","AKRA","ENRG","AALI",
           "LSIP","DSNG","SSMS","TAPG","SGRO"]
MR_CAND = ["BMRI","BBCA","BBRI","BBNI","BRIS","BBTN","ARTO","BJBR","ICBP","INDF","UNVR",
           "MYOR","KLBF","SIDO","CPIN","JPFA","AMRT","MAPI","ACES","TLKM","EXCL","ISAT",
           "TOWR","JSMR","ASII","UNTR","SMGR","INTP","INKP","TKIM"]


def bt(bars, I, nfsum, method, lo, hi):
    """Standalone backtest [lo,hi). Sizing tervalidasi. Return (ret%, PF, ntrade)."""
    atr = I["atr14"]; bal = BAL0; pos = None; trades = []
    for i in range(max(lo, 60), hi):
        bar = bars[i]; c = bar["close"]
        if pos:
            ex = None
            if method == "MR":
                if bar["low"] <= pos["sl"]: ex = pos["sl"]
                elif bar["high"] >= pos["tp"]: ex = pos["tp"]
            else:
                if nfsum[i] <= 0: ex = c
            if ex is not None:
                net = (ex-pos["entry"])*pos["sh"] - FEE/100*(pos["entry"]+ex)*pos["sh"]
                bal += net; trades.append(net); pos = None
        if pos: continue
        sig = False; sl = tp = sh = None
        if method == "MR":
            a = atr[i]; bpb,r,mfi,sd = I["bb_pctb"][i],I["rsi14"][i],I["mfi14"][i],I["stoch_d"][i]
            if a and not any(x is None or (isinstance(x,float) and math.isnan(x)) for x in (a,bpb,r,mfi,sd)) and a>0:
                if bpb<0.15 and r<40 and mfi<=33 and sd<=18:
                    sig=True; sl=c-1.5*a; tp=c+1.5*a; sh=int(min((bal*0.01)/(1.5*a),(bal*0.999)/c)//LOT)*LOT
        else:
            if i>=1 and nfsum[i]>0 and nfsum[i-1]<=0:
                sig=True; sh=int(min((bal/100)/(c*0.05),(bal*0.999)/c)//LOT)*LOT
        if not sig or sh<LOT or sh*c+FEE/100*c*sh>bal: continue
        pos=dict(entry=c,sh=sh,sl=sl,tp=tp)
    if pos:
        c=bars[hi-1]["close"]; net=(c-pos["entry"])*pos["sh"]-FEE/100*(pos["entry"]+c)*pos["sh"]
        bal+=net; trades.append(net)
    w=[t for t in trades if t>0]; gl=-sum(t for t in trades if t<=0)
    pf=(sum(w)/gl) if gl else (9.99 if w else 0)
    return (bal-BAL0)/BAL0*100, pf, len(trades)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capital", type=float, default=BAL0)
    ap.add_argument("--max-pos", type=float, default=15)
    ap.add_argument("--pf", type=float, default=1.3, help="ambang PF train utk lolos seleksi")
    a = ap.parse_args()

    cands = [(s,"FX") for s in FX_CAND] + [(s,"MR") for s in MR_CAND]
    print(f"Memuat {len(cands)} kandidat 10thn (lama)...")
    store = {}; all_dates = set()
    for s,m in cands:
        try:
            bars = H.historical(s,10)
            if len(bars)<200: continue
            I = ind.compute(bars)
            nf=[b.get("net_foreign",0) for b in bars]
            nfsum=[sum(nf[max(0,i-NF_WIN+1):i+1]) for i in range(len(bars))]
            store[s]=(bars,I,nfsum,{b["date"]:k for k,b in enumerate(bars)},m); all_dates|=set(b["date"] for b in bars)
        except Exception as e:
            print(f"  ! {s}: {str(e)[:40]}")
    dates=sorted(all_dates); split=dates[int(len(dates)*0.6)]
    print(f"Timeline {dates[0]}→{dates[-1]} | SPLIT {split} (train 60% / holdout 40%)")

    # ---- SELEKSI hanya dari TRAIN ----
    MIN_TR={"FX":5,"MR":10}
    selected=[]; print(f"\nSELEKSI dari TRAIN saja (syarat: ret>0 & PF≥{a.pf} & trade≥min):")
    print(f"{'saham':6}{'mtd':4}{'train_ret%':>11}{'train_PF':>9}{'tr':>4}  lolos?")
    for s,m in cands:
        if s not in store: continue
        bars,I,nfsum,d2i,_=store[s]
        spi=next((k for k,b in enumerate(bars) if b["date"]>=split), len(bars))
        ret,pf,n=bt(bars,I,nfsum,m,0,spi)
        ok = ret>0 and pf>=a.pf and n>=MIN_TR[m]
        if ok: selected.append(s)
        if ret>0 and pf>=1.0:   # tampilkan yg lumayan saja
            print(f"{s:6}{m:4}{ret:>+11.1f}{pf:>9.2f}{n:>4}  {'✅' if ok else ''}")
    print(f"\nTERPILIH dari train ({len(selected)}): {', '.join(selected)}")

    # ---- PORTOFOLIO HOLDOUT dgn saham terpilih (modal bersama) ----
    data={s:store[s] for s in selected}
    r=P.run(data,dates,split,dates[-1]+"z",a.capital,a.max_pos)
    print(f"\n{'='*70}\nHASIL HOLDOUT 2022→2026 (saham dipilih dari train, modal bersama)\n{'='*70}")
    P.report(r,a.capital,f"WALK-FORWARD HOLDOUT (cap {a.max_pos:.0f}%)")
    print(f"\nPembanding (PILIHAN dgn hindsight/14-saham): holdout +239% PF2.94 DD25.8%.")
    print("Bila walk-forward ini mendekati itu → edge NYATA & tahan tanpa hindsight.")


if __name__ == "__main__":
    main()
