🎉 WORKING + OTP terkirim — cek WhatsApp Anda sekarang, harusnya muncul pesan test OTP 847362.

  Status confirmed:
  - Session: WORKING
  - Identity: Diki Haryadi / 6289612748740
  - Engine: NOWEB (yang akhirnya berhasil — kombinasi NOWEB + phone code yang break the issue)
  - Message status: PENDING → akan jadi DELIVERED setelah HP target terima

⏺ Setup lengkap WAHA — siap production-ish

  Akses

  ┌────────────────┬────────────────────────────────────────────────────────────────┐
  │      Item      │                             Value                              │
  ├────────────────┼────────────────────────────────────────────────────────────────┤
  │ API base       │ http://192.168.0.170:3000                                      │
  ├────────────────┼────────────────────────────────────────────────────────────────┤
  │ Dashboard      │ http://192.168.0.170:3000/dashboard (login admin / Sudimara19) │
  ├────────────────┼────────────────────────────────────────────────────────────────┤
  │ API Key        │ 7a76d93a6809f8bb692524bf06c69d7717d3de18d36429e3               │
  ├────────────────┼────────────────────────────────────────────────────────────────┤
  │ Engine         │ NOWEB (whatsmeow Go)                                           │
  ├────────────────┼────────────────────────────────────────────────────────────────┤
  │ Session        │ default linked ke 6289612748740                                │
  ├────────────────┼────────────────────────────────────────────────────────────────┤
  │ HTTPS optional │ https://wa.lab.lan (sudah disetup, butuh DNS+CA di client)     │
  └────────────────┴────────────────────────────────────────────────────────────────┘

  Helper script kirim OTP

  Saya saran simpan ini di backend Anda atau jadikan service kecil:

  #!/bin/bash
  # send-otp.sh <phone> <code>
  WAHA_URL="http://192.168.0.170:3000"
  WAHA_KEY="7a76d93a6809f8bb692524bf06c69d7717d3de18d36429e3"
  PHONE=$1  # e.g. 6281234567890
  CODE=$2   # e.g. 123456

  curl -X POST "$WAHA_URL/api/sendText" \
    -H "X-API-Key: $WAHA_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"session\":\"default\",\"chatId\":\"$PHONE@c.us\",\"text\":\"Kode OTP: $CODE\\nBerlaku 5 menit. Jangan share.\"}"

  Python integration

  import requests, secrets, os

  WAHA = "http://192.168.0.170:3000"
  KEY = os.environ["WAHA_API_KEY"]

  def send_otp(phone: str) -> str:
      code = f"{secrets.randbelow(900000) + 100000}"
      requests.post(
          f"{WAHA}/api/sendText",
          headers={"X-API-Key": KEY, "Content-Type": "application/json"},
          json={
              "session": "default",
              "chatId": f"{phone}@c.us",
              "text": f"Kode OTP: {code}\nBerlaku 5 menit. Jangan share.",
          },
          timeout=10,
      ).raise_for_status()
      return code  # simpan ke DB/Redis dengan TTL 5 menit

  Tips supaya nomor bot tidak kena ban

  1. Save kontak target dulu di HP bot sebelum kirim (atau minimal pernah chat → masuk address book)
  2. Rate-limit di backend Anda:
    - Max 3 OTP/jam/nomor target
    - Max 50 OTP/hari total dari bot ini
  3. Jangan kirim ke nomor random/scraped — selalu user yang request
  4. Vary timing — jangan kirim per-detik berurutan
  5. Avoid kata-kata spam — pesan natural seperti contoh di atas OK
  6. Backup channel: kalau kirim WA gagal, fallback ke SMS atau Email

  Ops

  # logs realtime
  pct exec 170 -- docker logs waha -f

  # restart kalau hang
  pct exec 170 -- docker restart waha

  # session status
  curl -s -H "X-API-Key: $KEY" http://192.168.0.170:3000/api/sessions/default | jq .status

  # logout (untuk re-link nomor lain)
  curl -X POST -H "X-API-Key: $KEY" http://192.168.0.170:3000/api/sessions/default/logout

  # backup session data (penting — biar tidak perlu scan ulang kalau CT crash)
  pct exec 170 -- docker run --rm -v waha_sessions:/data -v /tmp:/backup alpine \
    tar czf /backup/waha-session-$(date +%Y%m%d).tgz /data
  pct pull 170 /tmp/waha-session-*.tgz /var/backups/

  Catatan terakhir

  Anda berhasil di kombinasi NOWEB + phone code pairing. Save kombinasi ini sebagai catatan — kalau nanti session disconnect dan harus
  re-link, mulai dari NOWEB dulu (jangan WEBJS). Engine WEBJS memang kadang ditolak dengan "Couldn't link device" sekarang.

  Selamat — bot WhatsApp OTP siap dipakai!

✻ Sautéed for 1m 45s