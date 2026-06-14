# Apex — 5 Agent Template Details

> Pre-built expert agents — `apex template list`

| Template | Icon | Role | Expertise | Skill Packages | Tools |
|----------|:----:|------|-----------|----------------|-------|
| frontend | 💻 | Frontend Developer | React, Vue, WeChat Mini Program, TypeScript, Tailwind, Next.js, Figma | component-building, responsive-design, state-management | filesystem, github, terminal, browser |
| backend | ⚙️ | Backend Architect | FastAPI, Go, PostgreSQL, Redis, Docker, K8s, Kafka, gRPC | system-design, api-design, database-schema, security | filesystem, github, terminal, docker |
| pm | 📋 | Product Manager | PRD, User Stories, A/B Testing, OKRs, Roadmap, MVP | prd-writing, user-research, data-analysis | filesystem, browser |
| content | ✍️ | Content Strategist | Copywriting, SEO, WeChat/Twitter, Localization | copywriting, seo-optimization, social-media | filesystem, browser |
| devops | 🔧 | DevOps Engineer | Docker, K8s, Terraform, CI/CD, Prometheus, AWS | ci-cd, infrastructure-as-code, monitoring | filesystem, github, terminal |

## Usage

```bash
apex template use frontend -a my-frontend
apex run "Build a login page" --profile my-frontend
```

## Creating Custom Templates

Edit apex/core/templates.py and add AgentTemplate(...) then register() it.
