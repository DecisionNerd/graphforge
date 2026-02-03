# Architecture Decision Record: SQLite Storage Backend

**Date:** 2026-01-30
**Status:** Accepted
**Decision:** Use SQLite as the persistence layer for GraphForge

---

## Context

GraphForge requires durable storage with the following characteristics:
- ACID transactions
- Crash recovery
- Write-ahead logging (WAL)
- Snapshot isolation for readers
- Single writer, multiple concurrent readers
- Cross-platform compatibility
- Zero operational overhead (embedded, zero-config)

Two approaches were evaluated:
1. **Custom WAL-based storage engine** (modeling SQLite's approach)
2. **SQLite as storage backend** (using SQLite directly)

---

## Decision

**Use SQLite as the storage backend for persistence.**

---

## Rationale

### Alignment with Project Goals

GraphForge's requirements state: *"The design philosophy mirrors SQLite: minimal operational overhead, stable APIs, and replaceable internals."*

SQLite delivers:
- ✅ Embedded architecture (no server/daemon)
- ✅ Single-file storage (durable but disposable)
- ✅ Zero configuration
- ✅ ACID guarantees
- ✅ WAL mode for concurrency
- ✅ Cross-platform compatibility

### Technical Benefits

**1. ACID Transactions (Free)**
```python
conn.execute("BEGIN")
# ... operations ...
conn.execute("COMMIT")
```
- Atomic commits
- Automatic rollback on failure
- No implementation needed

**2. WAL Mode (Free)**
```python
conn.execute("PRAGMA journal_mode=WAL")
```
- Single writer, multiple readers
- Readers don't block writer
- Writer doesn't block readers
- Snapshot isolation automatically

**3. Crash Recovery (Free)**
- Automatic recovery on database open
- WAL replay for committed transactions
- Discard uncommitted transactions
- 20+ years of battle-testing

**4. Durability (Free)**
- fsync guarantees on commit
- Corruption detection and repair
- Tested on billions of devices

### Development Efficiency

**Time Comparison:**
- SQLite implementation: **20-30 hours**
- Custom WAL implementation: **120-175 hours**
- **Savings: 90-145 hours**

**Risk Comparison:**
- SQLite: Minimal risk (proven, stable)
- Custom: High risk (storage engines are hard to get right)

### Performance

At GraphForge's target scale (10^6 nodes, 10^7 edges):

SQLite performance:
- Inserts: 50,000-100,000/sec (with transactions)
- Point queries: 100,000-500,000/sec
- Pattern matching: 1,000-10,000/sec

**Verdict:** More than sufficient for workbench use case.

### User Experience

**Inspectable Storage:**
```bash
# Users can inspect storage directly
sqlite3 my-graph.db
> SELECT COUNT(*) FROM nodes;
> SELECT * FROM edges WHERE type = 'KNOWS';
> .schema
```

**Tooling Ecosystem:**
- DB Browser for SQLite (GUI)
- sqlite3 CLI (built into most systems)
- Python sqlite3 module (stdlib)
- Extensive documentation and tutorials

**Disposable Experiments:**
```python
# Each experiment is just a file
db1 = GraphForge("experiment-v1.db")
db2 = GraphForge("experiment-v2.db")

# Compare approaches
# Copy files = copy experiments
```

### Replaceable Internals

The storage backend is abstracted behind an interface:

```python
class StorageBackend(Protocol):
    def add_node(self, node: NodeRef) -> None: ...
    def add_edge(self, edge: EdgeRef) -> None: ...
    # ...

# v1: SQLite
db = GraphForge("graph.db", backend="sqlite")

# v2: Custom (if needed)
db = GraphForge("graph.db", backend="custom")
```

SQLite can be replaced later if profiling shows it's a bottleneck (unlikely at target scale).

---

## Consequences

### Positive

1. **Fast Development**
   - 90-145 hours saved vs custom implementation
   - Can focus on openCypher features
   - Ship working product quickly

2. **Reliability**
   - Zero risk of data corruption bugs
   - Battle-tested durability
   - No maintenance burden

3. **User Experience**
   - Zero configuration
   - Inspectable storage
   - Familiar tooling
   - Cross-platform

4. **Technical Debt: None**
   - SQLite is stable (20+ years)
   - Can optimize later if needed
   - Storage is replaceable

### Negative

1. **Abstraction**
   - Not "pure" graph storage
   - Relational engine underneath
   - But: At target scale, this doesn't matter

2. **Learning Curve**
   - Need to understand SQLite internals
   - PRAGMA settings, transaction modes
   - But: Well-documented, not complex

3. **Dependency**
   - External dependency (though stdlib)
   - SQLite bugs affect GraphForge
   - But: SQLite is extremely stable

### Mitigations

**If Performance Becomes an Issue:**
1. Optimize SQLite queries/indexes first
2. Benchmark to identify actual bottlenecks
3. Only build custom storage if SQLite is proven insufficient
4. Storage backend is replaceable by design

**If SQLite Has Limitations:**
1. Most limitations won't affect workbench use case
2. Can work around with schema design
3. Can extend with custom functions if needed

---

## Implementation Plan

### Phase 5A: Basic SQLite Integration (Week 1)

**Schema Design:**
```sql
CREATE TABLE nodes (
    id INTEGER PRIMARY KEY,
    labels BLOB,
    properties BLOB
);

CREATE TABLE edges (
    id INTEGER PRIMARY KEY,
    type TEXT,
    src_id INTEGER,
    dst_id INTEGER,
    properties BLOB
);

CREATE TABLE adjacency_out (
    node_id INTEGER,
    edge_id INTEGER,
    PRIMARY KEY (node_id, edge_id)
);

CREATE TABLE adjacency_in (
    node_id INTEGER,
    edge_id INTEGER,
    PRIMARY KEY (node_id, edge_id)
);
```

**Backend Implementation:**
```python
class SQLiteBackend(StorageBackend):
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=FULL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def add_node(self, node: NodeRef) -> None:
        labels = msgpack.packb(list(node.labels))
        props = msgpack.packb(serialize_properties(node.properties))
        self.conn.execute(
            "INSERT INTO nodes (id, labels, properties) VALUES (?, ?, ?)",
            (node.id, labels, props)
        )

    def get_outgoing_edges(self, node_id: int) -> list[EdgeRef]:
        cursor = self.conn.execute("""
            SELECT e.* FROM edges e
            JOIN adjacency_out a ON e.id = a.edge_id
            WHERE a.node_id = ?
        """, (node_id,))
        return [self._edge_from_row(row) for row in cursor.fetchall()]
```

### Phase 5B: Transaction Support (Week 2)

```python
class SQLiteBackend:
    def begin_transaction(self) -> None:
        self.conn.execute("BEGIN IMMEDIATE")

    def commit_transaction(self) -> None:
        self.conn.execute("COMMIT")

    def rollback_transaction(self) -> None:
        self.conn.execute("ROLLBACK")
```

### Phase 5C: Testing & Documentation (Week 2)

- Persistence tests (save/load)
- Transaction tests (ACID properties)
- Crash recovery simulation
- Concurrent reader tests
- Documentation and examples

---

## References

- **Analysis Document:** `docs/storage-architecture-analysis.md`
- **Architecture Overview:** `docs/architecture-overview.md`
- **Requirements:** `docs/0-requirements.md` (Section 9: Storage Engine)
- **SQLite Documentation:** https://sqlite.org/docs.html
- **SQLite WAL Mode:** https://sqlite.org/wal.html

---

## Alternatives Considered

### Custom WAL-Based Engine

**Pros:**
- Graph-optimized storage format
- Complete control over implementation
- Educational experience

**Cons:**
- 120-175 hours implementation time
- High bug risk (storage engines are complex)
- Maintenance burden forever
- Diverts focus from core value (openCypher execution)

**Decision:** Rejected in favor of SQLite

**Reasoning:** GraphForge is a graph workbench, not a storage engine project. Use proven infrastructure (SQLite) and focus on graph features.

---

## Status

**Accepted:** 2026-01-30

**Implementation Status:** Not started (Phase 5 planned)

**Documentation Updated:**
- ✅ `docs/0-requirements.md` (Section 9)
- ✅ `docs/project-status-and-roadmap.md` (Phase 5)
- ✅ `docs/architecture-overview.md` (Storage section)
- ✅ `README.md` (Architecture section)
- ✅ Decision record created

**Next Steps:**
1. Implement SQLiteBackend class
2. Schema creation and migration
3. Transaction support
4. Testing (persistence, ACID, crash recovery)
5. Documentation and examples
