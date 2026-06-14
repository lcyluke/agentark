---
name: notion-api-pitfalls
description: Hard-won pitfalls and workarounds for the Notion API v2025-09-03. Covers the database/data_source dual-ID model, silent property-drop on database creation, integration access requirements, and reliable patterns for batch operations. Load this alongside the main `notion` skill whenever working with the 2025-09-03 API version.
version: 1.0.0
author: hermes-experience
license: MIT
metadata:
  hermes:
    tags: [Notion, API, Pitfalls, Reference]
---

# Notion API v2025-09-03 Pitfalls

Load this together with the main `notion` skill. It captures non-obvious failures that cost real debugging time.

## 1. database_id vs data_source_id — the dual-ID model

The 2025-09-03 API split each Notion database into two addressable objects:

- `database_id` — the page-like container.
- `data_source_id` — the actual table you query.

Endpoints expect different IDs:

| Operation | Endpoint | ID to use |
|---|---|---|
| Create database | `POST /v1/databases` | parent page_id |
| Get database (metadata + data_source list) | `GET /v1/databases/{database_id}` | database_id |
| Get / patch schema | `GET\|PATCH /v1/data_sources/{ds_id}` | data_source_id |
| Query items | `POST /v1/data_sources/{ds_id}/query` | data_source_id |
| Create a page inside the database | `POST /v1/pages` with `parent: {"database_id": "..."}` | database_id |

To resolve the data_source_id, call `GET /v1/databases/{database_id}` and read `.data_sources[0].id`.

A search response containing a database returns it as `"object": "data_source"` with the data_source_id — but the create-page parent still needs the database_id, so search results are NOT directly usable for parent references.

## 2. Silent property drop on database creation

`POST /v1/databases` with a fully-populated `properties` object can return HTTP 200 with a valid database object — yet the resulting data source ends up with **only the title field**. All other properties are silently discarded. This is intermittent and undocumented.

**Mitigation pattern**: always verify, and patch if needed:

```bash
# 1. Create
DB=$(curl -s -X POST https://api.notion.com/v1/databases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d @create_body.json)

DS_ID=$(echo "$DB" | jq -r '.data_sources[0].id')

# 2. Verify schema
PROP_COUNT=$(curl -s "https://api.notion.com/v1/data_sources/$DS_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Notion-Version: 2025-09-03" \
  | jq '.properties | length')

# 3. Patch if dropped
if [ "$PROP_COUNT" -lt 5 ]; then
  curl -s -X PATCH "https://api.notion.com/v1/data_sources/$DS_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Notion-Version: 2025-09-03" \
    -H "Content-Type: application/json" \
    -d @properties_body.json
fi
```

The PATCH form of the same schema reliably sticks. Treat the initial create as "best effort" only.

## 3. Integration access — the #1 false alarm

A freshly created integration has **zero workspace access**, regardless of token validity. Every API call against any page returns:

```
"Could not find page with ID: ... Make sure the relevant pages and
databases are shared with your integration"
```

This is NOT a bad token. The user must:

1. Open the target page in Notion
2. Click the `···` menu (top right)
3. Choose **Connections** → **Add connections**
4. Pick the integration name → Confirm

Once a parent page is connected, child pages and databases inherit access. Always confirm this step before debugging the token or headers.

## 4. The "page object: error" health check

To distinguish "bad token" vs "no access", call:

```bash
curl -s "https://api.notion.com/v1/pages/{any_known_page_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Notion-Version: 2025-09-03"
```

- Returns `{"object": "page", "id": "...", ...}` → token good, access good.
- Returns `{"object": "error", "code": "unauthorized"}` → token bad.
- Returns `{"object": "error", "message": "Could not find page..."}` → token good, access missing (see #3).

## 5. Batch create — rate limiting and partial-failure pattern

Notion's documented limit is ~3 req/sec, but bursts can trigger soft throttling. For batch page creation (e.g. seeding a database with dozens of rows):

- Sleep ~0.34s between requests as a baseline.
- Wrap every POST in try/except and capture the raw error body — Notion's validation errors are highly specific (e.g. `"<field> is not a property that exists"` signals a schema mismatch you can detect and skip).
- On 429, back off exponentially (start at 5s).
- Run batches as background processes (`background=true, notify_on_complete=true`), not foreground — long sleeps in foreground waste agent iterations.

## 6. Recovering from a stale background batch

If a long-running background uploader is producing `[SYSTEM: ...]` notification spam because of schema mismatches:

```bash
# Find and kill stale uploaders by name pattern
ps aux | grep -E "upload|notion" | grep -v grep
pkill -f upload.py
pkill -f update_coords
```

Then re-validate the database schema (step 2) before relaunching. The most common cause is launching the uploader before the schema PATCH completed.

## 7. Working with v2025-09-03 from Python (no SDK)

The official SDK lags the API version. Use `urllib.request` directly:

```python
import os, json, urllib.request

API = "https://api.notion.com/v1"
H = {
    "Authorization": f"Bearer {os.environ['NOTION_API_KEY']}",
    "Notion-Version": "2025-09-03",
    "Content-Type": "application/json",
}

def req(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(API + path, data=data, headers=H, method=method)
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read())
```

This avoids the SDK's version-pinning lag and gives you direct access to all 2025-09-03 features.

## 8. Useful property type cheat sheet (2025-09-03 specifics)

The most commonly mis-typed properties:

```json
"价格": {"number": {"format": "yuan"}}      // CNY symbol
"日期": {"date": {}}                         // empty object — date config goes on the value
"标签": {"multi_select": {"options": [...]}}
"关联场馆": {"relation": {
    "database_id": "...",                   // use database_id, not data_source_id
    "single_property": {}
}}
"标题": {"title": {}}                        // every database needs exactly one title prop
```

The `relation` property in 2025-09-03 still references **database_id**, not data_source_id — one of the few places where the old ID is correct.

## 9. Verification checklist before declaring "database setup complete"

After any database creation flow, before reporting success:

- [ ] `GET /v1/databases/{database_id}` returns the expected title and 1+ data_sources entries.
- [ ] `GET /v1/data_sources/{ds_id}` shows ALL expected properties with correct types.
- [ ] Test query: `POST /v1/data_sources/{ds_id}/query` with `{"page_size": 1}` returns successfully (even with 0 results).
- [ ] Test create: insert one dummy row, then DELETE or archive it. Validates the full write path.
- [ ] No background uploader processes left running from previous failed attempts.

Skip any of these and the failure tends to surface hours later as a `[SYSTEM: ...]` notification.
