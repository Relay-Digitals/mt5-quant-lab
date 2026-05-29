#!/usr/bin/env bash
# Run on Proxmox HOST (root@192.168.0.222)
# Creates LXC CT 132 'mt5-server' for running MetaTrader 5 inside Docker
# (gmag11/metatrader5_vnc) with noVNC + mt5linux RPyC bridge.
#
# Hardware target: any amd64 host. No GPU passthrough needed.
# Coexists with CT 130 (SD), CT 131 (LLM), CT 103 (code-server).
set -euo pipefail

CTID="${CTID:-132}"
HOSTNAME_CT="${HOSTNAME_CT:-mt5-server}"
DISK_GB="${DISK_GB:-30}"
RAM_MB="${RAM_MB:-4096}"
SWAP_MB="${SWAP_MB:-4096}"
CORES="${CORES:-2}"
BRIDGE="${BRIDGE:-vmbr0}"
STORAGE="${STORAGE:-local-lvm}"
TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-local}"
ROOT_PASSWORD="${ROOT_PASSWORD:-ChangeMe123!}"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
fail() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "must run as root on Proxmox host"
command -v pveversion >/dev/null || fail "this is not a Proxmox host"

say "Proxmox version: $(pveversion | head -1)"

# ---------- 1. ensure template ----------
say "Ensuring debian-12 template exists"
pveam update >/dev/null
TEMPLATE=$(pveam available -section system | awk '/debian-12-standard/ {print $2}' | sort | tail -1)
[[ -n "$TEMPLATE" ]] || fail "could not find debian-12-standard template"
if ! pveam list "$TEMPLATE_STORAGE" | grep -q "$TEMPLATE"; then
  pveam download "$TEMPLATE_STORAGE" "$TEMPLATE"
fi
TEMPLATE_PATH="${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE}"

# ---------- 2. create CT ----------
if pct status "$CTID" >/dev/null 2>&1; then
  fail "CTID $CTID already exists. Set CTID=<n> or: pct stop $CTID && pct destroy $CTID"
fi

# Note: features=nesting,keyctl are REQUIRED for Docker-in-LXC.
# Privileged container (--unprivileged 0) avoids the user-namespace gymnastics
# that often break Docker overlay2 storage in unprivileged LXC.
say "Creating CT $CTID ($HOSTNAME_CT)  —  ${CORES} cores, ${RAM_MB} MB RAM, ${SWAP_MB} MB swap, ${DISK_GB} GB disk"
pct create "$CTID" "$TEMPLATE_PATH" \
  --hostname "$HOSTNAME_CT" \
  --cores "$CORES" \
  --memory "$RAM_MB" \
  --swap "$SWAP_MB" \
  --rootfs "${STORAGE}:${DISK_GB}" \
  --net0 "name=eth0,bridge=${BRIDGE},ip=dhcp,firewall=0" \
  --features "nesting=1,keyctl=1" \
  --unprivileged 0 \
  --onboot 1 \
  --password "$ROOT_PASSWORD" \
  --start 0

# Extra fuse + cgroup permissions sometimes needed by Docker's overlay storage.
# Keep this minimal — Docker works on Proxmox 9.x with just nesting=1 + keyctl=1.

say "Starting CT $CTID"
pct start "$CTID"
sleep 5

IP=$(pct exec "$CTID" -- bash -c "ip -4 addr show eth0 | awk '/inet /{print \$2}' | cut -d/ -f1" || true)

cat <<EOF

\033[1;32m================================================================\033[0m
 CT $CTID '${HOSTNAME_CT}' created. IP: ${IP:-pending}
 root password: $ROOT_PASSWORD
\033[1;32m================================================================\033[0m

Next steps:
  pct push $CTID mt5-02-container-setup.sh /root/mt5-02-container-setup.sh
  pct exec $CTID -- bash /root/mt5-02-container-setup.sh

After setup, ports on http://${IP:-<ct-ip>}:
  3000  — noVNC web (visual MT5 access for login & monitoring)
  8001  — RPyC server (mt5linux Python bridge)
EOF
