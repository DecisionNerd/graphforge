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

## Patch-Level Release Strategy

**New Approach:** All features will be completed in patch releases (v0.3.x) until 100% complete.

### v0.3.1 (Target: March 2026) - Predicate Functions
**Goal:** 78% → 82% feature complete

**Issues (6): #205-#210**
- all() predicate function
- any() predicate function
- none() predicate function
- single() predicate function
- exists() predicate function
- isEmpty() predicate function

**Impact:** ~36 TCK scenarios, commonly used in WHERE clauses

### v0.3.2 (Target: April 2026) - List Operations
**Goal:** 82% → 85% feature complete

**Issues (3): #198-#200**
- extract() list function
- filter() list function
- reduce() list function

**Impact:** ~30 TCK scenarios, essential for data transformation

### v0.3.3 (Target: May 2026) - Pattern & CALL Features
**Goal:** 85% → 88% feature complete

**Issues (3): #189, #216-#217**
- Complete CALL { } subquery syntax (PARTIAL → COMPLETE)
- Complete pattern predicates (PARTIAL → COMPLETE)
- Pattern comprehension

**Impact:** ~40 TCK scenarios, advanced query capabilities

### v0.3.4 (Target: June 2026) - Operators & String Functions
**Goal:** 88% → 92% feature complete

**Issues (6): #193-#194, #212-#215**
- length() string function
- toUpper/toLower camelCase variants
- XOR logical operator
- ^ (power) arithmetic operator
- List slicing [start..end]
- Negative list indexing

**Impact:** Operator completeness, string function parity

### v0.3.5 (Target: July 2026) - Math & Aggregation Functions
**Goal:** 92% → 96% feature complete

**Issues (7): #195-#197, #201-#204**
- sqrt() function
- rand() function
- pow() function
- percentileDisc() aggregation
- percentileCont() aggregation
- stDev() aggregation
- stDevP() aggregation

**Impact:** Mathematical operations complete, statistical analysis support

### v0.3.6 (Target: August 2026) - Remaining Clauses
**Goal:** 96% → 99% feature complete

**Issues (4): #190-#192, #211**
- CALL procedures (with procedure registry)
- FOREACH clause
- LOAD CSV clause
- elementId() scalar function

**Impact:** Procedural capabilities, data import, GQL compliance

### v0.3.7 (Target: September 2026) - Final Polish
**Goal:** 99% → 100% feature complete

**Focus:**
- Edge case fixes from TCK
- Documentation completeness
- Performance optimization
- API refinements

**Result:** 134/134 features complete (100%)

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

### Overall Timeline

**Start:** v0.3.0 (Feb 2026) - 78% complete (105/134 features)
**End:** v0.3.7 (Sep 2026) - 100% complete (134/134 features)
**Duration:** 7 months with 7 patch releases

### Monthly Milestones

| Month | Release | Features Added | Total Complete | Percentage |
|-------|---------|----------------|----------------|------------|
| Feb 2026 | v0.3.0 | - | 105/134 | 78% |
| Mar 2026 | v0.3.1 | 6 predicates | 111/134 | 82% |
| Apr 2026 | v0.3.2 | 3 list ops | 114/134 | 85% |
| May 2026 | v0.3.3 | 3 patterns | 117/134 | 88% |
| Jun 2026 | v0.3.4 | 6 operators | 123/134 | 92% |
| Jul 2026 | v0.3.5 | 7 math/agg | 130/134 | 96% |
| Aug 2026 | v0.3.6 | 4 clauses | 134/134 | 99% |
| Sep 2026 | v0.3.7 | Polish | 134/134 | **100%** |

### Feature Completion by Category

| Category | v0.3.0 | v0.3.7 | Change |
|----------|--------|--------|--------|
| Clauses | 16/20 (80%) | 20/20 (100%) | +4 |
| Functions | 53/72 (74%) | 72/72 (100%) | +19 |
| Operators | 30/34 (88%) | 34/34 (100%) | +4 |
| Patterns | 6/8 (75%) | 8/8 (100%) | +2 |
| **TOTAL** | **105/134 (78%)** | **134/134 (100%)** | **+29** |

---

## References

- **Documentation:** [docs/reference/](../docs/reference/)
- **Validation Report:** [docs/reference/VALIDATION_REPORT.md](VALIDATION_REPORT.md)
- **Compatibility Matrix:** [docs/reference/opencypher-compatibility-matrix.md](opencypher-compatibility-matrix.md)
- **Issue #103:** TCK Coverage v0.4.0 (parent tracking issue)
- **GitHub Milestones:** https://github.com/DecisionNerd/graphforge/milestones

---

**Created:** 2026-02-17
**Last Updated:** 2026-02-17 (Updated for patch-level release strategy)
**Maintainer:** [@DecisionNerd](https://github.com/DecisionNerd)
