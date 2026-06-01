"""
idx_indicators.py — Indikator teknikal untuk SAHAM INDONESIA (terpisah dari forex).
Metode/rumus SAMA dengan forex (Wilder smoothing dll). compute(bars) -> dict series.
bars: list dict {open,high,low,close,volume,time}.
"""
from __future__ import annotations
import math
NAN = float("nan")


def sma(v, p):
    out = [NAN] * len(v)
    if len(v) < p: return out
    s = sum(v[:p]); out[p-1] = s/p
    for i in range(p, len(v)): s += v[i]-v[i-p]; out[i] = s/p
    return out

def ema(v, p):
    out = [NAN]*len(v)
    if len(v) < p: return out
    k = 2/(p+1); seed = sum(v[:p])/p; out[p-1] = seed; prev = seed
    for i in range(p, len(v)): prev = v[i]*k+prev*(1-k); out[i] = prev
    return out

def _ema_skip(v, p):
    out = [NAN]*len(v); st = next((i for i,x in enumerate(v) if x==x), None)
    if st is None or len(v)-st < p: return out
    e = ema(v[st:], p)
    for i,x in enumerate(e): out[st+i] = x
    return out

def _rma(v, p):
    out = [NAN]*len(v)
    if len(v) < p: return out
    a = sum(v[:p])/p; out[p-1] = a
    for i in range(p, len(v)): a = (a*(p-1)+v[i])/p; out[i] = a
    return out

def rsi(close, p=14):
    n = len(close); out = [NAN]*n
    if n < p+1: return out
    g = [0.0]*n; l = [0.0]*n
    for i in range(1, n):
        d = close[i]-close[i-1]; g[i] = max(d,0); l[i] = max(-d,0)
    ag = sum(g[1:p+1])/p; al = sum(l[1:p+1])/p
    out[p] = 100-100/(1+(ag/al if al else 1e9))
    for i in range(p+1, n):
        ag = (ag*(p-1)+g[i])/p; al = (al*(p-1)+l[i])/p
        out[i] = 100.0 if al == 0 else 100-100/(1+ag/al)
    return out

def atr(bars, p=14):
    n = len(bars); tr = [0.0]*n
    for i in range(1, n):
        h,l,pc = bars[i]["high"],bars[i]["low"],bars[i-1]["close"]
        tr[i] = max(h-l, abs(h-pc), abs(l-pc))
    return _rma([0.0]+tr[1:], p) if n > 1 else [NAN]*n

def macd(close, f=12, s=26, sig=9):
    ef = ema(close,f); es = ema(close,s)
    line = [(a-b) if (a==a and b==b) else NAN for a,b in zip(ef,es)]
    sigl = _ema_skip(line, sig)
    hist = [(x-y) if (x==x and y==y) else NAN for x,y in zip(line,sigl)]
    return line, sigl, hist

def adx(bars, p=14):
    n = len(bars); pdm=[0.0]*n; mdm=[0.0]*n; tr=[0.0]*n
    for i in range(1, n):
        up = bars[i]["high"]-bars[i-1]["high"]; dn = bars[i-1]["low"]-bars[i]["low"]
        pdm[i] = up if (up>dn and up>0) else 0; mdm[i] = dn if (dn>up and dn>0) else 0
        h,l,pc = bars[i]["high"],bars[i]["low"],bars[i-1]["close"]; tr[i] = max(h-l,abs(h-pc),abs(l-pc))
    a = _rma([0.0]+tr[1:],p); ps = _rma([0.0]+pdm[1:],p); ms = _rma([0.0]+mdm[1:],p)
    pdi=[NAN]*n; mdi=[NAN]*n; dx=[NAN]*n
    for i in range(n):
        if a[i]==a[i] and a[i]:
            pdi[i] = 100*ps[i]/a[i]; mdi[i] = 100*ms[i]/a[i]; ss = pdi[i]+mdi[i]
            dx[i] = 100*abs(pdi[i]-mdi[i])/ss if ss else 0
    ad = _rma([x if x==x else 0 for x in dx], p)
    for i in range(min(2*p,n)): ad[i] = NAN
    return pdi, mdi, ad

def stoch(bars, k=14, d=3):
    n = len(bars); K=[NAN]*n
    for i in range(k-1,n):
        w = bars[i-k+1:i+1]; hh=max(b["high"] for b in w); ll=min(b["low"] for b in w)
        K[i] = 100*(bars[i]["close"]-ll)/(hh-ll) if hh>ll else 50
    return K, _ema_skip(K, d)

def cci(bars, p=20):
    n = len(bars); out=[NAN]*n; tp=[(b["high"]+b["low"]+b["close"])/3 for b in bars]
    for i in range(p-1,n):
        w = tp[i-p+1:i+1]; m = sum(w)/p; md = sum(abs(x-m) for x in w)/p
        out[i] = (tp[i]-m)/(0.015*md) if md else 0
    return out

def willr(bars, p=14):
    n = len(bars); out=[NAN]*n
    for i in range(p-1,n):
        w = bars[i-p+1:i+1]; hh=max(b["high"] for b in w); ll=min(b["low"] for b in w)
        out[i] = -100*(hh-bars[i]["close"])/(hh-ll) if hh>ll else -50
    return out

def mfi(bars, p=14):
    n = len(bars); out=[NAN]*n; tp=[(b["high"]+b["low"]+b["close"])/3 for b in bars]
    rmf=[tp[i]*bars[i].get("volume",0) for i in range(n)]
    for i in range(p,n):
        pos=neg=0
        for j in range(i-p+1,i+1):
            if tp[j]>tp[j-1]: pos+=rmf[j]
            elif tp[j]<tp[j-1]: neg+=rmf[j]
        out[i] = 100.0 if neg==0 else 100-100/(1+pos/neg)
    return out

def obv(bars):
    n=len(bars); out=[0.0]*n
    for i in range(1,n):
        v=bars[i].get("volume",0)
        out[i]=out[i-1]+v if bars[i]["close"]>bars[i-1]["close"] else (out[i-1]-v if bars[i]["close"]<bars[i-1]["close"] else out[i-1])
    return out

def bollinger(close, p=20, mult=2.0):
    mid=sma(close,p); up=[NAN]*len(close); lo=[NAN]*len(close); pb=[NAN]*len(close); wd=[NAN]*len(close)
    for i in range(p-1,len(close)):
        w=close[i-p+1:i+1]; m=mid[i]; sd=math.sqrt(sum((x-m)**2 for x in w)/p)
        up[i]=m+mult*sd; lo[i]=m-mult*sd; rng=up[i]-lo[i]
        pb[i]=(close[i]-lo[i])/rng if rng else 0.5; wd[i]=rng/m*100 if m else NAN
    return mid,up,lo,pb,wd


def compute(bars) -> dict:
    """Hitung semua indikator → dict series selaras index bar."""
    n=len(bars); close=[b["close"] for b in bars]
    rsi14=rsi(close,14); ml,ms,mh=macd(close); a14=atr(bars,14); pdi,mdi,ad=adx(bars,14)
    sk,sd=stoch(bars,14,3); cci20=cci(bars,20); wr=willr(bars,14); mf=mfi(bars,14); ob=obv(bars)
    e9=ema(close,9); e21=ema(close,21); e50=ema(close,50); s20=sma(close,20); s50=sma(close,50)
    bm,bu,bl,bpb,bw=bollinger(close,20,2.0)
    dist50=[NAN]*n; mom10=[NAN]*n; volr=[NAN]*n; rng_atr=[NAN]*n
    vsma=sma([b.get("volume",0) for b in bars],20)
    for i in range(n):
        if a14[i]==a14[i] and a14[i]:
            if e50[i]==e50[i]: dist50[i]=(close[i]-e50[i])/a14[i]
            rng_atr[i]=(bars[i]["high"]-bars[i]["low"])/a14[i]
        if i>=10: mom10[i]=close[i]-close[i-10]
        if vsma[i]==vsma[i] and vsma[i]: volr[i]=bars[i].get("volume",0)/vsma[i]
    return {"rsi14":rsi14,"macd_line":ml,"macd_signal":ms,"macd_hist":mh,"adx14":ad,"plus_di":pdi,"minus_di":mdi,
            "stoch_k":sk,"stoch_d":sd,"cci20":cci20,"willr14":wr,"mfi14":mf,"atr14":a14,"obv":ob,
            "ema9":e9,"ema21":e21,"ema50":e50,"sma20":s20,"sma50":s50,
            "bb_pctb":bpb,"bb_width":bw,"dist_ema50_atr":dist50,"mom10":mom10,"vol_ratio":volr,"range_atr":rng_atr}
