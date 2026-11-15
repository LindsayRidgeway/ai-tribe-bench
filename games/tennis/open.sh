#!/bin/bash
# Start the tennis film in a Chrome tab, from a Spotlight entry.
#
#     games/tennis/open.sh                    the full 20-point demo film (demo3d.html)
#     games/tennis/open.sh replay.html        the top-down view
#     games/tennis/open.sh "replay3d.html?record=seasons/2026-spring/rally.json"
#
# Two things this has to get right, and neither is the tab.
#
# 1. The page cannot be opened from disk. `replay3d.html` is an ES module that imports three.js from
#    `vendor/` and fetches two ~700KB .glb bodies; `file://` refuses all three, and the film comes up
#    as an empty court with a console full of CORS. So there is a server, and the launcher's job is to
#    have one running.
#
# 2. The server has to outlive the launcher. A `nohup … &` from inside the double-clicked applet is a
#    child of a process macOS tears down when the applet exits; the port then closes under the tab that
#    is already loading. So the server is a launchd job, written once to ~/Library/LaunchAgents and
#    kickstarted rather than started. `python3 -m http.server` is single-threaded and that is fine: one
#    person, one film.

set -u
REPO="$HOME/ai_tribe"
PORT=8778
PAGE="${1:-demo3d.html}"
URL="http://localhost:$PORT/games/tennis/$PAGE"
LABEL="com.ait.tennis-server"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/ait-tennis-server.log"

# the film is served from the repository root, so check the page itself and not just the port: something
# else answering on 8778 is not this server and would open a 404 in the tab
up() { /usr/bin/curl -sf -o /dev/null --max-time 1 "$URL"; }

if ! up; then
  if [ ! -f "$PLIST" ]; then
    mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
    cat > "$PLIST" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/sh</string>
    <string>-c</string>
    <string>cd "$REPO" &amp;&amp; exec /usr/bin/python3 -m http.server $PORT --bind 127.0.0.1</string>
  </array>
  <key>RunAtLoad</key><false/>
  <key>KeepAlive</key><false/>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
PLISTEOF
  fi
  # bootout first so a stale job (repository moved, port changed) cannot shadow the file just written
  /bin/launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null
  /bin/launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/dev/null
  /bin/launchctl kickstart "gui/$(id -u)/$LABEL" 2>/dev/null
  for _ in $(seq 1 40); do up && break; sleep 0.1; done
fi

if ! up; then
  /usr/bin/osascript -e "display alert \"AIT Tennis\" message \"The film is served from $REPO on port $PORT and the server did not come up. The log is $LOG.\" as critical" >/dev/null 2>&1
  exit 1
fi

# Chrome, because Safari will not run this page and the film is a Chrome-shaped thing: `--use-angle=metal`
# is what makes WebGL work on this Mac, and opening the address in the browser that already has it right
# beats opening whatever the default is.
/usr/bin/open -a "Google Chrome" "$URL"
