#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="agile-future-490715-j4"
ZONE="us-central1-f"
INSTANCE="instance-20260427-101420"
SERVICE_USER="federico_larsen"
REMOTE_WATCHDOG="/home/${SERVICE_USER}/bin/openclaw-stuck-watchdog.sh"
REMOTE_CRON_TAG="# openclaw-stuck-watchdog"

gcloud compute scp \
  --project="${PROJECT}" \
  --zone="${ZONE}" \
  "${SCRIPT_DIR}/vm_watchdog_stuck_sessions.sh" \
  "${SERVICE_USER}@${INSTANCE}:/tmp/openclaw-stuck-watchdog.sh"

gcloud compute ssh \
  --project="${PROJECT}" \
  --zone="${ZONE}" \
  "${INSTANCE}" \
  --command="
    sudo -u '${SERVICE_USER}' bash -lc '
      set -euo pipefail
      mkdir -p /home/${SERVICE_USER}/bin
      mv /tmp/openclaw-stuck-watchdog.sh \"${REMOTE_WATCHDOG}\"
      chmod +x \"${REMOTE_WATCHDOG}\"

      current=\$(crontab -l 2>/dev/null || true)
      filtered=\$(printf \"%s\n\" \"\$current\" | awk \"!/openclaw-stuck-watchdog/\")
      {
        printf \"%s\n\" \"\$filtered\"
        printf \"*/2 * * * * %s %s\n\" \"${REMOTE_WATCHDOG}\" \"${REMOTE_CRON_TAG}\"
      } | crontab -
    '
  "

echo "Installed VM watchdog cron (every 2 minutes)."
