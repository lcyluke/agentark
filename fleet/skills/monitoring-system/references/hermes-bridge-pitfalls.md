# Hermes Bridge 常见问题与修复

## 问题 1：`ModuleNotFoundError: No module named 'agents'`

`hermes_bridge.py` 在 `agents/` 子目录下，内部 `from agents.cost_tracker import ...` 需要父目录在 `sys.path` 中。

**修复** — 在 `BASE_DIR` 定义之后加一行：

```python
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))   # ← 必须加这行
DB_PATH = BASE_DIR / "logs" / "monitor.db"
```

## 问题 2：`hermes send` 命令语法

桥脚本中 `send_wechat_message()` 调用 `hermes send`：

```python
# ❌ 错误（旧语法）
["hermes", "send", "--platform", "weixin", "--message", message]

# ✅ 正确
["hermes", "send", "--to", "weixin", message]
```

另外，微信必须先配置 home channel：

```bash
hermes config set WEIXIN_HOME_CHANNEL "o9cq801pPjNXqgPCdhTHLRu8eJL0@im.wechat"
```

## 问题 3：Cron 模式下 `hermes send` 被自动跳过

当 cron job 运行时，如果 `hermes send --to weixin` 的目标与 cron 自动投递的目标相同，系统会返回 `cron_auto_delivery_duplicate_target` 并跳过发送。

**原因**：cron job 本身就会把最终响应自动投递到微信，再显式发送同目标消息是冗余的。

**解决**：在 cron job 中，直接把日报内容作为最终响应输出（系统会自动投递），不要通过 `hermes send` 子进程发送。桥脚本可以在非 cron 场景（如手动运行或 auto_shutdown 引擎调用）使用 `hermes send`。

## 问题 4：日报在实例离线时发送全零"假报告"

当 AutoDL 实例离线（已关机/过期）且 `monitor.db` 无近期数据时，`hermes_bridge.py --daily-report` 仍然 exit 0 并发送一条全零日报：

```
📊 羽球宝日报 | 06月08日
💰 成本
  今日: ¥0
  本月: ¥0 / ¥500
  GPU: N/A
📈 训练
  ⚪ 暂无训练任务
🚨 预警: 0 条未处理
```

**症状检测** — 以下任一条件同时满足即判定为"实例离线"：
- `cost_tracker.get_runtime_stats()` 返回 `gpu_name == "N/A"` 且 `total_runtime_hours == 0`
- `training_tracker.get_current_status()` 返回 `[]`
- SSH 到 AutoDL 实例被拒绝（`Connection closed by ...`）

**建议修复** — 在 `push_daily_report()` 开头加守卫：

```python
def push_daily_report():
    from agents.cost_tracker import get_runtime_stats
    stats = get_runtime_stats()
    
    # 守卫：实例离线时不发假报告
    if stats.get("gpu_name") == "N/A" and stats.get("total_runtime_hours") == 0:
        print("[SILENT] GPU实例离线，跳过日报推送")
        return  # 不发送任何消息
    ...
```

Cron 模式下，脚本静默退出即可——Agent 会在自己的响应中报告离线状态，避免重复推送。
