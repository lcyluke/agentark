# Apex Superpowers — Integration Plan

## Superpowers Analysis Summary

### Project Stats
- 216K stars, 19.3K forks
- 14 skills + hooks + multi-harness plugins
- 441 commits, 80 branches
- Core philosophy: "methodology that works" — not tools, but behavior-shaping

### Superpowers' 7 Core Mechanisms

| # | Mechanism | What It Does | Impact |
|---|-----------|-------------|--------|
| 1 | **SessionStart Bootstrap** | Hook injects `using-superpowers` into system prompt at session start | Makes skill-awareness reflexive |
| 2 | **"1% Rule"** | "If even 1% chance a skill applies, invoke it" — overrides rationalization | Eliminates skill-skipping |
| 3 | **Hard Gate: Brainstorming** | No implementation code until design is approved | Prevents premature coding |
| 4 | **Subagent-Driven Dev** | Fresh subagent per task + 2-stage review (spec→quality) | Quality gates at each step |
| 5 | **Red Flags Tables** | Every skill has rationalization-excuse pairs | Anticipates agent rationalization |
| 6 | **Verification Iron Law** | "No completion claims without fresh verification evidence" | Eliminates hallucinated success |
| 7 | **Methodology Chain** | Brainstorm → Write Plan → Subagent Execute → Review → Finish Branch | Complete workflow pipeline |

### Apex Current State vs Superpowers

| Capability | Apex Now | Superpowers | Integration Strategy |
|-----------|----------|-------------|---------------------|
| Skills | SOUL.md + SKILL.md per agent | SKILL.md per harness | Compatible — use same format |
| Subagent | delegate_task() | Subagent-driven-dev | Enhanced with 2-stage review |
| Plans | writing-plans skill exists | Full spec→plan→task chain | Upgrade to Superpowers format |
| TDD | Not enforced | Iron law (test-first or delete) | Add to dev agent SOUL.md |
| Debugging | No formal protocol | 4-phase systematic debugging | New skill for Apex |
| Verification | Not enforced | Iron law with gate function | New skill + SOUL.md rule |
| Bootstrap | No session-start hook | Hook injects skill awareness | Add to Apex profile config |
| Parallel agents | delegate_task batch | dispatching-parallel-agents | Upgrade existing |
| Code review | requesting-code-review exists | Full 2-stage reviewer subagent | Extend with spec+quality split |
| Red flags | None | Every skill has one | Add to all skills |
| Finishing work | Manual | Structured merge/PR/discard | New skill for dev agents |

### Integration Plan: 5 Phases

```
Phase 1 — Methodology Chain Skills (HIGHEST impact)
  ├─ apex:brainstorming        — Hard gate: no code before design
  ├─ apex:writing-plans        — Bite-sized tasks with exact code/paths
  ├─ apex:verification-before-completion — Iron law: evidence before claims
  ├─ apex:finishing-development — Structured merge/PR/discard options
  └─ Add to dev agents SOUL.md — Methodology chain as "way of working"

Phase 2 — Agent Behavior Shaping (HIGH impact)
  ├─ Red Flags tables in all dev skills
  ├─ "1% rule" for skill invocation
  ├─ Rationalization prevention in SOUL.md
  └─ Upgrade calling conventions

Phase 3 — Quality Gates (MEDIUM impact)
  ├─ Systematic debugging 4-phase protocol
  ├─ TDD iron law enforcement
  ├─ 2-stage code review (spec compliance → code quality)
  └─ Receiving code review protocol

Phase 4 — Auto-Trigger Bootstrap (MEDIUM impact)
  ├─ Session-start context injection in Hermes profiles
  ├─ Skill auto-detection at conversation start
  └─ Methodology chaining via profile config

Phase 5 — Parallel & Workspace (LOWER impact)
  ├─ Enhanced parallel agent dispatch
  ├─ Git worktree isolation for dev agents
  └─ Harness plugin definitions
```

## Priority: Phase 1 + Phase 2

Immediate value: Upgrade the 4 development agents with the Superpowers methodology.
