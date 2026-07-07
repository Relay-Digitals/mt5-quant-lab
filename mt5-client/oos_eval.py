"""
oos_eval.py — Out-of-sample evaluator for the Package-2 regime-filter hypothesis
(MPBRKM1 / mp-brk-m1, XAUUSD M1, magic 770015).

Reads the FROZEN thresholds from pkg2_hypothesis.json (frozen 2026-07-02) and tests them
on trades that entered AFTER the freeze date (out-of-sample), pulled from the RAG journal
(Postgres `trades`, needs `features` snapshot + realized `net`). Reproduce in-sample with
`--since 2026-06-24`.

Decision rule per filter (indicator >= threshold): PASS if the DROPPED group is net-negative
(filter removes a losing group) AND kept win-rate >= unfiltered win-rate. Wait for >= N OOS
trades (default 20) before acting. Nothing here changes the live strategy — read-only eval.

Usage:
  ./venv/bin/python oos_eval.py                 # OOS since frozen_at
  ./venv/bin/python oos_eval.py --since 2026-06-24   # in-sample sanity
  ./venv/bin/python oos_eval.py --min 20
"""
from __future__ import annotations

import argparse
import json
import os

import journal

HERE = os.path.dirname(os.path.abspath(__file__))


def pf(nets: list[float]) -> float:
    gain = sum(n for n in nets if n > 0)
    loss = -sum(n for n in nets if n < 0)
    return gain / loss if loss > 0 else float("inf")


def wr(rows: list[dict]) -> float:
    if not rows:
        return 0.0
    w = sum(1 for r in rows if (r["net"] or 0) >= 0)
    return 100.0 * w / len(rows)


def fmt_pf(x: float) -> str:
    return "inf" if x == float("inf") else f"{x:.2f}"


def main() -> None:
    ap = argparse.ArgumentParser(description="OOS evaluator for Package-2 filters")
    ap.add_argument("--hyp", default=os.path.join(HERE, "pkg2_hypothesis.json"))
    ap.add_argument("--since", default=None, help="ISO date; default = hypothesis frozen_at (OOS)")
    ap.add_argument("--min", type=int, default=None, help="min OOS trades before verdict")
    args = ap.parse_args()

    hyp = json.load(open(args.hyp))
    frozen = hyp["frozen_at"]
    strat = hyp.get("strategy", "MPBRKM1")
    magic = hyp.get("magic", 770015)
    filters = hyp["filters"]
    min_n = args.min or hyp.get("min_oos_trades", 20)
    since = args.since or frozen
    mode = "IN-SAMPLE" if args.since and args.since < frozen else "OOS"

    with journal.conn() as c:
        rows = c.execute(
            """SELECT net, result, features, entry_time FROM trades
               WHERE (strategy=%s OR magic=%s) AND net IS NOT NULL
                 AND features IS NOT NULL AND entry_time >= %s
               ORDER BY entry_time""",
            (strat, magic, since),
        ).fetchall()

    print(f"── Package-2 OOS eval · {strat} (magic {magic}) · frozen {frozen} · mode {mode} (since {since})")
    print(f"   filters: " + ", ".join(f"{k}>={v}" for k, v in filters.items()))

    n = len(rows)
    if n == 0:
        print(f"   OOS trades with features: 0 — belum ada trade OOS terekam.")
        print(f"   → kurang {min_n} trade lagi (n=0/{min_n}). Live bot merekam fitur tiap entry; cek lagi nanti.")
        return

    nets = [r["net"] or 0.0 for r in rows]
    base_wr, base_net, base_pf = wr(rows), sum(nets), pf(nets)
    print(f"\n   UNFILTERED: n={n}  WR={base_wr:.1f}%  net=${base_net:+.2f}  PF={fmt_pf(base_pf)}")

    if n < min_n:
        print(f"   → kurang {min_n - n} trade lagi (n={n}/{min_n}). Verdict ditahan sampai sampel cukup.\n")

    print(f"\n   {'filter':<20} {'kept':>16} {'dropped':>18}  verdict")
    all_pass = True
    for ind, thr in filters.items():
        kept, dropped, missing = [], [], 0
        for r in rows:
            v = (r["features"] or {}).get(ind)
            if v is None:
                missing += 1
                continue
            (kept if v >= thr else dropped).append(r)
        if missing:
            print(f"   {ind:<20} (!) {missing} trade tanpa fitur ini — dilewati")
        k_wr, k_net = wr(kept), sum((r["net"] or 0) for r in kept)
        d_net = sum((r["net"] or 0) for r in dropped)
        passes = (len(dropped) > 0 and d_net < 0 and k_wr >= base_wr)
        all_pass = all_pass and passes
        verdict = "PASS" if passes else "FAIL"
        print(f"   {ind+'>='+str(thr):<20} "
              f"n={len(kept):>2} WR{k_wr:>4.0f}% ${k_net:>+7.0f} "
              f"| n={len(dropped):>2} ${d_net:>+7.0f} "
              f" {verdict}")

    print()
    if n < min_n:
        print(f"   VERDICT: PENDING — {n}/{min_n} OOS trades. (per-filter di atas indikatif saja)")
    elif all_pass:
        print(f"   VERDICT: ✅ PASS — semua filter valid OOS. Aman mengaktifkan gate Package-2 di mp_brk_m1.py.")
    else:
        print(f"   VERDICT: ❌ FAIL — minimal 1 filter tak lolos OOS. JANGAN aktifkan gate; jangan re-tune (overfit).")


if __name__ == "__main__":
    main()
