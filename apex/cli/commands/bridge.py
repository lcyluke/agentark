"""
Apex-Hermes Bridge Manager — 6 monitoring agents + sync engine.

CLI:
  apex bridge init      Create the 6 default monitoring agents
  apex bridge sync      Run a sync cycle (update Kanban)
  apex bridge status    Show bridge health
  apex bridge agents    List monitoring agents + their status
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from datetime import datetime

from apex.core.profile import ProfileManager, APEX_HOME, Profile, SoulConfig

# ── 6 Monitoring Agent Definitions ──────────────────────────────

BRIDGE_AGENTS = {
    "origin": {
        "display": "⚓ 始祖 · 项目群总指挥官",
        "role": "Origin Agent — Portfolio Commander",
        "personality": "舰队总司令，冷静果断。每条消息以⚓开头。",
        "expertise": ["多项目群管理", "Agent技能复制迁移", "战略目标分解", "资源平衡调度", "PM Agent部署"],
        "skills": ["origin-command", "profile-replication", "portfolio-management", "hermes-agent", "kanban-orchestrator"],
    },
    "fleet-commander": {
        "display": "🧭 指挥官 · Hermes舰队监控",
        "role": "Apex-Hermes Fleet Commander",
        "personality": "老练的舰队司令，冷静决策，对异常零容忍",
        "expertise": ["Hermes 多Profile编排", "Apex Kanban任务调度", "多Agent协调", "监控告警汇总", "舰队状态日报"],
        "skills": ["hermes-agent", "monitoring-system", "kanban-orchestrator"],
    },
    "session-scout": {
        "display": "🔍 斥候 · 会话侦测",
        "role": "Hermes Session Scout",
        "personality": "敏锐的侦察兵，不漏掉任何一个新会话",
        "expertise": ["Hermes state.db读取", "会话摘要提取", "Kanban任务创建", "新会话自动归类"],
        "skills": ["hermes-agent", "kanban-worker"],
    },
    "token-guardian": {
        "display": "💰 军需官 · Token预算守卫",
        "role": "Token Budget Guardian",
        "personality": "精打细算的财务官，每一分钱都要有据可查",
        "expertise": ["Token用量统计", "成本追踪USD/CNY", "预算预警", "deepseek定价追踪"],
        "skills": ["hermes-agent", "monitoring-system", "token-optimization"],
    },
    "gpu-sentinel": {
        "display": "⚡ 轮机长 · GPU成本哨兵",
        "role": "GPU Cost Sentinel",
        "personality": "沉默寡言的引擎室工程师，只在异常时出声",
        "expertise": ["GPU利用率/显存/温度监控", "AutoDL成本追踪", "闲时自动关机建议"],
        "skills": ["hermes-agent", "monitoring-system"],
    },
    "profile-syncer": {
        "display": "📡 通讯官 · Profile状态同步",
        "role": "Profile State Syncer",
        "personality": "全天候值守的通讯兵，连接状态一目了然",
        "expertise": ["Hermes profile list解析", "Gateway运行状态检测", "Profile↔Apex agent映射", "多平台消息通道状态"],
        "skills": ["hermes-agent", "kanban-worker"],
    },
    "cron-medic": {
        "display": "🛡️ 军医 · Cron健康巡检",
        "role": "Cron Health Inspector",
        "personality": "一丝不苟的军医，定时体检，不放过任何隐患",
        "expertise": ["Hermes cron job健康状态", "Job执行历史/失败率", "定时任务依赖链检查"],
        "skills": ["hermes-agent", "monitoring-system"],
    },
}


def init_bridge_agents(console=None):
    """Create/update the 6 default bridge monitoring agents."""
    pm = ProfileManager()
    created = []
    updated = []

    for name, cfg in BRIDGE_AGENTS.items():
        exists = False
        try:
            pm.load(name)
            exists = True
        except FileNotFoundError:
            pass

        profile = Profile(
            name=name,
            display=cfg["display"],
            soul=SoulConfig(
                role=cfg["role"],
                expertise=cfg["expertise"],
                personality=cfg["personality"],
                communication="航海隐喻风格，数据优先，趋势说话",
            ),
            skills=cfg["skills"],
            auto_improve=True,
            token_budget=100000,
        )
        pm.save(profile)
        if exists:
            updated.append(name)
        else:
            created.append(name)

    if console:
        console.print(f"[green]✅ Bridge Agents: {len(created)} created, {len(updated)} updated[/]")
        for a in created:
            console.print(f"   🆕 {a}")
        for a in updated:
            console.print(f"   🔄 {a}")

    return {"created": created, "updated": updated}


def get_bridge_status() -> dict:
    """Get bridge health status from Kanban task states."""
    from apex.orchestration.kanban import Kanban
    kanban_db = APEX_HOME / "kanban.db"

    if not kanban_db.exists():
        return {"status": "offline", "agents": [], "message": "kanban.db 不存在，请先运行 apex bridge init"}

    k = Kanban(kanban_db)
    tasks = k.list_tasks()

    watch_ids = ["watch-sessions", "watch-tokens", "watch-gpu", "watch-profiles", "watch-cron", "fleet-status"]
    agents = []
    for t in tasks:
        if t.id in watch_ids:
            agents.append({
                "id": t.id,
                "assignee": t.assignee,
                "title": t.title,
                "status": t.status,
                "output": (t.output or "")[:300],
                "completed_at": t.completed_at,
            })

    all_ok = all(a["status"] == "done" for a in agents)
    online_count = sum(1 for a in agents if a["status"] in ("done", "in_progress"))

    return {
        "status": "healthy" if all_ok else ("degraded" if online_count >= 3 else "offline"),
        "agents": agents,
        "total": len(agents),
        "healthy": sum(1 for a in agents if a["status"] == "done"),
        "degraded": sum(1 for a in agents if a["status"] == "in_progress"),
        "offline": sum(1 for a in agents if a["status"] == "blocked"),
        "last_sync": agents[0].get("completed_at") if agents else None,
    }


def run_bridge_sync(console=None):
    """Run one sync cycle via bridge_sync engine."""
    from apex.orchestration.bridge_sync import main
    main()
    if console:
        status = get_bridge_status()
        console.print(f"[green]✅ Sync complete | {status['healthy']}/{status['total']} healthy[/]")
    return get_bridge_status()
