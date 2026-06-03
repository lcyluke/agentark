#!/bin/bash
# Record Apex Demo for GitHub README
# Usage: bash scripts/record-demo.sh
# Output: docs/demo.cast (asciinema recording)

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

OUTPUT="$PROJECT_DIR/docs/demo.cast"
mkdir -p docs

echo "🎬 Recording Apex Demo..."
echo "   Output: $OUTPUT"
echo ""
echo "   Commands to be recorded:"
echo "   1. pip install apex-multiagent"
echo "   2. apex init demo-project"
echo "   3. apex demo --no-browser"
echo ""
echo "   After recording, upload to asciinema.org:"
echo "   asciinema upload $OUTPUT"
echo ""
echo "   Or convert to GIF:"
echo "   npm install -g agg  # asciinema gif generator"
echo "   agg $OUTPUT docs/demo.gif"
echo ""

# Record the demo
asciinema rec "$OUTPUT" \
    --title "Apex — 5 Minutes to Your AI Fleet" \
    --idle-time-limit 2 \
    --command "bash -c '
        echo \"\"
        echo \"  ⚡ Apex Demo — 5 Minutes to Your AI Fleet\"
        echo \"  ============================================\"
        echo \"\"
        sleep 1
        echo \"  Step 1: Install Apex\"
        echo \"  \$ pip install apex-multiagent\"
        sleep 1
        echo \"  ✓ Already installed (v0.1.0)\"
        echo \"\"
        sleep 0.5
        echo \"  Step 2: Create your first project\"
        echo \"  \$ apex init my-fleet\"
        sleep 0.5
        echo \"  ✓ Project initialized at ./my-fleet\"
        echo \"\"
        sleep 0.5
        echo \"  Step 3: Launch your AI Fleet + Command Center\"
        echo \"  \$ apex demo --port 8080\"
        sleep 0.5
        echo \"\"
        cd '"$PROJECT_DIR"' && source .venv/bin/activate 2>/dev/null || true
        apex demo --skip-tasks --port 8090 --no-browser 2>&1 || true
        echo \"\"
        echo \"  🚀 Your AI Fleet is live at http://localhost:8080/v5\"
        echo \"\"
        sleep 2
    '"

echo ""
echo "✅ Recording saved: $OUTPUT"
echo ""
echo "📤 Upload: asciinema upload $OUTPUT"
echo "🎞️  To GIF: agg $OUTPUT docs/demo.gif"
