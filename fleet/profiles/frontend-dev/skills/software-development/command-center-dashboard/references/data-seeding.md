# Apex Dashboard Data Seeding Reference

## Quick Seed: Full Fleet + Tasks + Knowledge

Run while Flask server is on port 8080. Seeds 6 agents, 8 tasks, 5 knowledge nodes, 3 teams.

### Profiles (6 agents)

```bash
BASE="http://localhost:8080"
for data in \
  '{"name":"frontend-dev","role":"Frontend Developer","skills":["react","typescript","tailwind","vitest"],"model":"deepseek-v4-pro"}' \
  '{"name":"devops","role":"DevOps Engineer","skills":["docker","kubernetes","github-actions"],"model":"deepseek-v4-pro"}' \
  '{"name":"qa-agent","role":"QA Tester","skills":["playwright","vitest","jest"],"model":"deepseek-v4-pro"}' \
  '{"name":"backend-dev","role":"Backend Developer","skills":["python","fastapi","postgres"],"model":"deepseek-v4-pro"}' \
  '{"name":"data-analyst","role":"Data Analyst","skills":["sql","pandas","numpy"],"model":"deepseek-v4-pro"}' \
  '{"name":"security-auditor","role":"Security Auditor","skills":["owasp","sast","dast"],"model":"deepseek-v4-pro"}'
do
  curl -s -X POST "$BASE/api/profiles" -H 'Content-Type: application/json' -d "$data"
done
```

### Tasks (8 tasks, 3 projects)

```bash
TASKS=(
  '{"title":"[羽球宝AI] 用户注册登录页面","assignee":"frontend-dev","priority":1}'
  '{"title":"[羽球宝AI] 球场预约API接口","assignee":"backend-dev","priority":1}'
  '{"title":"[羽球宝AI] 集成测试用例编写","assignee":"qa-agent","priority":2}'
  '{"title":"[羽球宝AI] CI/CD Pipeline配置","assignee":"devops","priority":1}'
  '{"title":"[Apex] 多Agent调度优化","assignee":"backend-dev","priority":2}'
  '{"title":"[Apex] Dashboard性能优化","assignee":"frontend-dev","priority":2}'
  '{"title":"[深圳羽球地图] 场馆数据爬虫","assignee":"data-analyst","priority":3}'
  '{"title":"[深圳羽球地图] API安全审计","assignee":"security-auditor","priority":2}'
)
for t in "${TASKS[@]}"; do
  curl -s -X POST "$BASE/api/tasks" -H 'Content-Type: application/json' -d "$t"
done
```

### Knowledge Graph Seeds

```bash
for entity in "羽毛球AI助手" "深圳羽毛球馆地图" "Apex多Agent操作系统" "Agent编排调度" "快速开发工作流"; do
  curl -s -X POST "$BASE/api/knowledge" -H 'Content-Type: application/json' \
    -d "{\"action\":\"learn\",\"entity\":\"$entity\",\"source\":\"seed\"}"
done
```

### Fleet Teams (fleet_teams.json)

Write to the path resolved by the Flask server's `HERMES_HOME` + `/fleet_teams.json`:

```json
{
  "teams": {
    "羽球宝AI": {
      "name": "羽球宝AI",
      "project": "羽球宝AI",
      "members": [
        {"agent_id": "frontend-dev", "role": "Frontend", "profile_type": "apex"},
        {"agent_id": "backend-dev", "role": "Backend", "profile_type": "apex"},
        {"agent_id": "qa-agent", "role": "QA", "profile_type": "apex"},
        {"agent_id": "devops", "role": "DevOps", "profile_type": "apex"}
      ]
    },
    "Apex": {
      "name": "Apex",
      "project": "Apex",
      "members": [
        {"agent_id": "frontend-dev", "role": "Frontend Architect", "profile_type": "apex"},
        {"agent_id": "backend-dev", "role": "Core Engine", "profile_type": "apex"},
        {"agent_id": "security-auditor", "role": "Security", "profile_type": "apex"}
      ]
    },
    "深圳羽球地图": {
      "name": "深圳羽球地图",
      "project": "深圳羽球地图",
      "members": [
        {"agent_id": "data-analyst", "role": "Data Pipeline", "profile_type": "apex"},
        {"agent_id": "security-auditor", "role": "Security Audit", "profile_type": "apex"}
      ]
    }
  },
  "updated_at": "2026-06-04T00:00:00"
}
```

### Verification

```bash
echo "=== Profiles ===" && curl -s $BASE/api/profiles | python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d),'profiles')"
echo "=== Tasks ===" && curl -s $BASE/api/tasks | python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d),'tasks')"
echo "=== Knowledge ===" && curl -s $BASE/api/knowledge | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('nodes'),'nodes')"
echo "=== Teams ===" && curl -s $BASE/api/fleet/teams/list | python3 -c "import sys,json;d=json.load(sys.stdin);t=d.get('teams',{});print(len(t),'teams:',list(t.keys()))"
echo "=== Live Projects ===" && curl -s $BASE/api/live/projects | python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d),'projects')"
echo "=== Workloads ===" && curl -s $BASE/api/ops/agents/workloads | python3 -c "import sys,json;d=json.load(sys.stdin);a=d.get('agents',[]);print(len(a),'agents')"
```

Expected output after seeding:
```
6 profiles
8+ tasks  (11 if demo tasks exist)
5 nodes
3 teams: ['Apex', '深圳羽球地图', '羽球宝AI']
4 projects
7 agents
```

## API Shape Notes

| Endpoint | Type | Key Field |
|----------|------|-----------|
| `/api/profiles` | `[...]` array | `.name`, `.role`, `.skills[]` |
| `/api/tasks` | `[...]` array | `.title`, `.assignee`, `.status` |
| `/api/knowledge` | `{nodes, edges, distribution}` object | `.nodes` |
| `/api/ops/agents/workloads` | `{agents:[], summary:{}}` object ⚠️ | `.agents[]` (not bare array!) |
| `/api/live/projects` | `[...]` array | `.name`, `.task_count` |
| `/api/fleet/teams/list` | `{teams:{}, updated_at}` object | `.teams` |
| `/api/autonomous` | `{status, knowledge_nodes, ...}` object | `.status` |
