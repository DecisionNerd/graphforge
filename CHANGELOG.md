# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/DecisionNerd/graphforge/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/DecisionNerd/graphforge/compare/v0.1.1...v0.1.2
[0.1.0]: https://github.com/DecisionNerd/graphforge/releases/tag/v0.1.0
