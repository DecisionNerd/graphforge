# GraphForge Architecture Overview

**Version:** 0.1.1
**Last Updated:** 2026-01-30
**Status:** Phase 4 Complete (TCK Compliant Query Engine)

---

## Executive Summary

GraphForge is an embedded, openCypher-compatible graph engine designed as a "graph workbench" for research, investigative, and analytical workflows. The architecture prioritizes:

1. **Correctness** over performance (strict openCypher TCK compliance)
2. **Developer experience** (Python-first, zero-config, notebook-friendly)
3. **Simplicity** (embedded, single-file storage, no server)
4. **Inspectability** (observable query plans, transparent storage)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       GraphForge API                         │
│                    (src/graphforge/api.py)                   │
│                                                               │
│  db = GraphForge("my-graph.db")                              │
│  results = db.execute("MATCH (n:Person) RETURN n")          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │         Query Processing Pipeline       │
         └────────────────────────────────────────┘
                              │
         ┌────────────────────┼─────────────────────┐
         │                    │                     │
         ▼                    ▼                     ▼
    ┌────────┐          ┌─────────┐          ┌──────────┐
    │ Parser │          │ Planner │          │ Executor │
    └────────┘          └─────────┘          └──────────┘
         │                    │                     │
         ▼                    ▼                     ▼
    ┌────────┐          ┌─────────┐          ┌──────────┐
    │  AST   │   ────▶  │ Logical │   ────▶  │  Result  │
    │        │          │  Plan   │          │   Rows   │
    └────────┘          └─────────┘          └──────────┘
                                                    │
                                                    ▼
                                            ┌──────────────┐
                                            │    Graph     │
                                            │   Storage    │
                                            └──────────────┘
                                                    │
                                                    ▼
                                            ┌──────────────┐
                                            │    SQLite    │
                                            │  (WAL Mode)  │
                                            └──────────────┘
```

---

## Component Details

### 1. GraphForge API (`src/graphforge/api.py`)

**Purpose:** High-level user-facing interface

**Responsibilities:**
- Database lifecycle management (open/close)
- Query execution orchestration
- Error handling and exception mapping

**Example:**
```python
from graphforge import GraphForge

# In-memory graph (current implementation)
db = GraphForge()

# Durable graph (future: Phase 5)
db = GraphForge("analysis.db")

# Execute queries
results = db.execute("""
    MATCH (p:Person)-[:KNOWS]->(f:Person)
    WHERE p.age > 30
    RETURN p.name, f.name
    ORDER BY p.name
    LIMIT 10
""")

for row in results:
    print(row["p.name"], row["f.name"])
```

---

### 2. Parser (`src/graphforge/parser/`)

**Purpose:** Convert Cypher query strings to Abstract Syntax Tree (AST)

**Implementation:** Lark parser with EBNF grammar

**Files:**
- `parser.py` - Lark transformer that builds AST nodes
- `cypher.lark` - openCypher grammar definition

**Supported Syntax (v1.0+):**
- MATCH patterns (nodes, relationships, directionality)
- WHERE clause (boolean logic, comparisons, property access)
- RETURN clause with aliasing (AS keyword)
- ORDER BY clause (single/multi-key, ASC/DESC)
- SKIP and LIMIT
- Aggregation functions (COUNT, SUM, AVG, MIN, MAX)

**Example AST:**
```python
# Query: MATCH (n:Person) WHERE n.age > 30 RETURN n.name AS name

CypherQuery(
    clauses=[
        MatchClause(
            patterns=[[
                NodePattern(
                    variable='n',
                    labels=['Person'],
                    properties={}
                )
            ]]
        ),
        WhereClause(
            predicate=Comparison(
                left=PropertyAccess(variable='n', property='age'),
                op='>',
                right=Literal(value=CypherInt(30))
            )
        ),
        ReturnClause(
            items=[
                ReturnItem(
                    expression=PropertyAccess(variable='n', property='name'),
                    alias='name'
                )
            ]
        )
    ]
)
```

**See:** `docs/open_cypher_ast_logical_plan_spec_v_1.md`

---

### 3. Planner (`src/graphforge/planner/`)

**Purpose:** Convert AST to executable logical plan

**Implementation:** Rule-based planner (no cost-based optimization)

**Files:**
- `planner.py` - AST → Logical Plan conversion
- `operators.py` - Logical plan operator definitions

**Logical Operators:**
```python
@dataclass
class ScanNodes:
    """Scan all nodes or nodes by label."""
    variable: str
    labels: list[str] | None

@dataclass
class ExpandEdges:
    """Traverse relationships."""
    src_var: str
    edge_var: str | None
    dst_var: str
    edge_types: list[str]
    direction: str  # 'OUT', 'IN', 'UNDIRECTED'

@dataclass
class Filter:
    """Apply WHERE predicate."""
    predicate: Any  # Expression AST node

@dataclass
class Sort:
    """Sort by expressions (ORDER BY)."""
    items: list[OrderByItem]
    return_items: list[ReturnItem] | None  # For alias resolution

@dataclass
class Aggregate:
    """Group and aggregate (implicit GROUP BY)."""
    grouping_exprs: list[Any]
    agg_exprs: list[FunctionCall]
    return_items: list[ReturnItem]

@dataclass
class Project:
    """Evaluate RETURN expressions."""
    items: list[ReturnItem]

@dataclass
class Skip:
    """Skip first N rows."""
    count: int

@dataclass
class Limit:
    """Limit to N rows."""
    count: int
```

**Operator Ordering (Critical for Semantics):**
1. MATCH (ScanNodes, ExpandEdges)
2. WHERE (Filter)
3. ORDER BY (Sort) - *before* RETURN to access all variables
4. RETURN (Project or Aggregate)
5. SKIP/LIMIT

**Example Plan:**
```python
# Query: MATCH (n:Person) WHERE n.age > 30 RETURN n.name LIMIT 5

[
    ScanNodes(variable='n', labels=['Person']),
    Filter(predicate=Comparison(...)),
    Project(items=[ReturnItem(...)]),
    Limit(count=5)
]
```

**See:** `docs/open_cypher_ast_logical_plan_spec_v_1.md`

---

### 4. Executor (`src/graphforge/executor/`)

**Purpose:** Execute logical plans against graph storage

**Implementation:** Pipeline architecture with streaming rows

**Files:**
- `executor.py` - Main execution engine
- `evaluator.py` - Expression evaluation with NULL propagation

**Execution Model:**
```python
class QueryExecutor:
    def execute(self, operators: list) -> list[dict]:
        """Stream rows through operator pipeline."""
        rows = [ExecutionContext()]  # Start with empty context

        for op in operators:
            rows = self._execute_operator(op, rows)

        return rows
```

**ExecutionContext:**
```python
class ExecutionContext:
    """Variable bindings during query execution."""
    bindings: dict[str, Any]  # Variable name → CypherValue | NodeRef | EdgeRef

    def bind(self, name: str, value: Any) -> None:
        self.bindings[name] = value

    def get(self, name: str) -> Any:
        return self.bindings.get(name)
```

**Operator Execution Examples:**

```python
def _execute_scan(self, op: ScanNodes, input_rows):
    """Scan nodes and bind to variable."""
    result = []
    for ctx in input_rows:
        nodes = self.graph.get_nodes_by_label(op.labels[0]) if op.labels else self.graph.get_all_nodes()
        for node in nodes:
            new_ctx = ExecutionContext()
            new_ctx.bindings = dict(ctx.bindings)
            new_ctx.bind(op.variable, node)
            result.append(new_ctx)
    return result

def _execute_filter(self, op: Filter, input_rows):
    """Filter rows by predicate."""
    result = []
    for ctx in input_rows:
        value = evaluate_expression(op.predicate, ctx)
        if isinstance(value, CypherBool) and value.value:
            result.append(ctx)
    return result

def _execute_sort(self, op: Sort, input_rows):
    """Sort rows by expressions (with NULL handling)."""
    # Pre-evaluate RETURN aliases for ORDER BY reference
    extended_rows = []
    for ctx in input_rows:
        extended_ctx = ExecutionContext()
        extended_ctx.bindings = dict(ctx.bindings)
        if op.return_items:
            for return_item in op.return_items:
                if return_item.alias and not isinstance(return_item.expression, FunctionCall):
                    value = evaluate_expression(return_item.expression, ctx)
                    extended_ctx.bind(return_item.alias, value)
        extended_rows.append(extended_ctx)

    # Sort using multi-key comparison
    sorted_rows = sorted(extended_rows, key=cmp_to_key(multi_key_compare))

    # Map back to original contexts
    return [original_context_for(row) for row in sorted_rows]
```

**NULL Handling:**
- Three-valued logic (TRUE, FALSE, NULL)
- NULL comparisons return NULL
- WHERE filters out NULL predicates
- Sorting: ASC puts NULLs last, DESC puts NULLs first

**See:** `docs/runtime_value_model_graph_execution_v_1.md`

---

### 5. Graph Storage (`src/graphforge/storage/`)

**Current Implementation:** In-memory storage (Phase 1-4)

**Future Implementation:** SQLite backend (Phase 5)

#### In-Memory Graph (Current)

**File:** `storage/memory.py`

```python
class Graph:
    """In-memory graph storage with adjacency lists."""

    def __init__(self):
        self.nodes: dict[int, NodeRef] = {}
        self.edges: dict[int, EdgeRef] = {}
        self.adjacency_out: dict[int, list[int]] = {}  # node_id → [edge_ids]
        self.adjacency_in: dict[int, list[int]] = {}
        self.label_index: dict[str, set[int]] = {}

    def add_node(self, node: NodeRef) -> None:
        self.nodes[node.id] = node
        for label in node.labels:
            self.label_index.setdefault(label, set()).add(node.id)

    def get_outgoing_edges(self, node_id: int) -> list[EdgeRef]:
        edge_ids = self.adjacency_out.get(node_id, [])
        return [self.edges[eid] for eid in edge_ids]
```

#### SQLite Backend (Phase 5 - Planned)

**Architecture Decision:** Use SQLite for persistence (see `docs/storage-architecture-analysis.md`)

**Schema Design:**
```sql
-- Enable WAL mode for concurrency
PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
PRAGMA foreign_keys=ON;

-- Nodes table
CREATE TABLE nodes (
    id INTEGER PRIMARY KEY,
    labels BLOB,        -- MessagePack: frozenset(['Person', 'Employee'])
    properties BLOB     -- MessagePack: {'name': 'Alice', 'age': 30}
);

-- Edges table
CREATE TABLE edges (
    id INTEGER PRIMARY KEY,
    type TEXT NOT NULL,
    src_id INTEGER NOT NULL,
    dst_id INTEGER NOT NULL,
    properties BLOB,
    FOREIGN KEY (src_id) REFERENCES nodes(id),
    FOREIGN KEY (dst_id) REFERENCES nodes(id)
);

-- Adjacency lists (explicit storage for graph-native traversal)
CREATE TABLE adjacency_out (
    node_id INTEGER NOT NULL,
    edge_id INTEGER NOT NULL,
    PRIMARY KEY (node_id, edge_id),
    FOREIGN KEY (node_id) REFERENCES nodes(id),
    FOREIGN KEY (edge_id) REFERENCES edges(id)
);

CREATE TABLE adjacency_in (
    node_id INTEGER NOT NULL,
    edge_id INTEGER NOT NULL,
    PRIMARY KEY (node_id, edge_id),
    FOREIGN KEY (node_id) REFERENCES nodes(id),
    FOREIGN KEY (edge_id) REFERENCES edges(id)
);

-- Indexes for performance
CREATE INDEX idx_nodes_labels ON nodes(labels);
CREATE INDEX idx_edges_type ON edges(type);
CREATE INDEX idx_edges_src ON edges(src_id);
CREATE INDEX idx_edges_dst ON edges(dst_id);
```

**Storage Backend Interface:**
```python
class StorageBackend(Protocol):
    """Storage backend interface (replaceable internals)."""

    def add_node(self, node: NodeRef) -> None: ...
    def add_edge(self, edge: EdgeRef) -> None: ...
    def get_node(self, node_id: int) -> NodeRef | None: ...
    def get_all_nodes(self) -> list[NodeRef]: ...
    def get_nodes_by_label(self, label: str) -> list[NodeRef]: ...
    def get_outgoing_edges(self, node_id: int) -> list[EdgeRef]: ...
    def get_incoming_edges(self, node_id: int) -> list[EdgeRef]: ...

    # Transaction support
    def begin_transaction(self) -> None: ...
    def commit_transaction(self) -> None: ...
    def rollback_transaction(self) -> None: ...
```

**SQLite Implementation:**
```python
class SQLiteBackend(StorageBackend):
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def add_node(self, node: NodeRef) -> None:
        labels_blob = msgpack.packb(list(node.labels))
        props_blob = msgpack.packb({k: serialize_cypher_value(v) for k, v in node.properties.items()})

        self.conn.execute(
            "INSERT INTO nodes (id, labels, properties) VALUES (?, ?, ?)",
            (node.id, labels_blob, props_blob)
        )

    def get_outgoing_edges(self, node_id: int) -> list[EdgeRef]:
        cursor = self.conn.execute("""
            SELECT e.id, e.type, e.src_id, e.dst_id, e.properties
            FROM edges e
            JOIN adjacency_out a ON e.id = a.edge_id
            WHERE a.node_id = ?
        """, (node_id,))

        return [self._edge_from_row(row) for row in cursor.fetchall()]
```

**Concurrency Model:**
- SQLite WAL mode: Single writer, multiple readers
- Readers see consistent snapshot (snapshot isolation)
- Writers don't block readers
- Automatic crash recovery

**See:** `docs/storage-architecture-analysis.md`

---

## Data Model

### CypherValue Types (`src/graphforge/types/values.py`)

```python
@dataclass
class CypherInt(CypherValue):
    value: int

@dataclass
class CypherFloat(CypherValue):
    value: float

@dataclass
class CypherString(CypherValue):
    value: str

@dataclass
class CypherBool(CypherValue):
    value: bool

@dataclass
class CypherNull(CypherValue):
    pass

@dataclass
class CypherList(CypherValue):
    value: list[CypherValue]

@dataclass
class CypherMap(CypherValue):
    value: dict[str, CypherValue]
```

**Operations:**
- Comparison: `less_than()`, `equals()`
- Arithmetic: `add()`, `subtract()`, `multiply()`, `divide()`
- NULL propagation throughout

### Graph Elements (`src/graphforge/types/graph.py`)

```python
@dataclass(frozen=True)
class NodeRef:
    """Node reference with identity semantics."""
    id: int
    labels: frozenset[str]
    properties: dict[str, CypherValue]

    def __hash__(self) -> int:
        return hash(self.id)  # Identity by ID

@dataclass(frozen=True)
class EdgeRef:
    """Edge reference with identity semantics."""
    id: int
    type: str
    src: NodeRef
    dst: NodeRef
    properties: dict[str, CypherValue]

    def __hash__(self) -> int:
        return hash(self.id)  # Identity by ID
```

**Design:** Immutable, hashable, identity-based equality

---

## Query Execution Flow (Example)

**Query:**
```cypher
MATCH (p:Person)-[:KNOWS]->(f:Person)
WHERE p.age > 30 AND f.age < p.age
RETURN p.name AS person, f.name AS friend, p.age - f.age AS age_diff
ORDER BY age_diff DESC
LIMIT 5
```

**1. Parse → AST:**
```python
CypherQuery(
    clauses=[
        MatchClause(...),
        WhereClause(...),
        ReturnClause(...),
        OrderByClause(...),
        LimitClause(...)
    ]
)
```

**2. Plan → Logical Operators:**
```python
[
    ScanNodes(variable='p', labels=['Person']),
    ExpandEdges(src_var='p', edge_var=None, dst_var='f', edge_types=['KNOWS'], direction='OUT'),
    Filter(predicate=And(...)),
    Sort(items=[OrderByItem(...)], return_items=[...]),
    Project(items=[ReturnItem(...), ReturnItem(...), ReturnItem(...)]),
    Limit(count=5)
]
```

**3. Execute → Results:**
```python
# Step 1: ScanNodes - Bind all Person nodes to 'p'
[ExecutionContext(bindings={'p': NodeRef(id=1, ...)}),
 ExecutionContext(bindings={'p': NodeRef(id=2, ...)}),
 ...]

# Step 2: ExpandEdges - Traverse KNOWS edges, bind 'f'
[ExecutionContext(bindings={'p': NodeRef(1), 'f': NodeRef(2)}),
 ExecutionContext(bindings={'p': NodeRef(1), 'f': NodeRef(3)}),
 ...]

# Step 3: Filter - Keep rows where p.age > 30 AND f.age < p.age
[ExecutionContext(bindings={'p': NodeRef(1), 'f': NodeRef(3)}),
 ...]

# Step 4: Sort - Sort by p.age - f.age DESC
[...sorted rows...]

# Step 5: Project - Evaluate RETURN expressions
[{'person': CypherString('Alice'), 'friend': CypherString('Charlie'), 'age_diff': CypherInt(10)},
 ...]

# Step 6: Limit - Take first 5
[...5 rows...]
```

---

## Testing Strategy

### Test Categories

**Unit Tests** (`tests/unit/`)
- Individual component testing
- Parser, AST, planner, executor, evaluator
- Fast (<1s total)

**Integration Tests** (`tests/integration/`)
- End-to-end query execution
- Multi-component interactions
- Moderate speed (<10s total)

**TCK Tests** (`tests/tck/`)
- openCypher TCK compliance
- Semantic correctness validation
- 17 tests, 100% passing

**Property Tests** (Hypothesis)
- Fuzzing and edge cases
- Configured but not yet implemented

### Current Coverage

- **267 tests passing (100%)**
- **Test coverage: ~89%**
- **TCK compliance: 100% for implemented features**

**Test Execution:**
```bash
# All tests
pytest

# By category
pytest -m unit
pytest -m integration
pytest -m tck

# With coverage
pytest --cov=src/graphforge --cov-report=html
```

---

## Design Principles Applied

### 1. Spec-Driven Correctness

**Implementation:**
- 17 TCK compliance tests passing
- Three-valued NULL logic (TRUE, FALSE, NULL)
- ORDER BY can reference RETURN aliases (non-trivial semantic fix)
- Proper NULL handling in sorting, comparisons, aggregation

**Trade-off:**
- Performance secondary to correctness
- No unsafe optimizations

### 2. Embedded & Zero-Config

**Implementation:**
- No server or daemon
- SQLite storage (single file)
- Zero configuration needed
- Works in notebooks and scripts

**Example:**
```python
# Just works
db = GraphForge("analysis.db")
```

### 3. Graph-Native Execution

**Implementation:**
- Adjacency list traversal (no joins)
- Pattern matching operators (ScanNodes, ExpandEdges)
- Direct graph semantics

**Schema:**
```sql
-- Adjacency lists explicitly stored
CREATE TABLE adjacency_out (node_id, edge_id, PRIMARY KEY (node_id, edge_id));
```

### 4. Inspectable

**Implementation:**
- Observable query plans (future: `db.explain()`)
- SQLite storage (inspectable with sqlite3 CLI)
- Clear operator pipeline
- Comprehensive logging

### 5. Replaceable Internals

**Implementation:**
- Storage backend interface (Protocol)
- Can swap SQLite for custom backend
- Parser, planner, executor decoupled
- Stable Python API

---

## Performance Characteristics

### Current (In-Memory)

**Query Execution:**
- Simple MATCH: < 1ms (10K nodes)
- Pattern matching: < 10ms (10K nodes, 50K edges)
- Aggregation: < 50ms (10K nodes)

**Test Suite:**
- 267 tests: ~1.3 seconds total
- Unit tests: ~0.5 seconds
- Integration tests: ~0.5 seconds
- TCK tests: ~0.2 seconds

### Expected (SQLite Backend)

**Based on SQLite performance characteristics:**
- Node inserts: 50K-100K/sec (with transactions)
- Point queries: 100K-500K/sec
- Pattern matching: 1K-10K/sec
- Aggregation: 10K-50K/sec

**Target Scale:**
- ~10^6 nodes
- ~10^7 edges
- Query latency: < 100ms typical
- Load time: < 10 seconds for full graph

---

## Future Roadmap

### Phase 5: SQLite Persistence (In Progress)

- SQLite backend implementation
- Transaction support (BEGIN/COMMIT/ROLLBACK)
- Crash recovery
- Concurrent readers

**Estimated:** 30 hours

### Phase 6: Mutation Clauses

- CREATE clause (node/edge insertion)
- SET clause (property updates)
- DELETE clause (node/edge removal)
- MERGE clause (upsert semantics)

**Estimated:** 60 hours

### Phase 7: Advanced Features

- OPTIONAL MATCH (left outer join)
- Variable-length paths `[:KNOWS*1..3]`
- WITH clause (query composition)
- String functions
- List operations

**Estimated:** 80 hours

---

## References

### Requirements & Specifications
- `docs/0-requirements.md` - System requirements and scope
- `docs/open_cypher_ast_logical_plan_spec_v_1.md` - AST and planner spec
- `docs/runtime_value_model_graph_execution_v_1.md` - Execution semantics
- `docs/storage-architecture-analysis.md` - Storage backend decision analysis

### Feature Documentation
- `docs/feature-return-aliasing.md` - RETURN AS clause
- `docs/feature-order-by.md` - ORDER BY clause
- `docs/feature-aggregation-functions.md` - Aggregation functions
- `docs/tck-compliance.md` - TCK test suite

### Project Status
- `docs/project-status-and-roadmap.md` - Implementation roadmap
- `docs/phase-1-complete.md` - Core data model completion
- `docs/phase-2-complete.md` - Parser completion
- `docs/phase-3-complete.md` - Execution engine completion

### External References
- [openCypher specification](https://opencypher.org/)
- [openCypher TCK](https://github.com/opencypher/openCypher/tree/master/tck)
- [SQLite documentation](https://sqlite.org/docs.html)
- [SQLite WAL mode](https://sqlite.org/wal.html)
