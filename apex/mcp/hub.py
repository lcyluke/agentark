"""Apex — MCP Hub
Agent与外部世界的连接器。跨语言、跨机器、跨框架。
任何支持MCP的工具/服务都可以无缝接入。

内置MCP工具:
  - filesystem: 文件读写搜索
  - github: 代码仓库管理
  - browser: 网页浏览
  - shell: 命令执行
  - http: API调用
  - search: 知识图谱查询
"""
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
    """MCP工具定义"""
    name: str
    description: str
    parameters: dict
    handler: Callable = None

    def to_openai_tool(self) -> dict:
        """转成OpenAI工具格式"""
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
    """MCP调用结果"""
    success: bool
    output: str = ""
    error: str = ""
    data: dict = field(default_factory=dict)


class BaseMCPHandler(ABC):
    """MCP处理器基类"""

    @abstractmethod
    def handle(self, **kwargs) -> MCPResult:
        ...


# ══════════════════════════════════════════
# 内置MCP工具实现
# ══════════════════════════════════════════

class FileSystemMCP(BaseMCPHandler):
    """文件系统操作"""

    def handle(self, action: str = "read", path: str = "", content: str = "",
               pattern: str = "", **kwargs) -> MCPResult:
        try:
            path = os.path.expanduser(path)
            if action == "read":
                if os.path.exists(path):
                    with open(path) as f:
                        data = f.read()
                    return MCPResult(success=True, output=data[:5000])
                return MCPResult(success=False, error=f"文件不存在: {path}")
            elif action == "write":
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    f.write(content)
                return MCPResult(success=True, output=f"已写入 {len(content)} 字符到 {path}")
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
                return MCPResult(success=False, error=f"未知操作: {action}")
        except Exception as e:
            return MCPResult(success=False, error=str(e))


class ShellMCP(BaseMCPHandler):
    """命令执行"""

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
            return MCPResult(success=False, error=f"命令超时({timeout}s): {command[:100]}")
        except Exception as e:
            return MCPResult(success=False, error=str(e))


class KnowledgeMCP(BaseMCPHandler):
    """知识图谱查询"""

    def __init__(self):
        from apex.core.knowledge import KnowledgeGraph
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
                return MCPResult(success=True, output=f"已学习实体: {entity}")
            elif action == "relate":
                self.kg.relate(entity, relation, target, source="mcp")
                return MCPResult(success=True, output=f"已建立关系: {entity} --({relation})--> {target}")
            elif action == "stats":
                stats = self.kg.stats()
                return MCPResult(success=True, output=json.dumps(stats, indent=2))
            else:
                return MCPResult(success=False, error=f"未知操作: {action}")
        except Exception as e:
            return MCPResult(success=False, error=str(e))


class HTTPSMCP(BaseMCPHandler):
    """HTTP API调用"""

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
# MCP Hub — 注册中心
# ══════════════════════════════════════════

class MCPHub:
    """MCP Hub — 所有工具的入口"""

    def __init__(self):
        self._tools: dict[str, MCPTool] = {}
        self._register_builtins()

    def _register_builtins(self):
        """注册内置MCP工具"""
        self.register(MCPTool(
            name="filesystem",
            description="文件系统操作：读取、写入、列出文件",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["read", "write", "list", "search"]},
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "写入内容（write时）"},
                    "pattern": {"type": "string", "description": "搜索模式（search时）"},
                },
                "required": ["action", "path"],
            },
            handler=FileSystemMCP().handle,
        ))
        self.register(MCPTool(
            name="shell",
            description="执行Shell命令",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的命令"},
                    "workdir": {"type": "string", "description": "工作目录"},
                    "timeout": {"type": "integer", "description": "超时秒数"},
                },
                "required": ["command"],
            },
            handler=ShellMCP().handle,
        ))
        self.register(MCPTool(
            name="knowledge",
            description="知识图谱查询和学习",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["query", "learn", "relate", "stats"]},
                    "query": {"type": "string", "description": "查询内容"},
                    "entity": {"type": "string", "description": "实体名称"},
                    "relation": {"type": "string", "description": "关系类型"},
                    "target": {"type": "string", "description": "目标实体"},
                },
                "required": ["action"],
            },
            handler=KnowledgeMCP().handle,
        ))
        self.register(MCPTool(
            name="http",
            description="HTTP API调用",
            parameters={
                "type": "object",
                "properties": {
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                    "url": {"type": "string", "description": "请求URL"},
                    "headers": {"type": "object", "description": "请求头"},
                    "body": {"type": "string", "description": "请求体"},
                    "timeout": {"type": "integer", "description": "超时秒数"},
                },
                "required": ["url"],
            },
            handler=HTTPSMCP().handle,
        ))

    def register(self, tool: MCPTool):
        """注册一个MCP工具"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[MCPTool]:
        return self._tools.get(name)

    def call(self, name: str, **kwargs) -> MCPResult:
        """调用一个MCP工具"""
        tool = self.get(name)
        if not tool:
            return MCPResult(success=False, error=f"未知MCP工具: {name}")
        if not tool.handler:
            return MCPResult(success=False, error=f"MCP工具 '{name}' 没有处理器")
        return tool.handler(**kwargs)

    def list_tools(self) -> list[dict]:
        """列出所有可用工具"""
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in self._tools.values()
        ]

    def to_openai_tools(self) -> list[dict]:
        """导出为OpenAI工具格式"""
        return [t.to_openai_tool() for t in self._tools.values()]


# 全局MCP Hub
hub = MCPHub()
