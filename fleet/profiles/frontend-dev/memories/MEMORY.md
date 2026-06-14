Apex项目位于 /Users/Mac/Desktop/2026AIAPP/Apex，Web dashboard 通过 `python -m apex dashboard --port 8080` 启动。命令中心CC页面模板位于 apex/interface/templates/command_center.html（1755行），后端API在 apex/interface/web.py（Flask）。实时状态模块在 apex/interface/live_status.py。参考设计文件在 /Users/Mac/Downloads/AgentCorp-OS/AgentCorp-OS.html。
§
Apex `/api/ops/agents/workloads` 返回 `{agents: [...], summary: {...}, total_active_tasks: N, total_agents: N}` 而非纯数组。前端所有 `.filter()` / `.length` / `.slice()` 调用前必须做 `data.workloads?.agents || []` 化解。同样 `/api/fleet/teams/list` 返回 `{teams: {}, updated_at: ...}` 而非数组。Dashboard渲染前必须检查数据类型。
§
Apex项目运行在 /Users/Mac/Desktop/2026AIAPP/Apex，使用 Flask + .venv。`python -m apex dashboard --port 8080` 启动。注意：$HERMES_HOME 有时指向 /Users/Mac/.hermes/profiles/frontend-dev 而非 /Users/Mac/.hermes，导致 fleet_teams.json 读取路径错误。修复方法：复制 fleet_teams.json 到 HERMES_HOME 实际指向的目录。
§
Apex CLI 命令已安装到 ~/.local/bin/apex。所有apex命令现在可直接使用 `apex <command>` 而无需 `python -m apex` 前缀。项目路径: /Users/Mac/Desktop/2026AIAPP/Apex。venv路径: .venv/bin/python。