# Semgrep MCP Server — Integration Reference

## Discovery

The npm package is **`mcp-server-semgrep`** (NOT `@semgrep/mcp`).
- Registry: https://www.npmjs.com/package/mcp-server-semgrep
- GitHub: https://github.com/VetCoders/mcp-server-semgrep
- Version tested: 1.0.1
- License: MIT

## Prerequisites

### semgrep CLI (REQUIRED)

Install via **Homebrew** on macOS (pip install fails — missing `pysemgrep` binary):

```bash
brew install semgrep
# → /opt/homebrew/bin/semgrep
```

Do NOT use `pip3 install semgrep` — it installs the Python package but lacks the native `pysemgrep` binary, producing:
```
Error: exception Unix_error: No such file or directory execvp pysemgrep
```

### Node.js

Node.js v18+ required. The MCP server is ES Modules.

## Installation

```bash
npm install -g mcp-server-semgrep
# → /opt/homebrew/lib/node_modules/mcp-server-semgrep/build/index.js
```

## Hermes config.yaml

```yaml
mcp_servers:
  semgrep:
    command: "node"
    args:
      - "/opt/homebrew/lib/node_modules/mcp-server-semgrep/build/index.js"
    env:
      MCP_SERVER_SEMGREP_ALLOWED_ROOTS: "/Users/Mac/Desktop/2026AIAPP:/Users/Mac/Desktop/2026Parsimo"
    timeout: 120
    connect_timeout: 60
```

### Allowed Roots

The server ONLY reads/writes within explicitly allowed roots. Use `:` as path separator on macOS/Linux, `;` on Windows. Without this, the server refuses to scan.

The `SEMGREP_APP_TOKEN` env var is optional for local use (uses existing `semgrep login` session).

## 7 MCP Tools Exposed

| Tool | Purpose |
|:--|:--|
| `scan_directory` | SAST scan of source directories |
| `list_rules` | List available Semgrep rules + supported languages |
| `analyze_results` | Detailed analysis of scan findings |
| `create_rule` | Create custom Semgrep rules |
| `filter_results` | Filter by severity, CWE, language, etc. |
| `export_results` | Export as JSON/CSV/SARIF |
| `compare_results` | Diff before/after scans to verify fixes |

Tool names in Hermes become: `mcp_semgrep_scan_directory`, `mcp_semgrep_list_rules`, etc.

## Standard Workflow

```
1. mcp_semgrep_list_rules          → discover available rules
2. mcp_semgrep_scan_directory      → execute scan
3. mcp_semgrep_filter_results      → focus on Critical/High
4. mcp_semgrep_analyze_results     → deep-dive on key findings
5. Fix the code
6. mcp_semgrep_scan_directory      → rescan
7. mcp_semgrep_compare_results     → verify fix efficacy
8. mcp_semgrep_export_results      → produce final report (SARIF)
```

## Apex Security Agent Integration

Wire into agent SOUL.md by adding a "Semgrep MCP 集成" section after the toolchain. Reference the MCP tools the agent should use. Updated agents:

- `vulnerability-scanner` — primary consumer (SAST + SCA + secret detection)
- `security-compliance` — secondary consumer (compliance auditing)

## Verification

```bash
# 1. Start MCP server in background
MCP_SERVER_SEMGREP_ALLOWED_ROOTS="/path/to/projects" \
  node /opt/homebrew/lib/node_modules/mcp-server-semgrep/build/index.js &

# 2. Test semgrep CLI directly
semgrep --config=auto --dryrun /path/to/project

# 3. After Hermes restart, check tools registered:
# Look for mcp_semgrep_* in tool list
```

## Pitfalls

- **config.yaml is protected**: Both `patch` tool and `terminal` block writes to `~/.hermes/config.yaml`. User must add the `mcp_servers` block manually.
- **Allowed roots must be absolute paths**: Relative paths are rejected.
- **First scan on large projects is slow**: Semgrep downloads community rules on first run (~1059 rules for Python).
