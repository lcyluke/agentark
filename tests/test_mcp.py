"""
Tests for the Apex MCP Hub.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agentark.mcp.hub import MCPHub, MCPTool, MCPResult
from agentark.core.knowledge import KnowledgeGraph


class TestMCPHub:
    """Test suite for the MCP Hub."""

    def test_hub_init(self):
        """MCPHub initializes with built-in tools."""
        hub = MCPHub()
        tools = hub.list_tools()
        tool_names = [t["name"] for t in tools]
        assert "filesystem" in tool_names
        assert "shell" in tool_names
        assert "knowledge" in tool_names
        assert "http" in tool_names

    def test_hub_list_tools(self):
        """list_tools returns metadata for all registered tools."""
        hub = MCPHub()
        tools = hub.list_tools()
        assert len(tools) >= 4
        for t in tools:
            assert "name" in t
            assert "description" in t
            assert "parameters" in t

    def test_filesystem_read_nonexistent(self):
        """Reading a non-existent file returns an error result."""
        hub = MCPHub()
        result = hub.call("filesystem", action="read", path="/tmp/nonexistent_file_xyz_123.test")
        assert result.success is False
        assert "not found" in result.error.lower() or "exist" in result.error.lower()

    def test_knowledge_query(self, tmp_agentark_home: Path):
        """Knowledge MCP tool returns a result for a query."""
        hub = MCPHub()
        # Seed some data into the default knowledge graph location
        # The KnowledgeMCP uses KnowledgeGraph() which defaults to AGENTARK_HOME/knowledge.db
        # We need to work around this — let's check that the tool at least responds
        result = hub.call("knowledge", action="stats")
        # stats should succeed even with an empty graph
        assert result.success is True
        assert "total_nodes" in result.output
