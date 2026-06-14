# Commercial Product Directory — Built-in Categories

Used by `apex survey` to provide offline product lookups without API keys.
When extending, add entries to `_get_product_directory()` in `apex/cli/commands/survey_cmds.py`.

## Coverage Rules

Each category needs:
- At least 3 products (enough for comparison)
- Maximum 5 products (keeps output readable)
- Known, verifiable products (not hypothetical)
- At minimum: name, url, description, pricing, features

## Adding a New Category

```python
if any(kw in topic_lower for kw in ["your topic keywords"]):
    return [
        {"name": "Product A", "url": "https://...",
         "description": "One-liner", "pricing": "Free + $X/mo",
         "features": ["Feature 1", "Feature 2", "Feature 3"],
         "stars": 5000},  # GitHub stars if OSS, 0 if closed-source
        ...
    ]
```

Keyword matching uses `any(kw in topic_lower ...)` — add enough keywords to catch variations.

## Existing Categories

| Category | Keywords | Products |
|----------|----------|----------|
| AI FinOps | finops, cloud cost, cloud finance, aws cost, azure cost, gcp cost, multi-cloud | CloudHealth, Vantage, Kubecost, Infracost, Cast AI |
| AI/LLM Agents | ai agent, llm, langchain, ai framework, agent framework, multi-agent | LangChain, CrewAI, AutoGen, OpenAI Assistants, Claude MCP |
| IDE/Dev Tools | ide, code editor, dev tool, developer tool | Cursor, Copilot, Windsurf |
| Project Management | project management, pm tool, task management, sprint, kanban | Linear, Notion, Asana |
| Data/Analytics | analytics, data platform, bi tool, dashboard | Metabase, Grafana, Tableau |

## GitHub API Rate Limiting

The GitHub search uses public API (no auth token) which has strict rate limits:

- **Unauthenticated**: 60 requests/hour
- **Authenticated** (via `Authorization` header): 5,000 requests/hour

The code handles `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers.

If on a commercial project or heavy usage, add a `GITHUB_TOKEN` env var:

```python
def _github_request(endpoint):
    headers = {"Accept": "application/vnd.github.v3+json",
               "User-Agent": "Apex-Survey/1.0"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    ...
```
