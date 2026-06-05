#!/usr/bin/env python3
"""snapshot.py — precompute data dashboard via bridge (Claude) lalu cache ke state/snap_*.json.
Dijalankan systemd timer tiap ~15 menit. App ambil hasilnya instan via GET /v1/cache/<name>.
Memindahkan latensi Claude (2-4 mnt) ke background; app tak nunggu."""
import os, json, re, time
import requests

DIR = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(DIR, "state")
B = "http://localhost:8090"
TOK = open(os.path.join(DIR, ".env")).read().split("DEVICE_TOKENS=phone:")[1].split()[0].strip()
H = {"Authorization": "Bearer " + TOK}

PROMPTS = {
"home": (
 "TUGAS: Ringkasan portfolio dashboard. HANYA blok JSON "
 '{"balance":<usd>,"currency":"USD","pnlToday":<%>,"pnl30":<%>,"winRate":<int>,"openPositions":<int>,'
 '"equity":[~30 float],"allocation":[{"name":"","pct":<int>}],"activity":[{"kind":"win|loss|signal","txt":"","t":""}],'
 '"signals":[{"pair":"","dir":"LONG","entry":0,"roi":0,"status":"active","market":"forex","strat":"","type":"position"}],"source":"live"}. '
 "Sumber: MT5 API http://192.168.0.111:8000 (/api/account,/api/positions,/api/deals) + /opt/idx-quant/data/ara_paper.json. Angka nyata. HANYA ```json```."),
"signals": (
 "TUGAS: sinyal trading + verdict. HANYA blok JSON {\"signals\":[{\"pair\":\"\",\"dir\":\"LONG|SHORT\",\"entry\":0,\"roi\":0,"
 "\"status\":\"active|candidate\",\"market\":\"forex|idx\",\"strat\":\"\",\"type\":\"position|ara\",\"note\":\"\",\"verdict\":\"green|amber|red|\"}],\"source\":\"live\"}. "
 "A. POSISI: forex MT5 API http://192.168.0.111:8000 /api/positions (magic 770003 TREND,770004 MEANREV) + IDX ara_paper.json open (verdict ''). "
 "B. KANDIDAT ARA (type ara): stockbit_history movers TOP_GAINER, ticker 4-huruf naik>=15% value>=Rp10M (maks 5); tiap satu jalankan idx_ara_validate.py <CODE> -> verdict green/amber/red + note alasan. Angka nyata. HANYA ```json```."),
"forward_forex": (
 "TUGAS: forward-test FOREX. HANYA blok JSON {\"balance\":<usd>,\"currency\":\"USD\",\"equity\":[],\"openPnlPct\":<%>,\"winRate\":<int>,"
 "\"positions\":[{\"sym\":\"\",\"side\":\"LONG|SHORT\",\"qty\":\"\",\"entry\":0,\"mark\":0,\"pnlPct\":0}],\"feed\":[],\"source\":\"mt5-live\"}. "
 "Sumber MT5 API http://192.168.0.111:8000 /api/account + /api/positions. Angka nyata. HANYA ```json```."),
"forward_idx": (
 "TUGAS: forward-test IDX paper. HANYA blok JSON {\"balance\":<idr>,\"currency\":\"IDR\",\"equity\":[],\"openPnlPct\":<%>,\"winRate\":<int>,"
 "\"positions\":[{\"sym\":\"\",\"side\":\"LONG\",\"qty\":\"\",\"entry\":0,\"mark\":0,\"pnlPct\":0}],\"feed\":[],\"source\":\"ara-paper\"}. "
 "Sumber /opt/idx-quant/data/ara_paper.json (capital0+realized, posisi open). HANYA ```json```."),
}

def extract(text):
    m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    s = m.group(1) if m else text
    i = s.find('{');
    if i < 0: return None
    depth = 0
    for k in range(i, len(s)):
        if s[k] == '{': depth += 1
        elif s[k] == '}':
            depth -= 1
            if depth == 0: return s[i:k+1]
    return None

def run(prompt):
    sid = requests.post(f"{B}/v1/sessions", headers=H, json={}, timeout=20).json()["session_id"]
    j = requests.post(f"{B}/v1/chat", headers=H, json={"session_id": sid, "message": prompt, "role": "research"}, timeout=20).json()["job_id"]
    done = ""
    for line in requests.get(f"{B}/v1/chat/stream/{j}", headers=H, stream=True, timeout=300).iter_lines():
        if line and line.decode().startswith("data:"):
            ev = json.loads(line.decode()[5:].strip())
            if ev.get("type") == "done": done = ev.get("result", ""); break
            if ev.get("type") == "error": break
    return done

def main():
    os.makedirs(STATE, exist_ok=True)
    for name, p in PROMPTS.items():
        try:
            txt = run(p); js = extract(txt)
            if js:
                json.loads(js)  # validasi
                open(os.path.join(STATE, f"snap_{name}.json"), "w").write(js)
                print(f"[snap] {name} OK ({len(js)}B)")
            else:
                print(f"[snap] {name} no-json")
        except Exception as e:
            print(f"[snap] {name} err {str(e)[:80]}")

if __name__ == "__main__":
    main()
