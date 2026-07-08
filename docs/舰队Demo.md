# 老卢舰队 — Demo 演示文档

> 跨机器多Agent舰队 — 一台Origin + N台Worker，LAN发现 + GitHub同步双通道，资源感知调度

---

## 架构图

```mermaid
graph TB
    subgraph Mac-A["🖥️ Mac-A (Origin) — lusPro.local"]
        direction TB
        TMUX["tmux: agentark-fleet<br/>7 Agent窗口"]
        CLI["agentark CLI<br/>fleet status / nodes / dispatch"]
        DASH["Dashboard :8765<br/>实时监控面板"]
        CRON["Cron集群<br/>心跳 / 健康扫描 / 调度"]
        
        TMUX --> CLI
        CLI --> DASH
        CRON --> TMUX
        CRON --> DASH
    end

    subgraph LAN["📡 LAN通道 (mDNS + SSH)"]
        MDNS["mDNS发现<br/>_agentark-fleet._tcp.local."]
        SSH["SSH调度<br/>agentark fleet dispatch"]
    end

    subgraph GIT["☁️ GitHub通道"]
        SYNC["git push/pull<br/>fleet/nodes/*.json<br/>心跳同步"]
    end

    subgraph Mac-B["🖥️ Mac-B (Worker)"]
        B_HEART["每2分钟心跳<br/>fleet_heartbeat.py"]
        B_PROBE["资源探测<br/>CPU/GPU/RAM/Disk"]
        B_AGENT["Hermes Agent<br/>接收SSH调度"]
    end

    subgraph Mac-Mini["🖥️ Mac-mini (Worker)"]
        M_HEART["每2分钟心跳<br/>fleet_heartbeat.py"]
        M_PROBE["资源探测<br/>CPU/GPU/RAM/Disk"]
        M_AGENT["Hermes Agent<br/>接收SSH调度"]
    end

    subgraph GB10["🖥️ GB10 (GPU Worker)"]
        G_GPU["NVIDIA GPU<br/>Ollama模型推理"]
        G_TRAIN["ML训练任务<br/>VideoMAE / RTMPose"]
        G_SSH["SSH隧道保活<br/>每2分钟cron"]
    end

    Mac-A -->|"LAN发现"| LAN
    LAN -->|"SSH"| Mac-B
    LAN -->|"SSH"| Mac-Mini
    Mac-A -->|"双通道同步"| GIT
    
    Mac-B -->|"心跳上报"| GIT
    Mac-Mini -->|"心跳上报"| GIT
    Mac-A -->|"SSH隧道"| GB10
```

## 舰队拓扑

```mermaid
graph LR
    subgraph Origin["⚓ Origin: lusPro.local (Mac-A)"]
        O1["7 Agent tmux"]
        O2["Dashboard :8765"]
        O3["Cron: 29个定时任务"]
    end
    
    subgraph Workers["Worker节点"]
        W1["Mac-B<br/>CPU任务"]
        W2["Mac-mini<br/>轻量任务"]
        W3["GB10<br/>GPU训练"]
    end
    
    Origin -->|"agentark fleet dispatch"| Workers
    Workers -->|"心跳每2分钟"| Origin
```

## 5分钟Demo演示

```bash
# ===== Step 1: 舰队状态总览 =====
agentark fleet status
# 输出：45 agents, 4 项目, 7 tmux窗口, 101 技能

# ===== Step 2: 查看所有节点 =====
agentark fleet nodes
# 输出：5台节点（含时间戳、角色、心跳状态）

# ===== Step 3: LAN发现邻居 =====
agentark fleet lan scan
# 输出：4秒内发现局域网内所有Worker节点

# ===== Step 4: 本机资源探测 =====
agentark fleet probe
# 输出：CPU 16核、64GB RAM、1TB 磁盘、Apple M4 GPU

# ===== Step 5: 干跑任务调度 =====
agentark fleet dispatch "分析用户数据" --cpu-cores 8 --dry-run
# 输出：评分矩阵，显示哪个节点最适合执行

# ===== Step 6: Dashboard实时监控 =====
open http://localhost:8765
# 展示：Token用量、Agent进程、Claude会话、14天趋势图
```

## 舰队命令速查

```
┌─────────────────────────────────────────────────────────────────────┐
│  🚢 舰队管理 (Fleet Management)                                       │
├─────────────────────────────────────────────────────────────────────┤
│  agentark fleet status                   舰队全局状态                  │
│  agentark fleet nodes                    节点列表(角色/心跳/项目)       │
│  agentark fleet probe                    本机硬件探测                   │
│  agentark fleet init-fleet               初始化Origin舰队               │
│  agentark fleet init                     启动tmux多Agent舰队            │
├─────────────────────────────────────────────────────────────────────┤
│  📡 LAN组网                                                            │
├─────────────────────────────────────────────────────────────────────┤
│  agentark fleet lan scan                 快速扫描LAN邻居(4秒)           │
│  agentark fleet lan discover             持续发现(后台运行)             │
│  agentark fleet dispatch <task> [flags]  跨机器任务调度                │
│    --gpu                                  需要GPU                     │
│    --gpu-memory-mb <MB>                   GPU显存要求                  │
│    --cpu-cores <N>                        CPU核心要求                  │
│    --ram-mb <MB>                          内存要求                    │
│    --target <hostname>                    指定目标机器                  │
│    --dry-run                              干跑(只评分不执行)            │
│  agentark fleet queue                    查看任务队列                  │
├─────────────────────────────────────────────────────────────────────┤
│  🖥️ tmux舰队操作                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  tmux attach -t agentark-fleet                附加到舰队终端                │
│  tmux detach (Ctrl+B d)                   分离会话                     │
│  tmux list-windows -t agentark-fleet          列出所有Agent窗口             │
│  tmux send-keys -t agentark-fleet:pm "任务"   派发任务给PM                  │
│  tmux capture-pane -t agentark-fleet:pm -S -20 读取最后20行输出            │
│  tmux kill-window -t agentark-fleet:agent     关闭单个Agent                │
│  tmux kill-session -t agentark-fleet          关闭整个舰队                  │
└─────────────────────────────────────────────────────────────────────┘
```

## 调度评分算法

```mermaid
graph TD
    START([接收任务]) --> PARSE[解析资源需求]
    PARSE --> PROBE[探测所有在线节点]
    PROBE --> HARD{硬约束检查}
    
    HARD -->|GPU不满足| ZERO[分数归零]
    HARD -->|显存不足| ZERO
    HARD -->|CPU不足| ZERO
    HARD -->|OS不匹配| ZERO
    HARD -->|Docker缺失| ZERO
    
    HARD -->|全部通过| SCORE[加权评分]
    
    subgraph SCORES["评分权重"]
        G1["GPU匹配: 40%"]
        G2["CPU空闲: 25%"]
        G3["RAM空闲: 15%"]
        G4["当前负载: 10%"]
        G5["LAN延迟: 10%"]
    end
    
    SCORE --> BEST[选最高分节点]
    BEST --> DISPATCH{节点可达?}
    DISPATCH -->|LAN可达| SSH_DISPATCH["SSH直接调度<br/>ssh host 'hermes chat task'"]
    DISPATCH -->|不可达| QUEUE["写入任务队列<br/>~/.apex/task_queue.json"]
    
    SSH_DISPATCH --> DONE([完成])
    QUEUE --> DONE
```

## 健康监控拓扑

```mermaid
sequenceDiagram
    participant Cron as Cron调度器
    participant Tmux as tmux舰队
    participant Dash as Dashboard :8765
    participant Gh as GitHub
    participant LK as 老卢 (IM)
    
    loop 每10分钟
        Cron->>Tmux: tmux list-windows
        Tmux-->>Cron: 7个窗口正常
        Cron->>Dash: curl /api/health
        Dash-->>Cron: HTTP 200
    end
    
    Note over Cron: SILENT — 一切正常

    alt Agent离线
        Cron->>Tmux: 窗口缺失
        Tmux-->>Cron: ERROR: 只有5个窗口
        Cron->>Cron: 自动重启缺失Agent
        Cron-->>Gh: 记录日志到fleet/nodes/
    end

    alt Dashboard宕机
        Cron->>Dash: curl超时
        Dash--x Cron: 无响应
        Cron-->>LK: 🚨 IM告警: Dashboard挂了！
    end
    
    loop 每2分钟
        Cron->>Cron: mDNS扫描 + SSH测试 + 资源探测
        Cron->>Gh: git push fleet/nodes/*.json
    end
```

## 实际运行截图（文字版）

```
$ agentark fleet nodes

  ⚓ 老卢舰队 ──── 5 节点

  ⚓  lusPro.local-luke ◀     ORIGIN  badminton-coac…  活跃  2026-07-04T00:00
                                       apex, finopsai
  💻  MacBook-Pro-2.…      WORKER  finopsai          上次  2026-06-28T23:00
                                       badminton-coac…
  💻  GB10.local-root       WORKER  gb10              上次  2026-06-28T22:45
  💻  parser-ubuntu.local   WORKER  badminton-coac…   上次  2026-06-28T21:30
  💻  parsimo-mac.local     WORKER  finopsai          上次  2026-06-28T20:15

  当前机器: lusPro.local-luke  角色: ORIGIN
```

```
$ agentark fleet status

  ⚓ 老卢舰队
  Agents: 45 total · 7 运行中 · 0 任务执行中
  项目:   4 (badminton-coach-ai, apex, finopsai, shenzhen-badminton)
  技能:   101
  节点:   5 (1 Origin · 4 Worker)
  心跳:   LAN ✅ · GitHub ⚠ (上次同步: 5分钟前)
```

## 舰队启动脚本（一键部署）

```bash
#!/bin/bash
# fleet-start.sh — 一键启动老卢舰队
set -e

AGENTS=(pm architect backend-dev frontend-dev devops qa-engineer github-release)
SESSION="agentark-fleet"
HERMES_BIN="hermes"

# 1. 杀旧舰队（如果存在）
tmux kill-session -t "$SESSION" 2>/dev/null || true

# 2. 创建新舰队
tmux new-session -d -s "$SESSION" -n "${AGENTS[0]}" -x 160 -y 40 \
  "$HERMES_BIN -p ${AGENTS[0]} chat"
echo "✅ 创建窗口: ${AGENTS[0]}"

# 3. 添加其余Agent
for agent in "${AGENTS[@]:1}"; do
  tmux new-window -t "$SESSION" -n "$agent" "$HERMES_BIN -p $agent chat"
  echo "✅ 创建窗口: $agent"
done

# 4. 验证
WINDOW_COUNT=$(tmux list-windows -t "$SESSION" | wc -l)
PROC_COUNT=$(ps aux | grep "hermes -p" | grep -v grep | wc -l)
echo ""
echo "🎉 老卢舰队已启动！"
echo "   窗口数: $WINDOW_COUNT"
echo "   进程数: $PROC_COUNT"
echo "   附加:   tmux attach -t $SESSION"
```

## 关键文件

| 文件 | 说明 |
|------|------|
| `docs/舰队运维手册.md` | 完整运维文档（8章） |
| `docs/舰队Demo.md` | 本文档（演示素材） |
| `fleet/fleet.json` | 舰队全局配置 |
| `fleet/nodes/*.json` | 节点心跳JSON |
| `scripts/fleet_heartbeat.py` | 双通道心跳脚本 |
| `scripts/gb10_tunnel_keepalive.sh` | GB10 SSH隧道保活 |

---

📖 完整文档: [docs/舰队运维手册.md](舰队运维手册.md)
