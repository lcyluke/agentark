---
name: monitoring-system
description: "羽球宝AI搭子全球大师级成本控制中心 — GPU/训练/成本/预警/闲时自动关机/看板一键关机，以省成本为核心设计"
version: 2.0.0
author: 小卢 (Hermes AI)
tags: [monitoring, gpu, cost, auto-shutdown, dashboard, gpu-management]
---

# 🚀 成本控制中心使用指南

> **设计哲学：不是监控工具，是省钱工具。每一分钟空闲都是浪费。**

## 目录
`~/Desktop/2026AIAPP/monitor/`

## 架构

```
用户 → Streamlit 看板 (:8050)    微信推送 (Hermes Bridge)
        ↑                               ↑
        │                               │
    ┌───┴───────────────┬───────────────┴───┐
    │   GPU 采集 Agent    │  智能关机引擎      │
    │  (gpu_monitor.py)  │  (auto_shutdown)  │
    └────────┬──────────┘ └────────┬─────────┘
             │                     │
    ┌────────▼──────────┐  ┌──────▼──────────┐
    │  SQLite DB        │  │ SSH 控制器       │
    │  (monitor.db)     │  │ (ssh_manager.py) │
    └───────────────────┘  └─────────────────┘
```

## 核心功能

### 成本时钟
- 总运行时间 + 总费用实时累计
- 今日费用（按日清零）
- 每分钟成本显示（¥0.08/分钟 on 4090）
- 实例每多开一分钟 = 多花 XX 元

### 闲时倒计时
- GPU 利用率 < 5% 视为空闲
- 进度条显示：距离自动关机还有多少分钟
- 「已浪费 ¥XX」提示
- 当前空闲/已运行比例

### 一键关机
- 看板上直接点「⛔ 立即关机」
- 通过 SSH 发送 `autodl shutdown` 指令
- 关机后看板自动显示「实例离线」

### 自动关机策略（硬编码阈值）
| 状态 | 动作 | 说明 |
|:---|:---|:---|
| 🟡 空闲 15 分钟 | 微信提醒 | "GPU 空闲中，训练完请关机" |
| 🟠 空闲 25 分钟 | 紧急微信提醒 | "再 5 分钟自动关机" |
| 🔴 空闲 30 分钟 | **自动关机** | 无需人工干预，微信通知 |

### GPU 利用率全景
- 24小时利用率 + 显存 + 温度历史曲线
- 平均利用率、峰值、空闲占比统计
- 温度红线 85°C

## 组件清单

| 文件 | 功能 | 运行位置 |
|:-----|:-----|:---------|
| `dashboards/monitor_app.py` | Streamlit 看板 v2（成本控制版） | AutoDL 服务器 |
| `agents/gpu_monitor.py` | GPU+系统指标采集（5秒间隔） | AutoDL 服务器 |
| `agents/ssh_manager.py` | SSH 远程控制（关机/状态查询） | Mac / 看板 |
| `agents/query_idle.py` | 查询GPU空闲分钟数 | AutoDL 服务器 |
| `agents/query_cost.py` | 查询成本和运行时间 | AutoDL 服务器 |
| `agents/query_history.py` | 查询24小时历史数据 | AutoDL 服务器 |
| `agents/cost_tracker.py` | 本地成本报告 | Mac |
| `alerts/auto_shutdown.py` | 智能关机引擎（微信推送+自动关机） | AutoDL 服务器 |
| `agents/hermes_bridge.py` | 微信推送桥 | Mac |
| `config/settings.yaml` | 全局配置 | Mac |

## 启动

### 首次部署到 AutoDL（一次性）
```bash
cd ~/Desktop/2026AIAPP/monitor

# 1. 发送文件到服务器（base64方式，避免SCP超时）
# 对小文件(<100KB)用base64编码+SSH管道写入比SCP更稳定
for f in agents/gpu_monitor.py agents/query_idle.py agents/query_cost.py \
         agents/query_history.py agents/cost_tracker.py \
         alerts/auto_shutdown.py dashboards/monitor_app.py; do
  b64=$(base64 < "$f" | tr -d '\n')
  sshpass -p '密码' ssh -p PORT root@HOST "echo '$b64' | base64 -d > ~/monitor/$f"
done

# 2. 安装依赖
sshpass -p '密码' ssh -p PORT root@HOST \
  "export PATH=/root/miniconda3/bin:\$PATH && \
   pip install psutil pyyaml streamlit plotly -q"

# 3. 启动 GPU 采集
sshpass -p '密码' ssh -p PORT root@HOST \
  "export PATH=/root/miniconda3/bin:\$PATH && \
   cd ~/monitor && nohup python3 agents/gpu_monitor.py --daemon > logs/gpu_monitor.log 2>&1 &"

# 4. 启动看板（用 setsid 确保 SSH 断开后不退出）
sshpass -p '密码' ssh -p PORT root@HOST \
  "export PATH=/root/miniconda3/bin:\$PATH && \
   cd ~/monitor && setsid streamlit run dashboards/monitor_app.py \
   --server.port 8050 --server.address 0.0.0.0 > logs/dashboard.log 2>&1 &"

# 5. 启动自动关机引擎
sshpass -p '密码' ssh -p PORT root@HOST \
  "export PATH=/root/miniconda3/bin:\$PATH && \
   cd ~/monitor && nohup python3 alerts/auto_shutdown.py --daemon > logs/auto_shutdown.log 2>&1 &"

# 6. 创建 SSH 隧道（在 Mac 上）
sshpass -p '密码' ssh -o ServerAliveInterval=30 -p PORT \
  -L 8050:localhost:8050 root@HOST -N
# 后台化：加 -f 或用 terminal(background=true)
```

### 日常启动（服务器重启后）
```bash
bash start_monitor.sh  # 一键全部启动
```

### 看板 URL
SSH 隧道建好后 → **http://localhost:8050**

## 关键架构决策

### 为什么看板跑在服务器而非Mac？
因为 GPU 数据在服务器上采集（nvidia-smi + SQLite），数据不跨网传输，看板直接读本地 DB 最实时。Mac 用 SSH 隧道转发端口查看。

### 为什么数据查询分离成独立脚本？
这些脚本（query_idle.py, query_cost.py, query_history.py）通过 SSH 远程执行，查询结果 JSON 返回。因为 Streamlit 看板内的「执行远程命令→解析」逻辑在复杂 SQL 内嵌 Python 字符串场景下容易因引号嵌套而出错。分离成服务器端独立文件可避免此问题。

### 自动关机时机选择
30 分钟空闲后关机是保守设定：15 分钟提醒 → 25 分钟紧急 → 30 分钟执行。太短会误关（训练间歇加载数据也超过 5 分钟无 GPU 工），太长浪费钱。30 分钟是经验平衡点。

### 后台进程持久化
使用 `nohup` + `setsid` + `disown` 确保后台进程在 SSH 断开后继续运行。`setsid` 比 `nohup` 更可靠——它创建一个新 session 彻底脱离父 shell。`ps aux | grep streamlit` 有时找不到 `setsid` 启动的进程，用 `ss -tlnp | grep 8050` 确认端口在监听。

## GPU守夜Agent模式（推荐替代纯脚本）

纯脚本的 `auto_shutdown.py` 有致命缺陷：GPU利用率降到0%时无法判断是"训练完成"还是"训练中加载数据"。Agent驱动的方案补上了这个判断力。

### 架构：Apex Dashboard + Hermes Cron 混合

```
Apex Dashboard (:8080)         ← 全局可视化（项目+任务+GPU+成本）
Apex Autonomous Engine         ← 7×24 调度触发器
Hermes Cron (ops-engineer)     ← 实际执行 SSH/判断/微信/关机
```

### Hermes Cron 配置

```bash
hermes cron create "*/10 * * * *" \
  --name "GPU守夜Agent" \
  --profile ops-engineer \
  --skills monitoring-system \
  --prompt "SSH到AutoDL检查GPU利用率。若空闲>15分钟发微信提醒，>30分钟自动关机。先检查进程列表确认无训练任务在跑。"
```

### Agent判断逻辑（优于纯脚本）

| 场景 | 纯脚本 | Agent |
|------|--------|-------|
| GPU 0%，但nvidia-smi显示python进程 | 🟡 可能误关 | ✅ 检测到训练进程，不关机 |
| GPU 0%，无进程，15分钟 | 🟡 只发提醒 | ✅ 发提醒 + 估算浪费金额 |
| GPU 0%，无进程，30分钟 | ✅ 关机 | ✅ 关机 + 微信通知省了多少钱 |
| 连续3次检查同一进程卡死 | ❌ 不知道 | ✅ 主动问"训练可能卡了，要强制关吗？" |

### 与Apex Dashboard集成

Dashboard V3 可增加GPU面板，通过调用Hermes Bridge API获取实时状态。已有API端点可用。

## 部署注意事项

1. **密码在 SSH 命令中是明文** — `sshpass` 读取环境变量更安全：`export SSHPASS='xxx' && sshpass -e ssh ...`
2. **看板进程检测** — 用 `ss -tlnp | grep 8050` 而非 `ps aux | grep streamlit`（后者可能找不到 `setsid` 运行的进程）
3. **文件上传** — 大文件（>100KB）用 base64 编码后通过 SSH 管道写入（`echo b64 | base64 -d > path`），比 SCP 更快更稳定
4. **看板自动刷新模式** — 用 `time.sleep(0.1) + st.rerun()` 实现 5 秒自动刷新，`@st.cache_data(ttl=5)` 控制数据缓存有效期
5. **SSH 隧道保活** — 用 `-o ServerAliveInterval=30` 每 30 秒发心跳防止隧道超时断开

## GPU 多实例舰队管理 (2026-06-03)

Apex Dashboard 现在支持多台 AutoDL GPU 实例的实时追踪。配置在 `apex/interface/hermes_bridge.py`：

```python
AUTODL_INSTANCES = [
    {"id": "cabf47a278", "name": "GPU-1 (cabf47a278)", "host": "connect.bjb2.seetacloud.com", "port": 32581, "user": "root"},
    {"id": "cac99c71", "name": "GPU-2 (cac99c71)", "host": "connect.bjb2.seetacloud.com", "port": 32581, "user": "root"},
]
```

每个实例通过 SSH `nvidia-smi` 检查，API `/api/gpu/status` 返回：
- `instances_online/offline` — 在线/离线计数
- `instances: [{id, online, gpu_name, utilization, memory, temperature, uptime}]` — 逐实例详情
- 同时保留 monitor.db 历史数据

Dashboard 在指挥中心视图展示 GPU 实例卡片：🟢 在线显示利用率条 + 温度 + 显存，🔴 离线显示错误信息。

## Hermes Bridge 微信推送配置

`agents/hermes_bridge.py` 是 Mac 端微信推送桥。首次使用前需完成以下配置：

### 友好通知模式（推荐）

对于服务监控类通知，使用 `no_agent=true` cron + 脚本控制通知内容和频率，避免原始 SSH 错误泄露密码或重复轰炸。详见 `references/friendly-cron-notifications.md`。

### 角色驱动通知系统 v2

> **详细文档已迁移至独立 skill `notification-dispatcher`** — load `notification-dispatcher` skill 获取完整操作手册。

对于**多项目多角色的复杂场景**，使用 `~/.hermes/scripts/notification_dispatcher.py` v2 引擎集中管理。核心升级：
- `notification_config.json` 控制中心（whitelist/blacklist/all/off 四种模式，改完即时生效）
- `templates/<role>.md` 独立消息模板（支持 `{{var}}` / `[?cond?]` / `{{#each}}`）
- Profile SOUL.md 感知 + 始祖子角色聚合

**管理命令：**
```bash
cd ~/.hermes/scripts && python3 notification_dispatcher.py roles  # 角色矩阵
python3 notification_dispatcher.py config                         # 控制配置
python3 notification_dispatcher.py <角色名>                       # 手动触发
```

**安全：**
- SSH密码锁入 `~/.hermes/.autodl_pass`（权限600），永不进入命令行或cron prompt
- 已删除的密码泄露 cron：autodl-complete-and-report, autodl-batch-progress
- 所有监控脚本默认使用 `no_agent=true`，不消耗 LLM token

### 一次性配置
```bash
# 设置微信 home channel（只需一次）
hermes config set WEIXIN_HOME_CHANNEL "o9cq801pPjNXqgPCdhTHLRu8eJL0@im.wechat"
```

### 导入路径修复
`hermes_bridge.py` 在 `agents/` 子目录下，内部 `from agents.cost_tracker import ...` 需要父目录在 `sys.path` 中。脚本必须在 `BASE_DIR` 定义后插入 `sys.path.insert(0, str(BASE_DIR))`，否则运行时报 `ModuleNotFoundError: No module named 'agents'`。

### `hermes send` 正确语法
```bash
hermes send --to weixin "消息内容"
```
**不是** `--platform weixin --message`（旧语法）。

### Cron 模式注意事项
在 cron job 中，`hermes send --to weixin` 会被系统自动跳过（`cron_auto_delivery_duplicate_target`），因为 cron 已经自动投递最终响应到同一目标。cron 场景下直接将日报内容作为最终响应输出即可，不要额外调用 `hermes send`。

**特别注意**：`python3 agents/hermes_bridge.py --daily-report` 在 cron 中会静默失败（脚本内部调 `hermes send` 被 suppress，exit 0 但 stdout 空）。Cron agent 必须绕过脚本，直接读取 `monitor.db` + CSV 指标文件自行组装报告。完整指南 → `references/cron-agent-daily-report.md`。

**强制检查清单**（每次 cron 执行前）：若 `monitor.db` 中 `gpu_metrics` 表行数为 0 且 CSV 指标文件仅含表头，说明AutoDL 服务器上守护进程未运行，立即报告"监控守护进程离线"而非静默返回。

详见 → `references/hermes-bridge-pitfalls.md`（含已知问题：导入路径、命令语法、cron模式、实例离线假报告）

## 看板 v1→v2 改动

| 改动 | v1 | v2 |
|:---|:---|:---|
| 核心目标 | 数据展示 | 成本控制 |
| 关机按钮 | ❌ | ✅ 一键关机 |
| 闲时倒计时 | ❌ | ✅ 进度条 + 剩余分钟 |
| 成本时钟 | 日/月累计 | 总运行/总费用/今日/每分钟 |
| 浪费金额显示 | ❌ | ✅ "已浪费 ¥XX" |
| 自动关机 | 外部脚本 | 集成到看板提示 |
| 24小时图 | ✅ | ✅ + 统计摘要 |

## LLM Token 成本追踪 (新增 v3)

独立于 GPU 成本监控的 LLM API token 追踪系统，从 Hermes `state.db` 提取所有 LLM 调用的 token 和成本。

- **Dashboard:** `http://localhost:8080/cost` — 4 标签页（Cron/Agent/项目/趋势）
- **API:** `/api/cost/*` — 7 个端点
- **模块:** `apex/cost_tracker.py`
- **数据源:** `state.db` sessions 表（按 source/cron_job_id/agent 聚合）

详见 → `references/llm-token-cost-dashboard.md`
