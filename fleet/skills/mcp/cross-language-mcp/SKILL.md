---
name: cross-language-mcp
description: "Build and test MCP stdio servers in any language (Node.js, Go, Rust, Java) — protocol, edge cases, lambda patterns, subprocess quirks"
version: 1.0.0
platforms: [macos, linux]
related_skills: [apex-uat-testing]
---

# Cross-Language MCP Server Integration

## Overview

Connect Apex (Python) to MCP servers written in Node.js, Go, Rust, Java, or any language that reads JSON-RPC 2.0 from stdin and writes to stdout.

## Core Pattern

```
Python (Apex MCPHub + StdioClient)
  ──stdin──▶ {"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
  ◀──stdout── {"jsonrpc":"2.0","id":1,"result":{"tools":[...]}}
```

Every MCP server must:
1. Print `{"jsonrpc":"2.0","method":"server/ready",...}` on startup (waited for by `connect()`)
2. Listen on stdin for JSON-RPC requests
3. Write JSON-RPC responses to stdout (one JSON per line, terminated by `\n`)
4. Support at minimum: `initialize`, `tools/list`, `tools/call`, `server/info`

## StdioClient Usage (apex/mcp/stdio_client.py)

```python
from apex.mcp.stdio_client import MCPStdioClient
from apex.mcp.hub import MCPHub

hub = MCPHub()
client = MCPStdioClient("node", ["server.js"], name="Node.js")
client.connect()

# Register all tools from the server into Hub with a prefix
client.register_with_hub(hub, prefix="node.")

# Call via Hub
hub.call("node.greet", name="World", language="zh")

# Call directly
result = client.call_tool("greet", {"name": "World"})

# Cleanup
client.disconnect()
```

## Pitfalls

### 1. Subprocess `text=True` breaks some servers
Rust servers (and potentially others) fail to encode/decode properly when `Popen` is opened in text mode. **Always use binary mode:**
```python
subprocess.Popen([cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
```
Then write bytes, read bytes:
```python
proc.stdin.write(json.dumps(req, separators=(',',':')).encode() + b"\n")
proc.stdin.flush()
```

### 2. `json.dumps()` spacing matters
Default `json.dumps()` produces `"key": "val"` (with spaces). Rust servers doing `line.contains("\"method\":\"tools/list\"")` will NOT match the spaced version.
**Always use compact JSON:**
```python
json.dumps(request, separators=(',', ':'))
```

### 3. `proc.stdout.readline()` has pipe buffering issues
Python's `stdout.readline()` (even with `bufsize=1`) can block indefinitely when reading from subprocess pipes. 
**Use `os.read(fd, 1)` byte-by-byte under `select.select()` timeout instead:**
```python
import select, os
fd = proc.stdout.fileno()
readable, _, _ = select.select([fd], [], [], timeout)
if readable:
    buf = b""
    while True:
        r, _, _ = select.select([fd], [], [], 0.5)
        if not r: break
        b = os.read(fd, 1)
        if not b or b == b'\n': break
        buf += b
    return buf.decode()
```

### 4. Hub `register_with_hub()` lambda pattern
The handler lambda for each registered MCPTool must accept `**kwargs` and forward them:
```python
handler=lambda n=name, fn=self.call_tool, **kw: self._mcp_wrapper(fn, n, kw)
```
Do NOT nest lambdas — parameter names like `name` and `fn` will shadow Hub.call() keyword arguments.

### 5. `MCPHub.call()` parameter name
**Do not name the first parameter `name`** — it clashes with keyword arguments passed to `**kwargs`. Use `tool_name` instead:
```python
def call(self, tool_name, **kwargs):
    tool = self.get(tool_name)
```

### 6. Server /ready signal
The `connect()` method waits for `{"method":"server/ready"}`. Rust and Go servers output this as the first line. Node.js uses `readline` which triggers after the first `\n`. If the server doesn't emit a ready signal, `connect()` will time out after 5 seconds.

## Minimal MCP Server Templates

### Node.js
```javascript
const readline = require('readline');
const rl = readline.createInterface({ input: process.stdin });
// Signal ready
process.stdout.write(JSON.stringify({"jsonrpc":"2.0","method":"server/ready",...})+"\n");
rl.on('line', (line) => {
  const msg = JSON.parse(line);
  if (msg.method === "tools/list") { ... }
  else if (msg.method === "tools/call") { ... }
});
```

### Go
```go
// Signal ready
json.NewEncoder(os.Stdout).Encode(map[string]interface{}{"jsonrpc":"2.0","method":"server/ready",...})
scanner := bufio.NewScanner(os.Stdin)
for scanner.Scan() {
    var req MCPRequest
    json.Unmarshal([]byte(scanner.Text()), &req)
    switch req.Method { ... }
}
```

### Rust (zero external deps)
Pure stdlib — build JSON strings manually with format!(). See `scripts/mcp-servers/mcp-rust-server.rs` for a complete working example. No serde, no serde_json. Uses `line.contains("\"method\":\"...\"")` for method routing. **Remember to strip spaces from `: ` to `:` before string matching.**
