---
name: cross-platform-handoff
description: "跨平台会话衔接策略 — 当用户从微信等平台切换到CLI（或反之）时，通过 Memory/Skill 桥接项目上下文。"
version: 1.0.0
---

# 跨平台会话衔接策略

## 适用场景

老卢通过多个平台和 Hermes 交互：CLI（终端）、微信（WeChat）、可能还有钉钉/飞书/Slack。每个平台是独立会话，上下文不互通。

此 Skill 定义跨平台上下文桥接的规则。

## 核心规则

### 1. 平台角色分工与连接特性

| 平台 | 角色 | 连接方式 | 需要公网IP？ | 能力 |
|------|------|----------|:---:|------|
| CLI 终端 | 主力开发平台 | 本地 | 不需要 | 完整工具链（文件、终端、部署、浏览器） |
| 微信 | 轻量互动 | iLink 长轮询 | 不需要 | 文字/图片/语音/文件 |
| 钉钉 | 轻量互动 | dingtalk-stream (WebSocket) | 不需要 | 文字/图片/语音 |
| 飞书 | 轻量互动 | Webhook 回调 | **需要** | 文字/图片/卡片 |
| Slack | 轻量互动 | WebSocket | 不需要 | 文字/图片 |

**关键发现：微信和钉钉都是从 Hermes 主动出站连接平台的，不需要公网 IP。飞书需要飞书服务器推送回调到 Hermes，所以需要公网可达的 URL（可用腾讯云做 frp 中转）。**

- 微信配置详见 `references/wechat-setup.md`
- 各平台连接需求详见 `references/platform-connectivity.md`

### 1b. macOS 常驻与休眠

网关通过 `hermes gateway install` 注册为 launchd 用户服务（`~/Library/LaunchAgents/ai.hermes.gateway.plist`），开机自启、崩溃自动重启。

休眠行为（MacBook）：
- **插电 + 显示器关** → 系统正常运行，网关不受影响 ✅
- **屏保** → 不受影响 ✅  
- **合盖（不外接显示器）** → 强制休眠 ❌，进程冻结，消息积压
- **合盖 + 外接显示器** → Clamshell 模式，不会休眠 ✅

建议设置插电不休眠：`sudo pmset -c sleep 0`（需要 sudo 权限）。

### 2. Memory 是唯一共享层

- 每个平台的会话是完全隔离的（不同 session_key）
- Memory 在每个新会话都会被注入
- **关键原则：在 CLI 完成复杂任务后，必须把核心结论/状态写入 Memory**
- 反过来，从微信收到的重要指令/偏好也要写 Memory

### 3. 什么必须写 Memory

- 项目关键路径（文件在哪里、最新状态）
- 用户偏好变化（"以后用 pnpm 而不是 npm"）
- 环境变化（"服务器已迁移到 xxx"）
- 决策结论（"决定用方案 B 因为 A 太慢"）

### 4. 什么写 Skill（更持久）

- 反复出现的操作流程（部署步骤、测试命令）
- 踩过的坑和 workaround
- 发现的工具用法

### 5. 微信→CLI 切换时的处理

当用户在微信上说「帮我在 CLI 上做 X」或提到之前 CLI 会话的内容：
1. 先查 Memory 了解项目背景
2. 如果 Memory 不够，提醒用户在 CLI 开启新会话（微信无法直接操作文件）
3. 复杂任务引导用户切换到 CLI

**⚠️ 上下文混淆陷阱（高优先级）：** 微信和 CLI 是完全隔离的会话。在微信上收到模糊请求时，**不要假设用户在问 CLI 会话里刚发生的事情**。典型错误：CLI 会话里刚重启了网关 → 微信上用户问「为什么 shutdown 了」→ 误以为在问网关 → 实际用户在问 IoT 设备场景。**验证规则：**
- 如果微信请求能同时匹配 CLI 当前话题和用户的其他项目/场景 → 停下来，列出两种可能的理解，让用户确认
- 不要在微信端基于 CLI 会话上下文做出未经确认的推断
- 用户说「刚才」在微信里指的是微信对话里刚才说的，不是 CLI 会话里刚才发生的
- 当用户说「刚才在XX平台让你做Y」→ 立即回想或搜索那个平台的消息，不要用CLI上下文覆盖
> 📋 实战案例：`references/cross-context-confusion-case.md`

### 7. 邮件审批工作流（Himalaya CLI）

不使用网关内置的 Email 适配器（不稳定，IMAP 重连噪音大）。用 Himalaya CLI 实现手动触发的审批制邮件：

```
你: "查邮件"
Hermes: → himalaya envelope list → 显示最新 20 封摘要

你: "看第 3 封"
Hermes: → himalaya message read 3 → 显示全文

你: "回复第 3 封，说 xxx"
Hermes: → 起草回复 → 展示草稿 → ⚠️ 停在这里等你批

你: "发" / "改一下 xxx"
Hermes: → 修改后重展草稿 / → himalaya template send → 发送 ✅
```

| 操作 | 需要批准？ |
|------|:---:|
| 查收件箱 | 不需要 |
| 读邮件 | 不需要 |
| 搜索邮件 | 不需要 |
| 发新邮件 | **需要** |
| 回复/转发 | **需要** |
| 删除/移动 | **需要** |

Outlook/Office 365 需要「应用密码」（不是登录密码）：
account.microsoft.com/security → 应用密码 → 生成 16 位密码。

Himalaya 配置详见 `references/email-via-himalaya.md`。

### 6. CLI→微信 通知策略

- 长任务完成后，如果微信已连接，可以主动提「需要我在微信上给你发个通知吗？」
- 不主动往微信推送（微信是拉取模式，不是推送）

### 6b. WeChat Communication Characteristics

老卢主要通过微信跟Hermes交互。微信作为核心沟通渠道的特性：

- **Markdown格式支持** — 微信消息支持Markdown（标题、表格、代码块、加粗等），合理使用提升可读性
- **多媒体发送** — `MEDIA:/absolute/path/to/file`可发送原生图片、视频、文件
- **会话持续性** — 微信会话持久，用户可能隔几小时甚至隔天继续话题
- **短消息风格** — 手机阅读，回复需紧凑、快速进入重点
- **限流保护** — iLink API有频率限制：连发消息间隔需≥3秒，否则触发`rate limited ret=-2`。网关自动backoff 3秒后恢复。用户看到延迟回复时，不要连续追问——等10秒后自动恢复

### 6c. 微信小程序 DevTools 测试

羽球宝AI搭子小程序(`~/Desktop/2026AIAPP/workspace/badminton-coach-ai/miniprogram/`)已接入Hermes网关：

```bash
# 启动后端API（小程序依赖）
cd ~/Desktop/2026AIAPP/workspace/badminton-coach-ai
python3 -m badminton_coach.webapp --host 0.0.0.0 --port 8000 &

# 打开DevTools
/Applications/wechatwebdevtools.app/Contents/MacOS/cli open \
  --project ~/Desktop/2026AIAPP/workspace/badminton-coach-ai/miniprogram
```

关键配置：`app.js`中`apiBase: 'http://127.0.0.1:8000'`指向本地webapp。
DevTools模拟器可测试登录→评估→结果全流程。微信Mock登录模式（`/api/auth/wechat POST`）无需真手机号。
webapp.py已集成标注管道API：`/api/v1/upload`（异步上传+骨骼标注+评估）、`/api/v1/task/{id}`（轮询结果）、`/api/v1/stats`（系统统计）。

> 📱 **小程序 UX 设计参考：** `references/wechat-miniapp-ux-patterns.md` — 5-tab 结构、首页仪表盘、技能测评/模拟训练/按摩预防页设计规范、新增匹配/球馆/打卡子页面、WXML 禁 JS 表达式等关键坑。

## 实战模式

```
微信上来就问: "上次那个羽球地图的场馆数据怎么样了？"
  ↓
1. 查 Memory → 找到项目路径、Notion 库、采集进度
2. 回复: "已采集 326 家，128 家入 Notion。详细数据在 ~/Desktop/2026AIAPP/shenzhen-badminton/"
3. 如果需要操作文件: "这事儿需要 CLI 来操作文件，你在终端开个新会话我帮你处理"
```

## 辅助文件

| 文件 | 用途 |
|------|------|
| `references/gateway-platform-ops.md` | 各平台已知问题/恢复/操作记录 (微信503+限流, 钉钉webhook丢失, Slack权限, Himalaya, 常驻服务) |
| `references/wechat-setup.md` | 微信接入完整指南：依赖安装、QR登录脚本与坑、环境变量、常见错误修复 |
| `references/dingtalk-setup.md` | 钉钉接入指南：Stream模式、开放平台配置、与微信对比 |
| `scripts/weixin_qr_login.py` | 微信扫码登录独立脚本（PNG+ASCII双输出，轮询直到确认） |
| `references/cronjob-delivery-patterns.md` | Cronjob 定时任务交付模式（工作 vs 副业区分、交付目标选择、测试流程） |
| `references/email-via-himalaya.md` | Himalaya CLI 邮箱配置：Outlook 应用密码、审批工作流、命令速查 |
| `references/docx-report-generation.md` | Word 报告生成：python-docx 用法、表格样式、lxml 踩坑、系统Python方案 |
| `references/project-directory-hygiene.md` | 多项目目录混淆处理策略 |
| `references/cross-context-confusion-case.md` | 跨平台上下文混淆实战案例（微信↔CLI 任务错位） |
| `references/badminton-pipeline-quirks.md` | 羽毛球标注系统 Agent 调用约定（位置参数 vs --flags、MediaPipe 容错、检测阈值） |
