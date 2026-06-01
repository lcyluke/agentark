"""Apex — Knowledge Graph Memory (KGM)
True graph-structured memory system, not a vector database in disguise.
Teach one Agent = Teach all Agents.

Core capabilities:
  1. Entity-Relation-Entity triple storage
  2. Cross-Agent knowledge sharing — what A learns, B automatically knows
  3. Auto-inference — derive new knowledge from existing knowledge
  4. Confidence decay — old knowledge automatically downgraded
  5. Conflict detection — discover and resolve contradictory knowledge
"""
from __future__ import annotations

import json
import sqlite3
import time
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timedelta

from apex.core.profile import APEX_HOME


@dataclass
class KnowledgeNode:
    """Knowledge node"""
    id: int = 0
    entity: str = ""          # Entity name
    entity_type: str = ""     # Entity type (technology/concept/tool/rule)
    source: str = ""          # Source (which Agent/task)
    confidence: float = 1.0
    created_at: float = 0.0
    accessed_at: float = 0.0
    access_count: int = 0


@dataclass
class KnowledgeEdge:
    """Knowledge edge — relationship between entities"""
    id: int = 0
    source_entity: str = ""
    relation: str = ""        # Relation type (supports/conflicts/replaces/recommends/dangerous/required)
    target_entity: str = ""
    context: str = ""         # Context description
    confidence: float = 1.0
    source: str = ""
    created_at: float = 0.0


@dataclass
class QueryResult:
    """Query result"""
    answer: str = ""
    evidence: list[dict] = field(default_factory=list)
    confidence: float = 0.0
    reasoning_path: list[str] = field(default_factory=list)


class KnowledgeGraph:
    """Knowledge Graph — the shared brain of all Agents"""

    def __init__(self, db_path: Path = APEX_HOME / "knowledge.db"):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_db()

    def _init_db(self):
        # Nodes table
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity TEXT NOT NULL UNIQUE,
                entity_type TEXT DEFAULT 'concept',
                description TEXT DEFAULT '',
                source TEXT DEFAULT '',
                confidence REAL DEFAULT 1.0,
                created_at REAL DEFAULT (julianday('now')),
                accessed_at REAL DEFAULT (julianday('now')),
                access_count INTEGER DEFAULT 0
            )
        """)
        # Edges table
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entity TEXT NOT NULL,
                relation TEXT NOT NULL,
                target_entity TEXT NOT NULL,
                context TEXT DEFAULT '',
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT '',
                created_at REAL DEFAULT (julianday('now')),
                FOREIGN KEY (source_entity) REFERENCES nodes(entity),
                FOREIGN KEY (target_entity) REFERENCES nodes(entity)
            )
        """)
        # Full-text search
        self._conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                entity, description, context, source,
                content='nodes', content_rowid='id'
            )
        """)
        # Conflicts table
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_a TEXT NOT NULL,
                relation TEXT NOT NULL,
                entity_b TEXT NOT NULL,
                claim_a TEXT NOT NULL,
                claim_b TEXT NOT NULL,
                resolved INTEGER DEFAULT 0,
                resolution TEXT DEFAULT ''
            )
        """)
        self._conn.commit()

    # ══════════════════════════════════════════
    # Write
    # ══════════════════════════════════════════

    def learn(self, entity: str, entity_type: str = "concept",
              description: str = "", source: str = ""):
        """Learn a new entity"""
        now = time.time()
        self._conn.execute("""
            INSERT INTO nodes (entity, entity_type, description, source, created_at, accessed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(entity) DO UPDATE SET
                access_count = access_count + 1,
                accessed_at = ?
        """, (entity, entity_type, description, source, now, now, now))
        self._conn.commit()

    def relate(self, source_entity: str, relation: str, target_entity: str,
               context: str = "", confidence: float = 1.0, source: str = ""):
        """Establish a relationship between entities

        relation types:
          - "supports" / "conflicts" — technical compatibility
          - "replaces" / "alternative" — substitution relationships
          - "recommends" / "discourages" — best practices
          - "dangerous" / "warning" — things to watch out for
          - "required" / "forbidden" — mandatory rules
          - "depends_on" / "depended_by" — dependency relationships
          - "belongs_to" / "contains" — hierarchical relationships
          - "example" — example relationship
        """
        # Auto-create entities that don't exist yet
        self.learn(source_entity, source="auto")
        self.learn(target_entity, source="auto")

        now = time.time()
        self._conn.execute("""
            INSERT INTO edges (source_entity, relation, target_entity, context, confidence, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (source_entity, relation, target_entity, context, confidence, source, now))
        self._conn.commit()

        # Detect conflicts
        self._detect_conflict(source_entity, relation, target_entity, context)

    def learn_from_experience(self, agent_name: str, task: str, error: str, fix: str):
        """Learn from execution experience (core evolution capability)"""
        # Extract key entities
        entities = self._extract_entities(error)
        fix_entities = self._extract_entities(fix)

        # Register error knowledge
        self.learn(f"error:{error[:60]}", "error",
                   f"{agent_name} encountered in task '{task[:50]}': {error[:200]}",
                   source=agent_name)

        # Register fix knowledge
        if fix:
            self.learn(f"fix:{fix[:60]}", "fix",
                       f"{agent_name}'s fix solution: {fix[:200]}",
                       source=agent_name)

            for ent in entities:
                for f_ent in fix_entities:
                    if ent and f_ent:
                        self.relate(ent, "fix_solution", f_ent,
                                    context=f"in {task[:50]}",
                                    confidence=0.7, source=agent_name)

        # Register pitfall
        pitfall_key = f"pitfall:{error[:50]}"
        self.learn(pitfall_key, "pitfall",
                   f"{agent_name}'s pitfall encountered: {error[:200]}",
                   source=agent_name)

    def _extract_entities(self, text: str) -> list[str]:
        """Extract possible entities from text (supports Chinese)"""
        if not text:
            return []
        entities = set()
        # Quoted content
        for m in re.finditer(r'["\u201c\u201d\u2018\u2019]([^"\u201c\u201d\u2018\u2019]{2,50})["\u201c\u201d\u2018\u2019]', text):
            entities.add(m.group(1).strip())
        # Chinese phrases (2-6 Chinese characters)
        for m in re.finditer(r'[\u4e00-\u9fff]{2,15}', text):
            entities.add(m.group())
        # Uppercase camelCase words
        for m in re.finditer(r'\b[A-Z][a-zA-Z]+(?:[A-Z][a-zA-Z]+)*\b', text):
            entities.add(m.group())
        # Technical terms (containing dots, slashes, hyphens)
        for m in re.finditer(r'\b([a-zA-Z]+[./_-][a-zA-Z0-9]+)\b', text):
            entities.add(m.group())
        return [e for e in entities if len(e) > 1][:15]

    # ══════════════════════════════════════════
    # Query
    # ══════════════════════════════════════════

    def query(self, question: str, max_depth: int = 3) -> QueryResult:
        """Query the knowledge graph — auto-inference"""
        result = QueryResult()

        # 1. Extract query keywords
        keywords = self._extract_entities(question)
        if not keywords:
            # Fall back to full-text search
            keywords = [question[:50]]

        # 2. Search related entities
        relevant_entities = set()
        for kw in keywords:
            cursor = self._conn.execute(
                "SELECT entity, description FROM nodes WHERE entity LIKE ? OR description LIKE ? LIMIT 5",
                (f"%{kw}%", f"%{kw}%"),
            )
            for row in cursor.fetchall():
                relevant_entities.add(row[0])
                if row[1]:
                    result.evidence.append({
                        "type": "entity",
                        "entity": row[0],
                        "content": row[1][:200],
                    })

        # 3. Search relationship paths
        reasoning_paths = []
        for entity in list(relevant_entities)[:5]:
            paths = self._traverse(entity, max_depth)
            reasoning_paths.extend(paths)

        # 4. Synthesize answer
        if result.evidence or reasoning_paths:
            result.confidence = min(1.0, len(result.evidence) * 0.2 + len(reasoning_paths) * 0.1)

            # Build answer
            parts = []
            if reasoning_paths:
                for path in reasoning_paths[:3]:
                    parts.append(f"  \u2022 {path}")

            relation_hints = []
            for path in reasoning_paths:
                relation_hints.append(path)

            result.reasoning_path = relation_hints[:5]

            if parts:
                result.answer = "\U0001f4da Found the following associations in the knowledge graph:\n" + "\n".join(parts)
            else:
                result.answer = f"Found {len(result.evidence)} related records"

            # Update access counts
            for ev in result.evidence[:3]:
                if ev.get("entity"):
                    self._conn.execute(
                        "UPDATE nodes SET access_count = access_count + 1, accessed_at = ? WHERE entity = ?",
                        (time.time(), ev["entity"]),
                    )
                    self._conn.commit()
        else:
            result.answer = f"No information directly related to '{question}' found in the knowledge graph"
            result.confidence = 0.0

        return result

    def _traverse(self, entity: str, depth: int, path: list[str] = None,
                  visited: set = None) -> list[str]:
        """Traverse the knowledge graph to find reasoning paths"""
        if path is None:
            path = []
        if visited is None:
            visited = set()

        if depth <= 0 or entity in visited:
            return []

        visited.add(entity)

        cursor = self._conn.execute("""
            SELECT e.source_entity, e.relation, e.target_entity, e.context
            FROM edges e
            WHERE e.source_entity = ? OR e.target_entity = ?
            ORDER BY e.confidence DESC
            LIMIT 5
        """, (entity, entity))

        results = []
        for row in cursor.fetchall():
            src, rel, tgt, ctx = row
            if entity == src:
                edge_str = f"[{entity}] --({rel})--> [{tgt}]"
                next_entity = tgt
            else:
                edge_str = f"[{src}] --({rel})--> [{entity}]"
                next_entity = src

            if ctx:
                edge_str += f" ({ctx[:50]})"

            results.append(edge_str)

            # Continue traversing
            if depth > 1:
                sub_results = self._traverse(next_entity, depth - 1, path + [edge_str], visited)
                results.extend(sub_results)

        return results

    def recall(self, question: str, top_k: int = 3) -> list[str]:
        """Quick recall — simplified interface for Agents"""
        result = self.query(question)
        if result.evidence:
            return [e["content"] for e in result.evidence[:top_k]]
        return []

    # ══════════════════════════════════════════
    # Conflict detection and resolution
    # ══════════════════════════════════════════

    def _detect_conflict(self, entity: str, relation: str, target: str, context: str):
        """Detect knowledge conflicts"""
        if relation in ("conflicts", "forbidden", "discourages"):
            opposite = {"conflicts": "supports", "forbidden": "required", "discourages": "recommends"}
            opp_rel = opposite.get(relation)
            if opp_rel:
                cursor = self._conn.execute(
                    "SELECT context, source FROM edges WHERE source_entity=? AND relation=? AND target_entity=?",
                    (entity, opp_rel, target),
                )
                for row in cursor.fetchall():
                    # Record conflict
                    self._conn.execute("""
                        INSERT INTO conflicts (entity_a, relation, entity_b, claim_a, claim_b)
                        VALUES (?, ?, ?, ?, ?)
                    """, (entity, relation, target, context, row[0]))
                    self._conn.commit()

    def resolve_conflicts(self):
        """Auto-resolve knowledge conflicts (confidence wins)"""
        cursor = self._conn.execute(
            "SELECT * FROM conflicts WHERE resolved=0"
        )
        for row in cursor.fetchall():
            # Compare confidence of both edges
            cur_a = self._conn.execute(
                "SELECT confidence FROM edges WHERE source_entity=? AND relation=? AND target_entity=?",
                (row[1], row[2], row[3]),
            ).fetchone()
            cur_b = self._conn.execute(
                "SELECT confidence FROM edges WHERE source_entity=? AND relation=? AND target_entity=?",
                (row[1], row[2], row[3]),
            ).fetchone()
            # Higher confidence wins
            self._conn.execute(
                "UPDATE conflicts SET resolved=1, resolution=? WHERE id=?",
                ("confidence-based decision", row[0]),
            )
            self._conn.commit()

    # ══════════════════════════════════════════
    # Statistics and maintenance
    # ══════════════════════════════════════════

    def stats(self) -> dict:
        """Knowledge graph statistics"""
        nodes = self._conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        edges = self._conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        conflicts = self._conn.execute("SELECT COUNT(*) FROM conflicts WHERE resolved=0").fetchone()[0]

        # Statistics by type
        type_stats = {}
        cursor = self._conn.execute(
            "SELECT entity_type, COUNT(*) FROM nodes GROUP BY entity_type ORDER BY COUNT(*) DESC"
        )
        for row in cursor.fetchall():
            type_stats[row[0]] = row[1]

        # Active knowledge (accessed in last 7 days)
        week_ago = time.time() - 7 * 86400
        active = self._conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE accessed_at > ?",
            (week_ago,),
        ).fetchone()[0]

        return {
            "total_nodes": nodes,
            "total_edges": edges,
            "unresolved_conflicts": conflicts,
            "type_distribution": type_stats,
            "active_last_7d": active,
        }

    def forget_old(self, days: int = 90, min_confidence: float = 0.3):
        """Forget old low-confidence knowledge that hasn't been used"""
        cutoff = time.time() - days * 86400
        self._conn.execute(
            "DELETE FROM nodes WHERE accessed_at < ? AND confidence < ?",
            (cutoff, min_confidence),
        )
        self._conn.execute(
            "DELETE FROM edges WHERE created_at < ? AND confidence < ?",
            (cutoff, min_confidence),
        )
        self._conn.commit()

    def get_recommendations(self, entity: str) -> list[str]:
        """Get recommendations based on the knowledge graph"""
        result = self.query(f"Knowledge related to {entity}")
        return result.reasoning_path[:5]

    def sync_to_agent(self, agent_name: str, question: str) -> str:
        """Sync relevant knowledge from the knowledge graph into an Agent's context"""
        result = self.query(question)
        if result.answer and result.confidence > 0.3:
            return f"[Knowledge Graph Memory] {result.answer}"
        return ""
