"""
rag.py — Lapisan pencarian semantik via Meilisearch (tf-meilisearch), index `mt5_runs`.
Terpisah dari index app TradeForge. Full-text + typo-tolerant atas ringkasan run.

API sama: reindex_runs() & search(query,k). Dipakai analyze.py (ask/reindex).
Config dari .env (di-load journal): MEILI_URL (default http://localhost:7700), MEILI_KEY.
"""
from __future__ import annotations

import os

import requests

import journal  # memuat .env + akses runs

INDEX = "mt5_runs"


def _base():
    return os.getenv("MEILI_URL", "http://localhost:7700").rstrip("/")


def _hdr():
    key = os.getenv("MEILI_KEY", "")
    return {"Authorization": f"Bearer {key}"} if key else {}


def _ensure_index():
    requests.post(f"{_base()}/indexes", headers=_hdr(),
                  json={"uid": INDEX, "primaryKey": "id"}, timeout=15)
    requests.patch(f"{_base()}/indexes/{INDEX}/settings", headers=_hdr(), json={
        "searchableAttributes": ["text", "strategy", "symbol", "source"],
        "filterableAttributes": ["strategy", "symbol", "source", "timeframe"],
        "sortableAttributes": ["ret_pct", "win_rate", "max_dd_pct"],
    }, timeout=15)


def run_to_text(r: dict) -> str:
    return (
        f"Run {r['source']} strategi {r['strategy']} di {r['symbol']} timeframe {r['timeframe']}. "
        f"Periode {r['period_from']} sampai {r['period_to']}. "
        f"Balance {r['start_balance']:.2f} menjadi {r['end_balance']:.2f} "
        f"(return {r['ret_pct']:+.2f}%). Total {r['trades']} trade, "
        f"win {r['wins']} loss {r['losses']} (win-rate {r['win_rate']:.1f}%). "
        f"Profit factor {r['profit_factor']:.2f}, max drawdown {r['max_dd_pct']:.1f}%. "
        f"{r.get('notes') or ''}"
    )


def reindex_runs() -> int:
    journal.init()
    _ensure_index()
    with journal.conn() as c:
        runs = c.execute("SELECT * FROM runs").fetchall()
    docs = []
    for r in runs:
        docs.append({
            "id": r["run_id"], "source": r["source"], "strategy": r["strategy"],
            "symbol": r["symbol"], "timeframe": r["timeframe"],
            "ret_pct": r["ret_pct"], "win_rate": r["win_rate"],
            "max_dd_pct": r["max_dd_pct"], "text": run_to_text(r),
        })
    if docs:
        r = requests.post(f"{_base()}/indexes/{INDEX}/documents", headers=_hdr(),
                          json=docs, timeout=30)
        _wait_task(r.json().get("taskUid"))
    return len(docs)


def _wait_task(uid, timeout=30):
    """Tunggu task Meili (indexing async) sampai selesai."""
    if uid is None:
        return
    import time
    for _ in range(timeout * 2):
        st = requests.get(f"{_base()}/tasks/{uid}", headers=_hdr(), timeout=10).json()
        if st.get("status") in ("succeeded", "failed", "canceled"):
            return st.get("status")
        time.sleep(0.5)


TRADE_INDEX = "mt5_live_trades"


def reindex_trades() -> int:
    """Index trade FORWARD (live) + snapshot indikatornya ke Meili (RAG)."""
    journal.init()
    requests.post(f"{_base()}/indexes", headers=_hdr(),
                  json={"uid": TRADE_INDEX, "primaryKey": "id"}, timeout=15)
    requests.patch(f"{_base()}/indexes/{TRADE_INDEX}/settings", headers=_hdr(), json={
        "searchableAttributes": ["text", "strategy", "symbol", "result"],
        "filterableAttributes": ["strategy", "symbol", "result", "side"],
    }, timeout=15)
    with journal.conn() as c:
        rows = c.execute("""SELECT id,strategy,symbol,side,entry_time,exit_time,net,result,features
                            FROM trades WHERE source='forward'""").fetchall()
    docs = []
    for r in rows:
        f = r["features"] or {}
        feat = " ".join(f"{k}={round(v, 2)}" for k, v in f.items() if isinstance(v, (int, float)))
        txt = (f"Trade live {r['strategy']} {r['symbol']} {r['side'] or ''} masuk {r['entry_time']} "
               f"hasil {r['result'] or 'open'} net {r['net'] if r['net'] is not None else '-'}. {feat}")
        docs.append({"id": r["id"], "strategy": r["strategy"], "symbol": r["symbol"],
                     "side": r["side"], "result": r["result"] or "open", "net": r["net"], "text": txt})
    if docs:
        rr = requests.post(f"{_base()}/indexes/{TRADE_INDEX}/documents", headers=_hdr(), json=docs, timeout=30)
        _wait_task(rr.json().get("taskUid"))
    return len(docs)


def search(query: str, k: int = 5, kind: str | None = None) -> list[dict]:
    r = requests.post(f"{_base()}/indexes/{INDEX}/search", headers=_hdr(),
                      json={"q": query, "limit": k, "showRankingScore": True}, timeout=15)
    r.raise_for_status()
    hits = r.json().get("hits", [])
    return [{"score": h.get("_rankingScore", 0), "kind": "run",
             "ref_id": h.get("id"), "text": h.get("text", "")} for h in hits]


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "reindex":
        print(f"Reindexed {reindex_runs()} run ke Meilisearch index '{INDEX}'.")
    elif len(sys.argv) > 2 and sys.argv[1] == "search":
        for h in search(" ".join(sys.argv[2:])):
            print(f"[{h['score']:.3f}] {h['ref_id']}\n  {h['text'][:160]}\n")
    else:
        print("usage: python rag.py reindex | search <query>")
