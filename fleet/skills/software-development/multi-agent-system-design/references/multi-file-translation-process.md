# Multi-File Translation Process

## Context
Apex codebase was initially written in Chinese (all user-facing strings, docstrings, comments, prompts). One session translated ALL 28 files to English.

## Strategy

### Step 1: Discovery
```bash
grep -rn '[\x{4e00}-\x{9fff}]' apex/ --include="*.py" --include="*.md" --include="*.html" 2>/dev/null
```
Find ALL Chinese characters. Collect the file list.

### Step 2: Parallel Dispatch via delegate_task
Split into 3 batches of ~9-12 files each. Max 3 parallel children.

- **Batch 1**: CLI files (click help strings, console.print messages, Panel titles, Prompt.ask defaults, docstrings)
- **Batch 2**: Core files (templates, runtime, profile, memory, skills, knowledge, evolution)
- **Batch 3**: Remaining (orchestration, economy, mcp, providers, interface, dashboard.html)

### Step 3: Subagent Instructions
Each subagent receives:
1. The list of files to translate
2. The rule: "Translate ALL Chinese string literals to English. Keep ALL code logic, variable names, function names, class names, imports, SQL queries, data structures IDENTICAL. Only translate string literals."
3. Write each file back via write_file

### Step 4: What to Translate per File Type

**Python CLI files (.py in cli/commands/)**
- `click.option(help=...)` strings
- `console.print()` user-facing messages
- Docstrings (module, class, function)
- `Panel(title=...)` and `Table(title=...)` strings
- `Prompt.ask()` default values
- Error messages (console.print(f"[red]..."))
- column names in Table.add_column()

**Python core files (.py in core/)**
- Docstrings
- Comments
- Default personality/communication values
- Expertise lists
- System prompt templates ("You are...", "Your expertise...", "Personality: ...")
- Skill names (e.g. "react-component-building")
- KnowledgeGraph entity types ("technology", "concept", "rule")
- Evolution pattern names ("error:api_key_missing", "success:code_review_approved")
- Relation types ("supports", "replaces", "recommends", "dangerous")

**Orchestration files**
- Crew DynamicTeamDesigner keywords ("Deploy to Production", "Content Creation")
- Swarm console output strings
- Healing diagnostic prompts
- Kanban AI suggestion strings
- Chain pipeline factory descriptions

**Economy files**
- ModelRoute descriptions
- TASK_TYPE_KEYWORDS values
- Budget account strings
- Report output strings

**MCP/Provider files**
- Tool descriptions
- Parameter descriptions
- Comments

**HTML files**
- `lang` attribute: `zh-CN` → `en`
- Agent icon role matching (Chinese → English)
- Locale strings

### Step 5: Verification
```bash
# Check for remaining Chinese
grep -rn '[\x{4e00}-\x{9fff}]' apex/ --include="*.py" 2>/dev/null

# Syntax check
python3 -c "
import py_compile, os
errors = []
for root, dirs, files in os.walk('apex'):
    if '.venv' in root or '__pycache__' in root: continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(str(e))
if errors:
    for e in errors: print(f'❌ {e}')
else:
    print('✅ All Python files compile OK')
"
```

### Key Pitfalls

1. **Code logic must NOT change.** Only string literals. If a variable is named `通用助手`, rename to `general_assistant` — but if it's used as a key, keep it as-is.
2. **Dashboard.html has special treatment.** Change `lang="zh-CN"` to `lang="en"`, replace Chinese role names with English in the getIcon() JS function.
3. **Confidence-based translation for KG.** Knowledge graph translations should preserve the entity type system (technology/concept/rule) that the code depends on.
4. **Relations must keep their enum semantics.** "不支持" → "conflicts_with", not just "does_not_support". The relation types are used by the conflict detection logic.

### Output
- 28 files translated
- All Chinese → English
- Zero Chinese characters remaining in source
- All Python files pass compile check
