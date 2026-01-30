<p align="center">
  <img src="https://img.shields.io/pypi/v/graphforge?style=for-the-badge" alt="PyPI version" />
  <img src="https://img.shields.io/badge/python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge" alt="License" />
  <img src="https://img.shields.io/badge/pydantic-2.6+-e92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic" />
  <img src="https://img.shields.io/badge/openCypher%20TCK%20target-2024.2-6c4f7c?style=for-the-badge" alt="openCypher TCK target" />
</p>

<h1 align="center">GraphForge</h1>
<p align="center">
  <strong>Composable graph tooling for analysis, construction, and refinement</strong>
</p>

<p align="center">
  A lightweight, embedded, openCypher-compatible graph engine for research and investigative workflows
</p>

---

## Why GraphForge?

Modern data science and ML workflows increasingly produce **graph-shaped data**—entities and relationships extracted from text, tables, and LLM outputs. Yet practitioners face a painful choice:

| | NetworkX | Production DBs (Neo4j, Memgraph) |
|:---|:---|:---|
| **Durability** | Manual serialization only | ✓ Persistent |
| **Query language** | None | Cypher |
| **Operational overhead** | Minimal | High (services, config) |
| **Notebook-friendly** | ✓ | ✗ |
| **Iterative analysis** | ✓ | Poor |

**GraphForge** fills the gap—embedded, durable, and declarative—without running external services.

> *We are not building a database for applications.*  
> *We are building a graph execution environment for thinking.*

---

## Features

- **Embedded & local-first** — No server, no daemon. Runs entirely inside your Python process.
- **openCypher subset** — Declarative pattern matching with semantic correctness validated against the TCK.
- **Graph-native execution** — Adjacency-based traversal, not relational joins.
- **Durable but disposable** — Persist graphs across restarts; treat them as analytical artifacts.
- **Python-first** — Designed for notebooks, scripts, and agentic pipelines.

### Planned v1 Scope

- **MATCH** (nodes, relationships, directionality)
- **WHERE** (boolean logic, comparisons, property access)
- **RETURN**, **LIMIT**, **SKIP**
- Node and relationship materialization
- Optional Pydantic-backed data models for validation

---

## Installation

```bash
# Using uv (recommended)
uv add graphforge

# Using pip
pip install graphforge
```

**Requirements:** Python 3.10+

---

## Quick Start

```python
from graphforge import GraphForge

# Create a graph (API in development)
db = GraphForge("my-graph.db")

# Execute openCypher queries
rows = db.execute("""
  MATCH (n:Person)
  WHERE n.age > 30
  RETURN n.name
  LIMIT 5
""")
```

> **Note:** GraphForge is early in development. The core API and storage layer are being built out per the [requirements document](docs/0-requirements.md).

---

## Design Principles

- **Spec-driven correctness** — openCypher semantics over performance.
- **Deterministic & reproducible** — Stable behavior across runs.
- **Inspectable** — Query plans, storage layout, and execution behavior are observable.
- **Replaceable internals** — Minimal operational overhead, stable APIs.

---

## Links

- [Requirements document](docs/0-requirements.md) — Full scope, TCK strategy, and design rationale
- [openCypher AST spec](docs/open_cypher_ast_logical_plan_spec_v_1.md)
- [Runtime value model](docs/runtime_value_model_graph_execution_v_1.md)

---

## License

MIT © David Spencer
