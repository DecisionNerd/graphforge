# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.4] - 2026-02-02

### Added
- **Local coverage validation workflow** (#15, #16)
  - `make pre-push` now validates 85% combined line+branch coverage locally before pushing
  - `make coverage` - Run tests with coverage measurement and generate reports
  - `make check-coverage` - Validate 85% combined coverage threshold
  - `make coverage-strict` - Strict 90% threshold validation for new features
  - `make coverage-report` - Open HTML coverage report in browser
  - `make coverage-diff` - Show coverage for changed files only
  - Catches 90% of coverage issues before CI, eliminating codecov patch failures
  - Current coverage: 88.69% (92.41% line + 81.19% branch)
- **Codecov Test Analytics integration** (#17, #18)
  - JUnit XML generation for all test runs across 8,203 tests (481 unit/integration + 7,722 TCK)
  - Test performance monitoring with execution time trends
  - Flaky test detection for intermittent failures
  - Failure rate tracking and reliability pattern analysis
  - Cross-platform analytics tracking (12 OS/Python combinations)
  - `make test-analytics` - Generate JUnit XML locally for analysis
  - Analytics dashboard at https://app.codecov.io/gh/DecisionNerd/graphforge
- **List and map literal support in CREATE statements** (#15)
  - CREATE now accepts complex property types: lists, maps, and nested structures
  - Proper bidirectional CypherValue ↔ Python type conversion
  - 10 new integration tests covering complex property edge cases
- Codecov integration for automated coverage tracking
  - Coverage reports uploaded from GitHub Actions
  - Component-level coverage tracking (parser, planner, executor, storage, ast, types)
  - PR comments with coverage changes
  - Branch coverage analysis
  - Configuration file (`.codecov.yml`) with 85% project target, 80% patch target

### Changed
- **Development workflow modernization** (#16)
  - Updated CONTRIBUTING.md with comprehensive make-based workflow documentation
  - Single command for all pre-push validation: `make pre-push` (format-check, lint, type-check, coverage, check-coverage)
  - Clear documentation of coverage requirements (85% project, 80% patch)
  - Complete guidance on all available make targets with examples
- Test suite significantly expanded to 479 unit/integration tests + 7,722 TCK compliance tests

### Fixed
- Codecov test analytics deprecation warning (#18)
  - Migrated from deprecated `test-results-action@v1` to `codecov-action@v5`
  - Uses `report_type: test_results` parameter for future-proof compatibility

## [0.1.3] - 2026-02-01

### Changed
- **Column naming now uses variable names for simple variable references** (openCypher TCK compliance)
  - `RETURN n` now produces column name "n" (previously "col_0")
  - `RETURN n AS alias` produces column name "alias" (unchanged)
  - `RETURN n.property` produces column name "col_0" (unchanged - complex expression)
  - This aligns GraphForge with the openCypher specification and improves Neo4j compatibility
  - Note: This is a breaking change from v0.1.2 but necessary for WITH clause correctness
  - Rationale: WITH clause requires preserving variable names through query pipeline
- Test suite expanded with WITH clause coverage (17 comprehensive test cases)

### Added
- Comprehensive WITH clause integration tests covering:
  - Basic projection and variable renaming
  - WHERE filtering on intermediate results
  - Aggregation with GROUP BY semantics
  - ORDER BY, SKIP, LIMIT on intermediate results
  - Multi-part query chaining
  - Edge cases and null handling

### Fixed
- WITH clause bugs: column naming, aggregations, and DISTINCT behavior
- CodeRabbit configuration file to use only valid schema properties
- Removed unused pytest import from WITH clause tests

## [0.1.2] - 2026-02-01

### Added
- Professional versioning and release management system
  - Comprehensive CHANGELOG.md following Keep a Changelog format
  - Automated version bumping script (`scripts/bump_version.py`)
  - Release process documentation (RELEASING.md, docs/RELEASE_PROCESS.md, docs/RELEASE_STRATEGY.md)
  - Weekly automated release check with GitHub issue reminders
  - Release tracking workflow with auto-labeling
- MkDocs Material documentation site
  - Auto-generated API documentation from docstrings
  - Complete user guide (installation, quickstart, Cypher guide)
  - Auto-deploy to GitHub Pages on every push
- CI/CD enhancements
  - CHANGELOG validation workflow (ensures PRs update changelog)
  - Automated PR labeling based on changed files
  - Labels for component tracking (parser, planner, executor)
- `.editorconfig` for consistent editor settings across IDEs

### Changed
- Updated GitHub Actions to Node.js 24 (actions/checkout v6, actions/setup-python v6, astral-sh/setup-uv v7)
- Enhanced PR guidelines to enforce small PRs and proper fixes
- Updated README badges to professional numpy-style flat badges

### Fixed
- Integration test regression from WITH clause implementation
- Column naming now correctly uses `col_N` for unnamed return items
- SKIP/LIMIT queries no longer return empty results
- TCK test collection error resolved
- API documentation now references actual modules (api, ast, parser, planner, executor, storage, types)

## [0.1.1] - 2026-01-31

### Added
- WITH clause for query chaining and subqueries
- Production-grade CI/CD infrastructure
  - Pre-commit hooks (ruff, mypy, bandit)
  - CodeRabbit integration
  - Dependabot configuration
  - PR and issue templates
- Comprehensive documentation (30+ docs)
- TCK compliance at 16.6% (638/3,837 scenarios)

### Changed
- Updated project URLs to reflect new organization
- Enhanced README with additional badges

### Fixed
- Critical integration test failures (20 tests)
- TCK test collection error

## [0.1.0] - 2026-01-30

### Added
- Initial release of GraphForge
- Core data model (nodes, edges, properties, labels)
- Python builder API (`create_node`, `create_relationship`)
- SQLite persistence with ACID transactions
- openCypher query execution
  - MATCH, WHERE, CREATE, SET, DELETE, MERGE, RETURN
  - ORDER BY, LIMIT, SKIP
  - Aggregations (COUNT, SUM, AVG, MIN, MAX)
- Parser and AST for openCypher subset
- Query planner and executor
- 351 tests (215 unit + 136 integration)
- 81% code coverage
- Multi-OS, multi-Python CI/CD (3 OS × 4 Python versions)

[Unreleased]: https://github.com/DecisionNerd/graphforge/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/DecisionNerd/graphforge/compare/v0.1.3...v0.1.4
[0.1.2]: https://github.com/DecisionNerd/graphforge/compare/v0.1.1...v0.1.2
[0.1.0]: https://github.com/DecisionNerd/graphforge/releases/tag/v0.1.0
