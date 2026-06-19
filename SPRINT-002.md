# Apex SPRINT-002 — 安装体验 & 配置系统

**Sprint Goal:** 将 Hermes 的安装引导、品牌Logo、模型配置、主题换肤等特性集成到 Apex

**Sprint Duration:** 预计 48h (可分4个Phase并行开发)
**Start:** 2026-06-19
**PM:** pm (Apex Agent)

---

## Phase 1 ⸻ Setup 交互式安装向导 (12h)

### TASK P1-001: 重写 `apex setup` 交互式向导 (4h)
- [ ] 分步引导流程: Welcome → Model → Provider → Tools → Fleet → Done
- [ ] 每步显示进度条 `[█░░░] 2/5`
- [ ] 自动检测系统环境 (Python版本/OS/tmux/Hermes)
- [ ] 调用 ToolDiscovery 扫描已安装工具
- [ ] 支持 --quick (全默认) 和 --interactive (交互)
- **Owner:** backend-dev | **Skills:** python, click, rich
- **File:** `apex/interface/setup_wizard.py`

### TASK P1-002: 模型自动检测 + 选择器 (3h)
- [ ] 扫描环境变量中的 API Key (DEEPSEEK_API_KEY, OPENAI_API_KEY, etc.)
- [ ] 检测已安装的 Hermes/Claude Code/Codex 模型配置
- [ ] Rich 选择器 UI (上下键选模型)
- [ ] 保存到 `~/.apex/config.yaml`
- **Owner:** backend-dev | **Skills:** python, api-integration
- **File:** `apex/interface/model_selector.py`

### TASK P1-003: 首次运行引导流程 (3h)
- [ ] 检测 `~/.apex/config.yaml` 是否存在
- [ ] 不存在时自动触发 setup wizard
- [ ] 完成后显示 "下一步" 建议 (fleet init → monitor status)
- [ ] 支持 `apex setup --check` 诊断常见问题
- **Owner:** pm | **Skills:** python, click
- **File:** `apex/interface/first_run.py`

### TASK P1-004: 配置存储系统 (2h)
- [ ] `~/.apex/config.yaml` 读写
- [ ] 字段: model, provider, api_key (env ref), fleet_defaults, ui_prefs
- [ ] JSON Schema 校验
- [ ] 环境变量覆盖优先级: env > config.yaml > defaults
- **Owner:** backend-dev | **Skills:** python, yaml, pydantic
- **File:** `apex/core/config.py` (new) + extend existing

---

## Phase 2 ⸻ 品牌Logo & 终端UX (10h)

### TASK P2-001: Apex ASCII/Emoji Logo Banner (2h)
- [ ] 设计 Apex Logo: ⚡ + 舰队主题
- [ ] `apex --version` 显示 Logo
- [ ] 每次命令启动可选显示 mini banner
- [ ] 参考 Hermes 的 `⚕` 蛇杖设计
- **Owner:** frontend-dev | **Skills:** ascii-art, rich
- **File:** `apex/interface/logo.py`

### TASK P2-002: 皮肤/主题引擎 (4h)
- [ ] 内置 3 套主题: dark (默认), ocean, sunset
- [ ] `apex config theme ocean` 切换
- [ ] 主题配置: 边框颜色、标题样式、强调色、背景亮度
- [ ] 实时预览 `apex config theme --preview`
- **Owner:** frontend-dev | **Skills:** rich themes, yaml
- **File:** `apex/interface/skin_engine.py`

### TASK P2-003: 命令别名系统 (2h)
- [ ] 短别名: `apex s` = `apex monitor status`, `apex fs` = `apex fleet status`
- [ ] 存储在 `~/.apex/aliases.yaml`
- [ ] `apex alias list/add/remove`
- [ ] 参考 git alias + hermes alias
- **Owner:** backend-dev | **Skills:** python, click
- **File:** `apex/interface/aliases.py`

### TASK P2-004: 加载动画/Spinner (2h)
- [ ] 长时间操作(init/install/scan)显示 spinner
- [ ] 支持多种风格: dots, arrow, bounce, kaomoji
- [ ] 进度条: `[█████░░░░░] 45% Initializing agents...`
- [ ] 参考 Hermes 的 KawaiiSpinner
- **Owner:** frontend-dev | **Skills:** rich progress, animation
- **File:** `apex/interface/spinner.py`

---

## Phase 3 ⸻ 配置管理系统 (10h)

### TASK P3-001: `apex config` 命令组 (3h)
- [ ] `apex config show` — 显示当前所有配置
- [ ] `apex config set <key> <value>` — 设置配置项
- [ ] `apex config get <key>` — 读取配置项
- [ ] `apex config path` — 显示配置文件路径
- [ ] `apex config edit` — 用 $EDITOR 打开配置文件
- **Owner:** devops | **Skills:** python, click, yaml
- **File:** `apex/cli/commands/config_cmds.py`

### TASK P3-002: 模型/Provider 管理 (3h)
- [ ] `apex config model list` — 列出可用模型
- [ ] `apex config model set deepseek-v4-pro` — 切换默认模型
- [ ] `apex config model detect` — 自动检测 (调用 model_selector)
- [ ] `apex config provider list` — 列出可用provider
- [ ] 支持多个 API Key 轮转 (credential pool)
- **Owner:** devops | **Skills:** python, api
- **File:** extend `apex/cli/commands/config_cmds.py`

### TASK P3-003: Agent Profile 检查器 (2h)
- [ ] `apex config profile <name>` — 查看Agent配置
- [ ] 显示: SOUL.md, model, skills count, wrapper path
- [ ] `apex config profile <name> --edit` — 编辑SOUL.md
- **Owner:** qa-engineer | **Skills:** python, click
- **File:** extend `apex/cli/commands/config_cmds.py`

### TASK P3-004: 环境诊断 `apex doctor` (2h)
- [ ] 检查: Python版本, tmux, Hermes, 网络, GitHub 连通性
- [ ] 检查: 配置文件完整性, API Key 有效性
- [ ] 输出诊断报告 + 修复建议
- [ ] `apex doctor --fix` 自动修复常见问题
- **Owner:** qa-engineer | **Skills:** python, system
- **File:** `apex/interface/doctor.py`

---

## Phase 4 ⸻ 高级特性 (12h)

### TASK P4-001: 交互式教程 (3h)
- [ ] `apex tutorial` — 交互式新手教程
- [ ] 步骤: Welcome → Fleet Init → Monitor → PM Dashboard → Done
- [ ] 每个步骤等待用户确认后继续
- [ ] 包含真实命令执行 + 结果展示
- **Owner:** frontend-dev | **Skills:** python, click, rich
- **File:** `apex/interface/tutorial.py`

### TASK P4-002: 通知钩子系统 (3h)
- [ ] Agent 任务完成 → 终端通知
- [ ] 关键路径阻塞 → 告警
- [ ] 支持: macOS notification center, Slack webhook, WeCom
- [ ] 配置: `apex config notify on/off/slack/webhook`
- **Owner:** devops | **Skills:** python, webhook, macos-notifications
- **File:** `apex/interface/notifier.py`

### TASK P4-003: Dashboard 自动刷新 (2h)
- [ ] `apex monitor status --watch` 增强
- [ ] 显示相对时间变化 (采集 +5, 剪辑 +2)
- [ ] 自动高亮变化行
- [ ] 声音/视觉告警 (可选)
- **Owner:** frontend-dev | **Skills:** python, rich live
- **File:** `apex/interface/monitor.py` (extend)

### TASK P4-004: 更新日志 + Release Notes (2h)
- [ ] `apex version` 显示最近3个版本的 release notes
- [ ] 自动从 GitHub Releases 拉取
- [ ] 更新后显示 "What's new" 摘要
- **Owner:** github-release | **Skills:** python, github-api
- **File:** `apex/interface/version.py` (extend)

### TASK P4-005: 国际化 i18n 框架 (2h)
- [ ] 提取所有用户可见字符串到语言文件
- [ ] 支持: zh-CN (默认), en
- [ ] `apex config lang en` 切换
- [ ] 翻译文件: `apex/i18n/zh-CN.json`, `apex/i18n/en.json`
- **Owner:** architect | **Skills:** python, i18n, json
- **File:** `apex/i18n/` (new directory)

---

## 依赖关系图

```
P1-001 (Setup Wizard)
  ├── P1-002 (Model Selector)
  ├── P1-003 (First Run)
  └── P1-004 (Config Storage)
        │
        ▼
P2-001 (Logo) ──┐
P2-002 (Skin)  ─┤ 可并行
P2-003 (Alias) ─┤
P2-004 (Spinner)┘
        │
        ▼
P3-001 (Config CLI) ──┬── P3-002 (Model Mgmt)
                      ├── P3-003 (Profile Check)
                      └── P3-004 (Doctor)
        │
        ▼
P4-001 (Tutorial) ──┐
P4-002 (Notifier)  ─┤ 可并行
P4-003 (Live Refresh)┤
P4-004 (Release Notes)┤
P4-005 (i18n) ──────┘
```

## 并行开发策略

```
Week 1:
  并行: P1 (backend-dev + pm)  |  P2 (frontend-dev + backend-dev)
  串行: P1 → P3 (依赖Config Storage)

Week 2:
  并行: P3 (devops + qa-engineer)  |  P4 (全队并行)

Week 3:
  集成测试 + 修复 Bug + 发布
```

## 关键路径

```
P1-001 → P1-004 → P3-001 → P3-002 → P4-002
  (12h)    (2h)     (3h)     (3h)     (3h) = 23h
```

## 验收标准

- [ ] `apex setup` 全新安装从零到舰队运行 < 5 分钟
- [ ] `apex config model set X` 立即生效
- [ ] `apex doctor` 能诊断 90% 常见问题
- [ ] 3 套主题可切换
- [ ] `apex tutorial` 新手 10 分钟内上手
- [ ] 中英文切换无乱码
