#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  LeadFlow AI — Mac Auto-Start Installer
#  Registers a LaunchAgent so the app starts on login
# ─────────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.leadflow.ai.plist"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
LOG_DIR="$SCRIPT_DIR/logs"

mkdir -p "$LOG_DIR"

cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.leadflow.ai</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_PYTHON</string>
        <string>$SCRIPT_DIR/app.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/leadflow.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/leadflow-error.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo ""
echo "✅ LeadFlow AI will now start automatically on login."
echo "   Dashboard: http://localhost:8080"
echo "   Logs:      $LOG_DIR/leadflow.log"
echo ""
echo "To stop:    launchctl unload $PLIST"
echo "To restart: launchctl unload $PLIST && launchctl load $PLIST"
