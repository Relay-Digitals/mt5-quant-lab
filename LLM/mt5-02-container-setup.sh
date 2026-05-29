#!/usr/bin/env bash
# Run INSIDE CT 132 (mt5-server).
# Installs:
#   - Docker engine (from docker.com apt repo) — needs nesting=1 + keyctl=1 on CT
#   - gmag11/metatrader5_vnc:latest Docker image (~4 GB, Debian-based)
#   - Persistent volume at /opt/mt5-data → /config in container
#   - systemd unit to keep the container alive across reboots
set -euo pipefail

MT5_HOME="${MT5_HOME:-/opt/mt5}"
MT5_DATA_DIR="${MT5_DATA_DIR:-/opt/mt5-data}"
MT5_IMAGE="${MT5_IMAGE:-gmag11/metatrader5_vnc:latest}"
VNC_PORT="${VNC_PORT:-3000}"
RPYC_PORT="${RPYC_PORT:-8001}"
CONTAINER_NAME="${CONTAINER_NAME:-mt5}"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
fail() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "run as root inside the container"

# ---------- 1. base packages ----------
say "Installing base packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates curl wget gnupg jq \
  systemd-timesyncd openssl

# ---------- 2. Docker engine ----------
say "Installing Docker engine from docker.com"
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian ${VERSION_CODENAME} stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# enable + start
systemctl enable --now docker
sleep 3

say "Verifying Docker daemon"
docker version --format '  Client: {{.Client.Version}}{{"\n"}}  Server: {{.Server.Version}}' \
  || fail "Docker daemon not responding. Check 'systemctl status docker' and ensure CT has nesting=1 + keyctl=1 features."

# ---------- 3. layout ----------
say "Layout"
mkdir -p "$MT5_HOME" "$MT5_DATA_DIR"
chmod 755 "$MT5_DATA_DIR"

# ---------- 4. pull image ----------
say "Pulling $MT5_IMAGE (~4 GB, takes 5-15 minutes depending on bandwidth)"
docker pull "$MT5_IMAGE"

# ---------- 5. systemd-managed Docker run ----------
# Use systemd as the supervisor instead of `docker run --restart=always`
# so the container plays nice with `systemctl stop` / logs aggregation.
say "Creating systemd unit mt5.service"
cat > /etc/systemd/system/mt5.service <<EOF
[Unit]
Description=MetaTrader 5 (gmag11/metatrader5_vnc in Docker)
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=simple
Restart=always
RestartSec=10
TimeoutStartSec=300
TimeoutStopSec=60

# Ensure clean state on start (remove any stale container with same name)
ExecStartPre=-/usr/bin/docker rm -f ${CONTAINER_NAME}
ExecStart=/usr/bin/docker run --rm \\
  --name ${CONTAINER_NAME} \\
  -p ${VNC_PORT}:3000 \\
  -p ${RPYC_PORT}:8001 \\
  -v ${MT5_DATA_DIR}:/config \\
  --shm-size=512m \\
  ${MT5_IMAGE}
ExecStop=/usr/bin/docker stop --time=30 ${CONTAINER_NAME}

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now mt5.service

# wait for noVNC to come up
say "Waiting for noVNC on :${VNC_PORT} (first start initializes Wine + MT5, ~3-5 minutes)"
for i in $(seq 1 60); do
  if curl -fsS --max-time 3 -o /dev/null "http://127.0.0.1:${VNC_PORT}/" 2>/dev/null; then
    echo "  noVNC ready after ${i}x5s"
    break
  fi
  sleep 5
done

# ---------- 5b. Workarounds for gmag11 image bugs (as of v2.1, 2026) ----------
# 1. mt5linux 1.0.3 changed CLI args from -H to --host AND no longer accepts
#    positional Python path. New invocation: wine <python.exe> -m mt5linux ...
# 2. Container's init pip install pulls numpy 2.x in Wine but MT5 _core.pyd is
#    compiled against numpy 1.x ABI → "numpy.core.multiarray failed to import".
# 3. Dep resolver leaves rpyc / plumbum / pyparsing version skew between
#    Wine Python (5.2.3/1.7.0) and Linux Python (6.0.2/1.10.0) — protocol break.
#
# We wait for the container's [7/7] init step to finish, then patch.

say "Waiting for Wine first-run init to complete (~10-15 minutes; downloads Mono + MT5 + Python + libs)"
for i in $(seq 1 240); do
  if docker logs "$CONTAINER_NAME" 2>&1 | grep -q "\[7/7\]"; then
    echo "  init reached [7/7] after ${i}x5s"
    break
  fi
  sleep 5
done

say "Patching dep skew (downgrade numpy in Wine, pin rpyc/plumbum on Linux side)"
PYTHON_EXE="/config/.wine/drive_c/Program Files (x86)/Python39-32/python.exe"

# Wine Python: pin numpy to 1.x (MT5 binary compat)
docker exec --user 911 "$CONTAINER_NAME" wine "$PYTHON_EXE" -m pip install "numpy<2" 2>&1 | tail -3 || true

# Linux Python: pin rpyc + plumbum + pyparsing to mt5linux 1.0.3-compatible versions
docker exec --user 911 "$CONTAINER_NAME" pip install --user --force-reinstall --break-system-packages \
  "rpyc==5.2.3" "plumbum==1.7.0" "pyparsing>=3.1.0,<4" 2>&1 | tail -3 || true

# Persist mt5linux launcher to /config (survives container restart via volume mount)
cat > "${MT5_DATA_DIR}/start-mt5linux.sh" <<EOF
#!/bin/bash
export WINEPREFIX=/config/.wine
exec wine "${PYTHON_EXE}" -m mt5linux --host 0.0.0.0 -p 8001
EOF
chmod +x "${MT5_DATA_DIR}/start-mt5linux.sh"
chown 911:911 "${MT5_DATA_DIR}/start-mt5linux.sh"

say "Creating mt5-rpyc.service (workaround supervisor)"
cat > /etc/systemd/system/mt5-rpyc.service <<EOF
[Unit]
Description=MT5 RPyC mt5linux server (workaround for image's broken auto-start)
After=mt5.service
Requires=mt5.service

[Service]
Type=simple
Restart=always
RestartSec=15
TimeoutStartSec=180
ExecStartPre=/bin/bash -c "until docker exec --user 911 ${CONTAINER_NAME} test -f /config/start-mt5linux.sh 2>/dev/null; do sleep 5; done; sleep 5"
ExecStart=/usr/bin/docker exec --user 911 ${CONTAINER_NAME} /config/start-mt5linux.sh
ExecStop=/usr/bin/docker exec ${CONTAINER_NAME} pkill -f mt5linux

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now mt5-rpyc.service
sleep 12

# verify
say "Verifying RPyC :${RPYC_PORT} listening"
if timeout 3 bash -c "</dev/tcp/127.0.0.1/${RPYC_PORT}" 2>/dev/null; then
  echo "  RPyC port ${RPYC_PORT} OPEN ✓"
else
  echo "  WARNING: RPyC port ${RPYC_PORT} not yet open. Check: journalctl -u mt5-rpyc -n 50"
fi

# ---------- 6. info file ----------
IP=$(ip -4 addr show eth0 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1)

cat > /root/MT5-INFO.txt <<EOF
=== MT5 Server CT 132 (deployed $(date -u +%Y-%m-%d)) ===
Container IP:        ${IP:-unknown}

noVNC (browser):     http://${IP}:${VNC_PORT}
  → opens MetaTrader 5 GUI in browser. Use this to log into your broker.

RPyC (Python API):   ${IP}:${RPYC_PORT}
  → mt5linux Python bridge for headless access from your code.

Persistent data:     ${MT5_DATA_DIR}  (= /config inside container)
  MQL5 files live at: ${MT5_DATA_DIR}/.wine/drive_c/Program Files/MetaTrader 5/MQL5/

Docker container:    ${CONTAINER_NAME}   (image ${MT5_IMAGE})

Services:
  systemctl status mt5
  docker logs ${CONTAINER_NAME} --tail 50 -f

Python client (any host, including code-server CT 103):
  pip install mt5linux
  python3 -c "
  from mt5linux import MetaTrader5
  mt5 = MetaTrader5(host='${IP}', port=${RPYC_PORT})
  mt5.initialize()
  print(mt5.terminal_info())
  print(mt5.account_info())
  "
EOF

cat <<EOF

\033[1;32m================================================================\033[0m
 MT5 stack installed.
 Details saved to: /root/MT5-INFO.txt
\033[1;32m================================================================\033[0m

 noVNC:        http://${IP}:${VNC_PORT}
 RPyC API:     ${IP}:${RPYC_PORT}
 Data dir:     ${MT5_DATA_DIR}

 NEXT: open noVNC in browser, click "Connect", you'll see MT5 splash screen.
 First start: ~3-5 min for Wine init + MT5 first-run.
 Then: File → Login to Trade Account → enter your broker creds.
EOF
