# Creating a New Apex Hermes Agent Profile

This document captures the repeatable workflow for creating a new agent profile from scratch, as done for `vulnerability-scanner` and `penetration-tester`.

## Prerequisites

- Apex project lives at `~/Desktop/2026AIAPP/Apex`
- Skill Registry at `~/.apex/skill-registry.yaml`
- Hermes profiles at `~/.hermes/profiles/`
- Wrapper scripts at `~/.local/bin/`

## Step-by-Step Workflow

### 1. Create Hermes Profile Directory

```bash
mkdir -p ~/.hermes/profiles/<agent-name>
```

### 2. Write config.yaml

**Must use nested model.default format:**

```yaml
model:
  default: deepseek-v4-pro
  provider: deepseek
agent:
  max_turns: 100
kanban:
  skills_policy: inherit
```

Pitfall: Do NOT use flat format — `model: deepseek-v4-pro` at top level causes provider-resolution failure. Hermes expects `model.default`.

### 3. Write SOUL.md

Template structure:
- `# <emoji> <Role Name>` heading
- `## 身份` — role definition
- Core responsibilities (Chinese)
- Expertise areas
- Personality style
- Communication format
- Skill list (8-16 skills, matching what will go in registry)
- Toolchain reference
- Red Flags table (7-10 rows — anti-rationalization traps)
- The Iron Laws (4 immutable rules)

Include the SUPERPOWERS-BOOTSTRAP block right after ## 身份:
```markdown
<!-- SUPERPOWERS-BOOTSTRAP -->
<EXTREMELY-IMPORTANT>
You have superpowers for [domain]. Before ANY action — [relevant actions] — check if a skill applies.
**If there is even a 1% chance a skill might apply, you MUST invoke it.**
</EXTREMELY-IMPORTANT>
```

### 4. Create Wrapper Script

```bash
DKEY=$(grep ^DEEPSEEK_API_KEY ~/.hermes/.env | cut -d= -f2)
cat > ~/.local/bin/<agent-name> << 'WRAPPER'
#!/bin/sh
export DEEPSEEK_API_KEY="DKEY"
exec hermes -p <agent-name> "$@"
WRAPPER
chmod 755 ~/.local/bin/<agent-name>
```

**Always export `DEEPSEEK_API_KEY`** — profile mode reads from `credential_pool` in `auth.json` which can have stale data. The env var takes precedence.

### 5. Register Skills in Skill Registry

For each skill, define L0-L5 levels with Chinese descriptions:

```python
from apex.interface.skill_registry import get_registry, LEVELS
r = get_registry()
now = __import__('time').strftime('%Y-%m-%d')

skills = {
    'skill-name': ('category', 'English description'),
    # ...
}

for sname, (cat, desc) in skills.items():
    if sname not in r._data.get('skills', {}):
        levels = {lvl: {'description': '', 'examples': []} for lvl in LEVELS}
        levels['L0'] = {'description': f'不了解 {sname}', 'examples': []}
        levels['L1'] = {'description': '了解概念但无法独立执行', 'examples': []}
        levels['L2'] = {'description': '能独立执行标准扫描流程', 'examples': []}
        levels['L3'] = {'description': '精通，能自定义规则和策略', 'examples': []}
        levels['L4'] = {'description': '能设计安全扫描架构', 'examples': []}
        levels['L5'] = {'description': '能创建工具/框架', 'examples': []}
        r._data.setdefault('skills', {})[sname] = {
            'name': sname.replace('-', ' ').title(),
            'category': cat, 'description': desc, 'levels': levels,
        }
    r._data.setdefault('agents', {}).setdefault(
        '<agent-name>', {'agent_name': '<agent-name>', 'skills': {}}
    )['skills'][sname] = {
        'level': 'L2', 'confidence': 0.7,
        'assessed_by': 'origin', 'assessed_at': now,
        'evidence': [{'type': 'initialization', 'ref': 'agent-creation',
                      'description': f'Initial baseline: {sname}', 'date': now}],
    }

r.save()
```

### 6. Generate SKILL.md

```bash
PYTHONPATH=/Users/Mac/Desktop/2026AIAPP/Apex python3 -c "
from apex.interface.skill_registry import get_registry, sync_skill_md
r = get_registry()
sync_skill_md('<agent-name>', registry=r)
"
```

### 7. Register in Dev Squad (if applicable)

Add to `DEV_SQUAD` dict in `apex/cli/commands/squad_cmds.py`:
```python
"<agent-name>": {
    "emoji": "<emoji>",
    "title": "<Display Title>",
    "skill": "<brief skill summary>",
    "color": "<color>",
},
```

And add to `click.Choice` list in `apex/cli/main.py` for `squad attach`.

### 8. Verify

```bash
<agent-name> chat -q "回复两个字：就绪"
```

Expected output: agent responds "就绪".
