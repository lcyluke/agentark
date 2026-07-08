#!/bin/bash
# fleet-start.sh — 一键启动老卢舰队
# 用法: bash scripts/fleet-start.sh
set -e

AGENTS=(pm architect backend-dev frontend-dev devops qa-engineer github-release)
SESSION="agentark-fleet"

# 1. 杀旧舰队（如果存在）
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "⚠️  发现旧舰队，正在关闭..."
  tmux kill-session -t "$SESSION"
  sleep 1
fi

# 2. 创建新舰队
echo "🚀 启动老卢舰队..."
tmux new-session -d -s "$SESSION" -n "${AGENTS[0]}" -x 160 -y 40 \
  "hermes -p ${AGENTS[0]} chat"
echo "   ✅ ${AGENTS[0]}"

# 3. 添加其余Agent
for agent in "${AGENTS[@]:1}"; do
  tmux new-window -t "$SESSION" -n "$agent" "hermes -p $agent chat"
  echo "   ✅ $agent"
  sleep 0.5
done

# 4. 验证
sleep 2
WINDOW_COUNT=$(tmux list-windows -t "$SESSION" 2>/dev/null | wc -l | tr -d ' ')
PROC_COUNT=$(ps aux | grep "hermes -p" | grep -v grep | wc -l | tr -d ' ')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎉 老卢舰队已启动！"
echo "  📊 窗口: $WINDOW_COUNT | 进程: $PROC_COUNT"
echo "  🖥️  附加: tmux attach -t $SESSION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
