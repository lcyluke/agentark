---
name: notification-dispatcher
description: 角色驱动的Hermes cron通知引擎 — 配置化激活/模板渲染/Profile感知/子角色聚合
version: 2.0.0
author: 小卢 (Hermes AI)
tags: [notification, cron, multi-agent, roles, templates, dispatch]
category: productivity
---

# 角色驱动通知系统 v2

> Hermes cron 通知的角色化分发引擎。配置驱动、模板渲染、可激活、可聚合。
> 
> 控制中心：`~/.hermes/scripts/notification_config.json` — 改完即时生效，无需重启 cron。

## 架构

```
notification_config.json            ← 控制中心 (whitelist/blacklist/all/off)
    │
    ▼
notification_dispatcher.py          ← 引擎
    ├── is_role_active()            — 激活检查
    ├── should_notify()             — 冷却 + 恶化优先
    ├── check_services()            — 健康采集
    ├── get_child_snapshots()       — 聚合子角色
    ├── load_profile_soul()         — Profile 感知
    └── render_template()           — 模板引擎
           │
           ▼
    templates/<role>.md             ← 独立消息模板
```

## 操作

### 查看角色矩阵
```bash
cd ~/.hermes/scripts && python3 notification_dispatcher.py roles
```

### 切换角色激活

编辑 `~/.hermes/scripts/notification_config.json` 的 `control` 节：

| mode | 行为 |
|:--|:--|
| `whitelist` | 仅 `active_roles` 中的角色生效 |
| `blacklist` | 除 `paused_roles` 外全部生效 |
| `all` | 全部角色 |
| `off` | 全部关闭 |

### 修改模板

编辑 `templates/<role>.md`。支持三种语法：

| 语法 | 示例 | 说明 |
|:--|:--|:--|
| `{{var}}` | `{{greeting}}` | 简单变量替换 |
| `[?cond:text?]` | `[?has_unhealthy:🔴 断开?]` | 条件渲染：cond 为 true 输出 text |
| `{{#each list}}...{{/each}}` | `{{#each services}}{{status}} {{name}}{{/each}}` | 循环渲染 |

详见 `references/template-syntax.md`。

### 手动触发
```bash
python3 ~/.hermes/scripts/notification_dispatcher.py <role>
# 可用: origin | pm | tech | biz | ops | health | all | roles | config
```

### Cron 管理
```bash
hermes cron list                          # 查看所有
hermes cron edit <job_id>                 # 修改频率/交付
hermes cronjob action=run job_id=<id>     # 手动触发一次
```

## 现有 Cron

| Job ID | 名称 | 频率 | 模式 | 脚本 |
|:--|:--|:--|:--|:--|
| 9762e4ee746b | ⚓ 始祖舰队巡检 | 每120m | no_agent | `notification_dispatcher.py origin` |
| 164c020654bd | 🛡️ 健康巡检 | 每30m | no_agent | `notification_dispatcher.py health` |
| 724b352db633 | 🎯 PM日报(晨) | 每天9:00 | LLM | prompt |
| 3d8d64605b92 | 🎯 PM日报(暮) | 每天21:00 | LLM | prompt |
| a5981094038f | AutoDL 隧道监控 | 每2m | no_agent | `autodl_health.py` |
| 02bf73371e3f | 🎭 角色矩阵状态 | 每周一10:00 | LLM | prompt |

## 角色-Profile 绑定

| 角色 | emoji | Profile | 激活条件 | 聚合 |
|:--|:--|:--|:--|:--|
| 始祖 | ⚓ | default | 正常不通知 | ✅ 汇总所有子角色 |
| PM | 🎯 | badminton-pm, architect | 每天早晚必通知 | — |
| 技术 | 🔧 | ai-algorithm, ai-vision, frontend-dev, ops-engineer | 异常/每日摘要 | ✅ 聚合4子角色 |
| 商业 | 📊 | content-marketing, fundraising-pitch | 里程碑变更 | — |
| 运维 | 🛡️ | ops-engineer, security-compliance | 异常立即告警 | — |

## 结构化路由标签 (v2.1)

每条通知自动带 `[📦 项目] [角色emoji 角色名] [类别]` 前缀，由 `wrap_route(role, content)` 实现：

```
[📦 🦅 Apex] [⚓ 始祖·总指挥] [舰队列检]
{通知内容}
```

标签格式: `[📦 项目名] [emoji 角色名] [类别]`

## 通知策略（should_notify 优先级）

1. **恶化 (🟢→🔴)** — 立即通知，跳过冷却
2. **恢复 (🔴→🟢)** — 立即通知
3. **快照不变** — 跳过（除非角色配置了 `on_green: true`）
4. **冷却期内** — 跳过

## 陷阱

### 模板渲染
- 条件块内的分隔符（`---`）必须包在 `[?...?]` 内部，否则无条件渲染
- 模板顶部避免写含 `{{var}}` 的注释行，会被误解析
- `[?...?]` 正则使用 `re.DOTALL`，条件文本可跨行但 `?]` 必须唯一

### 激活/冷却
- 新角色首次运行无 `last_snapshot`，会触发通知（正确行为）
- `notify_health()` 走 v1 兼容逻辑，不受角色配置控制
- PM 晨/暮报是 LLM 驱动 cron，非 no_agent，不在此脚本引擎范围内

### 运行时
- **状态文件残留**: 测试前 `rm -f ~/.hermes/notification_state/*.json` 避免冷却期屏蔽通知
- **Dashboard 未启动**: `check_dashboard()` / `check_services()` 会静默返回空，不影响通知输出

## 添加新角色

1. `notification_config.json` → `roles` 添加定义
2. 创建 `templates/<role>.md`
3. 在 `notification_dispatcher.py` 添加 `notify_<role>()` 函数
4. `main()` 添加路由
5. 创建 cron job

## 相关文档
- 完整文档：`~/Desktop/2026AIAPP/Apex/docs/notification-system.md`
- 模板语法：`references/template-syntax.md`
