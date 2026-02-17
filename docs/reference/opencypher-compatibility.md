# OpenCypher Compatibility Status

**Last Updated:** 2026-02-16
**GraphForge Version:** v0.4.0 (in progress)

---

## 📚 Documentation Navigation

This document provides a **high-level overview** of GraphForge's OpenCypher compatibility. For comprehensive details, see:

### Detailed Feature Documentation
- **[01-clauses.md](opencypher-features/01-clauses.md)** - Complete reference for all 16 OpenCypher clauses with syntax and examples
- **[02-functions.md](opencypher-features/02-functions.md)** - 72 functions across 9 categories (string, numeric, list, aggregation, predicate, scalar, temporal, spatial, path)
- **[03-operators.md](opencypher-features/03-operators.md)** - All operator types with precedence and NULL handling
- **[04-patterns.md](opencypher-features/04-patterns.md)** - Pattern matching with 90+ examples
- **[05-data-types.md](opencypher-features/05-data-types.md)** - Complete type system and coercion rules

### Implementation Status
- **[clauses.md](implementation-status/clauses.md)** - 16/20 clauses complete (80%), with file references
- **[functions.md](implementation-status/functions.md)** - 53/72 functions complete (74%), organized by category
- **[operators.md](implementation-status/operators.md)** - 30/34 operators complete (88%)
- **[patterns.md](implementation-status/patterns.md)** - 6.5/8 pattern types complete (81%)

### TCK Test Coverage
- **[tck-inventory.md](tck-inventory.md)** - Complete inventory of 1,626 TCK scenarios from 222 feature files
- **[clause-to-tck.md](feature-mapping/clause-to-tck.md)** - Maps clauses to ~1,180 TCK scenarios
- **[function-to-tck.md](feature-mapping/function-to-tck.md)** - Maps functions to ~380 TCK scenarios

### Comprehensive Analysis
- **[opencypher-compatibility-matrix.md](opencypher-compatibility-matrix.md)** - Complete feature-by-feature matrix with 134 features evaluated
- **[feature-graph-schema.md](feature-graph-schema.md)** - Queryable graph schema for feature relationships
- **[feature-graph-queries.md](feature-graph-queries.md)** - 20 example queries for analyzing features, status, and TCK coverage

---

## Executive Summary

GraphForge implements a **practical subset of OpenCypher** focused on common graph operations for embedded, notebook-friendly usage. It is **not** a full OpenCypher implementation, but provides the essential features needed for 80% of typical graph workflows.

### Current Status

| Version | TCK Scenarios | Feature Completeness | Status |
|---------|--------------|---------------------|--------|
| v0.1.4 | 638/3,837 | ~30% | Released |
| v0.2.0 | 638/3,837 | ~40% | Released |
| v0.2.1 | 638/3,837 | ~45% | Released |
| v0.3.0 | ~950/3,837 (25%) | ~65% | Released (February 2026) |
| v0.4.0 | 1,303/1,626 (34%) | **~78%** | **In Progress** (February 2026) |
| v1.0 | >3,800/3,837 | >99% | Goal (Full OpenCypher) |

**Note:** TCK scenario counts updated to reflect actual passing scenarios (1,303 of 1,626 tested).

**v0.4.0 Highlights:**
- **134 features evaluated:** 105 complete (78%), 2 partial (2%), 27 not implemented (20%)
- **Complete categories:** Temporal functions (100%), Spatial functions (100%), Comparison operators (100%)
- **High-impact gaps:** Predicate functions (all/any/none/single), list operations (extract/filter/reduce)
- **See:** [Compatibility Matrix](opencypher-compatibility-matrix.md) for complete feature-by-feature analysis

### Design Philosophy

GraphForge prioritizes:
- ✅ **Core Cypher clauses** for reading and writing (16/20 complete)
- ✅ **Common expressions** used in 80% of queries
- ✅ **Essential functions** for data manipulation (53/72 complete)
- ✅ **SQLite-backed persistence** with ACID transactions
- ✅ **Zero-configuration** embedded usage
- ✅ **Temporal/spatial types** - Complete as of v0.3.0 (date, datetime, time, duration, point, distance)
- ❌ Full-text search capabilities
- ❌ Multi-database features
- ❌ Distributed query execution

**See the [Compatibility Matrix](opencypher-compatibility-matrix.md) for detailed feature status.**

---

## Feature Matrix

**Note:** This section provides a high-level overview. For comprehensive feature documentation with syntax, examples, and implementation status, see:
- [Clause Documentation](opencypher-features/01-clauses.md) | [Clause Implementation Status](implementation-status/clauses.md)
- [Function Documentation](opencypher-features/02-functions.md) | [Function Implementation Status](implementation-status/functions.md)
- [Operator Documentation](opencypher-features/03-operators.md) | [Operator Implementation Status](implementation-status/operators.md)
- [Pattern Documentation](opencypher-features/04-patterns.md) | [Pattern Implementation Status](implementation-status/patterns.md)

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

Released: February 2026 | [Release Notes](changelog.md#030-2026-02-09)

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

| Feature Category | GraphForge v0.4.0 | Neo4j |
|------------------|-----------------|-------|
| **Core Clauses** | ✅ 80% (16/20) | ✅ 100% |
| **Pattern Matching** | ✅ 81% (6.5/8) | ✅ 100% |
| **Aggregations** | ✅ 5/10 core functions | ✅ 15+ functions |
| **Scalar Functions** | ✅ 53/72 (74%) | ✅ 100+ functions |
| **Temporal Types** | ✅ Complete (v0.3.0) | ✅ Full support |
| **Spatial Types** | ✅ Complete (v0.3.0) | ✅ Full support |
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

**See [TCK Inventory](tck-inventory.md) for complete catalog of 1,626 scenarios from 222 feature files.**

### Current Coverage (v0.4.0)

**1,303/1,626 scenarios passing (34% pass rate)**

*Note: GraphForge tests against a subset of 1,626 TCK scenarios. The full suite contains 3,837 total scenarios.*

**Detailed TCK Mappings:**
- [Clause to TCK Mapping](feature-mapping/clause-to-tck.md) - ~1,180 scenarios mapped to clauses
- [Function to TCK Mapping](feature-mapping/function-to-tck.md) - ~380 scenarios mapped to functions

#### Passing Scenario Categories (v0.4.0)
- ✅ Basic MATCH patterns (195 scenarios)
- ✅ WHERE clause filtering (53 scenarios)
- ✅ RETURN projection (129 scenarios)
- ✅ ORDER BY, LIMIT, SKIP (134 scenarios)
- ✅ CREATE nodes and relationships (78 scenarios)
- ✅ SET property updates (53 scenarios)
- ✅ DELETE operations (41 scenarios)
- ✅ MERGE patterns (75 scenarios)
- ✅ Basic aggregations (COUNT, SUM, AVG, MIN, MAX, COLLECT)
- ✅ WITH clause chaining (156 scenarios) — **Complete in v0.3.0**
- ✅ String functions (11/13 complete)
- ✅ Type conversion functions
- ✅ NULL handling in expressions
- ✅ List and map literals
- ✅ OPTIONAL MATCH — **Complete in v0.3.0** (~20 scenarios)
- ✅ Variable-length patterns — **Complete in v0.3.0** (~40 scenarios)
- ✅ UNWIND — **Complete in v0.2.0** (14 scenarios)
- ✅ CASE expressions — **Complete in v0.2.0**
- ✅ Arithmetic operators — **Complete in v0.2.0**
- ✅ String matching (STARTS WITH, ENDS WITH, CONTAINS) — **Complete in v0.2.0**
- ✅ EXISTS/COUNT subqueries — **Complete in v0.3.0** (10 scenarios)
- ✅ UNION / UNION ALL — **Complete in v0.3.0** (12 scenarios)
- ✅ Temporal functions — **Complete in v0.3.0** (11/11, 89 scenarios)
- ✅ Spatial functions — **Complete in v0.3.0** (2/2, ~10 scenarios)

#### Failing Scenario Categories (Notable)
- ❌ **Predicate functions** (all, any, none, single, isEmpty) - 0/6 complete, ~36 TCK scenarios
- ❌ **List operations** (extract, filter, reduce) - 0/3 complete, ~30 TCK scenarios
- ❌ **Pattern comprehension** - Not implemented, 15 TCK scenarios
- ❌ **CALL procedures** - Not implemented (no procedure system), 41 TCK scenarios
- ❌ **Statistical aggregations** (percentile, stdev) - 0/4 complete, ~3 TCK scenarios
- ❌ **Some mathematical functions** (sqrt, rand, pow) - 0/3 complete, minimal TCK coverage
- ❌ **List slicing** and negative indexing - Not implemented
- ❌ **XOR operator** - Not implemented

**Priority for v0.5.0:** Predicate functions and list operations (66 TCK scenarios, high impact)

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

| Milestone | Target | Feature % | TCK Pass Rate | Focus |
|-----------|--------|-----------|---------------|-------|
| v0.1.4 | Released | ~30% | 16.6% | Core clauses |
| v0.2.0 | Released | ~40% | 16.6% | Core features complete |
| v0.3.0 | Released | ~65% | ~25% | Advanced patterns, temporal, spatial |
| v0.4.0 | Feb 2026 | **~78%** | **34%** | **Documentation, TCK coverage analysis** |
| v0.5.0 | Jun 2026 | ~82% | ~50% | Predicate functions, list operations |
| v0.6.0 | Sep 2026 | ~88% | ~65% | Pattern comprehension, statistical aggregations |
| v0.7.0 | Dec 2026 | ~92% | ~78% | Edge cases & optimization |
| v0.8.0 | Mar 2027 | ~95% | ~88% | Advanced query features |
| v1.0.0 | Jun 2027 | >99% | >95% | Full OpenCypher |

**See [Compatibility Matrix](opencypher-compatibility-matrix.md) for detailed priority recommendations.**

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
1. **Predicate functions** (all, any, none, single) - ~36 TCK scenarios, commonly used in WHERE clauses
2. **List operations** (extract, filter, reduce) - ~30 TCK scenarios, useful for data transformation
3. **Pattern comprehension** - 15 TCK scenarios, complex but powerful feature
4. **Statistical aggregations** (percentileDisc, percentileCont, stDev) - ~3 TCK scenarios, analytics

**See [Implementation Priorities](opencypher-compatibility-matrix.md#implementation-priorities-for-v040) for detailed recommendations.**

---

## References

### External Resources
- **openCypher Specification:** https://opencypher.org/resources/
- **Neo4j Cypher Manual:** https://neo4j.com/docs/cypher-manual/
- **openCypher TCK:** https://github.com/opencypher/openCypher/tree/master/tck
- **GraphForge Issues:** https://github.com/DecisionNerd/graphforge/issues

### GraphForge Documentation
- **[README](README.md)** - Documentation directory structure and navigation guide
- **[Compatibility Matrix](opencypher-compatibility-matrix.md)** - Comprehensive feature-by-feature analysis
- **[Feature Documentation](opencypher-features/)** - Complete reference for clauses, functions, operators, patterns, and data types
- **[Implementation Status](implementation-status/)** - Detailed status with file references for all features
- **[Feature Mapping](feature-mapping/)** - TCK scenario mappings to clauses and functions
- **[TCK Inventory](tck-inventory.md)** - Complete catalog of 1,626 TCK scenarios
- **[Feature Graph Schema](feature-graph-schema.md)** - Queryable graph schema for feature relationships
- **[Feature Graph Queries](feature-graph-queries.md)** - Example queries for analyzing features and status

---

**Last Updated:** 2026-02-16
**Maintained by:** [@DecisionNerd](https://github.com/DecisionNerd)
