#!/bin/bash
# ════════════════════════════════════════════════════════════
# 老卢舰队 · Mac-B 一键入列脚本
# 不需要 Apex，不需要 Python venv
# 只需要: git + bash + curl (macOS 自带)
# ════════════════════════════════════════════════════════════
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

FLEET_REPO="https://github.com/lcyluke/hermes-fleet-config.git"
HERMES_DIR="$HOME/.hermes"
FLEET_CONFIG="$HERMES_DIR/fleet_config.json"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   ⚓ 老卢舰队 · Mac Worker 一键入列     ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

# ─── Step 0: 检测 ───
MACHINE_ID=$(hostname)-$(whoami)
echo -e "🖥  本机: ${GREEN}$MACHINE_ID${NC}"

if [ -f "$FLEET_CONFIG" ]; then
    ROLE=$(python3 -c "import json; print(json.load(open('$FLEET_CONFIG')).get('role','?'))" 2>/dev/null || echo "?")
    if [ "$ROLE" != "?" ] && [ "$ROLE" != "null" ]; then
        echo -e "${YELLOW}⚠️  已是舰队节点 (角色: $ROLE)${NC}"
        echo -e "   如需重新加入: rm $FLEET_CONFIG 后重跑"
        exit 0
    fi
fi

# ─── Step 1: 安装 Hermes ───
if ! command -v hermes &>/dev/null; then
    echo ""
    echo -e "${CYAN}📦 Step 1/4: 安装 Hermes Agent...${NC}"
    curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/install.sh | bash
    echo -e "${GREEN}✅ Hermes 已安装${NC}"
else
    echo -e "${GREEN}✅ Hermes 已存在 ($(hermes --version 2>&1 | head -1))${NC}"
fi

# ─── Step 2: 配置 API Key ───
echo ""
echo -e "${CYAN}🔑 Step 2/4: 配置 DeepSeek API...${NC}"
if [ -f "$HERMES_DIR/.env" ] && grep -q "DEEPSEEK_API_KEY" "$HERMES_DIR/.env" 2>/dev/null; then
    echo -e "${GREEN}✅ API Key 已配置${NC}"
else
    echo -e "${YELLOW}⚠️  需要配置 DeepSeek API Key${NC}"
    echo "   手动运行: hermes setup model"
    echo "   → DeepSeek → deepseek-v4-pro → 填入 Key"
    echo ""
    read -p "   现在配置? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        hermes setup model
    else
        echo "   跳过。稍后运行 'hermes setup model' 补配置"
    fi
fi

# ─── Step 3: 克隆舰队配置 ───
echo ""
echo -e "${CYAN}📡 Step 3/4: 拉取舰队配置...${NC}"

TMPDIR=$(mktemp -d)
git clone --depth 1 "$FLEET_REPO" "$TMPDIR" 2>/dev/null

# 备份 .env
if [ -f "$HERMES_DIR/.env" ]; then
    cp "$HERMES_DIR/.env" /tmp/hermes-env-backup
fi

# 同步 config.yaml
if [ -f "$TMPDIR/config.yaml" ]; then
    cp "$TMPDIR/config.yaml" "$HERMES_DIR/config.yaml"
    echo -e "  ✅ config.yaml"
fi

# 同步 SOUL.md
if [ -f "$TMPDIR/SOUL.md" ]; then
    cp "$TMPDIR/SOUL.md" "$HERMES_DIR/SOUL.md"
    echo -e "  ✅ SOUL.md"
fi

# 同步 skills/
if [ -d "$TMPDIR/skills" ]; then
    rm -rf "$HERMES_DIR/skills"
    cp -r "$TMPDIR/skills" "$HERMES_DIR/skills"
    SKILL_COUNT=$(find "$HERMES_DIR/skills" -name "SKILL.md" | wc -l | tr -d ' ')
    echo -e "  ✅ skills/ ($SKILL_COUNT 个技能)"
fi

# 同步 profiles/
if [ -d "$TMPDIR/profiles" ]; then
    rm -rf "$HERMES_DIR/profiles"
    cp -r "$TMPDIR/profiles" "$HERMES_DIR/profiles"
    PROFILE_COUNT=$(ls -d "$HERMES_DIR/profiles"/*/ 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ✅ profiles/ ($PROFILE_COUNT 个 Agent)"
fi

# 恢复 .env
if [ -f /tmp/hermes-env-backup ]; then
    cp /tmp/hermes-env-backup "$HERMES_DIR/.env"
    rm /tmp/hermes-env-backup
    echo -e "  ✅ .env 已保留 (本地)"
fi

rm -rf "$TMPDIR"

# ─── Step 4: 注册 Worker 身份 ───
echo ""
echo -e "${CYAN}📝 Step 4/4: 注册 Worker 身份...${NC}"

mkdir -p "$HERMES_DIR"
cat > "$FLEET_CONFIG" << EOF
{
  "fleet_name": "老卢舰队",
  "role": "worker",
  "machine_id": "$MACHINE_ID",
  "repo_url": "$FLEET_REPO",
  "projects": [],
  "joined_at": "$(date -u +%Y-%m-%dT%H:%M:%S)",
  "worker_machine": "$MACHINE_ID"
}
EOF
echo -e "${GREEN}✅ Worker 身份已注册${NC}"

# ─── 完成 ───
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ Mac-B 已入列！                     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  角色:     ${YELLOW}WORKER${NC} (执行舰)"
echo -e "  机器:     ${CYAN}$MACHINE_ID${NC}"
echo -e "  配置来自: ${CYAN}$FLEET_REPO${NC}"
echo ""
echo -e "${CYAN}📋 下一步:${NC}"
echo ""
echo -e "  1. 克隆 Apex (如需 fleet 命令):"
echo -e "     ${YELLOW}mkdir -p ~/Desktop/2026AIAPP && cd ~/Desktop/2026AIAPP${NC}"
echo -e "     ${YELLOW}git clone https://github.com/lcyluke/apex.git${NC}"
echo -e "     ${YELLOW}cd Apex && python3 -m venv .venv && source .venv/bin/activate${NC}"
echo -e "     ${YELLOW}pip install -r requirements.txt${NC}"
echo ""
echo -e "  2. 上报心跳 (让 Origin 看到你):"
echo -e "     ${YELLOW}cd ~/Desktop/2026AIAPP/Apex && source .venv/bin/activate${NC}"
echo -e "     ${YELLOW}apex fleet report${NC}"
echo ""
echo -e "  3. 克隆项目代码:"
echo -e "     ${YELLOW}git clone https://github.com/lcyluke/badmintonSmallApp.git${NC}"
echo ""
echo -e "${CYAN}⚓ 欢迎入列，老卢舰队！${NC}"
echo ""
