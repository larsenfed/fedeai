#!/usr/bin/env bash
set -euo pipefail

PROJECT="agile-future-490715-j4"
ZONE="us-central1-f"
INSTANCE="instance-20260427-101420"
USER="federico_larsen"

exec gcloud compute ssh \
  --project="${PROJECT}" \
  --zone="${ZONE}" \
  "${USER}@${INSTANCE}" \
  "$@"
