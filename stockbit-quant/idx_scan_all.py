"""
idx_scan_all.py — Scan kondisi TERKINI seluruh LQ45 dgn 2 strategi sekaligus:
  TEKNIKAL: MEANREV deep-oversold (bb%b<0.15 & rsi<40 & mfi<=33 & stochD<=18)
            FOREIGN regime (Σnet_foreign 60hr cross >0)
  VALUE:    top-10 termurah (PER terendah = Earnings Yield), + stop -20%
Tampilkan saham yg punya sinyal apa pun + tandai konfluensi.
Usage: python3 idx_scan_all.py
"""
from __future__ import annotations
import math, re, sys, datetime as dt, requests
import stockbit_history as H
import idx_indicators as ind

LQ45 = ["BBCA","BBRI","BMRI","BBNI","BRIS","BBTN","ARTO","TLKM","EXCL","ISAT","TOWR",
        "ASII","UNTR","ADRO","PTBA","ITMG","HRUM","ANTM","INCO","MDKA","TINS","MEDC",
        "PGAS","AKRA","ELSA","SMGR","INTP","INKP","TKIM","BRPT","ESSA","UNVR","ICBP",
        "INDF","MYOR","KLBF","SIDO","CPIN","JPFA","AMRT","ACES","MAPI","JSMR","TPIA"]
NF_WIN = 60
_NI = ["Net Income Attributable To", "Net Income From Continuing Operations", "Net Income", "Net Profit"]
_clean = lambda n: re.sub(r"</?b>", "", n or "", flags=re.I).strip()


def pbig(s):
    if s is None: return None
    s = str(s).strip(); neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace(",", "").strip(); mult = 1
    for suf, m in (("B", 1e9), ("T", 1e12), ("M", 1e6)):
        if s.endswith(suf): mult = m; s = s[:-1].strip(); break
    try: v = float(s) * mult
    except ValueError: return None
    return -v if neg else v


def latest_ni(sym, tok):
    r = requests.get(f"https://exodus.stockbit.com/findata-view/v2/financials/{sym}", headers=H._headers(tok),
                     params={"data_type": 1, "report_type": 1, "statement_type": 2, "is_percentage": "false"}, timeout=20)
    if r.status_code != 200: return None
    d = r.json().get("data", {}); found = {}
    def w(accs):
        for a in accs:
            nm = _clean(a.get("name"))
            if nm in _NI and a.get("values"): found.setdefault(nm, a["values"])
            w(a.get("accounts", []))
    w(d.get("data_tables", {}).get("accounts", []))
    vals = next((found[k] for k in _NI if k in found), None)
    return pbig(vals[0]) if vals else None      # tahun terakhir


def main():
    tok = H._read_env()["STOCKBIT_ACCESS_TOKEN"]
    res = {}
    asof = None
    for s in LQ45:
        try:
            b = H.historical(s, 1.3)
            if len(b) < 80: continue
            asof = b[-1]["date"]
            I = ind.compute(b); i = len(b) - 1
            nf = [x.get("net_foreign", 0) for x in b]
            nf_now = sum(nf[i-NF_WIN+1:i+1]); nf_prev = sum(nf[i-NF_WIN:i])
            bpb, rsi, mfi, sd = I["bb_pctb"][i], I["rsi14"][i], I["mfi14"][i], I["stoch_d"][i]
            mr = (not any(x is None or (isinstance(x,float) and math.isnan(x)) for x in (bpb,rsi,mfi,sd))
                  and bpb < 0.15 and rsi < 40 and mfi <= 33 and sd <= 18)
            fx = nf_now > 0 and nf_prev <= 0
            ni = latest_ni(s, tok)
            mc = requests.get(f"https://exodus.stockbit.com/keystats/ratio/v1/{s}", headers=H._headers(tok), timeout=15).json().get("data", {}).get("stats", {}).get("market_cap")
            mcap = pbig(mc) if mc else None   # pbig sudah skala 'B' (×1e9)
            per = (mcap / ni) if (mcap and ni and ni > 0) else None
            res[s] = dict(close=b[-1]["close"], mr=mr, fx=fx, per=per, rsi=rsi, mfi=mfi, bpb=bpb, nf60=nf_now)
        except Exception as e:
            print(f"  ! {s}: {str(e)[:40]}")

    # value rank (PER asc, profitable)
    prof = {s: d for s, d in res.items() if d["per"] and d["per"] > 0}
    vrank = {s: i for i, (s, _) in enumerate(sorted(prof.items(), key=lambda kv: kv[1]["per"]), 1)}
    BUYN = 10

    print(f"\n{'='*88}\nSCAN LQ45 — kondisi per {asof} | TEKNIKAL (MEANREV/FOREIGN) + VALUE (top-10 termurah)\n{'='*88}")
    # 1) sinyal teknikal
    mr_hits = [s for s in res if res[s]["mr"]]; fx_hits = [s for s in res if res[s]["fx"]]
    print(f"\n[TEKNIKAL] MEANREV deep-oversold ({len(mr_hits)}): {', '.join(mr_hits) or '(tidak ada)'}")
    print(f"[TEKNIKAL] FOREIGN regime cross>0 ({len(fx_hits)}): {', '.join(fx_hits) or '(tidak ada)'}")
    # 2) value buy
    buys = [s for s in vrank if vrank[s] <= BUYN]
    buys.sort(key=lambda s: vrank[s])
    print(f"\n[VALUE] 10 termurah (BELI, equal-weight, stop -20%):")
    print(f"  {'#':>2} {'saham':6}{'PER':>7}{'harga':>9}{'stop-20%':>10}")
    for s in buys:
        d = res[s]; print(f"  {vrank[s]:>2} {s:6}{d['per']:>7.1f}{d['close']:>9,.0f}{round(d['close']*0.8):>10,.0f}")
    # 3) konfluensi
    conf = [s for s in res if (res[s]["mr"] or res[s]["fx"]) and s in buys]
    print(f"\n[KONFLUENSI] sinyal teknikal DAN value-murah: {', '.join(conf) or '(tidak ada)'}")
    print("\nCatatan: value & timing cenderung berlawanan (value beli yg turun) — konfluensi jarang & bukan syarat.")

    if "--store" in sys.argv:
        import idx_rag
        recs = [{"id": f"{asof}_{s}", "symbol": s, "close": d["close"], "mr": bool(d["mr"]),
                 "fx": bool(d["fx"]), "per": (d["per"]/1 if d["per"] else None),
                 "value_rank": vrank.get(s), "is_buy": s in buys,
                 "is_confluence": s in conf} for s, d in res.items()]
        idx_rag.log_scan(recs, asof)


if __name__ == "__main__":
    main()
