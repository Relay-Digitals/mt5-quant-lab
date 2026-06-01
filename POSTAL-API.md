# Postal API Reference

Dokumentasi REST API + SMTP submission + webhook event untuk Postal SMTP relay di CT 200.

**Versi:** Postal 3.3.6 (CORE community)
**Web base:** `https://postal.lab.lan` (internal) atau `https://your-public-postal-host.com` (production via rathole)

---

## Konsep dasar Postal

```
Postal Admin (you)
   ├── Organization 1 (= customer 1)
   │   ├── Mail Server A (= 1 sending domain)
   │   │   ├── Credentials (SMTP user/pass + API key)
   │   │   └── Domain (your-domain.com) → DNS records
   │   └── Mail Server B
   ├── Organization 2 (= customer 2)
   └── ...
```

Setiap **Mail Server** punya **Credentials** untuk authentication. Credentials bisa berupa:
- **SMTP user + password** — untuk SMTP submission tradisional
- **API key** — untuk REST API send

---

## Bagian 1 — REST API: Send Message

Endpoint utama untuk kirim mail via HTTP API.

### POST `/api/v1/send/message`

```bash
curl -X POST https://postal.lab.lan/api/v1/send/message \
  -H "X-Server-API-Key: <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["recipient@example.com"],
    "cc": [],
    "bcc": [],
    "from": "noreply@your-domain.com",
    "sender": null,
    "subject": "Hello from Postal",
    "tag": "transactional",
    "reply_to": null,
    "plain_body": "Hello!\n\nThis is a plain text body.",
    "html_body": "<p>Hello!</p>",
    "attachments": [],
    "headers": {
      "X-Custom-Header": "value"
    },
    "bounce": false
  }'
```

**Response (success):**
```json
{
  "status": "success",
  "time": 0.045,
  "flags": {},
  "data": {
    "message_id": "12345",
    "messages": {
      "recipient@example.com": {
        "id": 12345,
        "token": "abc123def456"
      }
    }
  }
}
```

**Response (error):**
```json
{
  "status": "error",
  "time": 0.005,
  "flags": {},
  "data": {
    "code": "ValidationError",
    "message": "from is required"
  }
}
```

### Field reference

| Field | Type | Required | Notes |
|---|---|---|---|
| `to` | string[] | ✅ | Email addresses |
| `cc` | string[] | — | Carbon copy |
| `bcc` | string[] | — | Blind CC |
| `from` | string | ✅ | Must match verified domain di mail server |
| `sender` | string | — | Override sender (untuk DKIM split) |
| `subject` | string | ✅ | Subject line |
| `tag` | string | — | Untuk grouping di analytics (e.g., "otp", "welcome", "newsletter") |
| `reply_to` | string | — | Override Reply-To header |
| `plain_body` | string | * | Salah satu plain/html wajib |
| `html_body` | string | * | Salah satu plain/html wajib |
| `attachments` | object[] | — | Lihat di bawah |
| `headers` | object | — | Custom headers (X-prefix recommended) |
| `bounce` | bool | — | Mark sebagai bounce response (rare) |

### Attachments

```json
{
  "attachments": [
    {
      "name": "invoice.pdf",
      "content_type": "application/pdf",
      "data": "<base64>"
    }
  ]
}
```

### POST `/api/v1/send/raw`

Untuk raw RFC822 message dengan headers + body manual.

```bash
curl -X POST https://postal.lab.lan/api/v1/send/raw \
  -H "X-Server-API-Key: <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "mail_from": "noreply@your-domain.com",
    "rcpt_to": ["recipient@example.com"],
    "data": "<base64-encoded full RFC822 message>"
  }'
```

---

## Bagian 2 — REST API: Read Messages

### GET `/api/v1/messages`

List messages dengan filter.

```bash
curl "https://postal.lab.lan/api/v1/messages?from=noreply@your-domain.com&status=Sent&limit=20" \
  -H "X-Server-API-Key: <API_KEY>"
```

Query params:
- `from`, `to`, `subject` — filter
- `status` — `Held`, `Sent`, `SoftFail`, `HardFail`, `Bounced`
- `tag` — filter by tag
- `limit`, `offset` — pagination

### GET `/api/v1/messages/{id}`

Detail single message.

```bash
curl "https://postal.lab.lan/api/v1/messages/12345" \
  -H "X-Server-API-Key: <API_KEY>"
```

Response include: full headers, body, delivery attempts, status timeline.

### GET `/api/v1/messages/{id}/deliveries`

History delivery attempts.

```bash
curl "https://postal.lab.lan/api/v1/messages/12345/deliveries" \
  -H "X-Server-API-Key: <API_KEY>"
```

Response:
```json
[
  {
    "id": 1,
    "status": "Sent",
    "details": "250 2.0.0 OK",
    "output": "...",
    "sent_with_ssl": true,
    "log_id": "abc123",
    "timestamp": 1780125000
  }
]
```

### GET `/api/v1/messages/{id}/activity`

Open + click tracking events.

---

## Bagian 3 — SMTP Submission

Untuk legacy app yang pakai SMTP biasa.

### Connection details

```
Host:      postal.lab.lan (atau IP)
Port:      25 (STARTTLS) atau 587 (submission) atau 465 (SMTPS)
Username:  <smtp-username> (dari mail server credentials)
Password:  <smtp-password>
Encryption: STARTTLS atau SSL/TLS
```

### Python smtplib example

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

msg = MIMEMultipart("alternative")
msg["Subject"] = "Hello from Postal"
msg["From"] = "noreply@your-domain.com"
msg["To"] = "recipient@example.com"
msg["X-Tag"] = "transactional"

msg.attach(MIMEText("Hello plain!", "plain"))
msg.attach(MIMEText("<p>Hello HTML!</p>", "html"))

with smtplib.SMTP("postal.lab.lan", 587) as s:
    s.starttls()
    s.login("smtp-username", "smtp-password")
    s.send_message(msg)
```

### Node.js nodemailer

```javascript
import nodemailer from "nodemailer";

const transport = nodemailer.createTransport({
  host: "postal.lab.lan",
  port: 587,
  secure: false,
  requireTLS: true,
  auth: {
    user: "smtp-username",
    pass: "smtp-password",
  },
});

await transport.sendMail({
  from: '"Sender Name" <noreply@your-domain.com>',
  to: "recipient@example.com",
  subject: "Hello",
  text: "Plain body",
  html: "<p>HTML body</p>",
  headers: { "X-Tag": "transactional" },
});
```

### PHP (PHPMailer)

```php
use PHPMailer\PHPMailer\PHPMailer;

$mail = new PHPMailer(true);
$mail->isSMTP();
$mail->Host = 'postal.lab.lan';
$mail->Port = 587;
$mail->SMTPAuth = true;
$mail->Username = 'smtp-username';
$mail->Password = 'smtp-password';
$mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;

$mail->setFrom('noreply@your-domain.com', 'Sender');
$mail->addAddress('recipient@example.com');
$mail->Subject = 'Hello';
$mail->Body = 'Plain body';
$mail->isHTML(false);

$mail->send();
```

### Go (net/smtp)

```go
import "net/smtp"

auth := smtp.PlainAuth("", "smtp-username", "smtp-password", "postal.lab.lan")
msg := []byte("From: noreply@your-domain.com\r\nTo: recipient@example.com\r\nSubject: Hello\r\n\r\nPlain body")
err := smtp.SendMail("postal.lab.lan:587", auth, "noreply@your-domain.com",
                     []string{"recipient@example.com"}, msg)
```

---

## Bagian 4 — Webhook Events

Postal kirim HTTP POST ke webhook URL Anda saat ada event.

### Config webhook

Di Postal UI: Mail Server → Webhooks → Add webhook
- URL: `https://your-backend.com/postal-webhook`
- Events: pilih (atau "All Events")

### Event types

| Event | Trigger |
|---|---|
| `MessageSent` | Mail berhasil delivered ke recipient server |
| `MessageDelayed` | Sementara gagal, akan retry |
| `MessageDeliveryFailed` | Permanen gagal (bounce) |
| `MessageHeld` | Held untuk review (admin must approve) |
| `MessageBounced` | Recipient bounce notification received |
| `MessageLinkClicked` | Recipient klik tracked link |
| `MessageLoaded` | Recipient buka email (open tracking) |
| `MessageSpamComplaint` | Recipient mark sebagai spam |
| `DomainDNSCheckSucceeded` | Domain DNS records verified |
| `DomainDNSCheckFailed` | DNS records tidak match |

### Payload format

```json
{
  "event": "MessageSent",
  "timestamp": 1780125000,
  "payload": {
    "message": {
      "id": 12345,
      "token": "abc123",
      "direction": "outgoing",
      "message_id": "<abc@your-domain.com>",
      "to": "recipient@example.com",
      "from": "noreply@your-domain.com",
      "subject": "Hello",
      "timestamp": 1780124900,
      "spam_status": "NotSpam",
      "tag": "transactional"
    },
    "status": "Sent",
    "details": "250 2.0.0 Ok",
    "output": "...",
    "sent_with_ssl": true,
    "time": 0.532
  },
  "uuid": "..."
}
```

### Verify webhook signature

Postal sign webhook dengan signing key.

```python
import hmac, hashlib, base64

def verify(body: bytes, signature: str, secret: str) -> bool:
    expected = base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha1).digest()
    ).decode()
    return hmac.compare_digest(expected, signature)
```

Header dari Postal: `X-Postal-Signature: <base64-hmac-sha1>`

---

## Bagian 5 — Domain Setup (DNS Records)

Saat Anda add domain di Postal UI, system generate records yang harus disetup di DNS publik.

### SPF (TXT record)

Pada `your-domain.com`:
```
TXT  @  "v=spf1 include:spf.postal.your-mail-host.com -all"
```

`-all` = strict (reject yang bukan dari Postal). Pakai `~all` untuk softfail dulu kalau migrasi.

### DKIM (TXT record)

Postal generate per-server unique DKIM key. Set di:
```
TXT  postal-<random>._domainkey.your-domain.com  "v=DKIM1; t=s; h=sha256; p=<public-key>"
```

### Return Path (CNAME)

```
CNAME  rp.your-domain.com  →  rp.postal.your-mail-host.com
```

### Tracking (CNAME)

Untuk open/click tracking:
```
CNAME  track.your-domain.com  →  track.postal.your-mail-host.com
```

### MX (untuk bounce processing)

```
MX  rp.your-domain.com  priority=10  value=mx.postal.your-mail-host.com
```

### DMARC (TXT — strongly recommended)

```
TXT  _dmarc.your-domain.com  "v=DMARC1; p=quarantine; rua=mailto:dmarc@your-domain.com; pct=100"
```

Start dengan `p=none` (monitor only), upgrade ke `p=quarantine` setelah verifikasi clean.

### Reverse DNS (PTR) — Server-side

Di provider VPS (di control panel):
```
PTR  <VPS_IP>  →  mail.your-domain.com
```

Wajib match HELO/EHLO yang Postal kirim.

---

## Bagian 6 — Multi-tenant patterns

### Auto-create organization untuk customer baru (REST)

Postal **belum punya public REST API** untuk org/server management — pakai admin Rails console:

```bash
pct exec 200 -- bash -c '
export POSTAL_CONFIG_ROOT=/opt/postal/config
postal console
'
```

```ruby
# di console
org = Organization.create!(name: "Customer ACME", permalink: "acme")
server = org.servers.create!(name: "ACME Production", mode: "Live")
domain = server.domains.create!(name: "acme-mail.com")
cred = server.credentials.create!(name: "API Key", type: "API")
puts cred.key
```

### Programmatic via GraphQL (Postal 3.x+)

Postal v3 mulai expose GraphQL API. Endpoint: `/api/graphql`. Schema masih evolving.

```bash
curl -X POST https://postal.lab.lan/api/graphql \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ currentUser { id emailAddress } }"}'
```

### Quota enforcement

Postal punya **send quota** per mail server (UI: Server Settings → Limits). Set:
- Max messages per hour
- Max recipients per message
- Max bounce rate

Customer yang exceed quota → message rejected dengan error code.

---

## Bagian 7 — Integration use cases

### OTP via WhatsApp + fallback Email

```python
def send_otp(phone: str, email: str) -> str:
    code = f"{secrets.randbelow(900000) + 100000}"

    # 1. coba WhatsApp via WAHA
    try:
        send_via_waha(phone, f"OTP: {code}")
        return code
    except Exception:
        pass

    # 2. fallback email via Postal
    requests.post(
        "https://postal.lab.lan/api/v1/send/message",
        headers={"X-Server-API-Key": POSTAL_KEY, "Content-Type": "application/json"},
        json={
            "to": [email],
            "from": "noreply@your-domain.com",
            "subject": "Kode OTP Anda",
            "tag": "otp",
            "plain_body": f"Kode OTP: {code}\nBerlaku 5 menit.",
        },
        timeout=10,
    ).raise_for_status()
    return code
```

### Newsletter dengan unique tracking

```python
def send_newsletter(recipients: list[str], html: str, campaign: str):
    for email in recipients:
        requests.post(
            "https://postal.lab.lan/api/v1/send/message",
            headers={"X-Server-API-Key": POSTAL_KEY, "Content-Type": "application/json"},
            json={
                "to": [email],
                "from": "newsletter@your-domain.com",
                "subject": "Weekly Update",
                "tag": f"newsletter-{campaign}",
                "html_body": html,
                "headers": {
                    "List-Unsubscribe": f"<https://your-app/unsubscribe?email={email}>",
                    "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
                },
            },
        )
        time.sleep(0.5)  # rate limit
```

### Bounce processing webhook handler

```python
from fastapi import FastAPI, Request, HTTPException
import hmac, hashlib, base64

app = FastAPI()
SECRET = "your-signing-key"

@app.post("/postal-webhook")
async def handle(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Postal-Signature", "")

    expected = base64.b64encode(
        hmac.new(SECRET.encode(), body, hashlib.sha1).digest()
    ).decode()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(401, "Bad signature")

    data = await request.json()
    event = data["event"]
    payload = data["payload"]

    if event == "MessageBounced":
        # mark email as bounced di user DB
        db.users.update_one(
            {"email": payload["message"]["to"]},
            {"$set": {"email_bounced": True, "bounce_reason": payload["details"]}}
        )
    elif event == "MessageSpamComplaint":
        # remove from list
        db.subscribers.delete_one({"email": payload["message"]["to"]})
    elif event == "MessageDeliveryFailed":
        # log + alert
        logger.warning(f"Delivery failed: {payload}")
```

---

## Bagian 8 — IP warming schedule

Untuk IP baru, naikkan volume gradually:

| Day | Daily volume cap | Notes |
|---|---|---|
| 1–3 | 50 emails | Send hanya ke yang sudah opt-in dan engage |
| 4–7 | 100 | Add second day batches |
| 8–14 | 500 | Monitor bounce rate (<2%), spam complaint (<0.1%) |
| 15–21 | 1.000 | |
| 22–28 | 5.000 | |
| 29+ | 10.000+ | Steady state |

**Monitoring tools:**
- Google Postmaster Tools: https://postmaster.google.com
- Microsoft SNDS: https://sendersupport.olc.protection.outlook.com
- Spamhaus: https://check.spamhaus.org
- MXToolbox: https://mxtoolbox.com/blacklists.aspx

---

## Bagian 9 — Error codes & troubleshooting

### Status codes API

| Code | Meaning |
|---|---|
| 200 | Success |
| 401 | Bad/missing API key |
| 403 | API key tidak punya permission untuk mail server ini |
| 422 | Validation error (cek `data.message`) |
| 500 | Server error |

### SMTP response codes (delivery)

| Code | Meaning |
|---|---|
| `250 OK` | Delivered |
| `421 Service not available` | Recipient server temporary unavailable, akan retry |
| `450 Mailbox unavailable` | Soft fail (temporary) |
| `550 No such user` | Hard bounce — remove dari list |
| `554 Spam` | Recipient flagged as spam |

### Common issues

| Gejala | Cause | Fix |
|---|---|---|
| All mail spam folder | DKIM/SPF salah | Re-verify DNS, check DKIM signature live |
| Mail tidak sampai | Port 25 blocked di VPS | Open ticket ke provider |
| Bounce rate >5% | List quality jelek | Clean list, double opt-in only |
| Spam complaint >0.1% | Konten tidak ditunggu | Add unsubscribe link, segmen list |
| Gmail throttle | IP baru / volume spike | Slower volume increase |
| Spamhaus listed | Volume spike / bad list | Submit removal request + clean list |

---

## Referensi eksternal

- Postal docs: https://docs.postalserver.io
- Postal GitHub: https://github.com/postalserver/postal
- Email deliverability guide: https://postmarkapp.com/guides/email-deliverability
- Mail-tester (cek score): https://www.mail-tester.com
- DMARC analyzer: https://dmarcian.com
- Email on Acid (rendering test): https://www.emailonacid.com

---

_Postal API reference berlaku untuk Postal 3.3.6, deployed di CT 200 Proxmox._
