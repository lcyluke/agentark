#!/usr/bin/env bash
# ⚓ AgentArk — One-liner installer
# curl -sSL https://raw.githubusercontent.com/lcyluke/agentark/main/scripts/install.sh | bash
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
INSTALL_DIR="${HOME}/.agentark"
BIN_DIR="${HOME}/.local/bin"
REPO="https://github.com/lcyluke/agentark.git"

echo ""
echo -e "${CYAN}${BOLD}⚓ AgentArk — Multi-Agent Operating System${NC}"
echo -e "${CYAN}   One person, infinite capacity.${NC}"
echo ""

# ── Check Python ──
PYTHON=""
for py in python3.12 python3.11 python3.10 python3; do
    if command -v "$py" &>/dev/null; then
        ver=$("$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        major=$("$py" -c 'import sys; print(sys.version_info.major)')
        minor=$("$py" -c 'import sys; print(sys.version_info.minor)')
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON="$py"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}❌ Python 3.10+ required but not found.${NC}"
    echo "   macOS: brew install python@3.12"
    echo "   Linux: apt install python3.12"
    exit 1
fi
echo -e "${GREEN}✅ Python: $PYTHON ($ver)${NC}"

# ── Check tmux ──
if command -v tmux &>/dev/null; then
    echo -e "${GREEN}✅ tmux: $(tmux -V)${NC}"
else
    echo -e "${RED}⚠️  tmux not found. Install it: brew install tmux${NC}"
fi

# ── Create venv ──
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${CYAN}📦 Updating existing install...${NC}"
    cd "$INSTALL_DIR"
    git pull --ff-only origin main 2>/dev/null || true
else
    echo -e "${CYAN}📦 Cloning AgentArk...${NC}"
    git clone "$REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo -e "${CYAN}🐍 Creating virtual environment...${NC}"
"$PYTHON" -m venv --system-site-packages .venv
source .venv/bin/activate

echo -e "${CYAN}📥 Installing dependencies...${NC}"
pip install --quiet --upgrade pip
pip install --quiet --only-binary ":all:" .
pip install --quiet zeroconf  # LAN peer discovery

# ── Create symlink ──
mkdir -p "$BIN_DIR"
AGENTARK_BIN="$INSTALL_DIR/.venv/bin/agentark"
if [ -f "$AGENTARK_BIN" ]; then
    ln -sf "$AGENTARK_BIN" "$BIN_DIR/agentark"
    echo -e "${GREEN}✅ Binary: $BIN_DIR/agentark${NC}"
else
    echo -e "${RED}❌ agentark binary not found after install${NC}"
    exit 1
fi

# ── Verify ──
VER=$("$BIN_DIR/agentark" --version 2>&1 || echo "UNKNOWN")
echo ""
echo -e "${GREEN}${BOLD}✅ AgentArk installed!${NC}"
echo -e "   ${VER}"
echo ""
echo -e "${BOLD}Next steps:${NC}"
echo -e "   1. Add ${CYAN}$BIN_DIR${NC} to your PATH (if not already)"
echo -e "      echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
echo -e "   2. Run: ${CYAN}agentark setup${NC}"
echo -e "   3. Quickstart: ${CYAN}agentark tutorial${NC}"
echo ""

# ── PATH hint ──
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    export PATH="$BIN_DIR:$PATH"
    echo -e "${CYAN}💡 Added $BIN_DIR to current PATH. Restart shell or run:${NC}"
    echo -e "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi
