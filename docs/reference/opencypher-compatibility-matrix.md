# OpenCypher Compatibility Matrix

Comprehensive status matrix for GraphForge's OpenCypher implementation, showing features, implementation status, and TCK test coverage.

**Last Updated:** 2026-02-16
**GraphForge Version:** v0.4.0 (in progress)
**TCK Scenarios:** 1,626 total, 1,303 passing (34% pass rate)

---

## Executive Summary

| Category | Total Features | Complete | Partial | Not Implemented | TCK Scenarios | Coverage |
|----------|---------------|----------|---------|-----------------|---------------|----------|
| **Clauses** | 20 | 16 (80%) | 1 (5%) | 3 (15%) | ~1,180 | Good |
| **Functions** | 72 | 53 (74%) | 0 (0%) | 19 (26%) | ~380 | Good |
| **Operators** | 34 | 30 (88%) | 0 (0%) | 4 (12%) | ~300 | Good |
| **Patterns** | 8 | 6 (75%) | 1 (12%) | 1 (13%) | ~200 | Good |
| **TOTAL** | **134** | **105 (78%)** | **2 (2%)** | **27 (20%)** | **~2,060** | **Good** |

### Overall Compliance: **~78% Feature Complete**

---

## Quick Reference

### ✅ Fully Supported (105 features)
- Core querying: MATCH, RETURN, WHERE, ORDER BY, LIMIT, SKIP
- Query chaining: WITH (full spec compliance)
- Writing: CREATE, MERGE, SET, REMOVE, DELETE, DETACH DELETE
- Advanced: OPTIONAL MATCH, UNION, UNWIND, variable-length paths
- Temporal: All date/time types and functions (100% complete)
- Spatial: Point and distance functions (100% complete)
- Pattern matching: All node/relationship pattern variations

### ⚠️ Partially Supported (2 features)
- CALL { } subqueries (EXISTS/COUNT only, general syntax missing)
- Pattern predicates (basic WHERE in patterns, needs completion)

### ❌ Not Supported (27 features)
- CALL procedures (no procedure system)
- Predicate functions (all, any, none, single, isEmpty)
- List operations (extract, filter, reduce)
- Pattern comprehension
- Some math functions (sqrt, rand, pow)
- Statistical aggregations (percentile, stdev)

---

## Detailed Feature Matrix

### Clauses (20 total: 16 complete, 1 partial, 3 not implemented)

| Clause | Status | TCK Scenarios | Implementation Files | Notes |
|--------|--------|---------------|---------------------|-------|
| **MATCH** | ✅ Complete | 195 | executor.py:368, 554, 820 | All pattern types supported |
| **CREATE** | ✅ Complete | 78 | executor.py:1921 | Full pattern creation |
| **RETURN** | ✅ Complete | 129 | executor.py:1037 | With DISTINCT, aliases, aggregation |
| **WHERE** | ✅ Complete | 53 | executor.py:1021 | All predicates, NULL handling |
| **WITH** | ✅ Complete | 156 | executor.py:1072 | Full spec (v0.3.0) |
| **ORDER BY** | ✅ Complete | 134 | executor.py:1248 | ASC/DESC, multiple keys, NULL ordering |
| **LIMIT** | ✅ Complete | 40 | executor.py:1201 | Result limiting |
| **SKIP** | ✅ Complete | 40 | executor.py:1205 | Pagination support |
| **MERGE** | ✅ Complete | 75 | executor.py:2269 | With ON CREATE/MATCH |
| **SET** | ✅ Complete | 53 | executor.py:2096 | Property/label updates |
| **REMOVE** | ✅ Complete | 33 | executor.py:2116 | Property/label removal |
| **DELETE** | ✅ Complete | 41 | executor.py:2173 | Node/relationship deletion |
| **DETACH DELETE** | ✅ Complete | 41 | executor.py:2173 | Cascade deletion |
| **UNWIND** | ✅ Complete | 14 | executor.py:2687 | List expansion |
| **UNION/UNION ALL** | ✅ Complete | 12 | executor.py:2855 | Set operations |
| **OPTIONAL MATCH** | ✅ Complete | ~20 | executor.py:483, 2732 | NULL handling |
| **CALL { }** | ⚠️ Partial | 10 | executor.py:2954 | EXISTS/COUNT only |
| **CALL** | ❌ Not Implemented | 41 | N/A | Procedures not supported |
| **FOREACH** | ❌ Not Implemented | 0 | N/A | Low priority |
| **LOAD CSV** | ❌ Not Implemented | 0 | N/A | Use dataset system |

---

### Functions (72 total: 53 complete, 0 partial, 19 not implemented)

#### String Functions (13 total: 11 complete, 2 not implemented)

| Function | Status | TCK Scenarios | File | Notes |
|----------|--------|---------------|------|-------|
| substring() | ✅ Complete | 4 | evaluator.py:1185 | 2 and 3 arg forms |
| trim(), ltrim(), rtrim() | ✅ Complete | 3 | evaluator.py:1220, 1275, 1289 | Whitespace trimming |
| upper(), lower() | ✅ Complete | 3 | evaluator.py:1210, 1215 | Case conversion |
| split() | ✅ Complete | 2 | evaluator.py:1230 | String splitting |
| replace() | ✅ Complete | 2 | evaluator.py:1246 | String replacement |
| reverse() | ✅ Complete | 2 | evaluator.py:1225 | String reversal |
| left(), right() | ✅ Complete | 2 | evaluator.py:1303, 1320 | Substring extraction |
| toString() | ✅ Complete | 5 | evaluator.py:1569 | Type conversion |
| length() | ❌ Not Implemented | 1 | N/A | Conflicts with path length() |
| toUpper/toLower (camelCase) | ❌ Not Implemented | 2 | N/A | Only UPPER/LOWER aliases |

#### Numeric Functions (10 total: 7 complete, 3 not implemented)

| Function | Status | TCK Scenarios | File | Notes |
|----------|--------|---------------|------|-------|
| abs() | ✅ Complete | 1 | evaluator.py:1327 | Absolute value |
| ceil(), floor() | ✅ Complete | 1 | evaluator.py:1337, 1351 | Rounding |
| round() | ✅ Complete | 1 | evaluator.py:1369 | With precision |
| sign() | ✅ Complete | 1 | evaluator.py:1409 | Sign of number |
| toInteger(), toFloat() | ✅ Complete | 2 | evaluator.py:1556, 1600 | Type conversion |
| sqrt() | ❌ Not Implemented | 0 | N/A | Square root |
| rand() | ❌ Not Implemented | 0 | N/A | Random number |
| pow() / ^ | ❌ Not Implemented | 0 | N/A | Power operator |

#### List Functions (8 total: 6 complete, 2 not implemented)

| Function | Status | TCK Scenarios | File | Notes |
|----------|--------|---------------|------|-------|
| size() | ✅ Complete | 15 | evaluator.py:2720 | List/string length |
| head(), last() | ✅ Complete | 10 | evaluator.py:2739, 2768 | First/last element |
| tail() | ✅ Complete | 8 | evaluator.py:2753 | All but first |
| range() | ✅ Complete | 12 | evaluator.py:2787 | Integer sequence |
| reverse() | ✅ Complete | 5 | evaluator.py:1225 | List reversal |
| extract() | ❌ Not Implemented | 15 | N/A | List comprehension |
| filter() | ❌ Not Implemented | 10 | N/A | List filtering |
| reduce() | ❌ Not Implemented | 5 | N/A | List reduction |

#### Aggregation Functions (10 total: 5 complete, 5 not implemented)

| Function | Status | TCK Scenarios | File | Notes |
|----------|--------|---------------|------|-------|
| count() | ✅ Complete | 8 | executor.py | With DISTINCT |
| sum() | ✅ Complete | 4 | executor.py | Numeric sum |
| avg() | ✅ Complete | 3 | executor.py | Average |
| min(), max() | ✅ Complete | 5 | executor.py | Min/max values |
| collect() | ✅ Complete | 4 | executor.py | Collect to list |
| percentileDisc(), percentileCont() | ❌ Not Implemented | 2 | N/A | Percentiles |
| stDev(), stDevP() | ❌ Not Implemented | 1 | N/A | Standard deviation |

#### Predicate Functions (6 total: 0 complete, 6 not implemented) ⚠️ HIGH PRIORITY

| Function | Status | TCK Scenarios | File | Notes |
|----------|--------|---------------|------|-------|
| all() | ❌ Not Implemented | 8 | N/A | All elements match |
| any() | ❌ Not Implemented | 8 | N/A | Any element matches |
| none() | ❌ Not Implemented | 4 | N/A | No elements match |
| single() | ❌ Not Implemented | 4 | N/A | Exactly one matches |
| exists() | ❌ Not Implemented | 10 | N/A | Property/pattern exists |
| isEmpty() | ❌ Not Implemented | 2 | N/A | Empty list/string |

#### Scalar Functions (9 total: 8 complete, 1 not implemented)

| Function | Status | TCK Scenarios | File | Notes |
|----------|--------|---------------|------|-------|
| id() | ✅ Complete | 8 | evaluator.py:2537 | Element ID |
| type() | ✅ Complete | 6 | evaluator.py:2558 | Relationship type |
| labels() | ✅ Complete | 6 | evaluator.py:2583 | Node labels |
| properties() | ✅ Complete | 4 | N/A | Property map |
| keys() | ✅ Complete | 4 | N/A | Property keys |
| coalesce() | ✅ Complete | 8 | evaluator.py:1035 | First non-NULL |
| toBoolean() | ✅ Complete | 5 | evaluator.py:1644 | Boolean conversion |
| timestamp() | ✅ Complete | 2 | N/A | Current time |
| elementId() | ❌ Not Implemented | 0 | N/A | GQL spec feature |

#### Temporal Functions (11 total: 11 complete) ✅ COMPLETE CATEGORY

| Function | Status | TCK Scenarios | File | Notes |
|----------|--------|---------------|------|-------|
| date() | ✅ Complete | 15 | evaluator.py:1738 | Date creation |
| datetime() | ✅ Complete | 20 | evaluator.py:1807 | DateTime creation |
| time() | ✅ Complete | 12 | evaluator.py:1973 | Time creation |
| localtime() | ✅ Complete | 8 | evaluator.py:2084 | Local time |
| localdatetime() | ✅ Complete | 10 | evaluator.py:2145 | Local datetime |
| duration() | ✅ Complete | 12 | evaluator.py:2225 | Duration creation |
| year(), month(), day() | ✅ Complete | 8 | Various | Component accessors |
| hour(), minute(), second() | ✅ Complete | 8 | Various | Time accessors |
| truncate() | ✅ Complete | 4 | evaluator.py:919 | Temporal truncation |

#### Spatial Functions (2 total: 2 complete) ✅ COMPLETE CATEGORY

| Function | Status | TCK Scenarios | File | Notes |
|----------|--------|---------------|------|-------|
| point() | ✅ Complete | 6 | evaluator.py:2431 | Point creation (2D/3D) |
| distance() | ✅ Complete | 4 | evaluator.py:2469 | Distance calculation |

#### Path Functions (3 total: 3 complete) ✅ COMPLETE CATEGORY

| Function | Status | TCK Scenarios | File | Notes |
|----------|--------|---------------|------|-------|
| length() | ✅ Complete | 3 | evaluator.py:2604 | Path length |
| nodes() | ✅ Complete | 2 | evaluator.py:2622 | Path nodes |
| relationships() | ✅ Complete | 2 | evaluator.py:2657 | Path relationships |

---

### Operators (34 total: 30 complete, 0 partial, 4 not implemented)

#### Comparison Operators (8 total: 8 complete) ✅ COMPLETE CATEGORY

| Operator | Status | TCK Scenarios | Notes |
|----------|--------|---------------|-------|
| = | ✅ Complete | ~40 | Equality with NULL handling |
| <> | ✅ Complete | ~30 | Inequality |
| <, >, <=, >= | ✅ Complete | ~50 | Ordering comparisons |
| IS NULL, IS NOT NULL | ✅ Complete | ~20 | NULL testing |

#### Logical Operators (4 total: 3 complete, 1 not implemented)

| Operator | Status | TCK Scenarios | Notes |
|----------|--------|---------------|-------|
| AND | ✅ Complete | ~40 | Ternary logic |
| OR | ✅ Complete | ~35 | Ternary logic |
| NOT | ✅ Complete | ~25 | Ternary logic |
| XOR | ❌ Not Implemented | 0 | Exclusive or |

#### Arithmetic Operators (6 total: 5 complete, 1 not implemented)

| Operator | Status | TCK Scenarios | Notes |
|----------|--------|---------------|-------|
| +, -, *, /, % | ✅ Complete | ~100 | Standard arithmetic |
| ^ | ❌ Not Implemented | 0 | Power operator |

#### String Operators (5 total: 5 complete) ✅ COMPLETE CATEGORY

| Operator | Status | TCK Scenarios | Notes |
|----------|--------|---------------|-------|
| + | ✅ Complete | ~15 | Concatenation |
| =~ | ✅ Complete | ~8 | Regex match |
| STARTS WITH, ENDS WITH, CONTAINS | ✅ Complete | ~20 | Pattern matching |

#### List Operators (5 total: 3 complete, 2 not implemented)

| Operator | Status | TCK Scenarios | Notes |
|----------|--------|---------------|-------|
| IN | ✅ Complete | ~25 | Membership test |
| [] | ✅ Complete | ~20 | Index access |
| + | ✅ Complete | ~10 | List concatenation |
| [start..end] | ❌ Not Implemented | 0 | List slicing |
| Negative indexing | ❌ Not Implemented | 0 | Negative indices |

#### Pattern Operators (5 total: 5 complete) ✅ COMPLETE CATEGORY

| Operator | Status | TCK Scenarios | Notes |
|----------|--------|---------------|-------|
| - | ✅ Complete | ~60 | Undirected relationship |
| ->, <-- | ✅ Complete | ~100 | Directed relationships |
| -[*]- | ✅ Complete | ~40 | Variable-length |
| : | ✅ Complete | ~50 | Label check |

---

### Patterns (8 total: 6 complete, 1 partial, 1 not implemented)

| Pattern Type | Status | TCK Scenarios | Notes |
|--------------|--------|---------------|-------|
| Node patterns | ✅ Complete | ~100 | All variations supported |
| Relationship patterns | ✅ Complete | ~100 | Direction, types, properties |
| Variable-length paths | ✅ Complete | ~40 | All quantifier forms |
| Path variables | ✅ Complete | ~20 | Path binding |
| OPTIONAL patterns | ✅ Complete | ~20 | NULL handling |
| Multiple patterns | ✅ Complete | ~30 | Comma-separated |
| Pattern predicates | ⚠️ Partial | ~15 | Basic WHERE in patterns |
| Pattern comprehension | ❌ Not Implemented | 15 | Not supported |

---

## Implementation Priorities for v0.4.0+

### High Priority (Good TCK Coverage, High Impact)

1. **Predicate functions** (all, any, none, single)
   - 36 TCK scenarios available
   - Commonly used in WHERE clauses
   - Moderate implementation complexity

2. **Complete pattern predicates**
   - 15+ TCK scenarios
   - Part of core pattern matching
   - Improves query expressiveness

3. **List slicing [start..end]**
   - Common operation
   - Relatively simple to implement

### Medium Priority (Some TCK Coverage, Useful)

4. **List operations** (extract, filter, reduce)
   - 30 TCK scenarios
   - Useful for data transformation
   - Higher implementation complexity

5. **sqrt() function**
   - Common mathematical operation
   - Simple to implement

6. **Statistical aggregations** (percentile, stdev)
   - 3 TCK scenarios
   - Useful for analytics

### Low Priority (Minimal TCK Coverage or Low Usage)

7. **Pattern comprehension**
   - 15 TCK scenarios
   - Complex feature
   - Can use alternatives

8. **XOR operator**
   - 0 TCK scenarios
   - Rarely used

9. **Power operator (^)**
   - 0 TCK scenarios
   - Can use alternatives

10. **rand() function**
    - 0 TCK scenarios
    - Non-deterministic

---

## Version History

### v0.1.0 (Initial Release)
- Basic MATCH, CREATE, RETURN
- Core pattern matching
- String and numeric functions

### v0.2.0
- SET, REMOVE, DELETE, MERGE
- UNWIND clause
- Enhanced aggregations

### v0.3.0
- **OPTIONAL MATCH** (full NULL handling)
- **WITH clause** (full spec compliance)
- **UNION/UNION ALL**
- **Temporal functions** (complete)
- **Spatial functions** (complete)
- **EXISTS/COUNT subqueries**
- TCK pass rate: 16.6% → 32.6%

### v0.4.0 (In Progress)
- TCK coverage improvements
- Edge case fixes
- Documentation expansion
- **Goal:** Identify priority features for v0.5.0

---

## TCK Compliance Metrics

### Current Status
- **Total scenarios:** 1,626
- **Passing:** 1,303 (34% pass rate)
- **Failing:** 323 (20%)

### Pass Rate by Category

| Category | Scenarios | Passing | Pass Rate |
|----------|-----------|---------|-----------|
| Clauses (implemented) | ~780 | ~650 | ~83% |
| Expressions (implemented) | ~300 | ~220 | ~73% |
| Functions (implemented) | ~190 | ~150 | ~79% |
| Patterns | ~180 | ~160 | ~89% |

### Primary Failure Reasons

1. **Missing functions** (26%)
   - Predicate functions
   - List operations
   - Statistical aggregations

2. **Missing operators** (12%)
   - XOR, power, list slicing

3. **Pattern comprehension** (8%)

4. **Edge cases** (20%)
   - NULL handling in complex queries
   - Type coercion corner cases
   - Nested query scenarios

5. **CALL procedures** (25%)
   - Entire category not implemented

6. **Unimplemented clauses** (9%)
   - FOREACH, LOAD CSV

---

## Strengths & Limitations

### Major Strengths ✅

1. **Complete temporal support** (v0.3.0)
   - All date/time types
   - All temporal functions
   - Duration arithmetic

2. **Complete spatial support** (v0.3.0)
   - 2D/3D points
   - Cartesian/Geographic
   - Distance calculations

3. **Advanced query features**
   - OPTIONAL MATCH with proper NULL handling
   - WITH clause (full spec)
   - UNION operations
   - Variable-length paths

4. **Comprehensive pattern matching**
   - All node/relationship variations
   - Variable-length paths
   - Path variables and functions

5. **Core querying solid**
   - MATCH, CREATE, MERGE, RETURN all complete
   - WHERE with ternary logic
   - ORDER BY, LIMIT, SKIP

### Key Limitations ❌

1. **No procedure system**
   - CALL procedures not supported
   - 41 TCK scenarios skipped

2. **Missing predicate functions**
   - all(), any(), none(), single(), exists(), isEmpty()
   - 36 TCK scenarios failing

3. **Limited list operations**
   - extract(), filter(), reduce() not implemented
   - 30 TCK scenarios failing

4. **Pattern comprehension not supported**
   - Complex feature
   - 15 TCK scenarios failing

5. **Some mathematical functions missing**
   - sqrt(), rand(), pow()
   - Minimal TCK impact

---

## How to Use This Matrix

### For Contributors

1. **Prioritizing work:** Use "Implementation Priorities" section
2. **Finding implementation:** Use "File" column for line references
3. **Understanding coverage:** Check TCK Scenarios column
4. **Identifying gaps:** See ❌ Not Implemented rows

### For Users

1. **Feature support:** Check Status column (✅ ⚠️ ❌)
2. **Workarounds:** See Notes column for alternatives
3. **Completeness:** Check TCK Scenarios for test coverage
4. **Version planning:** See Version History for feature timeline

### For Researchers

1. **Compliance analysis:** Use Executive Summary statistics
2. **Coverage metrics:** See TCK Compliance Metrics section
3. **Trend analysis:** Compare across versions
4. **Gap analysis:** Review Implementation Priorities

---

## Related Documentation

- **Feature Documentation:** `docs/reference/opencypher-features/`
  - Detailed spec for each feature
- **Implementation Status:** `docs/reference/implementation-status/`
  - Per-category status with file references
- **TCK Mapping:** `docs/reference/feature-mapping/`
  - TCK test to feature mapping
- **TCK Inventory:** `docs/reference/tck-inventory.md`
  - Complete TCK scenario catalog
- **Graph Schema:** `docs/reference/feature-graph-schema.md`
  - Queryable feature knowledge graph

---

## References

- OpenCypher Specification: https://opencypher.org/resources/
- OpenCypher TCK: https://github.com/opencypher/openCypher/tree/master/tck
- GraphForge Repository: https://github.com/DecisionNerd/graphforge
- GQL Standard (ISO/IEC 39075): https://www.iso.org/standard/76120.html
