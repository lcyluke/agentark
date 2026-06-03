# 角色驱动通知系统

## 架构

```
notification_dispatcher.py (no_agent脚本)
    ├── origin   → 始祖舰队巡检 (每2h, 异常才通知)
    ├── health   → 全局健康巡检 (每30m, 异常才通知)
    └── (LLM驱动) PM 晨/暮报 (每天9:00 + 21:00, 必须通知)
```

## 角色-关注点矩阵

| 角色 | Emoji | Profile | 关注点 | 通知策略 |
|:--|:--|:--|:--|:--|
| 始祖Agent | ⚓ | default | 舰队总览/战略里程碑/跨项目阻塞/资源分配 | 每2h巡检, 正常不通知 |
| 项目PM | 🎯 | yuji-pm, architect | 任务进度/阻塞项/燃尽率/Sprint状态 | 每天9:00+21:00, 必须通知 |
| 技术专项 | 🔧 | ai-algorithm, ai-vision, frontend-dev, ops-engineer | 构建/测试/部署/API健康 | 每天9:00摘要, 异常实时告警 |
| 商业/内容 | 📊 | content-marketing, fundraising-pitch | 用户增长/转化/内容计划/融资 | 每周一10:00, 有变更才通知 |
| 运维/安全 | 🛡️ | ops-engineer, security-compliance | 服务器/安全漏洞/备份/成本 | 每天9:00摘要, 异常实时告警 |

## Cron 清单

| ID | 名称 | 角色 | 频率 | 模式 |
|:--|:--|:--|:--|:--|
| 9762e4ee746b | ⚓ 始祖舰队巡检 | origin | 每2h | no_agent |
| 164c020654bd | 🛡️ 健康巡检 | health | 每30m | no_agent |
| a5981094038f | AutoDL 隧道健康监控 | health | 每2m | no_agent |
| 724b352db633 | 🎯 羽球宝PM日报(晨) | pm | 每天9:00 | LLM |
| 3d8d64605b92 | 🎯 羽球宝PM日报(暮) | pm | 每天21:00 | LLM |
| 3cd6b26ea9df | apex-bridge-sync | sync | 每5m | LLM→local |

## 静默规则

- **始祖巡检**: 所有服务🟢 + 无Cron异常 → 4小时内不重复通知
- **健康巡检**: 全部服务🟢 → 不通知; 断开 → 10分钟冷却
- **AutoDL监控**: 同状态300秒冷却; 恢复立即通知
- **PM日报**: 永远通知 (每天不打扰)
- **Bridge同步**: local模式 (不推送微信)

## 调整方法

```bash
# 查看所有cron
hermes cron list

# 修改频率
hermes cron edit <id>    # 交互式修改 schedule

# 修改角色通知规则
vi ~/.hermes/scripts/notification_dispatcher.py
# 编辑 ROLES 字典中的 silence_rule / cadence

# 添加新角色
# 在 ROLES 中定义, 在脚本尾部添加 notify_xxx() 函数
# 然后 hermes cron create ... --script notification_dispatcher.py xxx
```

## 已删除的旧Job

| ID | 名称 | 原因 |
|:--|:--|:--|
| eaf1eb1033a1 | autodl-complete-and-report | prompt中含明文密码 |
| d99c98baf69c | autodl-batch-progress | prompt中含明文密码 |
