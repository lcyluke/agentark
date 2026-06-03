# 角色驱动通知系统 v2

## 架构升级

```
v1 (旧)                          v2 (新)
══════════                       ═══════════
硬编码 ROLES 字典                notification_config.json ← 控制中心
notify_*() 固定格式              templates/<role>.md     ← 独立模板
无激活/暂停                      白名单/黑名单/全开/全关
无 Profile 感知                  读取 SOUL.md 注入角色个性
无聚合                           始祖可汇总子角色快照
```

## 文件清单

```
~/.hermes/scripts/
├── notification_config.json      ← 控制中心 (改完即时生效)
├── notification_dispatcher.py    ← v2 引擎
└── templates/
    ├── origin.md                 ← 始祖格式
    ├── pm.md                     ← PM格式
    ├── tech.md                   ← 技术格式
    ├── biz.md                    ← 商业格式
    └── ops.md                    ← 运维格式

~/.hermes/notification_state/
└── <role>.json                   ← 自动生成的状态文件
```

## 操作手册

### 查看角色矩阵
```bash
cd ~/.hermes/scripts && python3 notification_dispatcher.py roles
```

输出:
```
  始祖Agent      ⚓      default                        ✅  🔗聚合
  项目PM         🎯      yuji-pm, architect             ✅
  技术专项       🔧      ai-algorithm, ...              ⭕  🔗聚合
  商业/内容      📊      content-marketing, ...         ⭕
  运维/安全      🛡️     ops-engineer, security          ⭕
```

### 切换角色激活

编辑 `notification_config.json` → `control` 部分:

```json
{
  "control": {
    "mode": "whitelist",
    "active_roles": ["origin", "pm", "health"],
    "paused_roles": ["tech", "biz", "ops"]
  }
}
```

四种模式:
- `whitelist` — 仅 `active_roles` 生效
- `blacklist` — 除 `paused_roles` 外全开
- `all` — 全部角色
- `off` — 全部关闭

### 修改模板

编辑 `templates/<role>.md`，支持:
- `{{var}}` — 变量替换
- `[?cond:text?]` — 条件渲染
- `{{#each list}}...{{/each}}` — 循环

### 手动触发测试
```bash
python3 notification_dispatcher.py origin    # 始祖
python3 notification_dispatcher.py pm        # PM
python3 notification_dispatcher.py tech      # 技术
python3 notification_dispatcher.py biz       # 商业
python3 notification_dispatcher.py ops       # 运维
python3 notification_dispatcher.py health    # 健康巡检
python3 notification_dispatcher.py all       # 全部
```

### Cron 清单

| Job ID | 名称 | 频率 | 模式 |
|:--|:--|:--|:--|
| 9762e4ee746b | ⚓ 始祖舰队巡检 | 每120m | no_agent |
| 164c020654bd | 🛡️ 健康巡检 | 每30m | no_agent |
| 724b352db633 | 🎯 PM日报(晨) | 每天9:00 | LLM |
| 3d8d64605b92 | 🎯 PM日报(暮) | 每天21:00 | LLM |
| a5981094038f | AutoDL 隧道监控 | 每2m | no_agent |
| 02bf73371e3f | 🎭 角色矩阵状态 | 每周一10:00 | LLM |

## 角色-Profile 绑定

| 角色 | emoji | 关联 Profile | 激活 |
|:--|:--|:--|:--|
| 始祖Agent | ⚓ | default | ✅ |
| 项目PM | 🎯 | yuji-pm, architect | ✅ |
| 技术专项 | 🔧 | ai-algorithm, ai-vision, frontend-dev, ops-engineer | ⭕ |
| 商业/内容 | 📊 | content-marketing, fundraising-pitch | ⭕ |
| 运维/安全 | 🛡️ | ops-engineer, security-compliance | ⭕ |

## 通知策略

- **恶化(🟢→🔴)** — 立即通知，跳过冷却
- **恢复(🔴→🟢)** — 立即通知
- **稳定正常** — 冷却期内不重复 (默认4h)
- **稳定异常** — 冷却期内不重复 (默认10min)
