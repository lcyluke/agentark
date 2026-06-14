# Model Auto-Discovery

`apex/interface/model_detect.py` and CLI hook in `apex/cli/commands/model_detect.py`.

## Purpose

Auto-detect available LLM models from the environment without manual configuration.
Runs at `apex demo` startup and can be invoked standalone.

## Detection Sources

| Source | Method | Example |
|--------|--------|---------|
| Environment variables | Check for `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc. | `os.environ.get("DEEPSEEK_API_KEY")` |
| AWS SSO | Read `~/.aws/config` for `sso_*` fields + check `~/.aws/sso/cache/` | kiro/Cursor use this |
| Tool configs | Check for kiro (`.kiro/`), claude-code (`.claude/`), cursor (`.cursor/`), hermes (`.hermes/`) directories | Cross-tool model reuse |

## Detected Providers

| Provider | Auth | Models |
|----------|------|--------|
| deepseek | DEEPSEEK_API_KEY | chat, v4-pro, r1 |
| anthropic | ANTHROPIC_API_KEY | sonnet-4, opus-4-7 |
| aws-bedrock | AWS SSO | claude-sonnet-4-6, claude-opus-4-7, nova-pro-v2 |
| openai | OPENAI_API_KEY | gpt-4o, gpt-4o-mini |
| openrouter | OPENROUTER_API_KEY | deepseek, claude, gpt variants |

## Usage

```bash
apex model detect                    # Show available models
apex model detect --auto-configure   # Auto-select best model and configure
```

## Architecture Note

Apex runs standalone. Hermes integration is OPTIONAL — enables real-time session tracking and token analytics but is not required for core functionality (Profile management, Kanban, project approval, Dashboard). All Hermes-dependent APIs gracefully return zeros when Hermes is not installed.
