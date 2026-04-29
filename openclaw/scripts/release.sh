#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 \"commit message\" [branch]"
  exit 1
fi

COMMIT_MESSAGE="$1"
BRANCH="${2:-main}"

git rev-parse --is-inside-work-tree >/dev/null 2>&1

git add .

if git diff --cached --quiet; then
  echo "Nothing to commit."
  exit 0
fi

git commit -m "${COMMIT_MESSAGE}"
git push -u origin "${BRANCH}"

"$(cd "$(dirname "$0")" && pwd)/deploy_vm_git_pull.sh" "${BRANCH}"

echo "Release completed: local -> git (${BRANCH}) -> VM."
