# WAHA Setup Runbook — Proxmox dari Nol sampai API Aktif

Panduan step-by-step setup self-hosted WhatsApp HTTP API di Proxmox LXC, dari container kosong sampai bisa kirim OTP via REST API.

**Target setup di guide ini:**
- CT 170 `whatsapp` (Debian 12 privileged, 1.5 GB RAM, 8 GB disk)
- IP statis `192.168.0.170`
- Docker + WAHA Community 2026.5.1
- Engine NOWEB (whatsmeow Go)
- Pairing code flow (bypass QR scan untuk lolos anti-bot 2025+)
- Optional: HTTPS via Caddy + Pi-hole DNS (skip kalau cukup HTTP intern)

**Estimasi waktu:** 15–20 menit + 2 menit waiting untuk WhatsApp link

---

## Prasyarat

Sebelum mulai:

- [x] Proxmox VE 8.x+ atau 9.x (panduan ini diuji di 9.1.7)
- [x] Storage Proxmox punya min 8 GB free (untuk CT rootfs)
- [x] Host RAM min 1.5 GB available
- [x] Template Debian 12 sudah ada di Proxmox: `local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst`
- [x] Network bridge `vmbr0` ke LAN (subnet `192.168.0.0/24` di guide ini)
- [x] Internet di Proxmox host untuk download Docker + image WAHA
- [x] **Nomor WhatsApp khusus bot** — terpisah dari nomor personal (resiko ban)
  - Saran: SIM kedua atau eSIM, install WA app, pakai normal 1–2 minggu dulu sebelum di-bot
- [x] HP target untuk scan/pairing — masih bisa login ke nomor bot

**Resiko penting** sebelum lanjut:
- Self-hosted bot WhatsApp **melanggar ToS Meta** — nomor bot bisa kena ban
- Volume aman: <20 pesan/hari ke nomor yang sudah di-save sebagai kontak
- Untuk production OTP yang sebenarnya, pertimbangkan **WhatsApp Cloud API resmi** (gratis 1000 conv/bulan dari Meta)

---

## Step 1 — Download template Debian 12 (skip kalau sudah ada)

Di Proxmox host:

```bash
pveam update
pveam download local debian-12-standard_12.12-1_amd64.tar.zst
```

Verifikasi:
```bash
pveam list local | grep debian-12
```

---

## Step 2 — Buat LXC container 170

```bash
pct create 170 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname whatsapp \
  --cores 1 --memory 1536 --swap 1024 \
  --rootfs local-lvm:8 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.0.170/24,gw=192.168.0.1,firewall=0 \
  --nameserver 1.1.1.1 \
  --features nesting=1,keyctl=1 \
  --unprivileged 0 --onboot 1 \
  --password 'GANTI_PASSWORD_INI' --start 1
```

**Penjelasan flag:**
- `--features nesting=1,keyctl=1` — penting untuk Docker-in-LXC
- `--unprivileged 0` — privileged container, butuh untuk Docker
- `--onboot 1` — auto-start saat Proxmox reboot
- `ip=192.168.0.170/24` — static, ganti sesuai subnet Anda
- `--memory 1536` — 1.5 GB, cukup untuk NOWEB. Kalau pakai WEBJS, naikkan ke 2048
- `--rootfs local-lvm:8` — 8 GB rootfs di local-lvm storage

Tunggu ~5 detik untuk boot. Verifikasi:

```bash
pct status 170                                    # status: running
pct exec 170 -- ip -4 addr show eth0 | grep inet  # IP 192.168.0.170
pct exec 170 -- ping -c 1 -W 2 1.1.1.1            # internet OK
```

---

## Step 3 — Install Docker di CT 170

```bash
pct exec 170 -- bash -c '
set -e
export DEBIAN_FRONTEND=noninteractive
echo nameserver 1.1.1.1 > /etc/resolv.conf

apt-get update -qq
apt-get install -y --no-install-recommends \
  ca-certificates curl gnupg

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -qq
apt-get install -y --no-install-recommends \
  docker-ce docker-ce-cli containerd.io

systemctl enable --now docker
systemctl is-active docker
'
```

Verifikasi Docker jalan:
```bash
pct exec 170 -- docker run --rm hello-world
```

---

## Step 4 — Generate API key + pull WAHA image

```bash
pct exec 170 -- bash -c '
# generate API key acak 48 hex
openssl rand -hex 24 > /root/waha-api-key
chmod 600 /root/waha-api-key
echo "API key:"
cat /root/waha-api-key
'

# pull image WAHA community (~709 MB)
pct exec 170 -- docker pull devlikeapro/waha:latest
```

Simpan API key ini — perlu untuk semua request.

---

## Step 5 — Buat volume persistent + jalankan WAHA

```bash
pct exec 170 -- bash -c '
# volume untuk session data, media, files (biar tahan restart container)
docker volume create waha_sessions
docker volume create waha_media
docker volume create waha_files

API_KEY=$(cat /root/waha-api-key)

docker run -d --restart=unless-stopped \
  --name waha \
  -p 3000:3000 \
  -v waha_sessions:/app/.sessions \
  -v waha_media:/app/.media \
  -v waha_files:/app/.files \
  -e WAHA_API_KEY="$API_KEY" \
  -e WAHA_BASE_URL=http://192.168.0.170:3000 \
  -e WAHA_DASHBOARD_USERNAME=admin \
  -e WAHA_DASHBOARD_PASSWORD=Sudimara19 \
  -e WHATSAPP_DEFAULT_ENGINE=NOWEB \
  devlikeapro/waha:latest

sleep 5
docker ps --format "{{.Names}}  {{.Status}}  {{.Ports}}"
'
```

**Pilihan env penting:**

| Env | Value | Catatan |
|---|---|---|
| `WAHA_API_KEY` | hex string | Wajib. Auth untuk semua API. |
| `WAHA_BASE_URL` | `http://192.168.0.170:3000` | Untuk auto-generate webhook URL & dashboard hint. Tanpa trailing slash. |
| `WAHA_DASHBOARD_USERNAME` / `PASSWORD` | admin / Sudimara19 | Login dashboard web. Ganti ke yang aman. |
| `WHATSAPP_DEFAULT_ENGINE` | `NOWEB` | ⭐ rekomendasi. Lebih ringan + paling sukses link saat ini. |

**Engine alternatif:**
- `NOWEB` — ⭐ default, ringan, paling sukses link via pairing code
- `WEBJS` — pakai Chromium, RAM ~800 MB, lebih kompatibel untuk fitur lama tapi sering ditolak link

Verifikasi WAHA running:
```bash
pct exec 170 -- docker ps                             # waha Up xx seconds
pct exec 170 -- docker logs waha 2>&1 | tail -5       # tidak ada error
```

Test API dari Proxmox host:
```bash
KEY=$(pct exec 170 -- cat /root/waha-api-key)
curl -H "X-API-Key: $KEY" http://192.168.0.170:3000/api/version
```

Expected:
```json
{"version":"2026.5.1","engine":"NOWEB","tier":"CORE",...}
```

---

## Step 6 — Buat session WhatsApp

```bash
KEY=$(pct exec 170 -- cat /root/waha-api-key)
WAHA="http://192.168.0.170:3000"

# create session 'default' + auto-start
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/sessions" \
  -d '{"name":"default","start":true}'
```

Tunggu ~8 detik untuk engine boot. Cek status:

```bash
curl -s -H "X-API-Key: $KEY" "$WAHA/api/sessions/default" | python3 -m json.tool
```

Expected: `"status": "SCAN_QR_CODE"` — siap link.

Kalau status `STOPPED` lebih lama dari 15 detik, start manual:
```bash
curl -X POST -H "X-API-Key: $KEY" "$WAHA/api/sessions/default/start"
```

---

## Step 7 — Link WhatsApp via Pairing Code (recommended)

**Penting:** **JANGAN coba scan QR dulu.** Pairing code lebih sering sukses di WhatsApp anti-bot 2025-2026.

### 7a. Request pairing code

Ganti nomor dengan nomor WhatsApp bot Anda (format internasional, tanpa `+` tanpa `0` depan):

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/default/auth/request-code" \
  -d '{"phoneNumber":"6289612748740"}'
```

Response:
```json
{ "code": "74ED-LS32" }
```

**Kode valid ~60 detik** — segera input di HP.

### 7b. Input code di HP nomor bot

1. Buka **WhatsApp** di HP nomor bot
2. **Settings (titik tiga kanan atas) → Linked Devices**
3. Tap **Link a Device**
4. Tap teks kecil **"Link with phone number instead"** (di bawah QR)
5. Masukkan nomor (contoh `+62 896-1274-8740`) → tap Next
6. WhatsApp tampil prompt **"Enter code"**
7. Ketik 8 karakter code (contoh `74ED-LS32`)

### 7c. Verifikasi WORKING

```bash
curl -s -H "X-API-Key: $KEY" "$WAHA/api/sessions/default" | python3 -m json.tool
```

Expected setelah pairing sukses:
```json
{
  "name": "default",
  "status": "WORKING",
  "me": {
    "id": "6289612748740@c.us",
    "pushName": "Nama Display Anda",
    "lid": "227191203877093@lid"
  },
  "engine": { "engine": "NOWEB" }
}
```

🎉 Session aktif.

### 7d. Fallback: kalau "Couldn't link device" muncul

**Coba urutan ini** (paling sering sukses di atas):

1. **Hapus session + recreate, request code ulang** — kadang transient:
   ```bash
   curl -X DELETE -H "X-API-Key: $KEY" "$WAHA/api/sessions/default"
   sleep 3
   curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
     "$WAHA/api/sessions" -d '{"name":"default","start":true}'
   sleep 8
   curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
     "$WAHA/api/default/auth/request-code" \
     -d '{"phoneNumber":"628XXXXXXXXX"}'
   ```

2. **Wipe semua volume dulu**, restart container, baru request code:
   ```bash
   pct exec 170 -- bash -c '
     docker stop waha && docker rm waha
     docker volume rm waha_sessions waha_media waha_files
     docker volume create waha_sessions
     docker volume create waha_media
     docker volume create waha_files
     # jalankan docker run yang sama seperti Step 5
   '
   ```

3. **Switch engine ke WEBJS** + coba pairing code:
   - Ubah env `WHATSAPP_DEFAULT_ENGINE=WEBJS` di docker run
   - Recreate container + session

4. **Coba QR scan** instead of pairing code:
   ```bash
   curl -H "X-API-Key: $KEY" "$WAHA/api/default/auth/qr" -o qr.png
   open qr.png   # di Mac
   ```
   Scan dari **Settings → Linked Devices → Link a Device** (tanpa "phone number instead")

5. **Coba nomor lain** — kalau nomor itu memang di-flag, no amount of retry akan work
6. **Tunggu 24–48 jam** — kadang Meta cooldown reset

---

## Step 8 — Test kirim pesan pertama

Kirim ke nomor target (ganti):

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/sendText" \
  -d '{
    "session": "default",
    "chatId": "6285319139480@c.us",
    "text": "Test pertama dari WAHA bot — kalau pesan ini sampai, setup berhasil."
  }'
```

Response sukses:
```json
{
  "key": {
    "remoteJid": "6285319139480@s.whatsapp.net",
    "fromMe": true,
    "id": "3EB07..."
  },
  "messageTimestamp": "1780122061",
  "status": "PENDING"
}
```

Cek HP target — pesan harusnya masuk dalam 1–5 detik.

**Format chatId:**
- Individu: `<countrycode><nomor>@c.us` — `6285319139480@c.us`
- Grup: `<group_id>@g.us` — perlu list grup dulu via `/api/{session}/groups`

---

## Step 9 — Smoke test sebagai script

Save sebagai `wa-test.sh` di Proxmox host:

```bash
#!/bin/bash
KEY=$(pct exec 170 -- cat /root/waha-api-key)
WAHA="http://192.168.0.170:3000"

echo "1. Version check..."
curl -s -H "X-API-Key: $KEY" "$WAHA/api/version" | jq

echo
echo "2. Session status..."
STATUS=$(curl -s -H "X-API-Key: $KEY" "$WAHA/api/sessions/default" | jq -r .status)
echo "Status: $STATUS"
[ "$STATUS" = "WORKING" ] || { echo "ERROR: session bukan WORKING"; exit 1; }

echo
echo "3. Check nomor target ada di WA..."
TARGET=6285319139480
RESULT=$(curl -s -H "X-API-Key: $KEY" \
  "$WAHA/api/contacts/check-exists?session=default&phone=$TARGET" | jq -r .numberExists)
echo "Number $TARGET exists: $RESULT"

echo
echo "4. Kirim test message..."
curl -s -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/sendText" \
  -d "{\"session\":\"default\",\"chatId\":\"$TARGET@c.us\",\"text\":\"Smoke test $(date)\"}" \
  | jq .key.id

echo
echo "Done. Cek HP target."
```

---

## Step 10 — (Optional) HTTPS via Caddy + Pi-hole DNS

Skip step ini kalau cukup pakai HTTP intern.

### 10a. Add DNS record di Pi-hole

```bash
# di Proxmox host (asumsi Pi-hole di CT 150 dengan custom DNS sudah aktif)
pct exec 150 -- /usr/bin/pihole-FTL --config dns.hosts \
  '[ "192.168.0.151 wa.lab.lan" ]'
pct exec 150 -- systemctl restart pihole-FTL
```

### 10b. Add Caddy reverse proxy

```bash
# di Proxmox host (Caddy di CT 151)
pct exec 151 -- bash -c '
cat >> /etc/caddy/Caddyfile <<EOF

wa.lab.lan {
    tls internal
    reverse_proxy 192.168.0.170:3000
}
EOF
systemctl reload caddy
'
```

### 10c. Trust root CA di CT 170 (WAHA worker need it)

```bash
# copy root CA dari Caddy ke CT 170
pct exec 151 -- cat /var/lib/caddy/.local/share/caddy/pki/authorities/local/root.crt > /tmp/lab-lan-ca.crt
pct push 170 /tmp/lab-lan-ca.crt /usr/local/share/ca-certificates/lab-lan-ca.crt
pct exec 170 -- update-ca-certificates

# add /etc/hosts entry di CT 170
pct exec 170 -- bash -c "echo '192.168.0.151 wa.lab.lan' >> /etc/hosts"

# restart WAHA dengan NODE_EXTRA_CA_CERTS
pct exec 170 -- bash -c '
docker stop waha && docker rm waha
API_KEY=$(cat /root/waha-api-key)
docker run -d --restart=unless-stopped \
  --name waha \
  --add-host wa.lab.lan:192.168.0.151 \
  -v /usr/local/share/ca-certificates/lab-lan-ca.crt:/etc/ssl/certs/lab-lan-ca.crt:ro \
  -p 3000:3000 \
  -v waha_sessions:/app/.sessions \
  -v waha_media:/app/.media \
  -v waha_files:/app/.files \
  -e WAHA_API_KEY="$API_KEY" \
  -e WAHA_BASE_URL=https://wa.lab.lan \
  -e WAHA_DASHBOARD_USERNAME=admin \
  -e WAHA_DASHBOARD_PASSWORD=Sudimara19 \
  -e WHATSAPP_DEFAULT_ENGINE=NOWEB \
  -e NODE_EXTRA_CA_CERTS=/etc/ssl/certs/lab-lan-ca.crt \
  devlikeapro/waha:latest
'
```

Test:
```bash
curl --cacert /tmp/lab-lan-ca.crt \
  -H "X-API-Key: $KEY" \
  https://wa.lab.lan/api/version
```

---

## Step 11 — Backup session (mandatory!)

**Session data = login WhatsApp Anda.** Kalau volume hilang, perlu scan/pairing ulang.

### Backup manual

```bash
# di Proxmox host
pct exec 170 -- docker run --rm \
  -v waha_sessions:/data -v /tmp:/backup alpine \
  tar czf /backup/waha-session-$(date +%Y%m%d).tgz /data

pct pull 170 /tmp/waha-session-$(date +%Y%m%d).tgz /var/backups/
```

### Backup otomatis (cron weekly)

Edit crontab Proxmox host:
```
0 3 * * 0 /usr/local/bin/waha-backup.sh
```

`/usr/local/bin/waha-backup.sh`:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
pct exec 170 -- docker run --rm \
  -v waha_sessions:/data -v /tmp:/backup alpine \
  tar czf /backup/waha-session-$DATE.tgz /data
pct pull 170 /tmp/waha-session-$DATE.tgz /var/backups/
# rotate: keep 4 backups
ls -t /var/backups/waha-session-*.tgz | tail -n +5 | xargs rm -f 2>/dev/null
echo "$(date) waha backup done"
```

### Restore

```bash
pct push 170 /var/backups/waha-session-YYYYMMDD.tgz /tmp/restore.tgz
pct exec 170 -- bash -c '
docker stop waha
docker run --rm -v waha_sessions:/data -v /tmp:/backup alpine \
  sh -c "rm -rf /data/* && tar xzf /backup/restore.tgz -C / "
docker start waha
'
```

---

## Step 12 — Health monitoring (auto-restart kalau session jatuh)

`/usr/local/bin/waha-healthcheck.sh` di Proxmox host:

```bash
#!/bin/bash
KEY=$(pct exec 170 -- cat /root/waha-api-key 2>/dev/null)
[ -z "$KEY" ] && exit 1

STATUS=$(curl -s --max-time 5 -H "X-API-Key: $KEY" \
  http://192.168.0.170:3000/api/sessions/default | jq -r .status 2>/dev/null)

case "$STATUS" in
  WORKING) exit 0 ;;
  ""|null)
    echo "[$(date)] WAHA API tidak respond, restart container"
    pct exec 170 -- docker restart waha
    ;;
  *)
    echo "[$(date)] Session status=$STATUS, restart session"
    curl -s -X POST --max-time 10 -H "X-API-Key: $KEY" \
      http://192.168.0.170:3000/api/sessions/default/restart
    ;;
esac
```

Add to crontab Proxmox host:
```
*/5 * * * * /usr/local/bin/waha-healthcheck.sh >> /var/log/waha-health.log 2>&1
```

---

## Step 13 — Integrasi backend Anda

Setelah API jalan, hubungkan dari aplikasi backend.

### Pattern recommended untuk OTP

```
[User klik "Send OTP"]
    ↓
[Backend Anda]
    ↓
1. Generate OTP code 6-digit
2. Cek rate-limit (max 3 OTP/jam/nomor, 50/hari total)
3. Save code ke Redis dengan TTL 300 detik:
   redis.SET "otp:6281234..." "123456" EX 300
4. POST ke WAHA /api/sendText
5. Kalau gagal → fallback ke SMS/Email
6. Return ke user "OTP sent"
    ↓
[User input OTP di form]
    ↓
[Backend verify dari Redis]
    ↓
Hapus entry dari Redis setelah verified
```

### Endpoint contoh (FastAPI)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis, requests, secrets, os

app = FastAPI()
r = redis.Redis(host="localhost", port=6379)
WAHA = "http://192.168.0.170:3000"
KEY = os.environ["WAHA_API_KEY"]

class OTPRequest(BaseModel):
    phone: str  # format: 6281234567890

class OTPVerify(BaseModel):
    phone: str
    code: str

@app.post("/otp/send")
def send_otp(req: OTPRequest):
    # rate limit: max 3 dalam 1 jam per nomor
    key = f"otp_count:{req.phone}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, 3600)
    if count > 3:
        raise HTTPException(429, "Terlalu banyak request OTP, coba 1 jam lagi")

    # generate + simpan dengan TTL 5 menit
    code = f"{secrets.randbelow(900000) + 100000}"
    r.setex(f"otp:{req.phone}", 300, code)

    # kirim via WAHA
    try:
        resp = requests.post(
            f"{WAHA}/api/sendText",
            headers={"X-API-Key": KEY, "Content-Type": "application/json"},
            json={
                "session": "default",
                "chatId": f"{req.phone}@c.us",
                "text": f"Kode OTP: *{code}*\n\nBerlaku 5 menit. Jangan share ke siapapun."
            },
            timeout=8,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        # TODO: fallback ke SMS Twilio
        raise HTTPException(503, f"Gagal kirim OTP: {e}")

    return {"status": "sent", "expires_in": 300}


@app.post("/otp/verify")
def verify_otp(req: OTPVerify):
    stored = r.get(f"otp:{req.phone}")
    if not stored or stored.decode() != req.code:
        raise HTTPException(401, "Kode salah atau expired")
    r.delete(f"otp:{req.phone}")
    return {"status": "verified"}
```

Lihat **WAHA-API.md** untuk reference endpoint lain.

---

## Troubleshooting cepat

| Gejala | Cek | Fix |
|---|---|---|
| `connection refused` ke :3000 | `docker ps` | Container mati → `docker start waha` atau restart CT |
| 401 Unauthorized | API key salah | `cat /root/waha-api-key` di CT 170, copy ulang |
| Session stuck di STARTING >30s | `docker logs waha` | Restart session: `POST /api/sessions/default/restart` |
| Sukses kirim tapi pesan tidak sampai | check chatId format `@c.us` | Pastikan nomor terdaftar WA: `/api/contacts/check-exists` |
| "Couldn't link device" terus-terusan | Engine + auth combo | Coba urutan di Step 7d |
| RAM CT 170 full | `free -h` | Naikkan: `pct set 170 -memory 2048` + reboot CT |
| Session disconnect tiap beberapa jam | HP nomor bot offline? | Pastikan HP tetap online (minimal nyala terus dengan data) |
| Webhook tidak nge-trigger | Test endpoint dari CT 170 | `pct exec 170 -- curl https://backend...` |

---

## Yang JANGAN dilakukan

❌ **Jangan kirim ke nomor random/scraped** — auto-ban
❌ **Jangan kirim >50/hari awalnya** — ramp up gradually
❌ **Jangan pakai nomor utama Anda** — kalau ban, akun WA pribadi hilang juga
❌ **Jangan pakai untuk marketing/spam** — Meta detect via pattern
❌ **Jangan share API key di repo Git public** — pakai .env / secrets manager
❌ **Jangan hapus volume `waha_sessions` tanpa backup** — re-link butuh nomor bot online lagi
❌ **Jangan expose port 3000 ke internet langsung** — minimal pakai reverse proxy + IP whitelist + HTTPS

---

## Checklist akhir (state target)

- [ ] CT 170 running, `pct status 170` = `running`
- [ ] Docker active di CT 170: `pct exec 170 -- systemctl is-active docker` = `active`
- [ ] WAHA container running: `pct exec 170 -- docker ps | grep waha`
- [ ] API version respond: `curl -H "X-API-Key:..." http://192.168.0.170:3000/api/version`
- [ ] Session `default` status = `WORKING`
- [ ] Test kirim ke nomor sendiri berhasil
- [ ] Backup script terpasang di crontab
- [ ] Health check script terpasang di crontab
- [ ] API key disimpan di password manager + di /root/waha-api-key

---

## Referensi konfigurasi instance ini

| Item | Value |
|---|---|
| Proxmox host | 192.168.0.222 |
| CT ID | 170 |
| Hostname | whatsapp |
| IP | 192.168.0.170 |
| Subnet | 192.168.0.0/24 |
| Gateway | 192.168.0.1 |
| DNS | 192.168.0.150 (Pi-hole) atau 1.1.1.1 |
| Resources | 1 core, 1.5 GB RAM, 1 GB swap, 8 GB disk |
| OS | Debian 12 (privileged LXC) |
| Docker version | latest stable |
| WAHA image | `devlikeapro/waha:latest` (2026.5.1) |
| Engine | NOWEB |
| HTTPS domain (opsional) | https://wa.lab.lan |
| Dashboard | http://192.168.0.170:3000/dashboard |
| Dashboard creds | admin / Sudimara19 |
| API base | http://192.168.0.170:3000 |
| API key location | `/root/waha-api-key` di CT 170 |

---

## Selanjutnya

Lihat dokumentasi terkait:
- **WAHA-API.md** — Reference semua endpoint API lengkap dengan curl/Python/Node example
- Setup OTP integration di backend Anda — lihat Step 13 untuk pattern Redis + FastAPI

Untuk update WAHA ke versi baru:
```bash
pct exec 170 -- bash -c '
  docker pull devlikeapro/waha:latest
  docker stop waha && docker rm waha
  # jalankan docker run yang sama seperti Step 5
'
```

---

_Setup runbook diuji di Proxmox VE 9.1.7, kernel 6.17.13-2-pve, WAHA Community 2026.5.1, 30 Mei 2026._
