"""Apex Project Factory — interactive project bootstrapper with intelligent agent matching.

Full 8-step interactive wizard:
  1. Identity     — name, tagline, description
  2. Type         — auto-detect from description or manual select
  3. Scale        — team size, timeline, complexity
  4. Tech Stack   — auto-recommend based on type + scale
  5. Agent Team   — intelligent assignment, add/remove/confirm
  6. Integrations — WeChat, DingTalk, Feishu quick config
  7. Roadmap      — MVP definition, 24h plan, sprint tasks
  8. Confirm      — summary → create everything

Usage:
  apex init my-project          Full interactive wizard
  apex init my-project --quick  Bypass wizard, use defaults
"""

from __future__ import annotations

import os
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from apex.core.profile import ProfileManager

# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATE LIBRARY — project types, tech stacks, agent recommendations
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_TIERS = {
    "mvp": {
        "label": "🧪 MVP / 原型",
        "team_size": "1-3 人",
        "timeline": "1-4 周",
        "agents": 3,
    },
    "startup": {
        "label": "🚀 创业 / 小团队",
        "team_size": "3-7 人",
        "timeline": "1-3 月",
        "agents": 5,
    },
    "growth": {
        "label": "📈 增长期",
        "team_size": "7-15 人",
        "timeline": "3-6 月",
        "agents": 7,
    },
    "enterprise": {
        "label": "🏢 企业级",
        "team_size": "15+ 人",
        "timeline": "6-12 月",
        "agents": 9,
    },
}

PROJECT_TEMPLATES = {
    # ── Web / SaaS ──
    "saas-dashboard": {
        "label": "📊 SaaS Dashboard",
        "description": "数据驱动的 SaaS 管理后台",
        "keywords": ["dashboard", "看板", "saas", "管理后台", "admin", "数据面板", "监控", "analytics"],
        "tech_stack": {
            "frontend": ["React 18 + TypeScript", "Next.js", "Ant Design / Shadcn"],
            "backend": ["Python FastAPI", "Node.js Express", "Go Gin"],
            "database": ["PostgreSQL", "Redis", "ClickHouse (分析)"],
            "infra": ["Docker + K8s", "Nginx", "GitHub Actions"],
        },
        "agents": [
            ("product-manager", "需求分析 & 路线图", ["PRD撰写", "用户分层", "竞品分析"]),
            ("architect", "系统架构设计", ["微服务", "API设计", "数据库建模"]),
            ("frontend-dev", "前端 UI & 交互", ["React", "TypeScript", "可视化"]),
            ("backend-dev", "后端 API & 数据", ["FastAPI", "SQL", "缓存策略"]),
            ("devops", "部署 & CI/CD", ["Docker", "K8s", "监控"]),
            ("qa-engineer", "测试 & 质量", ["E2E测试", "性能测试", "安全扫描"]),
        ],
    },
    "webapp-fullstack": {
        "label": "🌐 全栈 Web 应用",
        "description": "用户端 + 管理端的完整 Web 应用",
        "keywords": ["web", "网站", "全栈", "fullstack", "app", "应用", "平台", "platform"],
        "tech_stack": {
            "frontend": ["Next.js 14", "React 18 + TypeScript", "Tailwind CSS"],
            "backend": ["Python FastAPI / Django", "Node.js (可选)"],
            "database": ["PostgreSQL", "Redis"],
            "infra": ["Vercel / AWS", "Docker", "GitHub Actions"],
        },
        "agents": [
            ("product-manager", "需求分析 & 路线图", ["PRD撰写", "用户故事", "Roadmap"]),
            ("architect", "系统架构设计", ["全栈架构", "API设计", "安全方案"]),
            ("frontend-dev", "前端开发", ["React", "Next.js", "响应式设计"]),
            ("backend-dev", "后端开发", ["API", "数据库", "认证系统"]),
            ("devops", "部署运维", ["CI/CD", "云部署", "域名/SSL"]),
            ("qa-engineer", "质量保证", ["自动化测试", "性能优化"]),
        ],
    },
    "ecommerce": {
        "label": "🛒 电商 / Marketplace",
        "description": "在线商城或多方交易平台",
        "keywords": ["电商", "商城", "marketplace", "交易", "shop", "商品", "订单", "支付"],
        "tech_stack": {
            "frontend": ["Next.js / Nuxt", "React / Vue", "Tailwind"],
            "backend": ["Python FastAPI", "Node.js", "微服务架构"],
            "database": ["PostgreSQL", "Redis", "Elasticsearch"],
            "infra": ["AWS / 阿里云", "K8s", "CDN"],
        },
        "agents": [
            ("product-manager", "产品策略", ["市场分析", "GMV建模", "用户增长"]),
            ("architect", "架构设计", ["高并发", "分布式事务", "搜索架构"]),
            ("frontend-dev", "前端 & 体验", ["SSR", "PWA", "支付UI"]),
            ("backend-dev", "后端 & 交易", ["订单系统", "支付集成", "库存"]),
            ("devops", "基础设施", ["弹性伸缩", "灾备", "安全合规"]),
            ("security-by-design", "安全架构", ["支付安全", "数据加密", "风控"]),
            ("qa-engineer", "质量保证", ["压测", "安全测试", "兼容性"]),
        ],
    },
    # ── AI / ML ──
    "ai-agent": {
        "label": "🤖 多 Agent 系统",
        "description": "AI Agent 协作系统 / 舰队",
        "keywords": ["agent", "ai agent", "多agent", "multi-agent", "swarm", "舰队", "智能体", "llm", "大模型"],
        "tech_stack": {
            "frontend": ["Next.js", "React", "WebSocket 实时通信"],
            "backend": ["Python FastAPI", "LangChain / CrewAI", "WebSocket"],
            "database": ["PostgreSQL", "Vector DB (Qdrant/Pinecone)", "Redis"],
            "infra": ["Docker", "GPU 集群", "消息队列 (RabbitMQ)"],
        },
        "agents": [
            ("apex-pm", "Agent 项目管理", ["任务分解", "调度策略", "KPI追踪"]),
            ("architect", "Agent 架构", ["通信协议", "状态管理", "安全沙箱"]),
            ("backend-dev", "Agent 工具开发", ["Function Calling", "MCP协议", "插件系统"]),
            ("ml-engineer", "模型 & 推理", ["模型选型", "Fine-tuning", "推理优化"]),
            ("devops", "基础设施", ["GPU集群", "模型部署", "监控告警"]),
            ("fleet-commander", "舰队管理", ["Agent生命周期", "负载均衡", "故障恢复"]),
            ("qa-engineer", "质量 & 安全", ["Agent行为测试", "幻觉检测", "安全审计"]),
        ],
    },
    "ml-platform": {
        "label": "🧠 ML 平台 / AI 基础设施",
        "description": "模型训练、部署、监控平台",
        "keywords": ["ml", "机器学习", "训练", "模型", "推理", "gpu", "pipeline", "数据标注"],
        "tech_stack": {
            "frontend": ["React", "D3.js / ECharts", "JupyterHub"],
            "backend": ["Python FastAPI", "Celery", "gRPC"],
            "database": ["PostgreSQL", "MinIO / S3", "MLflow"],
            "infra": ["K8s + GPU", "Kubeflow", "Prometheus + Grafana"],
        },
        "agents": [
            ("ml-engineer", "ML 架构", ["训练Pipeline", "模型管理", "AutoML"]),
            ("data-engineer", "数据工程", ["ETL", "特征工程", "数据湖"]),
            ("backend-dev", "平台开发", ["API", "调度系统", "多租户"]),
            ("devops", "GPU 基础设施", ["GPU集群", "CUDA优化", "成本控制"]),
            ("qa-engineer", "质量验证", ["模型评估", "A/B测试", "漂移检测"]),
        ],
    },
    # ── Data & Analytics ──
    "data-platform": {
        "label": "📊 数据平台 / 分析系统",
        "description": "数据仓库、BI、实时分析",
        "keywords": ["数据", "data", "分析", "analytics", "bi", "报表", "数仓", "etl", "大数据"],
        "tech_stack": {
            "frontend": ["React", "Ant Design", "ECharts / D3.js"],
            "backend": ["Python FastAPI", "Apache Spark", "dbt"],
            "database": ["ClickHouse", "PostgreSQL", "Kafka"],
            "infra": ["K8s", "Airflow", "Grafana"],
        },
        "agents": [
            ("data-engineer", "数据管道", ["ETL", "Spark", "数据湖"]),
            ("data-analyst", "数据分析", ["SQL", "可视化", "指标体系"]),
            ("backend-dev", "平台开发", ["API", "查询引擎", "权限"]),
            ("devops", "基础设施", ["集群管理", "监控", "成本优化"]),
            ("qa-engineer", "数据质量", ["数据测试", "一致性", "准确性"]),
        ],
    },
    # ── FinOps / Cloud ──
    "finops": {
        "label": "💰 FinOps / 云成本优化",
        "description": "多云成本分析、优化、治理平台",
        "keywords": ["finops", "成本", "cost", "云", "cloud", "aws", "计费", "billing", "优化"],
        "tech_stack": {
            "frontend": ["React", "Recharts", "Tailwind"],
            "backend": ["Python FastAPI", "Pandas", "Celery"],
            "database": ["PostgreSQL", "TimescaleDB", "Redis"],
            "infra": ["Docker", "K8s", "多云 SDK"],
        },
        "agents": [
            ("finops-architect", "成本架构", ["多云策略", "预留实例", "FinOps框架"]),
            ("finops-backend", "后端分析", ["成本归因", "异常检测", "预测模型"]),
            ("finops-devops", "基础设施", ["资源优化", "自动化", "Tag治理"]),
            ("finops-frontend", "可视化", ["Dashboard", "报表", "告警"]),
            ("qa-engineer", "质量保证", ["数据准确性", "集成测试"]),
        ],
    },
    # ── CLI / Tools ──
    "cli-tool": {
        "label": "⌨️  CLI 工具 / 开发者工具",
        "description": "命令行工具、开发框架、SDK",
        "keywords": ["cli", "命令行", "tool", "工具", "sdk", "lib", "库", "framework", "框架", "devtools"],
        "tech_stack": {
            "frontend": ["N/A (CLI)"],
            "backend": ["Python Click/Typer", "Go Cobra", "Rust Clap"],
            "database": ["SQLite (可选)", "无/Local JSON"],
            "infra": ["GitHub Actions", "Homebrew", "PyPI / npm"],
        },
        "agents": [
            ("backend-dev", "核心开发", ["CLI框架", "插件系统", "配置管理"]),
            ("devops", "发布 & 分发", ["Homebrew", "PyPI", "CI/CD"]),
            ("qa-engineer", "测试", ["集成测试", "跨平台", "边缘用例"]),
        ],
    },
    # ── Mobile ──
    "mobile-app": {
        "label": "📱 移动应用",
        "description": "iOS / Android / 跨平台 App",
        "keywords": ["mobile", "移动", "app", "ios", "android", "flutter", "react native", "小程序"],
        "tech_stack": {
            "frontend": ["React Native / Flutter", "SwiftUI (iOS)", "Kotlin (Android)"],
            "backend": ["Python FastAPI", "Firebase", "GraphQL"],
            "database": ["PostgreSQL", "Firebase Firestore", "Redis"],
            "infra": ["AWS / GCP", "Fastlane", "App Store Connect"],
        },
        "agents": [
            ("product-manager", "产品策略", ["用户调研", "ASO", "A/B测试"]),
            ("architect", "架构设计", ["离线优先", "推送", "同步策略"]),
            ("frontend-dev", "移动开发", ["React Native", "原生模块", "UI"]),
            ("backend-dev", "API 开发", ["REST/GraphQL", "实时通信", "认证"]),
            ("devops", "发布管理", ["CI/CD", "TestFlight", "灰度发布"]),
            ("qa-engineer", "测试", ["设备测试", "性能", "安全"]),
        ],
    },
    # ── Security ──
    "security-tool": {
        "label": "🔒 安全工具 / 平台",
        "description": "安全扫描、渗透测试、合规审计",
        "keywords": ["security", "安全", "渗透", "扫描", "vulnerability", "合规", "audit", "审计"],
        "tech_stack": {
            "frontend": ["React", "Tailwind", "Cytoscape (拓扑图)"],
            "backend": ["Python / Go", "异步任务队列", "Nmap/ nuclei集成"],
            "database": ["PostgreSQL", "Elasticsearch", "Neo4j"],
            "infra": ["Docker", "K8s", "VPN/专线"],
        },
        "agents": [
            ("security-by-design", "安全架构", ["威胁建模", "安全设计", "零信任"]),
            ("vulnerability-scanner", "漏洞扫描", ["自动化扫描", "CVE跟踪", "报告"]),
            ("penetration-tester", "渗透测试", ["红队", "漏洞验证", "利用链"]),
            ("backend-dev", "平台开发", ["扫描引擎", "API", "规则引擎"]),
            ("devops", "安全基础设施", ["安全CI/CD", "镜像扫描", "密钥管理"]),
            ("security-compliance", "合规审计", ["SOC2", "ISO27001", "等保"]),
        ],
    },
    # ── Content / Media ──
    "content-platform": {
        "label": "📝 内容平台 / 媒体",
        "description": "博客、视频、知识库、社区",
        "keywords": ["内容", "博客", "视频", "社区", "知识库", "wiki", "媒体", "cms", "发布"],
        "tech_stack": {
            "frontend": ["Next.js", "MDX", "Tailwind"],
            "backend": ["Python / Node.js", "Headless CMS", "全文搜索"],
            "database": ["PostgreSQL", "Redis", "Meilisearch"],
            "infra": ["Vercel / Cloudflare", "CDN", "对象存储"],
        },
        "agents": [
            ("product-manager", "内容策略", ["用户增长", "SEO", "变现模型"]),
            ("frontend-dev", "前端 & SEO", ["SSR", "Core Web Vitals", "交互"]),
            ("backend-dev", "后端 & CMS", ["内容API", "搜索", "推荐"]),
            ("devops", "部署 & CDN", ["边缘部署", "缓存", "监控"]),
            ("qa-engineer", "质量 & 可访问性", ["Lighthouse", "a11y", "多语言"]),
        ],
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGING TEMPLATES — WeChat / DingTalk / Feishu
# ═══════════════════════════════════════════════════════════════════════════════

MESSAGING_TEMPLATES = {
    "wechat": {
        "label": "💬 微信 (企业微信)",
        "config_keys": ["corp_id", "agent_id", "app_secret", "webhook_url"],
        "setup_guide": "企业微信管理后台 → 应用管理 → 创建应用 → 获取 Corp ID / Agent ID / Secret",
    },
    "dingtalk": {
        "label": "📌 钉钉",
        "config_keys": ["app_key", "app_secret", "robot_webhook"],
        "setup_guide": "钉钉开放平台 → 创建应用 → 获取 AppKey / AppSecret → 添加机器人 Webhook",
    },
    "feishu": {
        "label": "🚀 飞书",
        "config_keys": ["app_id", "app_secret", "webhook_url"],
        "setup_guide": "飞书开放平台 → 创建企业自建应用 → 获取 App ID / Secret → 添加 Bot",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# PROJECT FACTORY — main interactive wizard
# ═══════════════════════════════════════════════════════════════════════════════

class ProjectFactory:
    """Interactive project bootstrapper with intelligent agent matching."""

    def __init__(self, name: str, project_dir: Path, console: Console):
        self.name = name
        self.project_dir = project_dir
        self.project_path = project_dir / name
        self.console = console

        # Collected state
        self.description = ""
        self.project_type = "saas-dashboard"
        self.scale = "startup"
        self.tech_stack = {}
        self.selected_agents = []
        self.integrations = {}
        self.roadmap = {}
        self.provider = "deepseek"
        self.model = "deepseek-v4-pro"

    def run(self) -> bool:
        """Run the full interactive wizard. Returns True if project was created."""
        try:
            self._step_welcome()
            if not self._step_identity():
                return False
            self._step_type()
            self._step_scale()
            self._step_tech_stack()
            self._step_agents()
            self._step_integrations()
            self._step_roadmap()
            if not self._step_confirm():
                return False
            self._create_project()
            self._show_success()
            return True
        except KeyboardInterrupt:
            self.console.print("\n[dim]已取消[/]")
            return False

    # ── Steps ──

    def _step_welcome(self):
        self.console.print()
        self.console.print(Panel(
            "[bold cyan]🏗️  Apex 项目工厂[/]\n"
            "[dim]8 步智能向导 → 分析目标 → 推荐技术栈 → 分配 Agent 团队 → 生成 Roadmap[/]",
            border_style="cyan",
        ))

    def _step_identity(self) -> bool:
        self.console.print(f"\n[bold]📋 Step 1/8: 项目身份[/]")

        if self.name == "my-project":
            self.name = Prompt.ask("  项目名称", default="my-apex-project")

        self.project_path = self.project_dir / self.name
        if self.project_path.exists():
            self.console.print(f"  [yellow]⚠ 目录已存在: {self.project_path}[/]")
            if not Confirm.ask("  覆盖?", default=False):
                self.console.print("[red]✗ 已取消[/]")
                return False

        self.description = Prompt.ask("  一句话描述", default="")
        tagline = Prompt.ask("  项目标签 (可选)", default="")
        if tagline:
            self.description = f"{self.description} [{tagline}]"
        return True

    def _step_type(self):
        self.console.print(f"\n[bold]🔍 Step 2/8: 项目类型[/]")

        # Auto-detect
        detected = self._auto_detect_type()
        if detected:
            preset = PROJECT_TEMPLATES[detected]
            self.console.print(f"  [green]🔮 智能识别: {preset['label']}[/]")
            self.console.print(f"      {preset['description']}")
            if Confirm.ask("  确认?", default=True):
                self.project_type = detected
                return

        # Manual selection
        self.console.print(f"\n  [bold]选择项目类型:[/]")
        items = list(PROJECT_TEMPLATES.items())
        for i, (key, preset) in enumerate(items, 1):
            self.console.print(f"  [{i:2d}] {preset['label']:<30s} {preset['description']}")

        choice = Prompt.ask("  输入编号", default="1")
        idx = int(choice) - 1 if choice.isdigit() else 0
        self.project_type = items[min(max(idx, 0), len(items) - 1)][0]
        self.console.print(f"  [green]✓ {PROJECT_TEMPLATES[self.project_type]['label']}[/]")

    def _auto_detect_type(self) -> str | None:
        """Auto-detect project type from description keywords."""
        if not self.description:
            return None
        desc_lower = self.description.lower()
        scores = {}
        for key, preset in PROJECT_TEMPLATES.items():
            score = sum(1 for kw in preset["keywords"] if kw in desc_lower)
            if score > 0:
                scores[key] = score
        if scores:
            best = max(scores, key=lambda k: scores[k])
            if scores[best] >= 1:  # At least 1 keyword match
                return best
        return None

    def _step_scale(self):
        self.console.print(f"\n[bold]📐 Step 3/8: 项目规模[/]")
        for i, (key, tier) in enumerate(SCALE_TIERS.items(), 1):
            self.console.print(
                f"  [{i}] {tier['label']:<20s} "
                f"团队: {tier['team_size']:<10s} "
                f"周期: {tier['timeline']}"
            )
        choice = Prompt.ask("  选择规模", default="2")
        idx = int(choice) - 1 if choice.isdigit() else 1
        keys = list(SCALE_TIERS.keys())
        self.scale = keys[min(max(idx, 0), len(keys) - 1)]
        self.console.print(f"  [green]✓ {SCALE_TIERS[self.scale]['label']}[/]")

    def _step_tech_stack(self):
        preset = PROJECT_TEMPLATES[self.project_type]
        self.console.print(f"\n[bold]⚡ Step 4/8: 技术栈[/]")
        self.console.print(f"  [dim]基于 {preset['label']} 的推荐技术栈:[/]")

        self.tech_stack = {}
        for category, options in preset["tech_stack"].items():
            self.console.print(f"\n  [bold]{category}:[/]")
            for i, opt in enumerate(options, 1):
                self.console.print(f"    [{i}] {opt}")

            if len(options) == 1 and options[0].startswith("N/A"):
                self.tech_stack[category] = []
                continue

            picks = Prompt.ask(
                f"  选择 (逗号分隔, 回车=全部)", default=""
            ).strip()

            if not picks:
                self.tech_stack[category] = options
            else:
                selected = []
                for p in picks.split(","):
                    p = p.strip()
                    if p.isdigit() and 1 <= int(p) <= len(options):
                        selected.append(options[int(p) - 1])
                self.tech_stack[category] = selected or options[:1]

        # Allow custom additions
        if Confirm.ask("\n  添加自定义技术?", default=False):
            cat = Prompt.ask("  类别 (frontend/backend/database/infra)")
            tech = Prompt.ask("  技术名称")
            if cat in self.tech_stack:
                self.tech_stack[cat].append(tech)

    def _step_agents(self):
        preset = PROJECT_TEMPLATES[self.project_type]
        tier = SCALE_TIERS[self.scale]
        max_agents = tier["agents"]

        self.console.print(f"\n[bold]👥 Step 5/8: Agent 团队[/]")
        self.console.print(f"  [dim]推荐 {len(preset['agents'])} 个角色 (规模限制: ≤{max_agents})[/]")

        # Show available agent pool
        agent_table = Table(show_header=True, title="推荐 Agent 池")
        agent_table.add_column("#", style="dim", width=3)
        agent_table.add_column("Agent", style="cyan")
        agent_table.add_column("角色", style="dim")
        agent_table.add_column("核心技能")

        self.selected_agents = []
        for i, (agent_id, role, skills) in enumerate(preset["agents"], 1):
            agent_table.add_row(str(i), agent_id, role, ", ".join(skills[:3]))

        self.console.print(agent_table)

        # Select agents
        self.console.print(f"\n  [dim]回车确认全部，逗号分隔选择，输入 'none' 跳过[/]")
        picks = Prompt.ask("  选择 Agent (编号)", default="").strip()

        if picks.lower() == "none":
            self.selected_agents = [("default", "通用助手", ["general"])]
        elif not picks:
            # Default: take all up to max
            self.selected_agents = [
                (aid, role, skills) for aid, role, skills in preset["agents"][:max_agents]
            ]
        else:
            for p in picks.split(","):
                p = p.strip()
                if p.isdigit() and 1 <= int(p) <= len(preset["agents"]):
                    self.selected_agents.append(preset["agents"][int(p) - 1])
            if not self.selected_agents:
                self.selected_agents = [("default", "通用助手", ["general"])]

        # Add custom agent
        if len(self.selected_agents) < max_agents and Confirm.ask(
            f"  添加自定义 Agent? ({len(self.selected_agents)}/{max_agents})", default=False
        ):
            custom_id = Prompt.ask("  Agent ID (小写+连字符)")
            custom_role = Prompt.ask("  角色描述")
            self.selected_agents.append((custom_id, custom_role, ["custom"]))

        # Remove agents
        if len(self.selected_agents) > 1 and Confirm.ask("  移除某个 Agent?", default=False):
            for i, (aid, role, _) in enumerate(self.selected_agents, 1):
                self.console.print(f"  [{i}] {aid} ({role})")
            remove = Prompt.ask("  输入要移除的编号")
            if remove.isdigit() and 1 <= int(remove) <= len(self.selected_agents):
                removed = self.selected_agents.pop(int(remove) - 1)
                self.console.print(f"  [dim]已移除 {removed[0]}[/]")

        # Confirm team
        self.console.print(f"\n  [green]✓ 团队确认 ({len(self.selected_agents)} Agent):[/]")
        for aid, role, _ in self.selected_agents:
            self.console.print(f"    • {aid:<25s} {role}")

    def _step_integrations(self):
        self.console.print(f"\n[bold]🔌 Step 6/8: 消息集成[/]")
        self.console.print("  [dim]配置后可实时推送任务状态到群聊[/]")

        self.integrations = {}
        for key, template in MESSAGING_TEMPLATES.items():
            if Confirm.ask(f"  配置 {template['label']}?", default=False):
                self.console.print(f"  [dim]{template['setup_guide']}[/]")
                config = {}
                for config_key in template["config_keys"]:
                    val = Prompt.ask(f"    {config_key}", default="").strip()
                    if val:
                        config[config_key] = val
                if config:
                    self.integrations[key] = config
                    self.console.print(f"  [green]✓ {template['label']} 已配置[/]")

    def _step_roadmap(self):
        self.console.print(f"\n[bold]🗺️  Step 7/8: Roadmap & 任务计划[/]")

        tier = SCALE_TIERS[self.scale]
        preset = PROJECT_TEMPLATES[self.project_type]

        # MVP definition
        self.console.print(f"\n  [bold]🎯 MVP 定义[/]")
        mvp_desc = Prompt.ask(
            "  MVP 核心功能 (一句话)", default=f"{preset['description']}的最小可用版本"
        )
        mvp_days = IntPrompt.ask("  MVP 预计天数", default=14)

        # 24h plan
        self.console.print(f"\n  [bold]⏰ 首个 24 小时任务计划[/]")
        self.console.print("  [dim]自动生成 6 个时间块的任务:[/]")

        now = datetime.now()
        plan_blocks = [
            ("0-2h", "环境搭建", f"初始化项目结构、配置开发环境、{self.name} repo"),
            ("2-4h", "核心设计", f"系统架构设计、数据库 Schema、API 契约"),
            ("4-8h", "基础设施", "CI/CD Pipeline、Docker 配置、开发/ staging 环境"),
            ("8-16h", "核心开发", f"实现 {mvp_desc} 的核心功能模块"),
            ("16-20h", "集成测试", "端到端测试、性能基线、错误处理"),
            ("20-24h", "部署上线", "生产环境部署、监控告警、文档"),
        ]

        for time_block, title, desc in plan_blocks:
            self.console.print(f"    [{time_block}] {title}: {desc}")

        if not Confirm.ask("  确认计划?", default=True):
            # Let user customize
            self.console.print("  [dim]跳过自动计划，可在项目内手动调整[/]")

        # Sprint tasks
        self.console.print(f"\n  [bold]🏃 Sprint 任务分解[/]")
        sprint_tasks = []
        for agent_id, role, _ in self.selected_agents[:5]:
            task_count = IntPrompt.ask(f"  {agent_id} 的任务数", default=3)
            for j in range(task_count):
                task_name = Prompt.ask(f"    任务 {j+1}", default=f"{role} - Phase {j+1}")
                sprint_tasks.append({
                    "agent": agent_id,
                    "task": task_name,
                    "status": "todo",
                    "phase": j + 1,
                })

        self.roadmap = {
            "mvp": {"description": mvp_desc, "days": mvp_days},
            "plan_24h": [{"time": t, "title": ti, "desc": d} for t, ti, d in plan_blocks],
            "sprint_tasks": sprint_tasks,
            "scale": self.scale,
            "timeline": SCALE_TIERS[self.scale]["timeline"],
        }

    def _step_confirm(self) -> bool:
        self.console.print(f"\n[bold]✅ Step 8/8: 确认创建[/]")

        # Summary
        summary = Table(title="📋 项目摘要", show_header=False)
        summary.add_column(style="dim"); summary.add_column()
        summary.add_row("名称", self.name)
        summary.add_row("类型", PROJECT_TEMPLATES[self.project_type]["label"])
        summary.add_row("规模", SCALE_TIERS[self.scale]["label"])
        summary.add_row("路径", str(self.project_path))
        summary.add_row("Agent 数", str(len(self.selected_agents)))
        summary.add_row("集成", ", ".join(self.integrations.keys()) or "无")
        self.console.print(summary)

        if not Confirm.ask("\n  确认创建项目?", default=True):
            self.console.print("[red]✗ 已取消[/]")
            return False
        return True

    def _create_project(self):
        """Create all project artifacts."""
        self.console.print(f"\n[bold]🏗️  正在创建项目...[/]")

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            # 1. Create directory
            t1 = progress.add_task("创建目录结构...", total=1)
            self.project_path.mkdir(parents=True, exist_ok=True)
            (self.project_path / "teams").mkdir(exist_ok=True)
            (self.project_path / "docs").mkdir(exist_ok=True)
            (self.project_path / ".apex").mkdir(exist_ok=True)
            progress.update(t1, completed=1)

            # 2. apex.yaml
            t2 = progress.add_task("生成 apex.yaml...", total=1)
            config = {
                "project": self.name,
                "description": self.description or PROJECT_TEMPLATES[self.project_type]["description"],
                "type": self.project_type,
                "scale": self.scale,
                "apex_version": "0.5.0",
                "default_provider": self.provider,
                "default_model": self.model,
                "team": [aid for aid, _, _ in self.selected_agents],
                "created_at": datetime.now().isoformat(),
            }
            with open(self.project_path / "apex.yaml", "w") as f:
                yaml.dump(config, f, allow_unicode=True, sort_keys=False)
            progress.update(t2, completed=1)

            # 3. Tech stack
            t3 = progress.add_task("写入技术栈...", total=1)
            tech_doc = self._generate_tech_doc()
            with open(self.project_path / "docs" / "TECH_STACK.md", "w") as f:
                f.write(tech_doc)
            progress.update(t3, completed=1)

            # 4. Agent profiles
            t4 = progress.add_task("创建 Agent Profiles...", total=len(self.selected_agents))
            pm = ProfileManager()
            for agent_id, role_desc, skills in self.selected_agents:
                pm.create_default(
                    agent_id,
                    role=f"{role_desc} ({self.name})",
                    expertise=skills if isinstance(skills, list) else [self.project_type],
                )
                progress.update(t4, advance=1)

            # 5. Roadmap
            t5 = progress.add_task("生成 Roadmap...", total=1)
            roadmap_doc = self._generate_roadmap_doc()
            with open(self.project_path / "docs" / "ROADMAP.md", "w") as f:
                f.write(roadmap_doc)
            # Also save as structured JSON for programmatic access
            with open(self.project_path / ".apex" / "roadmap.json", "w") as f:
                json.dump(self.roadmap, f, indent=2, ensure_ascii=False, default=str)
            progress.update(t5, completed=1)

            # 6. Integrations config
            t6 = progress.add_task("配置集成...", total=1)
            if self.integrations:
                with open(self.project_path / ".apex" / "integrations.yaml", "w") as f:
                    yaml.dump(self.integrations, f, allow_unicode=True)
            progress.update(t6, completed=1)

            # 7. README
            t7 = progress.add_task("生成 README...", total=1)
            readme = self._generate_readme()
            with open(self.project_path / "README.md", "w") as f:
                f.write(readme)
            progress.update(t7, completed=1)

            # 8. .gitignore
            t8 = progress.add_task("创建 .gitignore...", total=1)
            with open(self.project_path / ".gitignore", "w") as f:
                f.write("# Apex project\n.apex/state.*\n*.pyc\n__pycache__/\n.env\n")
            progress.update(t8, completed=1)

            # 9. AGENTS.md (Hermes project context injection)
            t9 = progress.add_task("生成 AGENTS.md (Hermes 上下文)...", total=1)
            from apex.interface.hermes_context import sync_agents_md
            sync_agents_md(self.project_path)
            progress.update(t9, completed=1)

    def _generate_tech_doc(self) -> str:
        preset = PROJECT_TEMPLATES[self.project_type]
        doc = f"# {self.name} — 技术栈\n\n"
        doc += f"> 类型: {preset['label']} | 规模: {SCALE_TIERS[self.scale]['label']}\n\n"
        for cat, techs in self.tech_stack.items():
            doc += f"## {cat}\n"
            for t in techs:
                doc += f"- {t}\n"
            doc += "\n"
        doc += "## Agent 团队\n"
        for aid, role, skills in self.selected_agents:
            doc += f"- **{aid}**: {role} ({', '.join(skills) if isinstance(skills, list) else skills})\n"
        return doc

    def _generate_roadmap_doc(self) -> str:
        doc = f"# {self.name} — Roadmap\n\n"
        doc += f"> MVP: {self.roadmap['mvp']['description']} ({self.roadmap['mvp']['days']}天)\n"
        doc += f"> 周期: {self.roadmap['timeline']}\n\n"

        doc += "## ⏰ 首个 24 小时\n\n"
        doc += "| 时间段 | 任务 | 描述 |\n"
        doc += "|--------|------|------|\n"
        for block in self.roadmap["plan_24h"]:
            doc += f"| {block['time']} | {block['title']} | {block['desc']} |\n"

        doc += "\n## 🏃 Sprint 任务\n\n"
        doc += "| Agent | 任务 | Phase | 状态 |\n"
        doc += "|-------|------|-------|------|\n"
        for task in self.roadmap["sprint_tasks"]:
            doc += f"| {task['agent']} | {task['task']} | {task['phase']} | {task['status']} |\n"

        return doc

    def _generate_readme(self) -> str:
        preset = PROJECT_TEMPLATES[self.project_type]
        readme = f"# {self.name}\n\n"
        readme += f"> {self.description or preset['description']}\n\n"
        readme += f"**类型**: {preset['label']} | **规模**: {SCALE_TIERS[self.scale]['label']}\n\n"

        readme += "## 👥 Agent 团队\n\n"
        readme += "| Agent | 角色 | 技能 |\n"
        readme += "|-------|------|------|\n"
        for aid, role, skills in self.selected_agents:
            sk = ", ".join(skills) if isinstance(skills, list) else str(skills)
            readme += f"| {aid} | {role} | {sk} |\n"

        readme += "\n## 🚀 快速开始\n\n"
        readme += "```bash\n"
        readme += f"cd {self.name}\n"
        if self.selected_agents:
            readme += f"apex run \"第一个任务\" -p {self.selected_agents[0][0]}\n"
        readme += "apex pm dashboard          # 项目管理面板\n"
        readme += "apex fleet status          # Agent 状态\n"
        readme += "```\n\n"

        if self.integrations:
            readme += "## 🔌 消息集成\n\n"
            for key in self.integrations:
                readme += f"- {MESSAGING_TEMPLATES[key]['label']}: 已配置 ✅\n"

        readme += "\n## 📁 项目结构\n\n"
        readme += "```\n"
        readme += f"{self.name}/\n"
        readme += "├── apex.yaml          # 项目配置\n"
        readme += "├── teams/             # Agent 团队定义\n"
        readme += "├── docs/\n"
        readme += "│   ├── TECH_STACK.md  # 技术栈\n"
        readme += "│   └── ROADMAP.md     # 路线图 & 任务\n"
        readme += "├── .apex/             # Apex 运行时数据\n"
        readme += "└── README.md\n"
        readme += "```\n"

        return readme

    def _show_success(self):
        """Display success summary."""
        preset = PROJECT_TEMPLATES[self.project_type]

        self.console.print()
        self.console.print(Panel(
            "[bold green]✅ 项目创建成功![/]",
            border_style="green",
        ))

        # Project card
        card = Table(title="📋 项目卡片", show_header=False, title_style="bold cyan")
        card.add_column(style="dim", width=12)
        card.add_column()
        card.add_row("项目", f"[bold]{self.name}[/]")
        card.add_row("类型", preset["label"])
        card.add_row("规模", SCALE_TIERS[self.scale]["label"])
        card.add_row("路径", str(self.project_path))
        card.add_row("模型", f"{self.provider}/{self.model}")
        self.console.print(card)

        # Agent team
        agent_table = Table(title="👥 Agent 团队", title_style="bold cyan")
        agent_table.add_column("Agent", style="cyan")
        agent_table.add_column("角色")
        agent_table.add_column("技能")
        for aid, role, skills in self.selected_agents:
            sk = ", ".join(skills[:3]) if isinstance(skills, list) else str(skills)
            agent_table.add_row(aid, role, sk)
        self.console.print(agent_table)

        # Tech stack
        if self.tech_stack:
            tech_table = Table(title="⚡ 技术栈", title_style="bold cyan")
            tech_table.add_column("层级", style="dim")
            tech_table.add_column("技术选型")
            for cat, techs in self.tech_stack.items():
                if techs:
                    tech_table.add_row(cat, "\n".join(f"• {t}" for t in techs))
            self.console.print(tech_table)

        # Integrations
        if self.integrations:
            int_table = Table(title="🔌 消息集成", title_style="bold cyan")
            int_table.add_column("平台")
            int_table.add_column("状态")
            for key in self.integrations:
                int_table.add_row(MESSAGING_TEMPLATES[key]["label"], "✅ 已配置")
            self.console.print(int_table)

        # 24h plan
        plan_table = Table(title="⏰ 首个 24 小时计划", title_style="bold cyan")
        plan_table.add_column("时间段", style="dim")
        plan_table.add_column("任务")
        plan_table.add_column("描述")
        for block in self.roadmap.get("plan_24h", []):
            plan_table.add_row(block["time"], block["title"], block["desc"])
        self.console.print(plan_table)

        # Next steps
        first_agent = self.selected_agents[0][0] if self.selected_agents else "default"
        self.console.print(Panel(
            "[bold]🚀 下一步:[/]\n\n"
            f"  [cyan]cd {self.name}[/]\n"
            f"  [cyan]apex run \"开始第一个任务\" -p {first_agent}[/]\n"
            f"  [cyan]apex pm dashboard[/]         项目管理 & 进度追踪\n"
            f"  [cyan]apex fleet start[/]          启动 Agent 舰队\n"
            f"  [cyan]apex status[/]              实时任务视图\n\n"
            f"[dim]文档:[/]\n"
            f"  [dim]docs/TECH_STACK.md   技术栈[/]\n"
            f"  [dim]docs/ROADMAP.md      路线图 & 任务计划[/]\n"
            f"  [dim].apex/roadmap.json   结构化任务数据[/]",
            title="开始使用",
            border_style="green",
        ))
        self.console.print()


# ═══════════════════════════════════════════════════════════════════════════════
# Quick mode (non-interactive)
# ═══════════════════════════════════════════════════════════════════════════════

def quick_init(name: str, project_dir: Path, console: Console):
    """Non-interactive quick init with smart defaults."""
    factory = ProjectFactory(name, project_dir, console)
    factory.project_path = project_dir / name
    if factory.project_path.exists():
        console.print(f"[yellow]⚠ {factory.project_path} already exists[/]")
        return

    # Auto-detect or default
    factory.project_type = factory._auto_detect_type() or "saas-dashboard"
    factory.scale = "startup"
    factory.description = f"{PROJECT_TEMPLATES[factory.project_type]['description']} — {name}"
    factory.tech_stack = {k: v[:2] for k, v in PROJECT_TEMPLATES[factory.project_type]["tech_stack"].items()}
    factory.selected_agents = [
        (aid, role, skills)
        for aid, role, skills in PROJECT_TEMPLATES[factory.project_type]["agents"]
    ][:SCALE_TIERS[factory.scale]["agents"]]
    factory.integrations = {}
    factory.roadmap = {
        "mvp": {"description": f"{name} MVP", "days": 14},
        "plan_24h": [],
        "sprint_tasks": [],
        "scale": factory.scale,
        "timeline": SCALE_TIERS[factory.scale]["timeline"],
    }

    factory._create_project()
    factory._show_success()
