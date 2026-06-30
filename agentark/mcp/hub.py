"""Apex — MCP tool hub and registry"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable
from abc import ABC, abstractmethod


@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    description: str
    parameters: dict
    handler: Callable = None

    def to_openai_tool(self) -> dict:
        """Convert to OpenAI tool format"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


@dataclass
class MCPResult:
    """MCP call result"""
    success: bool
    output: str = ""
    error: str = ""
    data: dict = field(default_factory=dict)


class BaseMCPHandler(ABC):
    """Base MCP handler class"""

    @abstractmethod
    def handle(self, **kwargs) -> MCPResult:
        ...


# ══════════════════════════════════════════
# Built-in MCP tool implementations
# ══════════════════════════════════════════

class FileSystemMCP(BaseMCPHandler):
    """Filesystem operations"""

    def handle(self, action: str = "read", path: str = "", content: str = "",
               pattern: str = "", **kwargs) -> MCPResult:
        try:
            path = os.path.expanduser(path)
            if action == "read":
                if os.path.exists(path):
                    with open(path) as f:
                        data = f.read()
                    return MCPResult(success=True, output=data[:5000])
                return MCPResult(success=False, error=f"File not found: {path}")
            elif action == "write":
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    f.write(content)
                return MCPResult(success=True, output=f"Written {len(content)} characters to {path}")
            elif action == "list":
                dir_path = path or "."
                files = os.listdir(dir_path)
                return MCPResult(success=True, output="\n".join(files[:50]))
            elif action == "search":
                import fnmatch
                results = []
                for root, dirs, files in os.walk(path or "."):
                    for f in files:
                        if fnmatch.fnmatch(f, pattern):
                            results.append(os.path.join(root, f))
                return MCPResult(success=True, output="\n".join(results[:30]))
            else:
                return MCPResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return MCPResult(success=False, error=str(e))


class ShellMCP(BaseMCPHandler):
    """Command execution"""

    def handle(self, command: str = "", workdir: str = "", timeout: int = 30, **kwargs) -> MCPResult:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=workdir or None,
                timeout=timeout,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            return MCPResult(
                success=result.returncode == 0,
                output=output[:3000],
                error=result.stderr[:1000] if result.returncode != 0 else "",
            )
        except subprocess.TimeoutExpired:
            return MCPResult(success=False, error=f"Command timed out ({timeout}s): {command[:100]}")
        except Exception as e:
            return MCPResult(success=False, error=str(e))


class KnowledgeMCP(BaseMCPHandler):
    """Knowledge graph query"""

    def __init__(self):
        from agentark.core.knowledge import KnowledgeGraph
        self.kg = KnowledgeGraph()

    def handle(self, query: str = "", action: str = "query", entity: str = "",
               relation: str = "", target: str = "", **kwargs) -> MCPResult:
        try:
            if action == "query":
                result = self.kg.query(query)
                return MCPResult(
                    success=True,
                    output=result.answer[:3000],
                    data={"confidence": result.confidence, "evidence_count": len(result.evidence)},
                )
            elif action == "learn":
                self.kg.learn(entity, source="mcp")
                return MCPResult(success=True, output=f"Learned entity: {entity}")
            elif action == "relate":
                self.kg.relate(entity, relation, target, source="mcp")
                return MCPResult(success=True, output=f"Created relation: {entity} --({relation})--> {target}")
            elif action == "stats":
                stats = self.kg.stats()
                return MCPResult(success=True, output=json.dumps(stats, indent=2))
            else:
                return MCPResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return MCPResult(success=False, error=str(e))


class HTTPSMCP(BaseMCPHandler):
    """HTTP API calls"""

    def handle(self, method: str = "GET", url: str = "", headers: dict = None,
               body: str = "", timeout: int = 30, **kwargs) -> MCPResult:
        try:
            import httpx
            with httpx.Client(timeout=timeout) as client:
                resp = client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers or {},
                    content=body or None,
                )
                return MCPResult(
                    success=resp.is_success,
                    output=resp.text[:3000],
                    data={"status_code": resp.status_code, "headers": dict(resp.headers)},
                )
        except Exception as e:
            return MCPResult(success=False, error=str(e))


# ══════════════════════════════════════════
# MCP Hub — Registry
# ══════════════════════════════════════════

class MCPHub:
    """MCP Hub — Entry point for all tools"""

    def __init__(self):
        self._tools: dict[str, MCPTool] = {}
        self._register_builtins()

    def _register_builtins(self):
        """Register built-in MCP tools"""
        self.register(MCPTool(
            name="filesystem",
            description="Filesystem operations: read, write, list files",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["read", "write", "list", "search"]},
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Content to write (for write action)"},
                    "pattern": {"type": "string", "description": "Search pattern (for search action)"},
                },
                "required": ["action", "path"],
            },
            handler=FileSystemMCP().handle,
        ))
        self.register(MCPTool(
            name="shell",
            description="Execute shell commands",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"},
                    "workdir": {"type": "string", "description": "Working directory"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds"},
                },
                "required": ["command"],
            },
            handler=ShellMCP().handle,
        ))
        self.register(MCPTool(
            name="knowledge",
            description="Knowledge graph query and learning",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["query", "learn", "relate", "stats"]},
                    "query": {"type": "string", "description": "Query content"},
                    "entity": {"type": "string", "description": "Entity name"},
                    "relation": {"type": "string", "description": "Relation type"},
                    "target": {"type": "string", "description": "Target entity"},
                },
                "required": ["action"],
            },
            handler=KnowledgeMCP().handle,
        ))
        self.register(MCPTool(
            name="http",
            description="HTTP API calls",
            parameters={
                "type": "object",
                "properties": {
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                    "url": {"type": "string", "description": "Request URL"},
                    "headers": {"type": "object", "description": "Request headers"},
                    "body": {"type": "string", "description": "Request body"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds"},
                },
                "required": ["url"],
            },
            handler=HTTPSMCP().handle,
        ))

    def register(self, tool: MCPTool):
        """Register an MCP tool"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[MCPTool]:
        return self._tools.get(name)

    def call(self, tool_name, **kwargs):
        """Call an MCP tool"""
        tool = self.get(tool_name)
        if not tool:
            return MCPResult(success=False, error=f"Unknown MCP tool: {tool_name}")
        if not tool.handler:
            return MCPResult(success=False, error=f"MCP tool '{tool_name}' has no handler")
        return tool.handler(**kwargs)

    def list_tools(self) -> list[dict]:
        """List all available tools"""
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in self._tools.values()
        ]

    def to_openai_tools(self) -> list[dict]:
        """Export to OpenAI tool format"""
        return [t.to_openai_tool() for t in self._tools.values()]


# Global MCP Hub
hub = MCPHub()
