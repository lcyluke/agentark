#!/usr/bin/env python3
"""7x24 autonomous operation engine with self-awareness and continuous operation."""
from __future__ import annotations

import asyncio
import json
import os
import signal
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable

from agentark.core.profile import ProfileManager, AGENTARK_HOME
from agentark.core.runtime import Agent
from agentark.core.knowledge import KnowledgeGraph
from agentark.core.evolution import EvolutionEngine, ExecutionRecord
from agentark.orchestration.kanban import Kanban, Task, TASK_STATUS_READY, TASK_STATUS_IN_PROGRESS, TASK_STATUS_DONE, TASK_STATUS_FAILED


# ════════════════════════════════════════════════════════════════════
# Data Models
# ════════════════════════════════════════════════════════════════════

@dataclass
class Heartbeat:
    """Agent heartbeat — self-awareness pulse"""
    agent_name: str
    status: str  # healthy | degraded | stalled | offline
    load: float  # 0.0-1.0 — how busy the agent is
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_response_ms: float = 0.0
    memory_usage: str = ""
    last_active: float = 0.0
    message: str = ""


@dataclass
class ScheduledTask:
    """A task scheduled for autonomous execution"""
    id: str
    name: str
    cron_expr: str  # "*/5 * * * *" or "every 30m" or ISO datetime
    task_description: str
    assigned_agent: str = ""
    priority: int = 2
    enabled: bool = True
    last_run: float = 0.0
    next_run: float = 0.0
    run_count: int = 0
    success_count: int = 0
    last_result: str = ""
    retry_on_fail: bool = True
    max_retries: int = 3
    notify_on_fail: bool = True
    tags: list[str] = field(default_factory=list)


@dataclass
class AutonomousReport:
    """Self-awareness report — the engine's view of itself"""
    engine_status: str  # running | paused | degraded | stopped
    uptime_seconds: float = 0.0
    active_agents: list[Heartbeat] = field(default_factory=list)
    scheduled_tasks: list[ScheduledTask] = field(default_factory=list)
    pending_queue: int = 0
    tasks_executed_total: int = 0
    tasks_succeeded: int = 0
    tasks_failed: int = 0
    average_queue_wait_ms: float = 0.0
    knowledge_nodes: int = 0
    evolution_patterns: int = 0
    alerts: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


# ════════════════════════════════════════════════════════════════════
# Autonomous Engine
# ════════════════════════════════════════════════════════════════════

class AutonomousEngine:
    """7x24 Autonomous Operation Engine — the brain behind continuous agent operation"""

    def __init__(self, db_path: Path = AGENTARK_HOME / "autonomous.db"):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_db()

        self.pm = ProfileManager()
        self.kanban = Kanban(AGENTARK_HOME / "kanban.db")
        self.kg = KnowledgeGraph()
        self.evolution = EvolutionEngine()

        self._running = False
        self._paused = False
        self._start_time = 0.0
        self._heartbeats: dict[str, Heartbeat] = {}
        self._task_queue: list[ScheduledTask] = []
        self._lock = threading.Lock()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._dispatcher_thread: Optional[threading.Thread] = None
        self._alerts: list[str] = []

        # Callbacks
        self.on_task_complete: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_heartbeat: Optional[Callable] = None

    def _init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                cron_expr TEXT NOT NULL,
                task_description TEXT NOT NULL,
                assigned_agent TEXT DEFAULT '',
                priority INTEGER DEFAULT 2,
                enabled INTEGER DEFAULT 1,
                last_run REAL DEFAULT 0.0,
                next_run REAL DEFAULT 0.0,
                run_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                last_result TEXT DEFAULT '',
                retry_on_fail INTEGER DEFAULT 1,
                max_retries INTEGER DEFAULT 3,
                notify_on_fail INTEGER DEFAULT 1,
                tags TEXT DEFAULT '[]',
                created_at REAL DEFAULT (julianday('now'))
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                agent_name TEXT DEFAULT '',
                status TEXT DEFAULT '',
                error TEXT DEFAULT '',
                duration_ms INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.0,
                attempted INTEGER DEFAULT 1,
                created_at REAL DEFAULT (julianday('now'))
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                severity TEXT DEFAULT 'info',
                source TEXT DEFAULT '',
                message TEXT DEFAULT '',
                resolved INTEGER DEFAULT 0,
                created_at REAL DEFAULT (julianday('now'))
            )
        """)
        self._conn.commit()

    # ════════════════════════════════════════════════════════════════
    # Lifecycle
    # ════════════════════════════════════════════════════════════════

    def start(self):
        """Start the autonomous engine — 7x24 operation"""
        if self._running:
            return

        self._running = True
        self._paused = False
        self._start_time = time.time()

        # Start threads
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True, name="apex-heartbeat")
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True, name="apex-scheduler")
        self._dispatcher_thread = threading.Thread(target=self._dispatcher_loop, daemon=True, name="apex-dispatcher")

        self._heartbeat_thread.start()
        self._scheduler_thread.start()
        self._dispatcher_thread.start()

        self._add_alert("info", "AutonomousEngine", "Engine started — 7x24 operation mode")
        return self

    def stop(self):
        """Gracefully stop the engine"""
        self._running = False
        self._add_alert("info", "AutonomousEngine", "Engine stopped")

    def pause(self):
        """Pause task execution (heartbeat continues)"""
        self._paused = True
        self._add_alert("info", "AutonomousEngine", "Engine paused — tasks queued but not dispatched")

    def resume(self):
        """Resume task execution"""
        self._paused = False
        self._add_alert("info", "AutonomousEngine", "Engine resumed")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def uptime(self) -> float:
        return time.time() - self._start_time if self._start_time > 0 else 0.0

    # ════════════════════════════════════════════════════════════════
    # Task Scheduling
    # ════════════════════════════════════════════════════════════════

    def schedule(self, name: str, cron_expr: str, task_description: str,
                 assigned_agent: str = "", priority: int = 2,
                 retry_on_fail: bool = True, max_retries: int = 3,
                 tags: list[str] = None) -> ScheduledTask:
        """Schedule a recurring task"""
        task_id = f"auto_{uuid.uuid4().hex[:8]}"
        next_run = self._parse_cron(cron_expr)

        task = ScheduledTask(
            id=task_id, name=name, cron_expr=cron_expr,
            task_description=task_description, assigned_agent=assigned_agent,
            priority=priority, enabled=True, next_run=next_run,
            retry_on_fail=retry_on_fail, max_retries=max_retries,
            tags=tags or [],
        )

        self._conn.execute("""
            INSERT INTO scheduled_tasks 
            (id, name, cron_expr, task_description, assigned_agent, priority,
             enabled, next_run, retry_on_fail, max_retries, notify_on_fail, tags)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, 1, ?)
        """, (task.id, task.name, task.cron_expr, task.task_description,
              task.assigned_agent, task.priority, task.next_run,
              1 if task.retry_on_fail else 0, task.max_retries,
              json.dumps(task.tags)))
        self._conn.commit()

        return task

    def unschedule(self, task_id: str):
        """Remove a scheduled task"""
        self._conn.execute("DELETE FROM scheduled_tasks WHERE id=?", (task_id,))
        self._conn.commit()

    def list_scheduled(self) -> list[ScheduledTask]:
        """List all scheduled tasks"""
        cursor = self._conn.execute("SELECT * FROM scheduled_tasks ORDER BY priority, next_run")
        tasks = []
        for row in cursor.fetchall():
            tasks.append(ScheduledTask(
                id=row[0], name=row[1], cron_expr=row[2],
                task_description=row[3], assigned_agent=row[4],
                priority=row[5], enabled=bool(row[6]),
                last_run=row[7], next_run=row[8],
                run_count=row[9], success_count=row[10],
                last_result=row[11], retry_on_fail=bool(row[12]),
                max_retries=row[13], notify_on_fail=bool(row[14]),
                tags=json.loads(row[15]) if row[15] else [],
            ))
        return tasks

    def _parse_cron(self, expr: str) -> float:
        """Parse cron expression or human-readable interval to next run timestamp"""
        now = time.time()
        expr = expr.strip()

        # Human-readable intervals
        if expr.startswith("every "):
            amount_str = expr.replace("every ", "").strip()
            unit = "m"
            if " " in amount_str:
                parts = amount_str.split(" ")
                amount_str = parts[0]
                unit = parts[1][0] if len(parts) > 1 else "m"

            try:
                amount = int(amount_str)
                if unit == "s":
                    return now + amount
                elif unit == "h":
                    return now + amount * 3600
                elif unit == "d":
                    return now + amount * 86400
                else:  # minutes
                    return now + amount * 60
            except ValueError:
                pass

        # ISO datetime
        try:
            dt = datetime.fromisoformat(expr)
            return dt.timestamp()
        except (ValueError, TypeError):
            pass

        # Simple cron: "*/N * * * *" — every N minutes
        if expr.startswith("*/") and expr.endswith(" * * * *"):
            try:
                minutes = int(expr[2:expr.index(" ")])
                return now + minutes * 60
            except (ValueError, IndexError):
                pass

        # Default: every 30 minutes
        return now + 1800

    def _next_occurrence(self, last_run: float, cron_expr: str) -> float:
        """Calculate next occurrence after last_run"""
        interval = self._parse_cron(cron_expr) - time.time() + 1  # approximate
        if interval <= 0:
            interval = 1800  # default 30 min
        return last_run + interval

    # ════════════════════════════════════════════════════════════════
    # Heartbeat & Self-Awareness
    # ════════════════════════════════════════════════════════════════

    def _heartbeat_loop(self):
        """Background thread: collect heartbeats from all agents every 30s"""
        while self._running:
            try:
                self._collect_heartbeats()
                if self.on_heartbeat:
                    self.on_heartbeat(self._heartbeats)
            except Exception as e:
                self._add_alert("warning", "Heartbeat", f"Collection failed: {e}")
            time.sleep(30)

    def _collect_heartbeats(self):
        """Collect status from all registered profiles"""
        profiles = self.pm.list()
        now = time.time()

        for name in profiles:
            try:
                profile = self.pm.load(name)
                # Get execution stats from evolution engine
                evo_data = self.evolution.get_agent_evolution(name) if self.evolution else {}
                total = evo_data.get("total_executions", 0)
                success_rate_str = evo_data.get("success_rate", "0%")
                try:
                    success_rate = float(success_rate_str.strip("%")) / 100
                except (ValueError, AttributeError):
                    success_rate = 1.0

                status = "healthy"
                load = 0.3  # default load

                # Check Kanban for active tasks
                active_tasks = self.kanban.list_tasks(status=TASK_STATUS_IN_PROGRESS)
                agent_tasks = [t for t in active_tasks if t.assignee == name]
                if len(agent_tasks) >= 3:
                    load = 0.8
                    status = "degraded"
                elif len(agent_tasks) >= 1:
                    load = 0.5

                # Check last activity
                if total == 0:
                    status = "stalled"

                heartbeat = Heartbeat(
                    agent_name=name,
                    status=status,
                    load=load,
                    tasks_completed=total,
                    tasks_failed=int(total * (1 - success_rate)),
                    avg_response_ms=evo_data.get("avg_response_ms", 0),
                    last_active=now,
                    message=f"{total} tasks, {success_rate:.0%} success",
                )
                self._heartbeats[name] = heartbeat

            except Exception:
                self._heartbeats[name] = Heartbeat(
                    agent_name=name, status="offline", load=0.0,
                    message="Profile load failed",
                )

    def get_heartbeats(self) -> list[Heartbeat]:
        """Get latest heartbeats"""
        return list(self._heartbeats.values())

    # ════════════════════════════════════════════════════════════════
    # Scheduler Loop
    # ════════════════════════════════════════════════════════════════

    def _scheduler_loop(self):
        """Background thread: check scheduled tasks every 15s"""
        while self._running:
            try:
                now = time.time()
                tasks = self.list_scheduled()
                for task in tasks:
                    if task.enabled and task.next_run <= now:
                        self._enqueue_task(task)
                        # Update next run
                        task.last_run = now
                        task.run_count += 1
                        task.next_run = self._next_occurrence(now, task.cron_expr)
                        self._conn.execute(
                            "UPDATE scheduled_tasks SET last_run=?, next_run=?, run_count=? WHERE id=?",
                            (task.last_run, task.next_run, task.run_count, task.id),
                        )
                        self._conn.commit()
            except Exception as e:
                self._add_alert("error", "Scheduler", f"Scheduler error: {e}")
            time.sleep(15)

    def _enqueue_task(self, task: ScheduledTask):
        """Add task to execution queue"""
        with self._lock:
            self._task_queue.append(task)
            # Sort by priority
            self._task_queue.sort(key=lambda t: t.priority)

    # ════════════════════════════════════════════════════════════════
    # Dispatcher Loop
    # ════════════════════════════════════════════════════════════════

    def _dispatcher_loop(self):
        """Background thread: dispatch queued tasks every 10s"""
        while self._running:
            try:
                if self._paused:
                    time.sleep(10)
                    continue

                # 1. Dispatch from queue
                task_to_dispatch = None
                with self._lock:
                    if self._task_queue:
                        task_to_dispatch = self._task_queue.pop(0)

                if task_to_dispatch:
                    self._execute_task(task_to_dispatch)

                # 2. Auto-dispatch ready Kanban tasks
                ready_tasks = self.kanban.get_ready_tasks()
                for rt in ready_tasks[:2]:  # Max 2 per cycle
                    self._dispatch_kanban_task(rt)

            except Exception as e:
                self._add_alert("error", "Dispatcher", f"Dispatch error: {e}")
            time.sleep(10)

    def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task with retry logic"""
        agent_name = task.assigned_agent or "default"
        attempt = 0
        max_attempts = task.max_retries if task.retry_on_fail else 1
        start_time = time.time()
        last_error = ""

        while attempt < max_attempts:
            attempt += 1
            try:
                profile = self.pm.load(agent_name)
                agent = Agent(profile)

                # Add knowledge graph context
                kg_context = self.kg.query(task.task_description)
                if kg_context.confidence > 0.3:
                    enriched_task = f"{task.task_description}\n\n[Knowledge Context]\n{kg_context.answer[:500]}"
                else:
                    enriched_task = task.task_description

                output = agent.run(enriched_task)
                duration_ms = int((time.time() - start_time) * 1000)

                # Record success
                self._conn.execute(
                    """INSERT INTO execution_log (task_id, agent_name, status, duration_ms, cost, attempted)
                       VALUES (?, ?, 'success', ?, ?, ?)""",
                    (task.id, agent_name, duration_ms, agent.context.cost, attempt),
                )
                self._conn.commit()

                # Update task stats
                task.success_count += 1
                task.last_result = output[:200]
                self._conn.execute(
                    "UPDATE scheduled_tasks SET success_count=?, last_result=? WHERE id=?",
                    (task.success_count, output[:200], task.id),
                )
                self._conn.commit()

                # Record in evolution engine
                self.evolution.record(ExecutionRecord(
                    agent_name=agent_name,
                    task=task.task_description,
                    task_type="scheduled",
                    prompt=task.task_description[:200],
                    output=output[:500],
                    success=True,
                    duration_ms=duration_ms,
                    quality_score=0.8,
                ))

                # Learn from execution
                self.kg.learn(f"task:{task.name[:50]}", "scheduled-task",
                              f"Successfully executed by {agent_name}: {task.task_description[:200]}",
                              source="autonomous")

                if self.on_task_complete:
                    self.on_task_complete(task, output)

                return

            except Exception as e:
                last_error = str(e)
                duration_ms = int((time.time() - start_time) * 1000)

                self._conn.execute(
                    """INSERT INTO execution_log (task_id, agent_name, status, error, duration_ms, attempted)
                       VALUES (?, ?, 'failed', ?, ?, ?)""",
                    (task.id, agent_name, str(e)[:200], duration_ms, attempt),
                )
                self._conn.commit()

                if attempt < max_attempts:
                    # Exponential backoff
                    backoff = 2 ** attempt
                    time.sleep(backoff)

        # All attempts failed
        task.last_result = f"FAILED after {max_attempts} attempts: {last_error[:100]}"
        self._conn.execute(
            "UPDATE scheduled_tasks SET last_result=? WHERE id=?",
            (task.last_result, task.id),
        )
        self._conn.commit()

        # Record failure in evolution
        self.evolution.record(ExecutionRecord(
            agent_name=agent_name,
            task=task.task_description,
            task_type="scheduled",
            prompt=task.task_description[:200],
            output="",
            success=False,
            duration_ms=int((time.time() - start_time) * 1000),
            quality_score=0.1,
            error=last_error[:200],
        ))

        # Learn from failure
        self.kg.learn(f"error:{task.name[:40]}", "error",
                      f"Scheduled task failed after {max_attempts} attempts: {last_error[:200]}",
                      source="autonomous")

        if task.notify_on_fail:
            self._add_alert("error", f"Task:{task.name}",
                            f"Failed after {max_attempts} attempts: {last_error[:100]}")

        if self.on_error:
            self.on_error(task, last_error)

    def _dispatch_kanban_task(self, task: Task):
        """Auto-dispatch a ready Kanban task"""
        agent_name = task.assignee or "default"
        self.kanban.update_task(task.id, status=TASK_STATUS_IN_PROGRESS)

        try:
            profile = self.pm.load(agent_name)
            agent = Agent(profile)
            output = agent.run(task.description or task.title)

            self.kanban.update_task(task.id, status=TASK_STATUS_DONE, output=output)
            self._log_execution(task.id, agent_name, "success")

        except Exception as e:
            self.kanban.update_task(task.id, status=TASK_STATUS_FAILED, output=str(e))
            self._log_execution(task.id, agent_name, "failed", error=str(e))
            self._add_alert("warning", f"Kanban:{task.id}", f"Auto-dispatch failed: {e}")

    def _log_execution(self, task_id: str, agent_name: str, status: str, error: str = ""):
        self._conn.execute(
            """INSERT INTO execution_log (task_id, agent_name, status, error)
               VALUES (?, ?, ?, ?)""",
            (task_id, agent_name, status, error[:200]),
        )
        self._conn.commit()

    # ════════════════════════════════════════════════════════════════
    # Self-Awareness Report
    # ════════════════════════════════════════════════════════════════

    def generate_report(self) -> AutonomousReport:
        """Generate a full self-awareness report"""
        status = "running"
        if not self._running:
            status = "stopped"
        elif self._paused:
            status = "paused"

        # Stats
        cursor = self._conn.execute(
            "SELECT COUNT(*), SUM(CASE WHEN status='success' THEN 1 ELSE 0 END), "
            "SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) FROM execution_log"
        )
        row = cursor.fetchone()
        total_exec = row[0] or 0
        succeeded = row[1] or 0
        failed = row[2] or 0

        # Queue wait
        kg_stats = self.kg.stats()
        evo_summary = self.evolution.summary()

        # Alerts
        cursor = self._conn.execute(
            "SELECT message FROM alerts WHERE resolved=0 ORDER BY created_at DESC LIMIT 5"
        )
        alerts = [r[0] for r in cursor.fetchall()]

        # Generate recommendations
        recommendations = []
        if failed > total_exec * 0.2:
            recommendations.append(f"High failure rate ({failed}/{total_exec}). Consider reviewing agent configurations.")
        stalled_agents = [h for h in self._heartbeats.values() if h.status == "stalled"]
        if stalled_agents:
            recommendations.append(f"{len(stalled_agents)} agents stalled. Run 'apex run \"test\"' to wake them.")
        if kg_stats.get("total_nodes", 0) > 100:
            recommendations.append("Knowledge graph growing well. Consider pruning low-confidence nodes.")

        return AutonomousReport(
            engine_status=status,
            uptime_seconds=self.uptime,
            active_agents=list(self._heartbeats.values()),
            scheduled_tasks=self.list_scheduled(),
            pending_queue=len(self._task_queue),
            tasks_executed_total=total_exec,
            tasks_succeeded=succeeded,
            tasks_failed=failed,
            knowledge_nodes=kg_stats.get("total_nodes", 0),
            evolution_patterns=evo_summary.get("patterns_discovered", 0),
            alerts=alerts,
            recommendations=recommendations,
        )

    # ════════════════════════════════════════════════════════════════
    # Alerts
    # ════════════════════════════════════════════════════════════════

    def _add_alert(self, severity: str, source: str, message: str):
        self._conn.execute(
            "INSERT INTO alerts (severity, source, message) VALUES (?, ?, ?)",
            (severity, source, message),
        )
        self._conn.commit()
        self._alerts.append(f"[{severity.upper()}] {source}: {message}")

    def get_alerts(self, unresolved_only: bool = True, limit: int = 20) -> list[dict]:
        query = "SELECT severity, source, message, created_at FROM alerts"
        if unresolved_only:
            query += " WHERE resolved=0"
        query += " ORDER BY created_at DESC LIMIT ?"

        cursor = self._conn.execute(query, (limit,))
        return [
            {"severity": r[0], "source": r[1], "message": r[2], "time": r[3]}
            for r in cursor.fetchall()
        ]

    def resolve_alert(self, alert_id: int):
        self._conn.execute("UPDATE alerts SET resolved=1 WHERE id=?", (alert_id,))
        self._conn.commit()


# Global singleton
engine: Optional[AutonomousEngine] = None


def get_engine() -> AutonomousEngine:
    """Get or create the global autonomous engine"""
    global engine
    if engine is None:
        engine = AutonomousEngine()
    return engine
