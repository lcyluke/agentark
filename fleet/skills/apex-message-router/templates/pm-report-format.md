# 多项目 PM 日报模板

## 使用方式

Hermes cron LLM 模式，prompt 中指定项目上下文，输出按此格式。

## 模板

```
{{timestamp}}

🎯 **{{project_name}}** · {{report_type}}报

---

## 📊 进展

### Sprint 状态
| 指标 | 值 |
|:--|:--|
| 当前 Sprint | {{sprint_name}} |
| 进度 | {{progress_bar}} {{progress_pct}}% |
| 燃尽 | {{burndown_status}} |
| 阻塞项 | {{blocked_count}} |

### 🔄 进行中
- {{icon}} {{title}} ({{assignee}})

### ✅ 已完成
- ✅ {{title}}

---

## 🎯 待决策

🔔 **需拍板事项**
- 背景: {{context}}
- 选项: {{options}}
- 建议: {{recommendation}}
- ⏰ 时效: {{deadline}}

---

## ⚠️ 风险

| 等级 | 风险 | 影响 | 缓解措施 |
|:--|:--|:--|:--|
| 🔴 | {{title}} | {{impact}} | {{mitigation}} |
| 🟡 | {{title}} | {{impact}} | {{mitigation}} |

---
> 🎯 下次{{report_type}}报: {{next_report}} · {{agent_signature}}
```

## Cron prompt 示例

```
你是{项目名}项目的 PM Agent。请准备一份简短的项目日报。

📊 进展: 用 session_search 查看最近24小时开发进展
🎯 待决策: 需要老卢拍板的事项
⚠️ 风险: 阻塞/延期/技术债

输出标签: [📦 {emoji} {项目名}] [🎯 PM] [项目管理]
不超过10行，老卢在微信上看。
```

## 当前部署

| Cron ID | 项目 | 频率 |
|:--|:--|:--|
| b642e372b679 | 🏸 羽球宝AI搭子 | 每天 9:30 |
| 724b352db633 | 🏸 羽球宝AI搭子 (暮报) | 每天 21:00 |
| a646bf3a76ce | 🦅 Apex Dashboard | 每天 10:00 |
| b90b6293fddd | 🗺️ 深圳羽球地图 | 每周一 10:00 |
