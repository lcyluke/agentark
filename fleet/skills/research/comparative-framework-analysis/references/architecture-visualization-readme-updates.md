# Architecture Visualization & README Documentation

> Support file for the `comparative-framework-analysis` skill.
> Use when the analysis phase leads to: designing an SVG architecture diagram of your own system, updating README with the diagram, and adding a competitor comparison section.

## When This Applies

After completing a framework comparison (Phase 1-7 of the parent skill), when the user asks you to:
- "Design an architecture diagram for [our system]"
- "Update the README with the architecture"
- "Add a comparison to [competitor] in the docs"

This flows naturally from the comparison task: you analyzed competitors, now you need to visualize what you built and document how it differs.

## Step 1: Analyze the Competitor's Architecture

1. **Fetch their README** — `curl -sL https://raw.githubusercontent.com/org/repo/main/README.md`
2. **Find their architecture diagram** — look for `docs/images/asset.png` or similar
3. **Analyze their docs** — check `https://docs.project.com/` for `Production Architecture`, `Concepts`, or `llms.txt`
4. **Extract key facts**: layer structure, components, data flow, positioning statements
5. **Save the competitor's diagram locally** if needed for reference — `curl -sL <url> -o /tmp/diagram.png` then `vision_analyze`

## Step 2: Analyze Your Own Codebase

Use `delegate_task` with toolsets `["terminal","file"]` to analyze the full project:

- Goal: "Read and summarize the architecture of [project] to understand all modules and their relationships"
- Ask for: modules organized by layer, dependency graph, data flow from input to output, all modes/features

This saves you 50+ read_file calls.

## Step 3: Design the SVG Architecture Diagram

### SVG Design Rules

- **Dimensions**: 1200×1600-1800 wide canvas (fits full-width GitHub rendering)
- **Color scheme**: Dark theme (matching the project's banner style)
  - Background: `#0a0e27` (deep navy)
  - Layer boxes: semi-transparent colored borders per layer
  - Text: `#e2e8f0` headings, `#94a3b8` body, `#64748b` labels
  - Bright accent colors for important headings/boxes
- **Layers**: Stack vertically with clear separation
  - Each layer gets a distinct background gradient and colored border
  - Arrows between layers (`marker-end="url(#arrowDown)"`)
- **Component boxes** inside each layer:
  - `rect` with `rx="8"` rounded corners
  - Title, subtitle, and 2-4 lines of detail text
  - Small inner badges/pills for specific sub-components
- **Cross-cutting**: A horizontal bar at the bottom for cross-cutting concerns (e.g., Token Economy, Security)
- **Data flow**: A legend/path diagram at the very bottom showing forward path (top-down) and return path (bottom-up) with feedback loops
- **Filters**: Use `filter="url(#shadow)"` for depth on layer boxes
- **Avoid**: Gradients on text, overly complex arrows, nested structures that don't fit
- **Test rendering**: Check width — 1200px canvas fits most README layouts

### Example Layer Structure

```
L5 — INTERFACE        (CLI / Web Dashboard / REST API / MCP Protocol)
L4 — INTELLIGENCE     (Evolution Engine / Knowledge Graph / Memory System)
L3 — ORCHESTRATION    (10+ modes: Single, Swarm, Crew, Chain, Debate, ...)
L2 — AGENT RUNTIME    (Profile / Execution Engine / Self-Healing / Tools)
L1 — PROVIDER         (DeepSeek / Ollama / Claude / MCP Tools)
```

### SVG Architecture File Placement

Save to `docs/images/<project>-architecture.svg` — this is a project asset, not a session artifact.

## Step 4: Update the README

### What to add/replace in the Architecture section

```markdown
## 🏗️ Architecture

> **How [Competitor] does it:** [1-2 sentences about their paradigm]
>
> **[Your project] takes it further:** [1-2 sentences about what makes yours different]

### Work Logic Architecture Diagram

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)"
            srcset="https://raw.githubusercontent.com/org/repo/main/docs/images/your-architecture.svg">
    <img alt="Your Project Architecture"
         src="https://raw.githubusercontent.com/org/repo/main/docs/images/your-architecture.svg"
         width="100%">
  </picture>
</p>
```

### Add a Five-Layer Architecture Table

```markdown
| Layer | Name | Purpose | Key Components |
|-------|------|---------|---------------|
| **L5** | **Interface** | ... | CLI, Web Dashboard, REST API, MCP |
| **L4** | **Intelligence** | ... | Evolution, Knowledge Graph, Memory |
| ... | ... | ... | ... |
```

### Add a Data Flow Section

```markdown
### Data Flow: How It All Connects

[ASCII diagram showing forward path ↓ with return path ↑ and feedback loops]

**Forward path (top-down):**
1. ...
2. ...

**Return path (bottom-up):**
1. ...
2. ...

**Feedback loops:**
- Evolution Engine learns ...
- Knowledge Graph shares ...
```

### Add a Comparison Table

```markdown
### [Your Project] vs [Competitor]: Architecture Comparison

| Dimension | [Competitor] | [Your Project] |
|-----------|--------------|----------------|
| Paradigms | 1-2 modes | [number] modes |
| Agent Learning | None | [your feature] |
| Shared Memory | Per-crew context | [your feature] |
| ... | ... | ... |
```

## Step 5: Commit and Push

```bash
cd <project_dir>
git add docs/images/<svg> README.md
git commit -m "📐 Architecture diagram + README update

- Full SVG architecture diagram (docs/images/...)
- Updated README with diagram, layer table, data flow, comparison
- [Competitor] architecture analysis"
git push
```

## Pitfalls

1. **SVG too complex** — The diagram should be readable at 1200px width. Avoid tiny fonts (<9px) or too many nested boxes. If a layer has 10+ items, split into rows.
2. **Banner mismatch** — Check the existing banner gradient. Your SVG's color scheme should complement it (same palette).
3. **Competitor docs are unreliable** — CrewAI's asset.png renders as blank in browser; use vision_analyze or read their docs.crewai.com directly.
4. **Comparison tables get stale** — Frame the comparison dimension-level ("has self-learning? yes/no/partial") not version-specific ("v1.14 supports X"). The latter requires constant updates.
5. **README is complex** — Use `patch` to replace the architecture section rather than rewriting the whole file. But patch only if the old_string is unique — surrounding it with `\n---\n## 🏗️` markers helps.
6. **SVG rendering on GitHub** — GitHub renders SVGs inline. Test by pushing and viewing on the repo. `<picture>` elements work if you include both light/dark variants.
