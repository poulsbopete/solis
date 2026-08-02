#!/usr/bin/env bash
# Install hourly local Solis/Travato watcher (macOS launchd or Linux cron).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
PLIST_LABEL="com.poulsbopete.solis-watch"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"

echo "Repo: $REPO_ROOT"

if [[ "$(uname -s)" == "Darwin" ]]; then
  mkdir -p "$HOME/Library/LaunchAgents" "$REPO_ROOT/.local"
  cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${PLIST_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON}</string>
    <string>${REPO_ROOT}/scripts/local_watch.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${REPO_ROOT}</string>
  <key>StartInterval</key>
  <integer>3600</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${REPO_ROOT}/.local/watch-stdout.log</string>
  <key>StandardErrorPath</key>
  <string>${REPO_ROOT}/.local/watch-stderr.log</string>
</dict>
</plist>
EOF
  launchctl bootout "gui/$(id -u)/${PLIST_LABEL}" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
  launchctl enable "gui/$(id -u)/${PLIST_LABEL}"
  echo "Installed launchd agent: $PLIST_PATH"
  echo "Runs every hour + once at login. Logs: .local/watch-stdout.log"
  echo "Test now: ${PYTHON} ${REPO_ROOT}/scripts/local_watch.py -v"
else
  CRON_LINE="0 * * * * cd ${REPO_ROOT} && ${PYTHON} scripts/local_watch.py >> .local/watch-stdout.log 2>&1"
  echo "Add this line to crontab -e:"
  echo "$CRON_LINE"
fi
