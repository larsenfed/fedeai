#!/usr/bin/env bash
set -euo pipefail

PROJECT="agile-future-490715-j4"
ZONE="us-central1-f"
INSTANCE="instance-20260427-101420"
REMOTE_USER="federico_larsen"
STAMP="$(date +%Y%m%d-%H%M%S)"
REMOTE_TAR="/tmp/openclaw-home-${STAMP}.tgz"
LOCAL_DIR="$(cd "$(dirname "$0")/../.." && pwd)/vm-import/backups"
LOCAL_TAR="${LOCAL_DIR}/openclaw-home-${STAMP}.tgz"

mkdir -p "${LOCAL_DIR}"

gcloud compute ssh \
  --project="${PROJECT}" \
  --zone="${ZONE}" \
  "${INSTANCE}" \
  --command="
    set -euo pipefail
    sudo tar -C /home/${REMOTE_USER} -czf '${REMOTE_TAR}' .openclaw
    sudo chown ${REMOTE_USER}:${REMOTE_USER} '${REMOTE_TAR}'
    ls -lh '${REMOTE_TAR}'
  "

gcloud compute scp \
  --project="${PROJECT}" \
  --zone="${ZONE}" \
  "${INSTANCE}:${REMOTE_TAR}" \
  "${LOCAL_TAR}"

echo "Downloaded backup to ${LOCAL_TAR}"
