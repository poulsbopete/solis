#!/usr/bin/env bash
# Hourly watcher entrypoint — loads .env then runs local_watch.py.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

exec python3 scripts/local_watch.py --publish "$@"
