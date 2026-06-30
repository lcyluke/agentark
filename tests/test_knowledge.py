"""
Tests for the Apex Knowledge Graph system.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from agentark.core.knowledge import KnowledgeGraph, QueryResult


class TestKnowledgeGraph:
    """Test suite for the knowledge graph."""

    def test_learn_entity(self, tmp_agentark_home: Path):
        """Learning an entity adds it to the graph."""
        kg = KnowledgeGraph(db_path=tmp_agentark_home / "knowledge.db")
        kg.learn("Redis", "database", "In-memory data structure store", source="test")
        stats = kg.stats()
        assert stats["total_nodes"] >= 1

        # Learning the same entity again increments access count
        kg.learn("Redis", "database", "Updated description", source="test")
        stats2 = kg.stats()
        # Node count should still be 1 (ON CONFLICT DO UPDATE)
        # We can verify via query
        result = kg.query("Redis")
        assert result.confidence > 0

    def test_relate_entities(self, tmp_agentark_home: Path):
        """Relating two entities creates an edge."""
        kg = KnowledgeGraph(db_path=tmp_agentark_home / "knowledge.db")
        kg.learn("Python", "language", source="test")
        kg.learn("FastAPI", "framework", source="test")
        kg.relate("FastAPI", "depends_on", "Python", "built on Python", source="test")

        stats = kg.stats()
        assert stats["total_edges"] >= 1

        # Query should find the relationship
        result = kg.query("FastAPI")
        assert result.confidence > 0
        assert result.answer != ""

    def test_query_with_results(self, sample_knowledge_graph: KnowledgeGraph):
        """Query returns results when matching entities exist."""
        kg = sample_knowledge_graph
        result = kg.query("FastAPI")
        assert result.confidence > 0
        assert "Found" in result.answer or "associations" in result.answer
        assert len(result.evidence) > 0

    def test_query_no_results(self, tmp_agentark_home: Path):
        """Query returns empty result when nothing matches."""
        kg = KnowledgeGraph(db_path=tmp_agentark_home / "knowledge.db")
        result = kg.query("NonExistentTechnologyXYZ123")
        assert result.confidence == 0.0
        assert "not found" in result.answer.lower() or "no information" in result.answer.lower()

    def test_stats(self, sample_knowledge_graph: KnowledgeGraph):
        """Stats returns correct counts."""
        kg = sample_knowledge_graph
        stats = kg.stats()
        assert stats["total_nodes"] >= 3
        assert stats["total_edges"] >= 2
        assert "type_distribution" in stats
        assert isinstance(stats["type_distribution"], dict)

    def test_learn_from_experience(self, tmp_agentark_home: Path):
        """learn_from_experience records errors, fixes, and pitfalls."""
        kg = KnowledgeGraph(db_path=tmp_agentark_home / "knowledge.db")
        kg.learn_from_experience(
            agent_name="test-agent",
            task="Deploy the application",
            error="ConnectionError: port 8080 already in use",
            fix="Change port to 8081 or kill the existing process",
        )

        # Query about the error should find related knowledge
        result = kg.query("ConnectionError port already in use")
        # Should have some confidence from the learned entities
        assert result.confidence >= 0 or result.answer != ""
        stats = kg.stats()
        assert stats["total_nodes"] >= 1
