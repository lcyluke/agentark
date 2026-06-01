# Contributing to Apex

Thank you for your interest in contributing to **Apex** — the multi-agent operating system. This document provides guidelines and instructions for contributing.

## Table of Contents

- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Architecture Overview](#architecture-overview)
- [Commit Message Conventions](#commit-message-conventions)

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- (Optional) Docker for containerized development

### Clone and Install

```bash
git clone https://github.com/lcyluke/Apex.git
cd Apex
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Install Pre-commit Hooks

```bash
pre-commit install
```

This ensures code style and linting checks are run automatically before each commit.

## Code Style

We use **Ruff** for linting and formatting. The configuration is defined in `pyproject.toml`. Key rules:

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions
- Use type hints for all public APIs
- Write docstrings in Google style (or NumPy style, consistent with the module)
- Maximum line length: 100 characters
- Run `ruff check .` and `ruff format .` before committing

## Testing

We use **pytest** for testing. All tests live in the `tests/` directory.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apex --cov-report=term-missing

# Run specific test file
pytest tests/test_core.py

# Run tests matching a keyword
pytest -k "agent"
```

Pull requests must maintain or improve test coverage. New features should include tests.

## Pull Request Process

1. **Fork the repository** and create a feature branch from `main`.
2. **Make your changes** following the code style guidelines.
3. **Run tests** to ensure nothing is broken.
4. **Run the linter** (`ruff check . && ruff format --check .`).
5. **Update documentation** if your changes affect public APIs or behavior.
6. **Open a pull request** against the `main` branch using the PR template.
7. A maintainer will review your PR. Address any feedback promptly.

## Architecture Overview

Apex is a multi-agent operating system with the following high-level architecture:

- **Core (`apex/core/`)** — Fundamental abstractions: Agent, Task, Message, orchestration primitives
- **Agents (`apex/agents/`)** — Built-in agent implementations (e.g., Hermes Agent, specialized roles)
- **Tools (`apex/tools/`)** — Tool definitions and execution framework
- **Runtime (`apex/runtime/`)** — Execution environment, sandboxing, resource management
- **CLI (`apex/cli/`)** — Command-line interface for interacting with Apex
- **API (`apex/api/`)** — REST/gRPC API for programmatic access
- **Tests (`tests/`)** — Test suite mirroring the `apex/` structure

The system follows a modular plugin architecture. New agents, tools, and runtimes can be added by implementing the appropriate base classes.

## Commit Message Conventions

We follow **Conventional Commits** for all commit messages. This enables automatic changelog generation and semantic versioning.

### Format

```
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

### Types

| Type       | Description                                 |
|------------|---------------------------------------------|
| `feat`     | A new feature                               |
| `fix`      | A bug fix                                   |
| `docs`     | Documentation only changes                  |
| `refactor` | Code restructuring without feature/bug fix  |
| `test`     | Adding or updating tests                    |
| `ci`       | Changes to CI configuration and scripts     |
| `chore`    | Maintenance, dependency updates, etc.       |

### Examples

```
feat(agents): add tool-calling loop to Hermes Agent
fix(runtime): handle connection timeout in sandbox
docs(api): update endpoint documentation for v2
test(core): add unit tests for Task scheduler
ci: switch from flake8 to ruff in CI pipeline
```

### Scope

The scope is optional but recommended. It should refer to the module or component being changed (e.g., `agents`, `runtime`, `core`, `cli`, `api`, `tools`).

---

Thank you for contributing to Apex! 🚀
