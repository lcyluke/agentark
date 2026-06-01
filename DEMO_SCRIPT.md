# 🚀 Apex Launch Demo Script

> Total demo time: 3 minutes
> Target: Hacker News + Reddit r/Python + Product Hunt

---

## [00:00-00:30] Hook — Show the problem

**Visual:** Split screen. Left = complex code to set up CrewAI + LangGraph.
Right = Apex.

```bash
# Before (CrewAI + LangGraph + LangSmith = 50+ lines)
# After (Apex = 1 line)
apex crew create "Build a landing page"
```

**Script:**
> "Multi-agent frameworks are powerful, but setting them up is a nightmare.
> CrewAI for roles, LangGraph for state, LangSmith for monitoring, CAMEL for learning...
> You need 3-5 frameworks just to get started.
> 
> We built Apex. One framework, 7 innovations, one command."

## [00:30-01:00] Demo 1 — Swarm Mode

```bash
apex run "Build a React dashboard with login" --swarm
```

**Show:** Parallel workers → verifier → synthesizer output.

**Narrate:**
> "Apex automatically breaks your task into parallel sub-tasks,
> runs multiple agents simultaneously, verifies the quality,
> and synthesizes the final result. All in one command."

## [01:00-01:30] Demo 2 — Crew Mode

```bash
apex crew create "Design a social media app" --members pm,frontend,backend
```

**Show:** PM writes PRD → Frontend designs UI → Backend designs API.
Then round-table discussion → final synthesis.

**Narrate:**
> "Want real collaboration? Crew mode lets agents with different roles
> work together, review each other's work, and produce a unified result.
> It's like having a whole product team in your terminal."

## [01:30-02:00] Demo 3 — One-Click Company

```bash
apex company create my-saas --industry saas
apex company start my-saas "Build MVP"
```

**Show:** 5 agents created, Kanban populated, SOP ready.

**Narrate:**
> "One command = a whole AI company. 5 specialized agents,
> complete Kanban board, production SOP, ready to execute.
> This is what 'one person, infinite capacity' means."

## [02:00-02:30] Demo 4 — Token Economy

```bash
apex economy status
apex economy classify "Design system architecture"
```

**Show:** Routing table, budget usage, classifier output (→ Claude).

**Narrate:**
> "Most frameworks waste money using expensive models for simple tasks.
> Apex's Token Economy intelligently routes each task to the right model.
> Simple edits → free Ollama. Code review → cheap DeepSeek. 
> Architecture → Claude. You save 95% without losing capability."

## [02:30-03:00] Close

```bash
# Show the full CLI
apex --help

# The money shot
pip install apex
apex company create my-startup
apex company start my-startup "Build everything"
```

**Script:**
> "Apex is open source, MIT licensed, and ready to use today.
> One person, infinite capacity.
> From today, YOU are a company."
