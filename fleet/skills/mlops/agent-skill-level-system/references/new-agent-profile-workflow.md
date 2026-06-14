# Agent Profile Creation — 6-Step Workflow

Refined through 6 agent creations in June 2026. Follow exactly.

## Step 1: SOUL.md

Path: `~/.hermes/profiles/<name>/SOUL.md`

Mandatory structure (in order):
```
# Emoji Role-Name

## 身份
你是谁

<!-- SUPERPOWERS-BOOTSTRAP -->
<EXTREMELY-IMPORTANT>
...1% rule + skill list...
</EXTREMELY-IMPORTANT>

## 核心职责 — 4-6 bullets
## 专业领域 — 8-10 bullets
## 个性风格 — 2-3 traits
## 沟通方式 — 1 line describing output format
## 技能列表 — 8 skill names matching registry
## Red Flags — table, 6-10 rows (Cognitive Trap | Remedy)
## The Iron Laws — 4 rules

--- footer sync line ---
```

The `<!-- SUPERPOWERS-BOOTSTRAP -->` comment marker is required — verification tools look for this exact string.

## Step 2: config.yaml

MUST use nested `model.default` structure:
```yaml
model:
  default: deepseek-v4-pro
  provider: deepseek
agent:
  max_turns: 100
kanban:
  skills_policy: inherit
```

**Pitfall:** Subagents often write flat structure (`model: deepseek-v4-pro` on one line). This causes provider-resolution errors. Always verify after creation.

## Step 3: Wrapper Script

```bash
cat > ~/.local/bin/<name> << 'EOF'
#!/bin/sh
export DEEPSEEK_API_KEY="sk-3a608f574c714ac4a15da2b385f25454"
exec hermes -p <name> "$@"
EOF
chmod 755 ~/.local/bin/<name>
```

**CRITICAL:** Exporting `DEEPSEEK_API_KEY` is REQUIRED. Without it, Hermes profile mode reads from `auth.json` credential_pool which may have:
- Stale `base_url` (`https://api.deepseek.com/anthropic` instead of `https://api.deepseek.com/v1`)
- Empty credential pools
- Expired cached keys

## Step 4: Skill Registry Registration

```bash
cd /Users/Mac/Desktop/2026AIAPP/Apex
PYTHONPATH=. python3 -c "
from apex.interface.skill_registry import get_registry, LEVELS
r = get_registry()
now = __import__('time').strftime('%Y-%m-%d')

# Define 8 skills for this agent
skills = {
    'skill-name': ('category', 'Description'),
}

for sname, (cat, desc) in skills.items():
    if sname not in r._data.get('skills', {}):
        levels = {lvl: {'description': '', 'examples': []} for lvl in LEVELS}
        levels['L0'] = {'description': '不了解', 'examples': []}
        levels['L1'] = {'description': '了解概念但无法独立执行', 'examples': []}
        levels['L2'] = {'description': '能独立执行标准流程', 'examples': []}
        levels['L3'] = {'description': '精通，能指导', 'examples': []}
        levels['L4'] = {'description': '能设计架构', 'examples': []}
        levels['L5'] = {'description': '能创建方法论', 'examples': []}
        r._data.setdefault('skills', {})[sname] = {
            'name': sname.replace('-',' ').title(),
            'category': cat,
            'description': desc,
            'levels': levels,
        }
    r._data.setdefault('agents', {}).setdefault('agent-name', {
        'agent_name': 'agent-name', 'skills': {}
    })['skills'][sname] = {
        'level': 'L2',
        'confidence': 0.7,
        'assessed_by': 'origin',
        'assessed_at': now,
        'evidence': [{'type': 'initialization', 'ref': 'creation', 'description': f'Baseline: {sname}', 'date': now}],
    }
r.save()
print('registered')
"

# Generate SKILL.md
PYTHONPATH=. python3 -c "
from apex.interface.skill_registry import sync_skill_md
print(sync_skill_md('agent-name'))
"
```

## Step 5: Register in `apex squad`

1. Add entry to `DEV_SQUAD` dict in `apex/cli/commands/squad_cmds.py`:
   ```python
   "agent-name": {
       "emoji": "🔐",
       "title": "Role Title",
       "skill": "Short/Skill/List",
       "color": "bright_red",
   },
   ```
2. Update squad count string: `11 Agents` → `12 Agents`
3. Add to `click.Choice` list in `apex/cli/main.py` for the `squad attach` command

## Step 6: Verify

```bash
# File checks
ls ~/.hermes/profiles/<name>/SOUL.md
ls ~/.hermes/profiles/<name>/config.yaml
ls ~/.local/bin/<name> && ls -la ~/.local/bin/<name>

# Live test
<name> chat -q "回复两个字：就绪"
```

## Pitfalls Seen

1. **config.yaml structure** — subagents write flat format. Always verify after delegate_task completes.
2. **Wrapper auth** — no env var export = 401. Always include `DEEPSEEK_API_KEY` export.
3. **Squad registration** — easy to forget to update the squad count string and the click.Choice list simultaneously.
4. **SKILL.md generation** — run `sync_skill_md()` after registry registration, not before.
5. **SOUL.md encoding** — use Chinese + English bilingual. Chinese for identity/duties, English for technical concepts.
