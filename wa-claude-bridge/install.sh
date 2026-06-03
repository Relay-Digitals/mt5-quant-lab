#!/usr/bin/env bash
# install.sh — setup WA->Claude bridge di CT 108 (/opt/wa-claude-bridge). Jalankan sbg root di CT.
set -e
DIR=/opt/wa-claude-bridge
echo "== 1) venv + deps =="
cd "$DIR"
python3 -m venv venv 2>/dev/null || true
./venv/bin/pip -q install -r requirements.txt
echo "== 2) install Claude Code CLI (native) =="
if ! command -v claude >/dev/null 2>&1; then
  curl -fsSL https://claude.ai/install.sh | bash || {
    echo "native gagal; coba npm..."; (command -v npm >/dev/null && npm install -g @anthropic-ai/claude-code) || echo "!! install Node+claude manual"; }
fi
export PATH="$HOME/.local/bin:$PATH"
command -v claude && claude --version || echo "!! claude belum ke-PATH — cek ~/.local/bin"
echo "== 3) .env =="
[ -f .env ] || { cp .env.example .env; echo ">> EDIT $DIR/.env (ALLOWED_NUMBERS, WAHA_KEY) lalu lanjut"; }
chmod +x permguard.py
echo "== 4) systemd =="
cp wa-claude-bot.service /etc/systemd/system/
systemctl daemon-reload
echo
echo "=== LANGKAH MANUAL BERIKUTNYA ==="
echo "1. LOGIN Claude (sekali, interaktif):  claude   (lalu /login, buka URL, paste kode)"
echo "   -> pakai akun Pro/Max. Verifikasi: claude -p 'halo' "
echo "2. Edit $DIR/.env (ALLOWED_NUMBERS=nomormu, WAHA_KEY)."
echo "3. Aktifkan bot:  systemctl enable --now wa-claude-bot  (port 8088)"
echo "4. Set webhook WAHA -> http://192.168.0.108:8088/webhook (lihat SETUP.md)"
echo "5. Tes: kirim 'halo' / '/help' dari WhatsApp."
