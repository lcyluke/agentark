#!/usr/bin/env python3
"""Seed the Apex Knowledge Graph with foundational best practices.

Run:  python scripts/seed_knowledge.py

This populates the KG with curated knowledge across several domains:
  - Python best practices
  - Docker patterns
  - API design patterns
  - Agent development patterns
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so we can import apex.*
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from apex.core.knowledge import KnowledgeGraph


def seed(kg: KnowledgeGraph) -> None:
    """Populate the knowledge graph with curated seed data."""

    # ──────────────────────────────────────────────────────────────
    # Python Best Practices
    # ──────────────────────────────────────────────────────────────
    kg.learn("PythonBestPractices", "category",
             "Core Python development best practices", source="seed")
    kg.learn("AvoidMutableDefaults", "rule",
             "Never use mutable default arguments (list/dict/set); use None + guard instead",
             source="seed")
    kg.learn("UsePathlib", "rule",
             "Use pathlib.Path for filesystem operations instead of os.path / string munging",
             source="seed")
    kg.learn("TypeHints", "rule",
             "Always add type hints to function signatures; use from __future__ import annotations",
             source="seed")
    kg.learn("ContextManagers", "rule",
             "Use with statements for resource management (files, locks, connections)",
             source="seed")
    kg.learn("Dataclasses", "rule",
             "Prefer dataclasses over manual __init__ for data-holding classes",
             source="seed")
    kg.learn("ListCompOverLoops", "rule",
             "Prefer list comprehensions and generator expressions over manual for-loops",
             source="seed")
    kg.learn("EarlyReturns", "rule",
             "Use early returns / guard clauses to flatten nested conditionals",
             source="seed")
    kg.learn("EnumForConstants", "rule",
             "Use enum.Enum for fixed sets of constants instead of string literals",
             source="seed")
    kg.learn("LoggingNotPrint", "rule",
             "Use the logging module instead of print() for production code",
             source="seed")
    kg.learn("FStrings", "rule",
             "Use f-strings for string formatting (Python 3.6+)",
             source="seed")

    # Relationships — Python best practices
    kg.relate("AvoidMutableDefaults", "belongs_to", "PythonBestPractices",
              context="function design", source="seed")
    kg.relate("UsePathlib", "belongs_to", "PythonBestPractices",
              context="I/O operations", source="seed")
    kg.relate("TypeHints", "belongs_to", "PythonBestPractices",
              context="code quality", source="seed")
    kg.relate("ContextManagers", "belongs_to", "PythonBestPractices",
              context="resource management", source="seed")
    kg.relate("Dataclasses", "belongs_to", "PythonBestPractices",
              context="data modeling", source="seed")
    kg.relate("ListCompOverLoops", "belongs_to", "PythonBestPractices",
              context="performance & readability", source="seed")
    kg.relate("EarlyReturns", "belongs_to", "PythonBestPractices",
              context="code style", source="seed")
    kg.relate("EnumForConstants", "belongs_to", "PythonBestPractices",
              context="type safety", source="seed")
    kg.relate("LoggingNotPrint", "belongs_to", "PythonBestPractices",
              context="production readiness", source="seed")
    kg.relate("FStrings", "belongs_to", "PythonBestPractices",
              context="string formatting", source="seed")

    # ──────────────────────────────────────────────────────────────
    # Docker Patterns
    # ──────────────────────────────────────────────────────────────
    kg.learn("DockerPatterns", "category",
             "Container and Dockerfile best practices", source="seed")
    kg.learn("MultiStageBuilds", "pattern",
             "Use multi-stage builds (FROM ... AS builder, final minimal image) to reduce image size",
             source="seed")
    kg.learn("HealthChecks", "pattern",
             "Always define HEALTHCHECK in Dockerfile for container orchestration",
             source="seed")
    kg.learn("NonRootUser", "pattern",
             "Run containers as non-root user (USER 1000) for security",
             source="seed")
    kg.learn("LayerCaching", "pattern",
             "Order Dockerfile commands from least to most frequently changing to maximise layer cache hits",
             source="seed")
    kg.learn("SpecificBaseTags", "pattern",
             "Pin base image tags (python:3.11-slim) instead of using 'latest'",
             source="seed")
    kg.learn(".dockerignore", "pattern",
             "Always include a .dockerignore file to exclude node_modules, .git, __pycache__",
             source="seed")
    kg.learn("OneProcessPerContainer", "pattern",
             "Run a single process per container; use docker-compose for multi-service apps",
             source="seed")

    kg.relate("MultiStageBuilds", "belongs_to", "DockerPatterns",
              context="image optimization", source="seed")
    kg.relate("HealthChecks", "belongs_to", "DockerPatterns",
              context="reliability", source="seed")
    kg.relate("NonRootUser", "belongs_to", "DockerPatterns",
              context="security", source="seed")
    kg.relate("LayerCaching", "belongs_to", "DockerPatterns",
              context="build performance", source="seed")
    kg.relate("SpecificBaseTags", "belongs_to", "DockerPatterns",
              context="reproducibility", source="seed")
    kg.relate(".dockerignore", "belongs_to", "DockerPatterns",
              context="build context", source="seed")
    kg.relate("OneProcessPerContainer", "belongs_to", "DockerPatterns",
              context="architecture", source="seed")

    # ──────────────────────────────────────────────────────────────
    # API Design Patterns
    # ──────────────────────────────────────────────────────────────
    kg.learn("APIDesignPatterns", "category",
             "RESTful and general API design best practices", source="seed")
    kg.learn("RestfulNaming", "rule",
             "Use nouns for resources (/users, /orders), HTTP verbs for actions (GET, POST, PUT, DELETE)",
             source="seed")
    kg.learn("ConsistentErrorResponses", "rule",
             "Return consistent error JSON: {error: {code, message, details}}",
             source="seed")
    kg.learn("Pagination", "rule",
             "Always paginate list endpoints with cursor or offset/limit; return next token",
             source="seed")
    kg.learn("InputValidation", "rule",
             "Validate all inputs at the API boundary; return 400 with actionable error messages",
             source="seed")
    kg.learn("SemanticVersioning", "rule",
             "Version your API (v1, v2) and follow semver for changes",
             source="seed")
    kg.learn("RateLimiting", "rule",
             "Implement rate limiting with X-RateLimit-* headers to protect against abuse",
             source="seed")
    kg.learn("Idempotency", "rule",
             "Use idempotency keys on POST/PATCH to handle safe retries",
             source="seed")

    kg.relate("RestfulNaming", "belongs_to", "APIDesignPatterns",
              context="routing", source="seed")
    kg.relate("ConsistentErrorResponses", "belongs_to", "APIDesignPatterns",
              context="error handling", source="seed")
    kg.relate("Pagination", "belongs_to", "APIDesignPatterns",
              context="scalability", source="seed")
    kg.relate("InputValidation", "belongs_to", "APIDesignPatterns",
              context="security", source="seed")
    kg.relate("SemanticVersioning", "belongs_to", "APIDesignPatterns",
              context="versioning", source="seed")
    kg.relate("RateLimiting", "belongs_to", "APIDesignPatterns",
              context="security", source="seed")
    kg.relate("Idempotency", "belongs_to", "APIDesignPatterns",
              context="reliability", source="seed")

    # ──────────────────────────────────────────────────────────────
    # Agent Development Patterns
    # ──────────────────────────────────────────────────────────────
    kg.learn("AgentDevelopmentPatterns", "category",
             "Best practices for building and deploying AI agents", source="seed")
    kg.learn("StructuredOutputs", "rule",
             "Always request structured JSON output from LLMs (response_format=json) for reliable parsing",
             source="seed")
    kg.learn("RetryBackoff", "rule",
             "Implement exponential backoff with jitter for LLM API calls",
             source="seed")
    kg.learn("SystemPromptFoundation", "rule",
             "Write a strong system prompt that defines role, constraints, output format, and tone",
             source="seed")
    kg.learn("ToolUseOverPrompting", "rule",
             "Prefer tool/function calling over asking the model to output structured text",
             source="seed")
    kg.learn("ContextWindowBudget", "rule",
             "Monitor and budget token usage; summarise or prune conversation history proactively",
             source="seed")
    kg.learn("SeparationOfConcerns", "rule",
             "Separate agent logic from tool implementation; let agents focus on reasoning",
             source="seed")
    kg.learn("Observability", "rule",
             "Log every LLM call (prompt, response, latency, tokens) for debugging and cost tracking",
             source="seed")
    kg.learn("HumanInTheLoop", "rule",
             "Include human approval gates for destructive actions (deployments, deletions, payments)",
             source="seed")
    kg.learn("KnowledgeGraphSeed", "rule",
             "Seed the KG with domain knowledge so the agent doesn't have to learn from scratch",
             source="seed")

    kg.relate("StructuredOutputs", "belongs_to", "AgentDevelopmentPatterns",
              context="reliability", source="seed")
    kg.relate("RetryBackoff", "belongs_to", "AgentDevelopmentPatterns",
              context="resilience", source="seed")
    kg.relate("SystemPromptFoundation", "belongs_to", "AgentDevelopmentPatterns",
              context="agent behavior", source="seed")
    kg.relate("ToolUseOverPrompting", "belongs_to", "AgentDevelopmentPatterns",
              context="architecture", source="seed")
    kg.relate("ContextWindowBudget", "belongs_to", "AgentDevelopmentPatterns",
              context="cost management", source="seed")
    kg.relate("SeparationOfConcerns", "belongs_to", "AgentDevelopmentPatterns",
              context="architecture", source="seed")
    kg.relate("Observability", "belongs_to", "AgentDevelopmentPatterns",
              context="operations", source="seed")
    kg.relate("HumanInTheLoop", "belongs_to", "AgentDevelopmentPatterns",
              context="safety", source="seed")
    kg.relate("KnowledgeGraphSeed", "belongs_to", "AgentDevelopmentPatterns",
              context="knowledge", source="seed")

    # ──────────────────────────────────────────────────────────────
    # Cross-domain connections
    # ──────────────────────────────────────────────────────────────
    kg.relate("MultiStageBuilds", "supports", "APIDesignPatterns",
              context="deploying API containers efficiently", source="seed")
    kg.relate("HealthChecks", "supports", "HumanInTheLoop",
              context="automated health verification", source="seed")
    kg.relate("LoggingNotPrint", "supports", "Observability",
              context="structured logging feeds observability", source="seed")
    kg.relate("TypeHints", "recommends", "Dataclasses",
              context="both improve code clarity and IDE support", source="seed")
    kg.relate("ContextManagers", "recommends", "OneProcessPerContainer",
              context="proper resource cleanup in single-process containers", source="seed")
    kg.relate("InputValidation", "recommends", "ConsistentErrorResponses",
              context="validation errors should follow the consistent error schema", source="seed")
    kg.relate("SystemPromptFoundation", "supports", "StructuredOutputs",
              context="system prompt should request structured output format", source="seed")


def main() -> None:
    kg = KnowledgeGraph()
    seed(kg)
    stats = kg.stats()
    print("✅ Knowledge Graph seeded successfully!")
    print(f"   Nodes: {stats['total_nodes']}")
    print(f"   Edges: {stats['total_edges']}")
    print(f"   Type distribution: {stats['type_distribution']}")


if __name__ == "__main__":
    main()
