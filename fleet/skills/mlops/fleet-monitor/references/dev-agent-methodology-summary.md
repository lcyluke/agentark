# Dev Agent Superpowers Methodology — Quick Reference

## The 7-Skill Chain
```
🧠 brainstorm → 📝 plan → 🔄 TDD → 🔬 verify → 🔍 debug → 👀 review → ✅ finish
```

## Iron Laws (all 5 agents)
1. **No code before design** — brainstorming must be invoked for any feature
2. **No fix without root cause** — systematic debugging for any bug
3. **No completion claim without verification** — fresh evidence required
4. **No merge without code review** — 2-stage review mandatory

## The "1% Rule"
If there is even a 1% chance a skill applies, invoke it. Not negotiable. Not optional. Cannot rationalize your way out.

## Dev Agent Checklist (per agent)
| Agent | Skills | Highest | Wrapper | Config |
|-------|--------|---------|---------|--------|
| frontend-dev | 16 | L3 | ✅ | ✅ |
| backend-dev | 15 | L2 | ✅ | ✅ |
| fullstack-dev | 16 | L2 | ✅ | ✅ |
| architect | 15 | L3 | ✅ | ✅ |
| devops | 16 | L2 | ✅ | ✅ |

## Bootstrap Injection
SUPERPOWERS-BOOTSTRAP injected after the identity header in each SOUL.md. Contains:
- 1% rule with skill list
- The dev chain
- Skill descriptions
- "If in doubt, start with brainstorming"

## Profile Auth Fix
See fleet-monitor SKILL.md for full pitfall details. TL;DR: wrapper must export DEEPSEEK_API_KEY.

## Launch
```bash
apex squad status    # Dashboard
apex squad start     # All 5 in new windows
<name> chat          # Single agent
```
