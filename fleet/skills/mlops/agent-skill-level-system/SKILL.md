---
name: agent-skill-level-system
description: "Agent Skill Level System — L0-L5 skill registry, evaluation pipeline, SKILL.md generation, task matching, fleet monitor integration, agent profile creation, Superpowers methodology, and squad commands for multi-agent fleets in Apex. Covers fleet-monitor content (consolidated)."
version: 2.1.0
author: Origin Agent
---

# 🎯 Agent Skill Level System

## Overview

A complete skill registry and evaluation system for Apex multi-agent fleets. Each agent has structured skill levels (L0-L5), evidence chains, and automated evaluation pipelines.

Covers: Skill Registry | Agent Profile Creation | Superpowers Methodology | Fleet Monitoring | Security Agent Creation | SQUAD Commands | Profile Auth Troubleshooting

## Core Architecture

```
~/.apex/skill-registry.yaml     — Central registry (90+ skills, 31 agents)
~/.apex/eval-reports/           — Evaluation reports history
~/.hermes/profiles/<name>/     — Per-agent: SOUL.md + config.yaml + SKILL.md
~/.hermes/profiles/skill-evaluator/ — Evaluator Agent profile
~/.hermes/scripts/evidence_collector.py  — Cron evidence scanner
~/.hermes/scripts/full_eval_cycle.py     — 24h full evaluation
~/.hermes/skills/dev-superpowers/*/SKILL.md — Superpowers skills (5)
```

## 1. CREATING A NEW AGENT PROFILE

When the user asks you to create a new agent, follow this exact sequence:

### Step 1: Create SOUL.md
Path: `~/.hermes/profiles/<agent-name>/SOUL.md`

Structure (in order):
1. **Title** — `# Emoji Agent-Name` (emoji + Chinese identity)
2. **Identity** — 你是谁 (1 paragraph)
3. **SUPERPOWERS-BOOTSTRAP** — the `<EXTREMELY-IMPORTANT>` block with 1% rule and methodology chain
4. **Core Responsibilities** — 4-6 bullet points
5. **Professional Domains** — 6-10 technical areas
6. **Personality** — 2-3 character traits
7. **Communication Style** — how they format output
8. **Skill List** — 8 skill names (matching the registry)
9. **Red Flags** — table 6-10 rows (Cognitive Trap → Remedy)
10. **The Iron Laws** — 4 non-negotiable rules

Use the `<!-- SUPERPOWERS-BOOTSTRAP -->` comment marker exactly as shown; the verification tool looks for this string.

### Step 2: Create config.yaml
```yaml
model:
  default: deepseek-v4-pro
  provider: deepseek
agent:
  max_turns: 100
kanban:
  skills_policy: inherit
```

### Step 3: Create wrapper script
```bash
cat > ~/.local/bin/<agent-name> << 'EOF'
#!/bin/sh
export DEEPSEEK_API_KEY="sk-your-key-here"
exec hermes -p <agent-name> "$@"
EOF
chmod 755 ~/.local/bin/<agent-name>
```

**CRITICAL:** The `DEEPSEEK_API_KEY` env var export is REQUIRED. Without it, Hermes profile mode reads from `auth.json` credential pool which may have stale keys or wrong base_url. The wrapper env var takes precedence over the credential pool.

### Step 4: Register skills in Skill Registry
```python
PYTHONPATH=. python3 -c "
from apex.interface.skill_registry import get_registry, LEVELS
r = get_registry()
now = __import__('time').strftime('%Y-%m-%d')
# ... define and register each skill, then assign to agent
r.save()
"

# Then generate SKILL.md
PYTHONPATH=. python3 -c "
from apex.interface.skill_registry import sync_skill_md
print(sync_skill_md('<agent-name>'))
"
```

### Step 5: Register in squad
Add to `DEV_SQUAD` dict in `apex/cli/commands/squad_cmds.py` and update the `click.Choice` list in `apex/cli/main.py`.

### Step 6: Verify
```bash
# Check files
ls ~/.hermes/profiles/<agent-name>/SOUL.md ~/.hermes/profiles/<agent-name>/config.yaml ~/.local/bin/<agent-name>

# Live test
<agent-name> chat -q "回复两个字：就绪"
```

## 2. FLEET & SQUAD MONITORING

### fleet commands (all agents)
```bash
apex fleet status            # Full fleet overview (58 agents)
apex fleet status --live     # Live-updating dashboard
apex fleet show <agent>      # Agent detail: skills, levels, tasks, stats
apex fleet refresh           # Force-refresh all agent states
apex fleet history           # Timeline of fleet snapshots
```

### squad commands (core 9 agents)
```bash
apex squad status            # Dev squad readiness with methodology chain
apex squad start             # Launch all 9 in new Terminal windows
apex squad attach <agent>    # Detailed methodology status
```

### Current Fleet (9 Core Agents)

**Development (5):**
| Agent | Role | Skills | Highest Skill |
|-------|------|--------|--------|
| frontend-dev | Frontend Developer | 16 | L3 |
| backend-dev | Backend Developer | 15 | L2 |
| fullstack-dev | Fullstack Developer | 16 | L2 |
| architect | System Architect | 15 | L3 |
| devops | DevOps Engineer | 16 | L2 |

**Security (3):**
| Agent | Role | Skills | Purpose |
|-------|------|--------|---------|
| vulnerability-scanner | Vulnerability Scanner | 8 (L2) | SAST/SCA/Secret/Docker scan |
| penetration-tester | Penetration Tester | 8 (L2) | Web/API/Logic pentest |
| security-by-design | Security by Design | 8 (L2) | Threat model/Secure arch |

**Management (1):**
| Agent | Role | Skills | Purpose |
|-------|------|--------|---------|
| project-manager | Project Manager | 8 (L2) | Planning/Risk/Tracking |

### Fleet Monitor State Machine
| State | Emoji | Condition |
|-------|-------|-----------|
| WORKING | 🟢 | Active tasks in progress |
| IDLE | ⚪ | No tasks, available |
| WAITING | 🟡 | Has tasks but stalled or long idle |
| STOPPED | 🔴 | No profile, no heartbeat, >24h inactive |

## 3. SUPERPIERS METHODOLOGY INTEGRATION

### User's Preferred Workflow Order
**The user explicitly requires: analysis → plan → implement.** Do NOT skip to implementation even when the user says "go ahead" or "just do it." Always:
1. **First** analyze the problem space deeply — read docs, existing code, surface requirements
2. **Then** present the plan with architecture, trade-offs, and bite-sized tasks
3. **Only after plan approval**, implement

This applies to ALL tasks, not just "big" ones. The user considers this non-negotiable. If you start coding before getting approval, you will be corrected.

### 7-Skill Methodology Chain
```
🧠 brainstorm → 📝 plan → 🔄 TDD → 🔬 verify → 🔍 debug → 👀 review → ✅ finish
```

### The Iron Laws (per agent)
1. No code before design — brainstorming must be invoked
2. No fix without root cause — systematic debugging must be invoked
3. No completion without verification — fresh evidence required
4. No merge without code review — always request reviewer subagent

### 1% Rule
If there is even a 1% chance a skill might apply, invoke it. This is non-negotiable.

### Red Flags
Every dev agent's SOUL.md has an 8-12 row Red Flags table — cognitive traps mapped to remedies. These override rationalization patterns that lead to skipping methodology.

### Phase 3-5: Deep Quality Gates
- **2-Stage Code Review:** spec compliance (Stage 1) gates code quality (Stage 2)
- **Auto-chaining engine:** methodology_engine.py with ChainState, auto-inference
- **Git worktree isolation:** ~/.apex/worktrees/ with provenance-checked cleanup
- **Enhanced parallel dispatch:** DispatchTask dataclass with scope/constraints

### Profile Auth Pitfall
**Problem:** Starting agent via wrapper fails with HTTP 401 despite valid `.env`.

**Root cause:** `hermes -p <name>` reads keys from `auth.json` credential_pool, not `.env`. The pool may have stale `base_url: https://api.deepseek.com/anthropic` (expired proxy).

**Fix (two parallel approaches):**
1. **Wrapper fix:** Export `DEEPSEEK_API_KEY` in wrapper script — env var takes precedence over credential pool
2. **auth.json fix:** Set `base_url` to `https://api.deepseek.com/v1` in both `~/.hermes/auth.json` and `~/.hermes/profiles/<name>/auth.json`

## 4. SKILL REGISTRY

### CLI Commands
| Command | Purpose |
|---------|---------|
| `apex skill list` | List skill catalog or agent skills |
| `apex skill show <agent>` | Show agent skill levels + evidence |
| `apex skill assess <agent> <skill>:<Lx>` | Assess/upgrade skill |
| `apex skill match <task>` | Find best agent for task |
| `apex skill diff <a> <b>` | Compare two agents |
| `apex skill sync <agent>` | Generate SKILL.md for agent |
| `apex skill sync-all` | Generate SKILL.md for all agents |
| `apex skill evaluate` | Run evaluation on recent tasks |
| `apex skill evidence <agent> <skill>` | Add evidence |

### Level System (L0-L5)
| Level | Title | Meaning |
|-------|-------|---------|
| L0 | Novice (新手) | 不了解，需要指导 |
| L1 | Apprentice (学徒) | 能简单完成，需监督 |
| L2 | Practitioner (独立执行) | 能独立完成标准任务 |
| L3 | Proficient (精通) | 能优化和教学 |
| L4 | Expert (专家) | 领域专家，架构决策 |
| L5 | Legend (传奇) | 开创性，创建工具/框架 |

### Skill Categories in Registry
| Category | Count | Example Skills |
|----------|-------|----------------|
| security | 16 | sast-analysis, dependency-scan, threat-modeling, web-pentest |
| frontend | 4 | react-development, responsive-design, typescript |
| backend | 4 | api-design, database-schema, system-design |
| devops | 4 | ci-cd-pipeline, infrastructure-as-code, docker-kubernetes |
| product | 12+ | prd-writing, project-planning, milestone-tracking |
| ai-ml | 4 | machine-learning, deep-learning, experiment-design |
| general | 20+ | peer-review, quality-assurance, systematic-debugging |
| superpowers | 7 | brainstorming, verification-before-completion, finishing-development |
| content/research/growth | 12 | seo-optimization, academic-writing, growth-hacking |

## 5. UPGRADE & EVALUATION

### Upgrade Rules
- L0→L1: 1 task at any difficulty
- L1→L2: 2 tasks at L2+ difficulty (auto-approved)
- L2→L3: 3 tasks at L3+ difficulty (pending Origin approval)
- L3→L4: 2 tasks at L4+ (Origin approval)
- L4→L5: Innovative contribution (Origin approval)

### Evaluation Pipeline
- `evidence-collector` cron: every 30 min, scans completed tasks for evidence
- `full-eval` cron: daily at 2am, full scan + SKILL.md sync
- Evidence types: task, pr, review, session
- Evaluations saved to `~/.apex/eval-reports/`

## 6. PRESENTATION & FORMAT PREFERENCES

### Agent Status Table Display
When showing `apex squad status`, the user requires:
- **Table format** with aligned borders (use `Table(box=box.SQUARE)` from Rich)
- **Emoji + full agent name** visible (not truncated — column width 22 chars for agent, 18 chars for role)
- **Color-coded** agent names per role type
- **State column** showing `● 在线` (green) or `○ 待启动` (dim)
- **Short command names** in the command column (e.g. `vuln-scan chat`, not `vulnerability-scanner chat`)
- **All columns aligned** on the same horizontal lines — no multi-row cells per agent
- **Header row** with bold cyan styling
- **Methodology chain** displayed as a single compact line above the table

**Pitfall:** Rich Table with `max_width` constraints or `show_lines=True` causes columns to disappear when terminal is narrow. Use fixed `width` columns instead and test with the longest agent name (vulnerability-scanner = 22 chars).

### Workflow Order (analysis-first)
The user expects **analysis → plan → implementation**, never skipping to code even for "simple" tasks. Present analysis first, get approval, then build. This is not negotiable.

## 7. KEY FILES

### Agent Badge Design (Visual Identity)

See `references/agent-badge-design-system.md` for:
- 11-agent Unicode symbol assignments (≪/≫, {⚙}, ⟡, ⊞, etc.)
- Role-group color scheme (DEV=blue, ARCH=purple, OPS=cyan, SEC=red, etc.)
- Rich table layout with badges, short names, and color-coded agents
- SVG hexagon badge template for design docs
- Anti-patterns

Apply this system whenever creating a new agent profile — assign a unique Unicode symbol and role color.

| File | Purpose |
|------|---------|
| apex/interface/skill_registry.py | Core module: SkillRegistry, SKILL.md gen |
| apex/interface/agent_monitor.py | FleetMonitor: agent state detection |
| apex/interface/superpowers_bridge.py | Bootstrap + registry sync + verify |
| apex/interface/methodology_engine.py | 2-stage review + auto-chaining + worktree |
| apex/cli/commands/skill_mgmt.py | All `apex skill *` commands |
| apex/cli/commands/fleet_cmds.py | Fleet dashboard renderers |
| apex/cli/commands/squad_cmds.py | Squad launch/status/attach commands |
| apex/skill_evaluator.py | Evaluation pipeline engine |
| ~/.hermes/skills/dev-superpowers/*/SKILL.md | 5 Superpowers skills |
