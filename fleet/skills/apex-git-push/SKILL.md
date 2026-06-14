---
name: apex-git-push
description: "Full Apex GitHub lifecycle: commit, push, create repo, manage auth."
version: 2.1.0
---

# Apex GitHub Lifecycle

## Trigger

- User says: "push apex", "推GitHub", "更新仓库", "上传到GitHub", "commit"
- User says: "create repo", "推代码", "push"
- User asks to put Apex on GitHub

## Remote Config

- Repo: `https://github.com/lcyluke/apex.git`
- Branch: `main`
- Local path: `~/Desktop/2026AIAPP/Apex`

## Auth (for initial setup or new machines)

Goal: the agent cannot directly handle GitHub PATs (security scanner blocks PAT-in-command and PAT-in-write_file).

**Best reliable sequence** (let user type the PAT):

```bash
cd ~/Desktop/2026AIAPP/Apex
git remote add origin https://github.com/lcyluke/apex.git
git branch -M main
git push -u origin main
# Git prompts for username (GitHub login) and password (PAT)
```

**Alternative — use `gh` with user-set env var:**

```bash
export GH_TOKEN="github_pat_..."
gh repo create lcyluke/apex --private --source=. --push 2>&1
```

**If `gh auth login --web` is needed:** background the command with PTY, capture the one-time code, tell user to open `https://github.com/login/device` in their browser.

**Pitfall**: `gh` device-code flow may fail with `unexpected EOF` from OAuth callback. Fall back to PAT + `git push` directly.

## Steps for Routine Push

```bash
cd ~/Desktop/2026AIAPP/Apex
git add -A
git commit -m "<concise description>"
git push
```

## Commit Message Style

- If user gave specific description: use it verbatim
- Template: `"<category>: <what changed>"` — feat, fix, docs, refactor, test, chore, i18n, perf

## Verification

```bash
cd ~/Desktop/2026AIAPP/Apex
git log --oneline -3
git remote -v
```

## Model Upgrade Pattern

When upgrading the LLM model across the full Apex system (6 source files, 17 profiles):

1. Source files: `grep -rl 'old-model-name' apex/ --include='*.py'` → 6 files
2. Profile YAMLs: `cd ~/.apex/profiles && for f in $(grep -l "old-model" *.yaml); do sed -i '' 's/old/new/g' "$f"; done` → 10-17 files
3. Hermes config: `hermes config set model.default new-model-name`
4. Hermes .env: remove conflicting BASE_URL override
5. Verify: `apex run "What model are you using?"`

Use `patch(replace_all=True)` for batch updates in source files.

## Private Repo Image 404 Fix

raw.githubusercontent.com does NOT serve files from private repositories. If committed images return 404:

1. Confirm file is in git: `git ls-files docs/images/`
2. Check repo visibility: `curl -s https://api.github.com/repos/user/repo | python3 -c "import sys,json; print(json.load(sys.stdin).get('private'))"`
3. Make public: `gh repo edit user/repo --visibility public`
4. Verify: `curl -sI "https://raw.githubusercontent.com/user/repo/main/path/file.png" | grep "HTTP/"` returns 200

## README Source Code Map Pattern

When the user asks to sync the README's code map with the actual folder tree:

1. Run `find apex -type f | sort` from the project root
2. Format as a tree matching the GitHub file explorer exactly
3. Include EVERY file: `__init__.py`, templates, scripts, nested commands, tests
4. One-line descriptions per file — brief purpose summaries, NOT process histories or commit logs
5. Max tree depth: 3-4 levels. Group by directory with section headers
6. Missing entries (e.g. `docs/`, `scripts/`, `tests/`, nested `commands/`) are immediately noticed by users

## Related Skills

- `github-repo-management` — general GitHub repo operations
- `multi-agent-system-design` — the Apex build methodology
