#!/usr/bin/env bash
# Push watch-pulse.json so the live site shows new-listing alerts.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
if [[ ! -f data/watch-pulse.json ]]; then
  echo "Run python3 scripts/local_watch.py first."
  exit 1
fi
NEW_COUNT="$(python3 -c "import json; print(len(json.load(open('data/watch-pulse.json')).get('newListings',[])))")"
MSG="Watch pulse: ${NEW_COUNT} new local listing(s) ($(date +%Y-%m-%d))"
git add data/watch-pulse.json
git diff --staged --quiet && { echo "No pulse changes to push."; exit 0; }
git commit -m "$MSG"
git push origin main
echo "Published — check https://poulsbopete.github.io/solis/"

# Cursor Mobile alert (optional — needs .env with CURSOR_AUTOMATION_*)
if [[ "$NEW_COUNT" -gt 0 ]]; then
  python3 scripts/cursor_notify.py --from-pulse 2>/dev/null || true
fi
