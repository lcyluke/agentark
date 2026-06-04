# 🦅 Apex Agent Fleet — 完整舰队编制

> **Apex 多 Agent 操作系统 · 33 Agent 编制**
> 一个人的公司，一支 AI 舰队。

---

## 舰队架构

```
                    ⚓ Origin (舰队总司令)
                    ┌───────┼───────┐
                    │       │       │
              🧭 监控层    📋 PM层   🔧 执行层
              (6 Agent)   (5 Agent)  (22 Agent)
                    │       │       │
              ┌─────┤   ┌───┤   ┌───┼───────┐
              │     │   │   │   │   │       │
            舰队   GPU  PM  项目 开发  AI   安全/内容
            指挥  哨兵  Agent Agent Agent Agent Agent
```

---

## 一、🧭 舰队管理层（Monitoring Fleet）

自动化运维，24×7 值守。6 个 Agent 通过 Apex AutonomousEngine + Hermes Cron 协同工作。

| Agent | 角色 | 职能 | Apex YAML | Hermes Profile |
|-------|------|------|-----------|----------------|
| **fleet-commander** | 🧭 舰队司令 | 全舰队状态汇总、异常预警 | ✅ | ✅ |
| **gpu-sentinel** | ⚡ GPU 哨兵 | GPU 利用率/成本/闲时关机 | ✅ | ✅ |
| **token-guardian** | 💰 Token 守卫 | API 用量统计/预算预警 | ✅ | ✅ |
| **session-scout** | 🔍 会话斥候 | 新会话发现/分类/登记 | ✅ | ✅ |
| **cron-medic** | 🛡️ Cron 军医 | 定时任务健康巡检 | ✅ | ✅ |
| **profile-syncer** | 📡 通讯兵 | Profile 状态同步 Apex↔Hermes | ✅ | ✅ |

---

## 二、📋 项目管理线（PM Fleet）

产品方向决策、需求管理、授权审批。

| Agent | 角色 | 职能 | Apex YAML | Hermes Profile |
|-------|------|------|-----------|----------------|
| **apex-pm** | 🦅 Apex PM | Apex 平台总管、授权引擎、里程碑 | ❌ | ✅ |
| **yuji-pm** | 🎯 羽球宝 PM | 羽球宝AI搭子项目管理 | ❌ | ✅ |
| **product-manager** | 📋 产品经理 | 通用 PRD/用户研究/路线图 | ✅ | ✅ |
| **project-manager** | 📊 项目经理 | 跨项目 Kanban/资源调度 | ❌ | ✅ |
| **requirements-analyst** | 📝 需求分析师 | 需求拆解/用例分析 | ❌ | ✅ |

---

## 三、💻 开发线（Dev Fleet）

### 3.1 前端

| Agent | 角色 | 核心技能 | Apex YAML | Hermes Profile |
|-------|------|---------|-----------|----------------|
| **frontend-dev** | 💻 前端开发 | React/Vue/小程序/Tailwind | ✅ | ✅ |
| **fullstack-dev** | 👨‍💻 全栈开发 | React+FastAPI+部署 | ❌ | ✅ |

### 3.2 后端

| Agent | 角色 | 核心技能 | Apex YAML | Hermes Profile |
|-------|------|---------|-----------|----------------|
| **backend-dev** | ⚙️ 后端开发 | FastAPI/Python/数据库 | ✅ | ✅ |
| **architect** | 🏛️ 架构师 | 系统设计/API/数据库 | ✅ | ✅ |

### 3.3 DevOps

| Agent | 角色 | 核心技能 | Apex YAML | Hermes Profile |
|-------|------|---------|-----------|----------------|
| **devops** | 🔧 DevOps | CI-CD/Docker/K8s/监控 | ✅ | ✅ |
| **ops-engineer** | 🐧 运维工程师 | Linux/Nginx/SSH/备份 | ❌ | ✅ |

---

## 四、🤖 AI 线（AI Fleet）

| Agent | 角色 | 核心技能 | Apex YAML | Hermes Profile |
|-------|------|---------|-----------|----------------|
| **ai-algorithm** | 🧠 算法专家 | ML/DL/推荐系统/NLP | ❌ | ✅ |
| **ai-vision** | 👁️ 视觉专家 | CV/MediaPipe/YOLO/姿态 | ❌ | ✅ |

---

## 五、🔒 安全线（Security Fleet）

| Agent | 角色 | 核心技能 | Apex YAML | Hermes Profile |
|-------|------|---------|-----------|----------------|
| **security-compliance** | 🛡️ 安全合规 | 审计/合规/GDPR/隐私 | ❌ | ✅ |
| **security-by-design** | 🔐 安全设计 | 威胁建模/安全架构 | ❌ | ✅ |
| **vulnerability-scanner** | 🔍 漏洞扫描 | CVE/依赖检查/SAST | ❌ | ✅ |
| **penetration-tester** | ⚔️ 渗透测试 | 红队/OWASP/漏洞利用 | ❌ | ✅ |
| **audit-guardian** | 📜 审计卫士 | 哈希链验证/只读克隆 | ❌ | ✅ |

---

## 六、✍️ 内容 & 商业线

| Agent | 角色 | 核心技能 | Apex YAML | Hermes Profile |
|-------|------|---------|-----------|----------------|
| **content-marketing** | ✍️ 内容营销 | 文案/SEO/社交媒体 | ❌ | ✅ |
| **editor** | 📝 编辑 | 审校/质量把关 | ✅ | ✅ |
| **writer** | ✍️ 写手 | 内容创作/故事叙述 | ✅ | ✅ |
| **publisher** | 📤 发布者 | 格式化/分发/CMS | ✅ | ✅ |
| **fundraising-pitch** | 💰 融资路演 | BP/财务模型/投资人 | ❌ | ✅ |

---

## 七、🔬 质量线（QA Fleet）

| Agent | 角色 | 核心技能 | Apex YAML | Hermes Profile |
|-------|------|---------|-----------|----------------|
| **qa-engineer** | 🧪 测试工程师 | 自动化测试/缺陷追踪 | ❌ | ✅ |
| **skill-evaluator** | 📏 技能评估 | 基准测试/能力度量 | ❌ | ✅ |

---

## 八、🏗️ 项目模板 Agent

Apex 支持 `apex team template` 一键创建项目团队。以下是预置模板 Agent：

| Agent | 类型 | Apex YAML | Hermes Profile |
|-------|------|-----------|----------------|
| **羽球宝AI_pm** | 产品经理 | ✅ | ❌ |
| **羽球宝AI_frontend** | 前端开发 | ✅ | ❌ |
| **羽球宝AI_backend** | 后端架构 | ✅ | ❌ |
| **羽球宝AI_devops** | DevOps | ✅ | ❌ |
| **羽球宝AI_content** | 内容运营 | ✅ | ❌ |

---

## 统计

| 维度 | 数量 |
|------|------|
| **总 Agent 数** | **33** |
| Apex YAML 注册 | 27 |
| Hermes Profile 注册 | 33 |
| 双注册 (Apex+Hermes) | 27 |
| Hermes 独有 | 6 (apex-pm, yuji-pm, project-manager, requirements-analyst, fullstack-dev, audit-guardian 等) |
| 模型 | 全部 deepseek-v4-pro |
| 日均成本估算 | ~$0.5-2.0（正常使用） |

---

## 快速开始

```bash
# 查看所有 Agent
apex squad status

# 创建项目团队
apex team template webapp

# 查看舰队状态
apex dashboard  # → http://localhost:8080/cc

# 给 Agent 派任务
apex task create "Build login page" --assignee frontend-dev --hours 4
```

---

## 一个人 = 一家公司

Apex 的核心理念：**一个人配备 33 个 AI Agent，可以同时管理多个项目、多个团队**。

- **监控层**自动运转，24×7 看守 GPU/Token/Cron
- **PM 层**每人负责一个项目，互不干扰
- **执行层**按需唤醒，用完即停
- **安全层**全程审计，不可篡改

这就是 Apex 要开源交付的愿景。
