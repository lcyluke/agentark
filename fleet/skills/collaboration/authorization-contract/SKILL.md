---
name: authorization-contract
description: "老卢（Luke）与 Hermes AI 的授权协作契约——分级授权模式 + 微信语音/文字快速确认，取代慢速打字 approve。"
version: 1.0.0
author: Luke & Hermes Agent
platforms: [macos, linux]
---

# 授权协作契约

## 适用场景

老卢通过微信与 Hermes AI 协作开发、部署、运维时，涉及文件操作、系统命令、账户登录等敏感操作前的授权确认。

## 核心理念

> **AI 判断风险等级 → 按等级执行对应授权策略 → 老卢用最快方式确认/拒绝**

授权不仅是为了安全，更是为了让老卢保持对项目的**控制感和信任感**。未经确认的意外操作比慢一点更伤协作体验。

## 四阶授权模式

| 模式 | 名称 | 自动放行 | 需确认 | 必须授权 |
|------|------|---------|--------|---------|
| 🟢 **open** | 开放模式 | 创建/修改文件、跑脚本、部署、搜索 | 删除文件/目录、系统命令、账户登录（需密语"阿宝"） | `rm -rf /` 级别 |
| 🔵 **smart** | 智能模式 | 读文件、查信息、轻量脚本 | 创建/修改文件、写配置 | 删除文件/目录、apt/yum install、账户登录 |
| 🟡 **cautious** | 谨慎模式 | read/cat/ls 纯读操作 | 创建/修改文件、写配置、运行脚本、npm/pip install | 删除文件/目录、系统命令、账户登录 |
| 🔴 **guardian** | 守护模式 | 纯读信息类 | 一切写操作、运行命令 | 同左（全部需要确认） |

当前模式：🟢 **open**（授权契约） + 🔵 **smart**（Hermes审批）—— 双重模式协同工作：
- 授权契约：几乎所有写操作自动放行，删除/系统命令/账户登录需确认
- Hermes审批：普通操作自动过，危险操作弹确认提示
- 层级C操作仍需要安全密语"阿宝"
- 切换方式：微信发 `/mode open` `/mode smart` `/mode cautious` `/mode guardian`

安全密语（已设置）：**阿宝 / abao**

已在2026-05-30由老卢亲自设置并验证通过。层级C操作必须附带此密语才执行。
使用方式：语音说"同意 阿宝" 或 打字"/approve 阿宝"

## 授权层级定义

### 层级 A — 自动放行（无需确认）
- `read_file`、`search_files`、`session_search`、`memory`（读）
- `vision_analyze`、`web_search`、`web_extract`
- `skills_list`、`skill_view`（读）
- `terminal` 中不写磁盘的命令（`python --version`、`ls -la`、`grep xx`）
- `browser_navigate`、`browser_snapshot`

### 层级 B — 需快速确认（微信语音/文字）
- 创建新文件（`write_file` 新路径）
- 修改已有文件（`patch`、`write_file`覆写）
- 部署脚本运行
- 安装依赖（`pip install`、`npm install`）
- git 操作（`git add`、`git commit`、`git push`）
- `terminal` 中带参数的执行命令（`python scripts/deploy.py`）
- `cronjob` 创建/修改

### 层级 C — 必须授权（语音/文字/手势确认）
- 删除文件或目录（`rm -rf`、`write_file ''` 清空文件）
- 系统级命令（`sudo`、`apt install`、`yum install`、`systemctl`）
- 账户登录操作（`ssh`、`hermes login`、`gh auth login`）
- 修改系统配置
- 修改 `.env`、密钥、凭证
- 数据库删除操作（`DROP TABLE`、`DELETE FROM`）
- **大规模文件重建/恢复操作**（scratch workspace 被 GC 后恢复代码、从 memory 或旧备份重建项目文件）—— 必须先确认有可用的备份恢复机制（git 仓库、文件快照、备份文件），**无备份则禁止重建**
- `delegate_task` 中涉及上述层级C的操作

## 🔐 安全机制：双重身份验证

### 信任基础

当前你通过**微信一对一私聊**与我沟通。微信平台本身已通过你的手机号+密码+设备绑定完成了用户身份认证。所以我接收到的每一条消息，来源都是**经过微信验证的你**（用户ID: o9cq801pPjNXqgPCdhTHLRu8eJL0@im.wechat）。

### 安全密语（可选开启）

如果你想再加一层保险，可以设置一个**安全密语**——一个只有你知道的短词，执行层级C（高风险）操作时必须附带此密语才有效。

**使用方式：**
```
/mypassword <你的安全密语>
```

设置后，高风险授权必须附带密语：
- ✅ `同意 苹果派` → AI识别已附带正确密语，执行
- ❌ `同意` → AI回复"请附带安全密语确认身份"
- ❌ `同意 西瓜` → AI回复"安全密语错误"

**如何设置：** 直接发微信告诉我你的安全密语就行，或者先不设，以后有需要再加。

### 语音授权的真实安全模型

> 🎤 **你发语音 → 微信服务器转文字并验证身份 → 我收到文字消息（来源已确认为老卢）**

我**没有**声纹识别能力（那是另一套需要提前注册声纹样本的AI系统），但微信的消息来源验证已经足够强。对于一对一私聊场景，**平台级认证 > 声纹识别**（声纹可以被录音骗过，微信账号不能）。

## 微信授权方式（按推荐优先级）

| 方式 | 操作 | 说明 |
|------|------|------|
| 🎤 **语音授权** | 发语音说"**同意**"（或设置安全密语后说"同意 密码"） | 最快，不用打字 |
| ✍️ **打 /approve** | 输入 `/approve` | 经典方式 |
| ✍️ **打 /always + 操作类型** | 如 `/always deploy` 永久信任部署命令 | 省去以后同类操作反复确认 |
| ✍️ **打 /deny** | 拒绝当前操作 | |
| ✍️ **打 /mode + 模式名** | 如 `/mode guardian` 切换守护模式 | 随时换挡 |
| 🎤 **语音说"不用问"** | 临时切换到 open 模式 | 你忙的时候 |

## 快速模式切换

在微信对话框中输入以下命令即可切换授权模式：

- `/mode open` → 🟢 开放模式（信任模式）
- `/mode smart` → 🔵 智能模式
- `/mode cautious` → 🟡 谨慎模式（推荐日常）
- `/mode guardian` → 🔴 守护模式

## 当前授权状态

当前模式：🟢 **open**（授权契约） + 🔵 **smart**（Hermes审批）—— 双重模式协同工作：
- 授权契约：几乎所有写操作自动放行，删除/系统命令/账户登录需确认
- Hermes审批：普通操作自动过，危险操作弹确认提示
- 层级C操作仍需要安全密语"阿宝"

安全密语（已设置）：**阿宝 / abao**
已在2026-05-30由老卢亲自设置并验证通过。层级C操作必须附带此密语才执行。
使用方式：语音说"同意 阿宝" 或 打字"/approve 阿宝"

切换方式：微信发 `/mode open` `/mode smart` `/mode cautious` `/mode guardian`
Hermes审批切换：用 `hermes config set approvals.mode [smart|off|manual]` 在终端执行

## 契约执行原则

1. **执行前告知**：遇到层级B/C操作时，我先向老卢说明"我要做什么操作"
2. **等待确认**：收到老卢的"同意"（语音/文字）后才执行
3. **不擅自升级**：不因为老卢忙就擅自放行高风险操作
4. **可回溯**：任何时候老卢可以问"刚才你做了什么操作"，我据实回答
5. **可撤回**：老卢可以要求回滚某个操作
6. **契约本身**：修改此契约本身需要 guardian 模式授权

## 🏛️ 技术实现：授权引擎 (AuthorizationEngine)

行为契约由 `apex/orchestration/authorization.py` 中的 `AuthorizationEngine` 类实现：

| 组件 | 位置 | 说明 |
|------|------|------|
| 核心引擎 | `apex/orchestration/authorization.py` | SQLite + SHA256 哈希链 · 15 种 scope · 多 Agent |
| Dashboard API | `/api/auth/*` (11 端点) | request / approve / deny / check / consume / revoke / grants / audit / stats / verify / scopes |
| 消息路由器 | `apex/orchestration/message_router.py` | `auth` 类别 → `apex-pm` profile 路由 |
| CLI wrapper | `~/.hermes/scripts/authorization_engine.py` | 薄 wrapper，cron/脚本兼容，调用核心引擎 |
| apex-pm Profile | `~/.hermes/profiles/apex-pm/` | Apex 专属 PM Agent，处理 auth 消息 |
| 数据库 | `~/.hermes/auth/grants.db` + `audit.log` | 授权记录 + append-only 审计日志 |

**Scope 命名规范**: `{domain}:{resource}:{action}` — 如 `autodl:ssh:shutdown`, `cloud:aws:ec2:terminate`

**唯一审批人**: 老卢 (`APPROVED_BY = "luke"`) — 通过微信确认码审批，不可被任何人修改

**使用流程**: 特权操作前 → `engine.check()` → 未授权则 `engine.request()` → 老卢微信确认 → `engine.approve(code)` → 执行 → `engine.consume(grant_id)`

完整集成架构见 `references/authorization-engine-integration.md`

### 实操记录
首次实战复盘见 `references/first-operations-record.md`
模式切换实战见 `references/2026-05-30-mode-switch.md`
安全密语设置记录见 `references/2026-05-30-passphrase-setup.md`

## 技术实现

授权引擎已集成到 Apex 项目，核心代码位于：
- `apex/orchestration/authorization.py` — AuthorizationEngine (570行，15个privileged scope，SHA256哈希链，SQLite grants.db)
- `apex/interface/web.py` — 11个 `/api/auth/*` REST端点
- `apex/orchestration/message_router.py` — `auth` 消息类别路由到 `apex-pm` Profile
- `~/.hermes/scripts/authorization_engine.py` — CLI薄wrapper（委托给Apex核心引擎）

所有特权操作（AutoDL开关机/释放、云资源管理、生产部署、系统配置修改）必须通过此引擎，仅老卢可通过微信确认6位授权码审批，每次授权形成不可篡改的审计链。
