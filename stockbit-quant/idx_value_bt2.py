"""
idx_value_bt2.py — VALUE lanjutan: + DIVIDEN (total return) + QUALITY filter (anti value-trap).
Point-in-time, anti-lookahead (NI thn lalu), anti-split (EY=NI/mcap). Rebalance tahunan top-K.
Quality = laba positif 3thn beruntun & tidak ambruk (NI(Y-1) ≥ 0.7×NI(Y-3)).
Total return = capital gain + dividen yg ex-date-nya jatuh dlm periode tahan.

Bandingkan: VALUE(harga) · VALUE(+dividen) · QUALITY-VALUE(+dividen) vs IHSG.
Usage: python3 idx_value_bt2.py [--topk 10]
"""
from __future__ import annotations
import argparse, bisect, re, requests
import stockbit_history as H

LQ45 = ["BBCA","BBRI","BMRI","BBNI","BRIS","BBTN","ARTO","TLKM","EXCL","ISAT","TOWR",
        "ASII","UNTR","ADRO","PTBA","ITMG","HRUM","ANTM","INCO","MDKA","TINS","MEDC",
        "PGAS","AKRA","ELSA","SMGR","INTP","INKP","TKIM","BRPT","ESSA","UNVR","ICBP",
        "INDF","MYOR","KLBF","SIDO","CPIN","JPFA","AMRT","ACES","MAPI","JSMR","TPIA"]
BAL0 = 100_000_000
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


def ni_annual(sym, tok):
    r = requests.get(f"https://exodus.stockbit.com/findata-view/v2/financials/{sym}", headers=H._headers(tok),
                     params={"data_type": 1, "report_type": 1, "statement_type": 2, "is_percentage": "false"}, timeout=20)
    if r.status_code != 200: return {}
    d = r.json().get("data", {}); years = [int(p.split()[-1]) for p in d.get("data_tables", {}).get("periods", [])]
    found = {}
    def w(accs):
        for a in accs:
            nm = _clean(a.get("name"))
            if nm in _NI and a.get("values"): found.setdefault(nm, a["values"])
            w(a.get("accounts", []))
    w(d.get("data_tables", {}).get("accounts", []))
    vals = next((found[k] for k in _NI if k in found), None)
    return {y: pbig(v) for y, v in zip(years, vals)} if vals else {}


def div_annual(sym, tok):
    """{tahun -> total dividen Rp/lembar} dari corpaction (by ex-date)."""
    r = requests.get("https://exodus.stockbit.com/corpaction/dividend", headers=H._headers(tok),
                     params={"symbol": sym}, timeout=20)
    out = {}
    if r.status_code != 200: return out
    for dv in r.json().get("data", {}).get("dividend", []):
        ex = dv.get("dividend_exdate", ""); val = pbig(dv.get("dividend_value"))
        if ex and val: y = int(ex[:4]); out[y] = out.get(y, 0) + val
    return out


def idx_at(dts, t):
    i = bisect.bisect_left(dts, t); return i if i < len(dts) else None


def quality_ok(nis, yp):
    """laba positif 3thn beruntun & tidak ambruk."""
    vals = [nis.get(yp), nis.get(yp - 1), nis.get(yp - 2)]
    if any(v is None or v <= 0 for v in vals): return False
    return nis.get(yp) >= 0.7 * nis.get(yp - 2)


def run(px, ni, div, mcap, rebals, topk, quality=False, use_div=False):
    bal = BAL0; hist = []
    for k in range(len(rebals) - 1):
        t0, t1 = rebals[k], rebals[k + 1]; yp = int(t0[:4]) - 1
        cand = []
        for s in px:
            if mcap.get(s) is None: continue
            nirec = ni.get(s, {}).get(yp)
            if nirec is None or nirec <= 0: continue
            if quality and not quality_ok(ni.get(s, {}), yp): continue
            dts, cls = px[s]; i0 = idx_at(dts, t0)
            if i0 is None: continue
            ey = nirec / (mcap[s] * cls[i0] / cls[-1])
            cand.append((ey, s, cls[i0], i0))
        cand.sort(reverse=True); picks = cand[:topk]
        rets = []
        for ey, s, p0, i0 in picks:
            dts, cls = px[s]; i1 = idx_at(dts, t1)
            if i1 is None: continue
            r = cls[i1] / p0 - 1
            if use_div:
                dy = sum(v for y, v in div.get(s, {}).items() if int(t0[:4]) <= y < int(t1[:4]))
                r += dy / p0
            rets.append(r)
        yr = sum(rets) / len(rets) if rets else 0; bal *= (1 + yr)
        hist.append((t0[:4], yr * 100, bal, [s for _, s, _, _ in picks]))
    return bal, hist


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--topk", type=int, default=10); a = ap.parse_args()
    tok = H._read_env()["STOCKBIT_ACCESS_TOKEN"]
    print(f"Memuat {len(LQ45)} saham (harga+laba+dividen) + IHSG...")
    px = {}; ni = {}; div = {}; mcap = {}
    for s in LQ45:
        try:
            b = H.historical(s, 10)
            if len(b) < 200: continue
            px[s] = ([x["date"] for x in b], [x["close"] for x in b])
            ni[s] = ni_annual(s, tok); div[s] = div_annual(s, tok)
            mc = requests.get(f"https://exodus.stockbit.com/keystats/ratio/v1/{s}", headers=H._headers(tok), timeout=15).json().get("data", {}).get("stats", {}).get("market_cap")
            mcap[s] = pbig(mc) * 1e9 if mc else None
        except Exception as e:
            print(f"  ! {s}: {str(e)[:40]}")
    ihb = H.historical("IHSG", 10); ihd = [x["date"] for x in ihb]; ihc = [x["close"] for x in ihb]
    rebals = [f"{y}-05-02" for y in range(2017, 2027)]; n = len(rebals) - 1

    V = {"VALUE harga": dict(quality=False, use_div=False),
         "VALUE +dividen": dict(quality=False, use_div=True),
         "QUALITY-VALUE +div": dict(quality=True, use_div=True)}
    res = {nm: run(px, ni, div, mcap, rebals, a.topk, **kw) for nm, kw in V.items()}
    ih = BAL0; ihh = []
    for k in range(n):
        i0 = idx_at(ihd, rebals[k]); i1 = idx_at(ihd, rebals[k + 1])
        r = (ihc[i1] / ihc[i0] - 1) if i0 is not None and i1 is not None else 0
        ih *= (1 + r); ihh.append(r * 100)

    print(f"\n{'='*94}\nVALUE + DIVIDEN + QUALITY (top-{a.topk}, rebalance tahunan, point-in-time) vs IHSG\n{'='*94}")
    print(f"{'thn':5}" + "".join(f"{nm:>20}" for nm in V) + f"{'IHSG':>9}")
    print("-" * 94)
    for k in range(n):
        print(f"{res['VALUE harga'][1][k][0]:5}" + "".join(f"{res[nm][1][k][1]:>+19.1f}%" for nm in V) + f"{ihh[k]:>+8.1f}%")
    print("-" * 94)
    print(f"{'×':5}" + "".join(f"{res[nm][0]/BAL0:>19.2f}x" for nm in V) + f"{ih/BAL0:>8.2f}x")
    print(f"{'CAGR':5}" + "".join(f"{((res[nm][0]/BAL0)**(1/n)-1)*100:>+17.1f}%/t" for nm in V) + f"{((ih/BAL0)**(1/n)-1)*100:>+6.1f}%")
    print("\nQuality = laba+ 3thn beruntun & NI(thn lalu)≥0.7×NI(3thn lalu). Dividen by ex-date dlm periode tahan.")
    print("Catatan: IHSG = harga saja (dividen indeks ~+2.5%/th tak dihitung); strategi dividen jauh lebih tinggi.")


if __name__ == "__main__":
    main()
