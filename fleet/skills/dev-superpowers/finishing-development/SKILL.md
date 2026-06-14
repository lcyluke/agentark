---
name: finishing-development
description: "Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion with structured options for merge, PR, or cleanup."
version: 1.0.0
author: Origin Agent
---

# finishing-development

## Overview

Guide completion of development work by presenting clear options and handling chosen workflow. This skill is triggered when implementation is finished, tests pass, and the developer must decide how to land their changes back into the mainline.

## The Process

### Step 1: Verify Tests

Run the project's test suite and report any failures before proceeding.

- **Command:** `pytest` or `npm test` or `cargo test` depending on project language.
- **Action:**
  - If **all pass**, proceed to Step 2.
  - If **any fail**, present the failures to the user and **stop**. Do not continue until failures are resolved or explicitly overridden.

### Step 2: Detect Environment

Check the git worktree state to understand what has changed and whether there are any blockers.

- **Commands:**
  - `git status --short` — show working tree changes.
  - `git stash list` — list any stashed changes.
  - `git log --oneline origin/main..HEAD` (or base branch equivalent) — show commits ahead of main.
- **Report:** Summarize number of changed files, staged vs unstaged, stashes, and commit history since divergence.

### Step 3: Determine Base Branch

Identify the correct target branch for integration.

- **Logic:**
  1. Check `git rev-parse --abbrev-ref HEAD` for the current branch name.
  2. If the branch follows a convention like `main`, `master`, `develop`, or `production`, treat that as the base.
  3. Otherwise, examine `git config --get-regexp branch.<current-branch>.merge` or fall back to `origin/main`, `origin/master`, or `origin/develop` (in priority order).
- **Output:** Declare the determined base branch clearly.

### Step 4: Present Options

Present exactly four options to the user, numbered 1–4, with a brief description of each:

| # | Option | Description |
|---|--------|-------------|
| 1 | **Merge locally** | Merge feature branch into base branch locally, then push the result. Best for simple, fast-forward or clean merges. |
| 2 | **Push and open a PR** | Push the current branch to remote and open a pull request. Best for collaborative review or CI gates. |
| 3 | **Keep branch** | Keep the branch as-is. Do nothing further. Best when work is paused or deferred. |
| 4 | **Discard** | Delete local (and optionally remote) branch, resetting to base branch. Best for throwaway experiments or abandoned work. |

### Step 5: Execute Choice

Execute the user's selected option using the exact git commands below.

**Option 1 — Merge locally:**
```bash
# Ensure base branch is up to date
git checkout <base-branch>
git pull origin <base-branch>

# Merge the feature branch
git merge <feature-branch>

# Push the result
git push origin <base-branch>

# (Optional) Delete the feature branch locally
git branch -d <feature-branch>
```

**Option 2 — Push and open a PR:**
```bash
# Push current branch to origin
git push origin HEAD

# Open a pull request (choose one):
gh pr create --title "<title>" --body "<body>"
# OR if using a GitHub remote URL:
open "https://github.com/<org>/<repo>/compare/<base-branch>...<feature-branch>?expand=1"
```

**Option 3 — Keep branch:**
```bash
# No action required. Branch stays as-is.
echo "Branch preserved. No changes made."
```

**Option 4 — Discard:**
```bash
# Switch back to base branch
git checkout <base-branch>

# Delete local feature branch
git branch -D <feature-branch>

# (If applicable) Delete remote feature branch
git push origin --delete <feature-branch>
```

### Step 6: Cleanup Workspace

Only applies when **Option 1 (Merge locally)** or **Option 4 (Discard)** was selected.

- **Remove stashes:** `git stash drop` or `git stash clear` (confirm with user first).
- **Remove untracked files:** `git clean -fd` (confirm with user first).
- **Remove local tags that no longer exist on remote:** `git fetch --prune origin "+refs/tags/*:refs/tags/*"`.
- **Report final state:**
  ```bash
  git status --short
  git log --oneline -5
  git branch -a
  ```

## Quick Reference

| Step | Action | Key Command |
|------|--------|-------------|
| 1 | Verify tests | `pytest` / `npm test` / `cargo test` |
| 2 | Detect environment | `git status --short` |
| 3 | Determine base branch | `git rev-parse --abbrev-ref HEAD` |
| 4 | Present options | List 1–4 to user |
| 5 | Execute choice | Git commands per option |
| 6 | Cleanup workspace | `git clean -fd`, `git stash clear` |

## References

- `references/cli-i18n-pattern.md` — Dual-language CLI with `--lang` flag + locale dict
- `references/demo-gif-workflow.md` — asciinema → GIF for GitHub README demos

## Red Flags

1. **Uncommitted changes exist** — dirty working tree can cause merge conflicts or accidental data loss. Always commit or stash before proceeding.
2. **Tests are failing** — do not merge or PR with failing tests unless the user explicitly acknowledges and overrides.
3. **Detached HEAD state** — merging or pushing from a detached HEAD can lose work. Check out a named branch first.
4. **Remote branch divergence** — if the local and remote branches have diverged, `git push` may be rejected. Fetch and inspect before force-pushing.
5. **Unpushed commits on base branch** — merging into a base branch that has unpushed commits complicates rollback. Pull updates first.
6. **Large diffs with no description** — a PR or merge with 50+ files changed and no summary is a red flag for incomplete or mis-scoped work.
7. **Confidential or sensitive files in diff** — check for accidentally committed secrets, API keys, credentials, or `.env` files before pushing.
8. **Stale branch (weeks/months old)** — branches long diverged from base may require significant rebase or conflict resolution. Alert the user.
9. **Binary file changes** — unexpected additions of large binaries (`.png`, `.pdf`, `.dmg`) bloat the repository. Flag for review.
10. **Merge conflicts predicted** — if `git merge --no-commit --no-ff <feature-branch>` exits non-zero, there are unresolved conflicts. Do not proceed without resolution.
11. **Missing changelog/version bump** — for release branches, ensure version files and `CHANGELOG.md` are updated before merging.
