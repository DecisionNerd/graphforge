# OpenCypher Compatibility Status

**Last Updated:** 2026-02-09
**GraphForge Version:** v0.3.0

## Executive Summary

GraphForge implements a **practical subset of OpenCypher** focused on common graph operations for embedded, notebook-friendly usage. It is **not** a full OpenCypher implementation, but provides the essential features needed for 80% of typical graph workflows.

### Current Status

| Version | TCK Scenarios | Compliance | Status |
|---------|--------------|------------|--------|
| v0.1.4 | 638/3,837 | 16.6% | Released |
| v0.2.0 | 638/3,837 | 16.6% | Released |
| v0.2.1 | 638/3,837 | 16.6% | Released |
| v0.3.0 | ~950/3,837 | ~29% | **Released** (February 2026) |
| v0.4.0 | ~1,500/3,837 | ~39% | Planned |
| v1.0 | >3,800/3,837 | >99% | Goal (Full OpenCypher) |

### Design Philosophy

GraphForge prioritizes:
- ✅ **Core Cypher clauses** for reading and writing
- ✅ **Common expressions** used in 80% of queries
- ✅ **Essential functions** for data manipulation
- ✅ **SQLite-backed persistence** with ACID transactions
- ✅ **Zero-configuration** embedded usage
- ❌ Advanced temporal/spatial types
- ❌ Full-text search capabilities
- ❌ Multi-database features
- ❌ Distributed query execution

---

## Feature Matrix

### ✅ Fully Supported (v0.1.4)

#### Reading Clauses
- **MATCH** - Basic pattern matching with node and relationship patterns
  - Single patterns: `MATCH (n:Label)`
  - Relationship patterns: `MATCH (a)-[r:TYPE]->(b)`
  - Multi-pattern: `MATCH (a), (b)`
  - Property filtering: `MATCH (n {key: value})`
- **WHERE** - Predicate filtering with comparisons and logical operators
  - Comparisons: `=`, `<>`, `<`, `>`, `<=`, `>=`
  - Logical operators: `AND`, `OR`
  - Property access: `n.property`
  - NULL handling with ternary logic
- **RETURN** - Projection with aliasing
  - Property projection: `RETURN n.name AS name`
  - Expressions: `RETURN n.age + 5`
  - DISTINCT: `RETURN DISTINCT n.city`
- **WITH** - Query chaining and variable passing
  - Pipeline queries: `MATCH ... WITH ... MATCH ...`
  - Filtering: `WITH n WHERE n.age > 18`
- **ORDER BY** - Sorting with multiple keys
  - Multi-key: `ORDER BY n.age DESC, n.name ASC`
  - NULL ordering: NULLs last by default
- **LIMIT** / **SKIP** - Result pagination

#### Writing Clauses
- **CREATE** - Node and relationship creation
  - Nodes: `CREATE (n:Label {key: value})`
  - Relationships: `CREATE (a)-[r:TYPE {key: value}]->(b)`
  - Multi-create: `CREATE (a), (b), (a)-[:KNOWS]->(b)`
- **SET** - Property updates
  - Set property: `SET n.key = value`
  - Set multiple: `SET n.key1 = value1, n.key2 = value2`
  - Copy properties: `SET n = m`
- **DELETE** - Node and relationship deletion
  - Delete nodes: `DELETE n`
  - Delete relationships: `DELETE r`
  - Constraint: Cannot delete node with relationships (use DETACH DELETE)
- **MERGE** - Create-or-match patterns
  - Basic: `MERGE (n:Label {key: value})`
  - ON CREATE: `MERGE (n) ON CREATE SET n.created = timestamp()`
  - ON MATCH: `MERGE (n) ON MATCH SET n.accessed = timestamp()`

#### Aggregations
- **COUNT** - Row counting
  - `COUNT(*)` - Count all rows
  - `COUNT(expr)` - Count non-NULL values
  - `COUNT(DISTINCT expr)` - Count distinct values
- **SUM** - Numeric summation
- **AVG** - Numeric average
- **MIN** - Minimum value
- **MAX** - Maximum value
- **Implicit GROUP BY** - Non-aggregated columns become grouping keys

#### Scalar Functions
- **String Functions**
  - `length(str)` - String length
  - `substring(str, start, length)` - Extract substring
  - `toUpper(str)` / `toLower(str)` - Case conversion
  - `trim(str)` - Remove whitespace
- **Type Conversion**
  - `toInteger(value)` - Convert to integer
  - `toFloat(value)` - Convert to float
  - `toString(value)` - Convert to string
- **Utility Functions**
  - `coalesce(expr1, expr2, ...)` - Return first non-NULL
  - `type(relationship)` - Get relationship type

#### Expressions & Operators
- **Comparison Operators:** `=`, `<>`, `<`, `>`, `<=`, `>=`
- **Logical Operators:** `AND`, `OR` (with NULL propagation)
- **Property Access:** `n.property`, `r.property`
- **Literals:** Integers, floats, strings, booleans, NULL, lists, maps
- **List Literals:** `[1, 2, 3]`, `['a', 'b', 'c']`
- **Map Literals:** `{key: value, nested: {k: v}}`

#### Data Types
- **CypherInt** - 64-bit signed integers
- **CypherFloat** - 64-bit floating point
- **CypherString** - UTF-8 strings
- **CypherBool** - Boolean (true/false)
- **CypherNull** - NULL value
- **CypherList** - Ordered lists (heterogeneous)
- **CypherMap** - Key-value maps (nested structures)
- **NodeRef** - Node references in query context
- **EdgeRef** - Relationship references in query context

---

### ✅ Completed in v0.2.0 and v0.2.1

Released: February 2026

| Feature | Version | Status |
|---------|---------|--------|
| CASE expressions | v0.2.0 | ✅ Complete |
| COLLECT aggregation | v0.2.0 | ✅ Complete |
| Arithmetic operators (+, -, *, /, %) | v0.2.0 | ✅ Complete |
| String matching (STARTS WITH, ENDS WITH, CONTAINS) | v0.2.0 | ✅ Complete |
| REMOVE clause | v0.2.0 | ✅ Complete |
| NOT operator | v0.2.0 | ✅ Complete |
| UNWIND clause | v0.2.0 | ✅ Complete |
| DETACH DELETE | v0.2.0 | ✅ Complete |
| MERGE ON CREATE SET | v0.2.1 | ✅ Complete |
| MERGE ON MATCH SET | v0.2.1 | ✅ Complete |
| Dataset loading infrastructure | v0.2.1 | ✅ Complete |
| CSV edge-list loader | v0.2.1 | ✅ Complete |
| 5 SNAP datasets | v0.2.1 | ✅ Complete |

#### What v0.2.0 Will Enable

```cypher
-- UNWIND: Iterate over lists
UNWIND [1, 2, 3] AS num
RETURN num

-- DETACH DELETE: Cascading deletion
MATCH (n:Temporary)
DETACH DELETE n

-- CASE: Conditional logic
MATCH (p:Person)
RETURN p.name,
       CASE
           WHEN p.age < 18 THEN 'minor'
           WHEN p.age < 65 THEN 'adult'
           ELSE 'senior'
       END AS category

-- REMOVE: Property/label removal
MATCH (n:Person)
REMOVE n.temporaryField, n:OldLabel

-- Arithmetic: Computations
MATCH (p:Person)
RETURN p.name, p.salary * 1.1 AS new_salary

-- COLLECT: Aggregate into lists
MATCH (p:Person)
RETURN p.city, COLLECT(p.name) AS residents

-- String matching: Text filtering
MATCH (p:Person)
WHERE p.email ENDS WITH '@example.com'
RETURN p

-- NOT: Logical negation
MATCH (p:Person)
WHERE NOT p.archived
RETURN p
```

---

### ✅ Completed in v0.3.0

Released: February 2026 | [Release Notes](../../CHANGELOG.md#030---2026-02-09)

#### Major Cypher Features

| Feature | Status | TCK Impact |
|---------|--------|------------|
| **OPTIONAL MATCH** | ✅ Complete | ~150 scenarios |
| **Variable-length patterns** (`-[:TYPE*1..3]->`) | ✅ Complete | ~100 scenarios |
| **List comprehensions** | ✅ Complete | ~100 scenarios |
| **Subqueries (EXISTS, COUNT)** | ✅ Complete | ~100 scenarios |
| **UNION / UNION ALL** | ✅ Complete | ~30 scenarios |
| **IS NULL / IS NOT NULL** | ✅ Complete | Integrated |
| **Spatial types** (Point, Distance) | ✅ Complete | ~50 scenarios |
| **Temporal types** (Date, DateTime, Time, Duration) | ✅ Complete | ~50 scenarios |

#### Dataset Integration

| Feature | Status |
|---------|--------|
| **95 SNAP datasets** | ✅ Complete |
| **10 LDBC datasets** | ✅ Complete |
| **10 NetworkRepository datasets** | ✅ Complete |
| **GraphML loader** | ✅ Complete |
| **Cypher script loader** | ✅ Complete |
| **Zip compression support** | ✅ Complete |
| **Zstandard compression support** | ✅ Complete |

**Actual TCK Compliance:** ~29% (950+ scenarios)
**Total Datasets:** 109+ validated datasets

---

### ⏳ Planned for v0.4.0 and Beyond

#### Coming in v0.4.0
- **Pattern predicates** - WHERE inside patterns: `MATCH (a)-[r WHERE r.weight > 5]->(b)`
- **Path expressions** - Path variables and functions
- **Additional string functions** - split(), replace(), reverse()
- **Additional list functions** - tail(), head(), last()
- **Query optimization** - Performance improvements for complex queries

**Target:** ~39% TCK coverage (1,500+ scenarios)

---

### ❌ Not Supported

These features are **out of scope** for GraphForge's design goals:
- ❌ **Full-Text Search** - `db.index.fulltext.*`
  - *Reason:* SQLite FTS could be added, but not core priority
  - *Workaround:* Use string matching (CONTAINS) or external FTS

#### Enterprise Features
- ❌ **User Management** - CREATE USER, GRANT, REVOKE, roles
  - *Reason:* Embedded design, no multi-user access
- ❌ **Multi-Database** - USE database, database switching
  - *Reason:* Single-database design, create multiple GraphForge instances if needed
- ❌ **Constraints (advanced)** - UNIQUE, EXISTS, KEY constraints
  - *Reason:* Validation can be done in Python, limited benefit for analysis
- ❌ **Indexes (advanced)** - CREATE INDEX, BTREE, HASH
  - *Reason:* SQLite provides indexing, but explicit index creation not exposed

#### Distributed Features
- ❌ **Sharding / Replication** - Multi-node clusters
  - *Reason:* Single-node embedded design
- ❌ **Distributed Transactions** - Cross-database ACID
  - *Reason:* SQLite ACID within single database only

#### Advanced Query Features
- ❌ **CALL Procedures** - User-defined procedures, built-in procedures
  - *Reason:* Could add in future, but Python functions are more natural
  - *Workaround:* Write Python functions, call from builder API
- ❌ **Label Expressions** - `:A|B` (union), `!:A` (negation)
  - *Reason:* Low priority, can filter in WHERE
- ❌ **Map Projections** - `node {.property1, .property2}`
  - *Reason:* Syntax sugar, not essential
- ❌ **FOREACH** - Iterative updates
  - *Reason:* Low usage, can use UNWIND + SET

#### Graph Algorithms
- ❌ **Built-in Algorithms** - PageRank, community detection, centrality
  - *Reason:* User can implement in Python or use NetworkX
  - *Workaround:* Export to NetworkX, run algorithms, import results

---

## Comparison with Neo4j

| Feature Category | GraphForge v0.2 | Neo4j |
|------------------|-----------------|-------|
| **Core Clauses** | ✅ 90% | ✅ 100% |
| **Pattern Matching** | ⚠️ Basic patterns | ✅ Full patterns |
| **Aggregations** | ⚠️ 6 functions | ✅ 15+ functions |
| **Scalar Functions** | ⚠️ 15 functions | ✅ 100+ functions |
| **Temporal Types** | ❌ None | ✅ Full support |
| **Spatial Types** | ❌ None | ✅ Full support |
| **Indexes** | ⚠️ SQLite automatic | ✅ Explicit control |
| **Constraints** | ❌ None | ✅ Full support |
| **Procedures** | ❌ None | ✅ CALL + APOC |
| **Deployment** | ✅ Embedded (pip) | ⚠️ Service (Docker/VM) |
| **Setup Complexity** | ✅ Zero config | ⚠️ Configuration needed |
| **ACID Transactions** | ✅ SQLite | ✅ Native |
| **Scale** | ⚠️ 100k-1M nodes | ✅ Billions of nodes |
| **Multi-user** | ❌ Single process | ✅ Full auth/RBAC |

**Summary:** GraphForge is to Neo4j as SQLite is to PostgreSQL — a lightweight, embedded alternative for single-user analytical workflows, not a production database replacement.

---

## TCK Compliance Details

The **Technology Compatibility Kit (TCK)** is the official openCypher test suite with 3,837 scenarios.

### Current Coverage (v0.1.4)

**1,277/7,722 scenarios passing (16.5%)**

*Note: TCK suite contains 7,722 total scenarios. Earlier documentation referenced a subset of 3,837 scenarios.*

#### Passing Scenario Categories
- ✅ Basic MATCH patterns
- ✅ WHERE clause filtering
- ✅ RETURN projection
- ✅ ORDER BY, LIMIT, SKIP
- ✅ CREATE nodes and relationships
- ✅ SET property updates
- ✅ DELETE operations
- ✅ MERGE patterns
- ✅ Basic aggregations (COUNT, SUM, AVG, MIN, MAX)
- ✅ WITH clause chaining
- ✅ String functions (length, substring, case conversion)
- ✅ Type conversion functions
- ✅ NULL handling in expressions
- ✅ List and map literals

#### Failing Scenario Categories (Notable)
- ❌ OPTIONAL MATCH (left outer joins)
- ❌ Variable-length patterns (`-[*1..5]->`)
- ❌ UNWIND (list iteration) — **Fixed in v0.2**
- ❌ CASE expressions — **Fixed in v0.2**
- ❌ COLLECT aggregation — **Fixed in v0.2**
- ❌ Arithmetic operators — **Fixed in v0.2**
- ❌ String matching (STARTS WITH, etc.) — **Fixed in v0.2**
- ❌ Subqueries (EXISTS, COUNT)
- ❌ UNION / UNION ALL
- ❌ List comprehensions
- ❌ Pattern predicates
- ❌ REMOVE clause — **Fixed in v0.2**
- ❌ Many advanced functions

### Projected v0.2.0 Coverage

**~1,900/7,722 scenarios passing (~25%)**

Adding 9 new features in v0.2 will close ~300-350 scenarios:
- UNWIND: +50
- DETACH DELETE: +10
- CASE: +100
- REMOVE: +20
- Arithmetic: +50
- COLLECT: +30
- String matching: +50
- NOT: +10
- Various edge cases: +50

### Projected v0.3.0 Coverage

**~3,000/7,722 scenarios passing (~39%)**

Adding advanced features in v0.3 will close ~550 scenarios:
- OPTIONAL MATCH: +150
- Variable-length patterns: +150
- List comprehensions: +100
- Subqueries: +150

---

## Usage Recommendations

### ✅ Good Use Cases for GraphForge

- **Notebook-based analysis** - Jupyter, IPython, exploratory data analysis
- **Knowledge graph prototyping** - Build and refine graph structures iteratively
- **LLM-powered graph generation** - Store entity-relationship extractions
- **Data lineage tracking** - Model data transformation pipelines
- **Small to medium graphs** - 100k-1M nodes, 1M-10M relationships
- **Single-user workflows** - No concurrent write access needed
- **Embedded applications** - Package graph database with Python app
- **Teaching and learning** - Learn Cypher without database setup

### ⚠️ Limited Use Cases

- **Complex path queries** - Variable-length patterns limited (v0.3 will improve)
- **Time-series data** - No native temporal types, use ISO strings
- **Geospatial queries** - No spatial types, store coordinates as properties
- **Full-text search** - Use CONTAINS for simple matching, or external tools
- **Very large graphs** - 10M+ nodes may hit performance limits
- **Concurrent writes** - SQLite single-writer limitation

### ❌ Not Recommended

- **Production web applications** - Use Neo4j, Memgraph, or similar
- **Multi-tenant systems** - No user management or security
- **Distributed queries** - Single-node only
- **Real-time analytics** - Limited optimization for high-throughput
- **Complex graph algorithms** - Use NetworkX or specialized tools
- **Mission-critical systems** - Embedded design, no HA/replication

---

## Roadmap to Full OpenCypher

### Realistic Timeline

| Milestone | Target | TCK % | Focus |
|-----------|--------|-------|-------|
| v0.2.0 | Mar 2026 | 25% | Core features complete |
| v0.3.0 | Jun 2026 | 39% | Advanced patterns |
| v0.4.0 | Sep 2026 | 55% | Comprehensive functions |
| v0.5.0 | Dec 2026 | 70% | Advanced expressions |
| v0.6.0 | Mar 2027 | 82% | Subqueries & procedures |
| v0.7.0 | Jun 2027 | 92% | Edge cases & optimization |
| v1.0.0 | Sep 2027 | >99% | Full OpenCypher |

**Goal:** GraphForge v1.0 will be a **complete production platform** with:
- >99% OpenCypher compliance (full query language)
- Modern APIs (REST, GraphQL, WebSocket)
- Analytical integrations (NetworkX, iGraph, QuantumFusion)
- Comprehensive import/export (GraphML, CSV, JSON, Parquet, Neo4j)
- Web GUI for exploration and querying
- Production features (monitoring, backup/restore, auth)

The remaining <1% TCK scenarios represent enterprise features (user management, distributed systems) that are incompatible with the embedded design.

### Target Compliance: >99%

GraphForge v1.0 will target **>99% TCK compliance** (Full OpenCypher), covering:
- ✅ All core clauses (MATCH, CREATE, MERGE, DELETE, etc.)
- ✅ All expressions (CASE, arithmetic, logical, pattern predicates)
- ✅ All standard functions (string, list, math, aggregations)
- ✅ Pattern matching (including variable-length, shortest path)
- ✅ Subqueries and advanced queries (EXISTS, CALL)
- ✅ List comprehensions and map projections
- ✅ UNION, FOREACH, and advanced control flow
- ⚠️ Temporal/spatial types (may defer to v1.1+)
- ❌ Enterprise features (user management, multi-DB - out of scope for embedded design)
- ❌ Distributed features (clustering, sharding - single-node architecture)

---

## Contributing

Help build GraphForge v1.0! See:
- [GitHub Milestones](https://github.com/DecisionNerd/graphforge/milestones)
- [Contributing Guide](https://github.com/DecisionNerd/graphforge/blob/main/CONTRIBUTING.md)
- [Issue Workflow](https://github.com/DecisionNerd/graphforge/blob/main/.github/ISSUE_WORKFLOW.md)

### High-Impact Contributions

Want to make a big impact? Consider implementing:
1. **OPTIONAL MATCH** (#planned) - Left outer joins, ~150 scenarios
2. **Variable-length patterns** (#24) - Path queries, ~150 scenarios
3. **List comprehensions** (#planned) - Functional list ops, ~100 scenarios
4. **EXISTS subqueries** (#planned) - Pattern predicates, ~100 scenarios

---

## References

- **openCypher Specification:** https://opencypher.org/resources/
- **Neo4j Cypher Manual:** https://neo4j.com/docs/cypher-manual/
- **openCypher TCK:** https://github.com/opencypher/openCypher/tree/master/tck
- **GraphForge Issues:** https://github.com/DecisionNerd/graphforge/issues

---

**Last Updated:** 2026-02-02
**Maintained by:** [@DecisionNerd](https://github.com/DecisionNerd)
