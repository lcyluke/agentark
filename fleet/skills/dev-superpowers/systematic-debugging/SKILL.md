---
name: systematic-debugging
description: "Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes. Enforces root-cause investigation before any fix attempt."
version: 1.0.0
author: Origin Agent
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Core principle: ALWAYS find root cause before attempting fixes.

When you encounter a bug, test failure, or unexpected behavior, do NOT jump to fixes. Follow the four phases below methodically. Every fix must be traceable back to a verified root cause.

## The Iron Law

**NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST**

This is non-negotiable. Any attempt to skip or shortcut root-cause investigation is a violation of this skill. If you find yourself thinking "I already know what's wrong" or "let me just try this quick fix," stop and run through the four phases.

## The Four Phases

### Phase 1: Root Cause Investigation

**Goal:** Find the exact point where behavior diverges from expected.

| Activity | Description |
|---|---|
| Read the errors | Examine the exact error message, stack trace, and surrounding logs. Pay attention to file names, line numbers, error types, and column offsets. |
| Reproduce | Run the failing test / command again to confirm it's deterministic. Note any flakiness or environmental differences. |
| Check recent changes | Look at git log, diff, or file modification times. Most bugs are introduced by a recent change — identify it. |
| Trace data flow | Follow the data from input to failure point. Inspect variable values, API responses, database queries, and intermediate transformations. |
| Isolate the failure | Minimize the reproduction case. Strip away unrelated code until only the essential failure remains. |
| Check assumptions | List every assumption you're making about the code, data, or environment. Test each one. |

### Phase 2: Pattern Analysis

**Goal:** Understand how the system should work by examining working examples.

| Activity | Description |
|---|---|
| Find working examples | Search for other tests, implementations, or usages of the same function/module that pass. |
| Compare against references | Check documentation, type stubs, schemas, or reference implementations. Does the failing code follow the same pattern? |
| Identify the delta | What is different between the working case and the failing case? That delta is likely the root cause or a strong clue. |
| Review similar bugs | Check if this pattern matches known bugs in the same codebase or library. |

### Phase 3: Hypothesis and Testing

**Goal:** Form a single, testable hypothesis and verify it with minimal intervention.

| Activity | Description |
|---|---|
| Form a single hypothesis | State clearly: "The root cause is X because Y." Only one hypothesis at a time. |
| Design a minimal test | What is the smallest change or experiment that would prove or disprove the hypothesis? |
| Execute the test | Run the experiment. Do NOT make unrelated changes. |
| Evaluate results | Did the hypothesis hold? If yes, proceed to Phase 4. If no, return to Phase 1. |

### Phase 4: Implementation

**Goal:** Fix the root cause and verify all tests pass.

| Activity | Description |
|---|---|
| Create a failing test | First, write a test that reproduces the bug. Verify it fails before the fix. |
| Implement the fix | Make the minimal change that addresses the root cause. Do not fix symptoms. |
| Verify | Run the failing test — it should pass. Then run the full test suite to check for regressions. |
| Document | If the fix non-obvious, add a comment explaining why the change was made. |

## Red Flags

Watch for these warning signs that you're not debugging properly:

| # | Red Flag | Why It's Dangerous |
|---|---|---|
| 1 | "Let me just try this quick fix" | Bypasses root-cause analysis. Quick fixes often introduce new bugs. |
| 2 | Changing multiple things at once | You won't know which change fixed (or broke) the issue. |
| 3 | Skipping reproduction | If you can't reproduce it, you can't verify the fix. The bug may still be latent. |
| 4 | Adding print/log statements instead of reasoning | Spamming logs is reactive. Trace data flow deliberately instead. |
| 5 | Blaming the compiler, framework, or library | 99% of the time the bug is in your own code. Check there first. |
| 6 | "It worked before, so nothing I did could cause this" | Every assumption is worth verifying. Check git diff objectively. |
| 7 | Fixing symptoms instead of the root cause | The symptom will reappear or manifest elsewhere. |
| 8 | Not checking the actual input values | Bugs often live in unexpected input. Verify what the code actually receives. |
| 9 | Making the same change in multiple places | If one location was wrong, assume others are too — but verify each independently. |
| 10 | Over-fixing (changing more than necessary) | Increases surface area for new bugs. Minimal changes are safer. |
| 11 | Ignoring test failures that seem unrelated | Could indicate a deeper issue or a regression from your change. |
| 12 | Debugging in production | You lose the ability to add instrumentation safely. Reproduce locally first. |

## Common Rationalizations

When you hear yourself thinking any of these, stop and go back to Phase 1:

| # | Rationalization | Why It's Wrong |
|---|---|---|
| 1 | "I already know what the bug is" | You might be right, but skipping verification creates blind spots. Formulate a hypothesis and test it. |
| 2 | "This is just a typo" | Even one-character bugs have root causes (e.g., copy-paste error, misread API). Understand why the typo happened. |
| 3 | "It's too small to matter" | Small bugs compound. The time saved skipping analysis is lost tenfold in later debugging. |
| 4 | "I'll just fix it and see if the tests pass" | This is gambling, not debugging. Fixes should be derived from root causes, not tested by luck. |
| 5 | "The tests are flaky" | Flaky tests are bugs too. Either way, investigate before dismissing. |
| 6 | "I've seen this before, it's the same issue" | Similar symptoms can have different root causes. Verify instead of assuming. |
| 7 | "We can clean it up later" | Later never comes. The fix will accumulate debt and confuse future maintainers. |
| 8 | "The error message is confusing, let me just ignore it" | Error messages contain valuable information. If confusing, that itself is a clue about the root cause. |
| 9 | "I don't need to reproduce it, the stack trace is clear" | Stack traces can be misleading or incomplete. Reproduce and verify every time. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|---|---|---|
| **1. Root Cause Investigation** | Read errors, reproduce, check git diff, trace data flow, isolate failure, check assumptions | Exact root cause identified — you can state "The failure happens at line X because Y" |
| **2. Pattern Analysis** | Find working examples, compare references, identify the delta, review similar bugs | You understand how the system should work and what specifically differs in the failing case |
| **3. Hypothesis and Testing** | Single hypothesis, minimal test, execute, evaluate | Hypothesis confirmed or disproven with clear evidence |
| **4. Implementation** | Write failing test, implement minimal fix, verify full suite, document | Bug fixed, test passes, no regressions, root cause documented |
