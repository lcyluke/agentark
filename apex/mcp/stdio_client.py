"""Apex — MCP Stdio Client
Connects to external MCP servers (Node.js, Go, Rust, etc.) via stdio transport.
Enables cross-language tool calling from Python Apex agents.

MCP Protocol: JSON-RPC 2.0 over stdin/stdout
  Client -> Server:  {"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
  Server -> Client:  {"jsonrpc":"2.0","id":1,"result":{"tools":[...]}}
"""
from __future__ import annotations

import json
import subprocess
import threading
import time
import os
from pathlib import Path
from typing import Optional

from .hub import MCPTool, MCPResult, MCPHub


class MCPStdioClient:
    """Connect to an external MCP server process via stdio transport.

    The server can be written in any language (Node.js, Go, Rust, Java, etc.)
    as long as it speaks JSON-RPC 2.0 over stdin/stdout.

    Usage:
        client = MCPStdioClient("node", ["server.js"])
        client.connect()
        tools = client.list_tools()
        result = client.call_tool("greet", {"name": "World"})
        client.disconnect()
    """

    def __init__(self, command: str, args: list[str] = None,
                 name: str = "mcp-server", env: dict = None):
        self.command = command
        self.args = args or []
        self.name = name
        self.env = env or {}
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._id_counter = 0
        self._buffer = ""

    def connect(self, timeout: float = 5.0) -> bool:
        """Start the MCP server process and wait for ready signal."""
        full_env = os.environ.copy()
        full_env.update(self.env)

        self._process = subprocess.Popen(
            [self.command] + self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=full_env,
        )

        # Wait for the server/ready signal
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self._read_line(timeout=1)
            if line is None:
                continue
            try:
                msg = json.loads(line)
                if msg.get("method") == "server/ready":
                    return True
            except (json.JSONDecodeError, KeyError):
                continue

        return False

    def disconnect(self):
        """Stop the MCP server process."""
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    def list_tools(self) -> list[dict]:
        """List tools available from this MCP server."""
        result = self._send_request("tools/list", {})
        if result and "tools" in result:
            return result["tools"]
        return []

    def call_tool(self, name: str, arguments: dict = None) -> dict:
        """Call a tool on the MCP server."""
        result = self._send_request("tools/call", {
            "name": name,
            "arguments": arguments or {},
        })
        return result or {}

    def get_server_info(self) -> dict:
        """Get server metadata."""
        result = self._send_request("server/info", {})
        return result or {}

    def register_with_hub(self, hub: MCPHub, prefix: str = ""):
        """Register all tools from this MCP server into the Apex MCP Hub.

        Args:
            hub: The Apex MCPHub instance.
            prefix: Optional prefix for tool names (e.g. "node.").
        """
        tools = self.list_tools()
        for tool_def in tools:
            name = tool_def.get("name", "unknown")
            full_name = f"{prefix}{name}" if prefix else name
            description = tool_def.get("description", "")
            input_schema = tool_def.get("inputSchema", tool_def.get("input_schema", {}))
            mcp_tool = MCPTool(
                name=full_name,
                description=f"[{self.name}] {description}",
                parameters=input_schema,
                handler=lambda n=name, fn=self.call_tool, **kw: self._mcp_wrapper(fn, n, kw),
            )
            hub.register(mcp_tool)

    # ── Internal ──

    def _mcp_wrapper(self, fn, tool_name: str, kwargs: dict) -> MCPResult:
        """Wrap an MCP tool call into the Apex MCPResult format."""
        try:
            result = fn(tool_name, kwargs)
            content_list = result.get("content", [])
            text = "\n".join(
                c.get("text", "") for c in content_list if c.get("type") == "text"
            )
            is_error = result.get("isError", False)
            return MCPResult(
                success=not is_error,
                output=text,
                error="" if not is_error else text,
                data=result,
            )
        except Exception as e:
            return MCPResult(success=False, error=str(e))

    def _send_request(self, method: str, params: dict) -> Optional[dict]:
        """Send a JSON-RPC request and wait for the response."""
        with self._lock:
            self._id_counter += 1
            request = {
                "jsonrpc": "2.0",
                "id": self._id_counter,
                "method": method,
                "params": params,
            }
            if self._process and self._process.stdin:
                self._process.stdin.write(json.dumps(request, separators=(',', ':')).encode('utf-8') + b"\n")
                self._process.stdin.flush()

        # Read response — small delay to let server process
        import time as time_module
        time_module.sleep(0.1)
        deadline = time_module.time() + 10.0
        while time_module.time() < deadline:
            line = self._read_line(timeout=5.0)
            if line is None:
                continue
            try:
                msg = json.loads(line)
                if msg.get("id") == self._id_counter:
                    if "result" in msg:
                        return msg["result"]
                    if "error" in msg:
                        raise RuntimeError(f"MCP error: {msg['error']}")
            except (json.JSONDecodeError, KeyError):
                continue

        raise TimeoutError(f"MCP request '{method}' timed out (id={self._id_counter})")

    def _read_line(self, timeout: float = 5.0) -> Optional[str]:
        """Read a single line from the MCP server stdout (byte-by-byte for safety)."""
        if not self._process or not self._process.stdout:
            return None

        import select
        import os as os_module

        fd = self._process.stdout.fileno()
        readable, _, _ = select.select([fd], [], [], timeout)
        if not readable:
            return None

        # Read byte by byte until newline
        buf = b""
        while True:
            r2, _, _ = select.select([fd], [], [], 0.5)
            if not r2:
                break
            b = os_module.read(fd, 1)
            if not b:
                break
            if b == b'\n':
                break
            buf += b

        if not buf:
            return None

        decoded = buf.decode('utf-8', errors='replace').strip()
        return decoded if decoded else None

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()
