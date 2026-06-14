# Multi-Project Directory Hygiene

A recurring source of user confusion: when multiple directories exist for the same project.

## The pattern

- `~/workspace/badminton-coach-ai/` — Hermes scratch workspace. Files appear and disappear across sessions. **Not where the canonical project lives.**
- `~/Desktop/2026AIAPP/workspace/badminton-coach-ai/` — **Canonical project location.** User's real project, git repo, deployable code, full mini-program with 9 pages. This is the source of truth.
- `~/Desktop/2026AIAPP/shenzhen-badminton/` — Separate project: "深圳羽球地图" (venue database + content). Not the same thing.

## How this happens

Hermes uses scratch workspaces (`~/workspace/`) for iterative development. These get recycled. Meanwhile, the user's real projects live under `~/Desktop/2026AIAPP/`. The user may see me working in `~/workspace/` and assume that's *their* project — leading to "where did my files go?" confusion.

## Guardrail

**Always tell the user which directory has their original, deployable project.** When starting work on an existing project:

1. Check BOTH `~/Desktop/2026AIAPP/` and `~/workspace/` for the project
2. If the canonical copy is in Desktop and I'm working in workspace, say so explicitly
3. When the user asks "is my project still intact?", answer from the canonical directory, not the scratch directory
4. Never delete or overwrite files under `~/Desktop/2026AIAPP/` unless the user explicitly asks for it
