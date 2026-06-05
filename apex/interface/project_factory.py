"""Apex Intelligent Project Factory — 模块库 + SKILL进化 + Pipeline

= Module Library: standardized reusable modules by project type
= SKILL Evolution: agent skill levels earned through project completion  
= Pipeline: dev→test→verify→deploy→evaluate automated workflow
"""
from __future__ import annotations

import json
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from collections import defaultdict


APEX_HOME = Path(os.path.expanduser("~/.apex"))
MODULES_FILE = APEX_HOME / "module_library.json"
SKILLS_FILE = APEX_HOME / "skill_evolution.json"


# ══════════════════════════════════════════
# STANDARDIZED MODULE LIBRARY
# ══════════════════════════════════════════

MODULE_CATEGORIES = {
    "miniprogram": {
        "name": "微信小程序",
        "icon": "ti-brand-wechat",
        "templates": [
            {
                "id": "mp-auth", "name": "登录认证模块",
                "description": "微信授权登录+手机号绑定+JWT Token管理",
                "files": ["pages/login/", "utils/auth.js", "api/user.js"],
                "agents": ["frontend-dev", "羽球宝AI_frontend"],
                "complexity": 2, "reuse_count": 12,
                "code_example": "wx.login() → getOpenId() → JWT → storage",
            },
            {
                "id": "mp-payment", "name": "微信支付模块",
                "description": "统一下单+支付回调+Mock支付+订阅管理",
                "files": ["pages/payment/", "utils/pay.js", "api/payment.js"],
                "agents": ["frontend-dev", "羽球宝AI_frontend", "羽球宝AI_backend"],
                "complexity": 4, "reuse_count": 8,
                "code_example": "wx.requestPayment({timeStamp,nonceStr,package,signType,paySign})",
            },
            {
                "id": "mp-mediapipe", "name": "MediaPipe骨架追踪",
                "description": "实时摄像头+MediaPipe WASM+33关键点+姿势分类",
                "files": ["pages/assess/", "utils/mediapipe.js", "components/pose-canvas/"],
                "agents": ["ai-vision", "frontend-dev"],
                "complexity": 5, "reuse_count": 3,
                "code_example": "PoseLandmarker.createFromOptions() → detectForVideo()",
            },
            {
                "id": "mp-tabbar", "name": "底部导航模板",
                "description": "标准5Tab导航(首页/评估/训练/我的)+图标切换",
                "files": ["app.json(tabBar)", "images/tabbar/", "custom-tab-bar/"],
                "agents": ["frontend-dev"],
                "complexity": 1, "reuse_count": 20,
            },
        ],
    },
    "saas": {
        "name": "SAAS系统",
        "icon": "ti-cloud-computing",
        "templates": [
            {
                "id": "saas-auth", "name": "RBAC+SSO认证",
                "description": "角色权限控制+单点登录+OAuth2.0+多租户",
                "files": ["auth/", "middleware/rbac.py", "models/permission.py"],
                "agents": ["architect", "羽球宝AI_backend"],
                "complexity": 5, "reuse_count": 6,
                "code_example": "FastAPI + OAuth2PasswordBearer + RoleChecker",
            },
            {
                "id": "saas-api-gw", "name": "API网关+限流",
                "description": "统一入口+Rate Limit+负载均衡+请求日志",
                "files": ["gateway/nginx.conf", "middleware/ratelimit.py", "api/proxy.py"],
                "agents": ["devops", "ops-engineer"],
                "complexity": 4, "reuse_count": 5,
            },
            {
                "id": "saas-audit", "name": "审计日志系统",
                "description": "全操作审计+敏感数据脱敏+合规报告+保留策略",
                "files": ["audit/logger.py", "models/audit_log.py", "api/audit.py"],
                "agents": ["security-compliance", "羽球宝AI_backend"],
                "complexity": 3, "reuse_count": 4,
            },
            {
                "id": "saas-deploy", "name": "K8S+Serverless部署",
                "description": "容器化+K8S编排+Serverless函数+自动扩缩",
                "files": ["k8s/", "Dockerfile", "serverless.yml", "terraform/"],
                "agents": ["devops", "ops-engineer"],
                "complexity": 5, "reuse_count": 3,
            },
        ],
    },
    "android": {
        "name": "Android App",
        "icon": "ti-brand-android",
        "templates": [
            {
                "id": "android-ux", "name": "Material Design UX模板",
                "description": "底部导航+Drawer+AppBar+暗色主题+FAB",
                "files": ["res/layout/", "ui/theme/", "navigation/"],
                "agents": ["frontend-dev"],
                "complexity": 2, "reuse_count": 10,
            },
            {
                "id": "android-camera", "name": "相机+视频录制",
                "description": "CameraX+实时预览+录制+帧提取+上传",
                "files": ["camera/", "video/", "upload/"],
                "agents": ["ai-vision", "frontend-dev"],
                "complexity": 4, "reuse_count": 3,
            },
        ],
    },
    "ai-chat": {
        "name": "AI Chat Web UI",
        "icon": "ti-messages",
        "templates": [
            {
                "id": "chat-ui", "name": "ChatGPT风格UI",
                "description": "消息列表+流式输出+Markdown渲染+附件上传+历史搜索",
                "files": ["components/Chat/", "hooks/useChat.ts", "api/chat.ts"],
                "agents": ["frontend-dev"],
                "complexity": 3, "reuse_count": 15,
                "code_example": "SSE stream → React state → Markdown render",
            },
            {
                "id": "chat-iam", "name": "IAM身份管理",
                "description": "OpenID Connect+Keycloak+多因素认证+会话管理",
                "files": ["auth/oidc.py", "middleware/session.py", "models/identity.py"],
                "agents": ["security-compliance", "architect"],
                "complexity": 5, "reuse_count": 4,
            },
        ],
    },
    "backend": {
        "name": "后端通用模块",
        "icon": "ti-server",
        "templates": [
            {
                "id": "be-fastapi", "name": "FastAPI项目骨架",
                "description": "路由+中间件+依赖注入+OpenAPI文档+异常处理",
                "files": ["main.py", "api/v1/", "core/config.py", "models/", "schemas/"],
                "agents": ["羽球宝AI_backend", "architect"],
                "complexity": 2, "reuse_count": 25,
            },
            {
                "id": "be-db", "name": "数据库迁移+种子",
                "description": "Alembic迁移+SQLAlchemy模型+种子数据+连接池",
                "files": ["alembic/", "models/base.py", "db/session.py", "seeds/"],
                "agents": ["architect", "羽球宝AI_backend"],
                "complexity": 3, "reuse_count": 18,
            },
            {
                "id": "be-taskq", "name": "异步任务队列",
                "description": "Celery/Redis+定时任务+重试机制+进度追踪",
                "files": ["tasks/", "celery_app.py", "scheduler.py"],
                "agents": ["devops", "羽球宝AI_backend"],
                "complexity": 4, "reuse_count": 7,
            },
        ],
    },
}


def get_module_library(category: str = None) -> dict:
    """Get the module library, optionally filtered by category"""
    lib = MODULE_CATEGORIES
    if category and category in lib:
        return {"category": category, **lib[category], "total_templates": len(lib[category]["templates"])}

    # Summary
    total = sum(len(cat["templates"]) for cat in lib.values())
    return {
        "categories": [
            {"id": cid, "name": cat["name"], "icon": cat["icon"], "template_count": len(cat["templates"])}
            for cid, cat in lib.items()
        ],
        "total_templates": total,
        "total_categories": len(lib),
    }


def get_module_templates(category: str) -> list:
    """Get all templates in a category"""
    cat = MODULE_CATEGORIES.get(category)
    if not cat:
        return []
    return cat["templates"]


def search_modules(query: str) -> list:
    """Search across all module templates"""
    results = []
    q = query.lower()
    for cid, cat in MODULE_CATEGORIES.items():
        for t in cat["templates"]:
            score = 0
            if q in t["name"].lower(): score += 10
            if q in t["description"].lower(): score += 5
            for f in t.get("files", []):
                if q in f.lower(): score += 3
            if score > 0:
                results.append({"category": cid, "category_name": cat["name"], "score": score, **t})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:10]


# ══════════════════════════════════════════
# SKILL EVOLUTION ENGINE
# ══════════════════════════════════════════

SKILL_LEVELS = {
    1: {"name": "学徒", "xp_required": 0, "icon": "⭐"},
    2: {"name": "初级", "xp_required": 100, "icon": "⭐⭐"},
    3: {"name": "中级", "xp_required": 300, "icon": "⭐⭐⭐"},
    4: {"name": "高级", "xp_required": 800, "icon": "🌟🌟"},
    5: {"name": "专家", "xp_required": 2000, "icon": "💎"},
    6: {"name": "大师", "xp_required": 5000, "icon": "👑"},
}

XP_PER_TASK = {
    "done": 50,       # Completing a task
    "failed": 5,      # Learning from failure
    "reused_module": 30,  # Reusing a module
    "created_module": 100,  # Creating a reusable module
    "project_complete": 200,  # Finishing a project
}


def _load_skills() -> dict:
    """Load skill evolution data"""
    if SKILLS_FILE.exists():
        with open(SKILLS_FILE) as f:
            return json.load(f)
    return {"agents": {}, "updated_at": None}


def _save_skills(data: dict):
    data["updated_at"] = datetime.now().isoformat()
    with open(SKILLS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def get_agent_skills(agent_id: str) -> dict:
    """Get agent skill profile with evolution history"""
    # Base skills from known profiles
    from apex.interface.project_registry import AGENT_SKILLS_DB
    base = AGENT_SKILLS_DB.get(agent_id, {"role": "Agent", "skills": [], "level": 1})

    data = _load_skills()
    agent_data = data["agents"].get(agent_id, {
        "xp": 0, "level": base["level"], "skills_learned": [],
        "projects_completed": [], "modules_created": [], "modules_reused": [],
        "history": [],
    })

    xp = agent_data.get("xp", 0)
    level = 1
    for lv in sorted(SKILL_LEVELS.keys(), reverse=True):
        if xp >= SKILL_LEVELS[lv]["xp_required"]:
            level = lv
            break

    next_level = level + 1 if level < 6 else 6
    next_xp = SKILL_LEVELS.get(next_level, {}).get("xp_required", xp + 1)
    progress = min(100, round((xp - SKILL_LEVELS[level]["xp_required"]) /
                              max(1, next_xp - SKILL_LEVELS[level]["xp_required"]) * 100))

    return {
        "agent_id": agent_id,
        "role": base["role"],
        "level": level,
        "level_name": SKILL_LEVELS[level]["name"],
        "xp": xp,
        "xp_next": next_xp,
        "progress_pct": progress,
        "skills": base["skills"],
        "skills_learned": agent_data.get("skills_learned", []),
        "projects_completed": agent_data.get("projects_completed", []),
        "modules_created": agent_data.get("modules_created", []),
        "modules_reused": agent_data.get("modules_reused", []),
        "history": agent_data.get("history", [])[-10:],
    }


def award_xp(agent_id: str, action: str, detail: str = "") -> dict:
    """Award XP to an agent for an action"""
    xp = XP_PER_TASK.get(action, 10)
    data = _load_skills()

    if agent_id not in data["agents"]:
        data["agents"][agent_id] = {
            "xp": 0, "level": 1, "skills_learned": [],
            "projects_completed": [], "modules_created": [], "modules_reused": [],
            "history": [],
        }

    ag = data["agents"][agent_id]
    ag["xp"] = ag.get("xp", 0) + xp
    ag["history"].append({
        "action": action, "xp": xp, "detail": detail,
        "timestamp": datetime.now().isoformat(),
    })

    # Check level up
    old_level = 1
    for lv in sorted(SKILL_LEVELS.keys(), reverse=True):
        if ag["xp"] - xp >= SKILL_LEVELS[lv]["xp_required"]:
            old_level = lv
            break

    new_level = 1
    for lv in sorted(SKILL_LEVELS.keys(), reverse=True):
        if ag["xp"] >= SKILL_LEVELS[lv]["xp_required"]:
            new_level = lv
            break

    leveled_up = new_level > old_level

    if action == "project_complete":
        ag["projects_completed"].append(detail)
    elif action == "created_module":
        ag["modules_created"].append(detail)
    elif action == "reused_module":
        ag["modules_reused"].append(detail)

    _save_skills(data)

    return {
        "ok": True, "agent": agent_id, "action": action,
        "xp_awarded": xp, "total_xp": ag["xp"],
        "level": new_level, "level_name": SKILL_LEVELS[new_level]["name"],
        "leveled_up": leveled_up,
        "message": f"🎉 {agent_id} 升级到 {SKILL_LEVELS[new_level]['name']}!" if leveled_up else
                   f"✅ {agent_id} +{xp}XP ({action})",
    }


def get_skill_leaderboard() -> list:
    """Get agent ranking by XP"""
    data = _load_skills()
    from apex.interface.project_registry import AGENT_SKILLS_DB

    rankings = []
    for aid, base in AGENT_SKILLS_DB.items():
        ag = data["agents"].get(aid, {"xp": 0, "level": base["level"]})
        xp = ag.get("xp", 0)
        level = 1
        for lv in sorted(SKILL_LEVELS.keys(), reverse=True):
            if xp >= SKILL_LEVELS[lv]["xp_required"]:
                level = lv
                break
        rankings.append({
            "agent_id": aid, "role": base["role"],
            "level": level, "level_name": SKILL_LEVELS[level]["name"],
            "xp": xp, "projects": len(ag.get("projects_completed", [])),
            "modules_created": len(ag.get("modules_created", [])),
        })

    rankings.sort(key=lambda r: r["xp"], reverse=True)
    return rankings


# ══════════════════════════════════════════
# PIPELINE — Dev→Test→Verify→Deploy→Evaluate
# ══════════════════════════════════════════

PIPELINE_STAGES = [
    {"id": "planning", "name": "需求规划", "icon": "ti-map", "order": 1},
    {"id": "development", "name": "开发中", "icon": "ti-code", "order": 2},
    {"id": "testing", "name": "测试验证", "icon": "ti-bug", "order": 3},
    {"id": "review", "name": "代码审查", "icon": "ti-eye-check", "order": 4},
    {"id": "staging", "name": "模拟环境", "icon": "ti-box", "order": 5},
    {"id": "deployment", "name": "部署上线", "icon": "ti-rocket", "order": 6},
    {"id": "evaluation", "name": "用户评价", "icon": "ti-star", "order": 7},
]


def get_project_pipeline(project: str) -> dict:
    """Get pipeline status for a project"""
    kanban_db = APEX_HOME / "kanban.db"
    if not kanban_db.exists():
        return {"stages": PIPELINE_STAGES, "tasks": []}

    conn = sqlite3.connect(str(kanban_db))
    conn.row_factory = sqlite3.Row
    try:
        # Map kanban task statuses to pipeline stages
        status_stage_map = {
            "todo": "planning",
            "ready": "development",
            "in_progress": "development",
            "done": "deployment",
            "blocked": "testing",
            "failed": "testing",
        }

        tasks = conn.execute(
            "SELECT id, title, status, assignee, priority, completed_at "
            "FROM tasks WHERE title LIKE ? AND status != 'done' "
            "ORDER BY priority ASC",
            (f"%[{project}]%",)
        ).fetchall()

        done = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE title LIKE ? AND status = 'done'",
            (f"%[{project}]%",)
        ).fetchone()[0]

        total = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE title LIKE ?",
            (f"%[{project}]%",)
        ).fetchone()[0]

        # Group tasks by stage
        stage_tasks = defaultdict(list)
        for t in tasks:
            stage = status_stage_map.get(t["status"], "planning")
            stage_tasks[stage].append({
                "id": t["id"][:12],
                "title": t["title"][:60],
                "agent": t["assignee"],
                "priority": t["priority"],
                "status": t["status"],
            })

        stages = []
        for s in PIPELINE_STAGES:
            sid = s["id"]
            ts = stage_tasks.get(sid, [])
            stages.append({
                **s,
                "task_count": len(ts),
                "tasks": ts,
                "active": len(ts) > 0,
            })

        conn.close()

        return {
            "project": project,
            "total_tasks": total,
            "done": done,
            "progress_pct": round(done / max(1, total) * 100),
            "stages": stages,
            "current_stage": next((s["name"] for s in stages if s["active"]), "规划中"),
        }
    finally:
        conn.close()


def get_project_evaluation(project: str) -> dict:
    """Simulated project evaluation metrics"""
    kanban_db = APEX_HOME / "kanban.db"
    if not kanban_db.exists():
        return {"error": "no data"}

    conn = sqlite3.connect(str(kanban_db))
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE title LIKE ?",
            (f"%[{project}]%",)
        ).fetchone()[0]
        done = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE title LIKE ? AND status = 'done'",
            (f"%[{project}]%",)
        ).fetchone()[0]
        failed = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE title LIKE ? AND status = 'failed'",
            (f"%[{project}]%",)
        ).fetchone()[0]
        conn.close()

        quality = round(done / max(1, total) * 100)
        velocity = done  # tasks completed
        bug_rate = round(failed / max(1, total) * 100, 1)

        return {
            "project": project,
            "metrics": {
                "quality_score": quality,
                "velocity": velocity,
                "bug_rate": bug_rate,
                "total_tasks": total,
                "completed": done,
                "failed": failed,
            },
            "evaluation": {
                "code_quality": min(100, quality + 10),
                "user_experience": min(100, quality + 5),
                "performance": min(100, quality + 15),
                "security": min(100, 85 - bug_rate * 2),
                "reusability": min(100, 60 + done // 2),
            },
            "rating": "⭐⭐⭐⭐⭐" if quality > 90 else
                      "⭐⭐⭐⭐" if quality > 70 else
                      "⭐⭐⭐" if quality > 50 else "⭐⭐",
        }
    finally:
        conn.close()
