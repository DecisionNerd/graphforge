# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-02-03

### Added
- **Dataset loading infrastructure** (#68)
  - Automatic dataset download and caching system
  - Dataset registry with metadata (nodes, edges, size, category, license)
  - Built-in support for HTTP downloads with retry logic and timeout
  - Local cache directory (`~/.graphforge/datasets/`) with TTL-based expiration
  - Public API: `load_dataset()`, `list_datasets()`, `get_dataset_info()`, `clear_cache()`
  - `GraphForge.from_dataset()` convenience method for loading datasets
  - Example: `gf = GraphForge.from_dataset("snap-ego-facebook")`
- **CSV edge-list loader** (#69)
  - Load edge-list datasets in CSV/TSV/space-delimited formats
  - Auto-delimiter detection (tab, comma, space)
  - Gzip compression support for `.gz` files
  - Comment line handling (lines starting with `#`)
  - Weighted and unweighted edge support
  - Node deduplication via caching
  - Consecutive whitespace handling
  - Example: Load SNAP datasets with simple edge-list format
- **5 SNAP datasets available** (#69)
  - `snap-ego-facebook` - Facebook social circles (4K nodes, 88K edges, 0.5 MB)
  - `snap-email-enron` - Enron email network (37K nodes, 184K edges, 2.5 MB)
  - `snap-ca-astroph` - Astrophysics collaboration (19K nodes, 198K edges, 1.8 MB)
  - `snap-web-google` - Google web graph (876K nodes, 5.1M edges, 75 MB)
  - `snap-twitter-combined` - Twitter social circles (81K nodes, 1.8M edges, 25 MB)
  - Auto-registered on module import
  - Filterable by source, category, and size
- **MERGE ON CREATE SET syntax** (#65)
  - Conditional property setting when creating nodes: `MERGE (n:Person {id: 1}) ON CREATE SET n.created = timestamp()`
  - Parser support in Lark grammar
  - Executor tracks whether MERGE created or matched nodes
  - Comprehensive test coverage (parser, executor, integration)
- **MERGE ON MATCH SET syntax** (#66)
  - Conditional property setting when matching existing nodes: `MERGE (n:Person {id: 1}) ON MATCH SET n.updated = timestamp()`
  - Supports both ON CREATE and ON MATCH in same statement
  - OpenCypher-compliant semantics

### Fixed
- **WITH clause variable passing in aggregation** (#67)
  - Fixed variable scoping issues when using WITH after aggregation
  - Correctly passes aggregated values to subsequent clauses
  - Example: `MATCH (n) WITH count(n) AS cnt RETURN cnt` now works correctly

### Documentation
- **Complete dataset documentation** (#69)
  - New dataset overview guide with usage examples
  - SNAP dataset documentation with 5 available datasets
  - Updated quick start with dataset loading examples
  - Added dataset examples to main README
  - Performance tips for large datasets

### Known Limitations
- Only SNAP datasets available in this release (5 datasets)
- Neo4j example datasets, LDBC, and NetworkRepository planned for v0.3.0
- See [Issue #70](https://github.com/DecisionNerd/graphforge/issues/70) for roadmap to 100+ SNAP datasets

## [0.2.0] - 2026-02-03

### Added
- **CASE expressions for conditional logic** (#49)
  - Full openCypher CASE expression support with WHEN/THEN/ELSE/END syntax
  - Simple CASE (`CASE expr WHEN value`) and searched CASE (`CASE WHEN condition`)
  - NULL-safe semantics following openCypher specification
  - Example: `RETURN CASE WHEN n.age < 18 THEN 'minor' ELSE 'adult' END`
- **COLLECT aggregation function** (#46, #48)
  - Aggregate values into lists with `COLLECT()` function
  - DISTINCT support: `COLLECT(DISTINCT n.name)` removes duplicates
  - Handles complex types (CypherList, CypherMap) correctly in DISTINCT mode
  - NULL filtering: NULL values excluded from collected lists
  - Example: `MATCH (n) RETURN COLLECT(n.name)`
- **Arithmetic operators** (#44)
  - Binary operators: `+`, `-`, `*`, `/`, `%` (modulo)
  - Unary minus: `-n.value`
  - NULL propagation: operations with NULL return NULL
  - Type coercion for mixed integer/float operations
  - Division by zero returns NULL (openCypher-compliant)
  - Example: `RETURN n.price * 1.1 AS price_with_tax`
- **String matching operators** (#43)
  - `STARTS WITH`: Prefix matching
  - `ENDS WITH`: Suffix matching
  - `CONTAINS`: Substring matching
  - Case-sensitive matching following openCypher specification
  - NULL handling: returns NULL if either operand is NULL
  - Example: `MATCH (n) WHERE n.email ENDS WITH '@example.com'`
- **REMOVE clause** (#42)
  - Remove properties: `REMOVE n.property`
  - Remove labels: `REMOVE n:Label`
  - Multi-target support: `REMOVE n.prop1, n.prop2, n:Label`
  - Idempotent: removing non-existent properties/labels is a no-op
  - Example: `MATCH (n:Person) REMOVE n.age, n:Temporary`
- **UNWIND clause** (#40)
  - Unwind lists into rows: `UNWIND [1, 2, 3] AS x RETURN x`
  - Supports nested lists, empty lists, NULL values
  - Can be used with MATCH, WHERE, and other clauses
  - Example: `UNWIND $ids AS id MATCH (n) WHERE n.id = id RETURN n`
- **NOT logical operator** (#30)
  - Unary negation operator for boolean expressions
  - NULL-safe semantics: `NOT NULL` returns NULL
  - Example: `MATCH (n) WHERE NOT n.active RETURN n`
- **DETACH DELETE clause** (#33)
  - OpenCypher-compliant DELETE semantics
  - `DELETE` raises error if node has relationships
  - `DETACH DELETE` removes all connected edges first, then the node
  - Example: `MATCH (n:Person) DETACH DELETE n`
- **Comprehensive MATCH-CREATE combination tests** (#41)
  - 12 integration tests for MATCH followed by CREATE patterns
  - Validates correctness of mixed read-write operations
- **Complete documentation reorganization** (#56)
  - Restructured docs into logical sections (getting-started, user-guide, reference, development)
  - New datasets documentation section with examples
  - Improved navigation and discoverability
- **Code of Conduct** - Added Contributor Covenant Code of Conduct

### Fixed
- **ORDER BY after aggregation** (#39)
  - ORDER BY now correctly finds aliased variables after aggregation
  - Example: `MATCH (n) RETURN COUNT(n) AS cnt ORDER BY cnt` now works
- **RETURN DISTINCT after projection** (#38)
  - RETURN DISTINCT now works correctly after projection expressions
  - Fixes issue where DISTINCT was applied to wrong columns

### Changed
- **Test coverage improved** (#37)
  - Coverage increased from 88.69% to 93.76% (+4.94%)
  - Added 50+ new tests across parser, planner, and executor
- **GitHub Pages deployment modernization** (#32)
  - Migrated from legacy `mkdocs gh-deploy` to GitHub Actions native deployment
  - Uses `actions/upload-pages-artifact@v3` and `actions/deploy-pages@v4`
  - Simpler, faster, more secure deployment with `id-token` authentication
- **Issue workflow documentation** (#45)
  - Updated ISSUE_WORKFLOW.md to reflect current development process

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

[Unreleased]: https://github.com/DecisionNerd/graphforge/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/DecisionNerd/graphforge/compare/v0.1.4...v0.2.0
[0.1.4]: https://github.com/DecisionNerd/graphforge/compare/v0.1.3...v0.1.4
[0.1.2]: https://github.com/DecisionNerd/graphforge/compare/v0.1.1...v0.1.2
[0.1.0]: https://github.com/DecisionNerd/graphforge/releases/tag/v0.1.0
