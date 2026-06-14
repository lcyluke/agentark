# Structured Output Format Specification

## Standard format

Every routed message follows this pattern:

```
[📦 {project_emoji} {project_name}] [{agent_emoji} {agent_role}] [{category}]
{content}
```

## Components

| Field | Source | Example |
|:--|:--|:--|
| `project_emoji` | PROJECTS dict | 🏸 🦅 🗺️ |
| `project_name` | PROJECTS dict | 羽球宝AI搭子 |
| `agent_emoji` | AGENT_EMOJI dict | 🧠 🎯 🔧 |
| `agent_role` | AGENT_ROLE dict | 算法专家 |
| `category` | CATEGORY_EMOJI dict | AI/ML |

## Integration points

1. **notification_dispatcher.py v2.1** — `ROUTE_BY_ROLE` dict maps each cron role (origin/pm/tech/biz/ops/health) to a fixed route tag. Every notification output is auto-wrapped via `wrap_route(role, content)`.

2. **Hermes response** — When loaded as a skill, the agent prepends the route tag to every reply. The tag is always on its own line, followed by a blank line, then the actual response.

3. **Apex Dashboard API** — `RouteResult.format_output(content)` generates the tagged string programmatically.

## Example outputs

```
[📦 🏸 羽球宝AI搭子] [🧠 算法专家] [AI/ML]
骨骼标注模型准确率分析...

[📦 🦅 Apex] [⚓ 始祖·总指挥] [舰队列检]
06月03日 13:05 · 舰队全域简报...

[📦 🗺️ 深圳羽球地图] [✍️ 内容推广] [content]
公众号文章推广方案...

[📦 🦅 Apex] [🛡️ 健康巡检] [服务健康]
🔴 已断开: apex-dashboard, autodl-inference
```
