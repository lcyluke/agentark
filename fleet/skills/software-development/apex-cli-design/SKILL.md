---
name: apex-cli-design
description: CLI hierarchy design for Click-based developer tools (Apex fleet). Covers 7±2 group principle, backward compatibility via hidden aliases, per-command parameter injection for Hermes profiles, Rich Panel quickstart/help, Mac Terminal window integration with agent name display, and apex survey competitive analysis pattern.
category: software-development
triggers:
  - User wants to redesign CLI command structure
  - User says "CLI is messy" / "commands are unorganized" / "need better --help"
  - User asks for beginner-friendly quickstart or setup wizard
  - Refactoring Click-based CLI from flat to hierarchical
  - Adding --model / --token-limit / --input-lines per-command config
  - Hermes terminal window integration from Apex
  - User asks for competitive analysis or market research command
  - Adding a survey/research command that uses parallel workers
---

# ⚓ Apex CLI Design Patterns

## Core Principle: 7±2 Grouping

The human brain can hold 5-9 items in working memory. CLI hierarchies should reflect this:

```
❌ Before (36 flat commands — overwhelming)
  apex autonomous bridge capacity chain chat company ...
  
✅ After (9 groups + 8 top-level — scanable)
  top-level:  init run chat dashboard demo status setup quickstart survey
  groups:     task team fleet mode project system help origin integrate
```

## CLI Hierarchy Template

```python
@click.group()
def cli():
    """⚓ Apex — One person, infinite capacity."""
    pass

# ── Top-level (no nesting, used daily) ──
@cli.command()
@click.argument("name")
def init(name):
    """🚀 Initialize a project"""
    ...

@cli.command()
@click.argument("task")
@click.option("--profile", "-p")
def run(task, profile):
    """▶️ Execute a task"""
    ...

@cli.command()
@click.argument("topic")
@click.option("--github-only", is_flag=True)
@click.option("--quick", is_flag=True)
def survey(topic, github_only, quick):
    """🔍 Competitive survey & market research"""
    ...

# ── Groups (sub-commands for related actions) ──
@cli.group()
def task():
    """📋 Task Management — create, dispatch, schedule"""

@task.command(name="create")
@click.argument("title")
def task_create(title):
    ...

@task.command(name="dispatch-smart")
@click.argument("requirement")
def task_dispatch_smart(requirement):
    ...

@cli.group()
def team():
    """👥 Team Management — create, start, template, sync"""

@team.command(name="start")
def team_start():
    ...

@team.command(name="template")
@click.argument("template_name")
def team_template(template_name):
    ...
```

## Naming Conventions

| Convention | Example | Rationale |
|------------|---------|-----------|
| `verb-noun` args | `dispatch-smart` | Click converts hyphens to underscores |
| Group name = domain | `task`, `team`, `fleet` | Intuitive mental model |
| Sub-command = action | `create`, `list`, `start`, `status` | Consistent verb reuse |
| Emoji prefix in docstring | `"""📋 Task Management"""` | Rich help improves scanability |
| Hidden deprecated aliases | `@cli.command(hidden=True)` | Backward compat without clutter |

## Rich Panel Quickstart Guide

For beginner-friendly output, use Rich Panel (NOT Click's help formatter — `formatter.write_text` wraps lines unpredictably):

```python
@cli.command(name="quickstart")
def quickstart():
    """🚀 Show quick start guide"""
    from rich.panel import Panel
    panel = Panel.fit(
        "[bold cyan]🚀 Quick Start[/]\n\n"
        "[bold]FIRST STEPS[/]\n"
        "  [green]apex setup --quick[/]     One-click config\n"
        "  [green]apex team start[/]        Launch agents\n\n"
        "[bold]EVERYDAY[/]\n"
        "  [green]apex task dispatch \"idea\"[/]  Decompose & assign\n"
        "  [green]apex fleet status[/]          Check status",
        border_style="cyan",
        title="⚓ Apex",
    )
    console.print(panel)
```

## Backward Compatibility Pattern

Always keep old flat commands working with deprecation notices:

```python
@cli.command(hidden=True)              # hidden=True → not shown in --help
@click.argument("topic")
@click.pass_context
def debate(ctx, topic):
    """[DEPRECATED] Use: apex mode debate"""
    console.print("[dim]⚠️ deprecated — use [cyan]apex mode debate[/] instead[/]")
    ctx.invoke(mode_debate, topic=topic)  # Forward to new command
```

Key points:
- `hidden=True` removes from `--help` output but keeps command functional
- `@click.pass_context` + `ctx.invoke()` lets you redirect to the new handler
- Old scripts and muscle memory continue working

## Per-Command Parameter Injection

When you need to pass tool-specific config (model, token limit, input lines) through Apex to Hermes profiles, inject them as per-command options that write to the profile's `config.yaml`:

```python
@click.option("--model", "-m", default=None, help="Override model")
@click.option("--token-limit", type=int, default=0, help="Max tokens")
@click.option("--input-lines", type=int, default=3, help="TUI input height")
```

### Helper function pattern

```python
HERMES_HOME = Path(os.environ.get("HERMES_HOME", "~/.hermes"))

def _configure_profile_model(profile_name: str, model: Optional[str]):
    """Write model override to Hermes profile config.yaml."""
    if not model:
        return
    profile_dir = HERMES_HOME / "profiles" / profile_name
    if not profile_dir.exists():
        return
    config_file = profile_dir / "config.yaml"
    try:
        import yaml
        with open(config_file) as f:
            cfg = yaml.safe_load(f) or {}
        if "model" not in cfg:
            cfg["model"] = {}
        cfg["model"]["default"] = model
        with open(config_file, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
    except:
        pass
```

Apply the same pattern for:
- `_configure_token_limit()` → writes to `agent.max_tokens_per_turn`
- `_configure_input_lines()` → writes to `display.composer_lines` + `display.multi_line_composer`

## Mac Terminal Window Integration

When opening Hermes agent terminals from Apex, set the window title to show the agent badge + name:

```python
badge = DEV_SQUAD[agent_name].get("badge", "●")
script = (
    'tell application "Terminal" to do script '
    '"export HERMES_COMPOSER_LINES={input_lines}'
    ' && echo -ne \\"\\\\033]0;{badge} {agent_name} ⚓ Apex\\\\007\\"'
    ' && {wrapper} chat"'
)
```

The `\033]0;...\007` OSC escape sets the terminal title. This is macOS-specific (uses `osascript` for AppleScript).

## Shell Wrapper Script Pattern

For `apex setup`, generate executable wrapper scripts at `~/.local/bin/<agent-name>`:

```bash
#!/bin/bash
# Apex Agent Wrapper: architect
export HERMES_COMPOSER_LINES=3
export APEX_AGENT_NAME="architect"
echo -ne "\033]0;architect ⚓ Apex\007"
exec hermes -p "architect" "$@"
```

## Hermes-Style `--help` Formatter

For the root CLI, override `click.Group.format_help` to produce a clean, grouped output matching Hermes Agent's style:

```
Apex --help                                           Sat Jun 06 00:38:19

usage: apex [-h] [--version] {command} ...

Apex - multi-Agent operating system. One person, infinite capacity.

SETUP & START:
    setup                        First-time setup: install, configure, launch
    quickstart                   Show quick start guide
    init                         Initialize a new Apex project

DAILY USE:
    run                          Execute a task
    chat                         Chat with an Apex agent.
    survey                       Competitive survey & market research
    ...

options:
    -h, --help                   show this help message and exit
    --version, -V                Show version and exit

    Per-command overrides:
    --model MODEL                Model override per command
    --token-limit N              Per-session token cap

Examples:
    apex setup --quick           First-time setup
    apex fleet status            Check agent status
    apex survey "AI FinOps"      Competitive analysis
    ...

For more help on a command:
    apex <command> --help
```

### Implementation

This is a monkey-patch on `click.Group.format_help` that uses `write()` (not `write_text()`) to prevent line wrapping:

```python
import shutil
from datetime import datetime

# Save original for sub-group fallback
original_format_help = click.Group.format_help

def format_apex_help(self, ctx, formatter):
    # Root CLI only — sub-groups use standard Click format
    if getattr(self, "name", None) is not None and self.name not in (None, "cli"):
        original_format_help(self, ctx, formatter)
        return

    terminal_width = shutil.get_terminal_size((80, 20)).columns
    now_str = datetime.now().strftime("%a %b %d %H:%M:%S")

    # Header with right-aligned timestamp
    formatter.write(f"Apex --help{' ' * (terminal_width - 18 - len(now_str))}{now_str}\n")
    formatter.write("\n")
    formatter.write("usage: apex [-h] [--version] {command} ...\n")
    formatter.write("\n")
    formatter.write("Apex - multi-Agent operating system. One person, infinite capacity.\n")
    formatter.write("\n")

    # Grouped commands
    groups = [
        ("SETUP & START", ["setup", "quickstart", "init", "demo"]),
        ("DAILY USE", ["run", "chat", "status", "survey", "dashboard"]),
        ("TASK MANAGEMENT", ["task"]),
        ("TEAM & AGENTS", ["team"]),
        ("FLEET & MONITORING", ["fleet"]),
        ("COLLABORATION MODES", ["mode"]),
        ("PROJECT MANAGEMENT", ["project"]),
        ("SYSTEM", ["system"]),
        ("HELP & INTEGRATION", ["help", "integrate"]),
        ("GLOBAL COMMANDS", ["origin", "crew"]),
    ]
    for group_name, cmd_names in groups:
        formatter.write(f"{group_name}:\n")
        for name in cmd_names:
            if name in cmd_data:
                formatter.write(f"    {name:<28s} {desc}\n")
        formatter.write("\n")

    # Options section
    formatter.write("options:\n")
    opts = [
        ("-h, --help", "show this help message and exit"),
        ("--version, -V", "Show version and exit"),
    ]
    for flag, desc in opts:
        formatter.write(f"    {flag:<45s} {desc}\n")

    # Examples section — include survey example
    formatter.write("Examples:\n")
    examples = [
        ("apex setup --quick", "First-time setup (quick, all defaults)"),
        ("apex team template webapp", "Create a 4-agent development team"),
        ("apex fleet status", "Show agent fleet status dashboard"),
        ("apex survey \"AI FinOps\"", "Competitive analysis — market research"),
        ...
    ]
    for cmd_example, desc in examples:
        formatter.write(f"    {cmd_example:<55s} {desc}\n")
    formatter.write("\n")

    formatter.write("For more help on a command:\n")
    formatter.write("    apex <command> --help\n")

# Apply the patch
click.Group.format_help = format_apex_help
```

### Key rules

| Rule | Reason |
|------|--------|
| Use `formatter.write()` not `write_text()` | `write_text()` wraps lines unpredictably at word boundaries; `write()` gives full control |
| Root-only check | Sub-groups (`task`, `team`, etc.) should keep standard Click format for discoverability of sub-commands |
| Save original before patching | Needed for sub-group fallback (`original_format_help(self, ctx, formatter)`) |
| Timestamp right-aligned | Matches Hermes CLI aesthetic (uses `shutil.get_terminal_size()`) |
| Emoji stripping for clean help output | Use `unicodedata.category(stripped[0]) == 'So'` to detect and strip emoji prefixes from command descriptions |
| Command names left-padded to 28 chars | Ensures alignment across groups |
| Examples left-padded to 55 chars | Consistent column alignment |
| Include `survey` in DAILY USE group | User validates this as a daily command |

## First-Time Setup Wizard

Create a dedicated `apex setup` command for beginners:

```python
@cli.command()
@click.option("--quick", is_flag=True, help="Quick setup with defaults")
@click.option("--check", "check_mode", is_flag=True, help="Check installation status")
@click.option("--model", default=None, help="Force specific model (skips auto-detect)")
@click.option("--token-limit", type=int, default=None)
@click.option("--input-lines", type=int, default=None)
def setup(quick, check_mode, model, token_limit, token_budget, input_lines):
    """🚀 First-time setup: install, configure, launch your AI fleet"""
    if check_mode:
        setup_cmds.check_cmd()
        return
    setup_cmds.setup_cmd(quick=quick, model=model, ...)
```

The setup wizard runs 5 steps:

| Step | Action | Mode |
|------|--------|------|
| 1/5 | Check Hermes Agent installation | auto |
| 2/5 | Create default Hermes profiles | auto |
| 3/5 | **Auto-detect model provider & configure** | auto (zero-interaction in 99% of cases) |
| 4/5 | Install shell wrapper scripts | auto |
| 5/5 | Verify configuration | auto |

Use Rich `Progress(SpinnerColumn(), TextColumn(), BarColumn())` for visual feedback.

### Step 3: Model Auto-Detection (replaces 4 manual prompts)

**Old (slow):** 4 `Prompt.ask()` calls — model name, token limit, token budget, input lines. 15-30 seconds of manual entry.

**New (fast):** Zero-interaction auto-detection:

```python
# In setup_cmds.py step 3 handler:
from apex.cli.commands.model_detect import detect_models
detected = detect_models()
providers = detected.get("providers", {})
if providers:
    best = _pick_best_provider(providers)  # priority-ordered selection
    model_cfg = best["model"]               # e.g. "deepseek-v4-pro"
    # Auto-write to all Hermes profile configs, no user input needed
```

The only time manual prompts appear: when `detect_models()` finds zero providers (no API keys, no tools configured) AND `--quick` is not set.

### Provider Priority Order

```python
PRIORITY_ORDER = ["deepseek", "aws-bedrock", "anthropic", "openai", "google", "openrouter"]
```

`_pick_best_provider()` iterates this list and returns the first match. DeepSeek wins on cost ($1/1M input), AWS Bedrock on SSO convenience (no API key needed), Anthropic on code quality.

### Standalone Model Detection CLI

The `apex model-detect` command is registered as a top-level command for standalone use:

```python
@cli.command("model-detect")
def model_detect():
    """🔍 Auto-detect available AI models from environment, tools, and cloud"""
    from apex.cli.commands.model_detect import detect_models
    # Scans: env vars (DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY),
    #        tool configs (~/.hermes, ~/.kiro, ~/.claude, ~/.cursor),
    #        AWS SSO cache (~/.aws/sso/cache/*.json)
    # Returns: Rich tables of detected providers, models, auth methods
```

See `references/model-auto-detect.md` for the full detection architecture and provider signatures.

## Survey / Competitive Analysis Command Pattern

When adding a `apex survey` command that researches markets or competitors using parallel workers, follow this structure:

### CLI Definition

```python
@cli.command()
@click.argument("topic")
@click.option("--github-only", is_flag=True, help="Only open-source GitHub projects")
@click.option("--saas-only", is_flag=True, help="Only commercial/SaaS products")
@click.option("--quick", is_flag=True, help="Quick overview (less depth)")
@click.option("--output", "-o", default="rich", type=click.Choice(["rich", "markdown"]))
@click.option("--workers", "-w", default=3, type=int, help="Parallel research workers")
def survey(topic, github_only, saas_only, quick, output, workers):
    """🔍 Competitive survey & market research"""
    survey_cmds.survey_cmd(topic=topic, ...)
```

### Research Engine Architecture

The survey engine uses parallel workers (ThreadPoolExecutor) to research multiple aspects simultaneously:

```
apex survey "topic"
       |
  ┌────┤────┐
Worker 1  Worker 2  Synthesizer
GitHub    Commercial → Rich Tables
(search   (directory  + AI Summary
 repos)    lookup)
```

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def survey_cmd(topic, github_only, saas_only, quick, output, workers):
    # Define research tasks
    tasks = []
    if not saas_only:
        tasks.append(("github", lambda: search_github(topic, limit)))
    if not github_only:
        tasks.append(("commercial", lambda: search_commercial(topic, limit)))

    # Execute in parallel
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fn): name for name, fn in tasks}
        for future in as_completed(futures):
            entries = future.result()
            # Merge results

    # Generate AI analysis
    result.ai_summary = generate_analysis(topic, result.projects)

    # Render as comparison tables or markdown
    render_table(result)
```

### Output Format

Rich comparison tables with:
- Open-source: Project name, Stars, Language, License, Key Features, Last Updated
- Commercial: Product name, Pricing, Description, Key Features, Category
- AI-generated insights: community health, pricing range, recommendation

## Built-in Product Directories

Include curated product directories for common categories so the command works offline without API dependencies:

| Category | Coverage |
|----------|----------|
| AI FinOps / Cloud Cost | CloudHealth, Vantage, Kubecost, Infracost, Cast AI |
| AI / LLM Agent | LangChain, CrewAI, AutoGen, OpenAI Assistants, Claude MCP |
| IDE / Dev Tools | Cursor, Copilot, Windsurf |
| Project Management | Linear, Notion, Asana |
| Data / Analytics | Metabase, Grafana, Tableau |
| Generic fallback | GitHub search + Google |

See `references/product-directories.md` for full entries with descriptions, pricing, and features.

### GitHub API Integration

Use `urllib.request` with no API key for public GitHub searches:

```python
def search_github(query, limit=5):
    encoded = urllib.parse.quote(f"{query} in:name,description,readme sort:stars")
    data = github_request(f"/search/repositories?q={encoded}&per_page={limit}")
    for item in data.get("items", []):
        repo_data = github_request(f"/repos/{item['full_name']}")
        entry = ProjectEntry(
            name=repo_data["full_name"],
            url=repo_data["html_url"],
            stars=repo_data["stargazers_count"],
            description=repo_data.get("description", "")[:200],
        )
        # Extract features from README
        entry.key_features = extract_features(entry.name)
        results.append(entry)
```

Rate-limit handling: check `X-RateLimit-Remaining` header, sleep if < 5 remaining using `X-RateLimit-Reset`.

## Group Layout (User-Validated)

This specific group layout was designed and accepted by the user after iterating from 36 flat commands:

```
top-level (9, no nesting):
  setup       — First-time wizard
  quickstart  — Rich Panel guide
  init        — Project init
  run         — Execute task
  chat        — Agent conversation
  status      — Current state
  survey      — Competitive analysis
  dashboard   — Web UI
  demo        — One-click demo

groups (9):
  task        — create, list, show, dispatch, dispatch-smart, epic, schedule, capacity
  team        — create, list, show, start, status, attach, template, sync, hermes
  fleet       — status, show, refresh, history, inspect, monitors, deploy
  mode        — chain, debate, supervise, pipeline (normal/direct/status/confirm)
  project     — create, analyze, list, sprint
  system      — skill, economy, evolution, knowledge, autonomous
  help        — request, approve, list
  origin      — init, replicate, portfolio, overview
  integrate   — hermes, bridge, router, monitor, company
```

The `crew` command is a third-party add-on (`cli.add_command(crew_group)`) and stays top-level for compatibility.

## macOS MallocStackLogging Suppression

A cross-cutting macOS issue — when `MallocStackLogging` is set (even to empty string), every Python subprocess spawned by Apex/Hermes prints a stderr warning on exit. This is not an Apex bug; it's a macOS debug env var leak.

### Symptom

```
python3(16688) MallocStackLogging: can't turn off malloc stack logging because it was not enabled.
```

Hundreds of lines, one per subprocess. Noisy but harmless.

### Triple-Layer Fix

```python
# 1 — Shell init (~/.zshrc / ~/.zprofile)
echo '[[ -z "${MallocStackLogging+x}" ]] || unset MallocStackLogging' >> ~/.zshrc
echo '[[ -z "${MallocStackLoggingNoCompact+x}" ]] || unset MallocStackLoggingNoCompact' >> ~/.zshrc

# 2 — Apex CLI bootstrap (main.py, before click import)
import os
for _v in ("MallocStackLogging", "MallocStackLoggingNoCompact"):
    if _v in os.environ:
        del os.environ[_v]
```

Layer 2 covers all subprocesses spawned by Apex CLI directly. Layer 1 covers all new Terminal windows. Apply both; they're not redundant (Terminal.app inherits env from the OS launchd, not from the shell's interactive unset).

\n## Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| `formatter.write_text()` wraps long lines unpredictably | Quickstart box misaligned in terminal | Use Rich `Panel.fit()` as a separate command, not Click's help formatter |
| Unicode box-drawing in Python string literals | SyntaxError from patch tool | Use plain `===` separators or embed as unicode escapes `\u2554...\u2557` |
| `click.argument("task_id", required=False, default=None)` | TypeError on missing arg | Use `@click.argument("task_id", required=False)` + `Optional[str]` type hint |
| Nested groups in Click (`@mode.group()`) | "No such command" | Each nesting level needs its own `@xxx.group()` + `def xxx(): pass` — you can't chain decorators |
| `@click.pass_context` on `@click.group()` | Breaks if also has `@click.version_option` | Keep `@click.group()` and `@click.version_option` on separate lines, both on root CLI function |
| Emoji stripping based on hardcoded char list | Misses emoji like 🔍 (survey) | Use `unicodedata.category(char) == 'So'` for general emoji detection |
| GitHub API 403 (rate limit) | Survey returns empty results | Implement retry with sleep based on `X-RateLimit-Reset` header |
| MallocStackLogging set to empty string in macOS env | Thousands of `MallocStackLogging: can't turn off` lines in subprocess stderr | Triple-layer fix: (1) `~/.zshrc`: `unset MallocStackLogging`, (2) apex/main.py: `del os.environ[_v]`, (3) current session apply |
| Added a new `@cli.command()` but it doesn't appear in `--help` | Command exists and runs, invisible in help output | `format_apex_help` uses hardcoded `groups` lists — add the command name to the appropriate group tuple (e.g. `("SETUP & START", [..., "new-cmd"])`) AND add an example entry. This is a design flaw in the custom formatter: it does NOT auto-discover commands. Every new top-level command needs 2 edits: the group list + the examples list. |
