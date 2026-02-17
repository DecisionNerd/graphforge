# Release Tracking - v0.3.x Series

**Created:** 2026-02-17
**Strategy:** Patch-level releases until 100% OpenCypher feature complete
**Timeline:** February 2026 (v0.3.0) → September 2026 (v0.3.7)

---

## Overview

This document tracks the 7 patch releases in the v0.3.x series that will take GraphForge from 78% to 100% OpenCypher feature completeness.

Each release has a dedicated tracking issue that:
- Lists all feature issues to be completed
- Defines acceptance criteria (implementation, testing, documentation)
- Provides a complete release checklist
- Serves as the release PR

---

## Release Schedule

| Release | Target | Goal | Features | Tracking Issue | Status |
|---------|--------|------|----------|----------------|--------|
| v0.3.0 | Feb 2026 | 78% | Baseline | #103 | ✅ Released |
| v0.3.1 | Mar 2026 | 82% | 6 predicates | [#218](https://github.com/DecisionNerd/graphforge/issues/218) | 🔄 Planned |
| v0.3.2 | Apr 2026 | 85% | 3 list ops | [#219](https://github.com/DecisionNerd/graphforge/issues/219) | 🔄 Planned |
| v0.3.3 | May 2026 | 88% | 3 patterns | [#220](https://github.com/DecisionNerd/graphforge/issues/220) | 🔄 Planned |
| v0.3.4 | Jun 2026 | 92% | 6 operators | [#221](https://github.com/DecisionNerd/graphforge/issues/221) | 🔄 Planned |
| v0.3.5 | Jul 2026 | 96% | 7 math/agg | [#222](https://github.com/DecisionNerd/graphforge/issues/222) | 🔄 Planned |
| v0.3.6 | Aug 2026 | 99% | 4 clauses | [#223](https://github.com/DecisionNerd/graphforge/issues/223) | 🔄 Planned |
| v0.3.7 | Sep 2026 | 100% | Polish | [#224](https://github.com/DecisionNerd/graphforge/issues/224) | 🔄 Planned |

---

## Release Details

### v0.3.1 - Predicate Functions (Issue #218)
**Target:** March 2026 | **Goal:** 78% → 82%

**Features (6):**
- #205 - all() predicate function
- #206 - any() predicate function
- #207 - none() predicate function
- #208 - single() predicate function
- #209 - exists() predicate function
- #210 - isEmpty() predicate function

**Impact:** ~36 TCK scenarios, commonly used in WHERE clauses

---

### v0.3.2 - List Operations (Issue #219)
**Target:** April 2026 | **Goal:** 82% → 85%

**Features (3):**
- #198 - extract() list function
- #199 - filter() list function
- #200 - reduce() list function

**Impact:** ~30 TCK scenarios, essential for data transformation

---

### v0.3.3 - Pattern & CALL Features (Issue #220)
**Target:** May 2026 | **Goal:** 85% → 88%

**Features (3):**
- #189 - Complete CALL { } subquery syntax (PARTIAL → COMPLETE)
- #216 - Complete pattern predicates (PARTIAL → COMPLETE)
- #217 - Pattern comprehension

**Impact:** ~40 TCK scenarios, advanced query capabilities

---

### v0.3.4 - Operators & String Functions (Issue #221)
**Target:** June 2026 | **Goal:** 88% → 92%

**Features (6):**
- #193 - length() string function
- #194 - toUpper/toLower camelCase variants
- #212 - XOR logical operator
- #213 - ^ (power) arithmetic operator
- #214 - List slicing [start..end]
- #215 - Negative list indexing

**Impact:** Operator completeness, string function parity

---

### v0.3.5 - Math & Aggregation Functions (Issue #222)
**Target:** July 2026 | **Goal:** 92% → 96%

**Features (7):**
- #195 - sqrt() function
- #196 - rand() function
- #197 - pow() function
- #201 - percentileDisc() aggregation
- #202 - percentileCont() aggregation
- #203 - stDev() aggregation
- #204 - stDevP() aggregation

**Impact:** Mathematical operations complete, statistical analysis support

---

### v0.3.6 - Remaining Clauses (Issue #223)
**Target:** August 2026 | **Goal:** 96% → 99%

**Features (4):**
- #190 - CALL procedures (with procedure registry)
- #191 - FOREACH clause
- #192 - LOAD CSV clause
- #211 - elementId() scalar function

**Impact:** Procedural capabilities, data import, GQL compliance

---

### v0.3.7 - Final Polish (Issue #224)
**Target:** September 2026 | **Goal:** 99% → 100%

**Features:** None (polish only)

**Focus:**
- Edge case fixes from TCK scenarios
- Documentation completeness verification
- Performance optimization
- API refinements and consistency
- Release notes and migration guides

**Impact:** All 134 OpenCypher features complete

---

## Release Process

Each release follows this standard process:

### 1. Feature Development
- All feature issues for the release are implemented
- Each feature has complete tests (unit + integration)
- Each feature has documentation updates
- Code review completed for all PRs

### 2. Pre-Release
- Create release branch: `release/v0.3.x`
- Version bump in relevant files
- Update CHANGELOG.md with release notes
- Run full test suite
- Tag release candidate: `v0.3.x-rc1`

### 3. Testing
- Smoke tests on release candidate
- Integration tests with real datasets
- Performance benchmarks
- TCK pass rate verification

### 4. Release
- Merge release branch to main
- Tag release: `v0.3.x`
- Build release artifacts
- Publish to PyPI
- Create GitHub release with notes

### 5. Post-Release
- Verify PyPI installation
- Update documentation
- Close release tracking issue
- Archive release branch

---

## Acceptance Criteria (All Releases)

### Feature Implementation
- All feature issues resolved and merged
- No blocking bugs in new features
- Code review completed
- All PRs merged to main

### Testing Requirements
- All unit tests passing (100%)
- All integration tests passing (100%)
- TCK pass rate improved
- Coverage: Total ≥85%, Patch ≥90%
- No test flakiness

### Documentation Requirements
- Implementation status docs updated
- Feature documentation with examples
- Compatibility matrix updated
- CHANGELOG.md updated
- API documentation complete

### Code Quality
- `make pre-push` passing
- No new warnings
- All TODO/FIXME addressed
- Code review feedback resolved

---

## Feature Mapping

Complete mapping of all 29 features to releases:

| Category | Features | Releases |
|----------|----------|----------|
| **Predicate Functions** | 6 | v0.3.1 (#205-#210) |
| **List Operations** | 3 | v0.3.2 (#198-#200) |
| **Patterns** | 2 | v0.3.3 (#216-#217) |
| **CALL Features** | 1 | v0.3.3 (#189) |
| **String Functions** | 2 | v0.3.4 (#193-#194) |
| **Operators** | 4 | v0.3.4 (#212-#215) |
| **Math Functions** | 3 | v0.3.5 (#195-#197) |
| **Aggregations** | 4 | v0.3.5 (#201-#204) |
| **Clauses** | 3 | v0.3.6 (#190-#192) |
| **Scalar Functions** | 1 | v0.3.6 (#211) |
| **TOTAL** | **29** | **7 releases** |

---

## Progress Tracking

### Feature Completion by Release

| Release | Start | Added | Total | Percentage |
|---------|-------|-------|-------|------------|
| v0.3.0 | - | - | 105/134 | 78% |
| v0.3.1 | 105/134 | +6 | 111/134 | 82% |
| v0.3.2 | 111/134 | +3 | 114/134 | 85% |
| v0.3.3 | 114/134 | +3 | 117/134 | 88% |
| v0.3.4 | 117/134 | +6 | 123/134 | 92% |
| v0.3.5 | 123/134 | +7 | 130/134 | 96% |
| v0.3.6 | 130/134 | +4 | 134/134 | 99% |
| v0.3.7 | 134/134 | +0 | 134/134 | **100%** |

### Category Completion

| Category | v0.3.0 | v0.3.7 | Change |
|----------|--------|--------|--------|
| Clauses | 16/20 (80%) | 20/20 (100%) | +4 |
| Functions | 53/72 (74%) | 72/72 (100%) | +19 |
| Operators | 30/34 (88%) | 34/34 (100%) | +4 |
| Patterns | 6/8 (75%) | 8/8 (100%) | +2 |
| **TOTAL** | **105/134 (78%)** | **134/134 (100%)** | **+29** |

---

## Related Documentation

- **Roadmap:** [opencypher-compatibility-matrix.md](opencypher-compatibility-matrix.md)
- **Feature Issues:** [INCOMPLETE_FEATURES_ISSUES.md](INCOMPLETE_FEATURES_ISSUES.md)
- **Compatibility Matrix:** [opencypher-compatibility-matrix.md](opencypher-compatibility-matrix.md)
- **TCK Inventory:** [tck-inventory.md](tck-inventory.md)
- **Parent Issue:** #103 (TCK Coverage v0.3.0)

---

## GitHub Milestones

Create corresponding GitHub milestones for each release:
- Milestone: v0.3.1 - Predicate Functions
- Milestone: v0.3.2 - List Operations
- Milestone: v0.3.3 - Pattern & CALL Features
- Milestone: v0.3.4 - Operators & Strings
- Milestone: v0.3.5 - Math & Aggregations
- Milestone: v0.3.6 - Remaining Clauses
- Milestone: v0.3.7 - Final Polish

Assign feature issues to their corresponding milestone.

---

**Created:** 2026-02-17
**Last Updated:** 2026-02-17
**Maintainer:** [@DecisionNerd](https://github.com/DecisionNerd)
