#!/usr/bin/env bash
# Run INSIDE CT 103 (vscode-server) — existing code-server installation.
# Installs Continue.dev extension and pre-configures it to use the Ollama API
# served by CT 131 (ai-coder).
#
# Required env: CT131_IP — the IP of CT 131 reachable from CT 103.
set -euo pipefail

CT131_IP="${CT131_IP:?must set CT131_IP=<ip-of-ct-131>}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
CODE_SERVER_USER="${CODE_SERVER_USER:-root}"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
fail() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

# verify Ollama reachable
say "Verifying Ollama at http://${CT131_IP}:${OLLAMA_PORT}"
curl -fsS --max-time 5 "http://${CT131_IP}:${OLLAMA_PORT}/api/tags" >/dev/null \
  || fail "Cannot reach Ollama on CT 131. Check llm-02 finished, port 11434 open, CT 131 reachable."

# detect code-server
command -v code-server >/dev/null || fail "code-server not found in CT 103"
say "Found: $(code-server --version | head -1)"

# install Continue.dev extension
say "Installing Continue.dev extension"
USER_HOME=$(getent passwd "$CODE_SERVER_USER" | cut -d: -f6)
[[ -d "$USER_HOME" ]] || fail "could not resolve home for user $CODE_SERVER_USER"

if [[ "$CODE_SERVER_USER" == "root" ]] || [[ "$(id -u)" -eq 0 && "$CODE_SERVER_USER" == "$(id -un)" ]]; then
  HOME="$USER_HOME" code-server --install-extension Continue.continue \
    || say "extension install via CLI failed — install from UI Extensions panel"
else
  su - "$CODE_SERVER_USER" -c "code-server --install-extension Continue.continue" \
    || say "extension install via CLI failed — install from UI Extensions panel"
fi

# pre-configure Continue.dev to point at CT 131
say "Writing Continue.dev config → ${USER_HOME}/.continue/config.yaml"
mkdir -p "${USER_HOME}/.continue"
cat > "${USER_HOME}/.continue/config.yaml" <<EOF
name: AI-Coder Remote Assistant (CT 131)
version: 1.0.0
schema: v1

models:
  - name: Qwen2.5-Coder 7B (chat / edit)
    provider: ollama
    model: qwen2.5-coder:7b
    apiBase: http://${CT131_IP}:${OLLAMA_PORT}
    roles: [chat, edit, apply]

  - name: Qwen2.5-Coder 1.5B (autocomplete)
    provider: ollama
    model: qwen2.5-coder:1.5b-base
    apiBase: http://${CT131_IP}:${OLLAMA_PORT}
    roles: [autocomplete]

  - name: Nomic Embed Text (embeddings)
    provider: ollama
    model: nomic-embed-text
    apiBase: http://${CT131_IP}:${OLLAMA_PORT}
    roles: [embed]

context:
  - provider: code
  - provider: docs
  - provider: diff
  - provider: terminal
  - provider: problems
  - provider: folder
  - provider: codebase
EOF
chown -R "$CODE_SERVER_USER:$CODE_SERVER_USER" "${USER_HOME}/.continue" 2>/dev/null || true

# restart code-server to pick up the extension
say "Restarting code-server"
systemctl restart "code-server@${CODE_SERVER_USER}" 2>/dev/null \
  || systemctl restart code-server 2>/dev/null \
  || say "could not restart code-server service automatically — please reload the browser tab"

cat <<EOF

\033[1;32m================================================================\033[0m
 Continue.dev installed in CT 103 (vscode-server).
 Pointed at: http://${CT131_IP}:${OLLAMA_PORT}
 Config:     ${USER_HOME}/.continue/config.yaml
\033[1;32m================================================================\033[0m

 Open code-server in browser (whatever URL/port you normally use),
 then in the Command Palette: "Continue: Open Chat" (Ctrl+L)
EOF
