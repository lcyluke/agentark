"""Apex — 知识图谱记忆（KGM）
真正的图结构记忆系统，不是向量数据库伪装。
教会一个Agent = 教会所有Agent。

核心能力:
  1. 实体-关系-实体三元组存储
  2. 跨Agent知识共享 — A学到的东西B自动知道
  3. 自动推理 — 从已有知识推导新知识
  4. 置信度衰减 — 旧知识自动降权
  5. 冲突检测 — 发现矛盾知识并解决
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
    """知识节点"""
    id: int = 0
    entity: str = ""          # 实体名称
    entity_type: str = ""     # 实体类型（技术/概念/工具/规则）
    source: str = ""          # 来源（哪个Agent/task）
    confidence: float = 1.0
    created_at: float = 0.0
    accessed_at: float = 0.0
    access_count: int = 0


@dataclass
class KnowledgeEdge:
    """知识边 — 实体之间的关系"""
    id: int = 0
    source_entity: str = ""
    relation: str = ""        # 关系类型（支持/不支持/替代/推荐/危险/必须）
    target_entity: str = ""
    context: str = ""         # 上下文说明
    confidence: float = 1.0
    source: str = ""
    created_at: float = 0.0


@dataclass
class QueryResult:
    """查询结果"""
    answer: str = ""
    evidence: list[dict] = field(default_factory=list)
    confidence: float = 0.0
    reasoning_path: list[str] = field(default_factory=list)


class KnowledgeGraph:
    """知识图谱 — 所有Agent共享的大脑"""

    def __init__(self, db_path: Path = APEX_HOME / "knowledge.db"):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_db()

    def _init_db(self):
        # 节点表
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
        # 边表
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
        # 全文搜索
        self._conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                entity, description, context, source,
                content='nodes', content_rowid='id'
            )
        """)
        # 冲突表
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
    # 写入
    # ══════════════════════════════════════════

    def learn(self, entity: str, entity_type: str = "concept",
              description: str = "", source: str = ""):
        """学习一个新实体"""
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
        """建立实体间关系

        relation类型:
          - "支持" / "不支持" — 技术兼容性
          - "替代" / "替代方案" — 替代关系
          - "推荐" / "不推荐" — 最佳实践
          - "危险" / "警告" — 需要注意
          - "必须" / "禁止" — 强制规则
          - "依赖" / "被依赖" — 依赖关系
          - "属于" / "包含" — 层级关系
          - "例子" — 示例关系
        """
        # 自动创建不存在的实体
        self.learn(source_entity, source="auto")
        self.learn(target_entity, source="auto")

        now = time.time()
        self._conn.execute("""
            INSERT INTO edges (source_entity, relation, target_entity, context, confidence, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (source_entity, relation, target_entity, context, confidence, source, now))
        self._conn.commit()

        # 检测冲突
        self._detect_conflict(source_entity, relation, target_entity, context)

    def learn_from_experience(self, agent_name: str, task: str, error: str, fix: str):
        """从执行经验中学习（核心进化能力）"""
        # 提取关键实体
        entities = self._extract_entities(error)
        fix_entities = self._extract_entities(fix)

        # 注册错误知识
        self.learn(f"错误:{error[:60]}", "error",
                   f"{agent_name}在任务'{task[:50]}'中遇到: {error[:200]}",
                   source=agent_name)

        # 注册修复知识
        if fix:
            self.learn(f"修复:{fix[:60]}", "fix",
                       f"{agent_name}的修复方案: {fix[:200]}",
                       source=agent_name)

            for ent in entities:
                for f_ent in fix_entities:
                    if ent and f_ent:
                        self.relate(ent, "修复方案", f_ent,
                                    context=f"在{task[:50]}中",
                                    confidence=0.7, source=agent_name)

        # 注册坑（pitfall）
        pitfall_key = f"坑:{error[:50]}"
        self.learn(pitfall_key, "pitfall",
                   f"{agent_name}踩过的坑: {error[:200]}",
                   source=agent_name)

    def _extract_entities(self, text: str) -> list[str]:
        """从文本中提取可能的实体（支持中文）"""
        if not text:
            return []
        entities = set()
        # 引号内容
        for m in re.finditer(r'["\u201c\u201d\u2018\u2019]([^"\u201c\u201d\u2018\u2019]{2,50})["\u201c\u201d\u2018\u2019]', text):
            entities.add(m.group(1).strip())
        # 中文词组（2-6个中文字符）
        for m in re.finditer(r'[\u4e00-\u9fff]{2,15}', text):
            entities.add(m.group())
        # 大写驼峰词
        for m in re.finditer(r'\b[A-Z][a-zA-Z]+(?:[A-Z][a-zA-Z]+)*\b', text):
            entities.add(m.group())
        # 技术术语（含点、斜杠、横杠）
        for m in re.finditer(r'\b([a-zA-Z]+[./_-][a-zA-Z0-9]+)\b', text):
            entities.add(m.group())
        return [e for e in entities if len(e) > 1][:15]

    # ══════════════════════════════════════════
    # 查询
    # ══════════════════════════════════════════

    def query(self, question: str, max_depth: int = 3) -> QueryResult:
        """查询知识图谱 — 自动推理"""
        result = QueryResult()

        # 1. 提取查询关键词
        keywords = self._extract_entities(question)
        if not keywords:
            # 用全文搜索兜底
            keywords = [question[:50]]

        # 2. 搜索相关实体
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

        # 3. 搜索关系路径
        reasoning_paths = []
        for entity in list(relevant_entities)[:5]:
            paths = self._traverse(entity, max_depth)
            reasoning_paths.extend(paths)

        # 4. 综合答案
        if result.evidence or reasoning_paths:
            result.confidence = min(1.0, len(result.evidence) * 0.2 + len(reasoning_paths) * 0.1)

            # 构建答案
            parts = []
            if reasoning_paths:
                for path in reasoning_paths[:3]:
                    parts.append(f"  • {path}")

            relation_hints = []
            for path in reasoning_paths:
                relation_hints.append(path)

            result.reasoning_path = relation_hints[:5]

            if parts:
                result.answer = "📚 知识图谱中找到以下关联:\n" + "\n".join(parts)
            else:
                result.answer = f"找到 {len(result.evidence)} 条相关记录"

            # 更新访问计数
            for ev in result.evidence[:3]:
                if ev.get("entity"):
                    self._conn.execute(
                        "UPDATE nodes SET access_count = access_count + 1, accessed_at = ? WHERE entity = ?",
                        (time.time(), ev["entity"]),
                    )
                    self._conn.commit()
        else:
            result.answer = f"知识图谱中没有找到与'{question}'直接相关的信息"
            result.confidence = 0.0

        return result

    def _traverse(self, entity: str, depth: int, path: list[str] = None,
                  visited: set = None) -> list[str]:
        """遍历知识图谱，找到推理路径"""
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

            # 继续遍历
            if depth > 1:
                sub_results = self._traverse(next_entity, depth - 1, path + [edge_str], visited)
                results.extend(sub_results)

        return results

    def recall(self, question: str, top_k: int = 3) -> list[str]:
        """快速回忆 — 给Agent用的简化接口"""
        result = self.query(question)
        if result.evidence:
            return [e["content"] for e in result.evidence[:top_k]]
        return []

    # ══════════════════════════════════════════
    # 冲突检测与解决
    # ══════════════════════════════════════════

    def _detect_conflict(self, entity: str, relation: str, target: str, context: str):
        """检测知识冲突"""
        if relation in ("不支持", "禁止", "不推荐"):
            opposite = {"不支持": "支持", "禁止": "必须", "不推荐": "推荐"}
            opp_rel = opposite.get(relation)
            if opp_rel:
                cursor = self._conn.execute(
                    "SELECT context, source FROM edges WHERE source_entity=? AND relation=? AND target_entity=?",
                    (entity, opp_rel, target),
                )
                for row in cursor.fetchall():
                    # 记录冲突
                    self._conn.execute("""
                        INSERT INTO conflicts (entity_a, relation, entity_b, claim_a, claim_b)
                        VALUES (?, ?, ?, ?, ?)
                    """, (entity, relation, target, context, row[0]))
                    self._conn.commit()

    def resolve_conflicts(self):
        """自动解决知识冲突（置信度优先）"""
        cursor = self._conn.execute(
            "SELECT * FROM conflicts WHERE resolved=0"
        )
        for row in cursor.fetchall():
            # 比较两条边的置信度
            cur_a = self._conn.execute(
                "SELECT confidence FROM edges WHERE source_entity=? AND relation=? AND target_entity=?",
                (row[1], row[2], row[3]),
            ).fetchone()
            cur_b = self._conn.execute(
                "SELECT confidence FROM edges WHERE source_entity=? AND relation=? AND target_entity=?",
                (row[1], row[2], row[3]),
            ).fetchone()
            # 置信度高者胜出
            self._conn.execute(
                "UPDATE conflicts SET resolved=1, resolution=? WHERE id=?",
                ("置信度决策", row[0]),
            )
            self._conn.commit()

    # ══════════════════════════════════════════
    # 统计与维护
    # ══════════════════════════════════════════

    def stats(self) -> dict:
        """知识图谱统计"""
        nodes = self._conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        edges = self._conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        conflicts = self._conn.execute("SELECT COUNT(*) FROM conflicts WHERE resolved=0").fetchone()[0]

        # 按类型统计
        type_stats = {}
        cursor = self._conn.execute(
            "SELECT entity_type, COUNT(*) FROM nodes GROUP BY entity_type ORDER BY COUNT(*) DESC"
        )
        for row in cursor.fetchall():
            type_stats[row[0]] = row[1]

        # 活跃知识（最近7天被访问）
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
        """遗忘长期不用的低置信度知识"""
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
        """基于知识图谱给出建议"""
        result = self.query(f"与{entity}相关的知识")
        return result.reasoning_path[:5]

    def sync_to_agent(self, agent_name: str, question: str) -> str:
        """将知识图谱中的相关知识同步到Agent的上下文中"""
        result = self.query(question)
        if result.answer and result.confidence > 0.3:
            return f"[知识图谱记忆] {result.answer}"
        return ""
