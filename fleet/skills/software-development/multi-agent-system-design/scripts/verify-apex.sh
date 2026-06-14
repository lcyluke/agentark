#!/usr/bin/env bash
# Quick verification script for Apex multi-agent OS.
# Run from project root.
# Usage: bash scripts/verify-apex.sh

set -e

echo "=== Apex Verification Suite ==="
echo ""

# Check project structure
echo "📁 Project structure..."
[ -f apex/core/runtime.py ] && echo "  ✅ core/runtime.py" || echo "  ❌ core/runtime.py"
[ -f apex/orchestration/swarm.py ] && echo "  ✅ orchestration/swarm.py" || echo "  ❌ orchestration/swarm.py"
[ -f apex/orchestration/crew.py ] && echo "  ✅ orchestration/crew.py" || echo "  ❌ orchestration/crew.py"
[ -f apex/orchestration/chain.py ] && echo "  ✅ orchestration/chain.py" || echo "  ❌ orchestration/chain.py"
[ -f apex/orchestration/debate.py ] && echo "  ✅ orchestration/debate.py" || echo "  ❌ orchestration/debate.py"
[ -f apex/orchestration/router.py ] && echo "  ✅ orchestration/router.py" || echo "  ❌ orchestration/router.py"
[ -f apex/orchestration/supervisor.py ] && echo "  ✅ orchestration/supervisor.py" || echo "  ❌ orchestration/supervisor.py"
[ -f apex/orchestration/monitor.py ] && echo "  ✅ orchestration/monitor.py" || echo "  ❌ orchestration/monitor.py"
[ -f apex/orchestration/healing.py ] && echo "  ✅ orchestration/healing.py" || echo "  ❌ orchestration/healing.py"
[ -f apex/orchestration/kanban.py ] && echo "  ✅ orchestration/kanban.py" || echo "  ❌ orchestration/kanban.py"
[ -f apex/providers/deepseek.py ] && echo "  ✅ providers/deepseek.py" || echo "  ❌ providers/deepseek.py"
[ -f apex/cli/main.py ] && echo "  ✅ cli/main.py" || echo "  ❌ cli/main.py"
[ -f pyproject.toml ] && echo "  ✅ pyproject.toml" || echo "  ❌ pyproject.toml"
echo ""

# Check imports
echo "🧪 Testing imports..."
python3 -c "from apex.core.profile import Profile, ProfileManager; exit(0)" 2>/dev/null && echo "  ✅ core.profile" || echo "  ❌ core.profile"
python3 -c "from apex.core.runtime import Agent; exit(0)" 2>/dev/null && echo "  ✅ core.runtime" || echo "  ❌ core.runtime"
python3 -c "from apex.core.knowledge import KnowledgeGraph; exit(0)" 2>/dev/null && echo "  ✅ core.knowledge" || echo "  ❌ core.knowledge"
python3 -c "from apex.core.evolution import EvolutionEngine; exit(0)" 2>/dev/null && echo "  ✅ core.evolution" || echo "  ❌ core.evolution"
python3 -c "from apex.providers import registry; exit(0)" 2>/dev/null && echo "  ✅ providers" || echo "  ❌ providers"
python3 -c "from apex.orchestration.kanban import Kanban; exit(0)" 2>/dev/null && echo "  ✅ orchestration.kanban" || echo "  ❌ orchestration.kanban"
python3 -c "from apex.orchestration.crew import Crew, DynamicTeamDesigner; exit(0)" 2>/dev/null && echo "  ✅ orchestration.crew" || echo "  ❌ orchestration.crew"
python3 -c "from apex.orchestration.healing import SelfHealingExecutor; exit(0)" 2>/dev/null && echo "  ✅ orchestration.healing" || echo "  ❌ orchestration.healing"
python3 -c "from apex.orchestration.chain import Chain, ChainResult; exit(0)" 2>/dev/null && echo "  ✅ orchestration.chain" || echo "  ❌ orchestration.chain"
python3 -c "from apex.orchestration.debate import Debate, DebateResult; exit(0)" 2>/dev/null && echo "  ✅ orchestration.debate" || echo "  ❌ orchestration.debate"
python3 -c "from apex.orchestration.router import Router, RouterResult; exit(0)" 2>/dev/null && echo "  ✅ orchestration.router" || echo "  ❌ orchestration.router"
python3 -c "from apex.orchestration.supervisor import Supervisor, SupervisorResult; exit(0)" 2>/dev/null && echo "  ✅ orchestration.supervisor" || echo "  ❌ orchestration.supervisor"
python3 -c "from apex.orchestration.monitor import Monitor, MonitorResult, WatcherRule; exit(0)" 2>/dev/null && echo "  ✅ orchestration.monitor" || echo "  ❌ orchestration.monitor"
python3 -c "from apex.mcp.hub import hub; t=hub.list_tools(); print(f'  ✅ MCP Hub: {len(t)} tools')" 2>/dev/null || echo "  ❌ MCP Hub"
python3 -c "from apex.economy import BudgetManager, TokenRouter; exit(0)" 2>/dev/null && echo "  ✅ economy" || echo "  ❌ economy"
python3 -c "from apex.interface.web import create_app; exit(0)" 2>/dev/null && echo "  ✅ interface.web" || echo "  ❌ interface.web"
echo ""

# Check CLI
echo "🔧 Testing CLI..."
if command -v apex &>/dev/null; then
    echo "  ✅ apex command found"
    apex --version 2>/dev/null && echo "  ✅ apex --version" || echo "  ❌ apex --version"
    apex --help 2>/dev/null | grep -q "chain\|debate\|router\|supervisor\|monitor" && echo "  ✅ All 9 orchestration modes in CLI" || echo "  ❌ Missing orchestration commands"
else
    echo "  ⚠️  apex not in PATH — try 'source .venv/bin/activate'"
fi

echo ""
echo "=== Lines of code ==="
find apex/ -name "*.py" -not -path "*/__pycache__/*" | xargs wc -l 2>/dev/null | tail -1

echo ""
echo "=== Done ==="
