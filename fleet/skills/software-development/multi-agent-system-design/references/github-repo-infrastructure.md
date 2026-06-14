# GitHub Open-Source Repo Infrastructure Setup

Built for the Apex project (session 2026-06-02). Reusable for any Python open-source project.

## File Inventory (13 files)

| File | Purpose |
|------|---------|
| `.github/ISSUE_TEMPLATE/bug_report.md` | Structured bug report: description, steps, expected/actual, environment, logs |
| `.github/ISSUE_TEMPLATE/feature_request.md` | Feature request: problem, solution, alternatives, use case |
| `.github/ISSUE_TEMPLATE/config.yml` | Disable blank issues, link Discord + Discussions |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR description, type of change (feat/fix/docs/refactor/test), how tested, checklist |
| `.github/CODEOWNERS` | Default owner: `* @lcyluke` |
| `.github/FUNDING.yml` | GitHub Sponsors: `github: user` |
| `.github/dependabot.yml` | Weekly pip dependency updates, labels, reviewer |
| `.github/workflows/ci.yml` | Matrix: Python 3.10/3.11/3.12, ruff, pytest with coverage, coverage badge in summary |
| `.github/workflows/release.yml` | Trigger: tag push v*, build with hatchling, create GitHub Release, publish to PyPI |
| `SECURITY.md` | Vulnerability reporting, supported versions, disclosure timeline |
| `CODE_OF_CONDUCT.md` | Contributor Covenant v2.1 |
| `.pre-commit-config.yaml` | trailing-whitespace, end-of-file-fixer, check-yaml, check-json, ruff, ruff-format, mixed-line-ending |
| `.editorconfig` | root=true, indent_style=space, indent_size=4, end_of_line=lf, charset=utf-8 |

## Testing Infrastructure (8 files, 42 tests)

| File | Tests | Coverage |
|------|-------|----------|
| `conftest.py` | 5 fixtures | tmp_path APEX_HOME, sample profiles, kanban, KG, mock LLM responses |
| `test_profile.py` | 10 | create, save/load, dict roundtrip, from_dict, from_template, list, delete, nonexistent error |
| `test_orchestration_kanban.py` | 7 | CRUD, status updates, dependency chains, ready tasks, AI suggestions |
| `test_orchestration_swarm.py` | 2 | init, dataclass defaults |
| `test_orchestration_healing.py` | 2 | init, result defaults |
| `test_economy.py` | 11 | classify_task (6 task types), select_model (3 scenarios), budget manager lifecycle, warnings |
| `test_knowledge.py` | 6 | learn, relate, query with/without results, stats, learn_from_experience |
| `test_mcp.py` | 4 | hub init (4 tools), list_tools, filesystem error, knowledge query |

## CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
- matrix: [python-version: ["3.10", "3.11", "3.12"]]
- steps: checkout → setup python → install uv → uv venv → uv pip install .[web] + pytest + pytest-cov
  → ruff check → pytest --cov=apex --cov-report=term-missing
  → coverage badge in step-summary
```

## pyproject.toml Additions

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.coverage.run]
source = ["apex"]

[tool.coverage.report]
exclude_lines = ["pragma: no cover", "def __repr__", "raise AssertionError", "if __name__ == .__main__.:"]
```

## Key Patterns

- **Issue templates**: YAML frontmatter with `name`, `about`, `title`, `labels`, `assignees`
- **PR template**: checklist for testing, linting, docs — convert to Markdown checkboxes `- [ ]`
- **CI matrix**: Python 3.10 as minimum (not 3.9), 3.12 as maximum
- **Coverage**: `--cov-report=term-missing` shows uncovered lines in CI output
- **Release workflow**: only triggers on `v*` tag push, uses hatchling for build, twine for PyPI upload
- **Dependabot**: `package-ecosystem: "pip"`, `schedule: "weekly"`, `open-pull-requests-limit: 10`
- **Pre-commit**: `repo: https://github.com/astral-sh/ruff-pre-commit` with `--fix` for auto-formatting
- **EditorConfig**: 4-space indent for Python, 2-space for YAML via `[*.yml]` override
