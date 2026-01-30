# Lightweight openCypher-Compatible Graph Engine

## Requirements Document (Draft)

---

## 1. Purpose

This document defines the functional and non-functional requirements for a **lightweight, embedded, openCypher-compatible graph engine** designed specifically for **research, investigative, and analytical workflows** in Python-centric data science and machine learning environments.

**This project implements a declared subset of the openCypher specification, validated via the openCypher Technology Compatibility Kit (TCK), rather than claiming full language coverage.**

The system is intentionally scoped to support **graph materialization and graph analytics as intermediate analytical steps**, not as a long-lived production database. It provides a standardized, portable, and semantically correct way to work with graphs during information extraction, investigation, and exploratory analysis.

---

## 2. Standards & Compatibility

### 2.1 openCypher Alignment

The engine MUST:
- Parse and validate queries using the openCypher grammar
- Follow openCypher semantic rules for pattern matching, filtering, and projection
- Maintain compatibility with the openCypher Technology Compatibility Kit (TCK) for supported features

The engine MUST NOT:
- Introduce proprietary Cypher extensions in the core language
- Silently accept unsupported syntax or semantics

### 2.2 TCK Compliance Model

- The project SHALL define a clear **TCK feature coverage matrix**
- Each openCypher feature SHALL be explicitly categorized as:
  - Supported
  - Unsupported (with defined failure behavior)
- Unsupported features MUST:
  - Fail deterministically
  - Produce clear, descriptive, spec-aligned errors

---

## 3. Design Principles

- Embedded-first (no server or daemon)
- Local-first (single-node execution)
- Graph-native execution (no relational joins)
- Spec-driven correctness over performance
- Deterministic and reproducible results
- Inspectable storage and execution behavior
- Python-first developer experience

The design philosophy mirrors SQLite: minimal operational overhead, stable APIs, and replaceable internals.

---

## 4. Intended Usage & Scope

### 4.1 What This Project Is

This system provides a **graph workbench** for:
- Materializing extracted entities and relationships into a property graph
- Iteratively refining and revising that graph
- Querying and analyzing graph structure using openCypher

It is designed to live *inside* Python workflows such as:
- Notebooks
- Research scripts
- Agentic or LLM-driven pipelines

### 4.2 What This Project Is Not

This system is explicitly NOT:
- A data ingestion platform
- An information extraction system
- A production graph database
- A graph-serving backend
- A distributed or multi-tenant service

---

## 5. Canonical Workflow Pattern (Scoped)

This project operates exclusively as an **intermediate analytical layer**.

### Upstream Context (Out of Scope)

The following steps are assumed to occur outside this system:

1. Data ingestion from structured or unstructured sources
2. Entity and relationship extraction (including probabilistic or noisy outputs)

No assumptions are made about how entities or relationships are produced.

### Core Responsibility (In Scope)

#### 3. Graph Materialization

The system MUST support:
- Creation of nodes and relationships from extracted data
- Iterative updates, corrections, and revisions
- Durable but disposable graph persistence
- Multiple experimental or competing graph states

Graphs at this stage may be incomplete, inconsistent, or exploratory.

#### 4. Graph Exploration & Analytics

The system MUST support:
- Pattern matching using openCypher
- Structural exploration of graphs
- Identification of:
  - Variations
  - Outliers
  - Structural anomalies
  - Unexpected relationships

This phase is explicitly analytical and investigative.

### Downstream Context (Out of Scope)

The system does NOT handle:
- Final data curation or validation
- Long-term systems of record
- Production database serving
- Feature stores or ML model hosting

---

## 6. Data Model Requirements

### 6.1 Nodes

- Each node MUST have:
  - A unique internal identifier
  - Zero or more labels
  - Zero or more properties
- Node identity MUST be stable within a transaction

### 6.2 Relationships

- Each relationship MUST have:
  - A unique internal identifier
  - A source node
  - A destination node
  - Exactly one relationship type
  - Directionality
  - Zero or more properties

### 6.3 Properties

Properties MUST support openCypher value types:
- Integer
- Float
- Boolean
- String
- Null
- List
- Map

Null propagation and comparison semantics MUST follow the openCypher specification.

---

## 7. Data Models, Schemas, and Ontologies

### 7.1 Purpose

The system MUST support optional **data models** (also referred to as ontologies or schemas) that provide semantic structure over nodes and relationships without imposing rigid database-style schemas.

These models are intended to:
- Standardize meaning across investigative and extraction workflows
- Improve consistency in graph materialization
- Enable validation and tooling in Python-based environments
- Remain flexible enough for exploratory and probabilistic data

### 7.2 Compatibility Requirements

Data models MUST be expressible in formats compatible with:
- Pydantic models
- JSON Schema (draft-agnostic, best-effort)

This ensures interoperability with:
- Python data validation tooling
- LLM extraction pipelines
- External schema and ontology tooling

### 7.3 Scope of Enforcement

Data models:
- MUST be **optional**
- MUST NOT be required to create or query graphs
- MUST NOT prevent insertion of incomplete or uncertain data by default

Schema enforcement SHOULD be:
- Advisory rather than mandatory
- Configurable by the user (e.g. strict vs permissive modes)

### 7.4 Modeling Capabilities

Data models SHOULD be able to define:

- Node types (conceptual classes)
- Relationship types
- Allowed properties and value types
- Optional vs required properties
- Inheritance or specialization (where supported by the model format)

These models MAY be used to:
- Validate extracted entities and relationships
- Annotate nodes and relationships with semantic meaning
- Assist in query formulation and interpretation

### 7.5 Relationship to Cypher Semantics

Data models MUST:
- Remain orthogonal to openCypher semantics
- NOT alter Cypher query meaning or execution results
- Provide metadata and validation layers only

Cypher queries MUST operate on graph data regardless of whether a data model is present.

---

## 8. Query Language Requirements

## 7. Query Language Requirements

### 7.1 Supported Constructs (v1)

The engine MUST support the following openCypher constructs exactly as specified:

- MATCH (nodes, relationships, directionality)
- WHERE (boolean logic, comparisons, property access)
- RETURN (expressions, aliases, multiple projections)
- LIMIT
- SKIP

### 7.2 Unsupported Constructs (v1)

The following constructs MAY be parsed but MUST fail validation or execution:

- CREATE, DELETE, SET, MERGE
- OPTIONAL MATCH
- Variable-length paths
- Aggregations
- Subqueries
- Procedures

Failures MUST be deterministic and explicitly documented.

---

## 8. Execution Engine Requirements

The execution engine MUST:
- Operate on graph-native primitives
- Use adjacency-based traversal
- Implement operators for:
  - Node scanning
  - Relationship expansion
  - Filtering
  - Projection
  - Limiting
- Preserve openCypher semantics throughout execution

Query planning MAY be rule-based; cost-based planning is out of scope.

---

## 9. Storage Engine Requirements

The storage layer MUST:
- Be durable across crashes
- Support atomic commits
- Use WAL or equivalent journaling
- Support snapshot isolation for readers
- Store adjacency lists explicitly
- Preserve stable internal IDs

The storage engine MUST remain opaque to Cypher semantics.

---

## 10. Concurrency Model

- Single writer at a time
- Multiple concurrent readers
- Readers MUST see only committed state
- Writers MUST not observe partial writes

---

## 11. Python API Requirements

```python
rows = db.execute("""
MATCH (n:Person)
WHERE n.age > 30
RETURN n.name
LIMIT 5
""")
```

API guarantees:
- Synchronous execution
- Deterministic results
- Typed exceptions for parse, validation, and execution errors
- Reusable database handle

---

## 12. Testing & Validation

### 12.1 openCypher TCK Integration

- The openCypher TCK MUST be integrated into continuous integration (CI)
- TCK tests MUST be runnable in an automated, reproducible manner
- Each TCK test MUST be explicitly classified as:
  - **Pass** (fully supported and compliant)
  - **Skip** (feature intentionally unsupported)
  - **Expected Failure** (known limitation, documented)

A public **TCK Coverage Matrix** MUST be maintained and versioned with the codebase.

### 12.2 Regression Testing

- All supported openCypher features MUST have regression tests
- Regression tests MUST ensure semantic stability across releases
- Storage durability MUST be tested across process restarts

---

## 13. Non-Functional Requirements

### Performance

- Correctness prioritized over throughput
- Target scale (best effort):
  - ~10^6 nodes
  - ~10^7 relationships

### Portability

- macOS, Linux, Windows
- Python 3.10 or newer

### Observability

- Inspectable query plans
- Configurable debug logging
- Documented storage layout

---

## 14. Explicit Non-Goals

This system is NOT intended to:
- Fully implement the openCypher language
- Replace production graph databases
- Serve as a long-running graph service
- Achieve full TCK coverage in v1
- Support high-concurrency OLTP workloads
- Introduce Cypher dialect fragmentation

---

## 15. Success Criteria (v1)

The project is successful if:
- A user can materialize a graph from extracted entities and relationships
- Execute valid openCypher MATCH queries within the declared feature set
- Pass the corresponding subset of the openCypher TCK
- Persist graphs across restarts
- Use the system entirely embedded, without external services

---

## 16. Comparison to Existing Approaches

This project intentionally occupies a middle ground between in-memory graph libraries and production-scale graph databases. The following comparisons clarify why neither "just using NetworkX" nor running an external graph database fully satisfies the intended use cases.

---

### 16.1 Comparison: Using NetworkX Alone

**What NetworkX Provides**

NetworkX is an excellent Python library for:
- Graph algorithms (centrality, clustering, paths)
- Rapid prototyping
- In-memory graph manipulation

However, NetworkX is explicitly **not a graph engine**. It lacks several capabilities that are critical for investigative and analytical workflows at scale.

**Limitations of NetworkX for These Use Cases**

- No durable storage (graphs must be serialized manually)
- No standardized query language
- No declarative pattern matching
- No snapshot isolation or transactional semantics
- No schema or semantic enforcement
- Poor reproducibility across sessions without custom glue code

As a result, NetworkX graphs tend to become:
- Ephemeral
- Ad-hoc
- Difficult to share or reproduce
- Tightly coupled to specific scripts or notebooks

**How This Project Differs**

This system complements NetworkX rather than replacing it:
- Provides durable, inspectable graph storage
- Supports declarative pattern matching via openCypher
- Enforces consistent graph semantics
- Enables reproducible analytical workflows

NetworkX is expected to remain a **downstream consumer** of graphs produced by this system, particularly for algorithmic analysis.

---

### 16.2 Comparison: External Graph Databases (Neo4j, Memgraph, etc.)

**What External Graph Databases Provide**

Production graph databases excel at:
- Long-lived, authoritative graph storage
- High-performance traversals
- Concurrent multi-user access
- Operational robustness

They are optimized for **serving applications**, not exploratory analysis.

**Limitations in Research & Investigative Contexts**

For Python-based research workflows, external graph databases introduce significant friction:

- Require separate processes or services
- Impose operational overhead (installation, configuration, lifecycle)
- Break notebook-local execution models
- Encourage premature schema and data-model finalization
- Make iterative or disposable graphs costly to manage

These systems assume that the graph is:
- Clean
- Stable
- Long-lived
- Worth operational investment

This assumption does not hold during information extraction or investigative analysis.

**How This Project Differs**

This system:
- Runs entirely embedded within Python
- Requires no external services
- Encourages iterative, revisable graph construction
- Treats graphs as analytical artifacts, not systems of record
- Optimizes for semantic correctness and reproducibility over throughput

Export to production graph databases is explicitly supported *after* analytical refinement.

---

### 16.3 Summary Comparison

| Dimension | NetworkX | External Graph DBs | This Project |
|--------|----------|-------------------|--------------|
| Execution Model | In-memory | External service | Embedded |
| Durability | None (manual) | Persistent | Persistent |
| Query Language | None | Cypher | openCypher |
| Graph Semantics | Weakly enforced | Strong | Strong |
| Iterative Analysis | Excellent | Poor | Excellent |
| Operational Overhead | Minimal | High | Minimal |
| Notebook-Friendly | Yes | No | Yes |
| Production Serving | No | Yes | No |

This project exists specifically to fill the analytical gap between these two extremes.

---

## 17. Cypher Support Clarification (Non-Normative)

To avoid ambiguity, the following clarifications apply:

- openCypher compatibility refers to **semantic correctness for supported features**, not total language coverage
- Unsupported clauses and expressions MUST fail explicitly and deterministically
- The absence of a feature does not imply partial or degraded semantics for supported features

Users should expect:
- Strong semantic guarantees within the supported subset
- Clear error messages for unsupported syntax
- Gradual, explicit expansion of Cypher coverage over time

---

## 18. Why This Exists (README Excerpt)

### The Problem

Modern data science, machine learning, and investigative workflows increasingly rely on **entities and relationships** extracted from messy, probabilistic sources: text, tables, OCR, logs, and LLM outputs. While these workflows naturally produce **graph-shaped data**, practitioners are forced into poor tooling choices:

- In-memory graph libraries (e.g. NetworkX) that lack durability, semantics, and declarative querying
- Production graph databases that impose operational overhead, rigidity, and premature commitment

As a result, graph-based analysis during research and investigation is often ad-hoc, non-reproducible, and tightly coupled to one-off scripts.

---

### The Gap

There is a missing middle layer between:

- **Ephemeral in-memory graphs** used for algorithms
- **Production graph databases** used as systems of record

This gap is where most investigative and information-extraction work actually happens.

Researchers and ML engineers need a way to:
- Materialize extracted entities and relationships into a graph
- Iteratively revise and explore that graph
- Ask declarative, pattern-based questions
- Do all of this **inside Python**, without running external services

---

### The Idea

This project provides a **lightweight, embedded, openCypher-compatible graph engine** designed specifically for that gap.

It is:
- Embedded and local-first (no server)
- Graph-native (adjacency-based execution)
- Declarative (openCypher subset)
- Durable but disposable
- Designed for analytical, not operational, workloads

Rather than replacing production graph databases, it acts as a **graph workbench**:

- Build and revise graphs during extraction and investigation
- Explore structure, patterns, and anomalies
- Export refined results into systems like Neo4j or Memgraph *after* analysis

---

### What This Is (and Is Not)

**This is:**
- A standardized, portable environment for graph-based analysis
- A Cypher-compatible execution engine for research workflows
- A bridge between extraction pipelines and production systems

**This is not:**
- A production graph database
- A high-concurrency graph service
- A replacement for Neo4j, Memgraph, or TigerGraph

---

### Why openCypher

openCypher provides a widely understood, declarative way to reason about graphs.

By aligning with the openCypher specification and validating behavior with the openCypher TCK (for supported features), this project ensures:
- Semantic correctness
- Portability of queries
- Low friction when moving results to production systems

---

### Philosophy

> We are not building a database for applications.
> We are building a graph execution environment for thinking.

---

## 19. Future Considerations (Non-Binding)

- Incremental TCK coverage expansion
- Write support (CREATE, MERGE)
- Aggregations and grouping
- Variable-length path traversal
- Native execution core
- Interoperability with in-memory graph libraries

