"""Apex Audit & Flow — 审批审计 + 数据流时序

= Approval engine: 项目立项审批 + 风险操作审批 + 审计日志
= Data flow: 任务全生命周期时序追踪
"""
from __future__ import annotations

import json, sqlite3, os, time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


APEX_HOME = Path(os.path.expanduser("~/.apex"))
KANBAN_DB = APEX_HOME / "kanban.db"
PROJECTS_FILE = APEX_HOME / "projects_registry.json"
AUDIT_LOG = APEX_HOME / "audit_log.json"


# ══════════════════════════════════════════
# APPROVAL ENGINE
# ══════════════════════════════════════════

APPROVAL_TYPES = {
    "project_proposal": {"name": "项目立项", "icon": "ti-target-arrow", "color": "violet"},
    "project_module": {"name": "添加模块", "icon": "ti-puzzle", "color": "blue"},
    "agent_delete": {"name": "删除Agent", "icon": "ti-user-x", "color": "red"},
    "gpu_shutdown": {"name": "GPU关机", "icon": "ti-plug-connected-x", "color": "amber"},
    "config_change": {"name": "配置修改", "icon": "ti-settings", "color": "teal"},
    "data_export": {"name": "数据导出", "icon": "ti-download", "color": "blue"},
}


def get_approval_queue() -> dict:
    """Get all pending approvals"""
    items = []
    
    # 1. Project proposals (from registry)
    if PROJECTS_FILE.exists():
        with open(PROJECTS_FILE) as f:
            reg = json.load(f)
        for name, proj in reg.get("projects", {}).items():
            if proj.get("status") == "proposed":
                items.append({
                    "id": f"proj-{name}",
                    "type": "project_proposal",
                    "title": f"项目立项: {name}",
                    "detail": proj.get("goal", "")[:100],
                    "proposer": proj.get("proposed_by", "unknown"),
                    "time": proj.get("proposed_at", ""),
                    "risk": "medium",
                })
    
    # 2. Blocked tasks needing attention (from Kanban)
    if KANBAN_DB.exists():
        conn = sqlite3.connect(str(KANBAN_DB))
        conn.row_factory = sqlite3.Row
        try:
            blocked = conn.execute(
                "SELECT id, title, assignee, priority FROM tasks WHERE status='blocked' LIMIT 5"
            ).fetchall()
            for b in blocked:
                items.append({
                    "id": f"task-{b['id'][:12]}",
                    "type": "agent_delete" if "delete" in (b["title"] or "").lower() else "config_change",
                    "title": f"堵塞任务: {(b['title'] or '')[:60]}",
                    "detail": f"Agent: {b['assignee']}, Priority: {b['priority']}",
                    "proposer": b["assignee"] or "system",
                    "time": datetime.now().isoformat(),
                    "risk": "high" if b["priority"] and int(b["priority"]) <= 1 else "medium",
                })
        finally:
            conn.close()
    
    # 3. GPU shutdown requests
    items.append({
        "id": "gpu-auto-shutdown",
        "type": "gpu_shutdown",
        "title": "GPU自动关机策略 (30分钟空闲)",
        "detail": "cabf47a278 + cac99c71 — 当前离线，下次启动后生效",
        "proposer": "ops-engineer",
        "time": datetime.now().isoformat(),
        "risk": "low",
    })
    
    return {
        "total": len(items),
        "pending": len([i for i in items if i.get("status") != "resolved"]),
        "items": items,
        "types": APPROVAL_TYPES,
    }


def approve_item(item_id: str, approver: str = "老卢") -> dict:
    """Approve a pending item"""
    if item_id.startswith("proj-"):
        name = item_id.replace("proj-", "")
        from apex.interface.project_registry import approve_project
        result = approve_project(name, f"始祖Agent·小卢 (审批人: {approver})")
        _log_audit("project_approved", approver, f"Approved project: {name}")
        return result
    
    _log_audit("approved", approver, f"Approved: {item_id}")
    return {"ok": True, "item": item_id, "action": "approved", "by": approver}


def reject_item(item_id: str, reason: str = "", rejector: str = "老卢") -> dict:
    """Reject a pending item"""
    _log_audit("rejected", rejector, f"Rejected: {item_id} — {reason}")
    return {"ok": True, "item": item_id, "action": "rejected", "reason": reason, "by": rejector}


# ══════════════════════════════════════════
# AUDIT LOG
# ══════════════════════════════════════════

def _log_audit(action: str, actor: str, detail: str):
    """Write audit log entry"""
    log = {"action": action, "actor": actor, "detail": detail, "timestamp": datetime.now().isoformat()}
    entries = []
    if AUDIT_LOG.exists():
        with open(AUDIT_LOG) as f:
            entries = json.load(f)
    entries.append(log)
    if len(entries) > 500:
        entries = entries[-500:]
    with open(AUDIT_LOG, "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def get_audit_log(limit: int = 50) -> dict:
    """Get audit log entries"""
    if not AUDIT_LOG.exists():
        return {"total": 0, "entries": []}
    with open(AUDIT_LOG) as f:
        entries = json.load(f)
    return {
        "total": len(entries),
        "entries": list(reversed(entries[-limit:])),
    }


def get_audit_stats() -> dict:
    """Audit statistics"""
    if not AUDIT_LOG.exists():
        return {"total": 0, "today": 0, "by_action": {}, "by_actor": {}}
    with open(AUDIT_LOG) as f:
        entries = json.load(f)
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_entries = [e for e in entries if e.get("timestamp", "").startswith(today)]
    
    by_action = defaultdict(int)
    by_actor = defaultdict(int)
    for e in entries:
        by_action[e.get("action", "unknown")] += 1
        by_actor[e.get("actor", "unknown")] += 1
    
    return {
        "total": len(entries),
        "today": len(today_entries),
        "by_action": dict(sorted(by_action.items(), key=lambda x: x[1], reverse=True)[:10]),
        "by_actor": dict(by_actor),
    }


# ══════════════════════════════════════════
# DATA FLOW TIMELINE
# ══════════════════════════════════════════

def get_data_flow_timeline(project: str = None) -> dict:
    """Build a data flow timeline showing task lifecycle"""
    kanban_db = KANBAN_DB
    if not kanban_db.exists():
        return {"error": "kanban.db not found", "nodes": [], "edges": []}
    
    conn = sqlite3.connect(str(kanban_db))
    conn.row_factory = sqlite3.Row
    try:
        project_filter = f"%[{project}]%" if project else "%"
        
        # Get all tasks with their status transitions
        tasks = conn.execute(
            "SELECT id, title, assignee, status, priority, created_at, completed_at "
            "FROM tasks WHERE title LIKE ? ORDER BY created_at DESC LIMIT 50",
            (project_filter,)
        ).fetchall()
        
        # Build timeline nodes (each task status change is a node)
        nodes = []
        edges = []
        
        status_order = {"todo": 0, "ready": 1, "in_progress": 2, "done": 3, "failed": 3, "blocked": 2}
        status_color = {"todo": "#5d6878", "ready": "#60a5fa", "in_progress": "#fbbf24", "done": "#34d399", "failed": "#f87171", "blocked": "#f87171"}
        
        prev_node = None
        for t in tasks:
            node_id = t["id"][:12]
            stage = t["status"]
            nodes.append({
                "id": node_id,
                "label": (t["title"] or "")[:40],
                "stage": stage,
                "agent": t["assignee"] or "unassigned",
                "priority": t["priority"],
                "color": status_color.get(stage, "#5d6878"),
                "time": t["created_at"],
            })
            
            if prev_node:
                edges.append({"from": prev_node, "to": node_id, "label": "next"})
            prev_node = node_id
        
        # Summary
        by_stage = defaultdict(int)
        for t in tasks:
            by_stage[t["status"]] += 1
        
        # Flow statistics
        total = len(tasks)
        done = by_stage.get("done", 0)
        
        return {
            "project": project or "all",
            "total_tasks": total,
            "completion_pct": round(done / max(1, total) * 100),
            "nodes": nodes[:30],
            "edges": edges[:30],
            "by_stage": dict(by_stage),
            "flow_statistics": {
                "input_stage": "用户自然语言 → AI指挥官拆解",
                "orchestration": "编排官 → 技能匹配 → Agent分配",
                "execution": "Agent执行 → 工具调用 → 结果输出",
                "review": "验证Agent → 质量检查 → 闸门审批",
                "output": "部署上线 → 用户评价 → 技能沉淀",
            },
        }
    finally:
        conn.close()
