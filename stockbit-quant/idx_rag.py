"""
idx_rag.py — Simpan report paper-trade IDX ke RAG (TimescaleDB + Meilisearch di CT 108).
TERPISAH dari forex: tabel `idx_paper_trades`, index Meili `idx_paper_trades`.
Reuse kredensial PG*/MEILI* dari /opt/mt5-quant/.env (atau /opt/idx-quant/.env).

API: log_trade(rec)  -> insert PG + index Meili (keduanya best-effort, tak pernah ganggu scanner).
     reindex_all()    -> rebuild index Meili dari tabel PG.
     search(q, k)     -> cari semantik report.
"""
from __future__ import annotations
import os, datetime as dt

INDEX = "idx_paper_trades"
TABLE = "idx_paper_trades"
_ENV_CANDIDATES = ["/opt/idx-quant/.env", "/opt/mt5-quant/.env",
                   os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")]


def _load_env():
    for path in _ENV_CANDIDATES:
        if os.path.exists(path):
            for line in open(path):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


_load_env()

SCHEMA = """
CREATE TABLE IF NOT EXISTS idx_paper_trades (
    id          TEXT PRIMARY KEY,
    ts          TIMESTAMPTZ NOT NULL DEFAULT now(),
    trade_date  DATE,
    action      TEXT, symbol TEXT, method TEXT,
    price       DOUBLE PRECISION, shares INTEGER, value DOUBLE PRECISION,
    net         DOUBLE PRECISION, sl DOUBLE PRECISION, tp DOUBLE PRECISION,
    equity      DOUBLE PRECISION, return_pct DOUBLE PRECISION, dd_pct DOUBLE PRECISION,
    reason      TEXT, features JSONB
);
CREATE INDEX IF NOT EXISTS ix_idxpt_sym    ON idx_paper_trades(symbol);
CREATE INDEX IF NOT EXISTS ix_idxpt_method ON idx_paper_trades(method);
CREATE INDEX IF NOT EXISTS ix_idxpt_date   ON idx_paper_trades(trade_date);
"""


def _pg():
    import psycopg
    from psycopg.rows import dict_row
    return psycopg.connect(row_factory=dict_row)   # pakai env PG* (libpq)


def _meili_base(): return os.getenv("MEILI_URL", "http://localhost:7700").rstrip("/")
def _meili_hdr():
    k = os.getenv("MEILI_KEY", "")
    return {"Authorization": f"Bearer {k}"} if k else {}


def init_db():
    with _pg() as c:
        c.execute(SCHEMA); c.commit()


def ensure_index():
    import requests
    b = _meili_base()
    requests.post(f"{b}/indexes", headers=_meili_hdr(),
                  json={"uid": INDEX, "primaryKey": "id"}, timeout=15)
    requests.patch(f"{b}/indexes/{INDEX}/settings", headers=_meili_hdr(), json={
        "searchableAttributes": ["text", "symbol", "method", "action", "reason"],
        "filterableAttributes": ["symbol", "method", "action", "trade_date"],
        "sortableAttributes": ["net", "return_pct", "ts_epoch"],
    }, timeout=15)


def rec_to_text(r: dict) -> str:
    base = (f"Paper-trade IDX {r['trade_date']}: {r['action']} {r['symbol']} "
            f"({r['method']}) {r['shares']} lembar @ Rp{r['price']:,.0f}. {r.get('reason','')}.")
    if r['action'] == "SELL" and r.get('net') is not None:
        base += f" Hasil net Rp{r['net']:+,.0f}."
    if r.get('sl'):
        base += f" SL Rp{r['sl']:,.0f} TP Rp{r['tp']:,.0f}."
    base += (f" Equity portofolio Rp{r.get('equity',0):,.0f} "
             f"return {r.get('return_pct',0):+.1f}% drawdown {r.get('dd_pct',0):.1f}%.")
    return base


def log_trade(r: dict):
    """Simpan 1 aksi paper-trade ke PG + Meili. Best-effort: error di-print, tak raise."""
    ok = []
    # --- TimescaleDB ---
    try:
        init_db()
        with _pg() as c:
            c.execute("""INSERT INTO idx_paper_trades
                (id,trade_date,action,symbol,method,price,shares,value,net,sl,tp,
                 equity,return_pct,dd_pct,reason,features)
                VALUES (%(id)s,%(trade_date)s,%(action)s,%(symbol)s,%(method)s,%(price)s,
                 %(shares)s,%(value)s,%(net)s,%(sl)s,%(tp)s,%(equity)s,%(return_pct)s,
                 %(dd_pct)s,%(reason)s,%(features)s)
                ON CONFLICT (id) DO UPDATE SET price=EXCLUDED.price, shares=EXCLUDED.shares,
                 value=EXCLUDED.value, net=EXCLUDED.net, sl=EXCLUDED.sl, tp=EXCLUDED.tp,
                 equity=EXCLUDED.equity, return_pct=EXCLUDED.return_pct, dd_pct=EXCLUDED.dd_pct,
                 reason=EXCLUDED.reason""",
                {**r, "features": __import__("json").dumps(r.get("features") or {})})
            c.commit()
        ok.append("PG")
    except Exception as e:
        print(f"[idx_rag] PG gagal: {str(e)[:80]}")
    # --- Meilisearch ---
    try:
        import requests
        ensure_index()
        ep = int(dt.datetime.now().timestamp())
        doc = {**{k: r.get(k) for k in ("id","trade_date","action","symbol","method",
                "price","shares","value","net","sl","tp","equity","return_pct","dd_pct","reason")},
               "trade_date": str(r["trade_date"]), "ts_epoch": ep, "text": rec_to_text(r)}
        requests.post(f"{_meili_base()}/indexes/{INDEX}/documents", headers=_meili_hdr(),
                      json=[doc], timeout=15)
        ok.append("Meili")
    except Exception as e:
        print(f"[idx_rag] Meili gagal: {str(e)[:80]}")
    if ok:
        print(f"[idx_rag] report tersimpan ke {'+'.join(ok)}: {r['action']} {r['symbol']}")


FUND_INDEX = "idx_fundamental"
FUND_TABLE = "idx_fundamental_screen"
FUND_SCHEMA = """
CREATE TABLE IF NOT EXISTS idx_fundamental_screen (
    id          TEXT PRIMARY KEY,
    scan_date   DATE, rank INTEGER, symbol TEXT, score DOUBLE PRECISION,
    per DOUBLE PRECISION, pbv DOUBLE PRECISION, roe DOUBLE PRECISION,
    npm DOUBLE PRECISION, ni_growth DOUBLE PRECISION, div_yield DOUBLE PRECISION,
    is_bank BOOLEAN, ts TIMESTAMPTZ NOT NULL DEFAULT now(),
    value_rank INTEGER, action TEXT, entry_price DOUBLE PRECISION, stop_price DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS ix_idxfs_date ON idx_fundamental_screen(scan_date);
CREATE INDEX IF NOT EXISTS ix_idxfs_sym  ON idx_fundamental_screen(symbol);
ALTER TABLE idx_fundamental_screen ADD COLUMN IF NOT EXISTS value_rank INTEGER;
ALTER TABLE idx_fundamental_screen ADD COLUMN IF NOT EXISTS action TEXT;
ALTER TABLE idx_fundamental_screen ADD COLUMN IF NOT EXISTS entry_price DOUBLE PRECISION;
ALTER TABLE idx_fundamental_screen ADD COLUMN IF NOT EXISTS stop_price DOUBLE PRECISION;
"""


def log_fundamental(records: list, scan_date: str):
    """Simpan ranking screener fundamental ke PG + Meili (best-effort).
    records boleh punya: value_rank, action(BUY/WATCH), entry_price, stop_price."""
    ok = []
    try:
        with _pg() as c:
            c.execute(FUND_SCHEMA)
            for r in records:
                c.execute("""INSERT INTO idx_fundamental_screen
                    (id,scan_date,rank,symbol,score,per,pbv,roe,npm,ni_growth,div_yield,is_bank,
                     value_rank,action,entry_price,stop_price)
                    VALUES (%(id)s,%(scan_date)s,%(rank)s,%(symbol)s,%(score)s,%(per)s,%(pbv)s,
                     %(roe)s,%(npm)s,%(ni_growth)s,%(div_yield)s,%(is_bank)s,
                     %(value_rank)s,%(action)s,%(entry_price)s,%(stop_price)s)
                    ON CONFLICT (id) DO UPDATE SET rank=EXCLUDED.rank, score=EXCLUDED.score,
                     per=EXCLUDED.per, pbv=EXCLUDED.pbv, roe=EXCLUDED.roe, div_yield=EXCLUDED.div_yield,
                     value_rank=EXCLUDED.value_rank, action=EXCLUDED.action,
                     entry_price=EXCLUDED.entry_price, stop_price=EXCLUDED.stop_price""",
                    {**{"value_rank": None, "action": None, "entry_price": None, "stop_price": None}, **r,
                     "scan_date": scan_date})
            c.commit()
        ok.append("PG")
    except Exception as e:
        print(f"[idx_rag] fund PG gagal: {str(e)[:80]}")
    try:
        import requests
        b = _meili_base()
        requests.post(f"{b}/indexes", headers=_meili_hdr(), json={"uid": FUND_INDEX, "primaryKey": "id"}, timeout=15)
        requests.patch(f"{b}/indexes/{FUND_INDEX}/settings", headers=_meili_hdr(),
                       json={"searchableAttributes": ["text", "symbol"],
                             "filterableAttributes": ["symbol", "scan_date", "is_bank"],
                             "sortableAttributes": ["rank", "score", "div_yield"]}, timeout=15)
        docs = [{**r, "scan_date": str(scan_date),
                 "text": f"Screener fundamental {scan_date} {r['symbol']}: "
                         f"{(r.get('action') or 'rank')+' value#'+str(r['value_rank']) if r.get('action') else 'skor '+format(r['score'],'.1f')}, "
                         f"PER {r['per']}, div yield {r['div_yield']}%"
                         + (f", entry Rp{r['entry_price']:,.0f} stop Rp{r['stop_price']:,.0f} (-20%)" if r.get('entry_price') else "") + "."}
                for r in records]
        requests.post(f"{b}/indexes/{FUND_INDEX}/documents", headers=_meili_hdr(), json=docs, timeout=20)
        ok.append("Meili")
    except Exception as e:
        print(f"[idx_rag] fund Meili gagal: {str(e)[:80]}")
    if ok: print(f"[idx_rag] screener fundamental ({len(records)} saham) tersimpan ke {'+'.join(ok)}")


SCAN_INDEX = "idx_signal_scan"
SCAN_SCHEMA = """
CREATE TABLE IF NOT EXISTS idx_signal_scan (
    id          TEXT PRIMARY KEY, scan_date DATE, symbol TEXT, close DOUBLE PRECISION,
    mr BOOLEAN, fx BOOLEAN, per DOUBLE PRECISION, value_rank INTEGER,
    is_buy BOOLEAN, is_confluence BOOLEAN, ts TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_idxss_date ON idx_signal_scan(scan_date);
"""


def log_scan(records: list, scan_date: str):
    """Simpan snapshot scan sinyal (TA+value) ke PG + Meili (best-effort)."""
    ok = []
    try:
        with _pg() as c:
            c.execute(SCAN_SCHEMA)
            for r in records:
                c.execute("""INSERT INTO idx_signal_scan
                    (id,scan_date,symbol,close,mr,fx,per,value_rank,is_buy,is_confluence)
                    VALUES (%(id)s,%(scan_date)s,%(symbol)s,%(close)s,%(mr)s,%(fx)s,%(per)s,
                     %(value_rank)s,%(is_buy)s,%(is_confluence)s)
                    ON CONFLICT (id) DO UPDATE SET mr=EXCLUDED.mr, fx=EXCLUDED.fx, per=EXCLUDED.per,
                     value_rank=EXCLUDED.value_rank, is_buy=EXCLUDED.is_buy, is_confluence=EXCLUDED.is_confluence,
                     close=EXCLUDED.close""", {**r, "scan_date": scan_date})
            c.commit()
        ok.append("PG")
    except Exception as e:
        print(f"[idx_rag] scan PG gagal: {str(e)[:80]}")
    try:
        import requests
        b = _meili_base()
        requests.post(f"{b}/indexes", headers=_meili_hdr(), json={"uid": SCAN_INDEX, "primaryKey": "id"}, timeout=15)
        requests.patch(f"{b}/indexes/{SCAN_INDEX}/settings", headers=_meili_hdr(),
                       json={"searchableAttributes": ["text", "symbol"],
                             "filterableAttributes": ["symbol", "scan_date", "mr", "fx", "is_buy", "is_confluence"]}, timeout=15)
        docs = [{**r, "scan_date": str(scan_date),
                 "text": f"Scan {scan_date} {r['symbol']} harga {r['close']:,.0f}: "
                         f"{'MEANREV-oversold ' if r['mr'] else ''}{'FOREIGN-cross ' if r['fx'] else ''}"
                         f"{'VALUE-BUY#'+str(r['value_rank']) if r['is_buy'] else ''}"
                         f"{' KONFLUENSI' if r['is_confluence'] else ''}".strip() or "tanpa sinyal"}
                for r in records]
        requests.post(f"{b}/indexes/{SCAN_INDEX}/documents", headers=_meili_hdr(), json=docs, timeout=20)
        ok.append("Meili")
    except Exception as e:
        print(f"[idx_rag] scan Meili gagal: {str(e)[:80]}")
    if ok: print(f"[idx_rag] snapshot scan {scan_date} ({len(records)} saham) tersimpan ke {'+'.join(ok)}")


def search(q: str, k: int = 5):
    import requests
    r = requests.post(f"{_meili_base()}/indexes/{INDEX}/search", headers=_meili_hdr(),
                      json={"q": q, "limit": k}, timeout=15)
    return [h["text"] for h in r.json().get("hits", [])]


def reindex_all() -> int:
    ensure_index()
    import requests
    with _pg() as c:
        rows = c.execute("SELECT * FROM idx_paper_trades").fetchall()
    docs = []
    for r in rows:
        ep = int(r["ts"].timestamp()) if r.get("ts") else 0
        docs.append({**{k: r[k] for k in ("id","action","symbol","method","price","shares",
                     "value","net","sl","tp","equity","return_pct","dd_pct","reason")},
                     "trade_date": str(r["trade_date"]), "ts_epoch": ep, "text": rec_to_text(r)})
    if docs:
        requests.post(f"{_meili_base()}/indexes/{INDEX}/documents", headers=_meili_hdr(),
                      json=docs, timeout=30)
    return len(docs)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "reindex":
        print("reindexed", reindex_all(), "docs")
    elif len(sys.argv) > 2 and sys.argv[1] == "search":
        for t in search(sys.argv[2]): print("•", t)
    else:
        print("usage: idx_rag.py reindex | search <query>")
