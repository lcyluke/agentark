# Dashboard Consolidation Pattern

## Rule: One entry point, one template file

After evolving through V3→V4→V5→Command Center, consolidate to a single `command_center.html` served at root `/`.

### Steps

1. Delete old template files: `dashboard.html`, `dashboard_v4.html`, `dashboard_v5.html`, `dashboard_daily.html`, `auth.html`
2. Remove old routes (`/v4`, `/v5`, `/v6`, `/cost`, `/cc`)
3. Set root `/` to `command_center.html`
4. Remove all aliases — no `/cc`, no `/dashboard`

### Why

- Multiple entry points confuse users and create maintenance burden
- Old versions accumulate broken references (deleted templates, stale APIs)
- Single-file simplicity: one template, one URL, zero ambiguity
- Shorter URL (just `/`) = cleaner deployment

### Verification

```bash
# After cleanup:
ls templates/         # Should show only command_center.html
curl localhost:8080/  # Returns command_center.html
curl localhost:8080/cc -o /dev/null -w "%{http_code}"  # 404
```

### Date applied
2026-06-07 — reduced from 7 template files to 1
