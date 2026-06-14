# Multi-Mac Apex Fleet Architecture v2 (Single Repo)

## Architecture

```
lcyluke/apex (唯一仓库)
├── apex/                    ← Python 代码 (fleet_multi_mac.py)
├── scripts/fleet-join-worker.sh  ← Worker 一键入列脚本
├── docs/fleet-mac-b-join-guide.md ← 入列指南
└── fleet/                   ← 舰队配置中心
    ├── config.yaml          ← Hermes 配置 (DeepSeek V4 Pro)
    ├── SOUL.md              ← Origin 人格定义
    ├── skills/              ← ~/.hermes/skills/ 同步副本
    ├── profiles/            ← ~/.hermes/profiles/ 同步副本
    └── nodes/               ← 各节点心跳 JSON
        ├── Mac-A-hostname.json
        └── Mac-B-hostname.json

  Mac-A (Origin) ←── git push/pull ──→ Mac-B (Worker)
```

## Node Roles

| Role | Machine | Runs | Can't do |
|------|---------|------|----------|
| ⚓ Origin | Mac-A | cron (all jobs), Dashboard, 授权引擎, WeChat通知 | — |
| 🔧 Worker | Mac-B | 项目开发, GPU训练, fleet report 心跳 | cron, 授权审批 |

## Sync Flow

```
Worker:   fleet_status() → nvidia-smi→GPU数据 → nodes/<id>.json → git push
Origin:   git pull → 读 nodes/*.json → fleet nodes/gpu-status 展示
Alert:    GPU >90% / <30% → fleet_report 输出告警 → cron投递WeChat
```

## Key Design Rules

1. **单仓库**: 所有舰队功能集成在 lcyluke/apex 内。禁止拆分配置仓库。
2. **fleet/ 是唯一配置源**: Worker 从 Apex repo 的 fleet/ 拉配置，同步到 ~/.hermes/。
3. **状态通过 git**: 节点心跳写入 fleet/nodes/<id>.json → git push → Origin pull 可见。
4. **GPU 是节点属性**: GPU 监控不是独立脚本，是 fleet_status() 的一部分。
5. **Worker 不跑 cron**: cron 只在 Origin 上运行。Worker 靠 fleet report 被动上报。

## Code Map

| File | Lines | Role |
|------|-------|------|
| `apex/interface/fleet_multi_mac.py` | ~500 | 后端引擎: _probe_gpu, _gpu_alerts, fleet_status, fleet_report, fleet_sync |
| `apex/cli/commands/fleet_cmds.py` | +200 | CLI 命令: fleet_init/join/report/nodes/gpu_status/sync |
| `apex/cli/main.py` | +40 | Click 命令注册 |
| `scripts/fleet-join-worker.sh` | 160 | Mac-B 一键入列 (免 Apex CLI) |

## CLI Commands

```bash
apex fleet init-fleet [-n "舰队名"]          # Origin 初始化
apex fleet join-fleet                        # Worker 加入
apex fleet report                            # 心跳+GPU上报 (cron驱动)
apex fleet nodes                             # 全舰队节点 (含GPU列)
apex fleet gpu-status                        # GPU资源中心
apex fleet sync --pull|--push                # 配置双向同步
```

## Worker One-Liner

```bash
curl -fsSL https://raw.githubusercontent.com/lcyluke/apex/main/scripts/fleet-join-worker.sh | bash
```

## Pitfalls

- **`HERMES_HOME` 被 profile 覆盖**: Apex venv 中 `HERMES_HOME` 指向 profile 目录。fleet 代码必须用 `Path(os.path.expanduser("~/.hermes"))` 硬编码。
- **`git add -A` 会引入 node_modules**: 使用 `git add fleet/` 精确提交。
- **Worker cron 禁用**: Worker 的 `~/.hermes/cron/jobs.json` 可复制但不应启动。
- **GPU 空闲检测用时间戳**: 不是累加计数器，避免 cron 间隔变化时误报。
