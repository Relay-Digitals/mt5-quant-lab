#!/usr/bin/env bash
# Run INSIDE LXC CT 131 (ai-coder).
# Installs:
#   - Intel iGPU userspace runtime (OpenCL + Level Zero) — shared with CT 130 pattern
#   - IPEX-LLM portable Ollama (Intel-optimized, runs on iGPU via SYCL/Level Zero)
#   - Open WebUI (Claude-like chat UI, RAG-capable) — Python install, no Docker
#   - code-server (VS Code in browser) with Continue.dev extension pre-configured
#   - systemd services for all three
set -euo pipefail

LLM_HOME="${LLM_HOME:-/opt/ai-coder}"
OLLAMA_PORT="${OLLAMA_PORT:-11434}"
WEBUI_PORT="${WEBUI_PORT:-3000}"
SKIP_CODE_SERVER="${SKIP_CODE_SERVER:-0}"
CODE_SERVER_PORT="${CODE_SERVER_PORT:-8443}"
CODE_SERVER_PASSWORD="${CODE_SERVER_PASSWORD:-$(openssl rand -hex 16)}"
# IPEX-LLM portable Ollama URL. If empty, will fetch latest from GitHub.
IPEX_OLLAMA_URL="${IPEX_OLLAMA_URL:-}"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
fail() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "run as root inside the container"

# ---------- 1. base + Intel runtime ----------
say "Enabling contrib + non-free + non-free-firmware (needed for intel-media-va-driver)"
sed -i 's|bookworm main$|bookworm main contrib non-free non-free-firmware|' /etc/apt/sources.list
sed -i 's|bookworm-updates main$|bookworm-updates main contrib non-free non-free-firmware|' /etc/apt/sources.list
sed -i 's|bookworm-security main$|bookworm-security main contrib non-free non-free-firmware|' /etc/apt/sources.list

say "Installing base packages + Intel GPU userspace"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates curl wget gnupg git git-lfs jq sudo \
  build-essential pkg-config \
  python3 python3-venv python3-pip python3-dev \
  libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 ffmpeg \
  intel-opencl-icd intel-media-va-driver intel-gpu-tools \
  ocl-icd-libopencl1 clinfo vainfo libtbb12 libtbbmalloc2 numactl \
  systemd-timesyncd openssl

git lfs install --system

say "Verifying iGPU visible via OpenCL (Debian stock driver)"
clinfo -l || fail "OpenCL did not see iGPU. Check /dev/dri passthrough on host."

# ---------- 1b. Modern Intel Level Zero stack (REQUIRED for IPEX-LLM) ----------
# Debian Bookworm's libze1 (1.8.12) + libze_intel_gpu (1.3.24595, Jan 2023) are too
# old for IPEX-LLM 2025. Pull modern versions from Intel's Graphics apt repo
# (jammy is binary-compatible with Bookworm).
say "Adding Intel Graphics apt repo (Ubuntu jammy) for modern Level Zero"
if [[ ! -f /usr/share/keyrings/intel-graphics.gpg ]]; then
  wget -qO- https://repositories.intel.com/gpu/intel-graphics.key | gpg --dearmor -o /usr/share/keyrings/intel-graphics.gpg
fi
cat > /etc/apt/sources.list.d/intel-gpu.list <<'EOF'
deb [arch=amd64 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/gpu/ubuntu jammy unified
EOF
apt-get update
# NOTE: libze-intel-gpu1 (current naming) BREAKS legacy intel-level-zero-gpu — install only the modern one
DEBIAN_FRONTEND=noninteractive apt-get install -y libze1 libze-intel-gpu1 intel-opencl-icd
ldconfig

say "Verifying SYCL/Level Zero sees iGPU"
clinfo -l

# ---------- 2. directories ----------
say "Layout in ${LLM_HOME}"
mkdir -p \
  "${LLM_HOME}/ipex-ollama" \
  "${LLM_HOME}/open-webui/data" \
  "${LLM_HOME}/code-server/workspace" \
  "${LLM_HOME}/models"

# ---------- 3. IPEX-LLM portable Ollama (Intel iGPU acceleration) ----------
say "Resolving IPEX-LLM Ollama portable release"
# NOTE: distribution repo is ipex-llm/ipex-llm (mirror), NOT intel/ipex-llm
if [[ -z "$IPEX_OLLAMA_URL" ]]; then
  IPEX_OLLAMA_URL=$(curl -fsSL https://api.github.com/repos/ipex-llm/ipex-llm/releases \
    | jq -r '[.[] | .assets[]? | select(.name | test("^ollama-ipex-llm-.*-ubuntu\\.tgz$"))][0].browser_download_url' \
    || true)
fi
# fallback to known-good stable v2.2.0 if API didn't return anything
if [[ -z "$IPEX_OLLAMA_URL" || "$IPEX_OLLAMA_URL" == "null" ]]; then
  IPEX_OLLAMA_URL="https://github.com/ipex-llm/ipex-llm/releases/download/v2.2.0/ollama-ipex-llm-2.2.0-ubuntu.tgz"
  say "API resolve failed, falling back to stable: $IPEX_OLLAMA_URL"
fi

say "Downloading: $IPEX_OLLAMA_URL"
cd "${LLM_HOME}/ipex-ollama"
curl -fL -o ollama-ipex-llm.tgz "$IPEX_OLLAMA_URL"
tar -xzf ollama-ipex-llm.tgz --strip-components=1
rm ollama-ipex-llm.tgz
ls -la

# IPEX-LLM ships init script for the SYCL/oneAPI env. The portable tarball contains
# 'ollama' binary plus init-ollama / start-ollama.sh. We invoke the binary directly
# from systemd with the recommended env vars.
[[ -x ./ollama ]] || fail "ollama binary not found in extracted tarball"

cat > /etc/systemd/system/ipex-ollama.service <<EOF
[Unit]
Description=IPEX-LLM Ollama (Intel iGPU accelerated)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${LLM_HOME}/ipex-ollama
Environment="OLLAMA_HOST=0.0.0.0:${OLLAMA_PORT}"
Environment="OLLAMA_MODELS=${LLM_HOME}/models"
Environment="OLLAMA_KEEP_ALIVE=5m"
Environment="OLLAMA_NUM_PARALLEL=1"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
# IPEX-LLM / SYCL knobs for Intel iGPU
Environment="OLLAMA_NUM_GPU=999"
Environment="ZES_ENABLE_SYSMAN=1"
Environment="SYCL_CACHE_PERSISTENT=1"
Environment="ONEAPI_DEVICE_SELECTOR=level_zero:0"
Environment="IPEX_LLM_NUM_CTX=8192"
ExecStart=${LLM_HOME}/ipex-ollama/ollama serve
Restart=on-failure
RestartSec=5
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now ipex-ollama.service
sleep 5
curl -fsS "http://127.0.0.1:${OLLAMA_PORT}/api/tags" >/dev/null \
  || fail "Ollama did not come up on :${OLLAMA_PORT}. Check: journalctl -u ipex-ollama -n 100"
say "Ollama API up on :${OLLAMA_PORT}"

# Convenience CLI shim so 'ollama ...' works regardless of cwd
echo "#!/usr/bin/env bash" > /usr/local/bin/ollama
echo "exec ${LLM_HOME}/ipex-ollama/ollama \"\$@\"" >> /usr/local/bin/ollama
chmod +x /usr/local/bin/ollama
# Ensure /usr/local/bin is in PATH for pct exec / systemd shells
echo 'PATH="/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin"' > /etc/environment

# ---------- 4. Open WebUI (Python install — no Docker in LXC) ----------
say "Installing Open WebUI (Python)"
python3 -m venv "${LLM_HOME}/open-webui/venv"
source "${LLM_HOME}/open-webui/venv/bin/activate"
pip install --upgrade pip wheel
# Pre-install torch CPU-only to prevent pulling ~2.5 GB of unused NVIDIA CUDA wheels
pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
pip install --no-cache-dir open-webui
deactivate

cat > /etc/systemd/system/open-webui.service <<EOF
[Unit]
Description=Open WebUI (chat UI for Ollama)
After=ipex-ollama.service network-online.target
Wants=ipex-ollama.service network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${LLM_HOME}/open-webui
Environment="DATA_DIR=${LLM_HOME}/open-webui/data"
Environment="OLLAMA_BASE_URL=http://127.0.0.1:${OLLAMA_PORT}"
Environment="WEBUI_AUTH=true"
Environment="ENABLE_SIGNUP=true"
Environment="RAG_EMBEDDING_ENGINE=ollama"
Environment="RAG_EMBEDDING_MODEL=nomic-embed-text"
Environment="AUDIO_STT_ENGINE="
Environment="ENABLE_OLLAMA_API=true"
Environment="PORT=${WEBUI_PORT}"
ExecStart=${LLM_HOME}/open-webui/venv/bin/open-webui serve --host 0.0.0.0 --port ${WEBUI_PORT}
Restart=on-failure
RestartSec=10
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now open-webui.service

# ---------- 5. code-server (VS Code in browser) + Continue.dev ----------
if [[ "$SKIP_CODE_SERVER" == "1" ]]; then
  say "Skipping code-server install (SKIP_CODE_SERVER=1)"
  say "Continue.dev should be installed on the existing code-server CT — see llm-04-ct103-continue-setup.sh"
else
  say "Installing code-server (official script)"
  curl -fsSL https://code-server.dev/install.sh | sh

  mkdir -p /root/.config/code-server
  cat > /root/.config/code-server/config.yaml <<EOF
bind-addr: 0.0.0.0:${CODE_SERVER_PORT}
auth: password
password: ${CODE_SERVER_PASSWORD}
cert: false
EOF
  chmod 600 /root/.config/code-server/config.yaml

  systemctl enable --now code-server@root.service
  sleep 3

  say "Installing Continue.dev extension"
  sudo -u root HOME=/root code-server --install-extension Continue.continue || \
    say "Continue.dev install via CLI failed — install from Extensions panel after first login"

  say "Pre-configuring Continue.dev (config.yaml) for local Ollama"
  mkdir -p /root/.continue
  cat > /root/.continue/config.yaml <<EOF
name: AI-Coder Local Assistant
version: 1.0.0
schema: v1

models:
  - name: Qwen2.5-Coder 7B (chat / edit)
    provider: ollama
    model: qwen2.5-coder:7b
    apiBase: http://localhost:${OLLAMA_PORT}
    roles: [chat, edit, apply]

  - name: Qwen2.5-Coder 1.5B (autocomplete)
    provider: ollama
    model: qwen2.5-coder:1.5b-base
    apiBase: http://localhost:${OLLAMA_PORT}
    roles: [autocomplete]

  - name: Nomic Embed Text (embeddings)
    provider: ollama
    model: nomic-embed-text
    apiBase: http://localhost:${OLLAMA_PORT}
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
fi

# ---------- 6. firewall hint + summary ----------
IP=$(ip -4 addr show eth0 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1)

# Persist credentials/info for future reference
cat > /root/AI-CODER-INFO.txt <<EOF
=== AI-Coder CT 131 ===
Container IP:        ${IP:-unknown}

Open WebUI:          http://${IP}:${WEBUI_PORT}
  (first visit: create admin account)

code-server:         http://${IP}:${CODE_SERVER_PORT}
  password:          ${CODE_SERVER_PASSWORD}
  workspace:         ${LLM_HOME}/code-server/workspace
  config:            /root/.config/code-server/config.yaml

Ollama API:          http://${IP}:${OLLAMA_PORT}
Models dir:          ${LLM_HOME}/models

Services:
  systemctl status ipex-ollama
  systemctl status open-webui
  systemctl status code-server@root

Continue.dev config: /root/.continue/config.yaml
EOF

cat <<EOF

\033[1;32m================================================================\033[0m
 AI-Coder stack installed.
 Details saved to: /root/AI-CODER-INFO.txt
\033[1;32m================================================================\033[0m

 Open WebUI:    http://${IP}:${WEBUI_PORT}
 code-server:   http://${IP}:${CODE_SERVER_PORT}   (pw: ${CODE_SERVER_PASSWORD})
 Ollama API:    http://${IP}:${OLLAMA_PORT}

 NEXT: pull models (~6 GB total)
   bash /root/llm-03-models-pull.sh

 Then visit Open WebUI — first user becomes admin.
EOF
