# System UAT: Deep-Dive Audit Techniques

## When to Use

When the user asks "is this system complete?" / "how much is done?" / "can it pass UAT?" — especially for CLI tools, Python packages, or multi-agent frameworks where you need to distinguish between **scaffold code** and **real execution**.

## Technique 1: Real-vs-Scaffold Detection

A module might import cleanly, have a class with a `.run()` method, and even produce output — but never *actually execute* its intended task. Use source inspection:

```python
import importlib, inspect

mod = importlib.import_module("pkg.orchestration.some_mode")
for name in dir(mod):
    cls = getattr(mod, name)
    if isinstance(cls, type) and hasattr(cls, "run") and name != "Agent":
        src = inspect.getsource(cls.run)
        lines = src.split("\n")
        agent_calls = sum(1 for l in lines if ".run(" in l)
        status = "🟢 EXECUTES" if agent_calls > 0 else ("🟡 CREATES" if "Agent(" in src else "🔴 SCAFFOLD")
        print(f"  {name}.run(): {status} ({len(lines)} lines)")
```

**Key indicators:**
- `agent.run(` call count = 0 → **scaffold**. The method defines workflow structure but never invokes an agent.
- Only `print/console.print` calls → **partial**. May render UI but no computation.
- `raise NotImplementedError` → **stub**. Not even scaffold.
- `agent.run(` calls >= 1 AND `return` with computed value → **real**.

## Technique 2: CLI-README Cross-Reference

Documented features that don't exist are P1 defects. Extract both sides:

```bash
# Extract README's command table entries
grep -oP '`apex\s+\S+[^`]*`' README.md | sed 's/`//g' | sort -u > /tmp/readme.txt

# Extract CLI help output
apex --help 2>/dev/null > /tmp/cli_help.txt
grep -E '^\s+(run|status|team|template|crew|economy|knowledge|evolution|company|autonomous|ops|chain|debate|router|supervisor|monitor|dashboard)' /tmp/cli_help.txt | sort -u > /tmp/cli.txt

# Find mismatches
echo "=== README only (doc bug) ==="
comm -23 /tmp/readme.txt /tmp/cli.txt
echo "=== CLI only (undocumented) ==="
comm -13 /tmp/readme.txt /tmp/cli.txt
```

## Technique 3: Multi-Surface Inventory

Run a complete inventory before fixing anything:

```python
def audit(project_path):
    results = {}
    
    # 1. Module imports
    results["imports"] = {}
    for m in ALL_MODULES:
        try:
            __import__(m)
            results["imports"][m] = "✅"
        except Exception as e:
            results["imports"][m] = f"❌ {e}"
    
    # 2. All CLI commands
    import subprocess
    out = subprocess.run(["python3", "-m", "apex"] + ["--help"],
        capture_output=True, text=True)
    results["cli_commands"] = len([l for l in out.stdout.split("\n") if l.strip() and not l.startswith("Usage")])
    
    # 3. Test suite
    out = subprocess.run(["python3", "-m", "pytest", "tests/", "-q", "--tb=short"],
        capture_output=True, text=True, cwd=project_path)
    results["tests"] = out.stdout.strip().split("\n")[-1]
    
    # 4. API endpoints (if Flask/FastAPI)
    from pkg.web import create_app
    app = create_app()
    results["api_endpoints"] = list(app.url_map.iter_rules())
    
    # 5. Code metrics
    metric_out = subprocess.run(
        ["bash", "-c", "find apex -name '*.py' -not -path '*/__pycache__*' -exec cat {} + | wc -l"],
        capture_output=True, text=True, cwd=project_path)
    results["sloc"] = metric_out.stdout.strip()
    
    return results
```

## Technique 4: Execution Confidence Levels

When assessing whether a feature "works" in a multi-agent system, use 4 levels:

| Level | Label | Test | Example |
|-------|-------|------|---------|
| 🟢 **Confirmed** | End-to-end verified | Run command, validate output | `apex status` → shows agent list |
| 🟡 **Structural** | Imports, class/method exists, but no run test | Import + inspect | `apex chain run "goal"` doesn't call Agent.run() |
| 🔴 **Documented** | README/help says it exists, but code doesn't | Help prints, execution fails | `apex crew design` — help shows it, but click group not registered |
| ⚪ **Speculative** | Competitive comparison table claims it | No code at all | Cross-language agents in architecture diagram |

## Technique 5: SQLite Thread Safety Check

A common P0 defect in Python multi-threaded systems — verify all `sqlite3.connect()` calls include `check_same_thread=False`:

```bash
python3 -c "
from apex.core.profile import APEX_HOME
import sqlite3
for name in ['evolution', 'knowledge', 'memory', 'skills', 'kanban', 'economy']:
    conn = sqlite3.connect(str(APEX_HOME / f'{name}.db'), check_same_thread=False)
    assert conn.execute('SELECT 1').fetchone()[0] == 1
    conn.close()
    print(f'  ✅ {name}')
"
```

This catches the "SQLite objects created in a thread can only be used in that same thread" error that crashes the service when background threads touch DB connections created in the main thread.

## Technique 6: Rapid Fix Cycle (Post-Audit)

When P0/P1 defects are found and the user says "fix it now":

1. **Complete the audit first** — know everything broken before touching code, even if some defects are obvious.
2. **Parallel dispatch** — split fixes across 3 delegate_task subagents:
   - Subagent A: P0 runtime/architecture (integration defects, thread safety, missing imports)
   - Subagent B: P1 feature CLI (missing commands, data seeding, dashboard panels)
   - You (main agent): P1/P2 middle-layer (templates, CSS, README)
3. **P3 inline** — fix docs/formatting yourself while subagents work.
4. **One-pass verify** — re-run the full inventory after all return.
5. **One commit** — `git add -A && git commit -m "🛠️ P0/P1 UAT fixes — [...]"`

This pattern completed 6 P0/P1/P3 fixes across 12 files in one ~8-minute cycle.
The key discipline: do NOT start fixing until the full inventory is done.
