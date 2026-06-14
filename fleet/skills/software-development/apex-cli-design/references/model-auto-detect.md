# Model Auto-Detection Architecture

## File: `apex/cli/commands/model_detect.py`

Scans the user's environment for available AI model providers without any API calls.

### Detection Pipeline

```
detect_models()
   ├── TOOL_CONFIGS scan (file existence check)
   │   ├── ~/.hermes → deepseek hint
   │   ├── ~/.kiro   → aws-bedrock hint
   │   ├── ~/.claude → anthropic hint
   │   └── ~/.cursor → openai hint
   │
   ├── MODEL_SIGNATURES scan (env var / config check)
   │   ├── deepseek    → DEEPSEEK_API_KEY
   │   ├── anthropic   → ANTHROPIC_API_KEY
   │   ├── openai      → OPENAI_API_KEY
   │   ├── openrouter  → OPENROUTER_API_KEY
   │   ├── google      → GOOGLE_API_KEY | GEMINI_API_KEY
   │   └── aws-bedrock → _check_aws_sso() — checks ~/.aws/config for sso_ + ~/.aws/sso/cache/*.json
   │
   └── Tool-hinted providers (fallback)
       └── If a tool exists but its provider wasn't detected via env var,
           register it with auth_method="via {tool}" anyway
```

### Provider Signatures

```python
MODEL_SIGNATURES = {
    "deepseek": {
        "env_vars": ["DEEPSEEK_API_KEY"],
        "models": ["deepseek-chat", "deepseek-v4-pro", "deepseek-r1"],
        "default": "deepseek-v4-pro",
        "base_url": "https://api.deepseek.com/v1",
    },
    "aws-bedrock": {
        "check_fn": "_check_aws_sso",
        "models": ["us.anthropic.claude-sonnet-4-6", "us.anthropic.claude-opus-4-7", "us.amazon.nova-pro-v2"],
        "default": "us.anthropic.claude-sonnet-4-6",
        "base_url": None,  # Uses boto3 SDK
    },
    # ... etc
}
```

### Priority Order (for auto-selection)

```python
PRIORITY_ORDER = ["deepseek", "aws-bedrock", "anthropic", "openai", "google", "openrouter"]
```

Rationale:
1. **deepseek** — cheapest ($1/1M input), already configured for Hermes
2. **aws-bedrock** — no API key needed (SSO), enterprise-friendly
3. **anthropic** — best code generation
4. **openai** — most widely supported
5. **google** — Gemini ecosystem
6. **openrouter** — multi-provider fallback

### Recommendation Logic

```python
def _recommend(available: dict, tools: list) -> str:
    if "deepseek" in available:
        return "deepseek-v4-pro (最便宜，$1/1M input)"
    if "aws-bedrock" in available:
        return "us.anthropic.claude-sonnet-4-6 (AWS Bedrock, SSO免key)"
    if "anthropic" in available:
        return "claude-sonnet-4 (最强代码能力)"
    if "openrouter" in available:
        return "deepseek/deepseek-chat (OpenRouter, 免多key)"
    return "需要配置至少一个model provider"
```

## Integration: `apex setup` Step 3

`setup_cmds.py` imports `detect_models()` and `_pick_best_provider()`:

```python
# Detect
from apex.cli.commands.model_detect import detect_models
detected = detect_models()
providers = detected.get("providers", {})

# Pick best
if providers:
    best = _pick_best_provider(providers)
    model_cfg = best["model"]     # e.g. "deepseek-v4-pro"
    # No user prompts needed

# Fallback: only prompt if nothing detected
if not quick and not providers:
    model_cfg = Prompt.ask("Default model", default="deepseek-v4-pro")
```

Then `_configure_model(model_cfg, token_lim, token_bgt)` writes to all Hermes profile `config.yaml` files.

## Standalone CLI

```
$ apex model-detect
🔍 Model Auto-Discovery — Found 4 providers

📦 Detected AI Tools
┌──────────┬─────────────┬──────────────────┐
│ Tool     │ Model Hint  │ Path             │
├──────────┼─────────────┼──────────────────┤
│ kiro     │ aws-bedrock │ /Users/.../.kiro │
│ hermes   │ deepseek    │ /Users/.../.hermes│
└──────────┴─────────────┴──────────────────┘

🤖 Available Models
┌────────────┬──────────────────────┬─────────────┐
│ Provider   │ Models               │ Auth        │
├────────────┼──────────────────────┼─────────────┤
│ deepseek   │ deepseek-chat,       │ via hermes  │
│            │ deepseek-v4-pro, ... │             │
│ aws-bedrock│ claude-sonnet-4-6,   │ sso/cache   │
│            │ nova-pro-v2          │             │
└────────────┴──────────────────────┴─────────────┘

→ Recommended: deepseek-v4-pro (最便宜，$1/1M input)
To auto-configure: apex model-detect --apply <provider>
```

## Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| `_pick_best_provider` imports `detect_models` in step 3 | Circular import in setup context | Import inside the try block, not at module top |
| AWS SSO cache expired | `aws-bedrock` not detected | Token refresh happens outside; detection only checks file existence |
| No providers found + --quick | Falls through to hardcoded `deepseek-v4-pro` | Acceptable default; user can run `apex model-detect` later to verify |
| MallocStackLogging noise in detection subprocess | Stderr pollution | Apply triple-layer fix before running detection |