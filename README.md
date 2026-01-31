<p align="center">
  <img src="https://img.shields.io/pypi/v/graphforge?style=for-the-badge" alt="PyPI version" />
  <img src="https://img.shields.io/badge/python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge" alt="License" />
</p>
<p align="center">
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

| | NetworkX | GraphForge | Production DBs (Neo4j, Memgraph) |
|:---|:---|:---|:---|
| **Durability** | Manual serialization | ✓ SQLite backend | ✓ Persistent |
| **Query language** | None | openCypher subset | Full Cypher |
| **Operational overhead** | Minimal | Minimal (embedded) | High (services, config) |
| **Notebook-friendly** | ✓ | ✓ | ✗ |
| **Iterative analysis** | ✓ | ✓ | Poor |

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

### Current Features

- **MATCH** (nodes, relationships, directionality) ✓
- **WHERE** (boolean logic, comparisons, property access) ✓
- **RETURN**, **LIMIT**, **SKIP**, **ORDER BY** ✓
- **Aggregations** (COUNT, SUM, AVG, MIN, MAX) ✓
- **Python builder API** for graph construction ✓
- **SQLite persistence** with WAL mode ✓

### Planned v1 Additions

- **CREATE**, **SET**, **DELETE**, **MERGE** (Cypher mutations)
- Optional Pydantic-backed data models for validation
- Transaction support with rollback

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

# Create a graph workbench
db = GraphForge()

# Create nodes with Python API
alice = db.create_node(['Person'], name='Alice', age=30, city='NYC')
bob = db.create_node(['Person'], name='Bob', age=25, city='NYC')
charlie = db.create_node(['Person'], name='Charlie', age=35, city='LA')

# Create relationships
db.create_relationship(alice, bob, 'KNOWS', since=2015)
db.create_relationship(alice, charlie, 'KNOWS', since=2018)

# Query with openCypher
results = db.execute("""
  MATCH (p:Person)
  WHERE p.age > 25
  RETURN p.name, p.city
  ORDER BY p.age
""")

for row in results:
    print(f"{row['p.name'].value} lives in {row['p.city'].value}")
```

**Persistence:** Graphs can persist across sessions using SQLite:

```python
# Create persistent graph
db = GraphForge("my-graph.db")

# ... create nodes and relationships ...

# Save to disk
db.close()

# Later: load the same graph
db = GraphForge("my-graph.db")  # All data is still there
```

> **Note:** GraphForge is in active development. The query engine is production-ready with 17 TCK compliance tests passing. SQLite persistence is now available.

---

## Design Principles

- **Spec-driven correctness** — openCypher semantics over performance.
- **Deterministic & reproducible** — Stable behavior across runs.
- **Inspectable** — Query plans, storage layout, and execution behavior are observable.
- **Replaceable internals** — Minimal operational overhead, stable APIs.

## Architecture

GraphForge is built on:
- **Parser:** Lark-based openCypher parser with full AST generation
- **Planner:** Logical plan generation (ScanNodes, ExpandEdges, Filter, Project, Sort, Aggregate)
- **Executor:** Pipeline-based query execution with streaming rows
- **Storage:** SQLite backend with WAL mode for ACID guarantees and zero-config durability

The architecture prioritizes correctness and developer experience over raw performance, with all components designed to be testable, inspectable, and replaceable.

---

## Links

- [Requirements document](docs/0-requirements.md) — Full scope, TCK strategy, and design rationale
- [openCypher AST spec](docs/open_cypher_ast_logical_plan_spec_v_1.md)
- [Runtime value model](docs/runtime_value_model_graph_execution_v_1.md)

---

## License

MIT © David Spencer
