#!/usr/bin/env bash
# Run INSIDE the LXC container (CT 200 by default).
# Installs NVIDIA userspace libs, ComfyUI, ComfyUI-LTXVideo nodes, and LTX-Video models.
set -euo pipefail

COMFY_USER="${COMFY_USER:-comfy}"
COMFY_HOME="${COMFY_HOME:-/opt/comfyui}"
LISTEN_HOST="${LISTEN_HOST:-0.0.0.0}"
LISTEN_PORT="${LISTEN_PORT:-8188}"
TORCH_CUDA="${TORCH_CUDA:-cu124}"   # cu121, cu124, cu128 — match driver

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
fail() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "run as root inside the container"

# ---------- 1. base packages ----------
say "Installing base packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates curl wget git git-lfs build-essential \
  python3 python3-venv python3-pip python3-dev \
  ffmpeg libgl1 libglib2.0-0 pkg-config \
  kmod

git lfs install --system

# ---------- 2. NVIDIA userspace (no kernel module — host owns it) ----------
say "Installing NVIDIA userspace libraries"
DRIVER_RUN=$(ls /root/NVIDIA-Linux-x86_64-*.run 2>/dev/null | head -1 || true)
[[ -n "$DRIVER_RUN" ]] || fail "driver installer not found in /root — host script should have bind-mounted it"

chmod +x "$DRIVER_RUN"
"$DRIVER_RUN" --silent --no-kernel-module --no-systemd --no-nvidia-modprobe \
  --install-libglvnd --no-questions --ui=none

ldconfig

say "Verifying GPU visible inside container"
nvidia-smi || fail "nvidia-smi failed inside container — check passthrough cgroup/mount lines on host"

# ---------- 3. comfy user ----------
if ! id "$COMFY_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash -d "$COMFY_HOME" "$COMFY_USER"
fi
mkdir -p "$COMFY_HOME"
chown -R "$COMFY_USER:$COMFY_USER" "$COMFY_HOME"

# ---------- 4. ComfyUI install ----------
say "Cloning ComfyUI"
sudo -u "$COMFY_USER" -H bash -lc "
  set -e
  cd '$COMFY_HOME'
  if [ ! -d ComfyUI ]; then
    git clone --depth=1 https://github.com/comfyanonymous/ComfyUI.git
  fi
  cd ComfyUI
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip wheel
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/${TORCH_CUDA}
  pip install -r requirements.txt
"

# ---------- 5. LTX-Video custom nodes ----------
say "Installing ComfyUI-LTXVideo custom nodes"
sudo -u "$COMFY_USER" -H bash -lc "
  set -e
  cd '$COMFY_HOME/ComfyUI/custom_nodes'
  [ -d ComfyUI-LTXVideo ] || git clone --depth=1 https://github.com/Lightricks/ComfyUI-LTXVideo.git
  [ -d ComfyUI-VideoHelperSuite ] || git clone --depth=1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
  source '$COMFY_HOME/ComfyUI/venv/bin/activate'
  pip install -r ComfyUI-LTXVideo/requirements.txt || true
  pip install -r ComfyUI-VideoHelperSuite/requirements.txt || true
"

# ---------- 6. download LTX-Video model + text encoder ----------
say "Downloading LTX-Video model (~9 GB) and T5 text encoder (~9 GB FP8)"
sudo -u "$COMFY_USER" -H bash -lc "
  set -e
  cd '$COMFY_HOME/ComfyUI/models'
  mkdir -p checkpoints text_encoders
  # LTX-Video 0.9.5 (single-file checkpoint, contains UNet + VAE)
  if [ ! -f checkpoints/ltx-video-2b-v0.9.5.safetensors ]; then
    wget -c -O checkpoints/ltx-video-2b-v0.9.5.safetensors \
      https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.5.safetensors
  fi
  # T5-XXL text encoder (FP8 to save VRAM)
  if [ ! -f text_encoders/t5xxl_fp8_e4m3fn.safetensors ]; then
    wget -c -O text_encoders/t5xxl_fp8_e4m3fn.safetensors \
      https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors
  fi
"

# ---------- 7. systemd service ----------
say "Creating systemd service"
cat > /etc/systemd/system/comfyui.service <<EOF
[Unit]
Description=ComfyUI (LTX-Video)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$COMFY_USER
WorkingDirectory=$COMFY_HOME/ComfyUI
Environment="PATH=$COMFY_HOME/ComfyUI/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$COMFY_HOME/ComfyUI/venv/bin/python main.py --listen $LISTEN_HOST --port $LISTEN_PORT
Restart=on-failure
RestartSec=5
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now comfyui.service
sleep 3
systemctl status comfyui.service --no-pager || true

IP=$(ip -4 addr show eth0 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1)
cat <<EOF

\033[1;32m================================================================\033[0m
 ComfyUI is starting on:  http://${IP:-<container-ip>}:${LISTEN_PORT}
 Service:                 systemctl status comfyui
 Logs:                    journalctl -u comfyui -f
 Models dir:              $COMFY_HOME/ComfyUI/models
 LTX example workflows:   $COMFY_HOME/ComfyUI/custom_nodes/ComfyUI-LTXVideo/example_workflows
\033[1;32m================================================================\033[0m

Tips:
  • First model load takes ~30s. Generation: 5s clip ≈ 20-40s on RTX 4070 (12GB).
  • Load a workflow via the UI: drag a .json from example_workflows onto the canvas.
  • To update ComfyUI later:  sudo -u $COMFY_USER git -C $COMFY_HOME/ComfyUI pull
EOF
