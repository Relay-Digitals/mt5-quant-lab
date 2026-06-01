# Browser Automation Stack — Setup Runbook

Panduan step-by-step setup dual-stack browser automation di Proxmox: **Browserless** (REST/WS API untuk script) + **Playwright MCP Server** (untuk LLM agent via MCP protocol). Keduanya share Chromium 148 di 1 CT.

**Target setup:**
- CT 180 `browser` (Debian 12 privileged, 2.5 GB RAM, 12 GB disk)
- IP statis `192.168.0.180`
- Docker + Node.js 20 LTS
- **Browserless** v2 community pada `:3000` (REST/WS, headless Chrome 148)
- **Playwright MCP Server** (Microsoft official) pada `:8931` (HTTP/SSE)
- Optional: HTTPS via Caddy + Pi-hole DNS (`browser.lab.lan`, `mcp.lab.lan`)
- Auto-wire ke Claude Code MCP

**Estimasi waktu:** 12–15 menit

---

## Prasyarat

- [x] Proxmox VE 8.x+ atau 9.x
- [x] Storage ≥ 12 GB free
- [x] Host RAM ≥ 2.5 GB available
- [x] Template Debian 12 di `local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst`
- [x] Network bridge ke LAN
- [x] (Optional) Pi-hole CT 150 + Caddy CT 151 untuk HTTPS via `*.lab.lan`
- [x] (Optional) Claude Code CLI di Mac untuk MCP wire-up

---

## Step 1 — Buat LXC container

```bash
pct create 180 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname browser \
  --cores 2 --memory 2560 --swap 1024 \
  --rootfs local-lvm:12 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.0.180/24,gw=192.168.0.1,firewall=0 \
  --nameserver 192.168.0.150 \
  --features nesting=1,keyctl=1 \
  --unprivileged 0 --onboot 1 \
  --password 'GANTI_PASSWORD' --start 1
```

**Penjelasan flag:**
- `--memory 2560` — Browserless ~800 MB + MCP ~400 MB + Chromium ~500 MB sisa untuk active tab
- `--rootfs local-lvm:12` — 12 GB cukup untuk Chromium + headless shell + npm deps
- `--features nesting=1` — Docker-in-LXC
- `--unprivileged 0` — Docker butuh privileged

Verifikasi:
```bash
pct exec 180 -- bash -c 'echo nameserver 1.1.1.1 > /etc/resolv.conf; ip -4 addr show eth0 | grep inet; ping -c 1 -W 2 1.1.1.1 && echo OK'
```

---

## Step 2 — Install Docker + Node.js 20

```bash
pct exec 180 -- bash -c '
set -e
export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
apt-get install -y --no-install-recommends ca-certificates curl gnupg

# Docker
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list

# Node.js 20 (LTS) via NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -

apt-get install -y --no-install-recommends docker-ce docker-ce-cli containerd.io nodejs
systemctl enable --now docker

# verify
docker --version
node --version
npm --version
'
```

Expected:
- `Docker version 27+`
- `node v20.x`
- `npm 10.x+`

---

## Step 3 — Generate token secrets

```bash
pct exec 180 -- bash -c '
openssl rand -hex 24 > /root/browserless-token
openssl rand -hex 24 > /root/mcp-token
chmod 600 /root/browserless-token /root/mcp-token
echo "Browserless: $(cat /root/browserless-token)"
echo "MCP:         $(cat /root/mcp-token)"
'
```

Token dipakai untuk auth client → server. **Simpan di password manager.**

---

## Step 4 — Install Browserless (REST/WS API)

```bash
pct exec 180 -- bash -c '
TOKEN=$(cat /root/browserless-token)

docker pull ghcr.io/browserless/chromium:latest

docker run -d --restart=unless-stopped \
  --name browserless \
  -p 3000:3000 \
  --shm-size=2gb \
  -e CONCURRENT=4 \
  -e TOKEN="$TOKEN" \
  -e MAX_CONCURRENT_SESSIONS=4 \
  -e DEFAULT_BLOCK_ADS=true \
  -e DEFAULT_LAUNCH_ARGS="[\"--disable-blink-features=AutomationControlled\", \"--no-sandbox\"]" \
  ghcr.io/browserless/chromium:latest

sleep 5
docker ps | grep browserless
'
```

**Env var penting:**

| Env | Value | Catatan |
|---|---|---|
| `TOKEN` | hex | Auth via `?token=...` di URL |
| `CONCURRENT` | `4` | Maximum simultaneous browser sessions |
| `MAX_CONCURRENT_SESSIONS` | `4` | Cap |
| `DEFAULT_BLOCK_ADS` | `true` | Block iklan untuk speed up scraping |
| `DEFAULT_LAUNCH_ARGS` | `["--disable-blink-features=AutomationControlled", "--no-sandbox"]` | Anti-detect + LXC compat |
| `--shm-size=2gb` | — | Chrome butuh shm yang besar untuk render |

Verify:
```bash
TOKEN=$(pct exec 180 -- cat /root/browserless-token)
curl -s "http://192.168.0.180:3000/json/version?token=$TOKEN" | python3 -m json.tool
```

Expected:
```json
{
  "Browser": "Chrome/148.0.7778.96",
  "Protocol-Version": "1.3",
  "webSocketDebuggerUrl": "ws://0.0.0.0:3000/",
  ...
}
```

---

## Step 5 — Install Playwright dependencies

Chromium butuh shared libraries di LXC:

```bash
pct exec 180 -- bash -c '
apt-get install -y --no-install-recommends \
  libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
  libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
  libgbm1 libpango-1.0-0 libcairo2 libasound2 fonts-liberation \
  libatspi2.0-0 libgtk-3-0 libx11-xcb1
'
```

---

## Step 6 — Install Playwright MCP Server

```bash
pct exec 180 -- bash -c '
# install Playwright MCP server globally
npm install -g @playwright/mcp@latest

# download Chromium browser binary (~113 MB)
npx playwright install chromium --with-deps
'
```

---

## Step 7 — systemd service untuk MCP

```bash
pct exec 180 -- bash -c '
cat > /etc/systemd/system/playwright-mcp.service <<EOF
[Unit]
Description=Playwright MCP Server (HTTP/SSE)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
Environment=PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright
ExecStart=/usr/bin/npx -y @playwright/mcp@latest --port 8931 --host 0.0.0.0 --headless --allowed-hosts *
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now playwright-mcp.service
sleep 5
systemctl is-active playwright-mcp.service
ss -tlnp | grep 8931
'
```

**Penting:** `--allowed-hosts *` — default Playwright MCP reject Host header yang bukan bind host (untuk anti-DNS-rebinding). Untuk LAN trust, set `*`. Untuk production internet-facing, list hostname explicit.

---

## Step 8 — (Optional) HTTPS via Caddy + Pi-hole

Skip kalau cukup HTTP intern.

### 8a. Add DNS di Pi-hole (CT 150)

```bash
pct exec 150 -- /usr/bin/pihole-FTL --config dns.hosts \
  '[ ..."192.168.0.151 browser.lab.lan", "192.168.0.151 mcp.lab.lan"... ]'
pct exec 150 -- systemctl restart pihole-FTL
```

(Append ke list existing, jangan replace.)

### 8b. Tambah Caddy proxy blocks (CT 151)

```bash
pct exec 151 -- bash -c '
cat >> /etc/caddy/Caddyfile <<EOF

# Browserless
browser.lab.lan {
    tls internal
    reverse_proxy 192.168.0.180:3000
}

# Playwright MCP
mcp.lab.lan {
    tls internal
    reverse_proxy 192.168.0.180:8931
}
EOF
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy
'
```

### 8c. Verify HTTPS

```bash
# extract root CA dari Caddy
pct exec 151 -- cat /var/lib/caddy/.local/share/caddy/pki/authorities/local/root.crt > /tmp/lab-lan-ca.crt

# test
curl --cacert /tmp/lab-lan-ca.crt --resolve browser.lab.lan:443:192.168.0.151 \
  "https://browser.lab.lan/json/version?token=$TOKEN"
```

---

## Step 9 — Wire MCP ke Claude Code

Di Mac terminal:

```bash
# add MCP server ke Claude Code config (project-level)
claude mcp add --transport http playwright-proxmox http://192.168.0.180:8931/mcp

# verify
claude mcp list
```

Expected:
```
playwright-proxmox: http://192.168.0.180:8931/mcp (HTTP) - ✓ Connected
```

**Penting:** MCP tools dimuat saat Claude Code startup. Untuk pakai sekarang:
```bash
exit         # close current Claude Code session
claude       # restart, MCP tools akan muncul
```

Setelah restart, tool yang tersedia (prefix `mcp__playwright-proxmox__`):
- `browser_navigate` — buka URL
- `browser_click` — klik element
- `browser_type` / `browser_press_key` — input
- `browser_snapshot` — accessibility tree (untuk AI lihat halaman)
- `browser_screenshot` — PNG screenshot
- `browser_evaluate` — execute JS
- `browser_wait_for` — wait element/state
- `browser_select_option` / `browser_file_upload`
- ~20+ tools

Untuk Claude Desktop / Cursor / Cline / other MCP clients, lihat **API doc** untuk config format masing-masing.

---

## Step 10 — Smoke test

### Browserless screenshot

```bash
TOKEN=$(pct exec 180 -- cat /root/browserless-token)

curl -X POST "http://192.168.0.180:3000/screenshot?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","options":{"fullPage":true}}' \
  -o /tmp/test.png

file /tmp/test.png   # harus: PNG image data
```

### Playwright via CDP from Python

```bash
pip install playwright
```

```python
from playwright.sync_api import sync_playwright

TOKEN = "<browserless-token>"
WS = f"ws://192.168.0.180:3000?token={TOKEN}"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(WS)
    page = browser.new_page()
    page.goto("https://example.com")
    print("Title:", page.title())
    page.screenshot(path="test.png")
    browser.close()
```

### MCP via Claude Code

Setelah `claude` restart, prompt:
> "Navigate to example.com using the playwright MCP, take a snapshot and tell me what's on the page."

Saya akan call `mcp__playwright-proxmox__browser_navigate` + `browser_snapshot` dan summarize.

---

## Step 11 — Backup & maintenance

### Update Browserless

```bash
pct exec 180 -- bash -c '
docker pull ghcr.io/browserless/chromium:latest
docker stop browserless && docker rm browserless
TOKEN=$(cat /root/browserless-token)
docker run -d --restart=unless-stopped \
  --name browserless \
  -p 3000:3000 \
  --shm-size=2gb \
  -e CONCURRENT=4 -e TOKEN="$TOKEN" -e MAX_CONCURRENT_SESSIONS=4 \
  -e DEFAULT_BLOCK_ADS=true \
  -e DEFAULT_LAUNCH_ARGS="[\"--disable-blink-features=AutomationControlled\",\"--no-sandbox\"]" \
  ghcr.io/browserless/chromium:latest
'
```

### Update Playwright MCP

```bash
pct exec 180 -- bash -c '
npm install -g @playwright/mcp@latest
npx playwright install chromium
systemctl restart playwright-mcp
'
```

### Logs

```bash
pct exec 180 -- docker logs browserless -f --tail 100
pct exec 180 -- journalctl -u playwright-mcp -f
```

### Health check cron (Mac atau Proxmox host)

`/usr/local/bin/browser-healthcheck.sh`:
```bash
#!/bin/bash
TOKEN=$(pct exec 180 -- cat /root/browserless-token 2>/dev/null)

# check Browserless
if ! curl -s --max-time 5 "http://192.168.0.180:3000/json/version?token=$TOKEN" > /dev/null; then
  echo "[$(date)] Browserless down, restart"
  pct exec 180 -- docker restart browserless
fi

# check MCP
if ! ss -tlnp -e "ss src :8931" >/dev/null 2>&1; then
  echo "[$(date)] MCP not listening, restart service"
  pct exec 180 -- systemctl restart playwright-mcp
fi
```

Cron: `*/5 * * * * /usr/local/bin/browser-healthcheck.sh >> /var/log/browser-health.log 2>&1`

---

## Troubleshooting

| Gejala | Cek | Fix |
|---|---|---|
| `connection refused :3000` | `pct exec 180 -- docker ps` | Container mati → `docker start browserless` |
| Browserless 401 | URL tanpa `?token=...` | Append `?token=<value>` |
| MCP 403 Forbidden | Host header rejected | Tambah `--allowed-hosts *` di systemd unit |
| MCP 400 Bad Request on GET | Normal | MCP need POST + proper JSON-RPC body |
| Chromium gagal launch (LXC) | `docker logs browserless` | Pastikan `--shm-size=2gb` + `--no-sandbox` di launch args |
| OOM saat banyak tab | RAM CT 180 cap | Naikkan `pct set 180 -memory 4096` + reboot |
| Playwright CDP timeout | Firewall | Cek bridge firewall `pct config 180 \| grep firewall` |
| Claude Code MCP "Needs auth" | Host header check | Update `--allowed-hosts *` (Step 7) |
| Screenshot blank putih | JS not loaded | Set `waitUntil: "networkidle"` di options |
| Site detect bot | Default Chromium fingerprint | Pakai stealth: `DEFAULT_LAUNCH_ARGS` sudah set anti-detect |

---

## Yang JANGAN dilakukan

❌ **Jangan expose port 3000/8931 ke internet** — minimal pakai reverse proxy + IP whitelist + token rotation
❌ **Jangan share token** di Git public — pakai `.env` / secrets manager
❌ **Jangan pakai untuk scraping site yang melarang** — patuhi `robots.txt` dan ToS
❌ **Jangan run lebih dari 4 concurrent browser** — RAM 2.5 GB tidak cukup, akan OOM kill
❌ **Jangan bypass `--no-sandbox` warning di production** — di LXC OK karena sudah sandbox layer luar, di server fisik jangan

---

## Checklist akhir

- [ ] CT 180 running, `pct status 180` = running
- [ ] Docker active: `pct exec 180 -- systemctl is-active docker` = active
- [ ] Browserless container Up: `pct exec 180 -- docker ps | grep browserless`
- [ ] Browserless health: `curl http://192.168.0.180:3000/json/version?token=...` returns Chrome version
- [ ] MCP service active: `pct exec 180 -- systemctl is-active playwright-mcp`
- [ ] MCP listening: `pct exec 180 -- ss -tlnp | grep 8931`
- [ ] (Optional) HTTPS `https://browser.lab.lan` returns 404 (proxy works)
- [ ] (Optional) HTTPS `https://mcp.lab.lan` returns 400 on GET
- [ ] Claude Code MCP shows ✓ Connected
- [ ] Smoke test screenshot OK
- [ ] Token saved di password manager

---

## Konfigurasi instance ini (referensi)

| Item | Value |
|---|---|
| Proxmox host | 192.168.0.222 |
| CT ID | 180 |
| Hostname | browser |
| IP | 192.168.0.180 |
| Resources | 2 core, 2.5 GB RAM, 1 GB swap, 12 GB disk |
| OS | Debian 12 (privileged LXC) |
| Docker | latest stable |
| Node.js | 20.20.2 LTS |
| Browserless | `ghcr.io/browserless/chromium:latest` (Chrome 148) |
| Playwright MCP | `@playwright/mcp@latest` (Microsoft official) |
| Browserless URL | `http://192.168.0.180:3000` atau `https://browser.lab.lan` |
| MCP URL | `http://192.168.0.180:8931/mcp` atau `https://mcp.lab.lan/mcp` |
| Browserless token | `/root/browserless-token` di CT 180 |
| MCP token | `/root/mcp-token` (saat ini tidak dipakai, MCP allow-all) |

---

## Selanjutnya

Lihat **BROWSER-MCP-API.md** untuk:
- Browserless REST endpoint detail (screenshot, PDF, scrape, function, content)
- Playwright connect-over-CDP via Python/Node
- Daftar Playwright MCP tools + signature + contoh
- Common patterns: auto-fill form, login, scrape table, anti-detect, file upload
- Performance tuning

---

_Setup runbook diuji di Proxmox VE 9.1.7, kernel 6.17.13-2-pve, Browserless v2 community (Chromium 148.0.7778.96), Playwright MCP latest, Node 20.20.2 LTS, 30 Mei 2026._
