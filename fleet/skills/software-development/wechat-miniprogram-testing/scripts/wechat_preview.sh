#!/bin/bash
# WeChat Mini-Program Preview via AppleScript
# Works when cli preview returns code 10 (the CLI port mismatch bug).
# Usage: ./wechat_preview.sh [/path/to/miniprogram]

PROJECT="${1:-/Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai/miniprogram}"
CLI="/Applications/wechatwebdevtools.app/Contents/MacOS/cli"

echo "📱 Opening project: $PROJECT"
$CLI open --project "$PROJECT" 2>/dev/null &
sleep 10

echo "📱 Triggering 工具 → 预览..."
osascript -e '
tell application "wechatwebdevtools" to activate
delay 2
tell application "System Events"
  tell process "wechatdevtools"
    tell menu "工具" of menu bar item "工具" of menu bar 1
      click menu item "预览  [⇧⌘P]"
    end tell
  end tell
end tell
' 2>/dev/null

echo "✅ Preview QR code should now be generating in the DevTools window."
echo "   Scan with WeChat on your phone. QR expires after a few minutes."
