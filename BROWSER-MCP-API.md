# Browser Automation API Reference

Dokumentasi lengkap untuk **Browserless REST/WS API** (script automation) dan **Playwright MCP Server** (LLM agent) yang berjalan di CT 180 Proxmox.

**Versi referensi:**
- Browserless: v2 community, Chromium 148.0.7778.96
- Playwright MCP: `@playwright/mcp@latest` (Microsoft official)

---

## Konfigurasi koneksi

| Service | URL (HTTP) | URL (HTTPS) | Auth |
|---|---|---|---|
| **Browserless REST** | `http://192.168.0.180:3000` | `https://browser.lab.lan` | `?token=<token>` di setiap URL |
| **Browserless WS/CDP** | `ws://192.168.0.180:3000` | `wss://browser.lab.lan` | `?token=<token>` di URL |
| **Playwright MCP** | `http://192.168.0.180:8931/mcp` | `https://mcp.lab.lan/mcp` | none (LAN trust) |
| **Playwright MCP SSE (legacy)** | `http://192.168.0.180:8931/sse` | `https://mcp.lab.lan/sse` | none |

Token tersimpan di `/Users/ben/Downloads/AI-Selfhosted/browserless-token` dan `mcp-token` lokal.

---

# Part 1 — Browserless REST API

## Quick start

```bash
export BL="http://192.168.0.180:3000"
export TOK="46e93554d04a7dcd0ae335a2eeffe71d04efb10e60485d95"

# health
curl -s "$BL/json/version?token=$TOK"

# screenshot
curl -X POST "$BL/screenshot?token=$TOK" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}' \
  -o out.png
```

## 1.1 `/json/version`

Get Chrome version + WebSocket debugger URL.

```bash
GET /json/version?token=<token>
```

Response:
```json
{
  "Browser": "Chrome/148.0.7778.96",
  "Protocol-Version": "1.3",
  "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/148.0.0.0 Safari/537.36",
  "V8-Version": "14.8.178.14",
  "WebKit-Version": "537.36",
  "webSocketDebuggerUrl": "ws://0.0.0.0:3000/"
}
```

## 1.2 `/screenshot`

Capture screenshot dari URL.

```bash
POST /screenshot?token=<token>
Content-Type: application/json

{
  "url": "https://example.com",
  "options": {
    "fullPage": true,
    "type": "png",
    "quality": 80,
    "omitBackground": false,
    "clip": { "x": 0, "y": 0, "width": 800, "height": 600 }
  },
  "viewport": { "width": 1280, "height": 800 },
  "waitFor": "networkidle0",
  "gotoOptions": { "waitUntil": "networkidle2", "timeout": 30000 },
  "addStyleTag": [{ "content": "body { background: white; }" }],
  "blockResources": ["image", "font"]
}
```

Returns: binary PNG/JPEG (Content-Type: image/png|jpeg).

**Common options:**
- `fullPage: true` — capture seluruh page, bukan viewport saja
- `type: "jpeg"` + `quality: 70` — file lebih kecil
- `clip` — capture region tertentu saja
- `blockResources` — speed up dengan skip images/fonts/css
- `gotoOptions.waitUntil`: `load`, `domcontentloaded`, `networkidle0`, `networkidle2`

## 1.3 `/pdf`

Generate PDF dari halaman.

```bash
POST /pdf?token=<token>
Content-Type: application/json

{
  "url": "https://example.com",
  "options": {
    "format": "A4",
    "landscape": false,
    "printBackground": true,
    "margin": { "top": "1cm", "bottom": "1cm" },
    "displayHeaderFooter": false,
    "headerTemplate": "<div></div>",
    "footerTemplate": "<div></div>"
  },
  "gotoOptions": { "waitUntil": "networkidle2" }
}
```

Returns: binary PDF (Content-Type: application/pdf).

## 1.4 `/content`

Get rendered HTML setelah JS execute.

```bash
POST /content?token=<token>
Content-Type: application/json

{
  "url": "https://news.ycombinator.com",
  "gotoOptions": { "waitUntil": "networkidle2" },
  "waitFor": "table.itemlist"
}
```

Returns: text/html — DOM setelah JS rendering selesai.

## 1.5 `/scrape`

Extract teks dari selector tertentu — ringkas, no full HTML.

```bash
POST /scrape?token=<token>
Content-Type: application/json

{
  "url": "https://news.ycombinator.com",
  "elements": [
    { "selector": "tr.athing a.titlelink", "timeout": 3000 },
    { "selector": "span.score" }
  ],
  "gotoOptions": { "waitUntil": "networkidle2" }
}
```

Returns:
```json
{
  "data": [
    {
      "selector": "tr.athing a.titlelink",
      "results": [
        { "text": "Title 1", "attributes": [{ "name": "href", "value": "..." }] },
        { "text": "Title 2", "attributes": [...] }
      ]
    },
    { "selector": "span.score", "results": [...] }
  ]
}
```

## 1.6 `/function`

Execute custom Puppeteer/Playwright code.

```bash
POST /function?token=<token>
Content-Type: application/json

{
  "code": "export default async ({ page, context }) => { await page.goto('https://example.com'); const title = await page.title(); const h1 = await page.$eval('h1', el => el.textContent); return { data: { title, h1 }, type: 'application/json' }; }",
  "context": {}
}
```

`code` adalah ESM module string yang export `default async function`. Function dapat `{ page, context, browser }`.

Returns:
```json
{ "data": { "title": "Example Domain", "h1": "Example Domain" }, "type": "application/json" }
```

Atau bisa return binary (PDF, screenshot, dll):
```javascript
return { data: pdfBuffer, type: "application/pdf" };
```

## 1.7 `/performance`

Run Lighthouse audit.

```bash
POST /performance?token=<token>
Content-Type: application/json

{
  "url": "https://example.com",
  "config": {
    "extends": "lighthouse:default",
    "settings": { "onlyCategories": ["performance", "accessibility"] }
  }
}
```

Returns full Lighthouse report JSON.

## 1.8 `/download`

Trigger download di page + return file content.

```bash
POST /download?token=<token>
Content-Type: application/json

{
  "code": "export default async ({ page }) => { await page.goto('https://example.com/file.zip'); }"
}
```

## 1.9 `/sessions`

List active browser sessions.

```bash
GET /sessions?token=<token>
```

Returns:
```json
[
  { "id": "...", "url": "https://...", "type": "page", "userAgent": "..." }
]
```

## 1.10 `/metrics`

Prometheus metrics (untuk Grafana monitoring).

```bash
GET /metrics?token=<token>
```

---

# Part 2 — Browserless WebSocket / CDP

Connect Playwright/Puppeteer langsung ke Browserless via WebSocket → kontrol penuh seperti browser lokal.

## 2.1 Python (Playwright)

```python
from playwright.sync_api import sync_playwright

TOKEN = "46e93554d04a7dcd0ae335a2eeffe71d04efb10e60485d95"
WS = f"ws://192.168.0.180:3000?token={TOKEN}"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(WS)
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 ...",
        locale="id-ID",
        timezone_id="Asia/Jakarta",
    )
    page = context.new_page()

    page.goto("https://example.com", wait_until="networkidle")
    print(page.title())

    page.screenshot(path="out.png", full_page=True)
    browser.close()
```

## 2.2 Python (async)

```python
import asyncio
from playwright.async_api import async_playwright

async def main():
    TOKEN = "..."
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(f"ws://192.168.0.180:3000?token={TOKEN}")
        page = await browser.new_page()
        await page.goto("https://example.com")
        print(await page.title())
        await browser.close()

asyncio.run(main())
```

## 2.3 Node.js (Playwright)

```javascript
import { chromium } from "playwright";

const TOKEN = "...";
const browser = await chromium.connectOverCDP(`ws://192.168.0.180:3000?token=${TOKEN}`);
const context = await browser.newContext();
const page = await context.newPage();

await page.goto("https://example.com");
console.log(await page.title());

await page.screenshot({ path: "out.png", fullPage: true });
await browser.close();
```

## 2.4 Node.js (Puppeteer)

```javascript
import puppeteer from "puppeteer-core";

const TOKEN = "...";
const browser = await puppeteer.connect({
  browserWSEndpoint: `ws://192.168.0.180:3000?token=${TOKEN}`,
});
const page = await browser.newPage();
await page.goto("https://example.com");
console.log(await page.title());
await browser.close();
```

---

# Part 3 — Playwright MCP Server

MCP (Model Context Protocol) — dipakai oleh LLM agent (Claude, Cursor, Cline, dll) untuk drive browser via tool calls.

## 3.1 Configure di MCP client

### Claude Code (CLI)

```bash
claude mcp add --transport http playwright-proxmox http://192.168.0.180:8931/mcp
claude mcp list   # verify
```

Config disimpan di `~/.claude.json` (user-level) atau `.claude.json` di project.

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "playwright-proxmox": {
      "url": "http://192.168.0.180:8931/mcp"
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "playwright-proxmox": {
      "transport": "streamable-http",
      "url": "http://192.168.0.180:8931/mcp"
    }
  }
}
```

### Cline (VS Code extension)

VS Code settings:
```json
"cline.mcpServers": {
  "playwright-proxmox": {
    "url": "http://192.168.0.180:8931/mcp"
  }
}
```

### Generic SSE transport (legacy)

```json
{
  "url": "http://192.168.0.180:8931/sse",
  "transport": "sse"
}
```

## 3.2 Tools yang tersedia

Semua tool prefix dengan `mcp__<server-name>__<tool>` saat dipanggil dari Claude Code. Daftar tool utama:

### Navigation

| Tool | Args | Fungsi |
|---|---|---|
| `browser_navigate` | `url: string` | Buka URL |
| `browser_navigate_back` | — | Tombol Back |
| `browser_navigate_forward` | — | Forward |
| `browser_close` | — | Tutup current tab |
| `browser_tabs` | `action: list\|new\|select\|close` | Manage tabs |

### Interaction

| Tool | Args | Fungsi |
|---|---|---|
| `browser_click` | `element: string, ref: string` | Klik element (ref dari snapshot) |
| `browser_type` | `element, ref, text, submit?: bool, slowly?: bool` | Type ke input |
| `browser_press_key` | `key: string` | Tombol keyboard (Enter, Escape, ArrowDown, dll) |
| `browser_hover` | `element, ref` | Hover element |
| `browser_drag` | `startElement, startRef, endElement, endRef` | Drag and drop |
| `browser_select_option` | `element, ref, values: string[]` | Pilih dropdown option |
| `browser_file_upload` | `paths: string[]` | Upload file (path lokal ke server) |
| `browser_handle_dialog` | `accept: bool, promptText?` | Handle alert/confirm/prompt |

### Inspection

| Tool | Args | Fungsi |
|---|---|---|
| `browser_snapshot` | — | **Accessibility tree** halaman (untuk AI baca struktur, lebih hemat token dari HTML) |
| `browser_screenshot` / `browser_take_screenshot` | `fullPage?: bool, filename?` | PNG screenshot |
| `browser_console_messages` | — | Get console.log output |
| `browser_network_requests` | — | Get list network calls |
| `browser_pdf_save` | `filename: string` | Save current page as PDF |

### Waiting

| Tool | Args | Fungsi |
|---|---|---|
| `browser_wait_for` | `text?, textGone?, time?` | Wait kondisi text muncul / hilang / time tertentu |

### Programming

| Tool | Args | Fungsi |
|---|---|---|
| `browser_evaluate` | `function: string, element?, ref?` | Execute JS in page context |
| `browser_resize` | `width, height` | Resize viewport |
| `browser_install` | — | Install browser binaries (rarely needed) |

### Vision (kalau `--caps vision`)

| Tool | Args |
|---|---|
| `browser_mouse_move_xy` | `x, y` |
| `browser_mouse_click_xy` | `x, y` |
| `browser_mouse_drag_xy` | `startX, startY, endX, endY` |

### PDF (kalau `--caps pdf`)

Same as `browser_pdf_save` above.

### DevTools (kalau `--caps devtools`)

Direct CDP access untuk advanced cases.

## 3.3 Workflow tipikal di LLM agent

Saat user minta "login ke github lalu ambil notification", LLM call sequence:

```
1. browser_navigate(url="https://github.com/login")
2. browser_snapshot()                     ← AI baca struktur, dapat "ref" untuk input
3. browser_type(element="username field", ref="e1", text="user")
4. browser_type(element="password field", ref="e2", text="pass", submit=true)
5. browser_wait_for(text="Sign out")      ← tunggu redirect login sukses
6. browser_navigate(url="https://github.com/notifications")
7. browser_snapshot()                     ← AI ambil daftar notifikasi
8. browser_close()
```

`browser_snapshot` return accessibility tree:
```yaml
- generic [ref=e1]:
  - heading "Sign in to GitHub" [ref=e2]
  - textbox "Username or email address" [ref=e3]
  - textbox "Password" [ref=e4]
  - button "Sign in" [ref=e5]
```

LLM pakai `ref` dari snapshot untuk target element berikutnya.

## 3.4 Direct API (kalau bukan dari MCP client)

MCP server adalah JSON-RPC over HTTP/SSE. Endpoint: `POST /mcp` dengan body MCP protocol.

```bash
# initialize session
curl -X POST http://192.168.0.180:8931/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-06-18",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "1.0"}
    }
  }'
```

Lebih praktis: gunakan MCP client library (`@modelcontextprotocol/sdk` Node, `mcp` Python).

---

# Part 4 — Common Patterns

## 4.1 Auto-fill + submit form (Playwright direct)

```python
from playwright.sync_api import sync_playwright

TOKEN = "..."

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(f"ws://192.168.0.180:3000?token={TOKEN}")
    page = browser.new_page()

    page.goto("https://example.com/contact")

    # fill form
    page.fill('input[name="name"]', "John Doe")
    page.fill('input[name="email"]', "john@example.com")
    page.fill('textarea[name="message"]', "Halo dari bot")
    page.select_option('select[name="topic"]', "support")
    page.check('input[name="newsletter"]')

    # submit
    page.click('button[type="submit"]')

    # wait redirect / success
    page.wait_for_load_state("networkidle")
    print("Setelah submit:", page.url)

    browser.close()
```

## 4.2 Infinite scroll scraping

```python
page.goto("https://twitter.com/search?q=playwright")

prev_height = 0
for _ in range(10):
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(2000)
    new_height = page.evaluate("document.body.scrollHeight")
    if new_height == prev_height:
        break
    prev_height = new_height

# extract semua tweet
tweets = page.eval_on_selector_all(
    "article",
    "elements => elements.map(e => e.innerText)"
)
print(f"Found {len(tweets)} tweets")
```

## 4.3 Login + simpan session (cookie persistence)

```python
# first run: login + save state
context = browser.new_context()
page = context.new_page()
page.goto("https://example.com/login")
page.fill('input[name=email]', "...")
page.fill('input[name=password]', "...")
page.click('button[type=submit]')
page.wait_for_url("**/dashboard")

context.storage_state(path="/tmp/auth.json")
browser.close()

# next run: reuse state — skip login
browser = p.chromium.connect_over_cdp(WS)
context = browser.new_context(storage_state="/tmp/auth.json")
page = context.new_page()
page.goto("https://example.com/dashboard")  # langsung logged in
```

## 4.4 Wait for AJAX response

```python
# wait specific API call
with page.expect_response(lambda r: "/api/users" in r.url and r.status == 200) as resp_info:
    page.click("button.load-users")
response = resp_info.value
data = response.json()
print(f"Loaded {len(data['users'])} users")
```

## 4.5 Anti-detection patterns

```python
# patch navigator.webdriver (already done by Browserless via launch args)
page.add_init_script("""
  Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  window.chrome = { runtime: {} };
""")

# random mouse movement (jangan langsung klik exact pixel)
page.mouse.move(100, 100)
page.mouse.move(200, 150, steps=10)  # gradual movement

# typing dengan delay realistic
page.type("input[name=q]", "search term", delay=80)  # 80ms per char
```

## 4.6 File upload

```python
# regular input[type=file]
page.set_input_files('input[type=file]', "/path/to/file.pdf")

# untuk upload yang trigger dari button:
with page.expect_file_chooser() as fc_info:
    page.click('button.upload-btn')
file_chooser = fc_info.value
file_chooser.set_files("/path/to/file.pdf")
```

## 4.7 Download file

```python
with page.expect_download() as download_info:
    page.click("a.download-link")
download = download_info.value
download.save_as("/tmp/downloaded.pdf")
print(f"Saved: {download.suggested_filename}")
```

## 4.8 Handle multi-tab / popup

```python
# new tab opened by click
with context.expect_page() as new_page_info:
    page.click("a.opens-new-tab")
new_page = new_page_info.value
new_page.wait_for_load_state()
print(new_page.url)
```

## 4.9 Intercept network (block ads, modify response)

```python
def handle_route(route):
    if "google-analytics" in route.request.url or "doubleclick" in route.request.url:
        route.abort()
    else:
        route.continue_()

page.route("**/*", handle_route)
page.goto("https://example.com")
```

## 4.10 PDF generation dengan custom header/footer

```python
page.goto("https://example.com/report")
page.pdf(
    path="report.pdf",
    format="A4",
    print_background=True,
    display_header_footer=True,
    header_template='<div style="font-size:10px;width:100%;text-align:center;">Header</div>',
    footer_template='<div style="font-size:10px;width:100%;text-align:center;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
    margin={"top": "1.5cm", "bottom": "1.5cm", "left": "1cm", "right": "1cm"},
)
```

---

# Part 5 — Performance & Concurrency

## 5.1 Browserless concurrency

CT 180 config: `CONCURRENT=4`. Max 4 simultaneous browser sessions.

Untuk batch scraping:
```python
import asyncio
from playwright.async_api import async_playwright

async def scrape_one(p, url):
    browser = await p.chromium.connect_over_cdp(f"ws://192.168.0.180:3000?token={TOKEN}")
    page = await browser.new_page()
    await page.goto(url)
    title = await page.title()
    await browser.close()
    return title

async def main():
    urls = ["https://example.com", "https://example.org", ...]
    async with async_playwright() as p:
        # batch 4 paralel
        results = []
        for i in range(0, len(urls), 4):
            batch = urls[i:i+4]
            batch_results = await asyncio.gather(*[scrape_one(p, u) for u in batch])
            results.extend(batch_results)
        return results

asyncio.run(main())
```

## 5.2 Resource tuning

```python
# skip heavy resources untuk speed up
context = browser.new_context(
    java_script_enabled=True,  # set False kalau cuma butuh static HTML
)

page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,otf}", lambda r: r.abort())
page.route("**/google-analytics.com/**", lambda r: r.abort())
page.route("**/doubleclick.net/**", lambda r: r.abort())
```

Dengan resource blocking, screenshot/scrape bisa 2-3× lebih cepat.

## 5.3 Page recycling

Untuk many requests, reuse context:
```python
browser = await p.chromium.connect_over_cdp(WS)
context = await browser.new_context()  # 1 context

for url in urls:
    page = await context.new_page()      # tab baru, share context cookies
    await page.goto(url)
    # ... process ...
    await page.close()                   # tutup tab tapi context tetap

await browser.close()
```

---

# Part 6 — Use case examples

## 6.1 Monitor harga competitor

```python
async def check_price(p, url, selector):
    browser = await p.chromium.connect_over_cdp(WS)
    page = await browser.new_page()
    await page.goto(url)
    await page.wait_for_selector(selector)
    price = await page.eval_on_selector(selector, "el => el.textContent.trim()")
    await browser.close()
    return price

# cron tiap jam
prices = [
    await check_price(p, "https://shopee.co.id/product/123", ".price"),
    await check_price(p, "https://tokopedia.com/product/abc", "[data-testid='price']"),
]
```

## 6.2 Auto-submit form survey / order

```python
def order_product(url, qty, address):
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(WS)
        page = browser.new_page()
        page.goto(url)

        page.fill('input[name="qty"]', str(qty))
        page.click("button.add-to-cart")
        page.wait_for_selector(".cart-badge")

        page.goto(url + "/checkout")
        page.fill('input[name="address"]', address)
        page.select_option('select[name="payment"]', "transfer")
        page.click('button.confirm-order')

        page.wait_for_url("**/order-success**", timeout=30000)
        order_id = page.locator(".order-id").text_content()
        browser.close()
        return order_id
```

## 6.3 Generate report PDF via API

```bash
# backend service receives request → returns PDF
curl -X POST "$BL/pdf?token=$TOK" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://internal.app/report/2026-q1",
    "options": {
      "format": "A4",
      "printBackground": true,
      "displayHeaderFooter": true,
      "headerTemplate": "<div style=\"font-size:10px;text-align:center;width:100%\">Q1 2026 Report</div>",
      "footerTemplate": "<div style=\"font-size:10px;text-align:center;width:100%\">Page <span class=\"pageNumber\"></span></div>",
      "margin": {"top":"2cm","bottom":"2cm"}
    },
    "gotoOptions": {"waitUntil":"networkidle2"}
  }' \
  -o report-q1-2026.pdf
```

## 6.4 OG card screenshot generator

```bash
curl -X POST "$BL/screenshot?token=$TOK" \
  -H "Content-Type: application/json" \
  -d '{
    "html": "<html><body style=\"display:flex;align-items:center;justify-content:center;width:1200px;height:630px;background:linear-gradient(135deg,#667eea,#764ba2);font-family:sans-serif;color:white;font-size:60px;font-weight:bold;\">My Awesome Title</body></html>",
    "options": { "type": "png" },
    "viewport": { "width": 1200, "height": 630 }
  }' \
  -o og-card.png
```

`html` field langsung set body inline tanpa goto URL.

## 6.5 LLM agent use case — Claude Code via MCP

Prompt natural ke Claude Code:
> "Buka https://news.ycombinator.com via playwright-proxmox, scroll 3 kali, kasih saya daftar 10 judul teratas."

Claude akan call:
1. `mcp__playwright-proxmox__browser_navigate` → news.ycombinator.com
2. `mcp__playwright-proxmox__browser_evaluate` → `window.scrollBy(0, window.innerHeight)` × 3
3. `mcp__playwright-proxmox__browser_snapshot` → accessibility tree
4. Parse + return ke user

Tidak perlu Anda code — semua orchestration di Claude.

---

# Part 7 — Troubleshooting

| Gejala | Diagnostic | Fix |
|---|---|---|
| `connection refused :3000` | `pct exec 180 -- docker ps` | Container mati → `docker start browserless` |
| Browserless 401 | URL tidak ada `?token=` | Append `?token=<value>` |
| Browserless 429 Too Many | Concurrent limit | Naikkan `CONCURRENT=8` env + restart |
| Screenshot blank putih | JS belum jalan | `gotoOptions.waitUntil: "networkidle2"` atau tambah `waitFor` |
| Site detect bot | Default Chromium fingerprint | Anti-detect launch args (default sudah set) + stealth plugin |
| Element not found | Element belum render | `page.wait_for_selector(...)` sebelum interact |
| Timeout 30s | Network slow / heavy page | `timeout=60000` di gotoOptions |
| Memory leak setelah jalan lama | Page tidak di-close | `await page.close()` di finally block |
| MCP 403 | Host header rejected | `--allowed-hosts *` di systemd unit |
| MCP "Needs authentication" di Claude | Initial probe fail | Restart MCP service, restart Claude Code |
| Captcha muncul | Site detect headless | Pakai `--cap vision` + manual handle, atau pakai captcha solver service |
| Cookies tidak persist | Browser ditutup | Pakai `context.storage_state(path=...)` + load di run berikutnya |

## Tools health monitoring

```bash
# Browserless health
curl -s "http://192.168.0.180:3000/json/version?token=$TOK" >/dev/null && echo "Browserless OK"

# MCP health (HTTP 400 = expected without proper MCP body)
curl -sI http://192.168.0.180:8931/mcp | grep -q "400" && echo "MCP OK"

# Resource usage
pct exec 180 -- docker stats browserless --no-stream
pct exec 180 -- ps aux | grep mcp | head -3
```

---

# Part 8 — Security best practices

1. **Token rotation** — generate token baru tiap 90 hari:
   ```bash
   pct exec 180 -- bash -c '
     openssl rand -hex 24 > /root/browserless-token.new
     # update docker run with new TOKEN env, recreate container
     mv /root/browserless-token.new /root/browserless-token
   '
   ```

2. **IP whitelist via Caddy** untuk production:
   ```caddy
   browser.lab.lan {
       tls internal
       @allowed remote_ip 192.168.0.0/24 10.0.0.0/8
       handle @allowed {
           reverse_proxy 192.168.0.180:3000
       }
       handle {
           respond "Forbidden" 403
       }
   }
   ```

3. **Jangan expose ke internet langsung** — minimal pakai Tailscale / Cloudflare Tunnel / WireGuard untuk remote access.

4. **Disable JavaScript dimana tidak perlu**:
   ```python
   context = browser.new_context(java_script_enabled=False)
   ```
   Mengurangi attack surface untuk scraping situs yang tidak butuh JS.

5. **Sandbox via privileged LXC** — sudah ada. Untuk extra defense, jalankan di unprivileged LXC + user namespace.

6. **Network egress filtering** — kalau bot dipakai untuk internal tool, batasi outbound:
   ```bash
   # di Proxmox host firewall rule untuk CT 180
   pct set 180 --firewall 1
   # configure di /etc/pve/firewall/180.fw
   ```

---

Untuk pakai dari Claude Code

  MCP server sudah di-wire ke config Anda. Untuk activate tools-nya:

  exit          # tutup Claude Code ini
  claude        # buka lagi

  Setelah restart, tools mcp__playwright-proxmox__browser_* tersedia. Coba prompt seperti:

  ▎ "Pakai playwright MCP, navigate ke hacker news, snapshot, dan kasih saya 5 judul teratas."

  Semua orchestration di saya, browser execute headless di CT 180.

## Referensi eksternal

- **Browserless** docs: https://docs.browserless.io
- **Browserless** REST: https://docs.browserless.io/HTTP-APIs/screenshot
- **Playwright** docs: https://playwright.dev
- **Playwright MCP**: https://github.com/microsoft/playwright-mcp
- **MCP spec**: https://modelcontextprotocol.io
- **Claude Code MCP**: https://docs.anthropic.com/en/docs/agents-and-tools/mcp
- **Anti-detection patterns**: https://github.com/berstend/puppeteer-extra-plugin-stealth

---

_Dokumentasi berlaku untuk Browserless v2 community (Chromium 148.0.7778.96) + Playwright MCP latest, deployed di CT 180 Proxmox._
