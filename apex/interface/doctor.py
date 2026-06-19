"""Apex Doctor — system diagnostics and auto-repair.

Usage:
  apex doctor              Full diagnostic report
  apex doctor --fix        Auto-fix common issues
  apex doctor --json       Machine-readable output
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm
from rich import box

from apex.core.config import get_config, config_exists

console = Console()
TZ = timezone(timedelta(hours=8))

# ─── Models ───────────────────────────────────────────────────────


@dataclass
class CheckResult:
    name: str
    status: str  # ok | warn | error | skip
    message: str
    fixable: bool = False
    fix_command: str = ""


@dataclass
class DiagnosticReport:
    timestamp: str
    system: dict
    tools: list[CheckResult]
    config: list[CheckResult]
    fleet: list[CheckResult]
    network: list[CheckResult]
    all_ok: bool
    issues: list[str]
    recommendations: list[str]


# ─── Doctor Engine ────────────────────────────────────────────────


class Doctor:
    """System diagnostic and auto-repair engine."""

    def __init__(self):
        self.results: dict[str, list[CheckResult]] = {
            "system": [],
            "tools": [],
            "config": [],
            "fleet": [],
            "network": [],
        }

    def run_all(self) -> DiagnosticReport:
        """Run all diagnostic checks."""
        self._check_system()
        self._check_tools()
        self._check_config()
        self._check_fleet()
        self._check_network()

        all_checks = (
            self.results["system"]
            + self.results["tools"]
            + self.results["config"]
            + self.results["fleet"]
            + self.results["network"]
        )

        errors = [c for c in all_checks if c.status == "error"]
        warnings = [c for c in all_checks if c.status == "warn"]
        all_ok = len(errors) == 0

        issues = []
        for c in errors + warnings:
            icon = "🔴" if c.status == "error" else "🟡"
            issues.append(f"{icon} {c.name}: {c.message}")

        recommendations = []
        for c in errors:
            if c.fixable:
                recommendations.append(f"Run: {c.fix_command}")

        return DiagnosticReport(
            timestamp=datetime.now(TZ).isoformat(),
            system={
                "os": sys.platform,
                "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "arch": __import__("platform").machine(),
                "hostname": __import__("platform").node(),
            },
            tools=self.results["tools"],
            config=self.results["config"],
            fleet=self.results["fleet"],
            network=self.results["network"],
            all_ok=all_ok,
            issues=issues,
            recommendations=recommendations,
        )

    def auto_fix(self) -> list[str]:
        """Attempt to auto-fix common issues."""
        fixed = []
        report = self.run_all()

        for check in (
            self.results["system"]
            + self.results["tools"]
            + self.results["config"]
            + self.results["fleet"]
        ):
            if check.status in ("error", "warn") and check.fixable:
                try:
                    subprocess.run(
                        check.fix_command, shell=True,
                        capture_output=True, timeout=30,
                    )
                    fixed.append(f"✅ {check.name}: {check.fix_command}")
                except Exception as e:
                    fixed.append(f"❌ {check.name}: {str(e)[:60]}")

        return fixed

    # ── Check Methods ─────────────────────────────────────────────

    def _check_system(self):
        checks = self.results["system"]

        # Python version
        checks.append(CheckResult(
            "Python版本", "ok" if sys.version_info >= (3, 10) else "error",
            f"Python {sys.version}",
            fixable=False,
        ))

        # macOS version
        if sys.platform == "darwin":
            try:
                ver = __import__("platform").mac_ver()[0]
                checks.append(CheckResult("macOS", "ok", f"macOS {ver}"))
            except Exception:
                checks.append(CheckResult("macOS", "warn", "Could not detect version"))

        # Disk space
        try:
            stat = shutil.disk_usage(Path.home())
            free_gb = stat.free / (1024 ** 3)
            if free_gb < 1:
                checks.append(CheckResult(
                    "磁盘空间", "error", f"Only {free_gb:.1f}GB free", fixable=False,
                ))
            else:
                checks.append(CheckResult(
                    "磁盘空间", "ok", f"{free_gb:.0f}GB free",
                ))
        except Exception:
            pass

    def _check_tools(self):
        checks = self.results["tools"]
        tools = [
            ("tmux", "tmux", "brew install tmux"),
            ("git", "git", "xcode-select --install"),
            ("python3", "python3", "brew install python@3.12"),
            ("hermes", "Hermes Agent", None),
            ("gh", "GitHub CLI", "brew install gh"),
            ("docker", "Docker", "brew install docker"),
            ("curl", "curl", None),
        ]
        for name, display, fix_cmd in tools:
            installed = shutil.which(name) is not None
            checks.append(CheckResult(
                display, "ok" if installed else "warn",
                "已安装" if installed else "未安装",
                fixable=fix_cmd is not None,
                fix_command=fix_cmd or "",
            ))

        # Check Hermes version
        try:
            result = subprocess.run(
                ["hermes", "--version"], capture_output=True, text=True, timeout=5,
            )
            for c in checks:
                if c.name == "Hermes Agent" and c.status == "ok":
                    c.message = result.stdout.strip()[:40]
        except Exception:
            pass

    def _check_config(self):
        checks = self.results["config"]

        has_config = config_exists()
        checks.append(CheckResult(
            "配置文件", "ok" if has_config else "warn",
            "~/.apex/config.yaml 存在" if has_config else "未找到 — 运行 apex setup",
            fixable=True,
            fix_command="apex setup --quick",
        ))

        if has_config:
            try:
                cfg = get_config()
                checks.append(CheckResult(
                    "模型配置", "ok" if cfg.model.default else "warn",
                    f"模型: {cfg.model.default}" if cfg.model.default else "未配置",
                ))
                checks.append(CheckResult(
                    "API Key", "ok" if os.environ.get(cfg.model.api_key_env) else "warn",
                    f"环境变量 {cfg.model.api_key_env} {'已设置' if os.environ.get(cfg.model.api_key_env) else '未设置'}",
                ))
            except Exception as e:
                checks.append(CheckResult(
                    "配置解析", "error", str(e)[:60],
                ))

    def _check_fleet(self):
        checks = self.results["fleet"]
        try:
            from apex.fleet import TmuxFleetManager
            fm = TmuxFleetManager()
            state = fm.exists
            if state:
                status = fm.status()
                checks.append(CheckResult(
                    "Fleet会话", "ok", f"运行中 ({status.total_windows} agents)",
                ))
            else:
                checks.append(CheckResult(
                    "Fleet会话", "warn", "未运行 — apex fleet start",
                    fixable=True, fix_command="apex fleet start",
                ))
        except Exception as e:
            checks.append(CheckResult(
                "Fleet会话", "error", str(e)[:60],
            ))

        # Check Hermes profiles
        profiles_dir = Path.home() / ".hermes" / "profiles"
        if profiles_dir.exists():
            count = len([d for d in profiles_dir.iterdir() if d.is_dir()])
            checks.append(CheckResult(
                "Agent Profiles", "ok" if count >= 3 else "warn",
                f"{count} profiles",
            ))

    def _check_network(self):
        checks = self.results["network"]
        import urllib.request

        endpoints = [
            ("GitHub", "https://github.com"),
            ("PyPI", "https://pypi.org"),
            ("DeepSeek API", "https://api.deepseek.com"),
        ]
        for name, url in endpoints:
            try:
                urllib.request.urlopen(url, timeout=5)
                checks.append(CheckResult(name, "ok", "可达"))
            except Exception:
                checks.append(CheckResult(name, "warn", "不可达"))


# ─── Renderer ─────────────────────────────────────────────────────


def render_diagnostic(report: DiagnosticReport, verbose: bool = True):
    """Render diagnostic report with Rich."""
    console.print()
    status_color = "green" if report.all_ok else "yellow"
    console.print(Panel(
        f"[bold {status_color}]🔍 Apex Doctor[/]\n"
        f"[dim]{report.timestamp[:19]}[/]",
        border_style=status_color,
    ))

    # System info
    sys = report.system
    console.print(f"[dim]System: {sys['os']} | Python {sys['python']} | {sys['arch']} | {sys['hostname']}[/]")
    console.print()

    # Results table
    sections = [
        ("💻 系统", report.tools[:4]),  # tmux, git, python, hermes
        ("⚙️ 配置", report.config),
        ("🚀 舰队", report.fleet),
        ("🌐 网络", report.network),
    ]

    for section_name, checks in sections:
        if not checks:
            continue
        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column("状态", width=2)
        table.add_column("项目", style="bold", width=15)
        table.add_column("详情", style="dim")

        for c in checks:
            icon = {"ok": "✅", "warn": "🟡", "error": "🔴"}.get(c.status, "❓")
            table.add_row(icon, c.name, c.message)

        console.print(f"[bold]{section_name}[/]")
        console.print(table)
        console.print()

    # Issues
    if report.issues:
        console.print(Panel(
            "\n".join(report.issues),
            title="⚠ 问题",
            border_style="yellow",
        ))

    # Recommendations
    if report.recommendations:
        console.print("\n[bold]🔧 修复建议:[/]")
        for rec in report.recommendations:
            console.print(f"  {rec}")

    # Summary
    if report.all_ok:
        console.print("\n[green]✅ 一切正常，系统就绪！[/]")
    else:
        error_count = sum(
            1 for c in report.config + report.fleet + report.tools
            if c.status == "error"
        )
        warn_count = sum(
            1 for c in report.config + report.fleet + report.tools
            if c.status == "warn"
        )
        console.print(
            f"\n[yellow]{error_count} errors, {warn_count} warnings[/]"
        )
        console.print("[dim]运行 apex doctor --fix 自动修复[/]")


def render_json(report: DiagnosticReport):
    """Output JSON format."""
    output = {
        "timestamp": report.timestamp,
        "all_ok": report.all_ok,
        "system": report.system,
        "checks": {},
        "issues": report.issues,
        "recommendations": report.recommendations,
    }
    for cat, checks in [
        ("tools", report.tools), ("config", report.config),
        ("fleet", report.fleet), ("network", report.network),
    ]:
        output["checks"][cat] = [
            {"name": c.name, "status": c.status, "message": c.message}
            for c in checks
        ]
    print(json.dumps(output, indent=2, ensure_ascii=False))
