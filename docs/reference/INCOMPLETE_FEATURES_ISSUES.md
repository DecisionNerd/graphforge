# GitHub Issues for Incomplete OpenCypher Features

**Created:** 2026-02-17
**Total Issues:** 29
**Issue Range:** #189-#217

This document tracks all GitHub issues created for partially implemented and unimplemented OpenCypher features in GraphForge.

---

## Summary by Category

| Category | Partial | Not Implemented | Total Issues | Issue Range |
|----------|---------|-----------------|--------------|-------------|
| **Clauses** | 1 | 3 | 4 | #189-#192 |
| **Functions** | 0 | 19 | 19 | #193-#211 |
| **Operators** | 0 | 4 | 4 | #212-#215 |
| **Patterns** | 1 | 1 | 2 | #216-#217 |
| **TOTAL** | **2** | **27** | **29** | #189-#217 |

---

## Clauses (4 issues)

### Partial Implementation (1)

| Issue | Feature | Status | TCK Scenarios | Priority |
|-------|---------|--------|---------------|----------|
| [#189](https://github.com/DecisionNerd/graphforge/issues/189) | CALL { } subqueries | ⚠️ PARTIAL | ~10 | Medium |

**Current:** EXISTS/COUNT subqueries only
**Needs:** General CALL { } syntax, UNION in subqueries, variable importing

### Not Implemented (3)

| Issue | Feature | Status | TCK Scenarios | Priority |
|-------|---------|--------|---------------|----------|
| [#190](https://github.com/DecisionNerd/graphforge/issues/190) | CALL procedures | ❌ NOT_IMPLEMENTED | 41 | Medium |
| [#191](https://github.com/DecisionNerd/graphforge/issues/191) | FOREACH | ❌ NOT_IMPLEMENTED | 0 | Low |
| [#192](https://github.com/DecisionNerd/graphforge/issues/192) | LOAD CSV | ❌ NOT_IMPLEMENTED | 0 | Medium |

---

## Functions (19 issues)

### String Functions (2 issues)

| Issue | Function | Status | TCK Scenarios | Priority |
|-------|----------|--------|---------------|----------|
| [#193](https://github.com/DecisionNerd/graphforge/issues/193) | length() | ❌ NOT_IMPLEMENTED | ~1 | Medium |
| [#194](https://github.com/DecisionNerd/graphforge/issues/194) | toUpper(), toLower() (camelCase) | ❌ NOT_IMPLEMENTED | ~2 | Low |

**Notes:**
- length() conflicts with path length(), needs context-dependent resolution
- UPPER/LOWER already exist, just need camelCase aliases

### Numeric Functions (3 issues)

| Issue | Function | Status | TCK Scenarios | Priority |
|-------|----------|--------|---------------|----------|
| [#195](https://github.com/DecisionNerd/graphforge/issues/195) | sqrt() | ❌ NOT_IMPLEMENTED | 0 | Medium |
| [#196](https://github.com/DecisionNerd/graphforge/issues/196) | rand() | ❌ NOT_IMPLEMENTED | 0 | Low |
| [#197](https://github.com/DecisionNerd/graphforge/issues/197) | pow() / ^ | ❌ NOT_IMPLEMENTED | 0 | Low |

### List Functions (3 issues)

| Issue | Function | Status | TCK Scenarios | Priority |
|-------|----------|--------|---------------|----------|
| [#198](https://github.com/DecisionNerd/graphforge/issues/198) | extract() | ❌ NOT_IMPLEMENTED | ~15 | **HIGH** |
| [#199](https://github.com/DecisionNerd/graphforge/issues/199) | filter() | ❌ NOT_IMPLEMENTED | ~10 | **HIGH** |
| [#200](https://github.com/DecisionNerd/graphforge/issues/200) | reduce() | ❌ NOT_IMPLEMENTED | ~5 | Medium |

**Notes:** extract() and filter() are high priority with good TCK coverage

### Aggregation Functions (4 issues)

| Issue | Function | Status | TCK Scenarios | Priority |
|-------|----------|--------|---------------|----------|
| [#201](https://github.com/DecisionNerd/graphforge/issues/201) | percentileDisc() | ❌ NOT_IMPLEMENTED | ~1 | Low |
| [#202](https://github.com/DecisionNerd/graphforge/issues/202) | percentileCont() | ❌ NOT_IMPLEMENTED | ~1 | Low |
| [#203](https://github.com/DecisionNerd/graphforge/issues/203) | stDev() | ❌ NOT_IMPLEMENTED | ~0.5 | Low |
| [#204](https://github.com/DecisionNerd/graphforge/issues/204) | stDevP() | ❌ NOT_IMPLEMENTED | ~0.5 | Low |

**Notes:** Statistical aggregations for analytics use cases

### Predicate Functions (6 issues) ⚠️ HIGH PRIORITY

| Issue | Function | Status | TCK Scenarios | Priority |
|-------|----------|--------|---------------|----------|
| [#205](https://github.com/DecisionNerd/graphforge/issues/205) | all() | ❌ NOT_IMPLEMENTED | ~8 | **HIGH** |
| [#206](https://github.com/DecisionNerd/graphforge/issues/206) | any() | ❌ NOT_IMPLEMENTED | ~8 | **HIGH** |
| [#207](https://github.com/DecisionNerd/graphforge/issues/207) | none() | ❌ NOT_IMPLEMENTED | ~4 | **HIGH** |
| [#208](https://github.com/DecisionNerd/graphforge/issues/208) | single() | ❌ NOT_IMPLEMENTED | ~4 | **HIGH** |
| [#209](https://github.com/DecisionNerd/graphforge/issues/209) | exists() | ❌ NOT_IMPLEMENTED | ~10 | **HIGH** |
| [#210](https://github.com/DecisionNerd/graphforge/issues/210) | isEmpty() | ❌ NOT_IMPLEMENTED | ~2 | Medium |

**Notes:**
- All predicate functions are HIGH PRIORITY
- Commonly used in WHERE clauses
- ~36 TCK scenarios total
- exists() is distinct from EXISTS() subquery expression (already implemented)

### Scalar Functions (1 issue)

| Issue | Function | Status | TCK Scenarios | Priority |
|-------|----------|--------|---------------|----------|
| [#211](https://github.com/DecisionNerd/graphforge/issues/211) | elementId() | ❌ NOT_IMPLEMENTED | 0 | Low |

**Notes:** GQL standard function, alternative to id()

---

## Operators (4 issues)

### Logical Operators (1 issue)

| Issue | Operator | Status | TCK Scenarios | Priority |
|-------|----------|--------|---------------|----------|
| [#212](https://github.com/DecisionNerd/graphforge/issues/212) | XOR | ❌ NOT_IMPLEMENTED | 0 | Low |

### Arithmetic Operators (1 issue)

| Issue | Operator | Status | TCK Scenarios | Priority |
|-------|----------|--------|---------------|----------|
| [#213](https://github.com/DecisionNerd/graphforge/issues/213) | ^ (power) | ❌ NOT_IMPLEMENTED | 0 | Low |

**Notes:** Related to pow() function (#197), should be implemented together

### List Operators (2 issues)

| Issue | Operator | Status | TCK Scenarios | Priority |
|-------|----------|--------|---------------|----------|
| [#214](https://github.com/DecisionNerd/graphforge/issues/214) | [start..end] slicing | ❌ NOT_IMPLEMENTED | Unknown | Medium |
| [#215](https://github.com/DecisionNerd/graphforge/issues/215) | Negative indexing | ❌ NOT_IMPLEMENTED | Unknown | Medium |

**Notes:** Python-style list operations

---

## Patterns (2 issues)

### Partial Implementation (1)

| Issue | Feature | Status | TCK Scenarios | Priority |
|-------|---------|--------|---------------|----------|
| [#216](https://github.com/DecisionNerd/graphforge/issues/216) | Pattern predicates | ⚠️ PARTIAL | ~15 | Medium |

**Current:** Basic WHERE in patterns
**Needs:** Full pattern predicate support

### Not Implemented (1)

| Issue | Feature | Status | TCK Scenarios | Priority |
|-------|---------|--------|---------------|----------|
| [#217](https://github.com/DecisionNerd/graphforge/issues/217) | Pattern comprehension | ❌ NOT_IMPLEMENTED | 15 | Medium |

**Notes:** Complex feature combining pattern matching with list comprehension

---

## Priority Recommendations

### High Priority (Good TCK Coverage, High Impact)

**Predicate Functions (6 issues: #205-#210)**
- ~36 TCK scenarios total
- Commonly used in WHERE clauses
- Moderate implementation complexity
- **Recommended for v0.5.0**

**List Operations (2 issues: #198-#199)**
- ~25 TCK scenarios (extract + filter)
- Useful for data transformation
- **Recommended for v0.5.0**

### Medium Priority

**Pattern Features (2 issues: #216-#217)**
- ~30 TCK scenarios combined
- Improves query expressiveness

**CALL Procedures (1 issue: #190)**
- 41 TCK scenarios
- Requires significant architecture (procedure registry)

**List Operators (2 issues: #214-#215)**
- Common operations, relatively simple

### Low Priority

**Statistical Aggregations (4 issues: #201-#204)**
- Minimal TCK coverage (~3 scenarios)
- Useful for analytics

**Math Functions (3 issues: #195-#197)**
- Minimal/no TCK coverage
- Can use alternatives

**XOR Operator (1 issue: #212)**
- No TCK scenarios, rarely used

**Other Clauses (2 issues: #191-#192)**
- No TCK scenarios
- FOREACH rarely used (UNWIND alternative)
- LOAD CSV has dataset system alternative

---

## Issue Template

All issues follow this template:

### Feature Information
- Type (Clause/Function/Operator/Pattern)
- Category
- Current Status (PARTIAL/NOT_IMPLEMENTED)

### Documentation References
- Implementation Status document
- Feature Documentation document
- Compatibility Matrix

### TCK Coverage
- Scenario count
- TCK mapping document reference

### Acceptance Criteria
- **Implementation:** Specific implementation requirements
- **Testing:** Unit tests, integration tests, TCK pass rate, 90% coverage minimum
- **Documentation:** Update all relevant docs, add examples, update CHANGELOG

### Notes
- Context and priority information
- Related issues
- Implementation considerations

---

## Tracking Progress

### v0.5.0 Target
- **Focus:** Predicate functions + List operations (8 issues: #198-#199, #205-#210)
- **Impact:** ~60 TCK scenarios, 78% → ~82% feature completeness
- **Time Estimate:** 2-3 months (March-May 2026)

### v0.6.0 Target
- **Focus:** Pattern features + CALL procedures (3 issues: #190, #216-#217)
- **Impact:** ~86 TCK scenarios, 82% → ~88% feature completeness

### v0.7.0+ Target
- **Focus:** Remaining functions + operators (18 issues: remaining)
- **Impact:** 88% → 95%+ feature completeness

---

## References

- **Documentation:** [docs/reference/](../docs/reference/)
- **Validation Report:** [docs/reference/VALIDATION_REPORT.md](VALIDATION_REPORT.md)
- **Compatibility Matrix:** [docs/reference/opencypher-compatibility-matrix.md](opencypher-compatibility-matrix.md)
- **Issue #103:** TCK Coverage v0.4.0 (parent tracking issue)
- **GitHub Milestones:** https://github.com/DecisionNerd/graphforge/milestones

---

**Created:** 2026-02-17
**Last Updated:** 2026-02-17
**Maintainer:** [@DecisionNerd](https://github.com/DecisionNerd)
