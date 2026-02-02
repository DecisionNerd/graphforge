# OpenCypher Compatibility Status

**Last Updated:** 2026-02-02
**GraphForge Version:** v0.1.4 → v0.2.0 (in progress)

## Executive Summary

GraphForge implements a **practical subset of OpenCypher** focused on common graph operations for embedded, notebook-friendly usage. It is **not** a full OpenCypher implementation, but provides the essential features needed for 80% of typical graph workflows.

### Current Status

| Version | TCK Scenarios | Compliance | Status |
|---------|--------------|------------|--------|
| v0.1.4 | 638/3,837 | 16.6% | Released |
| v0.2.0 | ~950/3,837 | ~25% | In Progress ([9 issues](https://github.com/DecisionNerd/graphforge/milestone/1)) |
| v0.3.0 | ~1,500/3,837 | ~39% | Planned ([1 issue](https://github.com/DecisionNerd/graphforge/milestone/2)) |

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

### 🚧 In Progress (v0.2.0)

Target: March 2026 | [GitHub Milestone](https://github.com/DecisionNerd/graphforge/milestone/1)

| Feature | Issue | Effort | Status |
|---------|-------|--------|--------|
| UNWIND clause | [#20](https://github.com/DecisionNerd/graphforge/issues/20) | 2-3h | 🚧 |
| DETACH DELETE | [#21](https://github.com/DecisionNerd/graphforge/issues/21) | 1-2h | 🚧 |
| CASE expressions | [#22](https://github.com/DecisionNerd/graphforge/issues/22) | 4-5h | 🚧 |
| MATCH-CREATE formalization | [#23](https://github.com/DecisionNerd/graphforge/issues/23) | 3-4h | 🚧 |
| REMOVE clause | [#25](https://github.com/DecisionNerd/graphforge/issues/25) | 2h | 🚧 |
| Arithmetic operators | [#26](https://github.com/DecisionNerd/graphforge/issues/26) | 2-3h | 🚧 |
| COLLECT aggregation | [#27](https://github.com/DecisionNerd/graphforge/issues/27) | 3-4h | 🚧 |
| String matching operators | [#28](https://github.com/DecisionNerd/graphforge/issues/28) | 2-3h | 🚧 |
| NOT operator | [#29](https://github.com/DecisionNerd/graphforge/issues/29) | 1-2h | 🚧 |

**Total Effort:** 20-28 hours
**Projected TCK Compliance:** ~25% (950+ scenarios)

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

### ⏳ Planned (v0.3.0)

Target: June 2026 | [GitHub Milestone](https://github.com/DecisionNerd/graphforge/milestone/2)

#### Critical Missing Features

| Feature | Priority | Effort | Impact |
|---------|----------|--------|--------|
| **OPTIONAL MATCH** | High | 8-10h | ~150 scenarios |
| **Variable-length patterns** | High | 10-15h | ~150 scenarios |
| **List comprehensions** | Medium | 5-7h | ~100 scenarios |
| **Subqueries (EXISTS, COUNT)** | Medium | 8-10h | ~150 scenarios |
| **UNION / UNION ALL** | Medium | 4-5h | ~30 scenarios |
| **Pattern predicates** | Medium | 6-8h | ~100 scenarios |
| **Additional string functions** | Low | 4-5h | ~100 scenarios |
| **Additional list functions** | Low | 4-5h | ~100 scenarios |

**Total Effort:** 50-70 hours
**Projected TCK Compliance:** ~39% (1,500+ scenarios)

---

### ❌ Not Supported

These features are **out of scope** for GraphForge's design goals:

#### Advanced Data Types
- ❌ **Temporal Types** - `date`, `datetime`, `time`, `duration`
  - *Reason:* Complex type system, limited use in analysis workflows
  - *Workaround:* Use ISO 8601 strings, parse in Python
- ❌ **Spatial Types** - `point`, `distance`, spatial indexing
  - *Reason:* Requires specialized indexing, better handled by PostGIS
  - *Workaround:* Store coordinates as properties, compute in Python
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

**638/3,837 scenarios passing (16.6%)**

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

**~950/3,837 scenarios passing (~25%)**

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

**~1,500/3,837 scenarios passing (~39%)**

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
| v0.4.0 | Sep 2026 | 50% | Performance + functions |
| v0.5.0 | Dec 2026 | 60% | Advanced expressions |
| v1.0.0 | Mar 2027 | 73% | Full core OpenCypher |

**Note:** 100% TCK compliance is **not a goal**. Many scenarios test enterprise features (user management, distributed systems) or advanced types (temporal, spatial) that are out of scope for GraphForge's embedded design.

### Target Compliance: 70-75%

GraphForge v1.0 will target **70-75% TCK compliance**, covering:
- ✅ All core clauses (MATCH, CREATE, MERGE, etc.)
- ✅ All essential expressions (CASE, arithmetic, logical)
- ✅ Most common functions (string, list, math)
- ✅ Pattern matching (including variable-length)
- ✅ Subqueries and advanced queries
- ❌ Temporal/spatial types (out of scope)
- ❌ Enterprise features (out of scope)
- ❌ Distributed features (out of scope)

---

## Contributing

Help improve OpenCypher compliance! See:
- [GitHub Issues by Milestone](https://github.com/DecisionNerd/graphforge/milestones)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [Issue Workflow](../../.github/ISSUE_WORKFLOW.md)

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
