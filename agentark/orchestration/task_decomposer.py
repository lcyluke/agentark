"""智能任务拆解与分派引擎

从自然语言需求 → 结构化Task列表 → 自动分派到Agent → 执行追踪

流程:
  用户消息 → message_router(项目识别) → decomposer(拆解) → task_manager(创建+分派)
                                                                  ↓
                                         completion_monitor(监听) → WeChat通知

集成点:
  - message_router: 识别到task_create意图时调用
  - web.py: POST /api/dispatch/smart
  - CLI: apex dispatch smart "requirement" --project <name>
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ═══════════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════════

@dataclass
class DecomposedTask:
    """拆解后的单个任务"""
    title: str
    description: str = ""
    assignee: str = ""               # profile name
    estimated_hours: float = 2.0
    priority: int = 1                # 0=阻塞 1=高 2=中 3=低
    skill_tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # 依赖其他task的title


@dataclass
class DecompositionResult:
    """拆解结果"""
    requirement: str
    project: str
    epic_title: str = ""
    tasks: list[DecomposedTask] = field(default_factory=list)
    analysis: str = ""               # AI分析总结
    created_at: str = ""


# ═══════════════════════════════════════════════════════════════
# Agent技能画像（用于智能匹配）
# ═══════════════════════════════════════════════════════════════

AGENT_SKILL_PROFILES: dict[str, dict] = {
    "finops-pm": {
        "skills": ["项目管理", "需求分析", "路线图", "UAT"],
        "keywords": ["产品", "规划", "路线图", "PRD", "需求文档", "里程碑", "发布"],
        "max_concurrent": 5,
    },
    "finops-architect": {
        "skills": ["系统架构", "多租户设计", "DB Schema", "API设计", "技术选型"],
        "keywords": ["架构", "数据库", "API设计", "扩展性", "技术选型", "schema", "ER图"],
        "max_concurrent": 3,
    },
    "finops-backend": {
        "skills": ["Python", "FastAPI", "PostgreSQL", "SQLAlchemy", "云API"],
        "keywords": ["后端", "API", "接口", "数据库", "CRUD", "billing", "计费", "数据模型"],
        "max_concurrent": 3,
    },
    "finops-frontend": {
        "skills": ["React", "TypeScript", "Tailwind", "Recharts", "Dashboard"],
        "keywords": ["前端", "页面", "UI", "组件", "dashboard", "图表", "可视化", "租户门户"],
        "max_concurrent": 3,
    },
    "finops-devops": {
        "skills": ["Docker", "K8s", "Terraform", "CI/CD", "监控"],
        "keywords": ["部署", "Docker", "K8s", "CI", "CD", "监控", "环境", "域名", "HTTPS"],
        "max_concurrent": 2,
    },
    "finops-security": {
        "skills": ["安全审计", "数据加密", "合规", "RBAC", "租户隔离"],
        "keywords": ["安全", "加密", "权限", "RBAC", "审计", "合规", "GDPR", "认证"],
        "max_concurrent": 2,
    },
    "finops-ai": {
        "skills": ["成本预测", "异常检测", "ML", "时序分析", "优化推荐"],
        "keywords": ["AI", "预测", "模型", "算法", "异常", "优化", "推荐", "ML", "训练"],
        "max_concurrent": 2,
    },
    # 通用Agent（跨项目复用）
    "architect": {
        "skills": ["系统架构", "技术选型", "API设计"],
        "keywords": ["架构", "设计", "技术选型"],
        "max_concurrent": 3,
    },
    "frontend-dev": {
        "skills": ["微信小程序", "React", "Vue", "UI"],
        "keywords": ["小程序", "页面", "前端", "UI", "H5"],
        "max_concurrent": 3,
    },
}


PROJECT_AGENTS: dict[str, list[str]] = {
    "finopsai": ["finops-pm", "finops-architect", "finops-backend",
                  "finops-frontend", "finops-devops", "finops-security", "finops-ai"],
    "badminton-coach-ai": ["badminton-pm", "architect", "frontend-dev",
                            "ai-vision", "ai-algorithm", "content-marketing"],
    "apex": ["apex-pm", "ops-engineer", "security-compliance"],
    "shenzhen-badminton": ["content-marketing"],
}


# ═══════════════════════════════════════════════════════════════
# 拆解逻辑
# ═══════════════════════════════════════════════════════════════

def decompose_requirement(
    requirement: str,
    project: str,
    context: Optional[dict] = None,
) -> DecompositionResult:
    """
    将需求拆解为结构化Task列表。

    Args:
        requirement: 用户需求原文
        project: 项目key (finopsai / badminton-coach-ai / apex / shenzhen-badminton)
        context: 额外上下文 {existing_modules, constraints, ...}

    Returns:
        DecompositionResult with tasks + analysis + epic_title
    """
    agents = PROJECT_AGENTS.get(project, [])
    skills_map = {a: AGENT_SKILL_PROFILES.get(a, {}) for a in agents}

    # 生成拆解prompt（供LLM使用）
    prompt = _build_decomposition_prompt(requirement, project, skills_map, context)

    # 基于关键词的快速预拆解（fallback）
    tasks = _keyword_decompose(requirement, agents)

    result = DecompositionResult(
        requirement=requirement,
        project=project,
        epic_title=_extract_epic_title(requirement),
        tasks=tasks,
        analysis=f"已拆解为 {len(tasks)} 个子任务，分配到 {len(set(t.assignee for t in tasks if t.assignee))} 个Agent",
        created_at=datetime.now().isoformat(),
    )
    return result


def _build_decomposition_prompt(
    requirement: str,
    project: str,
    skills_map: dict,
    context: Optional[dict] = None,
) -> str:
    """构建LLM拆解prompt"""
    agent_list = "\n".join(
        f"  - {name}: {info.get('skills', [])}"
        for name, info in skills_map.items()
    )

    ctx_str = ""
    if context:
        ctx_str = f"\n项目上下文: {json.dumps(context, ensure_ascii=False)}"

    return f"""你是 {project} 项目的PM。请将以下需求拆解为可执行的任务列表。

需求: {requirement}
{ctx_str}

可用Agent:
{agent_list}

拆解规则:
1. 每个任务是独立的、可在一个Agent内完成的
2. 优先使用与任务关键词最匹配的Agent
3. 估计合理工时 (0.5-8小时/任务)
4. 标注任务间依赖关系
5. 优先级: 0=阻塞交付, 1=本周必须, 2=本迭代, 3=Icebox

输出格式 (JSON):
{{
  "epic_title": "Epic名称",
  "analysis": "分析总结",
  "tasks": [
    {{
      "title": "任务标题",
      "description": "详细描述",
      "assignee": "agent-name",
      "estimated_hours": 2.0,
      "priority": 1,
      "dependencies": []
    }}
  ]
}}"""


def _keyword_decompose(requirement: str, agents: list[str]) -> list[DecomposedTask]:
    """基于关键词的快速拆解（LLM不可用时的fallback）"""
    tasks = []

    # 按领域识别关键词
    patterns = {
        "architect": ["架构", "设计", "数据库", "schema", "选型", "ER图"],
        "backend": ["后端", "API", "接口", "CRUD", "数据", "billing", "计费", "支付"],
        "frontend": ["前端", "页面", "UI", "组件", "dashboard", "可视化", "图表"],
        "devops": ["部署", "Docker", "K8s", "CI", "CD", "环境", "域名"],
        "security": ["安全", "加密", "权限", "RBAC", "认证", "审计"],
        "ai": ["AI", "预测", "模型", "算法", "ML", "训练", "异常"],
    }

    req_lower = requirement.lower()
    matched_domains = set()

    for domain, keywords in patterns.items():
        if any(kw.lower() in req_lower for kw in keywords):
            matched_domains.add(domain)

    # 查找匹配的agent
    for agent in agents:
        agent_lower = agent.lower()
        if "architect" in agent_lower and "architect" in matched_domains:
            tasks.append(DecomposedTask(
                title=f"设计{_short_title(requirement)}架构",
                description=requirement,
                assignee=agent,
                estimated_hours=2.0,
                priority=1,
            ))
        elif "backend" in agent_lower and "backend" in matched_domains:
            tasks.append(DecomposedTask(
                title=f"实现{_short_title(requirement)}后端",
                description=requirement,
                assignee=agent,
                estimated_hours=4.0,
                priority=1,
            ))
        elif "frontend" in agent_lower and "frontend" in matched_domains:
            tasks.append(DecomposedTask(
                title=f"实现{_short_title(requirement)}前端",
                description=requirement,
                assignee=agent,
                estimated_hours=3.0,
                priority=1,
            ))
        elif "devops" in agent_lower and "devops" in matched_domains:
            tasks.append(DecomposedTask(
                title=f"{_short_title(requirement)}部署配置",
                description=requirement,
                assignee=agent,
                estimated_hours=1.5,
                priority=2,
            ))

    # 如果没匹配到，创建通用task给PM
    if not tasks:
        pm_agent = next((a for a in agents if "pm" in a.lower()), agents[0] if agents else "finops-pm")
        tasks.append(DecomposedTask(
            title=f"分析需求: {_short_title(requirement)}",
            description=requirement,
            assignee=pm_agent,
            estimated_hours=1.0,
            priority=1,
        ))

    return tasks


def _extract_epic_title(requirement: str) -> str:
    """从需求提取Epic标题"""
    # 截取前30字作为标题
    cleaned = requirement.strip().replace("\n", " ")
    return cleaned[:30] + ("..." if len(cleaned) > 30 else "")


def _short_title(text: str) -> str:
    """截取简短标题"""
    return text.strip()[:20]


# ═══════════════════════════════════════════════════════════════
# 拆解结果解析（LLM返回的JSON → DecompositionResult）
# ═══════════════════════════════════════════════════════════════

def parse_llm_decomposition(llm_response: str, requirement: str, project: str) -> DecompositionResult:
    """解析LLM返回的JSON为结构化的DecompositionResult"""
    try:
        # 尝试提取JSON块
        json_match = re.search(r'\{[\s\S]*\}', llm_response)
        if json_match:
            data = json.loads(json_match.group(0))
        else:
            data = json.loads(llm_response)

        tasks = []
        for t in data.get("tasks", []):
            tasks.append(DecomposedTask(
                title=t.get("title", ""),
                description=t.get("description", ""),
                assignee=t.get("assignee", ""),
                estimated_hours=float(t.get("estimated_hours", 2.0)),
                priority=int(t.get("priority", 1)),
                skill_tags=t.get("skill_tags", []),
                dependencies=t.get("dependencies", []),
            ))

        return DecompositionResult(
            requirement=requirement,
            project=project,
            epic_title=data.get("epic_title", _extract_epic_title(requirement)),
            tasks=tasks,
            analysis=data.get("analysis", ""),
            created_at=datetime.now().isoformat(),
        )
    except (json.JSONDecodeError, KeyError, ValueError):
        # Fallback to keyword-based
        return decompose_requirement(requirement, project)


# ═══════════════════════════════════════════════════════════════
# 任务创建 + 分派（对接task_manager）
# ═══════════════════════════════════════════════════════════════

def dispatch_tasks(
    result: DecompositionResult,
    task_manager=None,
) -> dict:
    """
    将DecompositionResult中的tasks创建到Kanban并分派。

    Returns:
        {epic_id, task_ids: [...], dispatched: int, failed: int}
    """
    dispatched = 0
    failed = 0
    task_ids = []
    epic_id = None

    if task_manager is None:
        try:
            from agentark.orchestration.task_manager import TaskManager
            task_manager = TaskManager()
        except Exception:
            pass

    if task_manager:
        try:
            # 创建Epic
            epic = task_manager.create_task(
                title=result.epic_title,
                task_type="epic",
                project=result.project,
                description=result.requirement,
            )
            epic_id = epic.id if epic else None
        except Exception:
            epic_id = None

        # 创建子Task
        for task in result.tasks:
            try:
                t = task_manager.create_task(
                    title=task.title,
                    task_type="task",
                    project=result.project,
                    assignee=task.assignee,
                    description=task.description,
                    estimated_hours=task.estimated_hours,
                    priority=task.priority,
                    parent_id=epic_id,
                )
                if t:
                    task_ids.append(t.id)
                    dispatched += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

    return {
        "epic_id": epic_id,
        "task_ids": task_ids,
        "dispatched": dispatched,
        "failed": failed,
    }


# ═══════════════════════════════════════════════════════════════
# 完成监控（供cron job调用）
# ═══════════════════════════════════════════════════════════════

def check_completion(
    project: str,
    since_hours: int = 24,
    task_manager=None,
) -> dict:
    """
    检查项目任务完成情况。

    Returns:
        {completed: [...], in_progress: [...], blocked: [...], summary: str}
    """
    if task_manager is None:
        try:
            from agentark.orchestration.task_manager import TaskManager
            task_manager = TaskManager()
        except Exception:
            return {"error": "task_manager unavailable", "summary": "无法连接任务管理器"}

    try:
        all_tasks = task_manager.list_tasks(project=project)
    except Exception:
        all_tasks = []

    completed = []
    in_progress = []
    blocked = []

    cutoff = time.time() - (since_hours * 3600)

    for t in all_tasks:
        # 检查是否在时间窗口内
        updated = getattr(t, 'updated_at', 0) or getattr(t, 'created_at', 0)
        if isinstance(updated, str):
            try:
                updated = datetime.fromisoformat(updated).timestamp()
            except Exception:
                updated = 0

        if updated < cutoff:
            continue

        status = getattr(t, 'status', 'unknown')
        info = {
            "id": getattr(t, 'id', '?'),
            "title": getattr(t, 'title', ''),
            "assignee": getattr(t, 'assignee', ''),
            "status": status,
        }

        if status in ("completed", "verified", "done"):
            completed.append(info)
        elif status in ("in_progress", "assigned", "approved"):
            in_progress.append(info)
        elif status in ("blocked",):
            blocked.append(info)

    total = len(completed) + len(in_progress) + len(blocked)
    summary = (
        f"📊 {project} 近{since_hours}h: "
        f"完成 {len(completed)} · "
        f"进行中 {len(in_progress)}"
        + (f" · 阻塞 {len(blocked)} ⚠️" if blocked else "")
        + (f" · 共 {total} 任务" if total else " · 无活动任务")
    )

    return {
        "completed": completed,
        "in_progress": in_progress,
        "blocked": blocked,
        "summary": summary,
        "total": total,
    }
