"""任务管线引擎 — 正常流程 + 专项直达

两种流程模式:

  📋 正常流程 (Normal Pipeline)
     需求文本 → AI拆解 → 人工确认(可选) → 批量创建Task → 分派 → 监控 → 通知
     适用: 新功能、大需求、跨Agent协作
     
     阶段: ANALYZE → REVIEW → DISPATCH → EXECUTE → MONITOR → DONE

  ⚡ 专项流程 (Direct Pipeline)  
     指令直达 → 指定Agent → 创建单Task → 立即执行 → 完成通知
     适用: Bug修复、快速调整、单Agent任务
     
     阶段: ROUTE → CREATE → EXECUTE → DONE

集成点:
  - message_router: 自动识别意图 → 选择流程模式
  - web.py: POST /api/pipeline/normal  /api/pipeline/direct
  - CLI: apex pipeline normal "req"  /  apex pipeline direct "task" --agent X
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ════════════════════════════════════════════════════════════
# 阶段定义
# ════════════════════════════════════════════════════════════

class PipelineMode(str, Enum):
    NORMAL = "normal"     # 正常流程: 需求→拆解→分派
    DIRECT = "direct"     # 专项直达: 指令→Agent


class Stage(str, Enum):
    """管线阶段"""
    # 正常流程阶段
    ANALYZE = "analyze"       # 需求分析拆解中
    REVIEW = "review"         # 等待人工确认
    DISPATCH = "dispatch"     # 批量创建+分派中
    EXECUTE = "execute"       # Agent执行中
    MONITOR = "monitor"       # 完成监控中
    
    # 专项流程阶段
    ROUTE = "route"           # 意图路由识别
    CREATE = "create"         # 直接创建单Task
    
    # 终态
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"

    # 快捷阶段（跳过拆解）
    SKIP_ANALYZE = "skip_analyze"  # 用户已指定Agent，跳过拆解


# 正常流程阶段流转
NORMAL_STAGES = [
    Stage.ANALYZE,
    Stage.REVIEW,
    Stage.DISPATCH,
    Stage.EXECUTE,
    Stage.MONITOR,
    Stage.DONE,
]

# 专项流程阶段流转
DIRECT_STAGES = [
    Stage.ROUTE,
    Stage.CREATE,
    Stage.EXECUTE,
    Stage.DONE,
]


# ════════════════════════════════════════════════════════════
# 数据结构
# ════════════════════════════════════════════════════════════

@dataclass
class PipelineRun:
    """一次管线执行记录"""
    id: str = field(default_factory=lambda: f"pipe_{uuid.uuid4().hex[:8]}")
    mode: PipelineMode = PipelineMode.NORMAL
    project: str = ""
    requirement: str = ""
    target_agent: str = ""        # 专项流程的目标Agent
    
    stage: Stage = Stage.ANALYZE
    stage_history: list[dict] = field(default_factory=list)  # [{stage, at, note}]
    
    # 拆解结果（正常流程）
    epic_title: str = ""
    task_count: int = 0
    tasks: list[dict] = field(default_factory=list)
    
    # 执行结果
    task_ids: list[str] = field(default_factory=list)
    epic_id: str = ""
    completed_count: int = 0
    failed_count: int = 0
    
    # 时间戳
    created_at: str = ""
    completed_at: str = ""
    
    # 通知
    notify_on_complete: bool = True
    notify_target: str = "origin"  # weixin / local
    
    def advance(self, next_stage: Stage, note: str = ""):
        """推进到下一阶段"""
        self.stage_history.append({
            "from": self.stage.value,
            "to": next_stage.value,
            "at": datetime.now().isoformat(),
            "note": note,
        })
        self.stage = next_stage
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "mode": self.mode.value,
            "project": self.project,
            "requirement": self.requirement[:100],
            "target_agent": self.target_agent,
            "stage": self.stage.value,
            "epic_title": self.epic_title,
            "task_count": self.task_count,
            "task_ids": self.task_ids,
            "completed": self.completed_count,
            "failed": self.failed_count,
            "created_at": self.created_at,
            "stage_count": len(self.stage_history),
        }


# ════════════════════════════════════════════════════════════
# 项目→Agent映射（快速路由）
# ════════════════════════════════════════════════════════════

PROJECT_AGENT_MAP: dict[str, dict[str, str]] = {
    # project_key: {domain_keyword: agent_profile}
    "finopsai": {
        "架构": "finops-architect",
        "architect": "finops-architect",
        "后端": "finops-backend",
        "backend": "finops-backend",
        "api": "finops-backend",
        "接口": "finops-backend",
        "前端": "finops-frontend",
        "frontend": "finops-frontend",
        "页面": "finops-frontend",
        "ui": "finops-frontend",
        "可视化": "finops-frontend",
        "dashboard": "finops-frontend",
        "部署": "finops-devops",
        "devops": "finops-devops",
        "k8s": "finops-devops",
        "docker": "finops-devops",
        "cicd": "finops-devops",
        "安全": "finops-security",
        "security": "finops-security",
        "权限": "finops-security",
        "rbac": "finops-security",
        "加密": "finops-security",
        "ai": "finops-ai",
        "预测": "finops-ai",
        "模型": "finops-ai",
        "算法": "finops-ai",
        "异常": "finops-ai",
        "pm": "finops-pm",
        "规划": "finops-pm",
        "需求": "finops-pm",
    },
    "badminton-coach-ai": {
        "前端": "frontend-dev",
        "小程序": "frontend-dev",
        "页面": "frontend-dev",
        "后端": "architect",
        "api": "architect",
        "视觉": "ai-vision",
        "识别": "ai-vision",
        "算法": "ai-algorithm",
        "ai": "ai-algorithm",
        "内容": "content-marketing",
        "pm": "badminton-pm",
    },
    "apex": {
        "运维": "ops-engineer",
        "部署": "ops-engineer",
        "安全": "security-compliance",
        "dashboard": "apex-pm",
        "pm": "apex-pm",
    },
}


# ════════════════════════════════════════════════════════════
# 意图识别 — 自动选择正常/专项流程
# ════════════════════════════════════════════════════════════

@dataclass
class IntentResult:
    """意图识别结果"""
    mode: PipelineMode
    project: str
    target_agent: str = ""        # 专项流程的目标Agent
    requirement: str = ""         # 清洗后的需求文本
    confidence: float = 0.0
    reason: str = ""


# 直接指令模式 — 明确指定Agent
DIRECT_PATTERNS = [
    # @agent 格式
    (r'@(\S+)\s+(.+)', "mention"),
    # "agent名，做XXX"
    (r'(finops-\w+|frontend-dev|architect|ai-\w+|ops-\w+)\s*[,，]\s*(.+)', "comma"),
    # "让agent做XXX" / "叫agent做XXX"
    (r'[让叫派](finops-\w+|frontend-dev|architect|ai-\w+|ops-\w+)\s*(?:去)?\s*(.+)', "delegate"),
    # "agent来修XXX" / "agent处理XXX"
    (r'(finops-\w+|frontend-dev|architect)\s*(?:来|去|帮我)\s*(.+)', "direct"),
]

# 正常流程标识 — 需要拆解的需求
NORMAL_PATTERNS = [
    r'(?:需要|要做|实现|开发|搭建|设计|构建)\S*',
    r'(?:功能|模块|系统|平台|页面|接口)',
]


def identify_intent(message: str, project: str = "") -> IntentResult:
    """
    识别用户意图，选择流程模式。
    
    优先级:
      1. 明确@Agent → 专项流程
      2. "Agent名，做XXX" → 专项流程
      3. "需要做XXX功能" → 正常流程
      4. 默认 → 正常流程
    """
    import re
    
    msg = message.strip()
    
    # 1. 检查直接指令模式
    for pattern, ptype in DIRECT_PATTERNS:
        m = re.search(pattern, msg)
        if m:
            agent = m.group(1)
            task = m.group(2).strip()
            return IntentResult(
                mode=PipelineMode.DIRECT,
                project=project,
                target_agent=agent,
                requirement=task,
                confidence=0.9,
                reason=f"检测到直接指令: @{agent} ({ptype})",
            )
    
    # 2. 检查正常流程模式
    for pattern in NORMAL_PATTERNS:
        if re.search(pattern, msg):
            return IntentResult(
                mode=PipelineMode.NORMAL,
                project=project,
                requirement=msg,
                confidence=0.7,
                reason="检测到需求关键词，走正常拆解流程",
            )
    
    # 3. 默认：正常流程
    return IntentResult(
        mode=PipelineMode.NORMAL,
        project=project,
        requirement=msg,
        confidence=0.5,
        reason="默认走正常流程",
    )


# ════════════════════════════════════════════════════════════
# 正常流程执行器
# ════════════════════════════════════════════════════════════

def run_normal_pipeline(
    requirement: str,
    project: str,
    auto_confirm: bool = True,
    task_manager=None,
) -> PipelineRun:
    """
    执行正常流程管线。
    
    Args:
        requirement: 需求文本
        project: 项目key
        auto_confirm: True=跳过人工确认, False=等待确认后继续
        task_manager: 可注入的TaskManager实例
    """
    run = PipelineRun(
        mode=PipelineMode.NORMAL,
        project=project,
        requirement=requirement,
        created_at=datetime.now().isoformat(),
    )

    # ── Stage 1: ANALYZE ──
    run.advance(Stage.ANALYZE, "开始需求拆解")
    
    from agentark.orchestration.task_decomposer import (
        decompose_requirement, dispatch_tasks,
    )
    result = decompose_requirement(requirement, project)
    
    run.epic_title = result.epic_title
    run.task_count = len(result.tasks)
    run.tasks = [
        {
            "title": t.title,
            "assignee": t.assignee,
            "hours": t.estimated_hours,
            "priority": t.priority,
            "dependencies": t.dependencies,
        }
        for t in result.tasks
    ]
    run.advance(Stage.REVIEW, f"拆解完成: {run.task_count}个任务")

    # ── Stage 2: REVIEW (auto-confirm) ──
    if auto_confirm:
        run.advance(Stage.DISPATCH, "自动确认，跳过人工审核")
    else:
        # 等待人工确认
        return run  # 挂起，等外部调用 confirm()

    # ── Stage 3: DISPATCH ──
    if task_manager is None:
        try:
            from agentark.orchestration.task_manager import get_task_manager
            task_manager = get_task_manager()
        except Exception:
            pass
    
    dispatch_result = dispatch_tasks(result, task_manager)
    run.epic_id = dispatch_result.get("epic_id", "")
    run.task_ids = dispatch_result.get("task_ids", [])
    run.advance(
        Stage.EXECUTE,
        f"已分派 {dispatch_result['dispatched']}/{run.task_count} 个任务"
    )

    # ── Stage 4-5: EXECUTE → MONITOR (异步，由cron接管) ──
    run.advance(Stage.MONITOR, "Agent执行中，完成监控已启动")

    return run


def confirm_pipeline(run: PipelineRun, task_manager=None) -> PipelineRun:
    """人工确认后继续管线"""
    if run.stage != Stage.REVIEW:
        return run
    
    run.advance(Stage.DISPATCH, "人工确认通过")
    
    if task_manager is None:
        try:
            from agentark.orchestration.task_manager import get_task_manager
            task_manager = get_task_manager()
        except Exception:
            pass
    
    # 重新拆解（因为可能已经过了一段时间）
    from agentark.orchestration.task_decomposer import (
        decompose_requirement, dispatch_tasks,
    )
    result = decompose_requirement(run.requirement, run.project)
    dispatch_result = dispatch_tasks(result, task_manager)
    
    run.epic_id = dispatch_result.get("epic_id", "")
    run.task_ids = dispatch_result.get("task_ids", [])
    run.task_count = len(result.tasks)
    run.advance(Stage.EXECUTE, f"已分派 {dispatch_result['dispatched']} 个任务")
    run.advance(Stage.MONITOR, "Agent执行中")
    
    return run


# ════════════════════════════════════════════════════════════
# 专项流程执行器
# ════════════════════════════════════════════════════════════

def run_direct_pipeline(
    task: str,
    project: str,
    agent: str,
    priority: int = 1,
    task_manager=None,
) -> PipelineRun:
    """
    执行专项流程管线 — 指令直达Agent。
    
    Args:
        task: 任务描述
        project: 项目key
        agent: 目标Agent profile名称
        priority: 优先级 0-3
        task_manager: 可注入的TaskManager实例
    """
    run = PipelineRun(
        mode=PipelineMode.DIRECT,
        project=project,
        requirement=task,
        target_agent=agent,
        created_at=datetime.now().isoformat(),
    )

    # ── Stage 1: ROUTE ──
    run.advance(Stage.ROUTE, f"路由到 {agent}")

    # ── Stage 2: CREATE ──
    if task_manager is None:
        try:
            from agentark.orchestration.task_manager import get_task_manager
            task_manager = get_task_manager()
        except Exception:
            pass

    if task_manager:
        try:
            t = task_manager.create_task(
                title=task[:80],
                task_type="task",
                project=project,
                assignee=agent,
                description=task,
                priority=priority,
                estimated_hours=_estimate_hours(task),
            )
            if t:
                run.task_ids = [t.id]
                run.task_count = 1
                run.advance(Stage.CREATE, f"已创建任务: {t.id}")
                run.advance(Stage.EXECUTE, f"等待 {agent} 执行")
        except Exception as e:
            run.advance(Stage.FAILED, f"创建失败: {e}")
            return run
    else:
        run.advance(Stage.FAILED, "TaskManager不可用")
        return run

    # ── Stage 3: EXECUTE (cron接管) ──
    run.advance(Stage.DONE, f"已分派给 {agent}，等待执行")

    return run


def _estimate_hours(task: str) -> float:
    """根据任务描述估算工时"""
    task_lower = task.lower()
    if any(w in task_lower for w in ["修复", "fix", "bug", "调整", "改", "换"]):
        return 1.0
    elif any(w in task_lower for w in ["实现", "开发", "添加", "新增"]):
        return 3.0
    elif any(w in task_lower for w in ["设计", "架构", "重构", "优化"]):
        return 4.0
    return 2.0


# ════════════════════════════════════════════════════════════
# 智能路由 — 一键选择流程
# ════════════════════════════════════════════════════════════

def smart_route(
    message: str,
    project: str = "finopsai",
    auto_confirm: bool = True,
    task_manager=None,
) -> dict:
    """
    智能路由入口 — 自动识别意图 → 选择流程 → 执行 → 返回结果。
    
    这是消息路由器调用的统一入口。
    
    Returns:
        {mode, pipeline_id, stage, tasks_count, summary, ...}
    """
    intent = identify_intent(message, project)

    if intent.mode == PipelineMode.DIRECT:
        run = run_direct_pipeline(
            task=intent.requirement,
            project=intent.project or project,
            agent=intent.target_agent,
            task_manager=task_manager,
        )
    else:
        run = run_normal_pipeline(
            requirement=intent.requirement,
            project=intent.project or project,
            auto_confirm=auto_confirm,
            task_manager=task_manager,
        )

    return {
        "mode": run.mode.value,
        "pipeline_id": run.id,
        "project": run.project,
        "stage": run.stage.value,
        "target_agent": run.target_agent,
        "task_count": run.task_count,
        "task_ids": run.task_ids,
        "summary": _build_summary(run),
        "intent": {
            "confidence": intent.confidence,
            "reason": intent.reason,
        },
    }


def _build_summary(run: PipelineRun) -> str:
    """生成可读摘要"""
    if run.mode == PipelineMode.DIRECT:
        return (
            f"⚡ 专项直达 → {run.target_agent}\n"
            f"   任务: {run.requirement[:60]}\n"
            f"   状态: {run.stage.value}\n"
            + (f"   Task: {run.task_ids[0]}" if run.task_ids else "")
        )
    else:
        return (
            f"📋 正常流程 → {run.project}\n"
            f"   Epic: {run.epic_title}\n"
            f"   拆解: {run.task_count}个任务\n"
            f"   阶段: {run.stage.value}"
        )


# ════════════════════════════════════════════════════════════
# Agent 快捷指令解析（供 message_router 使用）
# ════════════════════════════════════════════════════════════

def resolve_agent(agent_hint: str, project: str) -> str:
    """
    解析Agent名称。支持:
      - 完整名: finops-backend
      - 简短名: backend → finops-backend (需要project上下文)
      - 角色名: 后端 → finops-backend
    """
    agent_map = PROJECT_AGENT_MAP.get(project, {})
    
    # 完整名直接返回
    if agent_hint in agent_map.values():
        return agent_hint
    
    # 简短名/角色名查找
    agent_lower = agent_hint.lower()
    for keyword, agent in agent_map.items():
        if keyword.lower() in agent_lower or agent_lower in keyword.lower():
            return agent
    
    # 模糊匹配 agent profile 名称
    candidates = set(agent_map.values())
    for c in candidates:
        if agent_lower in c.lower():
            return c
    
    return agent_hint  # 原样返回，后续校验
