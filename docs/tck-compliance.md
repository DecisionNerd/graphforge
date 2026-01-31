# openCypher TCK Compliance

GraphForge implements strict compliance with openCypher semantics through comprehensive TCK (Technology Compatibility Kit) tests.

## TCK Test Suite

Location: `tests/tck/test_tck_compliance.py`

The test suite validates GraphForge's compliance with openCypher standards across multiple feature areas:

### Test Coverage

**TestTCKMatch** (5 tests)
- Match all nodes
- Match nodes by label
- Match with WHERE clause filtering
- LIMIT clause
- SKIP clause with ORDER BY

**TestTCKAggregation** (6 tests)
- COUNT(*) - count all rows
- COUNT(expr) - count non-NULL values
- SUM aggregation
- AVG aggregation
- MIN and MAX aggregation
- Grouping with aggregation

**TestTCKOrderBy** (3 tests)
- ORDER BY ASC (ascending sort)
- ORDER BY DESC (descending sort)
- ORDER BY multiple keys

**TestTCKNullSemantics** (3 tests)
- NULL property access
- NULL in comparisons (three-valued logic)
- COUNT with NULL handling

**Total: 17 TCK compliance tests, all passing**

## Standards Compliance Features

### 1. ORDER BY with RETURN Aliases

GraphForge correctly implements the openCypher specification that allows ORDER BY clauses to reference aliases defined in the RETURN clause.

Example:
```cypher
MATCH (p:Person)
RETURN p.name AS name
ORDER BY name
```

**Implementation**: The Sort operator pre-evaluates non-aggregate RETURN expressions and temporarily extends the ExecutionContext with alias bindings. This allows ORDER BY to reference both original variables and RETURN aliases while maintaining correct operator execution order.

### 2. Aggregation with Grouping

Implicit GROUP BY semantics following SQL-style aggregation:
- Non-aggregated expressions in RETURN become grouping keys
- Aggregation functions compute over groups
- Supports ORDER BY on grouped results

Example:
```cypher
MATCH (p:Person)
RETURN p.city AS city, COUNT(*) AS count
ORDER BY city
```

### 3. NULL Semantics

Strict three-valued logic (TRUE, FALSE, NULL):
- Missing properties return NULL
- Comparisons with NULL return NULL (not TRUE or FALSE)
- WHERE clause filters out NULL predicates
- COUNT(*) counts all rows, COUNT(expr) ignores NULLs
- Sorting: ASC places NULLs last, DESC places NULLs first

### 4. Multi-key Sorting

Supports sorting by multiple expressions with independent ASC/DESC directions:
```cypher
MATCH (p:Person)
RETURN p.name
ORDER BY p.age ASC, p.name ASC
```

## Implementation Details

### Operator Pipeline Order

Critical for TCK compliance:

1. **MATCH** (ScanNodes, ExpandEdges)
2. **WHERE** (Filter)
3. **ORDER BY** (Sort) - executes before RETURN
4. **RETURN** (Project or Aggregate)
5. **SKIP/LIMIT**

ORDER BY must execute before RETURN projection to:
- Access all variables from MATCH
- Support sorting on expressions not in RETURN
- Enable RETURN alias references through pre-evaluation

### Sort Operator Enhancements

The Sort operator includes optional `return_items` parameter:
- When present, pre-evaluates non-aggregate RETURN expressions
- Binds evaluated values to alias names in temporary context
- Allows ORDER BY to reference RETURN aliases
- Skips aggregate functions (evaluated later by Aggregate operator)

### Files Modified

**src/graphforge/planner/operators.py**
- Added `return_items` field to Sort operator

**src/graphforge/planner/planner.py**
- Pass return_items to Sort when ORDER BY and RETURN both present

**src/graphforge/executor/executor.py**
- Pre-evaluate RETURN aliases in _execute_sort
- Extend ExecutionContext with alias bindings
- Map back to original contexts after sorting

## Running TCK Tests

Run the full TCK compliance suite:
```bash
pytest tests/tck/test_tck_compliance.py -v
```

Run specific test class:
```bash
pytest tests/tck/test_tck_compliance.py::TestTCKAggregation -v
```

Run with TCK marker:
```bash
pytest -m tck -v
```

## Future TCK Work

Additional openCypher TCK scenarios to implement:
- CREATE/UPDATE/DELETE clauses
- MERGE clause
- OPTIONAL MATCH
- Path patterns
- List operations
- String functions
- WITH clause
- UNION queries
- Subqueries

## References

- [openCypher specification](https://opencypher.org/)
- [openCypher TCK repository](https://github.com/opencypher/openCypher/tree/master/tck)
