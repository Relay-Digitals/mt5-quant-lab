"""bot.py — Python BOT: terima webhook WAHA (pesan WA masuk) → auth → role/command → Claude bridge → balas WA.
Jalankan: uvicorn bot:app --host 0.0.0.0 --port 8088
Config via .env (lihat .env.example)."""
import os, json, time, threading, requests
from fastapi import FastAPI, Request
import roles, bridge

def env(k, d=""): return os.environ.get(k, d)
WAHA_URL = env("WAHA_URL", "http://192.168.0.170:3000").rstrip("/")
WAHA_KEY = env("WAHA_KEY", "")
WAHA_SESSION = env("WAHA_SESSION", "default")
ALLOWED = {n.strip() for n in env("ALLOWED_NUMBERS", "").split(",") if n.strip()}  # mis. 6289617180294
BRIDGE_DIR = os.path.dirname(os.path.abspath(__file__))
RSTATE = os.path.join(BRIDGE_DIR, "state", "roles.json")
os.makedirs(os.path.dirname(RSTATE), exist_ok=True)

app = FastAPI()

def _load():
    try: return json.load(open(RSTATE))
    except Exception: return {}
def _save(d): json.dump(d, open(RSTATE, "w"))
def get_role(chat): return _load().get(chat, {}).get("role", roles.DEFAULT_ROLE)
def set_role(chat, role):
    d=_load(); d.setdefault(chat,{})["role"]=role; _save(d)
def set_confirm(chat, on):
    d=_load(); d.setdefault(chat,{})["confirm_until"]= (time.time()+300) if on else 0; _save(d)
def confirm_active(chat):
    return _load().get(chat,{}).get("confirm_until",0) > time.time()

def wa_send(chat, text):
    if not text: return
    for i in range(0, len(text), 3500):
        try:
            requests.post(f"{WAHA_URL}/api/sendText",
                headers={"X-Api-Key": WAHA_KEY, "Content-Type": "application/json"},
                json={"session": WAHA_SESSION, "chatId": chat, "text": text[i:i+3500]}, timeout=15)
        except Exception as e: print("[wa_send]", str(e)[:80])

HELP = ("🤖 *Quant Assistant (WhatsApp)*\n"
        "Ketik pertanyaan/instruksi strategi/backtest biasa.\n\n"
        "*Perintah:*\n"
        "/role research|deploy|live — ganti izin\n"
        "/confirm — izinkan 1 aksi sensitif (5 menit)\n"
        "/reset — mulai sesi baru (lupakan konteks)\n"
        "/status — role & info\n"
        "/help — bantuan")

def handle(chat, body):
    b = body.strip()
    low = b.lower()
    if low in ("/help", "help", "menu"):
        wa_send(chat, HELP); return
    if low.startswith("/role"):
        parts = low.split()
        if len(parts) > 1 and parts[1] in roles.ROLES:
            set_role(chat, parts[1])
            wa_send(chat, f"✅ Role → {roles.ROLES[parts[1]]['label']}\n{roles.ROLES[parts[1]]['desc']}")
        else:
            cur = get_role(chat)
            opts = "\n".join(f"• {k} — {v['label']}" for k,v in roles.ROLES.items())
            wa_send(chat, f"Role sekarang: *{cur}*\nGanti: /role <nama>\n{opts}")
        return
    if low == "/confirm":
        set_confirm(chat, True); wa_send(chat, "🔓 Konfirmasi aktif 5 menit — ulangi instruksi sensitifmu."); return
    if low == "/reset":
        bridge.reset_session(chat); wa_send(chat, "🔄 Sesi di-reset (konteks dilupakan)."); return
    if low == "/status":
        r = get_role(chat)
        wa_send(chat, f"Role: {roles.ROLES[r]['label']}\nKonfirmasi: {'aktif' if confirm_active(chat) else 'tidak'}\nModel: {bridge.MODEL}"); return
    # instruksi normal → Claude
    role = get_role(chat); conf = confirm_active(chat)
    wa_send(chat, f"⏳ Memproses ({roles.ROLES[role]['label']})...")
    ans = bridge.run_claude(b, chat, role, confirm=conf)
    if conf: set_confirm(chat, False)  # konsumsi sekali pakai
    wa_send(chat, ans)

@app.post("/webhook")
async def webhook(req: Request):
    try: data = await req.json()
    except Exception: return {"ok": False}
    if data.get("event") != "message": return {"ok": True}
    p = data.get("payload", {}) or {}
    if p.get("fromMe"): return {"ok": True}            # abaikan pesan sendiri (anti-loop)
    chat = p.get("from", ""); body = p.get("body", "") or ""
    num = chat.split("@")[0]
    if ALLOWED and num not in ALLOWED:
        print(f"[auth] tolak {num}"); return {"ok": True}   # senyap utk nomor tak diizinkan
    if not body.strip(): return {"ok": True}
    threading.Thread(target=handle, args=(chat, body), daemon=True).start()  # async, jangan blok webhook
    return {"ok": True}

@app.get("/health")
def health(): return {"ok": True, "allowed": len(ALLOWED), "model": bridge.MODEL}
