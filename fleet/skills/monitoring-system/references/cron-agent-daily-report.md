# Cron Agent 日报 — 绕过 hermes_bridge 直查方案

## 为什么不能用 hermes_bridge.py

`hermes_bridge.py --daily-report` 在 cron 模式下静默失败：
- 脚本内部调用 `hermes send --to weixin`，但 cron 的去重机制 (`cron_auto_delivery_duplicate_target`) 会 suppress 子进程中的 `send_message`
- 脚本 exit 0 但 stdout 为空，agent 收不到任何数据

## 替代方案：Cron agent 直查

Cron agent 必须在 Mac 本地自行组装日报，步骤：

### 1. 检查数据是否在线
```sql
SELECT COUNT(*) FROM gpu_metrics;           -- 必须 > 0
SELECT COUNT(*) FROM gpu_metrics WHERE timestamp LIKE '2026-06-13%';  -- 今日记录
```
从 `/Users/Mac/Desktop/2026AIAPP/monitor/logs/monitor.db` 读取。

如果 `gpu_metrics` 为空，再检查 CSV：
```bash
wc -l ~/Desktop/2026AIAPP/monitor/logs/metrics/gpu_*.csv
```
全部只有1行（表头）= 守护进程离线。直接报告 "监控守护进程未运行"。

### 2. 读取成本数据
直接从 `monitor.db` 的 `gpu_metrics` 表计算：
- 今日成本 = `COUNT(today_records) * 5 / 3600 * price_per_hour`
- 本月成本同理
- GPU 名称取最新一条记录的 `gpu_name` 字段
- 单价对照 `GPU_PRICES` 表（见 `cost_tracker.py` 第26-37行）

### 3. 读取训练状态
从 `training_progress` 表取最新记录（按 task_name + phase 分组的最新 id）。3分钟内更新的视为运行中。

### 4. 读取预警
从 `alerts` 表取 `acknowledged = 0` 的计数。

### 5. 组装最终响应
格式（直接作为 cron 响应输出，系统自动投递到微信）：
```
📊 羽球宝日报 | 6月13日

💰 成本
  今日: ¥X.XX
  本月: ¥X.XX / ¥500
  GPU: RTX 4090 (¥5.0/时)

📈 训练
  🟢/⚪ task_label: XX%

🚨 预警: N 条未处理
```

## 守护进程离线处理

若数据为空，响应简化为：
```
📊 羽球宝日报 | 6月13日

🔴 监控守护进程离线
  - monitor.db 无 GPU 数据
  - CSV 指标文件均为空
  - 需 SSH 到 AutoDL 执行: bash start_monitor.sh
```

不要尝试 SSH 重启（cron agent 仅报告，不操作）。