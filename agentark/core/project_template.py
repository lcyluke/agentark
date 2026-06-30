"""智能项目模板引擎 — 按项目类型和规模智能分配Agent

分层逻辑:
  🟢 小型 (萌芽期) — PM兼任巡检, 只配1-2核心Agent + Git脉搏
  🟡 中型 (成长期) — PM + 智能项目助手(独立) + 3-4核心Agent + 全套巡检
  🔴 大型 (成熟期) — PM + 智能项目助手 + 专项监控 + 5+核心Agent + 全巡检+风险预警+周报

使用:
  apex project create <project-key> --name "项目名" --type auto
  apex project create <project-key> --name "项目名" --type webapp --size medium

自动创建:
  1. PM Profile + SOUL (及智能助手 Profile，中大型)
  2. 核心Agent Profiles (按类型+规模智能匹配)
  3. 分级监控Cron (按规模: 1-6个)
  4. message_router 注册
  5. fleet_inspector 注册
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import os


# ═══════════════════════════════════════════════════════════
# 项目规模枚举
# ═══════════════════════════════════════════════════════════

class ProjectSize(Enum):
    SMALL = "small"     # 🟢 萌芽期: <20文件, 1人, <3周
    MEDIUM = "medium"   # 🟡 成长期: 20-100文件, 2-3人, 1-3月
    LARGE = "large"     # 🔴 成熟期: 100+文件, 3+人, 3+月


class ProjectType(Enum):
    WEBAPP = "webapp"       # Web全栈应用
    AI_ML = "ai-ml"         # AI/ML项目
    MOBILE = "mobile"       # 移动端(小程序/App)
    DATA = "data"           # 数据处理/分析
    CONTENT = "content"     # 内容创作/自媒体
    INFRA = "infra"         # 基础设施/DevOps


# ═══════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════

@dataclass
class MonitorAgent:
    """监控巡检Agent定义"""
    role: str
    emoji: str
    description: str
    cron_name: str
    cron_schedule: str
    prompt: str = ""
    script: str = ""
    profile: str = ""  # 运行此监控的Hermes Profile


@dataclass
class CoreAgent:
    """核心团队成员定义"""
    profile_name: str   # Hermes Profile名
    role: str           # 角色
    emoji: str          # 图标
    required: bool = True  # 是否必需


@dataclass
class SmartProjectTemplate:
    """智能项目模板"""
    key: str
    name: str
    emoji: str
    project_type: ProjectType
    size: ProjectSize

    # PM配置
    pm_agent: str = ""
    pm_role: str = "项目经理"

    # 智能助手 (中大型项目)
    has_assistant: bool = False

    # 核心团队
    core_agents: list[CoreAgent] = field(default_factory=list)

    # 巡检Agent (按规模分级)
    monitors: list[MonitorAgent] = field(default_factory=list)

    # 元数据
    path: str = ""
    keywords: list[str] = field(default_factory=list)
    description: str = ""


# ═══════════════════════════════════════════════════════════
# 类型检测 — 根据项目名/描述/目录推断
# ═══════════════════════════════════════════════════════════

TYPE_KEYWORDS: dict[ProjectType, list[str]] = {
    ProjectType.WEBAPP: [
        "web", "网站", "dashboard", "前端", "后端", "fullstack", "全栈",
        "react", "vue", "next", "fastapi", "flask", "django", "api",
        "saas", "平台", "后台", "管理",
    ],
    ProjectType.AI_ML: [
        "ai", "ml", "模型", "训练", "推理", "深度学习", "机器学习",
        "神经网络", "gpt", "llm", "transformer", "cv", "nlp", "识别",
        "检测", "分类", "预测", "标注", "algorithm", "算法",
    ],
    ProjectType.MOBILE: [
        "小程序", "miniapp", "app", "mobile", "移动端", "ios", "android",
        "flutter", "react native", "wechat", "微信",
    ],
    ProjectType.DATA: [
        "data", "数据", "etl", "分析", "可视化", "报表", "dashboard",
        "pipeline", "warehouse", "spark", "hadoop", "bi",
    ],
    ProjectType.CONTENT: [
        "content", "内容", "文章", "博客", "blog", "自媒体", "文案",
        "营销", "marketing", "推广", "seo", "写作", "出版",
    ],
    ProjectType.INFRA: [
        "infra", "基础设施", "devops", "部署", "监控", "运维",
        "ci/cd", "docker", "k8s", "kubernetes", "terraform", "cloud",
    ],
}


def detect_project_type(name: str, description: str = "", path: str = "") -> ProjectType:
    """智能检测项目类型"""
    text = f"{name} {description}".lower()
    scores: dict[ProjectType, int] = {}

    for ptype, keywords in TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[ptype] = score

    # 路径分析: 检查目录内容
    if path and os.path.isdir(os.path.expanduser(path)):
        import glob
        p = os.path.expanduser(path)
        files = glob.glob(f"{p}/**/*", recursive=True)[:200]
        extensions = set(os.path.splitext(f)[1] for f in files if os.path.isfile(f))

        # Python + model files → AI_ML
        if {".pth", ".pt", ".onnx", ".h5"} & extensions:
            scores[ProjectType.AI_ML] = scores.get(ProjectType.AI_ML, 0) + 5
        # .wxml/.wxss → Mobile (WeChat)
        if {".wxml", ".wxss"} & extensions:
            scores[ProjectType.MOBILE] = scores.get(ProjectType.MOBILE, 0) + 5
        # React/Vue files → Webapp
        if {".jsx", ".tsx", ".vue"} & extensions:
            scores[ProjectType.WEBAPP] = scores.get(ProjectType.WEBAPP, 0) + 3
        # Docker/k8s → Infra
        if any("Dockerfile" in f or "docker-compose" in f for f in files):
            scores[ProjectType.INFRA] = scores.get(ProjectType.INFRA, 0) + 5

    if scores:
        return max(scores, key=lambda k: scores[k])
    return ProjectType.WEBAPP  # 默认


def detect_project_size(path: str = "", description: str = "") -> ProjectSize:
    """智能检测项目规模"""
    if path and os.path.isdir(os.path.expanduser(path)):
        p = os.path.expanduser(path)
        try:
            # 统计文件数
            import glob
            files = [f for f in glob.glob(f"{p}/**/*", recursive=True) if os.path.isfile(f)]
            file_count = len(files)

            # Git提交数
            import subprocess
            result = subprocess.run(
                ["git", "log", "--oneline", "--all"],
                cwd=p, capture_output=True, text=True, timeout=10
            )
            commit_count = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

            # Git年龄
            result2 = subprocess.run(
                ["git", "log", "--reverse", "--format=%ct", "--all"],
                cwd=p, capture_output=True, text=True, timeout=10
            )
            ages = result2.stdout.strip().split("\n")
            age_weeks = 0
            if ages and ages[0]:
                import time
                first_commit = int(ages[0])
                age_weeks = (time.time() - first_commit) / (7 * 86400)

            # 判断
            if file_count >= 100 or commit_count >= 500 or age_weeks >= 12:
                return ProjectSize.LARGE
            elif file_count >= 20 or commit_count >= 50 or age_weeks >= 4:
                return ProjectSize.MEDIUM
            else:
                return ProjectSize.SMALL
        except Exception:
            pass
    return ProjectSize.SMALL  # 默认小型


# ═══════════════════════════════════════════════════════════
# 核心Agent分配矩阵 — 按项目类型
# ═══════════════════════════════════════════════════════════

TYPE_CORE_AGENTS: dict[ProjectType, dict[ProjectSize, list[CoreAgent]]] = {
    ProjectType.WEBAPP: {
        ProjectSize.SMALL: [
            CoreAgent("fullstack-dev", "全栈开发者", "👨‍💻"),
        ],
        ProjectSize.MEDIUM: [
            CoreAgent("frontend-dev", "前端开发", "💻"),
            CoreAgent("backend-dev", "后端开发", "⚙️"),
            CoreAgent("devops", "DevOps", "🔧"),
        ],
        ProjectSize.LARGE: [
            CoreAgent("frontend-dev", "前端开发", "💻"),
            CoreAgent("backend-dev", "后端开发", "⚙️"),
            CoreAgent("fullstack-dev", "全栈开发", "👨‍💻"),
            CoreAgent("devops", "DevOps工程师", "🔧"),
            CoreAgent("qa-engineer", "测试工程师", "🧪"),
            CoreAgent("security-compliance", "安全合规", "🔒"),
        ],
    },
    ProjectType.AI_ML: {
        ProjectSize.SMALL: [
            CoreAgent("data-scientist", "数据科学家", "🧪"),
        ],
        ProjectSize.MEDIUM: [
            CoreAgent("ai-algorithm", "AI算法", "🧠"),
            CoreAgent("ai-vision", "视觉识别", "👁️"),
            CoreAgent("ml-engineer", "ML工程师", "🤖"),
        ],
        ProjectSize.LARGE: [
            CoreAgent("ai-algorithm", "AI算法", "🧠"),
            CoreAgent("ai-vision", "视觉识别", "👁️"),
            CoreAgent("ml-engineer", "ML工程师", "🤖"),
            CoreAgent("data-scientist", "数据科学家", "🧪"),
            CoreAgent("devops", "DevOps", "🔧"),
            CoreAgent("qa-engineer", "测试工程师", "🧪"),
        ],
    },
    ProjectType.MOBILE: {
        ProjectSize.SMALL: [
            CoreAgent("frontend-dev", "前端开发", "💻"),
        ],
        ProjectSize.MEDIUM: [
            CoreAgent("frontend-dev", "小程序前端", "🎨"),
            CoreAgent("backend-dev", "后端开发", "⚙️"),
            CoreAgent("devops", "DevOps", "🔧"),
        ],
        ProjectSize.LARGE: [
            CoreAgent("frontend-dev", "小程序前端", "🎨"),
            CoreAgent("backend-dev", "后端开发", "⚙️"),
            CoreAgent("fullstack-dev", "全栈开发", "👨‍💻"),
            CoreAgent("devops", "DevOps", "🔧"),
            CoreAgent("qa-engineer", "测试", "🧪"),
            CoreAgent("content-marketing", "内容推广", "✍️"),
        ],
    },
    ProjectType.DATA: {
        ProjectSize.SMALL: [
            CoreAgent("data-analyst", "数据分析师", "📊"),
        ],
        ProjectSize.MEDIUM: [
            CoreAgent("data-engineer", "数据工程师", "🗄️"),
            CoreAgent("data-analyst", "数据分析师", "📊"),
            CoreAgent("data-scientist", "数据科学家", "🧪"),
        ],
        ProjectSize.LARGE: [
            CoreAgent("data-engineer", "数据工程师", "🗄️"),
            CoreAgent("data-analyst", "数据分析师", "📊"),
            CoreAgent("data-scientist", "数据科学家", "🧪"),
            CoreAgent("ml-engineer", "ML工程师", "🤖"),
            CoreAgent("devops", "DevOps", "🔧"),
        ],
    },
    ProjectType.CONTENT: {
        ProjectSize.SMALL: [
            CoreAgent("writer", "写手", "🖊️"),
        ],
        ProjectSize.MEDIUM: [
            CoreAgent("content-strategist", "内容策略", "✍️"),
            CoreAgent("writer", "写手", "🖊️"),
            CoreAgent("editor", "编辑", "📝"),
        ],
        ProjectSize.LARGE: [
            CoreAgent("content-strategist", "内容策略", "✍️"),
            CoreAgent("writer", "写手", "🖊️"),
            CoreAgent("editor", "编辑", "📝"),
            CoreAgent("publisher", "发布", "📤"),
            CoreAgent("designer", "设计", "🎨"),
        ],
    },
    ProjectType.INFRA: {
        ProjectSize.SMALL: [
            CoreAgent("devops", "DevOps", "🔧"),
        ],
        ProjectSize.MEDIUM: [
            CoreAgent("devops", "DevOps", "🔧"),
            CoreAgent("ops-engineer", "运维工程师", "🛠️"),
            CoreAgent("security-compliance", "安全合规", "🔒"),
        ],
        ProjectSize.LARGE: [
            CoreAgent("devops", "DevOps", "🔧"),
            CoreAgent("ops-engineer", "运维工程师", "🛠️"),
            CoreAgent("security-compliance", "安全合规", "🔒"),
            CoreAgent("backend-dev", "后端开发", "⚙️"),
            CoreAgent("qa-engineer", "测试", "🧪"),
        ],
    },
}


# ═══════════════════════════════════════════════════════════
# PM命名规则
# ═══════════════════════════════════════════════════════════

def generate_pm_name(project_key: str) -> str:
    """根据项目key生成PM Agent名"""
    # 简化key: 取第一个单词或全小写
    short = project_key.lower().replace(" ", "-").replace("_", "-").split("-")[0]
    return f"{short}-pm"


# ═══════════════════════════════════════════════════════════
# 智能项目助手定义 — 中大型项目独立追踪Agent
# ═══════════════════════════════════════════════════════════

PROJECT_ASSISTANT_SOUL = {
    "role": "智能项目助手",
    "expertise": [
        "项目看板管理", "里程碑追踪", "风险预警", "资源投入分析",
        "进度报告", "周报生成", "任务分配协调", "跨团队沟通"
    ],
    "personality": (
        "你是项目的'第二大脑'——不替代PM做战略决策，但确保PM不会遗漏任何细节。\n"
        "主动发现：不等PM问，主动扫描任务状态、代码提交、风险信号。\n"
        "数据驱动：所有判断基于实际数据（Git提交、任务状态、时间消耗），不凭感觉。\n"
        "预警优先：宁可多报一次风险，不可漏报一次阻塞。\n"
        "简洁有力：每条通知3行以内，关键信息加粗，附带行动建议。"
    ),
    "communication": (
        "结构化输出：任务看板→表格，风险→🔴🟡🟢分级，周报→固定模板。\n"
        "微信通知风格：短句+emoji+行动建议，不刷屏。\n"
        "主动推送：关键事件（里程碑达成/任务阻塞超24h/代码3天无提交）主动通知。"
    ),
    "emoji": "🧠",
    "skills": [
        "project-tracking", "milestone-monitoring", "risk-assessment",
        "resource-analysis", "weekly-reporting", "kanban-scanning"
    ],
}


def build_assistant_monitors(project_key: str, project_name: str, pm_agent: str, git_path: str = "") -> list[MonitorAgent]:
    """生成智能项目助手的监控任务列表 (中型及以上项目)"""
    assistant_profile = f"{project_key}-assistant"

    monitors = [
        # 1. 任务看板扫描 — 30min
        MonitorAgent(
            role="任务看板扫描",
            emoji="📋",
            description=f"每30分钟扫描{project_name}看板，任务完成/阻塞即时通知",
            cron_name=f"{project_name} 看板扫描",
            cron_schedule="every 30m",
            profile=assistant_profile,
            prompt=f"""你是 {project_name} 的智能项目助手。现在扫描项目看板状态。

用 hermes kanban list 检查所有任务卡:
- 列出最近完成的任务 (3个)
- 列出正在执行的任务 (3个)
- 检查是否有阻塞超过24h的任务
- 检查是否有卡在ready超过1h的任务

格式:
🧠 [{project_name}] 看板扫描
✅ 完成: task_names
⏳ 进行中: task_names + 耗时
🔴 阻塞>24h: task_names (如有)
🟡 待领取超1h: task_names (如有)

无活动时回复 [SILENT]。
无异常时仅输出最近完成+进行中，3行内。""",
        ),

        # 2. 里程碑追踪 — 每日09:00
        MonitorAgent(
            role="里程碑追踪",
            emoji="🎯",
            description=f"每日检查{project_name}里程碑进度，偏差预警",
            cron_name=f"{project_name} 里程碑",
            cron_schedule="0 9 * * *",
            profile=assistant_profile,
            prompt=f"""你是 {project_name} 的智能项目助手。现在是早上，请追踪项目里程碑。

检查:
1. 当前Sprint/Phase进度 (用 apex sprint status)
2. 里程碑是否按时 (对比计划vs实际)
3. 任何偏差 >20% 需要预警

格式:
🎯 [{project_name}] 里程碑日报
📊 Sprint进度: X% (计划X%)
⏰ 预计完成: YYYY-MM-DD (偏差: ±N天)
⚠️ 风险: (如有)

简洁5行内。""",
        ),

        # 3. 风险预警 — 每日20:00
        MonitorAgent(
            role="风险预警",
            emoji="⚠️",
            description=f"每日晚扫描{project_name}风险信号",
            cron_name=f"{project_name} 风险预警",
            cron_schedule="0 20 * * *",
            profile=assistant_profile,
            prompt=f"""你是 {project_name} 的智能项目助手。现在是晚上，扫描项目风险。

检查:
1. Git提交频率 (最近3天0提交=🔴)
2. 阻塞任务数量 (>2个=🔴, 1个=🟡)
3. 连续失败的任务
4. 任何异常模式

分级:
🔴 严重: 需立即行动
🟡 警告: 需关注
🟢 正常: 一切顺利

格式:
⚠️ [{project_name}] 风险扫描
整体: 🟢/🟡/🔴
Git: X天无提交 (🟢/🟡/🔴)
阻塞: N个任务
建议: 一行行动建议

简洁4行内。如果整体🟢一切正常，仅输出一行。""",
        ),

        # 4. 项目周报 — 每周一09:00
        MonitorAgent(
            role="项目周报",
            emoji="📊",
            description=f"{project_name}每周综合报告",
            cron_name=f"{project_name} 周报",
            cron_schedule="0 9 * * 1",  # 每周一早9点
            profile=assistant_profile,
            prompt=f"""你是 {project_name} 的智能项目助手。今天是周一，生成项目周报。

收集:
1. 本周Git提交统计 (git log --since=1.week)
2. 本周完成任务数 (kanban list)
3. 新增任务数
4. 本周里程碑进度
5. 关键风险和阻塞项
6. 下周计划

格式:
📊 [{project_name}] 周报 (YYYY-MM-DD ~ YYYY-MM-DD)

🔥 **本周亮点**:
📝 **Git**: N次提交, M个文件变更
✅ **完成**: N个任务 (列表)
🆕 **新增**: M个任务
🎯 **里程碑**: 进度X%
⚠️ **风险**: (如有)
📅 **下周重点**: 1-3项

控制在15行内，清晰可读。""",
        ),
    ]

    # 如果有Git路径，加Git脉搏检查
    if git_path:
        monitors.append(
            MonitorAgent(
                role="Git脉搏",
                emoji="🐙",
                description=f"检测{project_name}代码提交活跃度",
                cron_name=f"{project_name} Git脉搏",
                cron_schedule="0 10 * * *",
                profile=assistant_profile,
                prompt=f"""检查 {project_name} 代码活跃度:
cd {git_path} && git log --oneline --since=3.days | wc -l

超过3天无提交 → 通过微信提醒老卢。
正常 → [SILENT]""",
            )
        )

    return monitors


# ═══════════════════════════════════════════════════════════
# 小型项目巡检 (PM兼任)
# ═══════════════════════════════════════════════════════════

def build_small_monitors(project_key: str, project_name: str, pm_agent: str, git_path: str = "") -> list[MonitorAgent]:
    """小型项目：PM兼任巡检，最少监控"""
    monitors = []

    if git_path:
        monitors.append(
            MonitorAgent(
                role="Git脉搏",
                emoji="🐙",
                description=f"检测{project_name}代码提交活跃度",
                cron_name=f"{project_name} Git脉搏",
                cron_schedule="0 10 * * *",
                profile=pm_agent,
                prompt=f"""检查 {project_name} 代码活跃度:
cd {git_path} && git log --oneline --since=3.days | wc -l

超过3天无提交 → 提醒老卢。
正常 → [SILENT]""",
            )
        )

    return monitors


# ═══════════════════════════════════════════════════════════
# 大型项目额外巡检
# ═══════════════════════════════════════════════════════════

def build_large_monitors(project_key: str, project_name: str, pm_agent: str, git_path: str = "") -> list[MonitorAgent]:
    """大型项目：专项监控Agent"""
    monitors = [
        MonitorAgent(
            role="资源投入分析",
            emoji="💰",
            description=f"{project_name}资源投入/成本追踪",
            cron_name=f"{project_name} 资源分析",
            cron_schedule="0 9 * * 1",  # 每周一早9点
            profile=pm_agent,
            prompt=f"""分析 {project_name} 项目资源投入:

1. 本周API token消耗 (检查hermes cron历史)
2. GPU/云资源使用时间
3. 人力投入: Git提交者数 + 活跃Agent数
4. 与上周对比趋势

格式:
💰 [{project_name}] 资源周报
API: ~Xtokens (↑/↓X%)
GPU: Xh (↑/↓X%)
人力: N人/N Agents
趋势: 🟢正常 / 🟡需关注 / 🔴超标""",
        ),
        MonitorAgent(
            role="跨项目协调",
            emoji="🔗",
            description=f"{project_name}依赖/跨项目协调检查",
            cron_name=f"{project_name} 跨项目协调",
            cron_schedule="0 14 * * *",  # 每天下午2点
            profile=pm_agent,
            prompt=f"""检查 {project_name} 与其他项目的依赖关系:

1. 是否有阻塞项来自其他项目
2. 是否有输出被其他项目等待
3. 共享资源(如GPU/AutoDL)是否有冲突

格式:
🔗 [{project_name}] 跨项目协调
阻塞: (来自其他项目)
等待: (其他项目等待本项目的)
资源冲突: (如有)
无异常 → [SILENT]""",
        ),
    ]
    return monitors


# ═══════════════════════════════════════════════════════════
# 智能项目模板生成器 — 主入口
# ═══════════════════════════════════════════════════════════

def build_smart_template(
    project_key: str,
    project_name: str,
    project_type: ProjectType | str = "auto",
    project_size: ProjectSize | str = "auto",
    project_path: str = "",
    description: str = "",
) -> SmartProjectTemplate:
    """智能构建项目模板 — 根据类型和规模自动分配Agent

    Args:
        project_key: 项目唯一标识 (如 'badminton-coach-ai')
        project_name: 项目显示名 (如 '羽球宝AI搭子')
        project_type: 项目类型，'auto' 自动检测
        project_size: 项目规模，'auto' 自动检测
        project_path: 项目目录路径 (用于自动检测)
        description: 项目描述 (用于类型推断)

    Returns:
        SmartProjectTemplate 完整模板
    """
    # 1. 类型检测
    if isinstance(project_type, str):
        if project_type == "auto":
            project_type = detect_project_type(project_name, description, project_path)
        else:
            project_type = ProjectType(project_type)

    # 2. 规模检测
    if isinstance(project_size, str):
        if project_size == "auto":
            project_size = detect_project_size(project_path, description)
        else:
            project_size = ProjectSize(project_size)

    # 3. PM命名
    pm_agent = generate_pm_name(project_key)

    # 4. 是否需要智能助手
    has_assistant = project_size in (ProjectSize.MEDIUM, ProjectSize.LARGE)

    # 5. 核心Agent分配
    agent_map = TYPE_CORE_AGENTS.get(project_type, {})
    core_agents = agent_map.get(project_size, agent_map.get(ProjectSize.SMALL, []))

    # 6. 监控巡检分配
    monitors: list[MonitorAgent] = []

    git_path = project_path if project_path else ""

    if project_size == ProjectSize.SMALL:
        # 小型: PM兼任，仅Git脉搏
        monitors = build_small_monitors(project_key, project_name, pm_agent, git_path)
    elif project_size == ProjectSize.MEDIUM:
        # 中型: PM日报 + 智能助手全套
        # PM日报
        monitors.append(MonitorAgent(
            role="PM日报",
            emoji="📊",
            description=f"{project_name}日报",
            cron_name=f"{project_name} PM日报",
            cron_schedule="0 9 * * *",
            profile=pm_agent,
            prompt=f"""你是 {project_name} 的PM。早上准备日报:
📊 [{project_name}] 进展: 近24h活动
⚠️ 风险: 阻塞项
🎯 今日重点: 1-3项
6行内。""",
        ))
        # 智能助手监控
        monitors.extend(build_assistant_monitors(project_key, project_name, pm_agent, git_path))
    else:
        # 大型: PM日报 + 智能助手全套 + 专项监控
        monitors.append(MonitorAgent(
            role="PM日报",
            emoji="📊",
            description=f"{project_name}日报",
            cron_name=f"{project_name} PM日报",
            cron_schedule="0 9 * * *",
            profile=pm_agent,
            prompt=f"""你是 {project_name} 的PM。早上日报:
📊 [{project_name}] 进展: 近24h关键活动
⚠️ 风险: 阻塞项+影响范围
🎯 今日重点: 优先级排序
📅 本周里程碑: 进度
8行内。""",
        ))
        monitors.extend(build_assistant_monitors(project_key, project_name, pm_agent, git_path))
        monitors.extend(build_large_monitors(project_key, project_name, pm_agent, git_path))

    # 7. Emoji选择
    type_emoji = {
        ProjectType.WEBAPP: "🌐",
        ProjectType.AI_ML: "🤖",
        ProjectType.MOBILE: "📱",
        ProjectType.DATA: "📊",
        ProjectType.CONTENT: "✍️",
        ProjectType.INFRA: "🔧",
    }
    emoji = type_emoji.get(project_type, "📦")

    return SmartProjectTemplate(
        key=project_key,
        name=project_name,
        emoji=emoji,
        project_type=project_type,
        size=project_size,
        pm_agent=pm_agent,
        has_assistant=has_assistant,
        core_agents=core_agents,
        monitors=monitors,
        path=project_path,
        description=description,
    )


# ═══════════════════════════════════════════════════════════
# 向后兼容: 保留旧模板系统
# ═══════════════════════════════════════════════════════════

# 已注册的旧项目模板 (兼容现有项目)
LEGACY_TEMPLATES: dict[str, SmartProjectTemplate] = {}


def register_legacy_template(tmpl: SmartProjectTemplate):
    LEGACY_TEMPLATES[tmpl.key] = tmpl


# 预注册现有项目
register_legacy_template(SmartProjectTemplate(
    key="badminton-coach-ai",
    name="羽球宝AI搭子",
    emoji="🏸",
    project_type=ProjectType.AI_ML,
    size=ProjectSize.LARGE,
    pm_agent="badminton-pm",
    has_assistant=False,  # 已有badminton-pm在手动管理
    core_agents=[],
    path="~/Desktop/2026AIAPP/workspace/badminton-coach-ai",
))

register_legacy_template(SmartProjectTemplate(
    key="apex",
    name="Apex Dashboard",
    emoji="🦅",
    project_type=ProjectType.WEBAPP,
    size=ProjectSize.LARGE,
    pm_agent="apex-pm",
    has_assistant=False,
    core_agents=[],
    path="~/Desktop/2026AIAPP/Apex",
))

register_legacy_template(SmartProjectTemplate(
    key="finopsai",
    name="FinOps AI",
    emoji="💰",
    project_type=ProjectType.WEBAPP,
    size=ProjectSize.MEDIUM,
    pm_agent="finops-pm",
    has_assistant=False,
    core_agents=[],
    path="~/Desktop/2026AIAPP/finopsai",
))

register_legacy_template(SmartProjectTemplate(
    key="shenzhen-badminton",
    name="深圳羽球地图",
    emoji="🗺️",
    project_type=ProjectType.DATA,
    size=ProjectSize.SMALL,
    pm_agent="",
    has_assistant=False,
    core_agents=[],
    path="~/Desktop/2026AIAPP/shenzhen-badminton",
))


# ═══════════════════════════════════════════════════════════
# 统计 & 查询
# ═══════════════════════════════════════════════════════════

def summarize_template(tmpl: SmartProjectTemplate) -> dict:
    """模板摘要 — 用于展示"""
    size_labels = {
        ProjectSize.SMALL: "🟢 小型(萌芽期)",
        ProjectSize.MEDIUM: "🟡 中型(成长期)",
        ProjectSize.LARGE: "🔴 大型(成熟期)",
    }
    return {
        "key": tmpl.key,
        "name": f"{tmpl.emoji} {tmpl.name}",
        "type": tmpl.project_type.value,
        "size": size_labels.get(tmpl.size, tmpl.size.value),
        "pm": tmpl.pm_agent,
        "assistant": "🧠 智能助手" if tmpl.has_assistant else "— (PM兼任巡检)",
        "core_agents": [f"{a.emoji} {a.role}" for a in tmpl.core_agents],
        "core_count": len(tmpl.core_agents),
        "monitors": [f"{m.emoji} {m.role}" for m in tmpl.monitors],
        "monitor_count": len(tmpl.monitors),
        "total_agents": 1 + len(tmpl.core_agents) + (1 if tmpl.has_assistant else 0),
    }
