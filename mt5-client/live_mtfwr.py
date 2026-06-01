"""live_mtfwr.py — Forward test live MTF RSI+W%R (konversi mtf-wr-rsi.pine, tervalidasi holdout di GBPUSD).
H1 trigger + H4 bias + filter avoid-overbought. Rekam fitur tiap entry. Magic 770006."""
from __future__ import annotations
import argparse, time, datetime as dt
import requests
from mt5_scalper import MT5Api, calc_lot
import journal

MAGIC = 770006

def log(m): print(f"[{dt.datetime.now():%H:%M:%S}] {m}", flush=True)
def ind(api, sym, tf, count): return api._get(f"/api/symbols/{sym}/indicators", timeframe=tf, count=count, series="true")["indicators"]

def step(api, cfg, sinfo, state):
    sym=cfg["symbol"]; dg=sinfo["digits"]; pt=sinfo["point"]
    h1=ind(api,sym,"H1",300); h4=ind(api,sym,"H4",100)
    rsi=h1["rsi14"][:-1]; wr=h1["willr14"][:-1]; atr=h1["atr14"][:-1]; bbp=h1["bb_pctb"][:-1]; cci=h1["cci20"][:-1]; times=h1["time"][:-1]
    i=len(times)-1
    if i<2: return
    last_t=times[i]; br=h4["rsi14"][:-1][-1]; bw=h4["willr14"][:-1][-1]
    if state.get("last_bar")==last_t: return
    state["last_bar"]=last_t
    a=atr[i]
    cu=lambda arr,lv: arr[i-1] is not None and arr[i] is not None and arr[i-1]<=lv and arr[i]>lv
    cd=lambda arr,lv: arr[i-1] is not None and arr[i] is not None and arr[i-1]>=lv and arr[i]<lv
    buy=(br is not None and br<30 and bw<-80) and cu(rsi,30) and cu(wr,-80)
    sell=(br is not None and br>70 and bw>-20) and cd(rsi,70) and cd(wr,-20)
    side="buy" if buy else ("sell" if sell else None)
    biso=dt.datetime.fromtimestamp(last_t).strftime("%m-%d %H:%M")
    rstr=f"{rsi[i]:.0f}" if rsi[i] is not None else "?"; wstr=f"{wr[i]:.0f}" if wr[i] is not None else "?"
    bstr=f"{br:.0f}/{bw:.0f}" if br is not None else "?"
    log(f"bar {biso} | H1 rsi={rstr} wr={wstr} | H4bias {bstr} | sig={side or 'none'}")
    if not side or a is None or a<=0: return
    if cfg["avoid_ob"] and ((bbp[i] is not None and bbp[i]>0.8) or (cci[i] is not None and cci[i]>100)):
        log("   ✗ SKIP: overbought zone (filter)"); return
    if [p for p in api.positions(sym) if p.get("magic")==MAGIC]:
        log("   ✗ SKIP: sudah ada posisi MTFWR"); return
    tick=api.tick(sym); entry=tick["ask"] if side=="buy" else tick["bid"]; spr=tick["ask"]-tick["bid"]
    if spr/a*100>cfg["max_spread_pct"]: log("   ✗ SKIP: spread"); return
    sl_d=cfg["sl_atr"]*a; tp_d=cfg["tp_atr"]*a
    sl=round(entry-sl_d if side=="buy" else entry+sl_d,dg); tp=round(entry+tp_d if side=="buy" else entry-tp_d,dg)
    acc=api.account(); lot,el=calc_lot(acc["balance"]*cfg["risk"]/100,sl_d,sinfo)
    if el>acc["balance"]*cfg["max_risk"]/100: log(f"   ✗ SKIP: risk ${el:.0f}>cap"); return
    log(f"➤ {side.upper()} {sym} @ {entry:.{dg}f} SL {sl} TP {tp} lot {lot} risk ${el:.2f}")
    if not cfg["live"]: log("   [PAPER] tidak dikirim"); return
    try:
        out=api._post("/api/orders/send",dict(symbol=sym,side=side,volume=lot,sl=sl,tp=tp,deviation=20,magic=MAGIC,comment="MTFWR-FILT"))
        res=out.get("result",{}); tk=res.get("order") or res.get("deal")
        log(f"   ✓ LIVE retcode={res.get('retcode')} order={res.get('order')} price={res.get('price')}")
        if tk:
            snap={k:h1[k][:-1][i] for k in h1 if k!='time'}
            journal.log_live_entry(int(tk),strategy="MTFWR",symbol=sym,timeframe="H1",side=side,
                entry_time=dt.datetime.now().isoformat(),entry_price=res.get("price"),lot=res.get("volume"),
                sl=sl,tp=tp,magic=MAGIC,features=snap)
            log(f"   📝 fitur entry direkam (ticket {tk}, {len(snap)} indikator)")
    except Exception as e: log(f"   ✗ order GAGAL: {e}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--symbol",default="GBPUSD"); ap.add_argument("--risk",type=float,default=0.5)
    ap.add_argument("--max-risk",type=float,default=6.0); ap.add_argument("--max-spread-pct",type=float,default=12.0)
    ap.add_argument("--sl-atr",type=float,default=2.0); ap.add_argument("--tp-atr",type=float,default=2.0)
    ap.add_argument("--no-avoid-ob",action="store_true"); ap.add_argument("--poll",type=int,default=20)
    ap.add_argument("--live",action="store_true"); ap.add_argument("--once",action="store_true"); ap.add_argument("--api",default="http://192.168.0.116:8000")
    a=ap.parse_args(); api=MT5Api(a.api,timeout=30); sinfo=api.symbol_info(a.symbol); acc=api.account()
    cfg=dict(symbol=a.symbol,risk=a.risk,max_risk=a.max_risk,max_spread_pct=a.max_spread_pct,
             sl_atr=a.sl_atr,tp_atr=a.tp_atr,avoid_ob=not a.no_avoid_ob,live=a.live)
    log(f"Akun {acc['login']} bal=${acc['balance']:.2f} | MTFWR-FILT {a.symbol} H1+H4bias | SL{a.sl_atr} TP{a.tp_atr} risk{a.risk}% | magic {MAGIC} | {'LIVE' if a.live else 'PAPER'} | avoid_ob={not a.no_avoid_ob}")
    state={}
    if a.once: step(api,cfg,sinfo,state); return
    log(f"Loop {a.poll}s")
    while True:
        try: step(api,cfg,sinfo,state)
        except requests.RequestException as e: log(f"(net: {type(e).__name__})")
        except Exception as e: log(f"(err: {type(e).__name__}: {e})")
        time.sleep(a.poll)

if __name__=="__main__": main()
