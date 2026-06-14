---
name: dogfood
description: |
  Exploratory QA of web apps, CLI tools, and API services: find bugs,
  collect evidence, and produce structured UAT reports.
version: 1.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qa, testing, browser, web, cli, api, uat, dogfood]
    related_skills: [systematic-debugging]
---

# Dogfood: Systematic QA Testing

## Overview

This skill guides you through systematic QA testing of any software system — web
applications, CLI tools, REST APIs, or Python modules — using the available
toolset (browser for web, terminal for CLI/API, Python evaluation for imports).
You navigate the target, interact with it, capture evidence of issues, and
produce a structured bug/UAT report.

## Mode Selection

The dogfood skill supports **three modes**. Pick the one that matches the target:

| Mode | Target | Tools | When to Use |
|------|--------|-------|-------------|
| **🌐 Web** | Browser-based web apps | browser_navigate/click/type/console/vision | User gives a URL, or the system has a web UI |
| **🖥️ CLI** | Terminal commands, CLIs | terminal, execute_code | User says "test apex run" / "verify the CLI" / UAT of a CLI tool |
| **⚙️ System** | Python modules, REST APIs, test suites, code quality | terminal, execute_code, read_file | User asks "is this complete?" / "can it pass UAT?" — multi-surface analysis |

## Prerequisites

- **Web mode:** browser toolset (navigate, snapshot, click, type, console, vision)
- **CLI mode:** terminal tool, the target CLI installed and accessible
- **System mode:** access to source code, ability to run tests and module imports

## Inputs

The user provides:
1. **Target** — URL (web), command name (CLI), or repo/source path (system)
2. **Scope** — what areas/features to focus on
3. **Output directory** (optional) — where to save the report (default: `./dogfood-output`)

---

## Mode 1: 🌐 Web — Exploratory Browser QA

Follow the standard 5-phase workflow in `references/web-qa-checklist.md` for
browser-based web applications.

---

## Mode 2: 🖥️ CLI — Command-Line Tool UAT

### Phase 1: Plan

Identify the CLI's surface area:
- **Help/version**: `tool --help`, `tool --version`
- **All subcommands**: `tool --help` lists them; test each `tool subcommand --help`
- **Core commands**: run each with valid arguments, verify non-zero exit on error
- **Edge cases**: missing args, invalid flags, piping, file-not-found

### Phase 2: Run & Verify

For each CLI command:

1. **Check help works:**
   ```bash
   tool subcommand --help
   ```
   Expected: 0 exit, sensible output

2. **Run with valid input:**
   ```bash
   tool subcommand "valid input"
   ```
   Expected: succeeds, produces output, exits 0

3. **Run with bad input:**
   ```bash
   tool subcommand --nonexistent-flag
   ```
   Expected: exits non-zero, helpful error message

4. **Check Rich/click formatting** renders without traceback.

### Phase 3: Cross-reference Docs

1. List all commands the README advertises.
2. Run each documented command. File a bug for every missing or broken one.
   Common pattern: README adds a flag/feature in a refactor pass but forgets to
   register it in the Click group.

### Phase 4: Gather Evidence

For each issue found, collect:
- Exact command and its output (stdout + stderr)
- Exit code
- The README claim vs actual behavior
- No screenshots needed — paste terminal output into the report

### Phase 5: Report

Use `templates/dogfood-report-template.md` but adapt for CLI:
- Replace "URL" with "Command"
- Use terminal output excerpts instead of screenshots
- Add a "Documentation Consistency" section mapping README claims → actual behavior

---

## Mode 3: ⚙️ System — Full-Stack UAT

This is the most comprehensive mode — test the entire system across multiple
surfaces (imports, CLI, API, tests, code metrics) to answer "is it complete?"

### Phase 1: Inventory

1. **Module import test** — try importing every module in the codebase:
   ```python
   modules = ["pkg.a", "pkg.b", "pkg.c"]
   for m in modules:
       try:
           __import__(m)
       except Exception as e:
           print(f"FAIL: {m} -> {e}")
   ```

2. **CLI surface** — register all documented commands from `--help` output.

3. **API surface** — document all REST endpoints (if any) via route listing:
   ```python
   from pkg.web import create_app
   app = create_app()
   for rule in app.url_map.iter_rules():
       print(f"{rule.rule} -> {rule.endpoint}")
   ```

4. **Test suite** — run all tests:
   ```bash
   python -m pytest tests/ -q --tb=short
   ```

5. **Code metrics** — count classes/functions:
   ```bash
   grep -c 'class\|def ' pkg/**/*.py | awk -F: '{s+=$2} END {print s}'
   ```

### Phase 2: Run Critical Flows

Run the 3-5 most important user-facing flows end-to-end:

1. **CLI execution**: run the primary command (`tool run "hello"`)
2. **API health**: curl each endpoint, verify JSON with correct keys
3. **Background service**: start the server, hit it, stop it
4. **Edge cases**: port conflict (start twice), empty DB (first run)

### Phase 3: Classify Issues

Use P0-P3 severity instead of web's Critical/High/Medium/Low:

| Level | Label | Meaning |
|-------|-------|---------|
| 🔴 **P0** | Blocking | Service won't start, core flow crashes, data loss |
| 🟠 **P1** | Severe | Feature broken, docs vs code mismatch, important workflow blocked |
| 🟡 **P2** | Medium | Minor feature gap, untested code, cosmetic bug |
| 🔵 **P3** | Low | Polish, docs minor errors, edge cases |

Add category annotations:
- **`[Docs]`** — README says X, code does Y
- **`[Stability]`** — crashes, hangs, port/thread issues
- **`[TestGap]`** — uncovered code path
- **`[UX]`** — confusing output, missing error message

### Phase 4: Synthesize Verdict

Give an overall UAT verdict:

```
| Surface       | Status | Notes          |
|---------------|--------|----------------|
| Imports       | ✅     | 22/22 pass     |
| CLI Commands  | ✅     | 17/17 work     |
| API           | ⚠️     | 2 endpoints 404|
| Tests         | ✅     | 42/42 pass     |
|              |        |                |
| VERDICT      | ❌ Can't pass | P0 + 3 P1 |
```

**Verdict options:**
- ✅ **Production-ready** — no P0/P1, <=2 P2
- ⚠️ **Conditional pass** — P1 can be fixed in < 3h, state the blockers
- ❌ **Can't pass** — P0 exists or P1 > 3
- 🚧 **Preview only** — core works but major features missing or untested

### Phase 5: Report

Generate a UAT report using the template at `templates/uat-report-template.md`.

For deep-dive inspection (real-vs-scaffold detection, execution confidence levels, SQLite thread safety), see `references/system-uat-audit-deep-dive.md`.

Save to `{output_dir}/uat-report.md`.

**Report formatting rules:**
- Every issue gets one line: severity badge | category code | short title | fix pattern suggestion
- No paragraphs per issue — use summary tables
- End with a **verdict block**: `✅ Production-ready` / `⚠️ Conditional` / `❌ Can't pass` / `🚧 Preview only`
- Include a **before/after comparison table** showing how the fix round changed the score

### Post-UAT: Rapid Fix Cycle

When findings are P0/P1 and the user says "fix it", follow this pattern:

1. **Inventory first** — run ALL surfaces (imports, CLI, API, tests) before fixing. Know everything broken before touching code.
2. **Parallel fix dispatch** — fix across 3+ subagents via `delegate_task`:
   - Subagent A: P0 runtime/architecture defects (e.g. 3-strike healing integration, thread safety)
   - Subagent B: P1 CLI/feature defects (e.g. missing commands, seed data, dashboard panels)
   - You (main agent): P1/P2 middle-layer fixes (HTML/CSS/JS changes, README updates)
3. **P3 fixes inline** — fix documentation inconsistencies yourself while subagents work.
4. **Verify after all return** — re-run the full inventory (imports + CLI + API + tests) in one go.
5. **Commit as one batch** — `git add -A && git commit -m "🛠️ P0/P1 UAT fixes — [summary of what]"`

This pattern completed 6 P0/P1/P3 fixes across 12 files in one 8-minute cycle. The key discipline is: do NOT start fixing until the full inventory is done.

### README-CLI Consistency Cross-Reference

A critical UAT step often missed: **cross-reference what README claims against what the CLI actually provides.**

1. Extract all commands from README's command table:
   ```bash
   grep -oP '`apex[^`]+`' README.md | sort -u > /tmp/readme_commands.txt
   ```
2. Extract all commands from `--help`:
   ```bash
   tool --help 2>/dev/null | grep -oP '^- [a-z]+' | sort -u > /tmp/cli_commands.txt
   ```
3. Compare:
   ```bash
   comm -23 /tmp/readme_commands.txt /tmp/cli_commands.txt   # README-only → documentation bug
   comm -13 /tmp/readme_commands.txt /tmp/cli_commands.txt   # CLI-only → undocumented feature
   ```
4. For each mismatch, file as P1 defect with `[Docs]` prefix.
5. Fix by updating README table (add missing commands) or CLI (register missing Click commands).

---

## Issue Taxonomy

See `references/issue-taxonomy.md` for severity levels, category definitions,
and examples for all three modes (web, CLI, system).
