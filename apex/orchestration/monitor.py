"""Apex — Monitor / Reactive Mode
DevOps monitoring with anomaly detection, auto-remediation, and escalation.

Pattern:
  1. Watcher — Polls data sources (file, API, log) or receives push events
  2. Anomaly Detection — Analyzes state against thresholds/rules
  3. Trigger — If anomaly found, creates a Kanban task and spawns a fixer agent
  4. Verification — After fixer runs, verify the anomaly is resolved
  5. Escalation — If unresolved after N attempts, notify human
"""

from __future__ import annotations

import re
import json
import time
import uuid
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable

from apex.core.runtime import Agent
from apex.core.profile import Profile, SoulConfig
from apex.orchestration.kanban import Kanban, TASK_STATUS_TODO, TASK_STATUS_DONE, TASK_STATUS_FAILED

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Anomaly:
    """A single anomaly detected by a watcher."""
    id: str = ""
    rule_name: str = ""
    watcher_type: str = ""
    source: str = ""                      # e.g. file path or URL
    message: str = ""
    severity: int = 3                     # 1=critical, 2=high, 3=medium, 4=low
    value: float = 0.0                    # measured value (if numeric threshold)
    threshold: float = 0.0                # threshold that was breached
    timestamp: str = ""
    raw_data: str = ""                    # snapshot of what was seen
    resolved: bool = False
    fixer_task_id: str = ""
    verification_attempts: int = 0

    def __post_init__(self):
        if not self.id:
            self.id = f"anom_{uuid.uuid4().hex[:8]}"
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "watcher_type": self.watcher_type,
            "source": self.source,
            "message": self.message,
            "severity": self.severity,
            "value": self.value,
            "threshold": self.threshold,
            "timestamp": self.timestamp,
            "resolved": self.resolved,
            "fixer_task_id": self.fixer_task_id,
            "verification_attempts": self.verification_attempts,
        }


@dataclass
class MonitorResult:
    """Result of a full monitor cycle."""
    success: bool = True
    total_watchers: int = 0
    watchers_checked: int = 0
    anomalies_detected: int = 0
    anomalies: list[Anomaly] = field(default_factory=list)
    fixer_task_ids: list[str] = field(default_factory=list)
    resolved_count: int = 0
    escalated: bool = False
    duration_ms: int = 0
    cycle_start: str = ""
    cycle_end: str = ""
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "total_watchers": self.total_watchers,
            "watchers_checked": self.watchers_checked,
            "anomalies_detected": self.anomalies_detected,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "fixer_task_ids": self.fixer_task_ids,
            "resolved_count": self.resolved_count,
            "escalated": self.escalated,
            "duration_ms": self.duration_ms,
            "cycle_start": self.cycle_start,
            "cycle_end": self.cycle_end,
            "errors": self.errors,
        }


@dataclass
class WatcherRule:
    """Defines what to watch and how to detect anomalies."""
    name: str
    type: str                                     # "file-watcher" | "http-health-check"
    target: str                                   # file path or URL
    interval_seconds: int = 60                    # polling interval
    threshold: float = 0.0                        # numeric threshold (if applicable)
    severity: int = 3                             # severity level when anomaly detected
    pattern: str = ""                             # regex pattern for file-watcher (e.g. r"ERROR|CRITICAL")
    expected_status: int = 200                    # expected HTTP status for health check
    max_retries: int = 3                          # max fixer attempts before escalation
    description: str = ""
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "target": self.target,
            "interval_seconds": self.interval_seconds,
            "threshold": self.threshold,
            "severity": self.severity,
            "pattern": self.pattern,
            "expected_status": self.expected_status,
            "max_retries": self.max_retries,
            "description": self.description,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WatcherRule":
        return cls(
            name=data["name"],
            type=data["type"],
            target=data["target"],
            interval_seconds=data.get("interval_seconds", 60),
            threshold=data.get("threshold", 0.0),
            severity=data.get("severity", 3),
            pattern=data.get("pattern", ""),
            expected_status=data.get("expected_status", 200),
            max_retries=data.get("max_retries", 3),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
        )


# ---------------------------------------------------------------------------
# Built-in Watchers
# ---------------------------------------------------------------------------

class Watcher:
    """Base watcher class. Subclasses implement check() -> list[Anomaly]."""

    def __init__(self, rule: WatcherRule):
        self.rule = rule
        self._last_check: float = 0.0
        self._consecutive_failures: int = 0
        self._last_anomaly_count: int = 0

    @property
    def name(self) -> str:
        return self.rule.name

    def should_check(self) -> bool:
        """Return True if enough time has elapsed since last check."""
        return (time.time() - self._last_check) >= self.rule.interval_seconds

    def check(self) -> list[Anomaly]:
        """Run the check. Must be implemented by subclasses."""
        raise NotImplementedError

    def mark_checked(self):
        self._last_check = time.time()

    def reset_failures(self):
        self._consecutive_failures = 0

    def record_failure(self):
        self._consecutive_failures += 1

    @property
    def healthy(self) -> bool:
        return self._consecutive_failures < self.rule.max_retries


class FileWatcher(Watcher):
    """Watch a log file for matching error patterns.

    Tracks file position so it only reads new lines since last check.
    """

    def __init__(self, rule: WatcherRule):
        super().__init__(rule)
        self._file_position: int = 0
        self._compiled_pattern: Optional[re.Pattern] = None
        if rule.pattern:
            try:
                self._compiled_pattern = re.compile(rule.pattern)
            except re.error as e:
                logger.warning("FileWatcher '%s': invalid regex '%s' — %s", rule.name, rule.pattern, e)

    def check(self) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        target_path = Path(self.rule.target)

        if not target_path.exists():
            anomalies.append(Anomaly(
                rule_name=self.rule.name,
                watcher_type="file-watcher",
                source=str(target_path),
                message=f"File not found: {target_path}",
                severity=max(1, self.rule.severity - 1),
                raw_data=f"Path does not exist: {target_path}",
            ))
            self.record_failure()
            return anomalies

        if not target_path.is_file():
            anomalies.append(Anomaly(
                rule_name=self.rule.name,
                watcher_type="file-watcher",
                source=str(target_path),
                message=f"Not a regular file: {target_path}",
                severity=self.rule.severity,
                raw_data=f"Path exists but is not a file: {target_path}",
            ))
            self.record_failure()
            return anomalies

        try:
            current_size = target_path.stat().st_size

            # Read only new content since last check
            if current_size < self._file_position:
                # File was truncated/rotated — reset position
                self._file_position = 0

            if current_size == self._file_position:
                # No new content
                self.reset_failures()
                return anomalies

            with open(target_path, "r", errors="replace") as f:
                f.seek(self._file_position)
                new_lines = f.readlines()
                self._file_position = f.tell()

            if not self._compiled_pattern:
                # No pattern to match — just check file size as a basic health indicator
                if current_size > self.rule.threshold > 0:
                    anomalies.append(Anomaly(
                        rule_name=self.rule.name,
                        watcher_type="file-watcher",
                        source=str(target_path),
                        message=f"File size ({current_size} bytes) exceeds threshold ({self.rule.threshold})",
                        severity=self.rule.severity,
                        value=float(current_size),
                        threshold=self.rule.threshold,
                        raw_data=f"File size: {current_size} bytes, new lines: {len(new_lines)}",
                    ))
            else:
                for line in new_lines:
                    if self._compiled_pattern.search(line):
                        anomalies.append(Anomaly(
                            rule_name=self.rule.name,
                            watcher_type="file-watcher",
                            source=str(target_path),
                            message=f"Pattern match in {target_path.name}: {line.rstrip()[:200]}",
                            severity=self.rule.severity,
                            raw_data=line.rstrip(),
                        ))

                        # Apply threshold: stop after N matches per check cycle
                        if self.rule.threshold > 0 and len(anomalies) >= int(self.rule.threshold):
                            break

            self.reset_failures()

        except PermissionError as e:
            anomalies.append(Anomaly(
                rule_name=self.rule.name,
                watcher_type="file-watcher",
                source=str(target_path),
                message=f"Permission denied reading {target_path}: {e}",
                severity=2,
                raw_data=str(e),
            ))
            self.record_failure()
        except OSError as e:
            anomalies.append(Anomaly(
                rule_name=self.rule.name,
                watcher_type="file-watcher",
                source=str(target_path),
                message=f"I/O error reading {target_path}: {e}",
                severity=self.rule.severity,
                raw_data=str(e),
            ))
            self.record_failure()

        return anomalies


class HttpHealthCheckWatcher(Watcher):
    """Check an HTTP/HTTPS endpoint for health.

    Validates response status code and optionally response body content.
    """

    def __init__(self, rule: WatcherRule):
        super().__init__(rule)
        self._timeout: float = 10.0
        self._headers: dict[str, str] = {
            "User-Agent": "Apex-Monitor/1.0",
        }

    def check(self) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        url = self.rule.target

        try:
            import urllib.request
            import urllib.error

            req = urllib.request.Request(url, headers=self._headers, method="GET")
            start = time.time()
            resp = urllib.request.urlopen(req, timeout=self._timeout)
            elapsed = (time.time() - start) * 1000  # ms
            status = resp.status
            body_sample = resp.read(1024).decode("utf-8", errors="replace")
            resp.close()

            expected = self.rule.expected_status

            if status != expected:
                anomalies.append(Anomaly(
                    rule_name=self.rule.name,
                    watcher_type="http-health-check",
                    source=url,
                    message=f"HTTP {status} (expected {expected}) — response time: {elapsed:.0f}ms",
                    severity=self.rule.severity,
                    value=float(status),
                    threshold=float(expected),
                    raw_data=f"Status: {status}, Body (first 1KB): {body_sample[:300]}",
                ))
                self.record_failure()
            else:
                # Also check response time threshold if set
                if self.rule.threshold > 0 and elapsed > self.rule.threshold:
                    anomalies.append(Anomaly(
                        rule_name=self.rule.name,
                        watcher_type="http-health-check",
                        source=url,
                        message=f"Slow response: {elapsed:.0f}ms (threshold: {self.rule.threshold:.0f}ms)",
                        severity=self.rule.severity + 1,
                        value=elapsed,
                        threshold=self.rule.threshold,
                        raw_data=f"Status: {status}, Response time: {elapsed:.0f}ms",
                    ))
                self.reset_failures()

        except urllib.error.HTTPError as e:
            anomalies.append(Anomaly(
                rule_name=self.rule.name,
                watcher_type="http-health-check",
                source=url,
                message=f"HTTP error {e.code}: {e.reason}",
                severity=self.rule.severity,
                value=float(e.code),
                threshold=float(self.rule.expected_status),
                raw_data=f"HTTPError {e.code}: {e.reason}",
            ))
            self.record_failure()
        except urllib.error.URLError as e:
            anomalies.append(Anomaly(
                rule_name=self.rule.name,
                watcher_type="http-health-check",
                source=url,
                message=f"Connection failed: {e.reason}",
                severity=max(1, self.rule.severity - 1),
                raw_data=f"URLError: {e.reason}",
            ))
            self.record_failure()
        except Exception as e:
            anomalies.append(Anomaly(
                rule_name=self.rule.name,
                watcher_type="http-health-check",
                source=url,
                message=f"Unexpected error checking {url}: {e}",
                severity=self.rule.severity,
                raw_data=str(e),
            ))
            self.record_failure()

        return anomalies


# ---------------------------------------------------------------------------
# Monitor — main coordinator
# ---------------------------------------------------------------------------

class Monitor:
    """Main monitoring coordinator.

    Manages watchers, runs check cycles, triggers fixer agents via Kanban,
    verifies resolution, and escalates persistent anomalies.

    Usage:
        monitor = Monitor(kanban=kanban)
        monitor.add_rule(WatcherRule(name="app-errors", type="file-watcher", target="/var/log/app.log", pattern="ERROR"))
        monitor.add_rule(WatcherRule(name="api-health", type="http-health-check", target="https://api.example.com/health"))
        result = monitor.run_cycle()
    """

    def __init__(
        self,
        kanban: Optional[Kanban] = None,
        fixer_agent: Optional[Agent] = None,
        notifier: Optional[Callable[[str], None]] = None,
        history_size: int = 100,
    ):
        self._watchers: dict[str, Watcher] = {}
        self._rules: dict[str, WatcherRule] = {}
        self._active_anomalies: dict[str, Anomaly] = {}  # anomaly_id -> Anomaly
        self._anomaly_history: list[Anomaly] = []
        self._history_size = history_size
        self._kanban = kanban
        self._fixer_agent = fixer_agent
        self._notifier = notifier
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._cycle_count: int = 0

    # ---- Rule / Watcher management ---------------------------------------

    def add_rule(self, rule: WatcherRule) -> Watcher:
        """Register a new watcher rule and create its watcher instance."""
        if rule.name in self._rules:
            raise ValueError(f"Rule '{rule.name}' already exists")

        watcher = self._build_watcher(rule)
        with self._lock:
            self._rules[rule.name] = rule
            self._watchers[rule.name] = watcher
        logger.info("Monitor: added rule '%s' (type=%s, target=%s)", rule.name, rule.type, rule.target)
        return watcher

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a watcher rule by name."""
        with self._lock:
            existed = rule_name in self._rules
            self._rules.pop(rule_name, None)
            self._watchers.pop(rule_name, None)
        if existed:
            logger.info("Monitor: removed rule '%s'", rule_name)
        return existed

    def get_rule(self, rule_name: str) -> Optional[WatcherRule]:
        return self._rules.get(rule_name)

    def list_rules(self) -> list[WatcherRule]:
        return list(self._rules.values())

    def get_watcher(self, rule_name: str) -> Optional[Watcher]:
        return self._watchers.get(rule_name)

    # ---- Cycle execution -------------------------------------------------

    def run_cycle(self) -> MonitorResult:
        """Execute one full monitoring cycle.

        1. Check all eligible watchers
        2. Detect anomalies against thresholds
        3. Trigger fixers for new anomalies
        4. Verify previously unresolved anomalies
        5. Escalate if max retries exceeded
        """
        start_time = time.time()
        result = MonitorResult(
            cycle_start=datetime.now(timezone.utc).isoformat(),
        )

        with self._lock:
            watchers = list(self._watchers.values())
            rules = dict(self._rules)

        result.total_watchers = len(watchers)

        for watcher in watchers:
            rule = rules.get(watcher.name)
            if rule is None or not rule.enabled:
                continue

            if not watcher.should_check():
                continue

            result.watchers_checked += 1

            try:
                anomalies = watcher.check()
                watcher.mark_checked()
            except Exception as e:
                logger.error("Monitor: watcher '%s' check failed: %s", watcher.name, e)
                result.errors.append(f"Watcher '{watcher.name}': {e}")
                continue

            for anomaly in anomalies:
                self._register_anomaly(anomaly)
                result.anomalies.append(anomaly)
                result.anomalies_detected += 1

                # Trigger fixer
                task_id = self._trigger_fixer(anomaly)
                if task_id:
                    anomaly.fixer_task_id = task_id
                    result.fixer_task_ids.append(task_id)

        # Verify previously unresolved anomalies
        self._verify_active_anomalies(result)

        # Escalation check
        self._check_escalation(result)

        result.cycle_end = datetime.now(timezone.utc).isoformat()
        result.duration_ms = int((time.time() - start_time) * 1000)
        result.success = len(result.errors) == 0
        self._cycle_count += 1

        # Prune history
        while len(self._anomaly_history) > self._history_size:
            self._anomaly_history.pop(0)

        return result

    # ---- Continuous loop --------------------------------------------------

    def start(self, daemon: bool = True):
        """Start the monitor loop in a background thread."""
        if self._running:
            logger.warning("Monitor is already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=daemon, name="monitor-loop")
        self._thread.start()
        logger.info("Monitor: started continuous loop")

    def stop(self, timeout: float = 5.0):
        """Stop the monitor loop."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        logger.info("Monitor: stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    def _loop(self):
        """Continuous monitoring loop."""
        while self._running:
            try:
                result = self.run_cycle()
                if not result.success:
                    logger.warning(
                        "Monitor cycle completed with %d error(s), %d anomaly(ies)",
                        len(result.errors),
                        result.anomalies_detected,
                    )
            except Exception as e:
                logger.error("Monitor cycle failed: %s", e)

            # Sleep in small increments so we can respond to stop() quickly
            for _ in range(10):
                if not self._running:
                    break
                time.sleep(0.5)

    # ---- Anomaly management -----------------------------------------------

    def _register_anomaly(self, anomaly: Anomaly):
        """Register or update an anomaly in the active set."""
        key = self._anomaly_key(anomaly)
        existing = self._active_anomalies.get(key)

        if existing:
            # Update existing: increment occurrence count
            existing.verification_attempts += 1
            existing.raw_data = anomaly.raw_data
            existing.timestamp = anomaly.timestamp
        else:
            self._active_anomalies[key] = anomaly
            self._anomaly_history.append(anomaly)

    def _anomaly_key(self, anomaly: Anomaly) -> str:
        """Generate a deduplication key for an anomaly."""
        return f"{anomaly.rule_name}:{anomaly.source}:{anomaly.message[:80]}"

    def resolve_anomaly(self, anomaly_id: str) -> bool:
        """Mark an anomaly as resolved."""
        for key, anomaly in list(self._active_anomalies.items()):
            if anomaly.id == anomaly_id:
                anomaly.resolved = True
                self._active_anomalies.pop(key, None)
                logger.info("Monitor: anomaly '%s' marked as resolved", anomaly_id)
                return True
        return False

    def list_active_anomalies(self) -> list[Anomaly]:
        return list(self._active_anomalies.values())

    def list_anomaly_history(self, limit: int = 50) -> list[Anomaly]:
        return self._anomaly_history[-limit:]

    # ---- Fixer & Remediation ---------------------------------------------

    def _trigger_fixer(self, anomaly: Anomaly) -> str:
        """Create a Kanban task and optionally spawn a fixer agent.

        Returns the task ID if a Kanban task was created, else empty string.
        """
        if not self._kanban:
            logger.debug("Monitor: no Kanban configured, skipping fixer trigger")
            return ""

        severity_label = {1: "CRITICAL", 2: "HIGH", 3: "MEDIUM", 4: "LOW"}.get(anomaly.severity, "UNKNOWN")
        title = f"[{severity_label}] {anomaly.rule_name}: {anomaly.message[:100]}"
        description = (
            f"Anomaly detected by monitor.\n\n"
            f"Watcher: {anomaly.watcher_type} ({anomaly.rule_name})\n"
            f"Source: {anomaly.source}\n"
            f"Message: {anomaly.message}\n"
            f"Severity: {anomaly.severity}\n"
            f"Detected at: {anomaly.timestamp}\n"
            f"Raw data: {anomaly.raw_data[:500]}\n"
        )

        try:
            task = self._kanban.create_task(
                title=title,
                description=description,
                assignee="monitor-fixer",
                priority=max(1, 5 - anomaly.severity),  # severity 1 -> priority 4
                status=TASK_STATUS_TODO,
            )

            # Spawn fixer agent if configured
            if self._fixer_agent:
                self._run_fixer_agent(anomaly, task.id)

            return task.id
        except Exception as e:
            logger.error("Monitor: failed to create Kanban task for anomaly '%s': %s", anomaly.id, e)
            return ""

    def _run_fixer_agent(self, anomaly: Anomaly, task_id: str):
        """Run the fixer agent in a background thread to remediate the anomaly."""
        def _fix():
            try:
                fixer_prompt = (
                    f"You are a DevOps remediation agent. An anomaly has been detected and "
                    f"a Kanban task has been created (ID: {task_id}).\n\n"
                    f"Anomaly Details:\n"
                    f"- Rule: {anomaly.rule_name}\n"
                    f"- Watcher Type: {anomaly.watcher_type}\n"
                    f"- Source: {anomaly.source}\n"
                    f"- Message: {anomaly.message}\n"
                    f"- Severity: {anomaly.severity}/4\n"
                    f"- Detection Time: {anomaly.timestamp}\n"
                    f"- Raw Data: {anomaly.raw_data[:500]}\n\n"
                    f"Please:\n"
                    f"1. Analyze the root cause of this anomaly\n"
                    f"2. Provide step-by-step remediation instructions\n"
                    f"3. Generate any commands or configuration changes needed\n"
                    f"4. Summarize what was done and whether the issue is resolved\n\n"
                    f"Be specific and actionable."
                )

                output = self._fixer_agent.run(fixer_prompt)

                # Update the Kanban task with fixer output
                if self._kanban:
                    self._kanban.update_task(
                        task_id,
                        status=TASK_STATUS_DONE,
                        output=output[:2000],
                    )

                logger.info("Monitor: fixer agent completed for task '%s'", task_id)

            except Exception as e:
                logger.error("Monitor: fixer agent failed for task '%s': %s", task_id, e)
                if self._kanban:
                    self._kanban.update_task(
                        task_id,
                        status=TASK_STATUS_FAILED,
                        output=f"Fixer agent error: {e}",
                    )

        thread = threading.Thread(target=_fix, daemon=True, name=f"fixer-{task_id}")
        thread.start()

    # ---- Verification & Escalation ----------------------------------------

    def _verify_active_anomalies(self, result: MonitorResult):
        """Check if previously active anomalies are still present.

        If an anomaly was fixed (no longer detected), mark it resolved.
        Otherwise, increment verification attempts.
        """
        resolved_keys: set[str] = set()

        for key, anomaly in list(self._active_anomalies.items()):
            rule = self._rules.get(anomaly.rule_name)
            if not rule or not rule.enabled:
                continue

            # Re-check the source to verify resolution.
            # Use the original watcher to re-check this specific anomaly source.
            still_active = self._verify_single_anomaly(anomaly)

            if not still_active:
                anomaly.resolved = True
                anomaly.verification_attempts += 1
                resolved_keys.add(key)
                result.resolved_count += 1
                logger.info(
                    "Monitor: anomaly '%s' resolved after %d verification(s)",
                    anomaly.id, anomaly.verification_attempts,
                )

                # Update Kanban task
                if self._kanban and anomaly.fixer_task_id:
                    self._kanban.update_task(
                        anomaly.fixer_task_id,
                        status=TASK_STATUS_DONE,
                        output=f"Anomaly resolved after verification. Final verification: {anomaly.verification_attempts} attempt(s).",
                    )
            else:
                anomaly.verification_attempts += 1

        # Remove resolved anomalies from active set
        for key in resolved_keys:
            self._active_anomalies.pop(key, None)

    def _verify_single_anomaly(self, anomaly: Anomaly) -> bool:
        """Check if a specific anomaly is still active.

        Returns True if the anomaly is still present (unresolved).
        """
        watcher = self._watchers.get(anomaly.rule_name)
        if not watcher:
            return False  # Watcher removed, consider resolved

        try:
            current_anomalies = watcher.check()
            for ca in current_anomalies:
                if self._anomaly_key(ca) == self._anomaly_key(anomaly):
                    return True  # Still present
            return False  # No longer detected
        except Exception:
            return True  # Error during verification — assume still active

    def _check_escalation(self, result: MonitorResult):
        """Escalate anomalies that have exceeded max retries.

        Calls the notifier callback if one is configured.
        """
        for anomaly in list(self._active_anomalies.values()):
            rule = self._rules.get(anomaly.rule_name)
            max_attempts = rule.max_retries if rule else 3

            if anomaly.verification_attempts >= max_attempts and not anomaly.resolved:
                result.escalated = True
                escalation_msg = (
                    f"[ESCALATION] Anomaly '{anomaly.id}' ({anomaly.rule_name}) "
                    f"remains unresolved after {anomaly.verification_attempts} attempt(s).\n"
                    f"Source: {anomaly.source}\n"
                    f"Message: {anomaly.message}\n"
                    f"Severity: {anomaly.severity}/4\n"
                    f"First detected: {anomaly.timestamp}\n"
                    f"Fixer task: {anomaly.fixer_task_id}\n"
                    f"Action required: Manual intervention needed."
                )

                logger.warning("Monitor escalation: %s", escalation_msg)

                # Update Kanban with escalation status
                if self._kanban and anomaly.fixer_task_id:
                    self._kanban.update_task(
                        anomaly.fixer_task_id,
                        status=TASK_STATUS_FAILED,
                        output=f"Escalated after {anomaly.verification_attempts} attempts. Manual intervention required.",
                    )

                # Call notifier
                if self._notifier:
                    try:
                        self._notifier(escalation_msg)
                    except Exception as e:
                        logger.error("Monitor: notifier failed for escalation: %s", e)

    # ---- Helpers ----------------------------------------------------------

    @staticmethod
    def _build_watcher(rule: WatcherRule) -> Watcher:
        """Factory: create the correct watcher type from a rule."""
        if rule.type == "file-watcher":
            return FileWatcher(rule)
        elif rule.type == "http-health-check":
            return HttpHealthCheckWatcher(rule)
        else:
            raise ValueError(f"Unknown watcher type: '{rule.type}'. Supported: file-watcher, http-health-check")


# ---------------------------------------------------------------------------
# MonitorAgent — An agent that runs health checks
# ---------------------------------------------------------------------------

class MonitorAgent:
    """A watcher agent that runs health checks using an LLM-powered Agent.

    The MonitorAgent wraps an Agent instance and provides methods to
    interpret check results, generate remediation plans, and produce
    human-readable monitoring reports.
    """

    def __init__(
        self,
        agent: Agent,
        monitor: Optional[Monitor] = None,
    ):
        self.agent = agent
        self.monitor = monitor

    @classmethod
    def create(
        cls,
        name: str = "monitor-agent",
        monitor: Optional[Monitor] = None,
    ) -> "MonitorAgent":
        """Factory: create a MonitorAgent with a default profile."""
        profile = Profile(
            name=name,
            display="Monitor Agent",
            soul=SoulConfig(
                role="DevOps Monitoring Agent",
                expertise=[
                    "system-health-check",
                    "log-analysis",
                    "anomaly-detection",
                    "incident-response",
                    "remediation",
                    "observability",
                ],
                personality="Vigilant, methodical, proactive",
                communication="Clear with data-driven observations and actionable recommendations",
            ),
            skills=["monitoring", "devops", "remediation"],
        )
        agent = Agent(profile)
        return cls(agent=agent, monitor=monitor)

    def analyze_anomaly(self, anomaly: Anomaly) -> str:
        """Use the LLM agent to analyze a specific anomaly and recommend action."""
        prompt = (
            f"Analyze the following monitoring anomaly and provide a root cause analysis "
            f"along with recommended remediation steps.\n\n"
            f"Anomaly Details:\n"
            f"- Rule: {anomaly.rule_name}\n"
            f"- Watcher Type: {anomaly.watcher_type}\n"
            f"- Source: {anomaly.source}\n"
            f"- Message: {anomaly.message}\n"
            f"- Severity: {anomaly.severity}/4\n"
            f"- Raw Data: {anomaly.raw_data[:500]}\n\n"
            f"Provide:\n"
            f"1. Root cause analysis (what went wrong)\n"
            f"2. Impact assessment (what systems/users are affected)\n"
            f"3. Recommended remediation steps (step-by-step)\n"
            f"4. Prevention measures (how to avoid this in the future)"
        )
        return self.agent.run(prompt)

    def generate_report(self, result: MonitorResult) -> str:
        """Generate a human-readable monitoring report from a cycle result."""
        prompt = (
            f"Generate a concise monitoring report based on the following cycle result.\n\n"
            f"Monitor Cycle Report:\n"
            f"- Watchers checked: {result.watchers_checked}/{result.total_watchers}\n"
            f"- Anomalies detected: {result.anomalies_detected}\n"
            f"- Resolved: {result.resolved_count}\n"
            f"- Escalated: {result.escalated}\n"
            f"- Duration: {result.duration_ms}ms\n"
            f"- Errors: {len(result.errors)}\n\n"
        )

        if result.anomalies:
            prompt += "Anomalies:\n"
            for a in result.anomalies:
                prompt += f"  - [{a.severity}] {a.rule_name}: {a.message[:120]}\n"

        if result.errors:
            prompt += "\nErrors:\n"
            for e in result.errors:
                prompt += f"  - {e}\n"

        prompt += "\nProvide a clear executive summary with actionable insights."

        return self.agent.run(prompt)

    def check_health(self, rule: WatcherRule) -> str:
        """Run a health check using the watcher and return an AI-analyzed result."""
        watcher = Monitor._build_watcher(rule)
        anomalies = watcher.check()
        watcher.mark_checked()

        if not anomalies:
            return f"✅ Health check passed for '{rule.name}' ({rule.target}) — no anomalies detected."

        summary_parts = [f"⚠️  Health check for '{rule.name}' ({rule.target}) detected {len(anomalies)} anomaly(ies):"]
        for a in anomalies:
            summary_parts.append(f"  - [{a.severity}] {a.message}")
        summary_parts.append("")

        analysis = self.analyze_anomaly(anomalies[0])
        summary_parts.append(f"AI Analysis:\n{analysis}")

        return "\n".join(summary_parts)

    def run_diagnostic(self, target: str, description: str = "") -> str:
        """Run a general diagnostic against a target using the LLM agent."""
        prompt = (
            f"Perform a system diagnostic for the following target.\n\n"
            f"Target: {target}\n"
            f"Description: {description or 'General health check'}\n\n"
            f"Please provide:\n"
            f"1. What checks should be performed\n"
            f"2. Expected healthy state\n"
            f"3. Common failure modes\n"
            f"4. Recommended monitoring rules\n"
            f"5. Remediation playbook for common issues"
        )
        return self.agent.run(prompt)
