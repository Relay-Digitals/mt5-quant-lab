#!/usr/bin/env bash
# redroid-watchdog.sh — auto-restart android-1 kalau redroid hang. TANPA WA, log lokal saja.
# Sehat = adb get-state 'device' DAN sys.boot_completed=1. Skip restart kalau container baru start (<180s).
CONT=android-1
DEV=localhost:5555
LOG=/var/log/redroid-watchdog.log
ts(){ date '+%Y-%m-%d %H:%M:%S'; }
log(){ echo "$(ts) $*" >> "$LOG"; }

# container harus running
if ! docker ps --format '{{.Names}}' | grep -qx "$CONT"; then
  log "WARN: $CONT tidak running -> docker start"
  docker start "$CONT" >/dev/null 2>&1
  exit 0
fi

# umur sejak start (beri waktu boot, hindari restart-storm)
started=$(docker inspect -f '{{.State.StartedAt}}' "$CONT" 2>/dev/null)
start_epoch=$(date -d "$started" +%s 2>/dev/null || echo 0)
age=$(( $(date +%s) - start_epoch ))

adb connect "$DEV" >/dev/null 2>&1
state=$(adb -s "$DEV" get-state 2>/dev/null)
bc=$(adb -s "$DEV" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')

if [ "$state" = "device" ] && [ "$bc" = "1" ]; then
  exit 0   # sehat — diam (tak spam log)
fi

if [ "$age" -lt 180 ]; then
  log "unhealthy (state=$state boot=[$bc]) tapi baru start ${age}s -> tunggu boot, skip"
  exit 0
fi

log "HANG (state=$state boot_completed=[$bc], up ${age}s) -> docker restart $CONT"
docker restart "$CONT" >/dev/null 2>&1
sleep 3
adb kill-server >/dev/null 2>&1; adb start-server >/dev/null 2>&1
adb connect "$DEV" >/dev/null 2>&1
log "restart dikirim; boot diverifikasi siklus berikutnya"
