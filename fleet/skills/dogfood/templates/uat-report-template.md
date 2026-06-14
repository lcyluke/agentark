# UAT Report

**Target:** {system_name}
**Date:** {date}
**Scope:** {scope_description}
**Tester:** Hermes Agent (systematic UAT)

---

## Executive Summary

| Surface | Status | Details |
|---------|--------|---------|
| Module Imports | {status_imports} | {m_of_n} modules pass |
| CLI Commands | {status_cli} | {m_of_n} documented commands work |
| REST API | {status_api} | {m_of_n} endpoints return valid JSON |
| Test Suite | {status_tests} | {n} tests, {passes}/{failures}/{skips} |
| **Overall Verdict** | **{verdict}** | {one_sentence_assessment} |

**Total Issues:** {total_count} (🔴 P0: {p0} · 🟠 P1: {p1} · 🟡 P2: {p2} · 🔵 P3: {p3})

---

## Issues

### Issue #1: {title}

| Field | Value |
|-------|-------|
| **Severity** | {P0/P1/P2/P3} |
| **Category** | {Functional/Stability/Docs/TestGap/UX} |
| **Where** | {CLI command / API endpoint / module / test} |

**Description:**
{what_is_wrong}

**Evidence:**
```
{paste terminal output, error trace, or diff here}
```

**Expected:**
{what_should_happen}

**Actual:**
{what_actually_happens}

---

<!-- Repeat per issue, sorted P0 → P3 -->

## Issues Summary

| # | Title | Severity | Category | Surface |
|---|-------|----------|----------|---------|
| 1 | {title} | P0 | {category} | {surface} |
| 2 | {title} | P1 | {category} | {surface} |

## Documentation Consistency

| README Claim | Actual Behavior | Status |
|--------------|-----------------|--------|
| `apex run --swarm` | No --swarm flag | ❌ Missing |
| `apex ops release list` | No such command | ❌ Missing |

## Testing Coverage

### Tested
- {list of what was tested}

### Not Tested / Out of Scope
- {areas not covered and why}

### Blockers
- {issues that prevented testing certain areas}

---

## Verdict Detail

**{verdict}**

{expanded reasoning — what needs to happen for the system to pass UAT, estimated fix time, and which issues are trivial vs structural}

## Recommendations (Priority Order)

1. {first thing to fix}
2. {second thing to fix}
3. {third thing to fix}
