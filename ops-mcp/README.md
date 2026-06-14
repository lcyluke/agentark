# APEX Ops MCP Server

MCP (Model Context Protocol) server for APEX orchestration operations.
Provides 6 tools for managing APEX agent sessions, querying the shared
blackboard and claims registry, and running health checks.

## Tools

| Tool             | Description                                      |
|------------------|--------------------------------------------------|
| `apex_spawn`     | Spawn a new agent session with a task            |
| `apex_status`    | Query session status or list all sessions        |
| `apex_blackboard`| Search the shared cross-agent knowledge board    |
| `apex_claims`    | List active claims in the claims registry        |
| `apex_stop`      | Stop (dispose) a running agent session           |
| `apex_doctor`    | Run health checks on APEX infrastructure         |

## Architecture

```
┌──────────────┐     JSON-line      ┌──────────────┐
│  MCP Client  │◄────stdio────►│ apex-ops-mcp │
│ (Claude etc) │                    │  (this pkg)   │
└──────────────┘                    └──────┬───────┘
                                          │
                          ┌───────────────┼───────────────┐
                          │ Unix socket   │ SQLite (ro)   │
                          ▼               ▼               │
                   ┌──────────┐  ┌──────────────┐        │
                   │  apexd   │  │ agentops.db  │        │
                   │ (daemon) │  │ (blackboard  │        │
                   └──────────┘  │  + claims)   │        │
                                 └──────────────┘        │
```

- **Socket**: `~/.apex/apexd.sock` → `~/.apex/agentops.sock` → `127.0.0.1:8717`
- **DB**: `~/.apex/agentops.db` (read-only access for blackboard + claims)

## Prerequisites

- Node.js >= 18
- APEX daemon (`apexd`) running for spawn/status/stop operations
- SQLite database at `~/.apex/agentops.db` for blackboard/claims queries

## Installation

```bash
cd ops-mcp
npm install
npm run build
```

## Usage

### As an MCP server (stdio transport)

Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "apex-ops": {
      "command": "node",
      "args": ["/path/to/apex-ops-mcp/dist/index.js"],
      "env": {
        "APEX_HOME": "/Users/you/.apex"
      }
    }
  }
}
```

### Development

```bash
npm run dev     # Run with tsx (no build needed)
npm run watch   # Watch and rebuild
```

## Environment Variables

| Variable      | Default                  | Description                    |
|---------------|--------------------------|--------------------------------|
| `APEX_HOME`   | `~/.apex`                | APEX data directory            |
| `APEX_DB_PATH`| `$APEX_HOME/agentops.db` | SQLite database path           |
| `APEX_HOST`   | `127.0.0.1`              | TCP fallback host              |
| `APEX_PORT`   | `8717`                   | TCP fallback port              |

## Protocol

Uses the APEX JSON-line socket protocol (see `apex/protocol.py` and `apex/daemon.py`):

- **Request**: `{"id":"...", "command":"spawn", "session_id":"", "payload":{...}}\n`
- **Response**: `{"id":"...", "command":"spawn", "session_id":"...", "ok":true, "data":{...}, "error":"", "timestamp":"..."}\n`

## License

MIT
