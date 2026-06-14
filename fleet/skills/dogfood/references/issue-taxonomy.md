# Issue Taxonomy

Use this taxonomy to classify issues found during dogfood QA testing.
Supports all three modes: 🌐 Web, 🖥️ CLI, ⚙️ System.

## Severity Levels

### Web Mode (Critical / High / Medium / Low)

#### Critical
The issue makes a core feature completely unusable or causes data loss.

**Examples:**
- Application crashes or shows a blank white page
- Form submission silently loses user data
- Authentication is completely broken (can't log in at all)
- Payment flow fails and charges the user without completing the order
- Security vulnerability (e.g., XSS, exposed credentials in console)

### High
The issue significantly impairs functionality but a workaround may exist.

**Examples:**
- A key button does nothing when clicked (but refreshing fixes it)
- Search returns no results for valid queries
- Form validation rejects valid input
- Page loads but critical content is missing or garbled
- Navigation link leads to a 404 or wrong page
- Uncaught JavaScript exceptions in the console on core pages

### Medium
The issue is noticeable and affects user experience but doesn't block core functionality.

**Examples:**
- Layout is misaligned or overlapping on certain screen sections
- Images fail to load (broken image icons)
- Slow performance (visible loading delays > 3 seconds)
- Form field lacks proper validation feedback (no error message on bad input)
- Console warnings that suggest deprecated or misconfigured features
- Inconsistent styling between similar pages

### For CLI / System Mode

#### P0 — Blocking
Service won't start, core flow crashes silently, data loss, crash-loop.

**Examples:**
- Server exits immediately with a stack trace (port conflict, missing dependency)
- CLI returns non-zero on a documented command with valid args
- SQLite thread-safety error blocks a background service
- ImportError on a core module
- Core function raises unhandled exception on normal input

#### P1 — Severe
Important feature is broken, docs claim something that doesn't exist,
tests are missing for a core path, important command fails.

**Examples:**
- README says `tool subcommand --flag` but the flag is not registered
- CLI has no way to list/reference entities the docs describe
- Key API endpoint returns 404 or non-JSON response
- Less than 20% test coverage (<100 tests for a medium-size project)
- Knowledge graph / persistent store returns empty for valid queries

#### P2 — Medium
Minor feature gap, cosmetic CLI output issue, untested edge case,
partial feature works but with quirks.

**Examples:**
- CLI table formatting misaligned on certain terminals
- Port conflict not handled gracefully (crashes instead of suggesting --port)
- No `list` subcommand where one is expected by user convention
- Mock/fake data in persistent store instead of real content

#### P3 — Low
Polish issues, docs typos, missing examples, minor ergonomic improvements.

**Examples:**
- Help text has a typo
- No completion message after a long-running command
- Color/Label inconsistency across subcommand outputs

## Category Mapping (CLI/System Mode)

| Category | Use For |
|----------|---------|
| **Functional** | Feature doesn't work as documented |
| **Docs** | README/docs say X, code does Y |
| **Stability** | Crash, hang, port/thread issue, SQLite thread-safety |
| **TestGap** | Core code path has zero tests |
| **UX** | Confusing output, missing error message, unhelpful exit code |
### Functional
Issues where features don't work as expected.

- Buttons/links that don't respond
- Forms that don't submit or submit incorrectly
- Broken user flows (can't complete a multi-step process)
- Incorrect data displayed
- Features that work partially

### Visual
Issues with the visual presentation of the page.

- Layout problems (overlapping elements, broken grids)
- Broken images or missing media
- Styling inconsistencies
- Responsive design failures
- Z-index issues (elements hidden behind others)
- Text overflow or truncation

### Accessibility
Issues that prevent or hinder access for users with disabilities.

- Missing alt text on meaningful images
- Poor color contrast (fails WCAG AA)
- Elements not reachable via keyboard navigation
- Missing form labels or ARIA attributes
- Focus indicators missing or unclear
- Screen reader incompatible content

### Console
Issues detected through JavaScript console output.

- Uncaught exceptions and unhandled promise rejections
- Failed network requests (4xx, 5xx errors in console)
- Deprecation warnings
- CORS errors
- Mixed content warnings (HTTP resources on HTTPS page)
- Excessive console.log output left from development

### UX (User Experience)
Issues where functionality works but the experience is poor.

- Confusing navigation or information architecture
- Missing loading indicators (user doesn't know something is happening)
- No feedback after user actions (e.g., button click with no visible result)
- Inconsistent interaction patterns
- Missing confirmation dialogs for destructive actions
- Poor error messages that don't help the user recover

### Content
Issues with the text, media, or information on the page.

- Typos and grammatical errors
- Placeholder/dummy content in production
- Outdated information
- Missing content (empty sections)
- Broken or dead links to external resources
- Incorrect or misleading labels
