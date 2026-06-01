"""
idx_fundamental.py — Screener FUNDAMENTAL saham ID (Stockbit keystats/ratio).
Tarik rasio tiap saham LQ45 → skor komposit (Valuasi 30% + Kualitas 30% + Pertumbuhan 20% + Dividen 20%)
→ ranking. Skor berbasis PERSENTIL lintas-universe (tahan outlier). Bank ditandai (tanpa DER).

Hard filter: market cap ≥ Rp1T & PER(TTM) > 0 (profitable). Saham rugi/kecil dibuang.

Usage: python3 idx_fundamental.py [--symbols ...] [--top 20]
"""
from __future__ import annotations
import argparse, requests, statistics
import stockbit_history as H

LQ45 = ["BBCA","BBRI","BMRI","BBNI","BRIS","BBTN","ARTO","TLKM","EXCL","ISAT","TOWR",
        "ASII","UNTR","ADRO","PTBA","ITMG","HRUM","ANTM","INCO","MDKA","TINS","MEDC",
        "PGAS","AKRA","ELSA","SMGR","INTP","INKP","TKIM","BRPT","ESSA","UNVR","ICBP",
        "INDF","MYOR","KLBF","SIDO","CPIN","JPFA","AMRT","ACES","MAPI","JSMR","TPIA","BRMS"]

# metrik yg ditarik: (nama persis di keystats, arah: +1 makin tinggi makin baik / -1 sebaliknya, kategori)
METRICS = {
    "PER":      ("Current PE Ratio (TTM)",        -1, "value"),
    "PBV":      ("Current Price to Book Value",    -1, "value"),
    "EV/EBITDA":("EV to EBITDA (TTM)",             -1, "value"),
    "ROE":      ("Return on Equity (TTM)",         +1, "quality"),
    "NPM":      ("Net Profit Margin (Quarter)",    +1, "quality"),
    "NI_growth":("Net Income (Annual YoY Growth)", +1, "growth"),
    "EPS_growth":("EPS (Annual YoY Growth) ",      +1, "growth"),
    "DivYield": ("Dividend Yield",                 +1, "income"),
    "Payout":   ("Payout Ratio",                   +1, "income"),
    "DER":      ("Debt to Equity Ratio (Quarter)", -1, "info"),
}
WEIGHTS = {"value": 0.30, "quality": 0.30, "growth": 0.20, "income": 0.20}
BANKS = {"BBCA", "BBRI", "BMRI", "BBNI", "BRIS", "BBTN", "ARTO", "BJBR", "BANK"}
# winsorize: clip nilai ekstrem sebelum ranking (hindari distorsi ROE semu & growth dari basis ~nol)
CAPS = {"ROE": (None, 40.0), "NPM": (None, 60.0),
        "NI_growth": (-50.0, 100.0), "EPS_growth": (-50.0, 100.0)}


def clip(k, v):
    if v is None or k not in CAPS: return v
    lo, hi = CAPS[k]
    if lo is not None: v = max(lo, v)
    if hi is not None: v = min(hi, v)
    return v


def pnum(s):
    """Parse '702,668 B' / '22.41%' / '(46 B)' / '-' → float (None bila kosong)."""
    if s is None: return None
    s = str(s).strip()
    if s in ("-", "", "N/A"): return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace(",", "").replace("%", "").replace("B", "").strip()
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def fetch(sym, tok):
    j = requests.get(f"https://exodus.stockbit.com/keystats/ratio/v1/{sym}",
                     headers=H._headers(tok), timeout=20).json()
    d = j.get("data", {})
    flat = {}
    for grp in d.get("closure_fin_items_results", []):
        for it in grp.get("fin_name_results", []):
            fi = it.get("fitem", {})
            flat[fi.get("name")] = fi.get("value")
    out = {"mcap_b": pnum(d.get("stats", {}).get("market_cap")),
           "free_float": pnum(d.get("stats", {}).get("free_float"))}
    for key, (name, _, _) in METRICS.items():
        out[key] = pnum(flat.get(name))
    return out


def pct_rank(vals, x, direction):
    """persentil 0-100 dari x dlm vals; direction -1 = makin rendah makin baik."""
    v = [a for a in vals if a is not None]
    if not v or x is None: return 50.0   # netral bila data hilang
    below = sum(1 for a in v if a < x)
    p = below / len(v) * 100
    return p if direction == +1 else (100 - p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols"); ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--store", action="store_true", help="simpan ranking ke RAG (PG+Meili)")
    a = ap.parse_args()
    syms = a.symbols.split(",") if a.symbols else LQ45
    tok = H._read_env()["STOCKBIT_ACCESS_TOKEN"]

    data = {}
    for s in syms:
        try:
            data[s] = fetch(s, tok)
        except Exception as e:
            print(f"  ! {s}: {str(e)[:40]}")
    # hard filter
    elig = {s: d for s, d in data.items()
            if d.get("mcap_b") and d["mcap_b"] >= 1000 and d.get("PER") and d["PER"] > 0}
    dropped = [s for s in data if s not in elig]

    # kolom nilai per metrik utk persentil (sudah di-winsorize)
    cols = {k: [clip(k, elig[s].get(k)) for s in elig] for k in METRICS}
    rows = []
    for s, d in elig.items():
        catscore = {c: [] for c in WEIGHTS}
        for k, (_, direction, cat) in METRICS.items():
            if cat == "info": continue
            catscore[cat].append(pct_rank(cols[k], clip(k, d.get(k)), direction))
        cat_avg = {c: statistics.mean(v) if v else 50 for c, v in catscore.items()}
        score = sum(WEIGHTS[c] * cat_avg[c] for c in WEIGHTS)
        is_bank = s in BANKS
        rows.append((s, score, d, cat_avg, is_bank))

    rows.sort(key=lambda x: -x[1])
    print(f"\n{'='*112}\nSCREENER FUNDAMENTAL LQ45 — skor komposit (Val30/Qual30/Grow20/Div20), persentil lintas-universe")
    print(f"{len(elig)} lolos filter (mcap≥Rp1T & laba+), {len(dropped)} dibuang: {', '.join(dropped)}\n{'='*112}")
    print(f"{'#':>2} {'saham':6}{'skor':>6}{'PER':>7}{'PBV':>6}{'EV/EB':>7}{'ROE%':>7}{'NPM%':>7}{'NIgr%':>8}{'DivYld%':>8}{'DER':>6}  tipe")
    print("-" * 112)
    for i, (s, sc, d, ca, bank) in enumerate(rows[:a.top], 1):
        g = lambda k: f"{d[k]:.1f}" if d.get(k) is not None else "-"
        print(f"{i:>2} {s:6}{sc:>6.1f}{g('PER'):>7}{g('PBV'):>6}{g('EV/EBITDA'):>7}{g('ROE'):>7}{g('NPM'):>7}{g('NI_growth'):>8}{g('DivYield'):>8}{g('DER'):>6}  {'BANK' if bank else ''}")
    print("-" * 112)
    print("Skor 0-100 (makin tinggi makin menarik fundamental). Persentil: dibanding sesama LQ45 lolos filter.")
    print("Catatan: DER kosong = bank (rasio beda). Belum hitung NPL/CAR/NIM bank, & belum cek konsistensi 5thn.")

    # ---- VALUE PORTFOLIO actionable: top-10 termurah (PER terendah = Earnings Yield tertinggi) ----
    BUYN = 10
    val_ranked = sorted(elig.items(), key=lambda kv: kv[1]["PER"])   # PER asc = termurah
    buy_syms = [s for s, _ in val_ranked[:BUYN]]
    vrank = {s: i for i, (s, _) in enumerate(val_ranked, 1)}
    # harga terkini + stop -20% utk yang BUY
    import stockbit_history as _sh
    entry = {}; stop = {}
    for s in buy_syms:
        try:
            b = _sh.historical(s, 0.2)
            if b: entry[s] = b[-1]["close"]; stop[s] = round(b[-1]["close"] * 0.80)
        except Exception:
            pass
    print(f"\n{'='*70}\nVALUE PORTFOLIO ACTIONABLE — BELI 10 termurah (equal-weight ~10%/saham), STOP -20%")
    print(f"{'='*70}")
    print(f"{'#':>2} {'saham':6}{'PER':>7}{'DivYld%':>9}{'harga':>10}{'stop-20%':>11}  alok(Rp100jt)")
    for s in buy_syms:
        d = elig[s]
        e = entry.get(s); st = stop.get(s)
        print(f"{vrank[s]:>2} {s:6}{d['PER']:>7.1f}{(d.get('DivYield') or 0):>9.1f}"
              f"{(f'{e:,.0f}' if e else '-'):>10}{(f'{st:,.0f}' if st else '-'):>11}  ~Rp10.000.000")
    print("Aturan: rebalance tahunan (lepas yg keluar 10-termurah/jadi rugi) + STOP -20% intra-thn.")

    if a.store:
        import datetime as dt, idx_rag
        today = dt.date.today().isoformat()
        recs = [{"id": f"{today}_{s}", "rank": i, "symbol": s, "score": round(sc, 1),
                 "per": d.get("PER"), "pbv": d.get("PBV"), "roe": d.get("ROE"), "npm": d.get("NPM"),
                 "ni_growth": d.get("NI_growth"), "div_yield": d.get("DivYield"), "is_bank": bank,
                 "value_rank": vrank.get(s), "action": "BUY" if s in buy_syms else "WATCH",
                 "entry_price": entry.get(s), "stop_price": stop.get(s)}
                for i, (s, sc, d, ca, bank) in enumerate(rows, 1)]
        idx_rag.log_fundamental(recs, today)


if __name__ == "__main__":
    main()
