# GraphForge Implementation Plan
## Open Issues Analysis & Prioritized Roadmap

**Date:** 2026-02-08
**Current Status:** v0.3.0 features partially complete, 29% TCK coverage achieved

---

## Executive Summary

GraphForge has made significant progress with recent work completing major v0.3.0 features (OPTIONAL MATCH, UNION, list comprehensions, EXISTS/COUNT subqueries, variable-length paths). The project is at 29% TCK coverage with 4 open issues remaining. This plan prioritizes completing the dataset integration milestone (#61, #52) before continuing TCK coverage improvements (#103).

**Key Achievements (Recent):**
- ✅ OPTIONAL MATCH with IS NULL support
- ✅ UNION/UNION ALL operators
- ✅ List comprehensions
- ✅ EXISTS/COUNT subquery expressions
- ✅ Variable-length path patterns (-[:REL*1..3]->)
- ✅ Tree-based operator architecture
- ✅ GraphML loader (#101)
- ✅ Zip compression support (#102)
- ✅ MERGE ON CREATE/MATCH SET (#57, #58)
- ✅ WITH clause variable passing (#60)

---

## Current Open Issues (4 Total)

### Priority 1: Dataset Integration (Quick Wins)

#### Issue #52: Add NetworkRepository Dataset Integration
**Status:** Ready to implement
**Estimated Effort:** 3-4.5 hours
**Dependencies:** ✅ #93 (GraphML loader) - COMPLETE
**Impact:** Adds 10-15 high-quality datasets for research

**Rationale for Priority:**
- All dependencies resolved (GraphML loader implemented)
- Straightforward implementation (metadata registration)
- High value for users (popular research datasets)
- Quick win to show progress
- Completes dataset catalog diversity

**Implementation Steps:**
1. Create `src/graphforge/datasets/sources/networkrepository.py` (~80 lines)
2. Create `src/graphforge/datasets/data/networkrepository.json` (~300 lines)
3. Register 10-15 datasets (karate, dolphins, polbooks, football, etc.)
4. Add integration tests in `tests/integration/datasets/test_networkrepository_loader.py`
5. Create documentation in `docs/datasets/networkrepository.md`
6. Test loading, caching, and querying

**Success Criteria:**
- All 10-15 datasets load successfully
- Node/edge counts match documentation
- Caching works correctly
- Integration tests verify properties and queries
- 100% test coverage on new code

---

#### Issue #61: v0.3.0 Milestone - Full Dataset Integration
**Status:** Nearly complete, final validation needed
**Estimated Effort:** 2-3 hours
**Dependencies:**
- ✅ #57 (MERGE ON CREATE SET) - CLOSED
- ✅ #58 (MERGE ON MATCH SET) - CLOSED
- ✅ #60 (WITH clause variable passing) - CLOSED
- 🔄 #52 (NetworkRepository datasets) - IN PROGRESS

**Current State:**
- ✅ Dataset infrastructure complete
- ✅ CSV loader fully functional
- ✅ Cypher loader working
- ✅ GraphML loader implemented
- ✅ 5 SNAP datasets production-ready
- ✅ LDBC datasets integrated
- ⚠️ Need final validation of all 10+ datasets

**Implementation Steps:**
1. Complete #52 (NetworkRepository integration)
2. Run comprehensive validation tests on all datasets:
   - Test actual downloads from sources
   - Verify node/edge counts match metadata
   - Run example queries from dataset metadata
   - Test caching on second load
   - Benchmark load times
3. Update documentation:
   - Mark all datasets as ✅ in README.md
   - Update performance benchmarks
   - Create usage examples
4. Create v0.3.0 release checklist

**Success Criteria:**
- All 10+ datasets download and load successfully
- All example queries work correctly
- Caching verified for each dataset
- Load times meet targets (<5s for <10MB)
- Documentation complete and accurate
- Ready for v0.3.0 release

---

### Priority 2: TCK Coverage Expansion

#### Issue #103: Implement v0.3.0 TCK Coverage Features (39% Target)
**Status:** Partially complete (29% achieved, target 39%)
**Estimated Effort:** 30-50 hours remaining
**Current Coverage:** 29% (~1,113/3,837 scenarios)
**Target Coverage:** 39% (~1,500/3,837 scenarios)

**Completed Work:**
- ✅ Phase 1: Foundation (tree operators, OPTIONAL MATCH, left join primitive)
- ✅ Phase 2 (Partial): UNION/UNION ALL, list comprehensions, EXISTS/COUNT subqueries
- ✅ Phase 3 (Partial): Variable-length patterns

**Remaining Work:**

**1. TCK Test Validation & Bug Fixes (10-15 hours)**
- Run full TCK test suite against current implementation
- Identify failing scenarios for implemented features
- Debug and fix edge cases:
  - OPTIONAL MATCH with complex patterns
  - UNION with ORDER BY/LIMIT interaction
  - Quantifier expressions with nested NULLs
  - Variable-length paths with cycle detection edge cases
- Add missing function implementations discovered by TCK
- Ensure NULL handling is consistent across all operators

**2. Pattern Predicates (~100 scenarios, 10-15 hours)**
- Implement WHERE clause support within pattern expressions
- Grammar: `(n:Person WHERE n.age > 30)-[:KNOWS]->(m)`
- AST: Add predicate field to NodePattern and RelationshipPattern
- Planner: Push predicates into pattern matching
- Executor: Filter during traversal (not post-matching)
- Integration tests for various predicate patterns

**3. Additional Functions & Operators (5-8 hours)**
Identify missing functions from TCK failures:
- String functions: substring(), replace(), split(), trim(), etc.
- Math functions: abs(), ceil(), floor(), round(), sqrt(), etc.
- List functions: head(), tail(), last(), reverse(), range(), etc.
- Aggregation: collect(), distinct variations
- Implement as discovered by TCK test failures

**4. Edge Case Fixes (5-10 hours)**
- NULL propagation in complex expressions
- Empty result handling across operators
- Type coercion edge cases
- Property access on missing properties
- Aggregation with mixed types

**Recommended Approach:**
1. Run full TCK suite, capture results
2. Categorize failures by feature area
3. Prioritize by impact (# of scenarios affected)
4. Implement fixes in order of impact
5. Re-run TCK after each major fix
6. Document known limitations

**Success Criteria:**
- 35-39% TCK coverage achieved
- All implemented features work correctly on TCK scenarios
- No regressions in existing functionality
- 90%+ patch coverage maintained
- Documentation updated with limitations

---

### Priority 3: Future Enhancements

#### Issue #24: Path Expressions (Advanced)
**Status:** Partially complete, advanced features remain
**Estimated Effort:** 5-10 hours for remaining work
**Current State:**
- ✅ Variable-length patterns implemented (-[:REL*1..3]->)
- ⚠️ Path binding not yet implemented
- ⚠️ Path value type not implemented
- ⚠️ Path functions (nodes(), relationships()) not implemented
- ⚠️ shortestPath() not implemented

**Remaining Work:**
1. **Path Value Type (2-3 hours)**
   - Create CypherPath value type in types/values.py
   - Store list of nodes and edges
   - Implement equality and serialization

2. **Path Binding (1-2 hours)**
   - Support syntax: `p = (a)-[:REL*1..3]->(b)`
   - Bind variable `p` to Path value
   - Update executor to construct Path objects

3. **Path Functions (2-3 hours)**
   - Implement `length(path)` - return number of hops
   - Implement `nodes(path)` - return list of nodes
   - Implement `relationships(path)` - return list of edges

4. **Shortest Path (Optional, 3-5 hours)**
   - Implement `shortestPath()` function
   - Dijkstra's or BFS algorithm
   - Performance considerations for large graphs

**Defer to v0.4.0:** This is a nice-to-have enhancement. The core variable-length pattern functionality already works. Path binding and functions can be added later if needed by users or TCK tests.

---

## Recommended Implementation Order

### Phase 1: Complete Dataset Integration (1 week)
**Goal:** Finalize v0.3.0 dataset milestone, provide users with complete dataset catalog

1. **Implement Issue #52** (3-4.5 hours)
   - Add NetworkRepository dataset integration
   - 10-15 new datasets available

2. **Validate Issue #61** (2-3 hours)
   - Test all datasets with real downloads
   - Verify counts, queries, caching, performance
   - Update documentation

**Deliverable:** v0.3.0 dataset milestone complete, ready for release

---

### Phase 2: TCK Coverage Sprint (3-4 weeks)
**Goal:** Reach 39% TCK coverage with stable, well-tested features

1. **TCK Validation & Triage** (2-3 hours)
   - Run full TCK suite
   - Categorize failures by feature
   - Create prioritized fix list

2. **Bug Fixes for Implemented Features** (10-15 hours)
   - Fix OPTIONAL MATCH edge cases
   - Fix UNION with ORDER BY/LIMIT
   - Fix quantifier NULL handling
   - Fix variable-length path cycles

3. **Implement Pattern Predicates** (10-15 hours)
   - High-impact feature (~100 scenarios)
   - Grammar, AST, planner, executor changes
   - Comprehensive testing

4. **Add Missing Functions** (5-8 hours)
   - Implement functions discovered by TCK
   - String, math, list functions
   - Test coverage

5. **Final Edge Case Fixes** (5-10 hours)
   - NULL propagation fixes
   - Type coercion edge cases
   - Aggregation improvements

**Deliverable:** 35-39% TCK coverage, stable v0.3.0 release

---

### Phase 3: Advanced Path Features (Optional, v0.4.0)
**Goal:** Complete path expression support for advanced graph analytics

1. **Implement Issue #24 Remaining Work** (5-10 hours)
   - Path value type
   - Path binding syntax
   - Path manipulation functions
   - Shortest path algorithms (optional)

**Deliverable:** Full path expression support

---

## Risk Assessment

### Low Risk (Dataset Integration)
- **Issues:** #52, #61
- **Mitigation:** All dependencies resolved, straightforward implementation
- **Confidence:** Very high

### Medium Risk (TCK Coverage)
- **Issue:** #103
- **Challenges:**
  - Unknown edge cases in TCK tests
  - Potential grammar ambiguities
  - Complex NULL handling scenarios
- **Mitigation:**
  - Incremental approach (test after each fix)
  - Focus on high-impact features first
  - Document known limitations clearly
- **Confidence:** Medium-high

### Low Risk (Path Expressions)
- **Issue:** #24
- **Challenges:**
  - New value type (Path)
  - Performance considerations
- **Mitigation:**
  - Core functionality already implemented
  - Can defer advanced features
- **Confidence:** High

---

## Success Metrics

### v0.3.0 Release Criteria
- ✅ All 10+ datasets load successfully
- ✅ 35-39% TCK coverage achieved
- ✅ All existing tests pass (1,790+ tests)
- ✅ 90%+ test coverage maintained
- ✅ Documentation complete and accurate
- ✅ CHANGELOG updated with all features
- ✅ No critical bugs or blockers

### v0.4.0 Planning
- Advanced path features (#24 completion)
- Additional TCK coverage (45-50% target)
- Performance optimizations
- Additional dataset sources
- Ontology/schema support (future)

---

## Immediate Next Steps

**Recommend starting with Issue #52** (NetworkRepository integration):

1. Create GitHub issue branch: `feature/52-networkrepository-datasets`
2. Implement dataset registration and metadata
3. Add integration tests
4. Create documentation
5. Submit PR
6. Complete issue #61 validation after #52 merges

**Estimated Timeline:**
- Week 1: Complete #52 + #61 (dataset integration done)
- Weeks 2-5: TCK coverage sprint (#103)
- Week 6+: Optional path enhancements (#24)

**Total Estimated Effort:** 35-65 hours over 6-8 weeks

---

## Notes

- All work follows the standard workflow from CLAUDE.md (issue → branch → work → PR)
- Pre-push checks must pass for all changes
- Aim for 100% test coverage on new code
- Document all known limitations in CHANGELOG and docs
- Consider splitting large issues (#103) into smaller sub-issues for better tracking
