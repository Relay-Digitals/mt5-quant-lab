# WAHA API Reference

Self-hosted WhatsApp HTTP API yang berjalan di CT 170 Proxmox.

**Versi referensi:** WAHA Community 2026.5.1, engine NOWEB.
**Session aktif:** `default` linked ke `6289612748740` (Diki Haryadi).

---

## Konfigurasi koneksi

| Item | Value |
|---|---|
| Base URL (HTTP) | `http://192.168.0.170:3000` |
| Base URL (HTTPS) | `https://wa.lab.lan` (butuh DNS Pi-hole + root CA `lab-lan-ca.crt` di client) |
| API Key | `7a76d93a6809f8bb692524bf06c69d7717d3de18d36429e3` |
| Header auth | `X-API-Key: <api_key>` |
| Dashboard | `http://192.168.0.170:3000/dashboard` |
| Dashboard login | `admin` / `Sudimara19` |
| Default session | `default` |

**Format chatId:**
- Individu: `<countrycode><nomor>@c.us` — contoh `6285319139480@c.us`
- Grup: `<groupid>@g.us` — contoh `120363025246125486@g.us`
- Tanpa `+`, tanpa `0` di depan, dengan kode negara

---

## Quick start

```bash
export WAHA="http://192.168.0.170:3000"
export KEY="7a76d93a6809f8bb692524bf06c69d7717d3de18d36429e3"

# cek versi
curl -H "X-API-Key: $KEY" "$WAHA/api/version"

# kirim pesan
curl -X POST "$WAHA/api/sendText" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"session":"default","chatId":"6285319139480@c.us","text":"Halo"}'
```

---

## 1. Server

### GET `/api/version`
Info versi WAHA + engine.

```bash
curl -H "X-API-Key: $KEY" "$WAHA/api/version"
```

Response:
```json
{
  "version": "2026.5.1",
  "engine": "NOWEB",
  "tier": "CORE",
  "browser": null,
  "platform": "linux/x64"
}
```

### GET `/api/server/environment`
Daftar env var yang aktif (admin-only).

### GET `/api/server/status`
Health status.

### POST `/api/server/stop`
Stop server (jarang dipakai).

---

## 2. Sessions

WAHA satu instance bisa punya beberapa session WhatsApp paralel. Setiap session = 1 nomor WhatsApp.

### GET `/api/sessions`
List semua session.

```bash
curl -H "X-API-Key: $KEY" "$WAHA/api/sessions?all=true"
```

Response (per session):
```json
{
  "name": "default",
  "status": "WORKING",
  "engine": { "engine": "NOWEB" },
  "me": {
    "id": "6289612748740@c.us",
    "pushName": "Diki Haryadi",
    "lid": "227191203877093@lid"
  },
  "presence": "offline",
  "timestamps": { "activity": 1780122061593 }
}
```

**Status states:**
- `STOPPED` — session ada tapi tidak running
- `STARTING` — sedang inisialisasi engine
- `SCAN_QR_CODE` — siap di-scan QR
- `PAIRING` — sedang process pairing code
- `WORKING` — terkoneksi, siap kirim/terima
- `FAILED` — error, perlu restart

### GET `/api/sessions/{session}`
Info satu session.

```bash
curl -H "X-API-Key: $KEY" "$WAHA/api/sessions/default"
```

### POST `/api/sessions`
Buat session baru (auto-start kalau `start: true`).

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/sessions" \
  -d '{
    "name": "mybot",
    "start": true,
    "config": {
      "webhooks": [
        {
          "url": "https://my-backend.example.com/wa-webhook",
          "events": ["message", "message.ack"]
        }
      ]
    }
  }'
```

### PUT `/api/sessions/{session}`
Update config session existing.

### POST `/api/sessions/{session}/start`
Start session yang STOPPED.

```bash
curl -X POST -H "X-API-Key: $KEY" "$WAHA/api/sessions/default/start"
```

### POST `/api/sessions/{session}/stop`
Stop session (tidak hapus data login).

### POST `/api/sessions/{session}/restart`
Restart (= stop + start) — pakai kalau session hang.

### POST `/api/sessions/{session}/logout`
Logout dari WhatsApp + hapus auth data. Perlu scan QR / pairing code lagi untuk re-link.

### DELETE `/api/sessions/{session}`
Hapus session sepenuhnya (config + data).

---

## 3. Auth (QR & Pairing Code)

Cuma dipakai saat session status = `SCAN_QR_CODE`.

### GET `/api/{session}/auth/qr`
Get QR code sebagai image PNG (default) atau raw text.

```bash
# PNG image
curl -H "X-API-Key: $KEY" "$WAHA/api/default/auth/qr" -o qr.png

# Raw text (untuk di-encode sendiri)
curl -H "X-API-Key: $KEY" "$WAHA/api/default/auth/qr?format=raw"
```

QR refresh tiap ~30 detik.

### POST `/api/{session}/auth/request-code`
Request pairing code (alternative ke QR scan). Lebih reliable di WhatsApp anti-bot 2025+.

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/default/auth/request-code" \
  -d '{"phoneNumber": "6289612748740"}'
```

Response:
```json
{ "code": "ABCD-EFGH" }
```

Di HP target:
1. WhatsApp → Settings → Linked Devices → Link a Device
2. "Link with phone number instead"
3. Masukkan nomor + ketik 8-char code

**Note:** Kalau "couldn't link device" muncul, coba kombinasi engine + method:
- NOWEB + phone code ⭐ (paling sukses di 2026)
- WEBJS + QR
- WEBJS + phone code
- NOWEB + QR

### POST `/api/{session}/auth/authorize-code`
(Tidak umum) — submit code dari sisi server.

---

## 4. Kirim Pesan

Semua endpoint kirim butuh body field `session` + `chatId` + payload-specific.

### POST `/api/sendText`
Kirim text biasa.

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/sendText" \
  -d '{
    "session": "default",
    "chatId": "6285319139480@c.us",
    "text": "Halo dari bot!",
    "reply_to": null,
    "linkPreview": true,
    "mentions": []
  }'
```

**Options:**
- `text` — pesan (support emoji, multi-line `\n`, markdown WhatsApp `*bold*` `_italic_` `~strike~` `` `code` ``)
- `reply_to` — message ID yang di-reply (opsional)
- `linkPreview` — auto-generate preview untuk URL (default `true`)
- `mentions` — array of `[ "62812...@c.us" ]` untuk mention `@nama`

### POST `/api/sendImage`
Kirim gambar dengan caption.

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/sendImage" \
  -d '{
    "session": "default",
    "chatId": "6285319139480@c.us",
    "file": {
      "url": "https://example.com/photo.jpg"
    },
    "caption": "Foto pemandangan"
  }'
```

**File source options** (pilih salah satu di `file`):
- `{ "url": "https://..." }` — fetch dari URL
- `{ "data": "<base64>", "mimetype": "image/jpeg", "filename": "x.jpg" }` — base64 inline

### POST `/api/sendFile`
Kirim file/dokumen.

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/sendFile" \
  -d '{
    "session": "default",
    "chatId": "6285319139480@c.us",
    "file": {
      "url": "https://example.com/invoice.pdf",
      "filename": "invoice.pdf"
    },
    "caption": "Invoice bulan ini"
  }'
```

### POST `/api/sendVoice`
Kirim voice note (audio dengan waveform).

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/sendVoice" \
  -d '{
    "session": "default",
    "chatId": "6285319139480@c.us",
    "file": { "url": "https://example.com/voice.ogg" },
    "convert": true
  }'
```

`convert: true` — auto-convert ke OGG Opus (format yang WhatsApp pakai).

### POST `/api/sendVideo`
Kirim video.

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/sendVideo" \
  -d '{
    "session": "default",
    "chatId": "6285319139480@c.us",
    "file": { "url": "https://example.com/clip.mp4" },
    "caption": "Demo product",
    "asNote": false,
    "convert": true
  }'
```

`asNote: true` — kirim sebagai video note (bulat, max 60 detik).

### POST `/api/sendLocation`
Kirim location pin.

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/sendLocation" \
  -d '{
    "session": "default",
    "chatId": "6285319139480@c.us",
    "latitude": -6.2088,
    "longitude": 106.8456,
    "title": "Kantor Jakarta"
  }'
```

### POST `/api/sendContactVcard`
Kirim contact card.

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/sendContactVcard" \
  -d '{
    "session": "default",
    "chatId": "6285319139480@c.us",
    "contacts": [
      {
        "vcard": "BEGIN:VCARD\nVERSION:3.0\nFN:John Doe\nTEL;type=CELL:+62812345678\nEND:VCARD"
      }
    ]
  }'
```

### POST `/api/sendLinkPreview`
Kirim URL dengan preview kustom.

### POST `/api/sendReaction`
Kasih emoji reaction ke pesan.

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/reaction" \
  -d '{
    "session": "default",
    "messageId": "<id_pesan>",
    "reaction": "👍"
  }'
```

Hapus reaction: kirim `"reaction": ""` (empty string).

### POST `/api/sendSeen`
Mark message sebagai read (centang biru).

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/sendSeen" \
  -d '{
    "session": "default",
    "chatId": "6285319139480@c.us",
    "messageId": "<id_pesan>"
  }'
```

### POST `/api/startTyping` / `/api/stopTyping`
Indicator "sedang mengetik..."

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/startTyping" \
  -d '{"session":"default","chatId":"6285319139480@c.us"}'

# tunggu 1-3 detik, lalu stop sebelum kirim pesan asli
```

---

## 5. Chats & Messages (Receiving)

### GET `/api/{session}/chats`
List semua chat.

```bash
curl -H "X-API-Key: $KEY" "$WAHA/api/default/chats?limit=20&offset=0"
```

### GET `/api/{session}/chats/{chatId}/messages`
History pesan dari satu chat.

```bash
curl -H "X-API-Key: $KEY" \
  "$WAHA/api/default/chats/6285319139480@c.us/messages?limit=50&downloadMedia=false"
```

**Query params:**
- `limit` — jumlah pesan (default 100)
- `offset` — paging
- `downloadMedia` — kalau true, auto-download attachment
- `filter.timestamp.lte` / `gte` — filter range tanggal

### GET `/api/{session}/chats/{chatId}`
Info chat (last message, unread count, dll).

### DELETE `/api/{session}/chats/{chatId}/messages`
Clear semua pesan di chat (sisi bot saja).

### POST `/api/{session}/chats/{chatId}/archive`
Archive chat.

### POST `/api/{session}/chats/{chatId}/unarchive`
Unarchive.

### POST `/api/{session}/chats/{chatId}/unread`
Mark sebagai unread.

---

## 6. Contacts

### GET `/api/contacts/all`
Semua kontak.

```bash
curl -H "X-API-Key: $KEY" "$WAHA/api/contacts/all?session=default"
```

### GET `/api/contacts`
Cari kontak satuan.

```bash
curl -H "X-API-Key: $KEY" \
  "$WAHA/api/contacts?session=default&contactId=6285319139480@c.us"
```

### GET `/api/contacts/check-exists`
Cek apakah nomor terdaftar di WhatsApp.

```bash
curl -H "X-API-Key: $KEY" \
  "$WAHA/api/contacts/check-exists?session=default&phone=6285319139480"
```

Response:
```json
{ "numberExists": true, "chatId": "6285319139480@c.us" }
```

**Tip:** Selalu cek dulu sebelum kirim ke nomor baru, biar tidak waste rate-limit.

### GET `/api/contacts/profile-picture`
Get URL avatar kontak.

```bash
curl -H "X-API-Key: $KEY" \
  "$WAHA/api/contacts/profile-picture?session=default&contactId=6285319139480@c.us"
```

### POST `/api/contacts/block` / `/api/contacts/unblock`
Block / unblock kontak.

---

## 7. Groups

### GET `/api/{session}/groups`
List grup yang bot ikut.

### POST `/api/{session}/groups`
Buat grup baru.

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/default/groups" \
  -d '{
    "name": "Tim Marketing",
    "participants": [
      { "id": "6285319139480@c.us" },
      { "id": "6281234567890@c.us" }
    ]
  }'
```

### GET `/api/{session}/groups/{groupId}`
Info grup.

### POST `/api/{session}/groups/{groupId}/participants/add`
Add anggota.

### POST `/api/{session}/groups/{groupId}/participants/remove`
Kick anggota.

### POST `/api/{session}/groups/{groupId}/participants/promote`
Promote ke admin.

### POST `/api/{session}/groups/{groupId}/participants/demote`
Turunin dari admin.

### POST `/api/{session}/groups/{groupId}/leave`
Bot keluar grup.

### PUT `/api/{session}/groups/{groupId}/subject` / `/description` / `/settings`
Update info grup.

---

## 8. Profile

### GET `/api/{session}/profile`
Info profil bot.

### PUT `/api/{session}/profile/name`
Ubah display name.

```bash
curl -X PUT -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/default/profile/name" \
  -d '{"name":"OTP Bot Relay"}'
```

### PUT `/api/{session}/profile/status`
Ubah status (about/bio).

### PUT `/api/{session}/profile/picture`
Ubah foto profil.

```bash
curl -X PUT -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/default/profile/picture" \
  -d '{"file":{"url":"https://example.com/avatar.jpg"}}'
```

### DELETE `/api/{session}/profile/picture`
Hapus foto profil.

---

## 9. Presence (online / typing / lastseen)

### GET `/api/{session}/presence/{chatId}`
Cek presence kontak (online/offline/typing).

### POST `/api/{session}/presence`
Set presence bot sendiri (online / typing / paused).

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/default/presence" \
  -d '{"presence":"online"}'
```

---

## 10. Status (Stories)

### POST `/api/{session}/status/text`
Post status text.

### POST `/api/{session}/status/image` / `/video` / `/voice`
Post status berisi media.

### POST `/api/{session}/status/delete`
Hapus status.

---

## 11. Channels (Newsletter)

### GET `/api/{session}/channels`
List channel yang bot follow.

### POST `/api/{session}/channels/search/by-view`
Cari channel populer.

### POST `/api/{session}/channels/{channelId}/follow`
Follow channel.

---

## 12. Webhooks

Daftarkan webhook untuk dapat event real-time (incoming message, ack, presence change, dll).

### Config webhook di session

Saat create session:
```json
{
  "name": "default",
  "start": true,
  "config": {
    "webhooks": [
      {
        "url": "https://my-backend.example.com/wa-webhook",
        "events": ["message", "message.ack", "state.change"],
        "hmac": { "key": "secret-for-signature" },
        "retries": { "delaySeconds": 2, "attempts": 3 }
      }
    ]
  }
}
```

### Event types

| Event | Trigger |
|---|---|
| `message` | Pesan masuk |
| `message.any` | Semua pesan (in + out) |
| `message.reaction` | Reaction di-add/remove |
| `message.ack` | Delivery status berubah (PENDING/SERVER/DEVICE/READ/PLAYED) |
| `message.waiting` | Bot mau kirim, queued |
| `state.change` | Session state berubah (STARTING → WORKING dll) |
| `group.v2.join` | Bot di-add ke grup |
| `group.v2.leave` | Bot di-kick / leave |
| `group.v2.participants` | Anggota grup berubah |
| `presence.update` | Presence kontak update |
| `poll.vote` | Voting di poll |
| `chat.archive` | Chat di-archive |
| `call.received` | Telepon masuk |

### Payload contoh (event `message`)

```json
{
  "event": "message",
  "session": "default",
  "metadata": {},
  "me": { "id": "6289612748740@c.us", "pushName": "Diki Haryadi" },
  "payload": {
    "id": "false_6285319139480@c.us_3EB07...",
    "timestamp": 1780122061,
    "from": "6285319139480@c.us",
    "fromMe": false,
    "body": "Halo",
    "hasMedia": false,
    "ack": 1,
    "vCards": [],
    "_data": { ... }
  }
}
```

### HMAC signature verification

Kalau set `hmac.key` di config, WAHA tambahin header `X-Webhook-Hmac` berisi HMAC-SHA512 dari raw body. Verifikasi di backend:

**Python:**
```python
import hmac, hashlib

def verify(body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## 13. Files (Media Download)

Saat webhook event `message` masuk dengan `hasMedia: true`, download file via:

### GET `/api/files/{filename}`
Atau pakai URL yang ada di payload `payload._data.url`.

```python
# Auto-download media saat fetch messages
requests.get(f"{WAHA}/api/default/chats/{chat}/messages?downloadMedia=true",
             headers={"X-API-Key": KEY})
```

---

## 14. Code Examples per bahasa

### Python — OTP send (production-ready)

```python
import requests, secrets, time
from typing import Optional

class WahaClient:
    def __init__(self, base: str, key: str, session: str = "default"):
        self.base = base.rstrip("/")
        self.headers = {"X-API-Key": key, "Content-Type": "application/json"}
        self.session = session

    def send_text(self, phone: str, text: str, retries: int = 3) -> Optional[str]:
        """phone: '6281234567890' tanpa + atau 0. Returns message_id."""
        for attempt in range(retries):
            try:
                r = requests.post(
                    f"{self.base}/api/sendText",
                    headers=self.headers,
                    json={
                        "session": self.session,
                        "chatId": f"{phone}@c.us",
                        "text": text,
                    },
                    timeout=10,
                )
                r.raise_for_status()
                return r.json()["key"]["id"]
            except requests.RequestException as e:
                if attempt == retries - 1:
                    raise
                time.sleep(2 ** attempt)
        return None

    def check_exists(self, phone: str) -> bool:
        r = requests.get(
            f"{self.base}/api/contacts/check-exists",
            params={"session": self.session, "phone": phone},
            headers={"X-API-Key": self.headers["X-API-Key"]},
            timeout=5,
        )
        return r.json().get("numberExists", False)


def send_otp(phone: str) -> str:
    """Generate + send OTP, return code untuk disimpan di Redis dengan TTL."""
    wa = WahaClient(
        "http://192.168.0.170:3000",
        "7a76d93a6809f8bb692524bf06c69d7717d3de18d36429e3",
    )

    if not wa.check_exists(phone):
        raise ValueError(f"Nomor {phone} tidak terdaftar di WhatsApp")

    code = f"{secrets.randbelow(900000) + 100000}"
    wa.send_text(phone, f"Kode OTP Relay: *{code}*\n\nBerlaku 5 menit. Jangan share ke siapapun.")
    return code
```

### Node.js / TypeScript

```typescript
const WAHA = "http://192.168.0.170:3000";
const KEY = process.env.WAHA_API_KEY!;

async function sendOtp(phone: string): Promise<string> {
  const code = String(Math.floor(100000 + Math.random() * 900000));

  const res = await fetch(`${WAHA}/api/sendText`, {
    method: "POST",
    headers: {
      "X-API-Key": KEY,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session: "default",
      chatId: `${phone}@c.us`,
      text: `Kode OTP: *${code}*\nBerlaku 5 menit.`,
    }),
  });

  if (!res.ok) throw new Error(`WAHA error ${res.status}: ${await res.text()}`);
  return code;
}
```

### PHP

```php
<?php
function sendOtp(string $phone): string {
    $code = str_pad((string)random_int(0, 999999), 6, '0', STR_PAD_LEFT);
    $ch = curl_init('http://192.168.0.170:3000/api/sendText');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_HTTPHEADER => [
            'X-API-Key: ' . getenv('WAHA_KEY'),
            'Content-Type: application/json',
        ],
        CURLOPT_POSTFIELDS => json_encode([
            'session' => 'default',
            'chatId' => "{$phone}@c.us",
            'text' => "Kode OTP: *{$code}*\nBerlaku 5 menit.",
        ]),
    ]);
    $resp = curl_exec($ch);
    if (curl_getinfo($ch, CURLINFO_RESPONSE_CODE) >= 400) {
        throw new RuntimeException("WAHA failed: $resp");
    }
    return $code;
}
```

### Go

```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
)

const (
	wahaURL = "http://192.168.0.170:3000"
	wahaKey = "7a76d93a6809f8bb692524bf06c69d7717d3de18d36429e3"
)

func SendText(phone, text string) error {
	body, _ := json.Marshal(map[string]string{
		"session": "default",
		"chatId":  phone + "@c.us",
		"text":    text,
	})
	req, _ := http.NewRequest("POST", wahaURL+"/api/sendText", bytes.NewReader(body))
	req.Header.Set("X-API-Key", wahaKey)
	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return fmt.Errorf("waha %d", resp.StatusCode)
	}
	return nil
}
```

### curl one-liners cheatsheet

```bash
# Session WORKING?
curl -s -H "X-API-Key: $KEY" "$WAHA/api/sessions/default" | jq .status

# Kirim text
curl -s -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  "$WAHA/api/sendText" -d '{"session":"default","chatId":"6285319139480@c.us","text":"hi"}'

# Cek nomor exists
curl -s -H "X-API-Key: $KEY" \
  "$WAHA/api/contacts/check-exists?session=default&phone=6285319139480"

# Get profile picture URL
curl -s -H "X-API-Key: $KEY" \
  "$WAHA/api/contacts/profile-picture?session=default&contactId=6285319139480@c.us"

# Last 10 messages dari chat
curl -s -H "X-API-Key: $KEY" \
  "$WAHA/api/default/chats/6285319139480@c.us/messages?limit=10"

# Logout (perlu scan ulang)
curl -s -X POST -H "X-API-Key: $KEY" "$WAHA/api/sessions/default/logout"
```

---

## 15. Operations & Maintenance

### Backup session data

Penting — biar tidak perlu scan QR ulang kalau CT crash.

```bash
# di Proxmox host
pct exec 170 -- docker run --rm \
  -v waha_sessions:/data -v /tmp:/backup alpine \
  tar czf /backup/waha-session-$(date +%Y%m%d).tgz /data
pct pull 170 /tmp/waha-session-*.tgz /var/backups/
```

### Restore session

```bash
# kalau perlu restore dari backup
pct push 170 /var/backups/waha-session-YYYYMMDD.tgz /tmp/restore.tgz
pct exec 170 -- docker run --rm \
  -v waha_sessions:/data -v /tmp:/backup alpine \
  tar xzf /backup/restore.tgz -C /
```

### Logs

```bash
pct exec 170 -- docker logs waha -f --tail 100
pct exec 170 -- docker logs waha --since 10m
```

### Restart container

```bash
pct exec 170 -- docker restart waha
# tunggu ~10 detik, cek session balik ke WORKING
```

### Update WAHA

```bash
pct exec 170 -- bash -c '
  docker pull devlikeapro/waha:latest
  docker stop waha && docker rm waha
  API_KEY=$(cat /root/waha-api-key)
  docker run -d --restart=unless-stopped --name waha \
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
'
```

### Monitoring health (cron)

Script untuk auto-restart kalau session jatuh:

```bash
#!/bin/bash
# /usr/local/bin/wa-healthcheck.sh — jalankan via cron tiap 5 menit
KEY="7a76d93a6809f8bb692524bf06c69d7717d3de18d36429e3"
STATUS=$(curl -s -H "X-API-Key: $KEY" http://192.168.0.170:3000/api/sessions/default | jq -r .status)
if [ "$STATUS" != "WORKING" ]; then
  echo "[$(date)] Session status: $STATUS, restarting..."
  curl -s -X POST -H "X-API-Key: $KEY" http://192.168.0.170:3000/api/sessions/default/restart
fi
```

Add to crontab:
```
*/5 * * * * /usr/local/bin/wa-healthcheck.sh >> /var/log/wa-health.log 2>&1
```

---

## 16. Error codes & troubleshooting

| HTTP | Meaning | Common cause |
|---|---|---|
| 200 | Success | - |
| 201 | Created | Session/group created |
| 401 | Unauthorized | API key salah / hilang |
| 404 | Not Found | Session/chatId tidak ada |
| 422 | Unprocessable Entity | Body JSON salah, atau session dengan nama itu sudah exist |
| 500 | Internal Error | Engine crash, biasanya butuh restart session |
| 503 | Service Unavailable | Session belum WORKING (masih SCAN_QR_CODE/STARTING) |

### Status WORKING tapi pesan tidak terkirim

1. Cek `chatId` format — pastikan `<phone>@c.us` (bukan group `@g.us`)
2. Cek `check-exists` — nomor terdaftar di WA?
3. Cek logs container: `pct exec 170 -- docker logs waha --tail 50`
4. Cek session masih connected: `curl .../api/sessions/default | jq .status`

### "Couldn't link device" saat scan QR

Coba urutan ini (yang paling sering sukses ke atas):
1. **NOWEB engine + phone code pairing** ⭐
2. WEBJS engine + phone code
3. NOWEB engine + QR scan
4. WEBJS engine + QR scan

Switch engine: hapus session + create ulang dengan `WHATSAPP_DEFAULT_ENGINE` env atau `config.engine` di POST body.

### Session sering disconnect

- Pastikan CT 170 tidak suspend / freeze
- Cek RAM cukup (NOWEB ~250 MB, WEBJS ~800 MB)
- Cek koneksi internet stabil
- HP nomor bot harus tetap online (kalau HP mati >14 hari, session expired)

### Rate-limit & anti-ban

- Max **5 pesan per menit** ke nomor sama
- Max **50 pesan per hari** total dari bot (untuk nomor baru)
- **Save kontak target di HP bot** dulu sebelum kirim
- Pesan **tidak boleh terlihat spam** (kata "promo", "discount", "click", URL gelap)
- Backup channel — kalau gagal, fallback ke SMS/email

---

## 17. Glossary

| Istilah | Arti |
|---|---|
| **session** | 1 nomor WhatsApp yang di-link ke WAHA. Multiple session = multiple nomor. |
| **chatId** | ID chat. Individual: `phone@c.us`. Group: `groupid@g.us`. Channel: `id@newsletter`. |
| **engine** | Library backend: NOWEB (whatsmeow Go), WEBJS (Chromium + WhatsApp Web). |
| **ack** | Delivery acknowledgment: -1=PENDING, 0=SERVER, 1=DEVICE, 2=READ, 3=PLAYED |
| **lid** | Linked ID — anonymous ID baru WhatsApp untuk privacy. |
| **pushName** | Nama display di profil WA. |
| **NOWEB** | Engine tanpa browser, lebih ringan, kadang reject saat link. |
| **WEBJS** | Engine pakai Chromium, mirror WhatsApp Web. Lebih reliable link tapi RAM besar. |

---

## 18. Referensi eksternal

- WAHA official: https://waha.devlike.pro
- WAHA repo: https://github.com/devlikeapro/waha
- WhatsApp Cloud API (legit, ≤1000 conv/bulan free): https://developers.facebook.com/docs/whatsapp/cloud-api
- whatsapp-web.js (WEBJS underlying lib): https://wwebjs.dev
- whatsmeow (NOWEB underlying lib): https://github.com/tulir/whatsmeow

---

_Dokumentasi ini berlaku untuk WAHA Community 2026.5.1 yang berjalan di CT 170 Proxmox._
