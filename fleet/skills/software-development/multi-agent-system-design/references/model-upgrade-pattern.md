# Model Upgrade Pattern — Across Apex + Hermes

When a new LLM model version replaces the current default, the upgrade touches these locations:

## Apex Source Files (6+ files)

```bash
grep -rl 'old-model-name' apex/ --include='*.py' | grep -v __pycache__
```

Typical files:
- `apex/economy/__init__.py` — 6+ ModelRoute entries + comments
- `apex/core/profile.py` — default model string
- `apex/core/runtime.py` — provider matching comment
- `apex/core/templates.py` — template default models
- `apex/providers/deepseek.py` — actual model name in API calls + pricing comment
- `apex/cli/commands/init.py` — default model in config + display strings

## Profile YAMLs (17+ files)

```bash
cd ~/.apex/profiles
for f in $(grep -rl 'old-model' *.yaml); do sed -i '' 's/old-model/new-model/g' "$f"; done
```

## Economy Pricing

V4 Pro pricing is double V3: $1/M input, $4/M output (vs $0.5/$2).

## Hermes Config

```bash
hermes config set model.default new-model-name
# Verify: grep "default:" ~/.hermes/config.yaml
```

Check for conflicting `base_url` or `.env` overrides that send traffic to a wrong endpoint:

```bash
grep -i "base_url\|BASE_URL" ~/.hermes/.env ~/.hermes/config.yaml
```

## Verification

```bash
grep -rn 'old-model-name' apex/ --include='*.py' --include='*.yaml' | grep -v __pycache__ || echo "✅ No old model name remaining"
apex run "What model are you using?" | grep -i "model"
```
