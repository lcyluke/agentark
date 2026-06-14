---
name: brainstorming
description: "MUST use before any creative work - creating features, building components, adding functionality, or modifying behavior. Enforces design-before-code discipline."
version: 1.0.0
author: Origin Agent
---

# Brainstorming / 头脑风暴

## Overview

Help turn ideas into fully formed designs through collaborative dialogue. Key principle: design before code.

This skill enforces a structured, dialogue-driven approach to creative problem-solving. Before any line of code is written, the agent and user collaborate to explore context, define requirements, evaluate approaches, and produce a concrete design specification. The goal is to eliminate wasted implementation effort, reduce rework, and ensure every feature built has a clear rationale and agreed-upon blueprint.

**核心理念：先设计，后编码。** 通过协作对话将模糊想法转化为完整的设计方案，禁止在未经批准设计的情况下编写任何代码。

---

## The Hard Gate / 硬性闸门

> **Do NOT write any code until design is approved by user.**

This is a non-negotiable rule. The brainstorming process must reach a conclusion — documented, reviewed, and explicitly approved — before the agent proceeds to implementation. If the user requests code during brainstorming, politely decline and redirect back to the design phase.

**任何代码都必须等待用户批准设计方案后才能编写。** 如果用户在头脑风暴阶段要求写代码，礼貌地拒绝并引导回到设计流程。

---

## Checklist / 检查清单

Follow these steps in order. Do not skip steps or proceed without explicit user consent at each gate.

| Step | Action | 中文说明 |
|------|--------|---------|
| 1 | **Explore context** — Understand the problem space, user needs, constraints, existing architecture, and success criteria. Ask open-ended questions to surface hidden assumptions. | 探索上下文：理解问题空间、用户需求、约束条件、现有架构和成功标准。提出开放性问题以发现隐藏假设。 |
| 2 | **Ask clarifying questions** — Probe ambiguities, edge cases, non-functional requirements (performance, scalability, security), and integration points. Ensure shared understanding. | 提出澄清问题：探究模糊之处、边界情况、非功能性需求（性能、可扩展性、安全性）以及集成点。确保双方理解一致。 |
| 3 | **Propose 2-3 approaches** — Present distinct design approaches with trade-offs. For each: outline the core idea, key decisions, pros/cons, and rough effort estimate. Avoid anchoring on a single solution. | 提出 2-3 种方案：展示不同的设计方案及其权衡。每种方案应包含核心理念、关键决策、优缺点和粗略工作量估算。避免锚定单一方案。 |
| 4 | **Present design** — Select the best approach (or synthesize a hybrid) and produce a detailed design: components, data flow, interfaces, error handling, testing strategy, rollout plan. | 呈现设计：选择最佳方案（或综合方案）并生成详细设计：组件、数据流、接口、错误处理、测试策略、发布计划。 |
| 5 | **User approval** — Present the design for explicit sign-off. Do not proceed until the user says "approved" or equivalent. | 用户批准：提交设计以获得明确批准。在用户明确表示"批准"之前不得继续。 |
| 6 | **Write design to `docs/superpowers/specs/`** — Persist the approved design as a markdown file in the project's specs directory for traceability and future reference. | 将设计写入 `docs/superpowers/specs/`：将批准的设计以 markdown 文件形式保存在项目的 specs 目录中，以便追溯和未来参考。 |
| 7 | **Self-review** — Review your own spec for consistency, completeness, feasibility, and alignment with the approved approach. Fix issues before presenting to user. | 自审：检查规格文档的一致性、完整性、可行性以及与批准方案的符合性。在提交给用户前修复问题。 |
| 8 | **User reviews spec** — Share the written spec with the user for a final review pass. Incorporate feedback. | 用户审查规格：将书面规格文档提交给用户进行最终审查。纳入反馈意见。 |
| 9 | **Invoke `writing-plans`** — Call the `writing-plans` skill (or equivalent planning mechanism) to break the approved design into actionable implementation tickets or subtasks. | 调用 writing-plans：调用写作计划技能（或等效的规划机制）将批准的设计分解为可执行的实现任务或子任务。 |

---

## Red Flags / 危险信号

A table of rationalizations vs. reality — common excuses that lead to skipping design discipline, and the hard truths that counter them.

| # | Rationalization / 合理化借口 | Reality / 现实真相 |
|---|-----------------------------|-------------------|
| 1 | "This change is too small to need a design." | Small changes compound. Without a design, you don't know how small it actually is until halfway through implementation. |
| 2 | "I already know what to build — writing it down wastes time." | Writing exposes gaps in understanding. If you can't describe it simply, you don't understand it well enough. |
| 3 | "The user explicitly said 'just code it'." | The user wants the *right thing built*. Your job as agent is to ensure that happens. Politely enforce the hard gate. |
| 4 | "We can design while coding." | Multitasking design and implementation guarantees neither is done well. Half-baked designs produce half-baked code. |
| 5 | "The deadline is too tight for a design phase." | Designs prevent rework. Skipping design to save time is like skipping the map to save time on a road trip. |
| 6 | "It's just a prototype / POC / experiment." | Prototypes that survive become production. A good design makes the prototype useful as a foundation. |
| 7 | "We'll refactor later." | "Later" never comes. Refactoring without a design target is aimless. Design now, refactor with purpose later. |
| 8 | "This is exactly like something I've built before." | Similar != identical. Surface differences (context, scale, integration) matter. Treat every feature with fresh eyes. |
| 9 | "The design is obvious — everyone agrees on it." | "Obvious" designs are the most dangerous because they are least examined. Make it explicit and verify. |
| 10 | "We can't over-engineer something this simple." | Design is not over-engineering. A 15-minute lightweight design is proportionate; zero design is negligence. |
| 11 | "The spec is too long, nobody will read it." | A good spec is as long as it needs to be — no longer. If it's too long, structure it with summaries and TL;DR sections. |
| 12 | "The user will change their mind anyway, so why bother?" | If the user changes their mind, the spec becomes the diff baseline. Without it, you cannot track what changed or why. |

---

## Anti-Pattern: "Too Simple to Need a Design" / 反模式："太简单不需要设计"

This is the single most common failure mode of the brainstorming process. It manifests as:

> "Come on, this is trivial. Just a CRUD endpoint. Everyone knows how it works. Let's skip the ceremony and get to code."

**Why this is dangerous:**

1. **"Simple" is subjective.** What seems simple to you may have subtle edge cases, security implications, or integration nuances that only surface during design exploration.
2. **Design scales down.** A lightweight design for a "simple" feature takes 5–10 minutes of structured thinking. That's negligible compared to the 30–60 minutes of potential rework from a missed requirement.
3. **Simple features become complex features.** Requirements grow. A design provides a documented baseline for scope management when the feature inevitably grows.
4. **Team alignment requires documentation.** Even for solo projects, writing clarifies thinking. For teams (including future you), the spec is the single source of truth.
5. **Habit matters.** The discipline of always designing first — regardless of perceived simplicity — builds a muscle that pays dividends when complexity inevitably arrives.

**The fix:** Always run the full checklist. For trivially simple features, steps 1–4 can be completed in a single terse conversation turn (e.g., "I understand the context, here's my proposed approach, do you approve?"). The gate is not about effort — it's about *intentionality*.

> **反模式本质：** 以"简单"为借口跳过设计流程。解决方案：即使是最简单的功能，也要至少完成一次设计确认对话（哪怕只需要 30 秒）。设计的价值不在于篇幅，而在于有意识地做出决策。

---

## Team Context / 团队背景

This skill is designed for the **Apex Chinese team** (顶峰中国团队). All critical concepts include Chinese labels and explanations to ensure accessibility for Chinese-speaking team members. The bilingual structure supports collaboration across language preferences while maintaining a single canonical skill definition.

**适用团队：** 顶峰中国团队。关键概念均附有中文标注和说明，确保中文团队成员无障碍理解。双语结构支持跨语言协作，同时保持单一权威的技能定义。

---

## Conclusion / 总结

Brainstorming is not about generating infinite ideas — it's about converging on a shared, actionable design through structured dialogue. By enforcing the design-before-code gate, this skill protects implementation velocity, code quality, and team alignment.

**Design first. Code second. Always.**
