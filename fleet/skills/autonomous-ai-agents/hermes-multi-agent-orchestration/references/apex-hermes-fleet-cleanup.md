# Apex-Hermes Fleet Cleanup & Integration Pattern

> **Updated:** 2026-06-04  
> **Context:** Consolidated 37 Apex YAML + 27 Hermes Profiles → 27 + 33 unified fleet

## Fleet State After Cleanup

```
Apex YAML agents: 27 (down from 37)
Hermes Profiles:  33 (up from 27, all deepseek-v4-pro)
Dual-registered:  27 (Apex+Hermes both have them)
Hermes-only:      6  (apex-pm, badminton-pm, project-manager, requirements-analyst, fullstack-dev, audit-guardian)
```

## Cleanup Workflow

### Phase 1: Audit
Run full inventory of both systems:
```bash
# Apex agents
ls ~/.apex/profiles/*.yaml | wc -l

# Hermes profiles
hermes profile list | grep -c 'deepseek'

# Find overlaps
for f in ~/.apex/profiles/*.yaml; do
  name=$(basename $f .yaml)
  hermes profile list 2>/dev/null | grep -q "$name" && echo "DUAL: $name" || echo "APEX-ONLY: $name"
done
```

### Phase 2: Classify
Four categories:
- 🟢 **KEEP**: Core operational agents
- 🟡 **TEMPLATE**: Project template agents (keep as examples, no Hermes profile needed)
- 🟠 **LEGACY**: Used by existing pipelines (chain.py → writer/editor/publisher)
- 🔴 **DELETE**: Test/one-shot agents (test_pm*, test-company_*, proj_*)

### Phase 3: Delete Test Agents
```bash
cd ~/.apex/profiles
rm test_pm.yaml test_pm2.yaml test_pm_x.yaml
rm test-company_*.yaml proj_backend.yaml proj_frontend.yaml
```
Also remove references from `project_ops.py` AGENT_SKILLS dict.

### Phase 4: Create Hermes Profiles for Apex-Only Agents
For each Apex agent that needs execution capability:
```bash
hermes profile create <name>
# Then write SOUL.md + config.yaml + .env
```
Pattern: all monitoring agents use the same config template with deepseek-v4-pro.

### Phase 5: Model Unification
```bash
# Find old-model profiles
for d in ~/.hermes/profiles/*/; do
  name=$(basename $d)
  grep -q 'deepseek-chat' "$d/config.yaml" 2>/dev/null && echo "$name"
done

# Upgrade each
patch(path=f"{base}/{name}/config.yaml",
      old_string="default: deepseek-chat",
      new_string="default: deepseek-v4-pro")
```

### Phase 6: Update Skill Registry
Update `project_ops.py` AGENT_SKILLS to include all 33 agents, organized by category (开发/AI/PM/安全/内容/质量/舰队管理).

## Result: One Person = One Company

```
          ⚓ Origin (fleet commander)
     ┌────────┼────────┐
     │        │        │
  🧭 监控层   📋 PM层   🔧 执行层
  6 Agent    5 Agent   22 Agent
  24x7值守   分项目管理  按需唤醒
```

Apex open-source independent (27 YAML agents self-contained).
Install + Hermes → 33 profiles auto-discovered via bridge_sync.

## Pitfalls

1. **project_ops.py has hardcoded AGENT_SKILLS** — after deleting agents, must remove their entries.
2. **Chain.py references writer/editor/copywriter/publisher** — don't delete these even if they seem unused.
3. **Hermes-only profiles need full config** — SOUL.md + config.yaml + .env, not just the profile creation.
4. **Model upgrade requires checking all profiles** — some were missed in previous upgrade passes.
