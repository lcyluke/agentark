"""Apex — Skill Registry: Agent Skill Levels & Matcher.

Central registry for agent skill definitions, levels, evidence, and
task-to-agent matching. Persisted as ~/.apex/skill-registry.yaml.

Level System (L0-L5):
  L0 Novice      不了解，需要指导
  L1 Apprentice  能简单完成，需监督
  L2 Practitioner 独立完成标准任务
  L3 Proficient  精通，能优化和教学
  L4 Expert      领域专家，架构决策
  L5 Legend      开创性，能创建工具/框架
"""

from __future__ import annotations

import os
import time
import yaml
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Any

from agentark.core.profile import AGENTARK_HOME

# ── Paths ───────────────────────────────────────────────────────

REGISTRY_PATH = AGENTARK_HOME / "skill-registry.yaml"

# ── Level Constants ─────────────────────────────────────────────

LEVELS = ["L0", "L1", "L2", "L3", "L4", "L5"]

LEVEL_LABELS = {
    "L0": "Novice (新手)",
    "L1": "Apprentice (学徒)",
    "L2": "Practitioner (独立执行)",
    "L3": "Proficient (精通)",
    "L4": "Expert (专家)",
    "L5": "Legend (传奇)",
}


# ════════════════════════════════════════════════════════════════
# Data Classes
# ════════════════════════════════════════════════════════════════


@dataclass
class SkillLevelDef:
    """Definition of a skill at a specific level."""
    description: str = ""
    examples: list[str] = field(default_factory=list)


@dataclass
class SkillDef:
    """Canonical definition of a single skill."""
    name: str = ""
    category: str = "general"
    description: str = ""
    levels: dict[str, SkillLevelDef] = field(default_factory=lambda: {
        lvl: SkillLevelDef() for lvl in LEVELS
    })

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "levels": {k: asdict(v) for k, v in self.levels.items() if v.description},
        }


@dataclass
class EvidenceItem:
    """Evidence of a skill being demonstrated."""
    type: str = "task"  # task, pr, review, session
    ref: str = ""       # Task ID, PR URL, session ID
    description: str = ""
    date: str = ""
    assessed_by: str = "auto"


@dataclass
class AgentSkill:
    """An agent's level for a specific skill."""
    level: str = "L1"
    confidence: float = 0.5  # 0.0-1.0 how certain we are
    assessed_by: str = "origin"
    assessed_at: str = ""
    evidence: list[EvidenceItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "confidence": round(self.confidence, 2),
            "assessed_by": self.assessed_by,
            "assessed_at": self.assessed_at,
            "evidence": [asdict(e) for e in self.evidence],
        }


@dataclass
class AgentSkillSet:
    """All skill levels for a single agent."""
    agent_name: str = ""
    skills: dict[str, AgentSkill] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "skills": {k: v.to_dict() for k, v in sorted(self.skills.items())},
        }


@dataclass
class MatchResult:
    """Result of matching a task to agents by skill."""
    agent_name: str
    match_score: float  # 0.0-1.0
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    details: str = ""


# ════════════════════════════════════════════════════════════════
# Built-in Skill Catalog
# ════════════════════════════════════════════════════════════════

# Full canonical skill catalog
SKILL_CATALOG: dict[str, SkillDef] = {}

def _reg(name: str, category: str, description: str, levels: dict[str, str]):
    """Register a skill definition."""
    SKILL_CATALOG[name] = SkillDef(
        name=name, category=category, description=description,
        levels={k: SkillLevelDef(description=v) for k, v in levels.items()},
    )

# ── Frontend ──
_reg("react-development", "frontend",
     "React component development, hooks, state management",
     {"L0": "不了解 React",
      "L1": "能阅读和理解 React 代码，完成简单修改",
      "L2": "能独立开发 function/class 组件，使用 hooks 管理状态",
      "L3": "能优化性能（memo/useMemo），设计组件架构，自定义 hooks",
      "L4": "理解 Fiber/Concurrent 模式，能做架构决策和性能调优",
      "L5": "能创建 React 工具/框架，贡献核心生态"})

_reg("responsive-design", "frontend",
     "CSS/Tailwind, responsive layouts, mobile-first design",
     {"L0": "不了解响应式设计",
      "L1": "能使用基础 CSS 布局",
      "L2": "能独立使用 Tailwind/Flexbox/Grid 构建响应式页面",
      "L3": "能设计跨设备兼容方案，掌握 CSS 动画和过渡",
      "L4": "能设计完整的 Design System 和主题系统",
      "L5": "能创建 CSS 框架/工具"})

_reg("typescript", "frontend",
     "TypeScript type system, generics, advanced patterns",
     {"L0": "不了解 TypeScript",
      "L1": "能阅读 TypeScript 代码，理解类型注解",
      "L2": "能使用 interface/type/generics 编写类型安全的代码",
      "L3": "能使用 conditional types/mapped types 等高级类型",
      "L4": "能设计类型系统和类型工具库",
      "L5": "能贡献 TypeScript 编译器或类型定义"})

_reg("webpack-config", "frontend",
     "Build tooling: Webpack, Vite, bundler configuration",
     {"L0": "不了解前端构建工具",
      "L1": "能使用 create-react-app/vite 创建项目",
      "L2": "能配置 Webpack loaders/plugins",
      "L3": "能优化构建性能，配置 code splitting/tree shaking",
      "L4": "能自定义构建插件和 loader",
      "L5": "能开发构建工具或打包器"})

# ── Backend ──
_reg("api-design", "backend",
     "RESTful API design, FastAPI/Express, API standards",
     {"L0": "不了解 API 设计",
      "L1": "能编写简单 CRUD 路由",
      "L2": "能设计 RESTful API，处理认证/授权/错误",
      "L3": "能设计 API 规范，实现缓存/限流/版本管理",
      "L4": "能设计大规模 API 架构，API 网关设计",
      "L5": "能设计 API 标准和最佳实践"})

_reg("database-schema", "backend",
     "Database design, PostgreSQL/SQL, schema optimization",
     {"L0": "不了解数据库设计",
      "L1": "能编写简单 SQL 查询",
      "L2": "能设计数据库表结构，使用索引和外键",
      "L3": "能优化查询性能，设计分表/分区方案",
      "L4": "能设计分布式数据库架构，读写分离",
      "L5": "能设计数据库内核或数据仓库方案"})

_reg("system-design", "backend",
     "System architecture, scalability, distributed systems",
     {"L0": "不了解系统设计",
      "L1": "能理解单体架构",
      "L2": "能设计微服务架构",
      "L3": "能设计高可用/可扩展系统",
      "L4": "能设计分布式系统，CAP 权衡",
      "L5": "能设计跨数据中心架构"})

_reg("docker-compose", "backend",
     "Containerization, Docker Compose, container orchestration",
     {"L0": "不了解容器化",
      "L1": "能编写简单 Dockerfile",
      "L2": "能使用 Docker Compose 编排多容器",
      "L3": "能优化 Docker 镜像大小，安全配置",
      "L4": "能设计容器化微服务架构",
      "L5": "能开发容器编排工具"})

# ── DevOps ──
_reg("ci-cd-pipeline", "devops",
     "CI/CD pipeline design, GitHub Actions, automation",
     {"L0": "不了解 CI/CD",
      "L1": "能理解 CI/CD 概念",
      "L2": "能配置 GitHub Actions 流水线",
      "L3": "能设计多环境部署流水线",
      "L4": "能优化构建速度，设计发布策略（蓝绿/金丝雀）",
      "L5": "能创建 CI/CD 工具链"})

_reg("infrastructure-as-code", "devops",
     "Infrastructure automation, Terraform, Pulumi",
     {"L0": "不了解 IaC",
      "L1": "能阅读 Terraform 配置文件",
      "L2": "能使用 Terraform 管理云资源",
      "L3": "能设计模块化 IaC 架构",
      "L4": "能设计多云基础设施",
      "L5": "能开发 IaC 工具/Provider"})

_reg("monitoring-alerting", "devops",
     "Monitoring, alerting, observability, Prometheus/Grafana",
     {"L0": "不了解监控",
      "L1": "能理解监控基本概念",
      "L2": "能配置 Prometheus/Grafana 指标采集",
      "L3": "能设计告警规则和 SLO 体系",
      "L4": "能设计全链路可观测性",
      "L5": "能开发监控工具"})

_reg("docker-kubernetes", "devops",
     "Kubernetes orchestration, cluster management, k8s operators",
     {"L0": "不了解 Kubernetes",
      "L1": "能理解 k8s 核心概念",
      "L2": "能部署和管理 k8s 集群上的应用",
      "L3": "能设计 k8s 网络/存储/安全策略",
      "L4": "能开发 Operator/Custom Controller",
      "L5": "能贡献 k8s 生态"})

# ── PM / Product ──
_reg("prd-writing", "product",
     "Product Requirements Document writing",
     {"L0": "不了解 PRD",
      "L1": "能写简单功能说明",
      "L2": "能写结构化 PRD，含用户故事/验收标准",
      "L3": "能写包含商业模式/ROI 分析的完整 PRD",
      "L4": "能设计产品策略和路线图",
      "L5": "能定义行业级产品方法论"})

_reg("user-research", "product",
     "User research, usability testing, persona design",
     {"L0": "不了解用户研究",
      "L1": "能进行简单的用户访谈",
      "L2": "能设计问卷/用户测试，整理研究发现",
      "L3": "能设计完整的用户研究方案",
      "L4": "能指导产品战略的用户洞察",
      "L5": "能建立用户研究体系"})

_reg("data-analysis", "product",
     "Data analysis, metrics, A/B testing, SQL analytics",
     {"L0": "不了解数据分析",
      "L1": "能理解基础数据指标",
      "L2": "能使用 SQL 分析数据，生成报表",
      "L3": "能设计 A/B 测试，分析实验数据",
      "L4": "能建立数据驱动决策体系",
      "L5": "能设计数据分析平台"})

_reg("roadmap-planning", "product",
     "Product roadmap, OKR planning, prioritization frameworks",
     {"L0": "不了解路线图规划",
      "L1": "能列出功能清单",
      "L2": "能使用 RICE/ICE 框架排优先级",
      "L3": "能制定季度路线图，对齐 OKR",
      "L4": "能设计产品战略和长期路线图",
      "L5": "能建立产品规划方法论"})

# ── AI/ML ──
_reg("machine-learning", "ai-ml",
     "Machine learning model development, training, evaluation",
     {"L0": "不了解机器学习",
      "L1": "能理解 ML 基本概念",
      "L2": "能使用 sklearn/torch 构建标准模型",
      "L3": "能调参/特征工程/模型选择",
      "L4": "能设计深度学习架构",
      "L5": "能发表 ML 研究论文"})

_reg("deep-learning", "ai-ml",
     "Deep learning, neural networks, transformers",
     {"L0": "不了解深度学习",
      "L1": "能理解神经网络基本概念",
      "L2": "能使用 PyTorch/TF 构建标准网络",
      "L3": "能设计自定义网络架构",
      "L4": "能优化训练流程，分布式训练",
      "L5": "能贡献 DL 框架或架构创新"})

_reg("experiment-design", "ai-ml",
     "ML experiment design, validation, metric design",
     {"L0": "不了解实验设计",
      "L1": "能运行标准训练脚本",
      "L2": "能设计训练/验证/测试集，选择评估指标",
      "L3": "能设计对比实验/消融实验",
      "L4": "能设计大规模实验体系",
      "L5": "能定义评估标准"})

_reg("model-deployment", "ai-ml",
     "ML model serving, MLOps, model optimization",
     {"L0": "不了解模型部署",
      "L1": "能使用基础 API 部署模型",
      "L2": "能使用 ONNX/TensorRT 优化推理",
      "L3": "能设计模型管线和 A/B 服务",
      "L4": "能设计大规模推理系统",
      "L5": "能创建推理框架"})

# ── Content / Writing ──
_reg("seo-optimization", "content",
     "SEO content optimization, keyword research, ranking",
     {"L0": "不了解 SEO",
      "L1": "能理解 SEO 基本概念",
      "L2": "能进行关键词研究，优化文章 SEO",
      "L3": "能制定 SEO 策略，分析排名数据",
      "L4": "能设计 SEO 自动化工具",
      "L5": "能建立 SEO 最佳实践体系"})

_reg("copywriting", "content",
     "Copywriting, brand messaging, persuasive writing",
     {"L0": "不了解文案写作",
      "L1": "能写基础文案",
      "L2": "能写品牌文案和营销内容",
      "L3": "能制定品牌声音和文案策略",
      "L4": "能设计全渠道文案体系",
      "L5": "能建立文案方法论"})

_reg("social-media", "content",
     "Social media management, content strategy, engagement",
     {"L0": "不了解社交媒体",
      "L1": "能管理单个社媒账号",
      "L2": "能制定内容日历，分析互动数据",
      "L3": "能设计跨平台社媒策略",
      "L4": "能建立社媒运营体系",
      "L5": "能打造爆款内容策略"})

_reg("content-planning", "content",
     "Content planning, editorial calendar, content audit",
     {"L0": "不了解内容规划",
      "L1": "能列出内容想法",
      "L2": "能制定内容日历和排期",
      "L3": "能进行内容审计和优化",
      "L4": "能设计全渠道内容战略",
      "L5": "能建立内容体系"})

# ── Technical Writing ──
_reg("technical-writing", "technical",
     "Technical documentation, API docs, user manuals",
     {"L0": "不了解技术写作",
      "L1": "能写简单 README",
      "L2": "能写 API 文档和教程",
      "L3": "能写完整技术文档体系",
      "L4": "能设计信息架构",
      "L5": "能创建文档工具/框架"})

_reg("api-documentation", "technical",
     "API documentation, OpenAPI/Swagger, endpoint docs",
     {"L0": "不了解 API 文档",
      "L1": "能阅读 OpenAPI 规范",
      "L2": "能编写 OpenAPI/Swagger 文档",
      "L3": "能设计文档生成流程",
      "L4": "能设计交互式 API 文档平台",
      "L5": "能创建 API 文档工具"})

_reg("knowledge-base", "technical",
     "Knowledge base management, wiki, internal docs",
     {"L0": "不了解知识库管理",
      "L1": "能创建简单知识条目",
      "L2": "能组织知识库结构",
      "L3": "能设计知识分类和搜索方案",
      "L4": "能设计企业知识管理体系",
      "L5": "能创建知识管理平台"})

# ── Data Engineering ──
_reg("etl-pipeline", "data",
     "ETL pipeline design, data transformation, Airflow",
     {"L0": "不了解 ETL 管道",
      "L1": "能编写简单数据脚本",
      "L2": "能使用 Airflow/Dagster 编排管道",
      "L3": "能设计可扩展 ETL 架构",
      "L4": "能设计实时数据管道",
      "L5": "能创建数据管道框架"})

_reg("data-warehouse", "data",
     "Data warehouse design, star schema, data modeling",
     {"L0": "不了解数据仓库",
      "L1": "能理解维度建模",
      "L2": "能设计星型/雪花型模型",
      "L3": "能优化数仓查询性能",
      "L4": "能设计大规模数仓架构",
      "L5": "能设计数据网格架构"})

_reg("sql-optimization", "data",
     "SQL query optimization, indexing, query planning",
     {"L0": "不了解 SQL 优化",
      "L1": "能写基本查询",
      "L2": "能使用 EXPLAIN 分析查询计划",
      "L3": "能优化复杂查询（窗口函数/CTE）",
      "L4": "能设计查询路由和分片方案",
      "L5": "能贡献 SQL 引擎"})

# ── Growth ──
_reg("growth-hacking", "growth",
     "Growth experiments, viral mechanics, user acquisition",
     {"L0": "不了解增长黑客",
      "L1": "能理解增长概念",
      "L2": "能设计和分析增长实验",
      "L3": "能制定全渠道增长策略",
      "L4": "能建立增长引擎（AARRR）",
      "L5": "能创造新增长模式"})

_reg("user-acquisition", "growth",
     "User acquisition channels, CAC optimization, funnel analysis",
     {"L0": "不了解用户获取",
      "L1": "能理解获客渠道",
      "L2": "能分析获客漏斗和 CAC",
      "L3": "能优化付费获客 ROI",
      "L4": "能设计规模化获客体系",
      "L5": "能创建获客方法论"})

_reg("conversion-optimization", "growth",
     "CRO, A/B testing, landing page optimization",
     {"L0": "不了解转化优化",
      "L1": "能理解转化率概念",
      "L2": "能设计 A/B 测试和优化页面",
      "L3": "能制定 CRO 策略",
      "L4": "能建立数据驱动优化体系",
      "L5": "能创建 CRO 框架"})

# ── Research ──
_reg("literature-review", "research",
     "Academic literature review, paper analysis, citation tracking",
     {"L0": "不了解文献综述",
      "L1": "能搜索和阅读论文",
      "L2": "能进行系统性文献综述",
      "L3": "能识别研究趋势和空白",
      "L4": "能撰写高质量综述论文",
      "L5": "能建立领域知识体系"})

_reg("academic-writing", "research",
     "Academic paper writing, research proposals, technical reports",
     {"L0": "不了解学术写作",
      "L1": "能写简单报告",
      "L2": "能写结构化论文",
      "L3": "能写高质量期刊论文",
      "L4": "能撰写研究提案/基金申请",
      "L5": "能定义写作规范和流程"})

# ── General ──
_reg("peer-review", "general",
     "Code/design review, constructive feedback, quality assessment",
     {"L0": "不了解评审",
      "L1": "能发现明显问题",
      "L2": "能进行结构化代码审查",
      "L3": "能做全面设计评审",
      "L4": "能建立评审标准体系",
      "L5": "能创建评审流程框架"})

_reg("quality-assurance", "general",
     "QA testing, test automation, bug tracking",
     {"L0": "不了解 QA",
      "L1": "能手动测试功能",
      "L2": "能写单元测试和集成测试",
      "L3": "能设计测试策略和自动化",
      "L4": "能建立 QA 流程体系",
      "L5": "能创建测试框架"})

_reg("prototyping", "general",
     "Rapid prototyping, MVP development, proof of concept",
     {"L0": "不了解原型设计",
      "L1": "能根据需求做简单原型",
      "L2": "能快速搭建 MVP",
      "L3": "能做 POC 验证技术可行性",
      "L4": "能设计原型到产品化流程",
      "L5": "能创建 MVP 方法论"})

_reg("product-strategy", "general",
     "Product strategy, GTM, competitive analysis, positioning",
     {"L0": "不了解产品策略",
      "L1": "能理解产品定位",
      "L2": "能进行竞品分析",
      "L3": "能制定产品战略",
      "L4": "能制定公司级产品战略",
      "L5": "能定义行业格局"})

_reg("go-to-market", "general",
     "GTM strategy, launch planning, channel strategy",
     {"L0": "不了解GTM",
      "L1": "能理解GTM概念",
      "L2": "能制定产品上线计划",
      "L3": "能设计多渠道GTM策略",
      "L4": "能设计全球化GTM",
      "L5": "能建立GTM方法论"})

_reg("team-building", "general",
     "Team building, talent assessment, organizational design",
     {"L0": "不了解团队建设",
      "L1": "能理解团队角色",
      "L2": "能组建小型团队",
      "L3": "能设计团队架构",
      "L4": "能设计组织架构",
      "L5": "能建立人才体系"})

_reg("ui-design", "general",
     "UI design, design systems, visual design principles",
     {"L0": "不了解 UI 设计",
      "L1": "能使用设计工具做基础界面",
      "L2": "能设计一致性 UI，使用 Design System",
      "L3": "能设计完整设计系统",
      "L4": "能设计品牌级视觉体系",
      "L5": "能创造设计方法论"})

_reg("ux-research", "general",
     "UX research, usability testing, user journey mapping",
     {"L0": "不了解 UX 研究",
      "L1": "能进行基础可用性测试",
      "L2": "能设计用户旅程图",
      "L3": "能制定 UX 策略",
      "L4": "能建立 UX 研究体系",
      "L5": "能创造 UX 研究方法论"})

_reg("design-system", "general",
     "Design systems, component libraries, style guides",
     {"L0": "不了解Design System",
      "L1": "能使用现有组件库",
      "L2": "能搭建组件库和文档",
      "L3": "能设计跨产品Design System",
      "L4": "能建立Design System治理流程",
      "L5": "能创建Design System工具链"})

_reg("analytics", "general",
     "Analytics, data-driven decision making, metric frameworks",
     {"L0": "不了解数据分析",
      "L1": "能理解基础指标",
      "L2": "能使用分析工具做报表",
      "L3": "能建立指标体系",
      "L4": "能设计数据驱动文化",
      "L5": "能创造分析框架"})

# Remove entries with no level descriptions
SKILL_CATALOG = {k: v for k, v in SKILL_CATALOG.items() if any(
    lvl.description for lvl in v.levels.values()
)}

# Agent → baseline skills mapping (from ROLE_SOULS in hermes_sync)
AGENT_BASELINE_SKILLS: dict[str, dict[str, str]] = {
    "product-manager": {
        "prd-writing": "L2",
        "user-research": "L2",
        "data-analysis": "L2",
        "roadmap-planning": "L2",
        "product-strategy": "L1",
        "go-to-market": "L1",
    },
    "frontend-dev": {
        "react-development": "L2",
        "responsive-design": "L2",
        "typescript": "L2",
        "webpack-config": "L1",
    },
    "backend-dev": {
        "api-design": "L2",
        "database-schema": "L2",
        "system-design": "L1",
        "docker-compose": "L2",
    },
    "devops": {
        "ci-cd-pipeline": "L2",
        "infrastructure-as-code": "L2",
        "monitoring-alerting": "L2",
        "docker-kubernetes": "L2",
        "docker-compose": "L2",
    },
    "content-strategist": {
        "seo-optimization": "L2",
        "copywriting": "L2",
        "social-media": "L2",
        "content-planning": "L2",
    },
    "writer": {
        "copywriting": "L2",
        "technical-writing": "L2",
        "social-media": "L1",
    },
    "editor": {
        "peer-review": "L2",
        "quality-assurance": "L2",
        "copywriting": "L1",
    },
    "publisher": {
        "social-media": "L2",
        "content-planning": "L2",
        "analytics": "L1",
    },
    "data-engineer": {
        "etl-pipeline": "L2",
        "data-warehouse": "L2",
        "sql-optimization": "L2",
        "database-schema": "L2",
        "docker-compose": "L1",
    },
    "data-analyst": {
        "sql-optimization": "L2",
        "data-analysis": "L2",
        "analytics": "L2",
    },
    "data-scientist": {
        "machine-learning": "L2",
        "deep-learning": "L1",
        "experiment-design": "L2",
        "model-deployment": "L1",
    },
    "ml-engineer": {
        "machine-learning": "L2",
        "model-deployment": "L2",
        "etl-pipeline": "L1",
        "docker-compose": "L1",
    },
    "ceo-pm": {
        "product-strategy": "L2",
        "prd-writing": "L2",
        "go-to-market": "L2",
        "team-building": "L2",
        "roadmap-planning": "L2",
    },
    "fullstack-dev": {
        "react-development": "L2",
        "api-design": "L2",
        "database-schema": "L2",
        "docker-compose": "L1",
        "typescript": "L2",
    },
    "designer": {
        "ui-design": "L2",
        "ux-research": "L2",
        "design-system": "L2",
        "prototyping": "L2",
        "responsive-design": "L1",
    },
    "growth-marketer": {
        "growth-hacking": "L2",
        "user-acquisition": "L2",
        "conversion-optimization": "L2",
        "analytics": "L2",
        "social-media": "L1",
    },
    "lead-researcher": {
        "literature-review": "L2",
        "experiment-design": "L2",
        "academic-writing": "L2",
    },
    "research-analyst": {
        "literature-review": "L1",
        "data-analysis": "L2",
        "analytics": "L2",
    },
    "technical-writer": {
        "technical-writing": "L2",
        "api-documentation": "L2",
        "knowledge-base": "L2",
    },
    "peer-reviewer": {
        "peer-review": "L2",
        "quality-assurance": "L2",
        "academic-writing": "L1",
    },
    "architect": {
        "system-design": "L3",
        "api-design": "L3",
        "database-schema": "L2",
        "docker-kubernetes": "L2",
    },
    "ai-algorithm": {
        "machine-learning": "L3",
        "deep-learning": "L2",
        "experiment-design": "L2",
        "model-deployment": "L2",
    },
    "ai-vision": {
        "deep-learning": "L2",
        "machine-learning": "L2",
        "experiment-design": "L1",
    },
    "badminton-pm": {
        "roadmap-planning": "L2",
        "data-analysis": "L2",
        "user-research": "L2",
        "prd-writing": "L2",
    },
    "ops-engineer": {
        "ci-cd-pipeline": "L2",
        "monitoring-alerting": "L2",
        "docker-kubernetes": "L2",
        "infrastructure-as-code": "L1",
    },
    "security-compliance": {
        "quality-assurance": "L2",
        "system-design": "L1",
    },
}

# Task difficulty levels
TASK_DIFFICULTY_LEVELS = {
    "L1": {"label": "入门", "description": "简单任务，新手可完成"},
    "L2": {"label": "标准", "description": "常规开发任务"},
    "L3": {"label": "复杂", "description": "需要经验判断"},
    "L4": {"label": "专家", "description": "需要领域深度"},
    "L5": {"label": "开创", "description": "从零到一创新"},
}


# ════════════════════════════════════════════════════════════════
# Skill Registry
# ════════════════════════════════════════════════════════════════


class SkillRegistry:
    """Central skill registry — load, save, query, match.

    Thread-safe for single-process use. When multi-tenancy is needed,
    wrap with file locking.
    """

    def __init__(self, path: Path | str = None):
        self.path = Path(path or REGISTRY_PATH)
        self._data: dict = {"version": 1, "skills": {}, "agents": {}, "task_difficulty": {}}
        self._loaded = False

    # ── Load / Save ──────────────────────────────────────────

    def load(self) -> dict:
        """Load registry from YAML file. Creates default if missing."""
        if self.path.exists():
            with open(self.path) as f:
                raw = yaml.safe_load(f) or {}
            self._data = raw
        else:
            self._init_default()
        self._loaded = True
        return self._data

    def save(self):
        """Persist registry to YAML."""
        self._data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            yaml.dump(self._data, f, default_flow_style=False, allow_unicode=True)

    def _init_default(self):
        """Initialize registry with built-in skill catalog and baseline agents."""
        # Skill definitions
        skills_out = {}
        for sname, sdef in SKILL_CATALOG.items():
            skills_out[sname] = sdef.to_dict()
        self._data["version"] = 1
        self._data["skills"] = skills_out

        # Agent baseline assignments
        agents_out = {}
        now = time.strftime("%Y-%m-%d")
        for aname, skills in AGENT_BASELINE_SKILLS.items():
            agent_skills = {}
            for sname, level in skills.items():
                agent_skills[sname] = {
                    "level": level,
                    "confidence": 0.6,
                    "assessed_by": "origin",
                    "assessed_at": now,
                    "evidence": [{
                        "type": "initialization",
                        "ref": "template-baseline",
                        "description": f"Initial baseline from profile template",
                        "date": now,
                    }],
                }
            agents_out[aname] = {"agent_name": aname, "skills": agent_skills}
        self._data["agents"] = agents_out

        # Task difficulty
        self._data["task_difficulty"] = {}
        for lvl, info in TASK_DIFFICULTY_LEVELS.items():
            self._data["task_difficulty"][lvl] = info

        self.save()

    # ── Query ────────────────────────────────────────────────

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return sorted(self._data.get("agents", {}).keys())

    def list_skills(self, category: str = "") -> list[dict]:
        """List all skill definitions, optionally filtered by category."""
        skills = self._data.get("skills", {})
        result = []
        for sname, sdef in sorted(skills.items()):
            if category and sdef.get("category", "") != category:
                continue
            result.append({
                "name": sname,
                "category": sdef.get("category", ""),
                "description": sdef.get("description", ""),
                "levels": sdef.get("levels", {}),
            })
        return result

    def get_agent_skills(self, agent_name: str) -> list[dict]:
        """Get all skill levels for an agent."""
        agent = self._data.get("agents", {}).get(agent_name)
        if not agent:
            return []
        skills = agent.get("skills", {})
        catalog = self._data.get("skills", {})
        result = []
        for sname, sinfo in sorted(skills.items()):
            level_desc = ""
            cat_entry = catalog.get(sname, {})
            levels = cat_entry.get("levels", {})
            level_data = levels.get(sinfo.get("level", ""), {})
            level_desc = level_data.get("description", "") if isinstance(level_data, dict) else ""
            result.append({
                "skill_name": sname,
                "level": sinfo.get("level", "L0"),
                "confidence": sinfo.get("confidence", 0),
                "level_description": level_desc,
                "evidence_count": len(sinfo.get("evidence", [])),
            })
        return result

    def get_skill_level(self, agent_name: str, skill_name: str) -> Optional[str]:
        """Get an agent's level for a specific skill."""
        agent = self._data.get("agents", {}).get(agent_name)
        if not agent:
            return None
        sinfo = agent.get("skills", {}).get(skill_name)
        return sinfo.get("level") if sinfo else None

    def get_agent_details(self, agent_name: str) -> Optional[dict]:
        """Get full agent record including evidence chains."""
        agent = self._data.get("agents", {}).get(agent_name)
        if not agent:
            return None
        return {
            "agent_name": agent_name,
            "skill_count": len(agent.get("skills", {})),
            "skills": agent.get("skills", {}),
        }

    # ── Assessment ──────────────────────────────────────────

    def assess_skill(self, agent_name: str, skill_name: str,
                     new_level: str, assessed_by: str = "skill-evaluator",
                     confidence: float = 0.7,
                     evidence: list[dict] = None) -> dict:
        """Assess/update an agent's skill level.

        Args:
            agent_name: Agent profile name.
            skill_name: Skill name from catalog.
            new_level: L0-L5 level.
            assessed_by: Who assessed (default: skill-evaluator).
            confidence: 0.0-1.0 confidence in assessment.
            evidence: Optional list of evidence dicts.

        Returns:
            Dict with old/new level and outcome.
        """
        agents = self._data.setdefault("agents", {})
        if agent_name not in agents:
            agents[agent_name] = {"agent_name": agent_name, "skills": {}}
        agent = agents[agent_name]
        skills = agent.setdefault("skills", {})

        old_level = skills.get(skill_name, {}).get("level", "L0")

        entry = {
            "level": new_level,
            "confidence": round(confidence, 2),
            "assessed_by": assessed_by,
            "assessed_at": time.strftime("%Y-%m-%d"),
            "evidence": evidence or skills.get(skill_name, {}).get("evidence", []),
        }
        skills[skill_name] = entry
        self.save()

        return {
            "agent": agent_name,
            "skill": skill_name,
            "old_level": old_level,
            "new_level": new_level,
            "assessed_by": assessed_by,
            "confidence": confidence,
            "evidence_count": len(entry["evidence"]),
        }

    def add_evidence(self, agent_name: str, skill_name: str,
                     evidence: dict) -> dict:
        """Add evidence for an agent's skill demonstration.

        Args:
            agent_name: Agent profile name.
            skill_name: Skill name.
            evidence: Dict with type, ref, description, date.

        Returns:
            Updated skill entry.
        """
        agents = self._data.setdefault("agents", {})
        agent = agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")
        skills = agent.setdefault("skills", {})
        sinfo = skills.get(skill_name)
        if not sinfo:
            raise ValueError(f"Skill '{skill_name}' not registered for '{agent_name}'")

        sinfo.setdefault("evidence", []).append(evidence)
        # Auto-adjust confidence upward slightly with new evidence
        sinfo["confidence"] = round(min(1.0, sinfo.get("confidence", 0.5) + 0.05), 2)
        self.save()

        return sinfo

    # ── Task Matching ────────────────────────────────────────

    def match_task(self, description: str, required_skills: list[str] = None,
                   difficulty: str = "L2") -> list[MatchResult]:
        """Find best agents for a task based on required skills.

        Args:
            description: Task description (for NLP-based skill inference).
            required_skills: Optional explicit skill requirements.
            difficulty: Required minimum difficulty level.

        Returns:
            List of MatchResult sorted by match_score descending.
        """
        # Infer skills from description if not provided
        if not required_skills:
            required_skills = self._infer_skills(description)

        if not required_skills:
            return []

        req_idx = LEVELS.index(difficulty) if difficulty in LEVELS else 2

        results = []
        for agent_name in self.list_agents():
            matched = []
            missing = []
            agent_skills = self._data["agents"][agent_name].get("skills", {})

            for rs in required_skills:
                entry = agent_skills.get(rs)
                if entry:
                    agent_lvl = entry.get("level", "L0")
                    agent_idx = LEVELS.index(agent_lvl) if agent_lvl in LEVELS else 0
                    if agent_idx >= req_idx:
                        matched.append(rs)
                    else:
                        missing.append(f"{rs}(at {agent_lvl}, need ≥{difficulty})")
                else:
                    missing.append(f"{rs}(unregistered)")

            if not matched and not missing:
                continue

            # Calculate match score
            total_skills = len(required_skills)
            if total_skills == 0:
                match_score = 0.0
            else:
                match_score = round(len(matched) / total_skills, 2)

            results.append(MatchResult(
                agent_name=agent_name,
                match_score=match_score,
                matched_skills=matched,
                missing_skills=missing,
                details=f"{len(matched)}/{total_skills} skills matched at ≥{difficulty}",
            ))

        results.sort(key=lambda r: r.match_score, reverse=True)
        return results

    def _infer_skills(self, description: str) -> list[str]:
        """Infer required skills from task description text."""
        desc_lower = description.lower()
        inferred = []

        # Direct skill name matches
        for sname in self._data.get("skills", {}):
            sdef = self._data["skills"][sname]
            name_lower = sname.replace("-", " ").lower()
            skill_keywords = [
                name_lower,
                sdef.get("name", "").lower(),
            ]
            for kw in skill_keywords:
                if kw and kw in desc_lower:
                    if sname not in inferred:
                        inferred.append(sname)
                    break

        # Category-based matching
        category_keywords = {
            "frontend": ["frontend", "ui", "react", "vue", "css", "html", "component", "design", "web"],
            "backend": ["api", "backend", "server", "database", "sql", "endpoint", "service", "rest"],
            "devops": ["deploy", "ci", "cd", "docker", "kubernetes", "infrastructure", "monitoring"],
            "product": ["prd", "roadmap", "user story", "product", "okr", "feature"],
            "ai-ml": ["machine learning", "deep learning", "model", "train", "inference", "ml", "ai"],
            "content": ["content", "seo", "copy", "writing", "blog", "social media", "article"],
            "data": ["etl", "data", "pipeline", "warehouse", "analytics", "dashboard", "sql"],
            "growth": ["growth", "acquisition", "conversion", "aarrr", "funnel", "retention"],
            "research": ["research", "paper", "literature", "experiment", "hypothesis"],
        }

        for cat, kws in category_keywords.items():
            if any(kw in desc_lower for kw in kws):
                for sname, sdef in self._data.get("skills", {}).items():
                    if sdef.get("category", "") == cat and sname not in inferred:
                        inferred.append(sname)
                break  # Only add once per matched category

        return inferred[:8]  # Cap at 8 skills


# ════════════════════════════════════════════════════════════════
# SKILL.md Generation (Hermes Profile)
# ════════════════════════════════════════════════════════════════


def generate_skill_md(agent_name: str, registry: SkillRegistry = None) -> str:
    """Generate a Hermes-compatible SKILL.md for an agent profile.

    Follows SKILL.md standard (frontmatter + body) with agent's registered
    skills, levels, evidence, and associated Hermes skills/resources.

    Returns:
        SKILL.md content as a string.
    """
    if registry is None:
        registry = get_registry()

    agent = registry._data.get("agents", {}).get(agent_name)
    if not agent:
        return ""

    skills = agent.get("skills", {})
    catalog = registry._data.get("skills", {})

    # Build frontmatter
    role_name = agent_name.replace("-", " ").title()
    desc_parts = []
    tags = []
    for sname, sinfo in skills.items():
        cat_entry = catalog.get(sname, {})
        cat = cat_entry.get("category", "general") if isinstance(cat_entry, dict) else "general"
        if cat not in tags:
            tags.append(cat)
        lvl = sinfo.get("level", "L0")
        conf = sinfo.get("confidence", 0.5)
        desc_parts.append(f"- {sname}: **{lvl}** (confidence: {conf:.0%})")

    tag_str = ", ".join(tags[:6])

    lines = [
        "---",
        f"name: {agent_name}-skills",
        f"description: \"Skill profile for {role_name}. Registered {len(skills)} skills.\"",
        "version: 1.0.0",
        "author: Apex Skill Registry",
        "license: MIT",
        "metadata:",
        "  hermes:",
        f"    tags: [{tag_str}]",
        "    related_skills: []",
        "---",
        "",
        f"# 🎯 {role_name} — Skill Profile",
        "",
        f"Skill registry for agent `{agent_name}`. ",
        f"Total skills registered: **{len(skills)}**.",
        "",
        "## Skill Level Legend",
        "",
        "| Level | Title | Meaning |",
        "|-------|-------|---------|",
        "| L0 | Novice (新手) | 不了解，需要指导 |",
        "| L1 | Apprentice (学徒) | 能简单完成，需监督 |",
        "| L2 | Practitioner (独立执行) | 能独立完成标准任务 |",
        "| L3 | Proficient (精通) | 能优化和教学 |",
        "| L4 | Expert (专家) | 领域专家，架构决策 |",
        "| L5 | Legend (传奇) | 开创性，创建工具/框架 |",
        "",
        "## Registered Skills",
        "",
    ]

    # Sort skills by category then level descending
    skill_list = []
    for sname, sinfo in skills.items():
        cat_entry = catalog.get(sname, {})
        cat = cat_entry.get("category", "general") if isinstance(cat_entry, dict) else "general"
        lvl = sinfo.get("level", "L0")
        skill_list.append((cat, -LEVELS.index(lvl) if lvl in LEVELS else 0, sname, sinfo, cat_entry))
    skill_list.sort()

    current_cat = ""
    for cat, _, sname, sinfo, cat_entry in skill_list:
        if cat != current_cat:
            emoji_map = {"frontend": "💻", "backend": "⚙️", "devops": "🔧", "product": "📋",
                         "ai-ml": "🧠", "content": "✍️", "data": "🗄️", "growth": "📈",
                         "research": "🔬", "technical": "📚", "general": "🛠️"}
            lines.append(f"### {emoji_map.get(cat, '📁')} {cat.upper()}")
            lines.append("")
            current_cat = cat

        lvl = sinfo.get("level", "L0")
        conf = sinfo.get("confidence", 0.5)
        conf_bar = "█" * int(conf * 10) + "░" * (10 - int(conf * 10))
        ev_count = len(sinfo.get("evidence", []))

        # Skill description
        skill_desc = ""
        if isinstance(cat_entry, dict):
            levels = cat_entry.get("levels", {})
            lvl_data = levels.get(lvl, {})
            if isinstance(lvl_data, dict):
                skill_desc = lvl_data.get("description", "")

        lines.append(f"**{sname}** — `{lvl}` {LEVEL_LABELS.get(lvl, '')}")
        lines.append(f"  - Confidence: [{conf_bar}] {conf:.0%}")
        if skill_desc:
            lines.append(f"  - Level description: {skill_desc}")
        if ev_count:
            lines.append(f"  - Evidence: {ev_count} items")
            # Show latest evidence
            ev_list = sinfo.get("evidence", [])
            for ev in ev_list[-2:]:
                ev_ref = ev.get("ref", "")
                ev_desc = ev.get("description", "")[:60]
                if ev_ref:
                    lines.append(f"    - [{ev_ref}] {ev_desc}")
        lines.append("")

    # Assessment history summary
    lines.append("## Assessment History")
    lines.append("")

    assessed_entries = []
    for sname, sinfo in skills.items():
        assessed_by = sinfo.get("assessed_by", "auto")
        assessed_at = sinfo.get("assessed_at", "")
        if assessed_at:
            assessed_entries.append((assessed_at, sname, sinfo.get("level", "?"), assessed_by))
    assessed_entries.sort(reverse=True)

    if assessed_entries:
        for date, sname, lvl, by in assessed_entries[:10]:
            lines.append(f"- {date} | `{sname}` → {lvl} | by _{by}_")
    else:
        lines.append("_No assessments recorded yet._")
    lines.append("")

    lines.append("## Related Hermes Skills")
    lines.append("")
    related = []
    for sname in skills:
        # Map skill names to potential hermes skill names
        hs_name = sname
        if hs_name not in related:
            related.append(hs_name)
    for r in sorted(related)[:10]:
        lines.append(f"- `{r}`")
    if len(related) > 10:
        lines.append(f"- ... and {len(related) - 10} more")
    lines.append("")
    lines.append("---")
    lines.append(f"_Generated by Apex Skill Registry on {time.strftime('%Y-%m-%d %H:%M')}_")
    lines.append("")

    return "\n".join(lines)


def sync_skill_md(agent_name: str, hermes_profiles_dir: Path = None,
                  registry: SkillRegistry = None) -> dict:
    """Generate and write SKILL.md for an agent's Hermes profile.

    Args:
        agent_name: Agent profile name.
        hermes_profiles_dir: Hermes profiles directory (default: ~/.hermes/profiles/).
        registry: SkillRegistry instance.

    Returns:
        Dict with path and status.
    """
    if registry is None:
        registry = get_registry()
    if hermes_profiles_dir is None:
        hermes_profiles_dir = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")) / "profiles"

    # Generate SKILL.md content
    content = generate_skill_md(agent_name, registry)
    if not content:
        return {"agent": agent_name, "status": "skipped", "reason": "No skills registered"}

    # Write to Hermes profile dir
    profile_dir = hermes_profiles_dir / agent_name
    skill_file = profile_dir / "SKILL.md"

    if not profile_dir.exists():
        # Check if Apex profile exists instead
        from agentark.core.profile import ProfileManager
        pm = ProfileManager()
        try:
            pm.load(agent_name)
            # Create Hermes profile directory
            profile_dir.mkdir(parents=True, exist_ok=True)
        except FileNotFoundError:
            return {"agent": agent_name, "status": "error", "reason": f"Profile '{agent_name}' not found"}

    profile_dir.mkdir(parents=True, exist_ok=True)
    with open(skill_file, "w") as f:
        f.write(content)

    return {
        "agent": agent_name,
        "status": "synced",
        "path": str(skill_file),
        "size_bytes": len(content),
        "skills_count": len(registry.get_agent_skills(agent_name)),
    }


def sync_all_skill_md(hermes_profiles_dir: Path = None,
                      registry: SkillRegistry = None) -> list[dict]:
    """Generate SKILL.md for all registered agents.

    Returns:
        List of sync results.
    """
    if registry is None:
        registry = get_registry()

    results = []
    for agent_name in registry.list_agents():
        try:
            result = sync_skill_md(agent_name, hermes_profiles_dir, registry)
            results.append(result)
        except Exception as e:
            results.append({"agent": agent_name, "status": "error", "reason": str(e)})
    return results


# ════════════════════════════════════════════════════════════════
# Convenience
# ════════════════════════════════════════════════════════════════

_registry_instance: Optional[SkillRegistry] = None


def get_registry() -> SkillRegistry:
    """Get singleton SkillRegistry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = SkillRegistry()
        _registry_instance.load()
    return _registry_instance
