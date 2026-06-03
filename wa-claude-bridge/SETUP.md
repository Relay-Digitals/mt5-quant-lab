# WhatsApp ⇄ Claude Code Quant Bridge — Setup

Chat dengan Claude dari WhatsApp untuk riset strategi + backtest, dengan **role-based permission**.

```
HP/WA ⇄ WAHA (CT170) ⇄ Python Bot :8088 (CT108) → claude -p headless (CT108)
                                                     ↓ hook permguard.py (ROLE)
                                                   skrip backtest /opt/*-quant
```

## Komponen
| File | Fungsi |
|---|---|
| `bot.py` | FastAPI: webhook WAHA → auth → command/role → bridge → balas WA (async) |
| `bridge.py` | jalankan `claude -p` headless per-chat (role env + session resume + akses skrip quant) |
| `permguard.py` | hook PreToolUse: enforce role (blokir order/deploy sesuai role) |
| `roles.py` | definisi role: research / deploy / live |
| `.claude/settings.json` | daftarkan hook permguard |
| `wa-claude-bot.service` | systemd always-on |

## Deploy (di CT 108, sebagai root)
```bash
# 1. salin folder ini ke /opt/wa-claude-bridge (via pct push / scp / rathole)
mkdir -p /opt/wa-claude-bridge && cp -r * .claude /opt/wa-claude-bridge/
cd /opt/wa-claude-bridge
bash install.sh        # venv+deps, install claude CLI, systemd unit
```

## Langkah MANUAL (kamu)
### 1. Login Claude (Pro/Max) — sekali, interaktif
```bash
claude            # ketik /login → buka URL → login akun Pro/Max → paste kode
claude -p "halo"  # verifikasi jawab
```
> Headless langganan: kalau nanti minta login lagi (token expired), ulangi `claude /login`.

### 2. Isi `.env`
```bash
nano /opt/wa-claude-bridge/.env
# ALLOWED_NUMBERS=6289617180294   (nomor kamu, WAJIB diisi utk keamanan)
# WAHA_KEY=<api key WAHA>
```

### 3. Cari IP CT 108 (untuk webhook)
```bash
hostname -I        # mis. 192.168.0.108 — catat utk langkah 5
```

### 4. Jalankan bot
```bash
systemctl enable --now wa-claude-bot
curl localhost:8088/health     # {"ok":true,...}
```

### 5. Arahkan webhook WAHA ke bot (di CT 170)
WAHA harus POST pesan masuk ke bot. **Cara A — via API (tanpa restart, kalau versi WAHA dukung):**
```bash
KEY=<waha-key>
curl -X PUT "http://192.168.0.170:3000/api/sessions/default" -H "X-Api-Key: $KEY" -H "Content-Type: application/json" \
 -d '{"config":{"webhooks":[{"url":"http://<IP-CT108>:8088/webhook","events":["message"]}]}}'
# restart session bila perlu: POST /api/sessions/default/restart
```
**Cara B — via env container WAHA** (edit compose/env CT 170, lalu restart container):
```
WHATSAPP_HOOK_URL=http://<IP-CT108>:8088/webhook
WHATSAPP_HOOK_EVENTS=message
```
(Cara B mungkin perlu scan QR ulang — hati-hati.)

### 6. Tes dari WhatsApp
Kirim `/help`, lalu `analisa BBCA`, lalu `backtest TREND USDJPY 1 tahun`.

## Pemakaian (dari WhatsApp)
- Pesan biasa = instruksi ke Claude (riset/analisa/backtest).
- `/role research|deploy|live` — ganti izin (default research).
- `/confirm` — izinkan 1 aksi sensitif (5 menit) — untuk deploy/live.
- `/reset` — sesi baru (lupakan konteks).
- `/status`, `/help`.

## Role & keamanan
| Role | Boleh | Blokir |
|---|---|---|
| **research** (default) | baca data, riset, backtest | Write/Edit, order, systemctl |
| **deploy** | + ubah skrip, restart service (butuh /confirm) | order broker |
| **live** | + kirim order broker (butuh /confirm tiap kali) | — |

Enforcement: `permguard.py` (hook PreToolUse) memeriksa setiap tool-call vs role. Order/deploy butuh `CLAUDE_CONFIRM=1` (di-set bot setelah `/confirm`).

## Keamanan WAJIB
- Isi `ALLOWED_NUMBERS` — kalau kosong, **siapa pun** bisa pakai (jangan).
- Bot listen di LAN (:8088) — jangan ekspos ke internet tanpa proteksi.
- Role `live` = uang nyata (atau demo). Selalu butuh `/confirm`. Audit lewat log Claude + state/.
- `.env` jangan commit git.

## Troubleshooting
- Bot tak balas: `journalctl -u wa-claude-bot -f` ; cek `/health`.
- Webhook tak masuk: cek WAHA bisa reach `http://<IP-CT108>:8088/webhook` (firewall LAN), cek config session.
- Claude minta login: `claude /login` ulang.
- Aksi ditolak terus: cek role (`/status`), naikkan role + `/confirm`.
- Lambat/timeout: backtest besar makan menit; persempit (1 simbol/periode), atau naikkan `CLAUDE_TIMEOUT`.
