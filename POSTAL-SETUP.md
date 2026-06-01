# Postal SMTP Server — Setup Runbook

Panduan step-by-step setup self-hosted SMTP relay (transactional + multi-tenant API) di Proxmox LXC.

**Target setup:**
- CT 200 `mail` (Debian 12 privileged, 2.5 GB RAM, 16 GB disk)
- IP statis `192.168.0.200`
- **Postal 3.3.6** + **MariaDB 10.11** (native) + Docker untuk Postal services
- HTTPS via Caddy + DNS Pi-hole (`postal.lab.lan`)
- SMTP submission via port 25 + bridge `socat` 5001 → 5000 untuk web

**Estimasi waktu:** 20–25 menit + waktu untuk konfigurasi DNS publik domain mail Anda

---

## ⚠️ Peringatan realistis sebelum setup

Self-hosted SMTP untuk **production** (apalagi "jualan ke customer") punya tantangan besar:

| Faktor | Detail |
|---|---|
| **Port 25 outbound** | ISP residensial Indonesia (Indihome, MyRepublic, Biznet) **memblok port 25** untuk anti-spam. Anda **tidak bisa kirim langsung** dari rumah ke Gmail/Outlook. |
| **Port 25 inbound** | Diblock juga. MX record publik tidak bisa point ke IP rumah. |
| **VPS provider** | Banyak provider (Vultr, DO, Hetzner) default block port 25 outbound. AWS/GCP butuh kuota khusus. OVH dan beberapa kecil masih izinkan. |
| **IP reputation** | Gmail/Outlook throttle IP baru. Butuh IP warming weeks-to-months. Sekali masuk blacklist (Spamhaus), recovery sulit. |
| **Reverse DNS (PTR)** | Wajib match HELO. Hanya bisa diset oleh provider IP. |
| **Customer trust** | Customer expect 99%+ delivery rate. Bare-metal SMTP self-hosted sering kalah dari Postmark/SendGrid yang charge $20–100+/bulan karena IP rep + ops mahal. |

**Realistis di setup ini:**

| Use case | Feasible? |
|---|---|
| **Dev SMTP, test internal** | ✅ Sangat |
| **Transactional via VPS relay** | 🟡 Bisa, butuh VPS + warming |
| **Sell SMTP API ke customer** | ⚠️ Bisa secara software, tapi success rate tergantung IP infra di luar Postal sendiri |
| **Full mail server (receive)** | ❌ Tidak realistis dari residential |

---

## Prasyarat

- [x] Proxmox VE 8.x+ / 9.x
- [x] Storage ≥ 16 GB free
- [x] Host RAM ≥ 2.5 GB available
- [x] Template Debian 12
- [x] Pi-hole CT 150 + Caddy CT 151 (untuk HTTPS internal)
- [x] (Untuk production) Domain dengan akses penuh ke DNS records
- [x] (Untuk production) VPS dengan IP public + port 25 outbound enabled
- [x] (Optional) Rathole CT 100 sudah terhubung ke VPS untuk tunnel inbound

---

## Step 1 — Create CT 200

```bash
pct create 200 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname mail \
  --cores 2 --memory 2560 --swap 1024 \
  --rootfs local-lvm:16 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.0.200/24,gw=192.168.0.1,firewall=0 \
  --nameserver 192.168.0.150 \
  --features nesting=1,keyctl=1 \
  --unprivileged 0 --onboot 1 \
  --password 'GANTI_PASSWORD' --start 1
```

Verifikasi:
```bash
pct exec 200 -- bash -c 'echo nameserver 1.1.1.1 > /etc/resolv.conf; ip -4 addr show eth0 | grep inet; ping -c 1 -W 2 1.1.1.1 && echo OK'
```

---

## Step 2 — Install Docker + tools

```bash
pct exec 200 -- bash -c '
set -e
export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
apt-get install -y --no-install-recommends \
  ca-certificates curl gnupg git jq socat

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list

apt-get update -qq
apt-get install -y --no-install-recommends docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable --now docker
docker --version
'
```

---

## Step 3 — Remove default postfix (port 25 conflict)

Debian 12 sering punya postfix terinstall yang bind port 25 — block Postal.

```bash
pct exec 200 -- bash -c '
systemctl stop postfix 2>/dev/null
DEBIAN_FRONTEND=noninteractive apt-get remove -y postfix
ss -tlnp | grep :25 || echo "port 25 free"
'
```

---

## Step 4 — Install MariaDB native

Postal v3 perlu MariaDB tapi tidak ship Docker image untuk-nya. Install native.

```bash
pct exec 200 -- bash -c '
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends mariadb-server
systemctl enable --now mariadb

# bind ke semua interface biar container Postal bisa konek via 172.17.0.1
sed -i "s/^bind-address.*=.*/bind-address = 0.0.0.0/" /etc/mysql/mariadb.conf.d/50-server.cnf
systemctl restart mariadb

ss -tlnp | grep 3306
'
```

---

## Step 5 — Create Postal MariaDB user (grant untuk 127.0.0.1 DAN % wildcard)

**Penting:** Postal containers konek dari Docker bridge (172.17.0.x), bukan dari 127.0.0.1. Grant untuk `%` wajib.

```bash
pct exec 200 -- bash -c '
DB_PASS=$(openssl rand -hex 16)
echo "$DB_PASS" > /root/postal-db-pass
chmod 600 /root/postal-db-pass

mysql <<EOF
CREATE USER IF NOT EXISTS "postal"@"127.0.0.1" IDENTIFIED BY "$DB_PASS";
CREATE USER IF NOT EXISTS "postal"@"%" IDENTIFIED BY "$DB_PASS";
GRANT ALL ON \`postal\`.* TO "postal"@"127.0.0.1" WITH GRANT OPTION;
GRANT ALL ON \`postal-%\`.* TO "postal"@"127.0.0.1" WITH GRANT OPTION;
GRANT ALL ON \`postal\`.* TO "postal"@"%" WITH GRANT OPTION;
GRANT ALL ON \`postal-%\`.* TO "postal"@"%" WITH GRANT OPTION;
FLUSH PRIVILEGES;
EOF
echo "DB password saved to /root/postal-db-pass"
'
```

---

## Step 6 — Clone Postal install scripts

```bash
pct exec 200 -- bash -c '
git clone https://github.com/postalserver/install /opt/postal/install
ln -s /opt/postal/install/bin/postal /usr/bin/postal
'
```

---

## Step 7 — Bootstrap config

**Catatan:** Argument urutan dengan path eksplisit supaya config landing di `/opt/postal/config`:

```bash
pct exec 200 -- bash -c '
mkdir -p /opt/postal/config
postal bootstrap postal.lab.lan /opt/postal/config
ls /opt/postal/config/
'
```

Expected output:
```
Caddyfile
postal.yml
signing.key
```

Set env var permanen:
```bash
pct exec 200 -- bash -c '
echo "export POSTAL_CONFIG_ROOT=/opt/postal/config" > /etc/profile.d/postal.sh
'
```

---

## Step 8 — Patch postal.yml dengan credentials

```bash
pct exec 200 -- bash -c '
DB_PASS=$(cat /root/postal-db-pass)

python3 <<EOF
import re
cfg_path = "/opt/postal/config/postal.yml"
content = open(cfg_path).read()
HOST = "172.17.0.1"
DB = "$DB_PASS"

# main_db
content = re.sub(r"(main_db:\s*\n  host:)\s*\S+", lambda m: m.group(1) + " " + HOST, content, count=1)
content = re.sub(r"(main_db:[\s\S]*?username:)\s*\S+", lambda m: m.group(1) + " postal", content, count=1)
content = re.sub(r"(main_db:[\s\S]*?password:)\s*\S+", lambda m: m.group(1) + " " + DB, content, count=1)

# message_db
content = re.sub(r"(message_db:\s*\n  host:)\s*\S+", lambda m: m.group(1) + " " + HOST, content, count=1)
content = re.sub(r"(message_db:[\s\S]*?username:)\s*\S+", lambda m: m.group(1) + " postal", content, count=1)
content = re.sub(r"(message_db:[\s\S]*?password:)\s*\S+", lambda m: m.group(1) + " " + DB, content, count=1)

open(cfg_path, "w").write(content)
print("OK")
EOF
'
```

Verify:
```bash
pct exec 200 -- grep -A4 -E "^(main_db|message_db):" /opt/postal/config/postal.yml
```

---

## Step 9 — Initialize DB schema

```bash
pct exec 200 -- bash -c '
export POSTAL_CONFIG_ROOT=/opt/postal/config
postal initialize
'
```

Expected: `Loading schema with db:schema:load` dan exit 0.

---

## Step 10 — Start Postal stack

```bash
pct exec 200 -- bash -c '
export POSTAL_CONFIG_ROOT=/opt/postal/config
postal start
sleep 8
docker ps --format "{{.Names}}  {{.Status}}" | grep postal
'
```

Expected: 3 container running (postal-web-1, postal-smtp-1, postal-worker-1).

---

## Step 11 — socat bridge untuk web port

Postal web binds **hanya ke 127.0.0.1:5000** (anti misconfigurasi). Caddy CT 151 tidak bisa reach. Buat bridge `0.0.0.0:5001 → 127.0.0.1:5000`:

```bash
pct exec 200 -- bash -c '
cat > /etc/systemd/system/postal-web-bridge.service <<EOF
[Unit]
Description=Postal web port bridge 0.0.0.0:5001 -> 127.0.0.1:5000
After=network.target

[Service]
ExecStart=/usr/bin/socat TCP-LISTEN:5001,bind=0.0.0.0,fork,reuseaddr TCP:127.0.0.1:5000
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now postal-web-bridge
ss -tlnp | grep 5001
'
```

---

## Step 12 — DNS + Caddy HTTPS

### 12a. Pi-hole record

```bash
# di Proxmox host
pct exec 150 -- /usr/bin/pihole-FTL --config dns.hosts \
  '[ ..."192.168.0.151 postal.lab.lan"... ]'
pct exec 150 -- systemctl restart pihole-FTL
```

### 12b. Caddy block

Penting: butuh `header_up Host postal.lab.lan` karena Postal cek Host header (anti-CSRF).

```bash
pct exec 151 -- bash -c '
cat >> /etc/caddy/Caddyfile <<EOF

postal.lab.lan {
    tls internal
    reverse_proxy 192.168.0.200:5001 {
        header_up Host postal.lab.lan
    }
}
EOF
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy
'
```

Verify dari Proxmox host:
```bash
curl -sI --cacert /tmp/lab-lan-ca.crt \
  --resolve postal.lab.lan:443:192.168.0.151 \
  https://postal.lab.lan/ | head -3
# expected: HTTP/2 302 (redirect ke login)
```

---

## Step 13 — Create admin user

```bash
pct exec 200 -- bash -c '
export POSTAL_CONFIG_ROOT=/opt/postal/config
postal make-user <<INPUT
admin@lab.lan
Admin
Postal
Sudimara19
Sudimara19
INPUT
'
```

Expected: `User has been created with e-mail address admin@lab.lan`

---

## Step 14 — Login + buat organization pertama

Buka `https://postal.lab.lan` (atau `http://192.168.0.200:5001` kalau HTTPS belum siap di client).

Login: `admin@lab.lan` / `Sudimara19`.

1. Buat **Organization** baru — represent 1 tenant/customer
2. Dalam org, buat **Mail Server** — represent 1 domain pengirim
3. Add **domain** → Postal generate DNS records yang harus disetup di DNS publik:
   - **SPF** TXT: `v=spf1 include:spf.postal.your-mail-domain.com -all`
   - **DKIM** TXT: `postal-<server>._domainkey ... v=DKIM1; ...`
   - **MX** (return-path): point ke server Postal Anda
   - **CNAME** untuk track domain (untuk click/open tracking)
4. **Verify** DNS — Postal akan polling tiap beberapa menit
5. Generate **credentials** untuk customer (SMTP user/password OR API key)

---

## Step 15 — (Production) Rathole tunnel untuk SMTP inbound dari VPS

### 15a. Edit rathole client di CT 100

```bash
pct exec 100 -- bash -c '
cat >> /config/client.toml <<EOF

[client.services.postal_smtp]
token = "GANTI_TOKEN_SECURE_DI_SINI"
local_addr = "192.168.0.200:25"
EOF
systemctl restart rathole 2>/dev/null || docker restart rathole
'
```

### 15b. Edit rathole-server di VPS (`103.93.129.161` di setup ini)

SSH ke VPS, edit rathole-server config:
```toml
[server.services.postal_smtp]
token = "SAMA_DENGAN_CLIENT"
bind_addr = "0.0.0.0:25"   # atau 587 / 2525 kalau port 25 di-block
```

### 15c. Open port 25 di VPS firewall

```bash
# di VPS
ufw allow 25/tcp     # atau 587, 2525
```

**Note:** Port 25 outbound di VPS mungkin butuh request ke provider. Cek:
- DigitalOcean: support ticket
- Hetzner: enabled by default + ada anti-abuse limit
- Vultr: support ticket  
- AWS EC2: kuota khusus, butuh approval
- OVH: enabled by default

### 15d. MX record domain customer

Di DNS public domain customer/Anda:
```
MX  mail.your-domain.com   priority=10   value=mx.postal.your-domain.com
A   mx.postal.your-domain.com   value=<VPS_IP>
```

Inbound mail flow: external → VPS:25 → rathole tunnel → Postal CT 200:25.

---

## Step 16 — Smoke test

### Send test message via Postal CLI

```bash
pct exec 200 -- bash -c '
export POSTAL_CONFIG_ROOT=/opt/postal/config
postal test-app-smtp recipient@example.com
'
```

### Send via API (setelah generate credential di UI)

```bash
curl -X POST https://postal.lab.lan/api/v1/send/message \
  -H "X-Server-API-Key: <CREDENTIAL_FROM_UI>" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["test@example.com"],
    "from": "noreply@your-domain.com",
    "subject": "Test from Postal",
    "plain_body": "Hello World!"
  }'
```

### Send via SMTP submission (real client)

```python
import smtplib

with smtplib.SMTP("postal.lab.lan", 25) as s:
    s.starttls()
    s.login("<smtp-username-from-ui>", "<smtp-password-from-ui>")
    s.sendmail("noreply@your-domain.com", "test@example.com",
               "Subject: Test\n\nHello!")
```

---

## Step 17 — Backup & maintenance

### Backup MariaDB + config

```bash
pct exec 200 -- bash -c '
DATE=$(date +%Y%m%d)
mkdir -p /var/backups/postal

# database dump
mysqldump -u postal -p$(cat /root/postal-db-pass) postal > /var/backups/postal/postal-$DATE.sql
for db in $(mysql -e "SHOW DATABASES" | grep "^postal-"); do
  mysqldump -u postal -p$(cat /root/postal-db-pass) $db > /var/backups/postal/$db-$DATE.sql
done

# config + signing key
tar czf /var/backups/postal/config-$DATE.tgz -C /opt/postal config/

ls -la /var/backups/postal/
'
```

### Cron weekly

```bash
# di Proxmox host
echo '0 3 * * 0 pct exec 200 -- /usr/local/bin/postal-backup.sh' | crontab -
```

### Logs

```bash
pct exec 200 -- bash -c '
export POSTAL_CONFIG_ROOT=/opt/postal/config
postal logs web --tail 50
postal logs smtp --tail 50
postal logs worker --tail 50
'
```

### Update Postal

```bash
pct exec 200 -- bash -c '
export POSTAL_CONFIG_ROOT=/opt/postal/config
postal stop
postal upgrade
postal start
'
```

---

## Troubleshooting

| Gejala | Cek | Fix |
|---|---|---|
| `port 25 already in use` | `ss -tlnp \| grep :25` | Remove postfix: `apt-get remove -y postfix` |
| `db:create` failed | grant MySQL `postal@%` | `GRANT ... TO "postal"@"%"` |
| MariaDB connection refused | bind-address di config | Set `bind-address = 0.0.0.0` |
| Container reach 172.17.0.1 fail | docker0 routing | Restart docker, check `ip route` |
| 403 Forbidden di web | Host header mismatch | Caddy: `header_up Host postal.lab.lan` |
| HTTPS cert fail | CA tidak trusted di Mac | Install root CA dari `http://ca.lab.lan/root.crt` |
| Mail kena spam folder di Gmail | SPF/DKIM/PTR | Setup semua DNS + IP warming |
| Bounces / blacklisted | IP reputation | Cek MXToolbox + Spamhaus + warming history |
| Stuck at "Validating" domain | DNS belum propagate | Tunggu 5–15 menit, atau cek `dig` |

---

## Yang JANGAN dilakukan

❌ **Jangan kirim mass bulk dari hari pertama** — IP rep langsung kena flag
❌ **Jangan beli VPS shared IP** — IP rep sudah jelek dari user sebelumnya
❌ **Jangan pakai domain yang sudah dipakai untuk spam** — bawa baggage
❌ **Jangan skip DMARC** — Gmail/Outlook akan reject mail tanpa DMARC enforcement
❌ **Jangan share API key di Git** — pakai env / vault
❌ **Jangan expose port 5000 atau 5001 ke internet** — UI cuma untuk admin/internal
❌ **Jangan disable verification kewarganegaraan** kalau user belum scan QR (Postal anti-bot fail kalau tampak suspicious)

---

## Checklist akhir

- [ ] CT 200 running
- [ ] Docker active
- [ ] MariaDB active + postal user grants OK
- [ ] postfix removed (port 25 free)
- [ ] `postal initialize` exit 0
- [ ] `postal start` semua 3 container Up
- [ ] socat bridge :5001 → :5000 active
- [ ] DNS `postal.lab.lan` resolve ke Caddy
- [ ] Caddy proxy passing dengan Host header
- [ ] HTTPS test return 302
- [ ] Admin user created
- [ ] Login web OK
- [ ] First organization + mail server created
- [ ] DNS records publik untuk domain mail set (SPF/DKIM/MX/track)
- [ ] (Production) Rathole tunnel ke VPS configured
- [ ] (Production) VPS port 25 outbound enabled
- [ ] (Production) Backup cron setup

---

## Konfigurasi instance ini (referensi)

| Item | Value |
|---|---|
| CT ID | 200 |
| Hostname | mail |
| IP | 192.168.0.200 |
| Resources | 2 core, 2.5 GB RAM, 1 GB swap, 16 GB disk |
| OS | Debian 12 (privileged LXC) |
| Postal version | 3.3.6 |
| MariaDB | 10.11.14 (native) |
| Docker | latest |
| Web URL HTTPS | https://postal.lab.lan |
| Web URL HTTP direct | http://192.168.0.200:5001 (via socat bridge) |
| Internal web | 127.0.0.1:5000 |
| SMTP submission | port 25 |
| Admin login | admin@lab.lan / Sudimara19 |
| DB password | `/root/postal-db-pass` |
| Config | `/opt/postal/config/postal.yml` |
| Signing key | `/opt/postal/config/signing.key` |

---

## Selanjutnya

- Lihat **POSTAL-API.md** untuk reference endpoint REST + integration example
- (Production) Setup IP warming schedule
- Setup monitoring: Google Postmaster, MS SNDS, Spamhaus check
- Build customer-facing signup (kalau "jualan")
- Setup bounce/complaint webhook handler

---

_Setup runbook diuji di Proxmox VE 9.1.7, Postal 3.3.6, MariaDB 10.11.14, Docker 29.5.2, 30 Mei 2026._
