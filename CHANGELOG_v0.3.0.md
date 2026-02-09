# GraphForge v0.3.0 Release Notes

## Overview

Version 0.3.0 represents a major advancement in GraphForge's Cypher capabilities, adding support for complex query features that significantly increase openCypher compatibility. This release implements 8 major features from the v0.3.0 roadmap, substantially improving TCK (Technology Compatibility Kit) coverage.

## Major New Features

### 1. OPTIONAL MATCH (Left Outer Joins)

OPTIONAL MATCH allows matching patterns that may not exist, preserving rows with NULL values when no match is found.

**Syntax:**
```cypher
OPTIONAL MATCH (pattern)
```

**Example:**
```cypher
// Find all people and their friends (if any)
MATCH (p:Person)
OPTIONAL MATCH (p)-[:KNOWS]->(f)
RETURN p.name, f.name
```

**Implementation Details:**
- Left outer join semantics
- NULL propagation for unmatched patterns
- Works with property access, aggregations, and WHERE clauses
- NULL handling: accessing properties on NULL returns NULL

**Files Changed:**
- `src/graphforge/ast/clause.py` - Added `OptionalMatchClause`
- `src/graphforge/parser/cypher.lark` - Added OPTIONAL MATCH grammar
- `src/graphforge/planner/operators.py` - Added `OptionalExpandEdges` operator
- `src/graphforge/executor/executor.py` - Implemented left join logic

**Tests:** 6 comprehensive integration tests

---

### 2. UNION and UNION ALL

Combine results from multiple queries with automatic deduplication (UNION) or preserve duplicates (UNION ALL).

**Syntax:**
```cypher
query1
UNION [ALL]
query2
```

**Examples:**
```cypher
// Combine unique names from two node types
MATCH (p:Person) RETURN p.name AS name
UNION
MATCH (c:Company) RETURN c.name AS name

// Keep all results including duplicates
MATCH (p:Person) RETURN p.name AS name
UNION ALL
MATCH (p:Person) RETURN p.name AS name
```

**Implementation Details:**
- Tree-based operator structure for nested queries
- Deduplication using hashable value conversion
- Support for multiple UNION branches
- Works with ORDER BY, LIMIT, SKIP in branches

**Files Changed:**
- `src/graphforge/planner/operators.py` - Added `Union` and `Subquery` operators
- `src/graphforge/parser/cypher.lark` - Added UNION grammar
- `src/graphforge/executor/executor.py` - Implemented union execution
- `src/graphforge/api.py` - Added UNION query detection

**Tests:** 9 comprehensive integration tests

---

### 3. List Comprehensions

Transform and filter lists using declarative syntax similar to Python list comprehensions.

**Syntax:**
```cypher
[variable IN list WHERE condition | transformation]
```

**Examples:**
```cypher
// Filter list
RETURN [x IN [1,2,3,4,5] WHERE x > 3] AS filtered
// Returns: [4, 5]

// Transform list
RETURN [x IN [1,2,3] | x * 2] AS doubled
// Returns: [2, 4, 6]

// Filter and transform
RETURN [x IN [1,2,3,4,5] WHERE x > 2 | x * 2] AS result
// Returns: [6, 8, 10]

// With graph data
MATCH (p:Person)
WITH collect(p.age) AS ages
RETURN [age IN ages WHERE age > 30] AS older_ages
```

**Implementation Details:**
- Context isolation for loop variable
- Filter expression evaluation (WHERE clause)
- Map expression evaluation (| clause)
- NULL handling in filters (NULL treated as false)
- Nested comprehension support

**Files Changed:**
- `src/graphforge/ast/expression.py` - Added `ListComprehension` AST node
- `src/graphforge/parser/cypher.lark` - Added comprehension grammar
- `src/graphforge/executor/evaluator.py` - Implemented evaluation logic

**Tests:** 12 comprehensive integration tests

---

### 4. EXISTS and COUNT Subquery Expressions

Execute nested queries within expressions to check existence or count results.

**Syntax:**
```cypher
EXISTS { subquery }
COUNT { subquery }
```

**Examples:**
```cypher
// EXISTS in WHERE clause
MATCH (p:Person)
WHERE EXISTS { MATCH (p)-[:KNOWS]->() }
RETURN p.name
// Returns people who know someone

// COUNT in RETURN clause
MATCH (p:Person)
RETURN p.name, COUNT { MATCH (p)-[:KNOWS]->() } AS friend_count

// COUNT with filtering
MATCH (p:Person)
WITH p, COUNT { MATCH (p)-[:KNOWS]->(f) WHERE f.age > 30 } AS older_friends
WHERE older_friends > 2
RETURN p.name
```

**Implementation Details:**
- Correlated subqueries (reference outer variables)
- Isolated execution context with outer bindings
- Full operator pipeline execution for nested queries
- EXISTS returns boolean, COUNT returns integer

**Files Changed:**
- `src/graphforge/ast/expression.py` - Added `SubqueryExpression`
- `src/graphforge/parser/cypher.lark` - Added EXISTS/COUNT grammar
- `src/graphforge/executor/evaluator.py` - Added subquery evaluation
- `src/graphforge/executor/executor.py` - Added planner attribute for recursion
- `src/graphforge/api.py` - Pass planner to executor

**Tests:** 13 comprehensive integration tests

---

### 5. Variable-Length Path Patterns

Match paths of varying lengths using recursive traversal with cycle detection.

**Syntax:**
```cypher
-[:TYPE*]->          // 1 or more hops (unbounded)
-[:TYPE*1..3]->      // 1 to 3 hops
-[:TYPE*..3]->       // 1 to 3 hops
-[:TYPE*2..]->       // 2 or more hops
```

**Examples:**
```cypher
// Find all reachable friends
MATCH (p:Person {name: 'Alice'})-[:KNOWS*]->(f)
RETURN f.name

// Find friends within 2 degrees of separation
MATCH (p:Person)-[:KNOWS*1..2]->(f)
RETURN DISTINCT f.name

// Find shortest paths
MATCH path = (a:City)-[:ROAD*1..5]->(b:City)
WHERE a.name = 'NYC' AND b.name = 'LA'
RETURN path
```

**Implementation Details:**
- Depth-first search with stack-based traversal
- Per-path cycle detection (prevents infinite loops)
- Edge list accumulation for path binding
- Type and direction filtering
- Configurable min/max hop counts

**Files Changed:**
- `src/graphforge/ast/pattern.py` - Added `min_hops` and `max_hops` fields
- `src/graphforge/parser/cypher.lark` - Added variable-length syntax
- `src/graphforge/planner/operators.py` - Added `ExpandVariableLength`
- `src/graphforge/executor/executor.py` - Implemented recursive traversal

**Tests:** 2 integration tests

---

### 6. IS NULL and IS NOT NULL Operators

Proper NULL checking with boolean semantics (distinct from = NULL ternary logic).

**Syntax:**
```cypher
expression IS NULL
expression IS NOT NULL
```

**Examples:**
```cypher
// Find nodes without a property
MATCH (p:Person)
WHERE p.age IS NULL
RETURN p.name

// Filter on optional match results
MATCH (p:Person)
OPTIONAL MATCH (p)-[:KNOWS]->(f)
WHERE f IS NOT NULL
RETURN p.name, f.name
```

**Implementation Details:**
- UnaryOp representation (not BinaryOp) to distinguish from = NULL
- Boolean semantics: always returns true or false (never NULL)
- Properly handles NULL property access from OPTIONAL MATCH

**Files Changed:**
- `src/graphforge/parser/cypher.lark` - Added IS NULL grammar
- `src/graphforge/executor/evaluator.py` - Added NULL check evaluation

**Tests:** Integrated into OPTIONAL MATCH tests

---

### 7. Tree-Based Operator Structure

Foundation for nested query execution, enabling UNION and subqueries.

**Implementation Details:**
- Extended operator model to support nested branches
- `Union` operator contains multiple query branches
- `Subquery` operator for expression-level nesting
- Enables recursive query planning and execution

**Files Changed:**
- `src/graphforge/planner/operators.py` - Added nested operator support
- `src/graphforge/executor/executor.py` - Added nested dispatch logic

---

### 8. Enhanced Expression Evaluator

Improved expression evaluation with support for complex nested expressions.

**Enhancements:**
- Executor parameter threading for subquery support
- NULL property access handling
- List and map nested expression evaluation
- Support for SubqueryExpression and ListComprehension

**Files Changed:**
- `src/graphforge/executor/evaluator.py` - Updated all evaluation paths

---

## Architecture Improvements

### Operator Architecture
- **Tree-based operators**: Support for nested query execution (UNION, subqueries)
- **Left outer join primitive**: `OptionalExpandEdges` for OPTIONAL MATCH
- **Recursive traversal**: `ExpandVariableLength` for variable-length paths

### Evaluation Chain
- **Executor threading**: Pass executor and planner through evaluation chain for recursive execution
- **Context isolation**: Proper variable scoping for subqueries and comprehensions

### Serialization
- **Dual serialization systems**:
  - SQLite + MessagePack for graph data (performance)
  - Pydantic + JSON for metadata (validation, readability)

---

## Testing

### Integration Tests
- **Total integration tests**: 767 passing
- **New tests for v0.3.0**: 42+ tests across all new features
- **Coverage**: 91.96% code coverage maintained

### Test Categories
- OPTIONAL MATCH: 6 tests
- UNION/UNION ALL: 9 tests
- List comprehensions: 12 tests
- EXISTS/COUNT subqueries: 13 tests
- Variable-length paths: 2 tests

---

## TCK Compatibility

### Progress Toward 39% Goal
Starting point: 638/3,837 scenarios (16.6%)

**Features implemented** with estimated TCK impact:
1. ✅ WITH clause - Already in v0.2.0
2. ✅ OPTIONAL MATCH - ~150 scenarios
3. ✅ UNION - ~30 scenarios
4. ✅ List comprehensions - ~100 scenarios
5. ✅ EXISTS/COUNT subqueries - ~100 scenarios
6. ✅ Variable-length paths - ~100 scenarios

**Estimated new coverage**: 480+ additional scenarios
**Projected total**: ~1,100-1,200 scenarios (~30% coverage)

*Note: Final TCK numbers require full test suite validation*

---

## Breaking Changes

None. All changes are additive and maintain backward compatibility with v0.2.0 queries.

---

## Known Limitations

### Variable-Length Paths
- No configurable max depth limit in unbounded queries (defaults to unlimited)
- No query timeout mechanism (can be slow on dense graphs)
- No shortest path optimization (returns all paths within range)

### Pattern Predicates
- WHERE inside patterns not yet supported: `MATCH (a)-[r WHERE r.weight > 5]->(b)`
- Use separate WHERE clause: `MATCH (a)-[r]->(b) WHERE r.weight > 5`

### UNION
- No post-UNION ORDER BY (ORDER BY must be in each branch)
- Column name/count must match across branches

---

## Performance Considerations

### Variable-Length Paths
- Can be expensive on dense graphs with high branching factor
- Unbounded patterns (*) on social networks can explore millions of nodes
- Consider using bounded patterns (*1..3) when possible
- Cycle detection prevents infinite loops but doesn't limit exploration depth

### Subqueries
- Each EXISTS/COUNT executes full query pipeline
- Correlated subqueries re-execute for each outer row
- Consider using WITH + aggregation for better performance when possible

---

## Migration Guide

### From v0.2.0

All v0.2.0 queries continue to work unchanged. To use new features:

**Before (v0.2.0):**
```cypher
// Using LEFT JOIN pattern
MATCH (p:Person)
MATCH (p)-[:KNOWS]->(f)
RETURN p.name, COLLECT(f.name) AS friends
```

**After (v0.3.0):**
```cypher
// Using OPTIONAL MATCH
MATCH (p:Person)
OPTIONAL MATCH (p)-[:KNOWS]->(f)
RETURN p.name, COLLECT(f.name) AS friends
```

**New capabilities:**
```cypher
// List comprehensions
MATCH (p:Person)
WITH COLLECT(p.age) AS ages
RETURN [age IN ages WHERE age > 30] AS adult_ages

// Subqueries
MATCH (p:Person)
WHERE EXISTS { MATCH (p)-[:KNOWS]->(:Person {verified: true}) }
RETURN p.name

// Variable-length paths
MATCH (a)-[:FOLLOWS*1..3]->(b)
RETURN a.name, b.name
```

---

## Future Roadmap

### v0.4.0 (Planned)
- Pattern predicates (WHERE inside patterns)
- Path expressions and path functions
- Advanced aggregation functions
- Query optimization and performance tuning
- Additional TCK scenarios

### Long-term
- Shortest path algorithms
- Query hints and optimization directives
- Parallel query execution
- Advanced indexing strategies

---

## Contributors

This release was implemented with assistance from Claude Sonnet 4.5.

**Development Period**: February 2026
**Branch**: feature/103-v0.3.0-tck-coverage
**Issue**: #94

---

## Acknowledgments

This release brings GraphForge significantly closer to full openCypher compatibility, implementing features that are essential for complex graph queries in production environments. Special thanks to the openCypher and Neo4j communities for the comprehensive TCK test suite.

---

## Related Documentation

- [openCypher Compatibility Matrix](docs/reference/opencypher-compatibility.md)
- [Tutorial](docs/tutorial.md)
- [API Reference](docs/reference/api.md)

---

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/DecisionNerd/graphforge/issues
- Documentation: https://github.com/DecisionNerd/graphforge/docs
