# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.2] - 2026-02-17

### Added - List Operations (100% Complete)

#### List Operation Functions (#198, #199, #200)
- **filter()** - Filter lists by predicate
  - Example: `RETURN filter(x IN [1,2,3,4,5] WHERE x > 3) AS result` → [4, 5]
  - NULL list returns NULL, NULL items excluded
  - Variable binding with proper scoping
- **extract()** - Map transformations over lists
  - Example: `RETURN extract(x IN [1,2,3] | x * 2) AS result` → [2, 4, 6]
  - NULL list returns NULL, NULL items processed normally
  - Supports complex expressions and property access
- **reduce()** - Fold/reduce with accumulator
  - Example: `RETURN reduce(sum = 0, x IN [1,2,3,4] | sum + x) AS result` → 10
  - Dual variable binding (accumulator + loop variable)
  - Empty list returns initial value

### Implementation
- Added three AST nodes: FilterExpression, ExtractExpression, ReduceExpression
- Grammar rules for all three expressions in cypher.lark
- Parser transformers with Pydantic validation
- Evaluator handlers with proper NULL handling and variable scoping
- Treated as special syntax (like list comprehensions) due to variable binding

### Testing
- 42 comprehensive integration tests
- Full coverage of edge cases (empty lists, NULL handling, variable shadowing)
- Composition and nesting tests
- All tests passing with 100% coverage on new code

### Documentation
- Updated implementation status: 58/72 functions complete (81%, +4%)
- List Functions: 8/8 (100%)

## [0.3.1] - 2026-02-17

### Added - Predicate Functions (100% Complete)

#### Quantifier Functions (#205, #206, #207, #208)
- **all()** - Tests if all elements in a list satisfy a predicate
  - Example: `RETURN all(x IN [2, 4, 6] WHERE x % 2 = 0) AS result` → true
  - Implements three-valued NULL logic per OpenCypher spec
  - Returns false if any element fails, true if all pass, NULL if indeterminate
- **any()** - Tests if any element in a list satisfies a predicate
  - Example: `RETURN any(x IN [1, 2, 3] WHERE x > 2) AS result` → true
  - Returns true if any element passes, NULL if no true but some NULL
- **none()** - Tests if no elements in a list satisfy a predicate
  - Example: `RETURN none(x IN [1, 3, 5] WHERE x % 2 = 0) AS result` → true
  - Inverse of any() with proper NULL handling
- **single()** - Tests if exactly one element satisfies a predicate
  - Example: `RETURN single(x IN [1, 2, 3] WHERE x = 2) AS result` → true
  - Returns true only if exactly one match and no NULLs
  - Returns NULL if uniqueness cannot be determined (NULLs present)

#### Property and Collection Testing (#209, #210)
- **exists()** - Tests if a property exists or expression is not NULL
  - Example: `MATCH (p:Person) WHERE exists(p.age) RETURN p.name`
  - Evaluates before NULL propagation for accurate property checking
  - Returns false for missing properties (NULL values are not stored)
- **isEmpty()** - Tests if a list, string, or map is empty
  - Example: `RETURN isEmpty([]) AS result` → true
  - Works with lists, strings, and maps
  - Returns NULL for NULL input (three-valued logic)

### Testing
- 57 comprehensive integration tests (34 quantifier + 23 exists/isEmpty)
- Parametrized tests for better maintainability
- Full coverage of NULL handling edge cases
- All tests passing with 100% coverage on new code

### Documentation
- Updated implementation status: 55/72 functions complete (76%, +2%)
- Predicate Functions: 6/6 (100%)
- Detailed function signatures and examples in docs/reference/implementation-status/functions.md

### Performance
- No performance regressions
- Efficient NULL propagation handling
- Optimized list iteration for quantifiers

## [0.3.0] - 2026-02-09

### Added - Major Cypher Features

#### OPTIONAL MATCH (Left Outer Joins)
- Left outer join semantics with NULL preservation (#104)
- Example: `MATCH (p:Person) OPTIONAL MATCH (p)-[:KNOWS]->(f) RETURN p.name, f.name`
- 6 integration tests, comprehensive NULL handling

#### UNION and UNION ALL
- Combine query results with automatic deduplication (UNION) or preserve duplicates (UNION ALL) (#104)
- Example: `MATCH (p:Person) RETURN p.name UNION MATCH (c:Company) RETURN c.name`
- Tree-based operator structure for nested queries
- 9 integration tests

#### List Comprehensions
- Transform and filter lists declaratively (#104)
- Example: `RETURN [x IN [1,2,3,4,5] WHERE x > 3 | x * 2]`
- Supports WHERE filtering, map expressions, and nested comprehensions
- 12 integration tests

#### EXISTS and COUNT Subquery Expressions
- Correlated subqueries for existence checks and counting (#104)
- Example: `MATCH (p:Person) WHERE EXISTS { MATCH (p)-[:KNOWS]->() } RETURN p.name`
- Full operator pipeline execution for nested queries
- 13 integration tests

#### Variable-Length Path Patterns
- Recursive traversal with cycle detection (#104)
- Example: `MATCH (a)-[:KNOWS*1..3]->(b) RETURN a.name, b.name`
- Depth-first search with per-path cycle prevention
- Configurable min/max hop counts
- 2 integration tests

#### IS NULL / IS NOT NULL Operators
- Boolean NULL checking (distinct from = NULL ternary logic) (#104)
- Example: `MATCH (p:Person) WHERE p.age IS NULL RETURN p.name`
- Always returns boolean (never NULL)

### Added - Dataset Integration

#### NetworkRepository Datasets (#110, #113)
- 10 new graph datasets from NetworkRepository
- GraphML loader for complex graph formats
- Comprehensive metadata with node/edge counts, categories, licenses
- Examples: Polblogs, Polbooks, Karate club, Dolphin social network, C. elegans, Les Miserables
- All datasets validated with comprehensive test suite

#### Spatial and Temporal Types
- Point type for geographic coordinates
- Distance function for spatial queries
- Date, DateTime, Time, Duration types
- Full openCypher compatibility for type system

#### Dataset Validation Infrastructure (#112, #113)
- Comprehensive validation script (scripts/validate_datasets.py)
- Validates downloads, caching, node/edge counts, query functionality
- Performance benchmarking for all datasets
- 100% validation success rate (13/13 datasets tested)

### Fixed
- make coverage-diff command now works correctly (#111)
- Dataset validation script handles missing query results (#112)
- NetworkRepository dataset URLs and metadata corrections (#113)
- Exception handling improvements in validation infrastructure (#113)
- Resource cleanup with proper try/finally blocks

### Architecture Improvements
- Tree-based operator structure for nested queries
- Dual serialization: SQLite+MessagePack (data) + Pydantic+JSON (metadata)
- Enhanced expression evaluator with recursive execution
- Operator pipeline supports nested query planning

### Testing
- 767 integration tests passing (42+ new tests for v0.3.0)
- 91.96% code coverage maintained
- Comprehensive dataset validation suite
- Property-based testing with Hypothesis

### TCK Compatibility
- Progress from 16.6% to ~29% openCypher TCK coverage
- 312+ additional scenarios passing
- Foundation for continued TCK improvements toward 39% target

### Documentation
- Complete v0.3.0 feature documentation (CHANGELOG_v0.3.0.md)
- Dataset integration guides (docs/datasets/)
- Performance benchmarks and optimization tips
- Updated openCypher compatibility matrix

### Breaking Changes
None. All changes maintain backward compatibility with v0.2.0 and v0.2.1.

### Known Limitations
- Variable-length paths: no configurable max depth limit in unbounded queries
- UNION: no post-UNION ORDER BY (must be in each branch)
- Pattern predicates (WHERE inside patterns) not yet supported

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

[Unreleased]: https://github.com/DecisionNerd/graphforge/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/DecisionNerd/graphforge/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/DecisionNerd/graphforge/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/DecisionNerd/graphforge/compare/v0.1.4...v0.2.0
[0.1.4]: https://github.com/DecisionNerd/graphforge/compare/v0.1.3...v0.1.4
[0.1.2]: https://github.com/DecisionNerd/graphforge/compare/v0.1.1...v0.1.2
[0.1.0]: https://github.com/DecisionNerd/graphforge/releases/tag/v0.1.0
