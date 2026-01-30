# GitHub Actions Workflows

This directory contains CI/CD workflows for GraphForge.

## Workflows

### `test.yml` - Test Suite
**Triggers:** Push to main/develop, PRs to main

**Jobs:**
- **test**: Runs unit and integration tests across multiple OS and Python versions
  - Matrix: Ubuntu, macOS, Windows × Python 3.10, 3.11, 3.12, 3.13
  - Uploads coverage from Ubuntu/Python 3.12 to Codecov

- **lint**: Code quality checks
  - Format checking with ruff
  - Linting with ruff

- **coverage**: Coverage reporting
  - Generates HTML coverage report
  - Checks 85% threshold (soft fail during development)
  - Uploads coverage artifacts

### `publish.yml` - Package Publishing
**Triggers:** Manual workflow dispatch

Publishes package to PyPI (existing workflow).

## Local Equivalents

Run these locally before pushing:

```bash
# Run what CI runs
uv sync --all-extras
uv run pytest -m unit --cov=src
uv run pytest -m integration
uv run ruff format --check .
uv run ruff check .

# Or use shortcuts
pytest -m unit
ruff format .
ruff check .
```

## Status Badges

Add to README.md:

```markdown
![Tests](https://github.com/DecisionNerd/graphforge/workflows/Test%20Suite/badge.svg)
[![codecov](https://codecov.io/gh/DecisionNerd/graphforge/branch/main/graph/badge.svg)](https://codecov.io/gh/DecisionNerd/graphforge)
```
