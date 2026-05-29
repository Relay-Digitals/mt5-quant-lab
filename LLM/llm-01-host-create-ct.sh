#!/usr/bin/env bash
# Run on Proxmox HOST (root@192.168.0.222)
# Creates LXC CT 131 'ai-coder' with Intel iGPU passthrough for self-hosted
# coding LLM (Qwen2.5-Coder via IPEX-LLM Ollama) + Open WebUI + code-server.
#
# Hardware target: Intel i3-1215U (Alder Lake), Intel UHD iGPU, 15 GB host RAM.
# Coexists with CT 130 (Stable Diffusion / OpenVINO) — both share /dev/dri.
set -euo pipefail

CTID="${CTID:-131}"
HOSTNAME_CT="${HOSTNAME_CT:-ai-coder}"
DISK_GB="${DISK_GB:-50}"
RAM_MB="${RAM_MB:-6144}"
SWAP_MB="${SWAP_MB:-8192}"
CORES="${CORES:-4}"
BRIDGE="${BRIDGE:-vmbr0}"
STORAGE="${STORAGE:-local-lvm}"
TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-local}"
ROOT_PASSWORD="${ROOT_PASSWORD:-ChangeMe123!}"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
fail() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "must run as root on Proxmox host"
command -v pveversion >/dev/null || fail "this is not a Proxmox host"

say "Proxmox version: $(pveversion | head -1)"

# ---------- 1. detect Intel iGPU ----------
say "Intel iGPU detection"
if ! lspci | grep -Ei 'vga|display' | grep -qi intel; then
  fail "no Intel iGPU detected. This script assumes Intel UHD / Iris Xe."
fi
lspci | grep -Ei 'vga|display' | grep -i intel

if ! ls /dev/dri/renderD128 >/dev/null 2>&1; then
  fail "/dev/dri/renderD128 missing on host. Install i915/xe kernel modules first."
fi
ls -l /dev/dri/

# ---------- 2. ensure template ----------
say "Ensuring debian-12 template exists"
pveam update >/dev/null
TEMPLATE=$(pveam available -section system | awk '/debian-12-standard/ {print $2}' | sort | tail -1)
[[ -n "$TEMPLATE" ]] || fail "could not find debian-12-standard template"
if ! pveam list "$TEMPLATE_STORAGE" | grep -q "$TEMPLATE"; then
  pveam download "$TEMPLATE_STORAGE" "$TEMPLATE"
fi
TEMPLATE_PATH="${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE}"

# ---------- 3. create CT ----------
if pct status "$CTID" >/dev/null 2>&1; then
  fail "CTID $CTID already exists. Set CTID=<n> or destroy with: pct stop $CTID && pct destroy $CTID"
fi

say "Creating CT $CTID ($HOSTNAME_CT)  —  ${CORES} cores, ${RAM_MB} MB RAM, ${SWAP_MB} MB swap, ${DISK_GB} GB disk"
pct create "$CTID" "$TEMPLATE_PATH" \
  --hostname "$HOSTNAME_CT" \
  --cores "$CORES" \
  --memory "$RAM_MB" \
  --swap "$SWAP_MB" \
  --rootfs "${STORAGE}:${DISK_GB}" \
  --net0 "name=eth0,bridge=${BRIDGE},ip=dhcp,firewall=0" \
  --features nesting=1 \
  --unprivileged 0 \
  --onboot 1 \
  --password "$ROOT_PASSWORD" \
  --start 0

# ---------- 4. iGPU passthrough (DRM major = 226) ----------
say "Configuring Intel iGPU passthrough"
CONF="/etc/pve/lxc/${CTID}.conf"
cat >> "$CONF" <<'EOF'

# Intel iGPU passthrough (DRM major = 226)
lxc.cgroup2.devices.allow: c 226:* rwm
lxc.mount.entry: /dev/dri dev/dri none bind,optional,create=dir
EOF

say "LXC config written:"
grep -E 'cgroup2|mount.entry' "$CONF"

# ---------- 5. start ----------
say "Starting CT $CTID"
pct start "$CTID"
sleep 5

# verify /dev/dri inside CT
say "Verifying /dev/dri inside CT"
pct exec "$CTID" -- ls -l /dev/dri || fail "iGPU not visible inside CT"

IP=$(pct exec "$CTID" -- bash -c "ip -4 addr show eth0 | awk '/inet /{print \$2}' | cut -d/ -f1" || true)

cat <<EOF

\033[1;32m================================================================\033[0m
 CT $CTID '${HOSTNAME_CT}' created. IP: ${IP:-pending}
 root password: $ROOT_PASSWORD
\033[1;32m================================================================\033[0m

Next steps:
  pct push $CTID llm-02-container-setup.sh /root/llm-02-container-setup.sh
  pct exec $CTID -- bash /root/llm-02-container-setup.sh

Or enter interactively:
  pct enter $CTID

After setup, ports will be exposed on http://${IP:-<ct-ip>}:
  3000  — Open WebUI (Claude-like chat)
  8443  — code-server (VS Code in browser)
  11434 — Ollama API (for Continue.dev / external clients)
EOF
