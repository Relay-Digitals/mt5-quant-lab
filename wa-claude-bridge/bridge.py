"""bridge.py — jembatan ke Claude Code headless (langganan Pro/Max).
Jalankan `claude -p` per chat dgn ROLE (env) + session resume (konteks nyambung) + akses skrip quant.
Hook permguard.py (via .claude/settings.json) enforce role. Return teks jawaban Claude."""
import os, json, subprocess, time

BRIDGE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BRIDGE_DIR, "state"); os.makedirs(STATE_DIR, exist_ok=True)
QUANT_DIRS = ["/opt/idx-quant", "/opt/mt5-quant"]
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")   # hemat; ganti opus utk kualitas
TIMEOUT = int(os.environ.get("CLAUDE_TIMEOUT", "600"))

SYSTEM = (
 "Kamu asisten quant yang diakses lewat WhatsApp oleh pemiliknya (Ben). "
 "Server: Proxmox CT 108 (/opt/idx-quant = saham IDX/Stockbit, /opt/mt5-quant = forex MT5). "
 "Untuk backtest/analisa, jalankan skrip via: PYTHONPATH=/opt/idx-quant /opt/idx-quant/venv/bin/python <skrip>. "
 "Skrip kunci: idx_stock_analysis.py <KODE> (analisa saham), idx_movers.py, bt_*.py (backtest), regime_scan.py (forex). "
 "Data: Stockbit REST via stockbit_history (saham), MT5 API 192.168.0.111:8000 (forex). "
 "JAWAB RINGKAS & cocok untuk WhatsApp (teks pendek, poin, angka penting). "
 "Hormati batas ROLE — kalau suatu aksi ditolak hook, jelaskan ke user role apa yg dibutuhkan. "
 "Jangan kirim order broker kecuali diminta eksplisit & role=live."
)

def _sfile(chat): return os.path.join(STATE_DIR, f"sess_{chat}.txt")

def load_session(chat):
    p=_sfile(chat)
    return open(p).read().strip() if os.path.exists(p) else None

def save_session(chat, sid):
    if sid: open(_sfile(chat),"w").write(sid)

def run_claude(prompt, chat, role, confirm=False):
    sid = load_session(chat)
    cmd = ["claude","-p",prompt,"--output-format","json","--model",MODEL,
           "--append-system-prompt",SYSTEM]
    for d in QUANT_DIRS: cmd += ["--add-dir", d]
    if sid: cmd += ["--resume", sid]
    env = {**os.environ, "CLAUDE_ROLE": role, "CLAUDE_CHAT": str(chat),
           "CLAUDE_CONFIRM": "1" if confirm else "0"}
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, env=env,
                           cwd=BRIDGE_DIR, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return "⏱️ Timeout — tugas terlalu lama. Coba persempit (mis. 1 simbol)."
    if r.returncode != 0:
        return f"⚠️ Error Claude (rc={r.returncode}): {(r.stderr or r.stdout)[:300]}"
    try:
        data = json.loads(r.stdout)
    except Exception:
        return (r.stdout or "(kosong)")[:1500]
    save_session(chat, data.get("session_id"))
    return data.get("result") or "(tidak ada jawaban)"

def reset_session(chat):
    p=_sfile(chat)
    if os.path.exists(p): os.remove(p)
