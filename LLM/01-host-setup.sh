#!/usr/bin/env bash
# Run on Proxmox HOST (root@192.168.0.222)
# Creates an LXC container with NVIDIA GPU passthrough for ComfyUI + LTX-Video.
set -euo pipefail

CTID="${CTID:-200}"
HOSTNAME="${HOSTNAME:-comfyui}"
DISK_GB="${DISK_GB:-80}"
RAM_MB="${RAM_MB:-16384}"
CORES="${CORES:-8}"
BRIDGE="${BRIDGE:-vmbr0}"
STORAGE="${STORAGE:-local-lvm}"
TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-local}"
ROOT_PASSWORD="${ROOT_PASSWORD:-ChangeMe123!}"
NVIDIA_DRIVER_VERSION="${NVIDIA_DRIVER_VERSION:-550.127.05}"  # match host once installed

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
fail() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

# ---------- 0. sanity ----------
[[ $EUID -eq 0 ]] || fail "must run as root on Proxmox host"
command -v pveversion >/dev/null || fail "this is not a Proxmox host"

say "Proxmox version: $(pveversion | head -1)"

# ---------- 1. detect GPU ----------
say "GPU detection"
if ! lspci | grep -qi 'nvidia'; then
  fail "no NVIDIA GPU detected by lspci. LTX-Video needs an NVIDIA GPU (≥12GB VRAM)."
fi
lspci | grep -i nvidia

# ---------- 2. install host NVIDIA driver if missing ----------
if ! command -v nvidia-smi >/dev/null 2>&1; then
  say "NVIDIA driver not installed on host. Installing..."
  apt-get update
  apt-get install -y pve-headers-"$(uname -r)" build-essential dkms wget gnupg
  cd /tmp
  wget -q "https://us.download.nvidia.com/XFree86/Linux-x86_64/${NVIDIA_DRIVER_VERSION}/NVIDIA-Linux-x86_64-${NVIDIA_DRIVER_VERSION}.run"
  chmod +x "NVIDIA-Linux-x86_64-${NVIDIA_DRIVER_VERSION}.run"
  ./"NVIDIA-Linux-x86_64-${NVIDIA_DRIVER_VERSION}.run" --silent --dkms
  # load uvm at boot
  cat > /etc/modules-load.d/nvidia.conf <<'EOF'
nvidia
nvidia_uvm
nvidia_modeset
EOF
  cat > /etc/udev/rules.d/70-nvidia.rules <<'EOF'
KERNEL=="nvidia", RUN+="/bin/bash -c '/usr/bin/nvidia-smi -L && /bin/chmod 0666 /dev/nvidia*'"
KERNEL=="nvidia_uvm", RUN+="/bin/bash -c '/usr/bin/nvidia-modprobe -c0 -u && /bin/chmod 0666 /dev/nvidia-uvm*'"
EOF
  modprobe nvidia
  modprobe nvidia_uvm
fi

say "Host nvidia-smi:"
nvidia-smi || fail "nvidia-smi failed on host — reboot may be required after driver install"

# Pin the driver .run file path for use in container (must match exactly)
DRIVER_FILE="/tmp/NVIDIA-Linux-x86_64-${NVIDIA_DRIVER_VERSION}.run"
if [[ ! -f "$DRIVER_FILE" ]]; then
  say "Downloading driver installer to share with container..."
  wget -q -O "$DRIVER_FILE" "https://us.download.nvidia.com/XFree86/Linux-x86_64/${NVIDIA_DRIVER_VERSION}/NVIDIA-Linux-x86_64-${NVIDIA_DRIVER_VERSION}.run"
  chmod +x "$DRIVER_FILE"
fi

# ---------- 3. ensure LXC template is present ----------
say "Ensuring debian-12 template exists"
pveam update >/dev/null
TEMPLATE=$(pveam available -section system | awk '/debian-12-standard/ {print $2}' | sort | tail -1)
[[ -n "$TEMPLATE" ]] || fail "could not find debian-12-standard template"
if ! pveam list "$TEMPLATE_STORAGE" | grep -q "$TEMPLATE"; then
  pveam download "$TEMPLATE_STORAGE" "$TEMPLATE"
fi
TEMPLATE_PATH="${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE}"

# ---------- 4. create container ----------
if pct status "$CTID" >/dev/null 2>&1; then
  fail "CTID $CTID already exists. Set CTID=<n> to use a different ID."
fi

say "Creating CT $CTID ($HOSTNAME)"
pct create "$CTID" "$TEMPLATE_PATH" \
  --hostname "$HOSTNAME" \
  --cores "$CORES" \
  --memory "$RAM_MB" \
  --swap 2048 \
  --rootfs "${STORAGE}:${DISK_GB}" \
  --net0 "name=eth0,bridge=${BRIDGE},ip=dhcp,firewall=0" \
  --features nesting=1 \
  --unprivileged 0 \
  --onboot 1 \
  --password "$ROOT_PASSWORD"

# ---------- 5. GPU passthrough config ----------
say "Configuring GPU passthrough"
CONF="/etc/pve/lxc/${CTID}.conf"

# discover major numbers of nvidia devices
mapfile -t NV_MAJORS < <(ls -l /dev/nvidia* /dev/nvidia-caps/* 2>/dev/null \
  | awk '/^c/ {print $5}' | tr -d , | sort -u)

{
  echo "# --- GPU passthrough ---"
  for M in "${NV_MAJORS[@]}"; do
    echo "lxc.cgroup2.devices.allow: c ${M}:* rwm"
  done
  for DEV in /dev/nvidia0 /dev/nvidia1 /dev/nvidia2 /dev/nvidia3 \
             /dev/nvidiactl /dev/nvidia-modeset \
             /dev/nvidia-uvm /dev/nvidia-uvm-tools; do
    [[ -e "$DEV" ]] && echo "lxc.mount.entry: ${DEV} ${DEV#/} none bind,optional,create=file"
  done
  if [[ -d /dev/nvidia-caps ]]; then
    echo "lxc.mount.entry: /dev/nvidia-caps dev/nvidia-caps none bind,optional,create=dir"
  fi
  # share the driver installer + a marker
  echo "lxc.mount.entry: ${DRIVER_FILE} root/$(basename "$DRIVER_FILE") none bind,optional,create=file"
} >> "$CONF"

say "LXC config written:"
grep -E 'cgroup2|mount.entry' "$CONF"

# ---------- 6. start ----------
say "Starting CT $CTID"
pct start "$CTID"
sleep 4

# ---------- 7. handoff ----------
IP=$(pct exec "$CTID" -- bash -c "ip -4 addr show eth0 | awk '/inet /{print \$2}' | cut -d/ -f1" || true)

cat <<EOF

\033[1;32m================================================================\033[0m
 CT $CTID created. IP: ${IP:-unknown}
 root password: $ROOT_PASSWORD
 Driver installer staged in container at: /root/$(basename "$DRIVER_FILE")
\033[1;32m================================================================\033[0m

Next:
  pct push $CTID 02-container-setup.sh /root/02-container-setup.sh
  pct exec $CTID -- bash /root/02-container-setup.sh

Or enter the container interactively:
  pct enter $CTID
EOF
