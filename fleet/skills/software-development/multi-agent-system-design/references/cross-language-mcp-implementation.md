# Cross-Language MCP Implementation

## Architecture

```
Python Apex Host
├── apex/mcp/hub.py           — MCP Hub (tool registry, built-in tools)
├── apex/mcp/stdio_client.py  — MCP stdio client (JSON-RPC 2.0 over subprocess)
├── apex/mcp/__init__.py      — package marker
│
├── scripts/mcp-servers/mcp-node-server.js  — Node.js MCP server (greet/weather/sentiment)
├── scripts/mcp-servers/mcp-go-server.go    — Go MCP server (calculate/file/time)
├── scripts/mcp-servers/mcp-rust-server.rs  — Rust MCP server (text analysis/math)
│
└── tests/test_mcp_cross_language.py        — 39 integration tests
```

## Protocol (JSON-RPC 2.0)

All communication is line-delimited JSON over the server process's stdin/stdout:

**Server → Client (init):**
```json
{"jsonrpc":"2.0","method":"server/ready","params":{"name":"Name","version":"1.0.0"}}
```

**Client → Server:** (compact JSON, required for Rust compatibility)
```json
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"greet","arguments":{"name":"World"}}}
```

**Server → Client:**
```json
{"jsonrpc":"2.0","id":1,"result":{"tools":[{"name":"greet","description":"...","inputSchema":{...}}]}}
{"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"Hello!"}],"isError":false}}
```

## MCPStdioClient API

```python
from apex.mcp.stdio_client import MCPStdioClient
from apex.mcp.hub import MCPHub

hub = MCPHub()

# Connect to any MCP server
server = MCPStdioClient(
    command="node",
    args=["path/to/server.js"],
    name="MyServer",  # used in tool descriptions
)
server.connect(timeout=5.0)  # returns True/False

# Manually call tools
tools = server.list_tools()                      # -> list[dict]
result = server.call_tool("greet", {"name": "X"}) # -> dict with content/isError
info = server.get_server_info()                   # -> dict

# Or register all tools into hub
server.register_with_hub(hub, prefix="my.")       # tools become "my.greet" etc.

# Through the hub
hub.call("my.greet", name="Luke", language="zh")

# Cleanup
server.disconnect()
```

## Known Pitfalls

1. **Compact JSON required** — `json.dumps(request, separators=(',', ':'))` not `json.dumps(request)`. Some MCP servers (Rust with string-based method detection) fail on Python's default pretty JSON that adds spaces.

2. **Binary-safe I/O required** — Use `os.read(fd, 1)` byte-by-byte, NOT `proc.stdout.readline()` which buffers text differently. Some servers (Rust, Go) produce output that gets stuck in Python's buffered reader.

3. **No `text=True` in Popen** — `subprocess.Popen(text=True, bufsize=1)` causes issues with servers that flush output line-by-line in a different encoding. Use the default binary mode and decode manually.

4. **server/ready signal** — The client's `connect()` method waits for a `server/ready` signal before returning. If the server emits it as a normal `tools/list response`-style JSON-RPC message, the connect() method won't see it. Only the explicit `method: "server/ready"` format is recognized.

5. **Handler parameter shadowing** — When registering tools via `register_with_hub()`, the lambda wrapping `call_tool` must NOT use `name` as the parameter name because `hub.call(tool_name, name="value")` passes `name` as both a keyword argument AND the parameter name. Use a unique parameter name like `tool_name` instead.

6. **Rust with zero deps** — Pure Rust without serde/serde_json requires manual JSON building via string concatenation. The server uses `line_compact = line.replace(": ", ":")` to normalize incoming JSON before string-based method detection. This works for simple JSON but doesn't handle nested spaces or escaped quotes.

## Test Results (2026-06-03)

| Language | Connect | List Tools | Call Tools | Server Info | Hub Register | Details |
|----------|---------|------------|------------|-------------|--------------|---------|
| Node.js  | ✅ | ✅ (3) | ✅ greet/weather/sentiment | 100% | ✅ | Full round-trip |
| Go       | ✅ | ✅ (3) | ✅ calculate/file/time | 100% | ✅ | Full round-trip |
| Rust     | ✅ | ✅ (3) | ✅ text/fib/prime | 100% | ✅ | Zero deps stdlib |
| Hub Chain | — | — | ✅ node + go + hub | — | 10 tools, 6 cross-lang | 2 args-shadow bugs |

**Total: 37/39 passed (94.9%)**
