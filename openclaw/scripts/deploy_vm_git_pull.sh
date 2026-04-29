#!/usr/bin/env bash
set -euo pipefail

PROJECT="agile-future-490715-j4"
ZONE="us-central1-f"
INSTANCE="instance-20260427-101420"
SERVICE_USER="federico_larsen"
REPO_NAME="fedeAI"
REMOTE_HOME="/home/${SERVICE_USER}"
REMOTE_RUNTIME_WORKSPACE="${REMOTE_HOME}/.openclaw/workspace"
REMOTE_REPO_DIR="${REMOTE_HOME}/${REPO_NAME}"
REMOTE_REPO_URL="https://github.com/larsenfed/fedeai.git"
BRANCH="${1:-main}"

gcloud compute ssh \
  --project="${PROJECT}" \
  --zone="${ZONE}" \
  "${INSTANCE}" \
  --command="
    set -euo pipefail
    sudo -u '${SERVICE_USER}' bash -lc '
      set -euo pipefail

      if [ ! -d \"${REMOTE_REPO_DIR}/.git\" ]; then
        git clone \"${REMOTE_REPO_URL}\" \"${REMOTE_REPO_DIR}\"
      fi

      cd \"${REMOTE_REPO_DIR}\"
      git fetch origin
      git checkout \"${BRANCH}\"
      git pull --ff-only origin \"${BRANCH}\"

      mkdir -p \"${REMOTE_RUNTIME_WORKSPACE}\"
      rsync -a --delete \"${REMOTE_REPO_DIR}/openclaw/.openclaw/workspace/\" \"${REMOTE_RUNTIME_WORKSPACE}/\"

      XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus systemctl --user restart openclaw-gateway.service
      XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus systemctl --user status openclaw-gateway.service --no-pager | sed -n \"1,20p\"
    '
  "
