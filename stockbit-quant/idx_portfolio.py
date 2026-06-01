"""
idx_portfolio.py — Portofolio terpadu saham ID (SATU akun, modal dirotasi/compounding).
Menggabungkan 2 metode tervalidasi OOS, di-route per universe:
  - BANK/CONSUMER  -> MEANREV deep-oversold (bb<0.15 & rsi<40 & mfi<33 & stochD<18, SL/TP 1.5ATR)
  - KOMODITAS/ENERGI -> FOREIGN-FLOW regime (Σnet_foreign 60hr cross>0 masuk, <0 keluar)

Engine event-driven 1 kas bersama: tiap hari proses EXIT dulu lalu ENTRY bila kas cukup.
Sizing: risk 1%/SL utk meanrev, cap per-posisi = MAX_POS% equity, no-leverage (≤kas). Fee 0.2%/sisi, lot 100.

Usage:
  python3 idx_portfolio.py                       # full 10thn, modal Rp100jt
  python3 idx_portfolio.py --holdout             # train60/holdout40 split
  python3 idx_portfolio.py --capital 200000000 --max-pos 25
"""
from __future__ import annotations
import argparse, math
import stockbit_history
import idx_indicators as ind

# universe -> metode (DIPERLUAS: holdout-validated, screening 57 saham)
MEANREV_SYMS = ["BMRI", "BBCA", "ICBP", "ASII", "UNTR", "TKIM"]          # bank/consumer/industri
FOREIGN_SYMS = ["ADRO", "MEDC", "ANTM", "INCO", "TOBA", "TINS", "BRMS", "DSNG"]  # komoditas/energi
FEE = 0.2; LOT = 100; NF_WIN = 60


def load(sym):
    bars = stockbit_history.historical(sym, 10)
    I = ind.compute(bars)
    nf = [b.get("net_foreign", 0) for b in bars]
    nfsum = [sum(nf[max(0, i - NF_WIN + 1):i + 1]) for i in range(len(bars))]
    return bars, I, nfsum


def run(data, dates, lo_date, hi_date, capital, max_pos_frac):
    """Event-driven portfolio. data[sym]=(bars,I,nfsum,date2idx,method). dates=master sorted."""
    cash = capital; pos = {}          # sym -> dict(method,entry,sh,sl,tp)
    peak = capital; mdd = 0.0; trades = []
    eq_curve = []
    for d in dates:
        if d < lo_date or d >= hi_date:
            continue
        # ---- EXITS ----
        for sym in list(pos.keys()):
            bars, I, nfsum, d2i, method = data[sym]
            i = d2i.get(d)
            if i is None:
                continue
            bar = bars[i]; p = pos[sym]; exit_px = None
            if method == "MR":
                if bar["low"] <= p["sl"]: exit_px = p["sl"]
                elif bar["high"] >= p["tp"]: exit_px = p["tp"]
            else:  # FOREIGN regime flip
                if nfsum[i] <= 0: exit_px = bar["close"]
            if exit_px is not None:
                gross = (exit_px - p["entry"]) * p["sh"]
                net = gross - FEE / 100 * (p["entry"] + exit_px) * p["sh"]
                cash += p["sh"] * exit_px - FEE / 100 * exit_px * p["sh"]
                trades.append({"sym": sym, "method": method, "net": net})
                del pos[sym]
        # ---- ENTRIES ----
        for sym, (bars, I, nfsum, d2i, method) in data.items():
            if sym in pos:
                continue
            i = d2i.get(d)
            if i is None or i < 60:
                continue
            c = bars[i]["close"]; sig = False; sl = tp = None
            if method == "MR":
                bpb, r, mfi, sd, atr = I["bb_pctb"][i], I["rsi14"][i], I["mfi14"][i], I["stoch_d"][i], I["atr14"][i]
                if any(x is None or (isinstance(x, float) and math.isnan(x)) for x in (bpb, r, mfi, sd, atr)) or atr <= 0:
                    continue
                if bpb < 0.15 and r < 40 and mfi <= 33 and sd <= 18:
                    sig = True; sl = c - 1.5 * atr; tp = c + 1.5 * atr
                    risk_sh = (capital * 0.01) / (1.5 * atr)  # risk 1% modal awal
            else:
                if i < 1 or nfsum[i] is None or nfsum[i - 1] is None:
                    continue
                if nfsum[i] > 0 and nfsum[i - 1] <= 0:
                    sig = True
            if not sig:
                continue
            equity = cash + sum(po["sh"] * data[s][0][data[s][3][d]]["close"]
                                for s, po in pos.items() if d in data[s][3])
            cap_sh = (equity * max_pos_frac / 100) / c
            cash_sh = (cash * 0.999) / c
            cands = [cap_sh, cash_sh]
            if method == "MR":
                cands.append(risk_sh)
            sh = int(min(cands) // LOT) * LOT
            if sh < LOT:
                continue
            cost = sh * c + FEE / 100 * c * sh
            if cost > cash:
                continue
            cash -= cost
            pos[sym] = dict(method=method, entry=c, sh=sh, sl=sl, tp=tp)
        # ---- mark equity ----
        equity = cash + sum(po["sh"] * data[s][0][data[s][3][d]]["close"]
                            for s, po in pos.items() if d in data[s][3])
        peak = max(peak, equity); mdd = max(mdd, (peak - equity) / peak * 100)
        eq_curve.append((d, equity))
    # likuidasi sisa di harga terakhir
    for sym, p in list(pos.items()):
        bars = data[sym][0]; c = bars[-1]["close"]
        net = (c - p["entry"]) * p["sh"] - FEE / 100 * (p["entry"] + c) * p["sh"]
        cash += p["sh"] * c - FEE / 100 * c * p["sh"]
        trades.append({"sym": sym, "method": p["method"], "net": net})
    final_eq = cash
    return dict(trades=trades, ret=(final_eq - capital) / capital * 100, mdd=mdd,
                net=final_eq - capital, eq=eq_curve)


def report(res, capital, label):
    t = res["trades"]; wins = [x for x in t if x["net"] > 0]
    gl = -sum(x["net"] for x in t if x["net"] <= 0)
    pf = (sum(x["net"] for x in wins) / gl) if gl else (9.99 if wins else 0)
    mr = [x for x in t if x["method"] == "MR"]; fr = [x for x in t if x["method"] == "FX"]
    print(f"\n=== {label} === modal Rp{capital:,.0f}")
    print(f"  trade {len(t)} (MEANREV {len(mr)} / FOREIGN {len(fr)}) | WR {len(wins)/len(t)*100:.0f}% | PF {pf:.2f}")
    print(f"  return {res['ret']:+.1f}% | net Rp{res['net']:+,.0f} | maxDD {res['mdd']:.1f}%")
    by = {}
    for x in t:
        by.setdefault(x["sym"], 0)
        by[x["sym"]] += x["net"]
    print("  per-saham: " + " ".join(f"{s}{v/1e6:+.1f}jt" for s, v in sorted(by.items(), key=lambda z: -z[1])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capital", type=float, default=100_000_000)
    ap.add_argument("--max-pos", type=float, default=15, help="cap %% equity per posisi")
    ap.add_argument("--holdout", action="store_true")
    args = ap.parse_args()

    print(f"Memuat data 10thn ({len(MEANREV_SYMS)+len(FOREIGN_SYMS)} saham)...")
    data = {}; all_dates = set()
    for sym, m in [(s, "MR") for s in MEANREV_SYMS] + [(s, "FX") for s in FOREIGN_SYMS]:
        bars, I, nfsum = load(sym)
        d2i = {b["date"]: k for k, b in enumerate(bars)}
        data[sym] = (bars, I, nfsum, d2i, m)
        all_dates |= set(d2i.keys())
        print(f"  {sym}({m}) {len(bars)} candle")
    dates = sorted(all_dates)
    print(f"Timeline {dates[0]} -> {dates[-1]} ({len(dates)} hari)")

    if args.holdout:
        split = dates[int(len(dates) * 0.6)]
        rt = run(data, dates, dates[0], split, args.capital, args.max_pos)
        rh = run(data, dates, split, dates[-1] + "z", args.capital, args.max_pos)
        report(rt, args.capital, f"TRAIN  ({dates[0]}..{split})")
        report(rh, args.capital, f"HOLDOUT ({split}..{dates[-1]})")
        print(f"\nEdge nyata bila HOLDOUT tetap profit. Train {rt['ret']:+.1f}% / Holdout {rh['ret']:+.1f}%.")
    else:
        r = run(data, dates, dates[0], dates[-1] + "z", args.capital, args.max_pos)
        report(r, args.capital, f"PORTOFOLIO PENUH 10thn (max {args.max_pos:.0f}%/posisi)")


if __name__ == "__main__":
    main()
