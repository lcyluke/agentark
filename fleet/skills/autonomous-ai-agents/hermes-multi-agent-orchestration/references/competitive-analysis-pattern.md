# Competitive Dashboard Analysis Pattern

## When to use
When the user wants to analyze competitor dashboards, frameworks, or tools to inform Apex's design direction. Triggers: "compare X with Y", "analyze competitor dashboards", "what can we learn from Z".

## Pattern: 3-Agent Parallel Delegate

```python
delegate_task(tasks=[
    {
        "goal": "Analyze from ARCHITECTURE dimension: tech stack, deployment, extensibility",
        "toolsets": ["web", "terminal"],
        "context": "Analyze these projects: [list]. Read GitHub READMEs and source structure. Output Chinese comparison tables with 10-pt scores."
    },
    {
        "goal": "Analyze from UI/UX dimension: visual design, navigation, components, interaction",
        "toolsets": ["web", "terminal"], 
        "context": "Analyze these projects: [list]. Look at screenshots, CSS, component libraries. Output Chinese comparison tables with scores."
    },
    {
        "goal": "Analyze from FEATURES dimension: agent management, task tracking, token, pipeline, skills",
        "toolsets": ["web", "terminal"],
        "context": "Analyze these projects: [list]. Compare against Apex Command Center features. Output gap analysis."
    },
])
```

## Why 3 Agents

1. **Architect**: Reads code structure, deployment configs, database schemas. Biased toward system design quality.
2. **Frontend-dev**: Reads CSS, HTML, component libraries, screenshots. Biased toward visual polish.
3. **Devops/PM**: Reads feature lists, API surfaces, workflows. Biased toward functional completeness.

Each agent's bias is a FEATURE — they notice different things. The synthesis of their reports is more balanced than a single agent doing everything.

## Process

1. GitHub API search → find candidate repos (web_search or curl)
2. For each repo: read README, check source structure, note star count
3. Each agent analyzes from their dimension
4. Merge results into a single comparison report
5. Output: ranking table + gap analysis + actionable recommendations

## Pitfalls

- GitHub API rate limits: stagger requests, use `per_page=5`
- Some repos have sparse READMEs: fall back to source structure analysis
- Agents may timeout on large repos: set `max_iterations` or break into smaller batches
- Vision API may not work (model-dependent): rely on text analysis of CSS/HTML instead
