---
name: deepseek-provider
description: DeepSeek provider configuration for Hermes Agent — endpoint selection, model mapping, thinking-mode pitfalls.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [deepseek, provider, configuration, troubleshooting]
---

# DeepSeek Provider Configuration

DeepSeek exposes two API endpoints that map to different model behaviors. Choosing the wrong one silently routes to the wrong model class.

## Endpoint vs Model Mapping

| Endpoint | Format | Models | Notes |
|----------|--------|--------|-------|
| `https://api.deepseek.com/v1` | OpenAI-compatible | `deepseek-chat`, `deepseek-chat-v3`, `deepseek-v4-pro`, `deepseek-v4-flash` | Standard chat models. `deepseek-v4-pro` is the current best model. Use this endpoint. |
| `https://api.deepseek.com/anthropic` | Anthropic Messages-compatible | `deepseek-reasoner` (thinking models) | Requires `thinking` block passthrough. Hermes does NOT support this — causes HTTP 400. |

## Configuration

```bash
hermes config set providers.deepseek.base_url "https://api.deepseek.com/v1"
hermes config set model.default "deepseek-chat"
hermes config set model.provider "deepseek"
```

## Pitfall: /anthropic Endpoint

Setting `base_url` to `https://api.deepseek.com/anthropic` silently maps to DeepSeek's reasoning/thinking models regardless of `model.default`. Hermes then fails with:

```
HTTP 400: The `content[].thinking` in the thinking mode must be passed back to the API.
```

This error is **not retryable** and means the wrong endpoint is configured.

## Pitfall: auth.json Credential Pool Overrides .env

When Hermes runs in **profile mode** (`hermes -p <name>`) — as all wrapper scripts do — the API key is read from `credential_pool` in `auth.json`, **NOT** from `DEEPSEEK_API_KEY` in `.env`.

### Symptom
```yaml
HTTP 401: Authentication Fails, Your api key: ****ired is invalid
```
Despite the key being verifiably correct (curl test succeeds with it).

### Root Cause
`auth.json` has a `credential_pool.deepseek` entry with a stale or missing `api_key`, or a wrong `base_url`:
```json
{
  "credential_pool": {
    "deepseek": [
      {
        "base_url": "https://api.deepseek.com/anthropic",  // WRONG
        "api_key": "..."                                   // MISSING or stale
      }
    ]
  }
}
```

Two files need fixing:
- `~/.hermes/auth.json` — main credential pool
- `~/.hermes/profiles/<name>/auth.json` — per-profile credential pool

### Fixes

**Fix 1 — Fix auth.json (addresses root cause):**
```bash
python3 << 'PYEOF'
import json, os
for path in [
    os.path.expanduser('~/.hermes/auth.json'),
    os.path.expanduser('~/.hermes/profiles/<name>/auth.json'),
]:
    with open(path) as f:
        auth = json.load(f)
    for entry in auth.get('credential_pool', {}).get('deepseek', []):
        entry['base_url'] = 'https://api.deepseek.com/v1'
        # Read actual key from .env
        with open(os.path.expanduser('~/.hermes/.env')) as envf:
            for line in envf:
                if line.startswith('DEEPSEEK_API_KEY='):
                    entry['api_key'] = line.split('=', 1)[1].strip()
    with open(path, 'w') as f:
        json.dump(auth, f, indent=2)
PYEOF
```

**Fix 2 — Export env var in wrapper (workaround, faster):**
```bash
#!/bin/sh
export DEEPSEEK_API_KEY="sk-your-key-here"
exec hermes -p profile-name "$@"
```
This makes the env var take precedence over `credential_pool`.

**Fix 3 — Restart gateway after fixing auth.json:**
```bash
pkill -f "hermes.*gateway"
hermes gateway run --replace &
```
The gateway caches credentials at startup. Fixing the file without restarting does nothing.

### Prevention
When creating a NEW Hermes profile wrapper script, **always** include `export DEEPSEEK_API_KEY=...` as the first line after `#!/bin/sh`. Do not rely on credential pool resolution for profile mode.

## After Fixing Config

Config changes to `model.default` and `providers.deepseek.base_url` require a **new session** (`/reset` or restart Hermes) to take effect. They are read once at session start for prompt caching reasons.

## Upgrading from deepseek-chat to deepseek-v4-pro (Apex-side)

When upgrading Apex (not Hermes) from `deepseek-chat` to `deepseek-v4-pro`:

1. **Model name confirmed via API**: `curl -s https://api.deepseek.com/v1/models -H "Authorization: Bearer $KEY"` returns `deepseek-v4-pro` and `deepseek-v4-flash`.

2. **6 source files and all profile YAMLs** need the model name changed. The files are: economy/__init__.py (6 ModelRoute entries + 1 default), core/profile.py, core/runtime.py, core/templates.py, providers/deepseek.py, cli/commands/init.py.

3. **Pricing must update alongside model name**: V4 Pro is $1/M input, $4/M output (vs V3's $0.5/M and $2/M). Quality scores should bump from 7→8 (default) and 8→9 (dev tasks).

4. **Profile YAMLs** in `~/.apex/profiles/*.yaml` must also be updated — `sed -i '' 's/deepseek-chat/deepseek-v4-pro/g' *.yaml`.

5. **base_url conflict**: If `.env` sets `DEEPSEEK_BASE_URL=https://api.deepseek.com/anthropic`, it overrides config.yaml's base_url. The `/anthropic` endpoint maps to different model classes. Remove the `.env` override to ensure V4 Pro routes correctly via the standard `/v1` endpoint.

6. **Hermes model upgrade**: `hermes config set model.default deepseek-v4-pro` — no restart needed, changes take effect on next API call.
