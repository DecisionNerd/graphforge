# Testing Strategy & Infrastructure

## Overview

This document defines the testing infrastructure, conventions, and quality standards for GraphForge. The testing approach prioritizes correctness, maintainability, and TCK compliance from the beginning.

---

## Testing Principles

1. **Spec-driven correctness** — openCypher semantics verified via TCK
2. **Fast feedback loops** — Unit tests run in milliseconds
3. **Hermetic tests** — No shared state between tests
4. **Clear test organization** — Easy to find and understand test coverage
5. **Deterministic behavior** — Tests pass or fail consistently
6. **Documentation through tests** — Tests serve as usage examples

---

## Test Categories

### 1. Unit Tests (`tests/unit/`)

Tests for individual components in isolation.

**Scope:**
- Data structures (NodeRef, EdgeRef, Value types)
- AST node construction and validation
- Expression evaluation
- Logical plan operators
- Property access and comparison semantics
- Storage primitives (without I/O)

**Characteristics:**
- No file I/O or external dependencies
- Mock/stub external interfaces
- Fast (< 1ms per test typically)
- High coverage target (>90%)

**Example structure:**
```
tests/unit/
├── __init__.py
├── test_data_model.py
├── test_ast.py
├── test_logical_plan.py
├── test_expression_eval.py
├── test_pattern_matching.py
└── storage/
    ├── __init__.py
    ├── test_adjacency_list.py
    └── test_property_store.py
```

---

### 2. Integration Tests (`tests/integration/`)

Tests for component interactions and end-to-end query execution.

**Scope:**
- Full query pipeline (parse → plan → execute)
- Storage durability across sessions
- Transaction isolation
- Python API surface
- Error handling and validation
- Query result correctness

**Characteristics:**
- May use temporary databases
- Test realistic query patterns
- Validate end-to-end behavior
- Target execution time < 100ms per test

**Example structure:**
```
tests/integration/
├── __init__.py
├── test_query_execution.py
├── test_storage_durability.py
├── test_api.py
├── test_transactions.py
└── test_error_handling.py
```

---

### 3. openCypher TCK Tests (`tests/tck/`)

Tests from the openCypher Technology Compatibility Kit.

**Scope:**
- Official openCypher semantics validation
- Feature coverage verification
- Regression prevention for supported features

**Characteristics:**
- Generated from TCK Gherkin scenarios
- Explicit pass/skip/xfail classification
- Versioned against TCK release (2024.2)
- Coverage matrix auto-generated

**Example structure:**
```
tests/tck/
├── __init__.py
├── conftest.py                 # TCK test harness
├── coverage_matrix.json        # Feature support declaration
├── features/
│   ├── match/
│   │   ├── test_match_nodes.py
│   │   └── test_match_relationships.py
│   ├── where/
│   │   └── test_filtering.py
│   └── return/
│       └── test_projection.py
└── utils/
    ├── __init__.py
    └── tck_runner.py          # TCK scenario executor
```

---

### 4. Property-Based Tests (`tests/property/`)

Generative tests using Hypothesis for edge cases.

**Scope:**
- Property value handling (null, lists, maps)
- Expression evaluation edge cases
- Query generation and fuzzing
- Storage consistency invariants

**Characteristics:**
- Uses Hypothesis for property-based testing
- Validates invariants across random inputs
- Catches edge cases missed by example-based tests

**Example structure:**
```
tests/property/
├── __init__.py
├── test_value_semantics.py
├── test_expression_invariants.py
└── strategies.py              # Hypothesis strategies
```

---

### 5. Performance Benchmarks (`tests/benchmarks/`)

Performance regression tracking (not run in standard test suite).

**Scope:**
- Query execution performance
- Storage I/O characteristics
- Scaling behavior

**Characteristics:**
- Uses pytest-benchmark
- Tracked over time, not pass/fail
- Run separately from unit/integration tests

---

## Pytest Configuration

### `pyproject.toml` Configuration

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# Output configuration
addopts = [
    "-ra",                      # Show summary of all test outcomes
    "--strict-markers",         # Error on unknown markers
    "--strict-config",          # Error on config issues
    "--showlocals",             # Show local variables on failure
    "--tb=short",               # Shorter traceback format
    "-v",                       # Verbose output
]

# Test discovery
norecursedirs = [
    ".git",
    ".venv",
    "dist",
    "build",
    "*.egg",
]

# Coverage
[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/tests/*",
    "*/__init__.py",
    "*/conftest.py",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]

[tool.coverage.html]
directory = "htmlcov"
```

### Test Markers

Define markers in `pyproject.toml`:

```toml
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (slower, may use I/O)",
    "tck: openCypher TCK compliance tests",
    "property: Property-based tests",
    "benchmark: Performance benchmarks",
    "slow: Tests that take >1s",
]
```

---

## Fixtures and Utilities

### Core Fixtures (`tests/conftest.py`)

```python
import pytest
from pathlib import Path
import tempfile
from graphforge import GraphForge

@pytest.fixture
def tmp_db_path():
    """Provides a temporary database path that's cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"

@pytest.fixture
def db(tmp_db_path):
    """Provides a fresh GraphForge instance with temporary storage."""
    return GraphForge(tmp_db_path)

@pytest.fixture
def memory_db():
    """Provides an in-memory GraphForge instance (no persistence)."""
    return GraphForge(":memory:")

@pytest.fixture
def sample_graph(db):
    """Provides a database with sample data for testing."""
    # TODO: Populate with standard test data
    return db
```

### TCK Fixtures (`tests/tck/conftest.py`)

```python
import pytest
from tests.tck.utils.tck_runner import TCKRunner

@pytest.fixture
def tck_runner(db):
    """Provides TCK scenario runner."""
    return TCKRunner(db)

@pytest.fixture
def tck_coverage():
    """Loads TCK coverage matrix."""
    import json
    from pathlib import Path

    matrix_path = Path(__file__).parent / "coverage_matrix.json"
    with open(matrix_path) as f:
        return json.load(f)
```

---

## Test Data Management

### Approach

1. **Inline data** — Simple cases use inline graph construction
2. **Fixture data** — Shared test graphs defined in fixtures
3. **External files** — Complex scenarios loaded from `tests/data/`

### Example Test Data Structure

```
tests/data/
├── graphs/
│   ├── simple_graph.json       # Small test graph
│   ├── social_network.json     # Medium social graph
│   └── knowledge_graph.json    # Complex multi-label graph
└── queries/
    ├── basic_match.cypher
    ├── filtering.cypher
    └── projection.cypher
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run specific category
pytest -m unit
pytest -m integration
pytest -m tck

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific file
pytest tests/unit/test_data_model.py

# Run specific test
pytest tests/unit/test_data_model.py::test_node_ref_equality

# Run in parallel (with pytest-xdist)
pytest -n auto

# Run TCK tests in parallel (recommended for large TCK suite)
make test-tck-parallel   # or: pytest tests/tck/ -n auto

# Run with verbose output
pytest -vv

# Stop on first failure
pytest -x

# Run only failed tests from last run
pytest --lf
```

### CI Commands

```bash
# Full test suite with coverage
pytest --cov=src --cov-report=xml --cov-report=term -m "not benchmark"

# Just unit tests (fast feedback)
pytest -m unit --cov=src

# TCK compliance check
pytest -m tck --strict-markers
```

---

## Quality Gates

### Coverage Requirements

- **Overall coverage:** ≥85%
- **Core modules:** ≥90%
  - Data model
  - Expression evaluation
  - Logical plan operators
- **Storage layer:** ≥80%
- **Parser/AST:** ≥75%

### Test Suite Performance

- **Unit tests:** < 5 seconds total
- **Integration tests:** < 30 seconds total
- **TCK tests:** < 60 seconds total
- **Full suite:** < 2 minutes (excluding benchmarks)

### Required Checks

All PRs must pass:
1. All unit tests
2. All integration tests
3. All non-skipped TCK tests
4. Coverage threshold (85%)
5. No new test warnings
6. Ruff linting (tests included)

---

## openCypher TCK Integration

### TCK Coverage Matrix

Maintain `tests/tck/coverage_matrix.json`:

```json
{
  "tck_version": "2024.2",
  "features": {
    "Match1_Nodes": {
      "status": "supported",
      "scenarios": {
        "Match single node": "pass",
        "Match node with label": "pass",
        "Match node with properties": "pass"
      }
    },
    "Match2_Relationships": {
      "status": "supported",
      "scenarios": {
        "Match outgoing relationship": "pass",
        "Match incoming relationship": "pass",
        "Match undirected relationship": "pass"
      }
    },
    "Match3_VariableLength": {
      "status": "unsupported",
      "reason": "Variable-length paths not in v1 scope"
    }
  }
}
```

### TCK Test Generation

Tests are generated from TCK Gherkin scenarios:

```python
# tests/tck/utils/tck_runner.py
class TCKRunner:
    """Executes openCypher TCK scenarios."""

    def run_scenario(self, scenario_name: str, steps: list):
        """Execute a TCK scenario with given/when/then steps."""
        pass

    def should_skip(self, feature: str) -> bool:
        """Check if feature is marked as unsupported."""
        pass
```

### TCK Test Example

```python
# tests/tck/features/match/test_match_nodes.py
import pytest

@pytest.mark.tck
def test_match_single_node(tck_runner):
    """TCK: Match1_Nodes - Match single node"""
    tck_runner.given_empty_graph()
    tck_runner.execute("CREATE (n)")
    result = tck_runner.execute("MATCH (n) RETURN n")
    assert len(result) == 1

@pytest.mark.tck
@pytest.mark.xfail(reason="Variable-length paths not supported in v1")
def test_variable_length_path(tck_runner):
    """TCK: Match3_VariableLength - Not supported in v1"""
    result = tck_runner.execute("MATCH (a)-[*1..3]->(b) RETURN a, b")
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install uv
          uv sync --all-extras

      - name: Run unit tests
        run: pytest -m unit --cov=src --cov-report=xml

      - name: Run integration tests
        run: pytest -m integration

      - name: Run TCK tests
        run: pytest -m tck

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## Development Workflow

### Test-Driven Development

1. **Write failing test** — Define expected behavior
2. **Implement minimal code** — Make test pass
3. **Refactor** — Improve design while keeping tests green
4. **Verify coverage** — Ensure new code is tested

### Before Committing

```bash
# Run full test suite
pytest

# Check coverage
pytest --cov=src --cov-report=term-missing

# Run linter
ruff check .

# Run formatter
ruff format .
```

### Pre-commit Hooks (Optional)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest-unit
        entry: pytest -m unit
        language: system
        pass_filenames: false
        always_run: true
```

---

## Dependencies

### Required Testing Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-xdist>=3.0",        # Parallel execution
    "pytest-timeout>=2.0",      # Test timeouts
    "pytest-mock>=3.0",         # Mocking utilities
    "hypothesis>=6.0",          # Property-based testing
    "pytest-benchmark>=4.0",    # Performance benchmarks
]
```

Install with:
```bash
uv sync --all-extras
# or
pip install -e ".[dev]"
```

---

## Test Maintenance

### Regular Tasks

1. **Update TCK coverage matrix** — When adding features
2. **Review slow tests** — Keep test suite fast
3. **Prune obsolete tests** — Remove tests for removed features
4. **Update test data** — Keep fixtures realistic
5. **Monitor flaky tests** — Investigate and fix non-deterministic tests

### Quarterly Review

- Coverage analysis — Identify gaps
- TCK version update — Sync with latest openCypher TCK
- Performance benchmarks — Track regressions
- Test organization — Refactor as needed

---

## References

- [pytest documentation](https://docs.pytest.org/)
- [openCypher TCK](https://github.com/opencypher/openCypher/tree/master/tck)
- [Hypothesis documentation](https://hypothesis.readthedocs.io/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)

---

## Known Issues & Investigated Solutions

### pytest-xdist + pytest-cov deadlock on macOS / Python 3.13

**Symptom:** `make pre-push` (or any `pytest -n auto --cov=...` invocation) hangs
indefinitely at the very end of the test run. Progress reaches ~100% then freezes.
CPU drops to 0%. Only `kill` escapes it.

**Root cause:** `pytest-cov` collects coverage data from xdist workers via IPC
(inter-process communication sockets). When workers finish and close their sockets,
a coverage data-collection thread in the main process is still blocked on `read()`.
The main thread waits for that lock → deadlock. Confirmed via `sample <PID>`:
```
main thread: lock_PyThread_acquire_lock → _PyMutex_LockTimed → _PySemaphore_Wait
worker thread: read() (44020 calls pending)
```
Reproduced consistently on macOS (Darwin 25.x) + Python 3.13.7 + pytest-cov 7.0.0 +
pytest-xdist 3.x. Not observed on Linux CI.

**What does NOT work:**

| Attempted fix | Result |
|---|---|
| `--cov-report=html` alone | Still deadlocks; HTML is slow but not the cause |
| `[tool.coverage.run] parallel = true` + `-n auto` | No deadlock but **2× slower** (3:54 vs 1:30) — per-process `.coverage.PID` file I/O overwhelms the speedup from parallelism |
| `concurrency = ["multiprocessing", "thread"]` + `parallel = true` | Same outcome as above; requires `coverage combine` step which adds no benefit |

**Solution (current `Makefile`):** Run coverage serially (no `-n auto`) and exclude
the two other causes of slowdown:

```makefile
coverage:
    uv run pytest tests/unit tests/integration -m "not snap" \
        --cov=src \
        --cov-branch \
        --cov-report=term-missing \
        --cov-report=xml
```

Key flags:
- **No `-n auto`** — eliminates the IPC deadlock entirely.
- **`-m "not snap"`** — skips SNAP network-dataset tests (they download files, run
  alphabetically last, and are already skipped in CI per their marker description).
- **No `--cov-report=html`** — HTML generation over ~13 k lines of source is slow;
  use `make coverage-report` on demand instead.

**Timing (Apple Silicon, Python 3.13, ~3 450 tests):**

| Approach | Wall time |
|---|---|
| `-n auto`, no coverage (baseline) | ~91 s |
| `-n auto` + `--cov` (original, pre-fix) | ∞ (deadlock) |
| `-n auto` + `--cov` + `parallel=true` | ~234 s |
| Serial `--cov`, `-m "not snap"`, no HTML (current) | ~150 s |

The serial run is only ~60 s slower than the parallel baseline because coverage
overhead is modest (~38 s) and `parallel=true` file-I/O costs more than it saves.

**If this is re-investigated in the future:** the deadlock is a known upstream issue
between pytest-cov and pytest-xdist on Python 3.13's stricter GIL/semaphore
behaviour. Check the [pytest-cov changelog](https://pytest-cov.readthedocs.io/) for
a fix before attempting another workaround.

---

## Success Metrics

The testing infrastructure is successful when:

1. **Fast feedback** — Developers get test results in < 10s for unit tests
2. **Clear failures** — Test failures clearly indicate what's broken
3. **High confidence** — Passing tests mean code works correctly
4. **TCK compliance** — Supported features pass relevant TCK tests
5. **Easy to extend** — Adding new tests is straightforward
6. **Low maintenance** — Tests rarely need updates unless requirements change
