#!/bin/bash
# ════════════════════════════════════════════════════════════
# 老卢舰队 · Mac Worker 一键入列 (v2 — 单仓库)
# 从 lcyluke/apex 拉取全部配置
# 只需要: git + bash (macOS 自带)
# ════════════════════════════════════════════════════════════
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
MACHINE_ID=$(hostname)-$(whoami)
HERMES_DIR="$HOME/.hermes"
FLEET_CONFIG="$HERMES_DIR/fleet_config.json"
APEX_DIR="$HOME/Desktop/2026AIAPP/Apex"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   ⚓ 老卢舰队 · Mac Worker 一键入列 v2  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo -e "  仓库: ${YELLOW}lcyluke/apex${NC} (唯一)"
echo ""

# ─── Step 0: 检测 ───
if [ -f "$FLEET_CONFIG" ]; then
    ROLE=$(python3 -c "import json; print(json.load(open('$FLEET_CONFIG')).get('role','?'))" 2>/dev/null || echo "?")
    if [ "$ROLE" != "?" ] && [ "$ROLE" != "null" ] && [ "$ROLE" != "None" ]; then
        echo -e "${YELLOW}⚠️  已是舰队节点 (角色: $ROLE)${NC}"
        exit 0
    fi
fi

# ─── Step 1: 安装 Hermes ───
if ! command -v hermes &>/dev/null; then
    echo -e "${CYAN}📦 Step 1/5: 安装 Hermes Agent...${NC}"
    curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/install.sh | bash
    echo -e "${GREEN}✅ Hermes 已安装${NC}"
else
    echo -e "${GREEN}✅ Hermes 已存在${NC}"
fi

# ─── Step 2: 配置 API ───
echo ""
echo -e "${CYAN}🔑 Step 2/5: DeepSeek API Key${NC}"
if [ -f "$HERMES_DIR/.env" ] && grep -q "DEEPSEEK_API_KEY" "$HERMES_DIR/.env" 2>/dev/null; then
    echo -e "${GREEN}✅ 已配置${NC}"
else
    echo -e "${YELLOW}⚠️  请手动运行: hermes setup model → DeepSeek → deepseek-v4-pro${NC}"
fi

# ─── Step 3: 克隆 Apex ───
echo ""
echo -e "${CYAN}📡 Step 3/5: 克隆 Apex 仓库...${NC}"
mkdir -p "$HOME/Desktop/2026AIAPP"
if [ -d "$APEX_DIR" ]; then
    cd "$APEX_DIR" && git pull origin main 2>/dev/null
    echo -e "${GREEN}✅ Apex 已更新${NC}"
else
    git clone https://github.com/lcyluke/apex.git "$APEX_DIR"
    echo -e "${GREEN}✅ Apex 已克隆${NC}"
fi

# ─── Step 4: 同步舰队配置 → ~/.hermes/ ───
echo ""
echo -e "${CYAN}🔄 Step 4/5: 同步舰队配置...${NC}"

FLEET_DIR="$APEX_DIR/fleet"
if [ ! -d "$FLEET_DIR" ]; then
    echo -e "${RED}✗ fleet/ 目录不存在，Origin 尚未初始化${NC}"
    exit 1
fi

# 备份 .env
[ -f "$HERMES_DIR/.env" ] && cp "$HERMES_DIR/.env" /tmp/hermes-env-backup

# 同步文件
for f in config.yaml SOUL.md; do
    [ -f "$FLEET_DIR/$f" ] && cp "$FLEET_DIR/$f" "$HERMES_DIR/$f" && echo "  ✅ $f"
done

for d in skills profiles; do
    if [ -d "$FLEET_DIR/$d" ]; then
        rm -rf "$HERMES_DIR/$d"
        cp -r "$FLEET_DIR/$d" "$HERMES_DIR/$d"
        echo "  ✅ $d/ ($(find "$HERMES_DIR/$d" -name 'SKILL.md' 2>/dev/null | wc -l | tr -d ' ') skills)"
    fi
done

# 恢复 .env
[ -f /tmp/hermes-env-backup ] && cp /tmp/hermes-env-backup "$HERMES_DIR/.env" && rm /tmp/hermes-env-backup && echo "  ✅ .env 已保留"

# ─── Step 5: 注册 Worker ───
echo ""
echo -e "${CYAN}📝 Step 5/5: 注册 Worker 身份...${NC}"
mkdir -p "$HERMES_DIR"
cat > "$FLEET_CONFIG" << EOF
{
  "fleet_name": "老卢舰队",
  "role": "worker",
  "machine_id": "$MACHINE_ID",
  "projects": [],
  "joined_at": "$(date -u +%Y-%m-%dT%H:%M:%S)",
  "worker_machine": "$MACHINE_ID"
}
EOF
echo -e "${GREEN}✅ Worker 已注册${NC}"

# ─── 完成 ───
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ Mac Worker 已入列！                 ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  角色:   ${YELLOW}WORKER${NC}"
echo -e "  机器:   ${CYAN}$MACHINE_ID${NC}"
echo -e "  仓库:   ${CYAN}lcyluke/apex${NC}"
echo ""
echo -e "${CYAN}📋 下一步:${NC}"
echo ""
echo -e "  安装 Apex CLI:"
echo -e "    ${YELLOW}cd ~/Desktop/2026AIAPP/Apex${NC}"
echo -e "    ${YELLOW}python3 -m venv .venv && source .venv/bin/activate${NC}"
echo -e "    ${YELLOW}pip install -r requirements.txt${NC}"
echo ""
echo -e "  上报心跳 (GPU+状态):"
echo -e "    ${YELLOW}apex fleet report${NC}"
echo ""
echo -e "  查看舰队:"
echo -e "    ${YELLOW}apex fleet nodes${NC}"
echo ""
echo -e "${CYAN}⚓ 欢迎入列，老卢舰队！${NC}"
