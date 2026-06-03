#!/usr/bin/env python3
"""
🦅 Apex AutonomousEngine 守护进程

用法:
  python3 autonomous_daemon.py            # 前台运行
  nohup python3 autonomous_daemon.py &    # 后台运行

停止: kill <pid> 或 pkill -f autonomous_daemon

特性:
  - 启动 AutonomousEngine 3 线程 (心跳/调度/分发)
  - 信号处理: SIGTERM/SIGINT 优雅退出
  - 状态输出到 stdout (可重定向到日志)
"""

import os
import signal
import sys
import time
from datetime import datetime

# Unbuffered output for daemon mode
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Add Apex to path
APEX_HOME = os.path.expanduser("~/Desktop/2026AIAPP/Apex")
if APEX_HOME not in sys.path:
    sys.path.insert(0, APEX_HOME)

from apex.orchestration.autonomous import get_engine


def main():
    engine = get_engine()

    if engine.is_running:
        print(f"[{datetime.now():%H:%M:%S}] ⚠ Engine already running — exiting")
        sys.exit(1)

    print(f"[{datetime.now():%H:%M:%S}] 🦅 Apex AutonomousEngine starting...")

    # Graceful shutdown
    def shutdown(signum, frame):
        print(f"\n[{datetime.now():%H:%M:%S}] ⏹ Received signal {signum}, shutting down...")
        engine.stop()
        uptime = engine.uptime
        print(f"[{datetime.now():%H:%M:%S}] Uptime: {uptime:.0f}s — Goodbye.")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # Start
    engine.start()

    tasks = engine.list_scheduled()
    print(f"[{datetime.now():%H:%M:%S}] ✅ Engine started with {len(tasks)} scheduled tasks:")
    for t in tasks:
        print(f"     {t.name:20s} | {t.cron_expr:12s} | agent={t.assigned_agent or 'default'}")

    print(f"[{datetime.now():%H:%M:%S}] 💓 Heartbeat every 30s | 📅 Scheduler every 15s | 📤 Dispatcher every 10s")
    print(f"[{datetime.now():%H:%M:%S}] ─── waiting for work ───")

    # Keep alive — the daemon threads are running in background
    try:
        while engine.is_running:
            time.sleep(10)
            # Heartbeat: print stats every 5 minutes
            if int(time.time()) % 300 < 10:
                report = engine.generate_report()
                hb = engine.get_heartbeats()
                active = len([h for h in hb if h.status != "offline"])
                print(f"[{datetime.now():%H:%M:%S}] 💓 {active} agents | {len(report.alerts)} alerts | {engine.uptime:.0f}s uptime")
    except KeyboardInterrupt:
        shutdown(signal.SIGINT, None)


if __name__ == "__main__":
    main()
