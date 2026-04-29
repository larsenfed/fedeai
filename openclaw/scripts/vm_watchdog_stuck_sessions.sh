#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="/tmp/openclaw/openclaw-$(date +%Y-%m-%d).log"
STAMP_FILE="/tmp/openclaw-watchdog-last-restart.txt"
COOLDOWN_SECONDS=180
SCAN_LINES=180

if [ ! -f "${LOG_FILE}" ]; then
  exit 0
fi

# Only act when the gateway explicitly reports a stuck session.
if ! tail -n "${SCAN_LINES}" "${LOG_FILE}" | grep -q "stuck session"; then
  exit 0
fi

now="$(date +%s)"
last=0
if [ -f "${STAMP_FILE}" ]; then
  last="$(cat "${STAMP_FILE}" || echo 0)"
fi

if [ $((now - last)) -lt "${COOLDOWN_SECONDS}" ]; then
  exit 0
fi

echo "${now}" > "${STAMP_FILE}"

XDG_RUNTIME_DIR=/run/user/1000 \
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
systemctl --user restart openclaw-gateway.service
