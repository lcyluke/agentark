# Contributing to Apex

We love contributions! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/luke/apex.git
cd apex
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[dev,web]"
```

## Code Style

- Follow PEP 8
- Use type hints
- Keep functions under 50 lines
- Docstrings for all public APIs

## Testing

```bash
# Run import tests
python -c "from apex.core.runtime import Agent; print('OK')"

# Run full test suite
pytest
```

## Pull Request Process

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a PR with clear description

## Architecture

```
apex/
├── core/           # Agent runtime, profile, memory, skills
├── providers/      # LLM providers (DeepSeek, Ollama, etc.)
├── orchestration/  # Swarm, Crew, Kanban, Healing
├── economy/        # Token economy, budget management
├── mcp/            # MCP Hub (tools integration)
├── cli/            # Click CLI commands
└── interface/      # Web UI (Flask)
```

## License

MIT
