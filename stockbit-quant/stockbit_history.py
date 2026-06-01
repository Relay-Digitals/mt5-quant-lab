"""
stockbit_history.py — History OHLC dalam (s/d 10+ thn) saham ID via Stockbit native
endpoint `company-price-feed/historical/summary/{symbol}` (paginasi 50/halaman, newest-first).
+ auto-refresh access token via carina auth/refresh saat expired.

Field candle: date,open,high,low,close,volume (+ foreign_buy/sell/net_foreign tersedia).
Return bar format sama dgn idx_indicators: {time,date,open,high,low,close,volume}.
"""
from __future__ import annotations
import os, datetime as dt
import requests

_DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stockbit-docs")
_ENV = os.path.join(_DOCS, "stockbit_token.env")
EXODUS = "https://exodus.stockbit.com"
CARINA = "https://carina.stockbit.com"


def _read_env() -> dict:
    d = {}
    for line in open(_ENV):
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1); d[k.strip()] = v.strip()
    return d


def _write_token(access: str, refresh: str | None = None):
    """Update STOCKBIT_ACCESS_TOKEN (+ STOCKBIT_REFRESH_TOKEN bila ada) di env file.
    PENTING: refresh token Stockbit ROTATING/single-use — tiap refresh balas pasangan BARU,
    keduanya WAJIB disimpan, kalau tidak refresh berikutnya gagal (UNAUTHORIZED)."""
    lines = open(_ENV).read().splitlines()
    out = []; seen_r = False
    for l in lines:
        if l.startswith("STOCKBIT_ACCESS_TOKEN="):
            out.append(f"STOCKBIT_ACCESS_TOKEN={access}")
        elif l.startswith("STOCKBIT_REFRESH_TOKEN=") and refresh:
            out.append(f"STOCKBIT_REFRESH_TOKEN={refresh}"); seen_r = True
        else:
            out.append(l)
    if refresh and not seen_r:
        out.append(f"STOCKBIT_REFRESH_TOKEN={refresh}")
    open(_ENV, "w").write("\n".join(out) + "\n")


def _find(j, *paths):
    """Ambil nilai string pertama dari beberapa path nested di response JSON."""
    for path in paths:
        cur = j; ok = True
        for k in path:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False; break
        if ok and isinstance(cur, str) and len(cur) > 20:
            return cur
    return None


def _headers(token: str) -> dict:
    return {"User-Agent": "okhttp/4.12.0", "Authorization": f"Bearer {token}",
            "X-AppVersion": "3.21.0", "X-Platform": "android", "Accept-Language": "id"}


def refresh_access() -> str | None:
    """Refresh access token via `POST exodus/login/refresh` dgn REFRESH TOKEN sebagai Bearer
    (terverifikasi 200, doc baris 3526). Response balas pasangan BARU (rotating) → simpan keduanya.
    Return access token baru / None."""
    env = _read_env()
    rt = env.get("STOCKBIT_REFRESH_TOKEN")
    if not rt:
        return None
    try:
        r = requests.post(f"{EXODUS}/login/refresh", headers=_headers(rt), timeout=15)
    except Exception as e:
        print(f"[stockbit] refresh error: {e}"); return None
    if r.status_code != 200:
        print(f"[stockbit] refresh HTTP {r.status_code} — refresh token mati/expired. "
              f"Login ulang via app & update STOCKBIT_ACCESS_TOKEN+REFRESH_TOKEN di stockbit_token.env.")
        return None
    try:
        j = r.json()
    except Exception:
        print("[stockbit] refresh: response non-JSON."); return None
    new_access = _find(j, ("data", "access", "token"), ("data", "access_token"),
                       ("data", "token"), ("access_token",), ("data", "accessToken"))
    new_refresh = _find(j, ("data", "refresh", "token"), ("data", "refresh_token"),
                        ("refresh_token",), ("data", "refreshToken"))
    if not new_access:
        print(f"[stockbit] refresh 200 tapi access_token tak ditemukan. keys={list(j)}"); return None
    _write_token(new_access, new_refresh)
    print(f"[stockbit] token di-refresh (login/refresh){' +refresh baru' if new_refresh else ''}.")
    return new_access


def login() -> str | None:
    """Login penuh user+password+player_id (device terdaftar → tanpa MFA, doc baris 8203).
    Fallback bila refresh chain putus. Butuh STOCKBIT_USER/PASSWORD/PLAYER_ID di env.
    Simpan access+refresh baru. Return access / None."""
    env = _read_env()
    user = env.get("STOCKBIT_USER"); pw = env.get("STOCKBIT_PASSWORD"); pid = env.get("STOCKBIT_PLAYER_ID")
    if not (user and pw and pid):
        print("[stockbit] login fallback skip — set STOCKBIT_USER/PASSWORD/PLAYER_ID di env utk auto-login."); return None
    body = {"user": user, "password": pw, "player_id": pid, "signature": ""}
    try:
        r = requests.post(f"{EXODUS}/login/v6/username", headers={
            "User-Agent": "okhttp/4.12.0", "X-AppVersion": "3.21.0", "X-Platform": "android",
            "Accept-Language": "id", "Content-Type": "application/json"}, json=body, timeout=20)
    except Exception as e:
        print(f"[stockbit] login error: {e}"); return None
    if r.status_code != 200:
        print(f"[stockbit] login HTTP {r.status_code}"); return None
    j = r.json(); d = j.get("data", {})
    if "new_device" in d:
        print("[stockbit] login minta MFA — player_id tak dikenal? login manual via app sekali."); return None
    td = (d.get("login") or {}).get("token_data") or {}
    na = (td.get("access") or {}).get("token"); nr = (td.get("refresh") or {}).get("token")
    if not na:
        print(f"[stockbit] login 200 tapi token tak ketemu: {list(d)}"); return None
    _write_token(na, nr)
    print("[stockbit] LOGIN ulang sukses (player_id terdaftar, tanpa MFA).")
    return na


def _get(url: str, params: dict, _retried=False):
    env = _read_env(); token = env.get("STOCKBIT_ACCESS_TOKEN", "")
    r = requests.get(url, headers=_headers(token), params=params, timeout=20)
    if r.status_code in (401, 403) and not _retried:
        # expired → refresh; bila refresh mati → login penuh; lalu ulang sekali
        if refresh_access() or login():
            return _get(url, params, _retried=True)
    r.raise_for_status()
    return r.json()


def historical(symbol: str, years: float = 5, max_pages: int = 80) -> list[dict]:
    """Paginasi historical OHLC sampai menutup `years` tahun. Return bar ASCENDING (lama→baru)."""
    cutoff = (dt.datetime.now() - dt.timedelta(days=int(years * 366))).strftime("%Y-%m-%d")
    rows = []; page = "1"
    url = f"{EXODUS}/company-price-feed/historical/summary/{symbol}"
    while page and page != "null" and int(page) <= max_pages:
        j = _get(url, {"period": 1, "page": page, "limit": 50})
        data = j.get("data", {}); res = data.get("result", [])
        if not res:
            break
        rows.extend(res)
        oldest = res[-1].get("date", "")
        if oldest and oldest < cutoff:
            break
        page = (data.get("paginate") or {}).get("next_page")
    # parse + ascending
    out = []
    for c in rows:
        try:
            d = dt.datetime.strptime(c["date"], "%Y-%m-%d")
            out.append({"time": int(d.timestamp()), "date": c["date"],
                        "open": float(c["open"]), "high": float(c["high"]),
                        "low": float(c["low"]), "close": float(c["close"]),
                        "volume": float(c.get("volume") or 0),
                        "value": float(c.get("value") or 0),
                        "frequency": float(c.get("frequency") or 0),
                        "net_foreign": float(c.get("net_foreign") or 0),
                        "foreign_buy": float(c.get("foreign_buy") or 0),
                        "foreign_sell": float(c.get("foreign_sell") or 0)})
        except (KeyError, ValueError, TypeError):
            continue
    out.sort(key=lambda x: x["time"])
    # dedup by date
    seen = set(); ded = []
    for b in out:
        if b["date"] not in seen:
            seen.add(b["date"]); ded.append(b)
    return ded


if __name__ == "__main__":
    import sys
    sym = sys.argv[1] if len(sys.argv) > 1 else "BBCA"
    yrs = float(sys.argv[2]) if len(sys.argv) > 2 else 5
    c = historical(sym, yrs)
    print(f"{sym}: {len(c)} candle | {c[0]['date']} → {c[-1]['date']}" if c else f"{sym}: kosong")
