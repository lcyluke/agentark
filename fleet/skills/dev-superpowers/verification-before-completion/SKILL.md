---
name: verification-before-completion
description: "Use when about to claim work is complete, fixed, or passing - requires running verification commands and confirming output before making any success claims. Evidence before assertions always."
version: 1.0.0
author: Origin Agent
---

# Verification Before Completion

## Overview

**Core principle:** Evidence before claims, always. Claiming work is complete without verification is dishonesty, not efficiency.

This skill instills a mandatory gate before any completion, fix, or success assertion. Every "it works" statement must be backed by freshly-run verification output. The agent must never take the user's or its own word that something is fixed — it must prove it through command execution and output inspection.

## The Iron Law

**NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE**

- No "Tests pass" without showing the test run.
- No "Linter is clean" without showing the linter output.
- No "Build succeeds" without showing the build log.
- No "Bug is fixed" without showing the reproduction case now passing.
- No "Deployed successfully" without showing the deployment confirmation.

The output must be from the current session — cached or assumed results are invalid. If the command cannot be run (environment unavailable, missing dependencies, etc.), that must be reported as a barrier to completion, not bypassed with an assertion.

## The Gate Function

Before claiming any status — complete, fixed, passing, deployed, resolved, done — the agent MUST execute the following five-step gate:

1. **IDENTIFY** — Determine the single command (or minimal sequence) that would prove or disprove the claim. Be specific: `pytest tests/unit/test_foo.py -x` not just "run tests".
2. **RUN** — Execute the full command. Do not truncate flags, skip steps, or run a subset unless it is the definitive proof. Capture all output (stdout + stderr).
3. **READ** — Inspect the entire output. Do not skim. Check exit codes, error lines, warning counts, summary lines.
4. **VERIFY** — Confirm that the output explicitly supports the claim. Look for pass/fail counts, "0 errors", "BUILD SUCCESSFUL", "All tests passed", absence of regression markers, etc. If the output is ambiguous, do not proceed — run a more specific command.
5. **ONLY THEN CLAIM** — Present the evidence to the user and state the conclusion. Format: "[Evidence: command output snippet] → Claim: ..."

**Failure at any step resets the gate.** If step 2 produces an error, fix it first. If step 3 reveals a failure, do not claim success. If step 4 shows ambiguous results, refine step 1 and loop.

## Common Failures

| Claim | Verification Command | What to Check |
|---|---|---|
| Tests pass | `pytest --tb=short -q` | "FAILED", "X failed", exit code != 0 |
| Linter clean | `ruff check .` / `flake8 .` / `eslint .` | "error", "warning", "X problems", exit code != 0 |
| Build succeeds | `npm run build` / `go build ./...` / `cargo build` | "ERROR", "Build failed", non-zero exit code, missing artifacts |
| Bug fixed | Reproduction command or test case | Previously failing case now passes with expected output |
| Regression clean | `pytest --regression-only` or full suite | Zero new failures vs baseline, no unexpected skips |
| Type checks pass | `mypy .` / `tsc --noEmit` | "Found X errors", "error TS...", exit code != 0 |
| Formatting correct | `black --check .` / `prettier --check .` | "would reformat", "error", non-zero exit code |
| Security audit clean | `bandit -r .` / `npm audit` / `trivy fs .` | "Issues found", "HIGH", "CRITICAL", non-zero exit |
| Docker build | `docker build -t test .` | "ERROR", "failed to solve", exit code != 0 |
| Deployment | `deploy script output` / `kubectl rollout status` | "error", "CrashLoopBackOff", "unhealthy", non-zero exit |

## Red Flags

| # | Red Flag | Why It's Dangerous |
|---|---|---|
| 1 | "It worked on my machine" without showing output | No evidence; environment differences may hide failures. |
| 2 | "I ran the tests earlier and they passed" | Stale results; code may have changed since, or tests may be non-deterministic. |
| 3 | "Trust me, it's fixed" / "I checked it already" | Appeal to authority substitutes for evidence. Always run the gate fresh. |
| 4 | "The output is too long, here's a summary" | Summarization can omit critical failures. Show raw output or at minimum the tail/summary line. |
| 5 | "The tests pass except for pre-existing failures" | Pre-existing failures are still failures. Either document them as known and block unrelated changes, or fix them first. |
| 6 | "I can't run the verifier, but I'm sure it's fine" | Environmental blockers must be resolved or escalated. Assumption is not verification. |
| 7 | "There are no errors (I didn't check warnings)" | Warnings are unacknowledged risks. Many projects treat warnings as errors. |
| 8 | "The build succeeds on CI" without local verification | CI may have different state (cached deps, different OS/architecture). Local verification is required first. |
| 9 | "I only changed a comment, no need to verify" | Even comments can break doc generation, type stubs, or linter rules. Verify everything. |
| 10 | "I saw the green checkmark on the PR" | CI results may be stale, gated on different commit, or flaky. Run locally or fetch fresh CI output. |

## When To Apply

Apply this skill **every time** the agent is about to make any of these statements:

- "Done."
- "Fixed."
- "Tests pass."
- "The build is green."
- "It's working now."
- "That should resolve the issue."
- "The bug is squashed."
- "Ready for review."
- "All checks pass."
- "Deployment is complete."
- "The refactor didn't break anything."
- "No regressions introduced."

Apply it **even if**:

- The change was trivial (typo, comment, rename).
- The user explicitly says "don't bother testing."
- The fix looks obvious.
- The environment is degraded (report the barrier instead).
- The previous run was seconds ago (run it again — state changes, caches expire, non-determinism exists).

**Do not skip the gate. Do not shortcut the gate. Do not assume the gate passed without running it.**

Evidence before claims, always.
