# Intelligent Project Factory

Three interconnected systems that turn Apex into a self-improving project machine.

## Module Library

Standardized reusable code modules organized by project type.

**Categories:**
| Type | Templates | Best For |
|------|-----------|----------|
| miniprogram | 登录认证/微信支付/MediaPipe追踪/TabBar | 微信小程序 |
| saas | RBAC+SSO/API网关/审计日志/K8S部署 | SAAS系统 |
| android | Material UX/相机视频录制 | Android App |
| ai-chat | ChatGPT UI/IAM身份管理 | AI Chat界面 |
| backend | FastAPI骨架/数据库迁移/异步队列 | 后端通用 |

**API:** `GET /api/modules`, `GET /api/modules?q=支付`, `GET /api/modules?category=miniprogram`

**Module:** `apex/interface/project_factory.py::MODULE_CATEGORIES`

## SKILL Evolution Engine

Agent XP system with 6 levels. Agents earn XP by completing tasks and projects.

| Level | Name | XP Required | Badge |
|-------|------|-------------|-------|
| 1 | 学徒 | 0 | ⭐ |
| 2 | 初级 | 100 | ⭐⭐ |
| 3 | 中级 | 300 | ⭐⭐⭐ |
| 4 | 高级 | 800 | 🌟🌟 |
| 5 | 专家 | 2000 | 💎 |
| 6 | 大师 | 5000 | 👑 |

**XP Awards:**
- Complete task: +50 XP
- Reuse module: +30 XP
- Create module: +100 XP
- Complete project: +200 XP

**API:** `GET /api/skills/<agent>`, `POST /api/skills/award`, `GET /api/skills/leaderboard`

**Module:** `apex/interface/project_factory.py::SKILL_LEVELS`

## Pipeline (7-Stage)

Development workflow from planning to evaluation.

```
需求规划 → 开发中 → 测试验证 → 代码审查 → 模拟环境 → 部署上线 → 用户评价
```

Each stage shows task count and task list. Progress bar tracks overall completion.

**API:** `GET /api/pipeline/<project>` — returns stages + evaluation metrics

**Evaluation Dimensions:** Quality / User Experience / Performance / Security / Reusability

## Project Registry

Project proposals require approval from 始祖Agent before appearing in dropdowns.

**Flow:** `propose_project()` → `approve_project("始祖Agent·小卢")` → appears in `/api/projects/approved`

**Module:** `apex/interface/project_registry.py`

**API:** `POST /api/projects/propose`, `POST /api/projects/approve`, `GET /api/projects/approved`, `GET /api/projects/<name>`, `GET /api/agents/<agent_id>`

## Agent Capability Profile

Each agent gets a comprehensive profile: role, skills, completed/active projects, task queue, model comparison (4 models × 4 dimensions).

**Dimensions:** coding / reasoning / speed / cost_efficiency

**API:** `GET /api/agents/<agent_id>`, `GET /api/agents`
