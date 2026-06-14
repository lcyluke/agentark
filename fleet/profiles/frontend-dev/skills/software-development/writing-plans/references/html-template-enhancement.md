# HTML Template Enhancement — Reference-Driven Workflow

## When to Use

Use this pattern when:
- A reference design (HTML file, mockup, or spec) exists and must be integrated into a target template
- The target file is large (1000+ lines) and modifying it all at once is error-prone
- You're the implementer (not delegating) — direct coding, no subagents
- Features are UI components: drawers, modals, diagrams, cards, chat engines
- The target file already has working API integration that must be preserved

## The 5-Phase Workflow

### Phase 1: Reference Analysis (Read Everything)

Read the reference file completely — no partial reads. Understand every feature:
```
read_file(path="reference.html")  # full file, no pagination
```
Map features to a structured checklist:
- Component name → CSS classes used → HTML structure → JS functions → Data model
- Note: colors, spacing, typography, animation patterns from the reference CSS

### Phase 2: Target Codebase Audit

Read the target file and its backend dependencies:
```
read_file(path="target.html")      # full file
search_files("*.py", path="api/")  # understand API surface
search_files("*.py", path="templates/")  # find sibling templates for patterns
```
Identify:
- Existing views, navigation items, API endpoints
- Which CSS variables/classes already exist (reuse, don't duplicate)
- Where new HTML must be injected (between which existing elements)
- JS state object structure (extend it, don't replace it)

### Phase 3: CSS Injection (Always First)

Add ALL new CSS rules before touching HTML or JS:
```
patch(path="target.html", old_string="last_existing_css_rule", new_string="last_existing_css_rule\n\n/* new components */\n...")
```
Rules:
- Reuse existing CSS variables (`var(--bg)`, `var(--teal)`, etc.) — don't create new ones unless necessary
- Group new rules by component with comment headers
- Insert before the closing `</style>` tag, before any `@media` blocks
- Include ALL components that will be added, even if some won't be populated immediately

### Phase 4: HTML Structure (Insert Skeleton First)

Add empty component shells first, then populate:
1. Navigation items (sidebar links)
2. View sections (with placeholder divs and IDs)
3. Drawers, modals, FAB (fixed-position elements go at the end, before `</body>`)

``` 
patch(mode="replace", old_string="<!-- EXISTING_ANCHOR -->", new_string="<!-- EXISTING_ANCHOR -->\n<!-- NEW COMPONENT -->\n...")
```
Rules:
- Find a stable, unique anchor string in the HTML to inject after/before
- Use existing HTML comments as anchors when available
- Add `id` attributes to every new container div — needed for JS `$('#id')` queries
- For tables/forms inside dynamic sections, add the wrapper with an `id` and let JS populate

### Phase 5: JS Logic (Wire Last)

Add functions after the last existing JS function but before event listeners:
```
patch(old_string="/* ========== last_existing_section ========== */\n...}", new_string="...}\n\n/* ========== NEW SECTION ========== */\n...")
```
Rules:
- Extend existing `state` objects with new fields (don't create a second state)
- Add new view titles to the existing `VIEW_TITLES` map
- Register new views in the `renderActiveView()` switch statement
- Wire onclick handlers in HTML templates directly (`onclick="fn('${id}')"`) — inline is fine for template-driven UIs
- For chat/decomposition engines: implement keyword matching → plan generation first, API integration second

## Verification Protocol

After ALL phases complete, verify with browser tools:

```
# 1. Restart server (fresh serve)
terminal("kill old; python -m apex dashboard --port 8080 &")

# 2. Navigate and check HTTP status
terminal("curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/cc")

# 3. Browser load + error check
browser_navigate("http://localhost:8080/cc")
browser_console()  # must show zero JS errors

# 4. Click through ALL views
browser_snapshot(full=true)  # verify nav items, header buttons, drawer shells exist
```

If `browser_console()` shows errors: go back to JS phase and fix. If HTTP returns non-200: check Flask templates path.

## When NOT to Use This

- If the target file is <200 lines — just rewrite the whole thing
- If there are no backend APIs to integrate — consider a standalone page
- If the feature set is small (1-2 components) — inline the HTML/JS directly
- If you're delegating to subagents — use the standard writing-plans → subagent-driven-development flow instead

## Common Pitfalls

### PITFALL: Duplicating CSS variables
**Wrong:** Creating `--my-new-bg: #0a0d12` 
**Right:** Using `var(--bg)` which already equals `#0a0d12`

### PITFALL: Overwriting the entire file
**Wrong:** `write_file(path, new_content)` on a 1700-line file
**Right:** Use `patch` with targeted `old_string` / `new_string` pairs

### PITFALL: Adding JS before HTML
**Wrong:** `patch` new JS functions that reference `$('#newComponent')` before the HTML exists
**Right:** Add HTML structure first, JS last

### PITFALL: Forgetting to update `VIEW_TITLES`
**Wrong:** Adding a new nav item and view section without adding to the titles map
**Right:** Add to `VIEW_TITLES` and `renderActiveView()` switch together

### PITFALL: Not re-reading the file after large patches
**Wrong:** Assuming the file state after 5+ patch operations
**Right:** `terminal("wc -l file && grep -c '<script>' file")` to verify structural integrity
