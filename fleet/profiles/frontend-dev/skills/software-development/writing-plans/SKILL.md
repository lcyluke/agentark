---
name: writing-plans
description: "Write implementation plans: bite-sized tasks, paths, code."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, design, implementation, workflow, documentation]
    related_skills: [subagent-driven-development, test-driven-development, requesting-code-review]
---

# Writing Implementation Plans

## Overview

Write comprehensive implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume the implementer is a skilled developer but knows almost nothing about the toolset or problem domain. Assume they don't know good test design very well.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## When to Use

**Always use before:**
- Implementing multi-step features
- Breaking down complex requirements
- Delegating to subagents via subagent-driven-development

**Don't skip when:**
- Feature seems simple (assumptions cause bugs)
- You plan to implement it yourself (future you needs guidance)
- Working alone (documentation matters)

## Bite-Sized Task Granularity

**Each task = 2-5 minutes of focused work.**

Every step is one action:
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement the minimal code to make the test pass" — step
- "Run the tests and make sure they pass" — step
- "Commit" — step

**Too big:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Right size:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Plan Document Structure

### Header (Required)

Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Task Structure

Each task follows this format:

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Writing Process

### Step 1: Understand Requirements

Read and understand:
- Feature requirements
- Design documents or user description
- Acceptance criteria
- Constraints

### Step 2: Explore the Codebase

Use Hermes tools to understand the project:

```python
# Understand project structure
search_files("*.py", target="files", path="src/")

# Look at similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Check existing tests
search_files("*.py", target="files", path="tests/")

# Read key files
read_file("src/app.py")
```

### Step 3: Design Approach

Decide:
- Architecture pattern
- File organization
- Dependencies needed
- Testing strategy

### Step 4: Write Tasks

Create tasks in order:
1. Setup/infrastructure
2. Core functionality (TDD for each)
3. Edge cases
4. Integration
5. Cleanup/documentation

### Step 5: Add Complete Details

For each task, include:
- **Exact file paths** (not "the config file" but `src/config/settings.py`)
- **Complete code examples** (not "add validation" but the actual code)
- **Exact commands** with expected output
- **Verification steps** that prove the task works

### Step 6: Review the Plan

Check:
- [ ] Tasks are sequential and logical
- [ ] Each task is bite-sized (2-5 min)
- [ ] File paths are exact
- [ ] Code examples are complete (copy-pasteable)
- [ ] Commands are exact with expected output
- [ ] No missing context
- [ ] DRY, YAGNI, TDD principles applied

### Step 7: Save the Plan

```bash
mkdir -p docs/plans
# Save plan to docs/plans/YYYY-MM-DD-feature-name.md
git add docs/plans/
git commit -m "docs: add implementation plan for [feature]"
```

## Principles

### DRY (Don't Repeat Yourself)

**Bad:** Copy-paste validation in 3 places
**Good:** Extract validation function, use everywhere

### YAGNI (You Aren't Gonna Need It)

**Bad:** Add "flexibility" for future requirements
**Good:** Implement only what's needed now

```python
# Bad — YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # Not needed yet!
        self.metadata = {}     # Not needed yet!

# Good — YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

### TDD (Test-Driven Development)

Every task that produces code should include the full TDD cycle:
1. Write failing test
2. Run to verify failure
3. Write minimal code
4. Run to verify pass

See `test-driven-development` skill for details.

### Frequent Commits

Commit after every task:
```bash
git add [files]
git commit -m "type: description"
```

## Common Mistakes

### Vague Tasks

**Bad:** "Add authentication"
**Good:** "Create User model with email and password_hash fields"

### Incomplete Code

**Bad:** "Step 1: Add validation function"
**Good:** "Step 1: Add validation function" followed by the complete function code

### Missing Verification

**Bad:** "Step 3: Test it works"
**Good:** "Step 3: Run `pytest tests/test_auth.py -v`, expected: 3 passed"

### Missing File Paths

**Bad:** "Create the model file"
**Good:** "Create: `src/models/user.py`"

### Claiming Completion Without Fresh Evidence

**Bad:** "All done. Server running. Verified." (said after implementing, before restarting server)
**Good:** Restart server → hit API endpoints → browser-render → console-error-check → THEN claim done.

**Rule:** No completion claim without at least one of: browser console output showing zero JS errors, API response with populated data, or screenshot of rendered UI.

### Assuming API Data Shapes

**Bad:** `workloads.filter(w => w.load < 0.3)` 
**Good:** `(data.workloads?.agents || []).filter(...)`

APIs change over time. A subagent may modify the backend and return `{agents: [...], summary: {}}` where the frontend expects `[{...}, ...]`. Always normalize data at the usage site with `Array.isArray()` guard.

## Execution Handoff

After saving the plan, offer the execution approach:

**"Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?"**

When executing, use the `subagent-driven-development` skill:
- Fresh `delegate_task` per task with full context
- Spec compliance review after each task
- Code quality review after spec passes
- Proceed only when both reviews approve

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**A good plan makes implementation obvious.**

---

## Phase 3: Post-Implementation UAT (Mandatory)

**Do NOT claim "done" until this phase is complete.** Implementation without fresh verification is not implementation — it's wishful thinking.

### Step 1: Restart the Service

Subagents may have modified files that the running process hasn't picked up. Always restart:

```bash
lsof -ti:<PORT> | xargs kill -9 2>/dev/null
sleep 2
<start command>
sleep 4  # Wait for startup
```

### Step 2: Verify Backend APIs

Hit every API endpoint used by the frontend. Check HTTP codes AND data shapes:

```python
from hermes_tools import terminal, json

endpoints = ['/api/profiles', '/api/tasks', '/api/autonomous', ...]
for ep in endpoints:
    r = terminal(f"curl -s {base}{ep}")
    data = json.loads(r['output'])
    # VERIFY SHAPE, not just HTTP 200
    if isinstance(data, list) and len(data) == 0:
        print(f"⚠️ WARNING: {ep} returns empty list")
```

### Step 3: Browser Rendering Check

Navigate to the page and verify JS executes without errors:

```javascript
// Browser console
JSON.stringify({
  hasState: typeof state !== 'undefined',
  errors: window.__errors || 'none',
  cards: document.querySelectorAll('.fleet-card').length
})
```

### Step 4: Click-Through All Views

Navigate to every view. Check that:
- HTML elements render (not just exist, but have content)
- No console errors appear
- Data from APIs actually populates the UI

### Step 5: Subagent Side-Effect Scan

After delegating to a subagent (e.g., backend-dev), scan the codebase for:

| Signal | Check | Why |
|--------|-------|-----|
| Duplicate routes | `grep -n "@app.route"` | Subagent may re-add existing routes |
| Unclosed template literals | Count backticks parity | A single missing `` ` `` breaks ALL JS |
| Imbalanced braces | `count('{') - count('}')` | Syntax error silence |
| Missing imports | `grep "from .* import" ` | New code may reference un-imported modules |

**JS Template String Debugging Recipe:** See `references/js-template-debugging.md`.

### Pitfall: API Data Shape Assumptions

Backend APIs may return objects where the frontend expects arrays. Common example:

```
❌ ASSUMED:  workloads = [{agent_id:..., load: 0.5}, ...]
✅ ACTUAL:   workloads = {agents: [{...}], summary: {...}, total_active_tasks: 0}
```

The fix pattern — defensive normalization at usage site:
```javascript
const workloads = (data.workloads?.agents) || (Array.isArray(data.workloads) ? data.workloads : []);
```

Never call `.filter()`, `.map()`, `.length`, or `.slice()` on API data without first asserting it's an array.

## When NOT to Write a Formal Plan

The standard plan-then-delegate flow is overkill when:
- You are the sole implementer, working directly on a single file
- The work is reference-driven (porting features from a design file into an existing template)
- No subagents will be involved

In these cases, use the `todo` tool for in-memory task tracking and follow the workflow documented in `references/html-template-enhancement.md` — a CSS-first, incremental-patch pattern for large HTML template enhancement tasks. Write the plan inline with your response (feature mapping table), not as a separate `docs/plans/` file.

If the page renders but JS is silent (no state, no functions), consult `references/js-template-debugging.md` — this is almost always an unclosed template literal introduced by a subagent.
