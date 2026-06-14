# Web QA Checklist

Use this as a quick reference when running web-mode dogfood. Follow the 5-phase workflow from the main SKILL.md, and check off items here.

## Phase 1 — Plan
- [ ] Create output directory: `{output_dir}/screenshots/`
- [ ] Identify pages to test (landing, nav flows, forms, edge cases)
- [ ] Build rough sitemap

## Phase 2 — Explore
- [ ] Navigate to each page: `browser_navigate(url)`
- [ ] Snapshot DOM: `browser_snapshot()` — understand structure
- [ ] Check console: `browser_console(clear=true)` — JS errors = high value
- [ ] Annotated screenshot: `browser_vision(annotate=true)` — map interactive elements
- [ ] Click every button and link
- [ ] Fill and submit forms with valid + invalid data
- [ ] Test keyboard nav: Tab, Enter
- [ ] Scroll to bottom: `browser_scroll(direction="down")`
- [ ] After each interaction: re-check console + visual changes

## Phase 3 — Collect Evidence
- [ ] Screenshot every issue: `browser_vision()` — note the screenshot_path
- [ ] Record: URL, steps, expected, actual, console errors
- [ ] Classify: severity + category per issue-taxonomy.md

## Phase 4 — Categorize
- [ ] De-duplicate issues
- [ ] Sort by severity (Critical first)
- [ ] Count by severity

## Phase 5 — Report
- [ ] Use `templates/dogfood-report-template.md`
- [ ] Include: exec summary, per-issue sections, summary table, notes
- [ ] Embed screenshots: `MEDIA:<screenshot_path>`
