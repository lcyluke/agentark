"""
智能消息路由器 v2 — 项目识别 → Agent匹配 → 结构化输出
═══════════════════════════════════════════════════════════════

每条用户消息经过三层分析:
  1. 项目识别  — 属于哪个项目? (羽球宝AI / Apex / 深圳羽球地图 / 通用)
  2. 类别分类  — 什么问题类型? (开发/架构/PM/运维/内容/商业/安全)
  3. Agent映射 — 匹配哪个Hermes Profile执行?

输出格式: [项目名] [Agent角色·emoji] [问题类别] → 分析/回复

集成点:
  - Apex web.py: /api/router/analyze  /api/router/dispatch  /api/router/matrix
  - Hermes skill: apex-message-router
  - notification_dispatcher: 复用结构化格式
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

APEX_HOME = Path(os.environ.get("APEX_HOME", Path.home() / ".apex"))
HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))


# ════════════════════════════════════════════════════════════
# 项目定义
# ════════════════════════════════════════════════════════════

@dataclass
class Project:
    key: str
    name: str
    emoji: str
    path: str
    keywords: list[str]           # 触发关键词
    profiles: list[str]           # 关联的 Hermes Profiles
    categories: list[str] = field(default_factory=list)  # 该项目常见问题类别

PROJECTS: dict[str, Project] = {
    "badminton-coach-ai": Project(
        key="badminton-coach-ai",
        name="羽球宝AI搭子",
        emoji="🏸",
        path="~/Desktop/2026AIAPP/workspace/badminton-coach-ai",
        keywords=[
            "羽球宝", "羽球", "羽毛球", "badminton", "小程序", "评估", "训练",
            "动作", "标注", "姿势", "骨骼", "双打", "付费", "订阅", "课程",
            "教练", "场馆", "预约", "伤病", "按摩", "换脸", "mimic",
            "sprint", "kanban 羽球", "P0", "UAT", "labeling", "pose",
            "rtmpose", "st-gcn", "gbdt", "dtw", "videomae",
            "球友匹配", "matching", "coach", "injury",
        ],
        profiles=["yuji-pm", "architect", "ai-algorithm", "ai-vision",
                   "frontend-dev", "content-marketing"],
        categories=["development", "architecture", "pm", "testing", "content", "biz"],
    ),
    "apex": Project(
        key="apex",
        name="Apex Dashboard",
        emoji="🦅",
        path="~/Desktop/2026AIAPP/Apex",
        keywords=[
            "apex", "dashboard", "origin agent", "始祖", "fleet", "舰队",
            "bridge", "router", "profile manager", "kanban", "swarm",
            "evolution", "knowledge graph", "economy", "budget",
            "hermes bridge", "openclaw", "多agent", "multi-agent",
            "cron", "notification", "通知系统", "角色矩阵",
            "授权引擎", "授权请求", "授权码", "authorization",
            "audit chain", "审计链", "哈希链", "特权操作",
            "scope", "grants", "autodl:ssh", "autodl:api",
            "委派", "delegation", "双重审批", "origin pre-approve",
            "审计分身", "audit guardian",
        ],
        profiles=["default", "ops-engineer", "security-compliance", "apex-pm"],
        categories=["development", "architecture", "devops", "pm", "auth"],
    ),
    "shenzhen-badminton": Project(
        key="shenzhen-badminton",
        name="深圳羽球地图",
        emoji="🗺️",
        path="~/Desktop/2026AIAPP/shenzhen-badminton",
        keywords=[
            "深圳", "地图", "ball map", "326", "场馆", "打卡", "venue",
            "notion 场馆", "content 深圳", "marketing 深圳",
        ],
        profiles=["content-marketing", "fundraising-pitch"],
        categories=["content", "biz"],
    ),
}


# ════════════════════════════════════════════════════════════
# 类别定义 (关键字 + 对应 Profile)
# ════════════════════════════════════════════════════════════

# NOTE: All patterns use simple substring matching (no \\b) to support Chinese.
# False positives are minimal since we score by match count / message length.

CATEGORY_PATTERNS: list[tuple[str, str, list[str]]] = [
    # (category, agent_profile, keywords)
    ("pm", "yuji-pm", [
        "sprint", "kanban", "任务看板", "PRD", "需求",
        "路线图", "roadmap", "里程碑", "milestone",
        "迭代", "iteration", "优先级", "priority",
        "排期", "进度", "progress", "燃尽", "burndown",
        "发布", "release", "UAT", "验收",
        "commit", "git push", "tag",
    ]),
    ("development", "architect", [
        "代码", "code", "开发", "实现", "implement",
        "feature", "fix", "bug", "修复",
        "api", "端点", "endpoint", "接口",
        "webapp", "后端", "backend", "前端", "frontend",
        "小程序页面", "component", "wxml", "wxss",
        "测试", "test", "单元测试",
    ]),
    ("architecture", "architect", [
        "架构", "设计", "design", "数据库", "database",
        "schema", "数据模型", "扩展", "scal",
        "重构", "refactor", "技术选型",
        "sqlite", "postgres", "migration",
    ]),
    ("ai-ml", "ai-algorithm", [
        "模型", "model", "训练", "train", "fine.tun",
        "推理", "inference", "gpu", "autodl",
        "标注", "label", "数据集", "dataset",
        "mediapipe", "yolo", "clip", "rtmpose",
        "st-gcn", "gbdt", "准确率", "accuracy",
        "特征", "feature", "骨骼", "pose",
        "换脸", "mimic", "mimicmotion",
        "videomae", "dtw", "gat", "tcn",
    ]),
    ("vision", "ai-vision", [
        "视频", "video", "图像", "image", "照片",
        "图像识别", "物体检测", "detect", "跟踪", "track",
        "opencv", "截图", "screenshot",
        "动作分析", "姿态", "landmark",
        "摄像头", "camera", "录像",
    ]),
    ("frontend", "frontend-dev", [
        "UI", "界面", "样式", "css", "wxss",
        "交互", "animation", "动画", "图标",
        "icon", "组件", "小程序前端",
        "页面", "page", "分享", "share",
    ]),
    ("devops", "ops-engineer", [
        "部署", "deploy", "服务器", "server",
        "docker", "nginx", "ssh", "隧道",
        "tunnel", "监控", "monitor", "告警",
        "备份", "backup", "日志", "log",
        "环境", "env", "配置", "config",
        "端口", "port", "重启", "restart",
        "进程", "process", "daemon",
        "断连", "断开", "连接", "connection",
        "在线", "健康", "health",
    ]),
    ("security", "security-compliance", [
        "安全", "security", "密码", "password",
        "密钥", "key", "加密", "encrypt",
        "权限", "permission", "合规", "compliance",
        "隐私", "privacy", "gdpr", "漏洞",
        "授权", "auth", "token",
    ]),
    ("auth", "apex-pm", [
        "授权请求", "授权码", "request_code", "授权引擎",
        "特权操作", "审批", "approve", "拒绝", "deny",
        "consume", "revoke", "吊销", "授权记录", "审计链",
        "哈希链", "verify", "grants", "scope",
        "autodl:ssh", "autodl:api", "cloud:aws", "deploy:production",
    ]),
    ("content", "content-marketing", [
        "内容", "content", "文章", "article",
        "公众号", "小红书", "品牌", "brand",
        "文案", "copy", "推广", "marketing",
        "用户增长", "growth", "裂变",
        "朋友圈", "社群", "社区",
    ]),
    ("biz", "fundraising-pitch", [
        "商业", "business", "融资", "fund",
        "BP", "路演", "pitch", "估值",
        "营收", "revenue", "盈利", "profit",
        "商业模式", "转化", "conversion",
        "付费", "payment", "pricing",
        "竞品", "competitor",
    ]),
]


# ════════════════════════════════════════════════════════════
# 结构化输出格式
# ════════════════════════════════════════════════════════════

OUTPUT_TEMPLATE = """[📦 {project_emoji} {project_name}] [{agent_emoji} {agent_role}] [{category_emoji} {category_name}] {separator}
{content}"""

CATEGORY_EMOJI = {
    "pm": "📋", "development": "💻", "architecture": "🏗️",
    "ai-ml": "🧠", "vision": "👁️", "frontend": "🎨",
    "devops": "🔧", "security": "🔒", "content": "✍️",
    "biz": "💰", "general": "📌",
    "auth": "🏛️",
}

AGENT_EMOJI = {
    "yuji-pm": "🎯", "architect": "🏛️", "ai-algorithm": "🧠",
    "ai-vision": "👁️", "frontend-dev": "🎨", "ops-engineer": "🔧",
    "content-marketing": "✍️", "fundraising-pitch": "💰",
    "security-compliance": "🔒", "default": "⚓",
    "apex-pm": "🦅",
}

AGENT_ROLE = {
    "yuji-pm": "PM·羽迹",
    "architect": "架构师",
    "ai-algorithm": "算法专家",
    "ai-vision": "视觉专家",
    "frontend-dev": "前端开发",
    "ops-engineer": "运维工程师",
    "content-marketing": "内容推广",
    "fundraising-pitch": "融资路演",
    "security-compliance": "安全合规",
    "apex-pm": "🦅 Apex总管",
    "default": "始祖·总指挥",
}


# ════════════════════════════════════════════════════════════
# 路由器
# ════════════════════════════════════════════════════════════

@dataclass
class RouteResult:
    """路由分析结果"""
    project: str          # project key
    project_name: str     # 中文名
    project_emoji: str
    category: str         # category key
    category_name: str    # 中文类名
    agent_profile: str    # Hermes profile 名
    agent_role: str       # 角色中文名
    agent_emoji: str
    confidence: float     # 0-1
    keywords_matched: list[str] = field(default_factory=list)
    reasoning: str = ""

    def format_output(self, content: str, separator: str = "\n") -> str:
        """按标准格式输出"""
        return OUTPUT_TEMPLATE.format(
            project_emoji=self.project_emoji,
            project_name=self.project_name,
            agent_emoji=self.agent_emoji,
            agent_role=self.agent_role,
            category_emoji=CATEGORY_EMOJI.get(self.category, "📌"),
            category_name=self.category_name,
            separator=separator,
            content=content,
        )


class MessageRouter:
    """智能消息路由器

    用法:
        router = MessageRouter()
        result = router.analyze("羽球宝的小程序训练页接真实API")
        print(result.format_output("我来处理这个需求..."))
    """

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译关键词正则 (去掉 \\b 以支持中文)"""
        # 项目关键词
        self._project_patterns = {}
        for key, proj in PROJECTS.items():
            self._project_patterns[key] = re.compile(
                "|".join(proj.keywords), re.IGNORECASE
            )

        # 类别关键词
        self._category_patterns: list[tuple[str, str, re.Pattern]] = []
        for cat, profile, keywords in CATEGORY_PATTERNS:
            self._category_patterns.append(
                (cat, profile, re.compile("|".join(keywords), re.IGNORECASE))
            )

    # ── 分析 ─────────────────────────────────────────────

    def analyze(self, message: str, prefer_project: str = "") -> RouteResult:
        """分析一条消息，返回路由结果

        Args:
            message: 用户消息内容
            prefer_project: 偏好的项目key（当前会话上下文）
        """
        matched_keywords: list[str] = []

        # Step 1: 项目识别
        project_scores: dict[str, float] = {}
        for key, pattern in self._project_patterns.items():
            matches = pattern.findall(message)
            if matches:
                project_scores[key] = len(matches) / max(1, len(message.split()) * 0.1)
                matched_keywords.extend(matches)

        # 确定项目
        if project_scores:
            best_project = max(project_scores, key=lambda k: project_scores[k])
            confidence_base = min(project_scores[best_project], 1.0)
        elif prefer_project and prefer_project in PROJECTS:
            best_project = prefer_project
            confidence_base = 0.3
        else:
            best_project = "badminton-coach-ai"  # 默认羽球宝
            confidence_base = 0.1

        project = PROJECTS[best_project]

        # Step 2: 类别分类
        cat_scores: dict[str, tuple[str, float, str]] = {}
        # (category, agent_profile, score, match_str)
        for cat, profile, pattern in self._category_patterns:
            matches = pattern.findall(message)
            if matches:
                score = len(matches) / max(1, len(message.split()) * 0.08)
                cat_scores[cat] = (profile, score, matches[0])

        if cat_scores:
            best_cat = max(cat_scores, key=lambda k: cat_scores[k][1])
            category = best_cat
            agent_profile = cat_scores[best_cat][0]
        else:
            # 降级：用项目默认profile
            category = "general"
            agent_profile = project.profiles[0] if project.profiles else "default"

        # Step 3: 角色名和emoji
        agent_role = AGENT_ROLE.get(agent_profile, agent_profile)
        agent_emoji = AGENT_EMOJI.get(agent_profile, "🤖")

        # 类别中文名
        cat_names = {
            "pm": "项目管理", "development": "功能开发", "architecture": "架构设计",
            "ai-ml": "AI/ML", "vision": "视觉识别", "frontend": "前端开发",
            "devops": "运维部署", "security": "安全合规", "content": "内容推广",
            "biz": "商业分析", "general": "综合分析",
            "auth": "授权管理",
        }

        return RouteResult(
            project=best_project,
            project_name=project.name,
            project_emoji=project.emoji,
            category=category,
            category_name=cat_names.get(category, category),
            agent_profile=agent_profile,
            agent_role=agent_role,
            agent_emoji=agent_emoji,
            confidence=min(confidence_base + 0.2, 1.0),
            keywords_matched=matched_keywords[:15],
            reasoning=f"{project.name} × {cat_names.get(category, category)} → {agent_role}",
        )

    # ── 矩阵 ─────────────────────────────────────────────

    def get_matrix(self) -> dict:
        """返回完整的项目-类别-角色映射矩阵"""
        projects = []
        for key, proj in PROJECTS.items():
            categories = []
            for cat, profile, _ in CATEGORY_PATTERNS:
                if cat in proj.categories:
                    categories.append({
                        "category": cat,
                        "name": {
                            "pm": "项目管理", "development": "功能开发",
                            "architecture": "架构设计", "ai-ml": "AI/ML",
                            "vision": "视觉识别", "frontend": "前端开发",
                            "devops": "运维部署", "security": "安全合规",
                            "content": "内容推广", "biz": "商业分析",
                            "auth": "授权管理",
                        }.get(cat, cat),
                        "agent_profile": profile,
                        "agent_role": AGENT_ROLE.get(profile, profile),
                        "agent_emoji": AGENT_EMOJI.get(profile, "🤖"),
                    })
            projects.append({
                "key": key,
                "name": proj.name,
                "emoji": proj.emoji,
                "profiles": proj.profiles,
                "categories": categories,
            })

        return {
            "projects": projects,
            "profiles": [
                {"name": name, "role": AGENT_ROLE.get(name, name),
                 "emoji": AGENT_EMOJI.get(name, "🤖")}
                for name in AGENT_ROLE
            ],
        }

    # ── 快捷分析 ─────────────────────────────────────────

    def quick(self, message: str) -> str:
        """一行分析：返回 reasoning 字符串"""
        r = self.analyze(message)
        return f"[{r.project_emoji} {r.project_name}] [{r.agent_emoji} {r.agent_role}] [{r.category}] — {r.confidence:.0%}"


# ════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════

def main():
    import sys

    router = MessageRouter()

    if len(sys.argv) < 2:
        print("用法: message_router.py <消息>")
        print("      message_router.py matrix   # 打印矩阵")
        print("      message_router.py quick <消息>")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "matrix":
        print(json.dumps(router.get_matrix(), ensure_ascii=False, indent=2))
        return

    if cmd == "quick":
        msg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        if msg:
            print(router.quick(msg))
        else:
            print("需要提供消息")
        return

    # analyze mode
    msg = " ".join(sys.argv[1:])
    result = router.analyze(msg)
    print(json.dumps({
        "project": result.project,
        "project_name": result.project_name,
        "project_emoji": result.project_emoji,
        "category": result.category,
        "category_name": result.category_name,
        "agent_profile": result.agent_profile,
        "agent_role": result.agent_role,
        "agent_emoji": result.agent_emoji,
        "confidence": result.confidence,
        "keywords_matched": result.keywords_matched,
        "reasoning": result.reasoning,
        "formatted": result.format_output("→ 待执行"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
