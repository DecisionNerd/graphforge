# Contributing to GraphForge

Thank you for your interest in contributing to GraphForge! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.10 or newer
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/DecisionNerd/graphforge.git
   cd graphforge
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync --all-extras

   # Or using pip
   pip install -e ".[dev]"
   ```

3. **Verify installation**
   ```bash
   pytest -m unit
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run specific categories
pytest -m unit           # Fast unit tests
pytest -m integration    # Integration tests
pytest -m tck            # TCK compliance tests

# Run with coverage
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Run in parallel
pytest -n auto

# Watch mode (requires pytest-watch)
pytest-watch
```

### Code Quality

```bash
# Format code
ruff format .

# Check formatting
ruff format --check .

# Lint code
ruff check .

# Auto-fix linting issues
ruff check --fix .
```

### Before Committing

Run this checklist:

```bash
# 1. Format code
ruff format .

# 2. Fix linting issues
ruff check --fix .

# 3. Run tests
pytest

# 4. Check coverage
pytest --cov=src --cov-report=term-missing
```

## Project Structure

```
graphforge/
├── src/graphforge/          # Main package code
│   ├── __init__.py
│   └── main.py
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── tck/                # TCK compliance tests
│   └── property/           # Property-based tests
├── docs/                    # Documentation
│   ├── 0-requirements.md
│   └── testing-strategy.md
└── pyproject.toml          # Project configuration
```

## Testing Guidelines

### Writing Tests

1. **Unit tests** - Test components in isolation
   ```python
   import pytest

   @pytest.mark.unit
   def test_node_creation():
       node = Node(labels={"Person"})
       assert "Person" in node.labels
   ```

2. **Integration tests** - Test component interactions
   ```python
   import pytest

   @pytest.mark.integration
   def test_query_execution(db):
       result = db.execute("MATCH (n) RETURN n")
       assert result is not None
   ```

3. **Use fixtures** - Leverage existing fixtures for common setup
   ```python
   def test_with_temp_db(tmp_db_path):
       db = GraphForge(tmp_db_path)
       # Test logic
   ```

### Test Quality Standards

- **Fast**: Unit tests should run in < 1ms
- **Isolated**: No shared state between tests
- **Deterministic**: Same input = same output
- **Clear**: Test names describe what is being tested
- **Maintainable**: Easy to update when requirements change

See [docs/testing-strategy.md](docs/testing-strategy.md) for comprehensive testing documentation.

## Code Style

### General Guidelines

- Follow PEP 8 conventions
- Use type hints for function signatures
- Keep functions focused and small
- Write docstrings for public APIs
- Prefer explicit over implicit

### Example

```python
from typing import Optional


def create_node(
    labels: set[str],
    properties: Optional[dict[str, Any]] = None,
) -> Node:
    """Create a new node with labels and properties.

    Args:
        labels: Set of node labels
        properties: Optional property map

    Returns:
        A new Node instance

    Raises:
        ValueError: If labels is empty
    """
    if not labels:
        raise ValueError("Node must have at least one label")

    return Node(labels=labels, properties=properties or {})
```

## Pull Request Process

### PR Size Guidelines

**IMPORTANT: Keep PRs small and focused.**

CI/CD tools (CodeRabbit, GitHub Actions) work best with small, reviewable PRs. Large PRs are:
- Harder to review thoroughly
- More likely to introduce bugs
- Slower to get merged
- More difficult for CI/CD tools to process

**Good PR size:**
- ✅ Single feature or bug fix
- ✅ 50-300 lines of code changed
- ✅ 1-5 files modified
- ✅ Reviewable in < 30 minutes
- ✅ Clear, focused purpose

**Too large:**
- ❌ Multiple unrelated changes
- ❌ 1,000+ lines changed
- ❌ Refactoring + new feature + bug fixes combined
- ❌ Takes > 1 hour to review

**How to keep PRs small:**
1. Break large features into smaller PRs
2. Submit infrastructure changes separately from features
3. Refactor in one PR, add features in another
4. Use feature flags for incomplete features

**Example breakdown:**
```
❌ Bad: "Add WITH clause support" (2,000 lines, 20 files)

✅ Good: Break into multiple PRs
  PR 1: "Add WITH AST nodes and parser support" (200 lines)
  PR 2: "Add WITH planner operators" (150 lines)
  PR 3: "Add WITH executor logic" (180 lines)
  PR 4: "Add WITH integration tests" (120 lines)
```

### No Bandaid Fixes

**Fix problems properly, not with temporary workarounds.**

When you encounter an issue:

**❌ Bad approach (bandaids):**
- Add `# type: ignore` without understanding the issue
- Comment out failing tests
- Add workarounds instead of fixing root causes
- Use try/except to hide errors
- Skip CI checks temporarily

**✅ Good approach (proper fixes):**
- Investigate the root cause
- Fix the underlying problem
- Add tests to prevent regression
- Document why the fix is correct
- Update related code to be consistent

**Example:**

```python
# ❌ BANDAID - hides the real issue
try:
    result = process_data(input)
except Exception:
    result = None  # Hope this works...

# ✅ PROPER FIX - addresses root cause
def process_data(input: str | None) -> Result | None:
    """Process data with proper null handling."""
    if input is None:
        return None  # Explicitly handle null case

    try:
        return _parse_and_validate(input)
    except ValidationError as e:
        raise ValueError(f"Invalid input: {e}") from e
```

**When you're tempted to add a bandaid, ask:**
1. Why is this failing?
2. What's the root cause?
3. How can I fix it properly?
4. What tests will prevent this from happening again?

### Creating a PR

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write tests first (TDD)
   - Implement the feature
   - Update documentation
   - Add tests to verify behavior

3. **Ensure quality**
   ```bash
   ruff format .
   ruff check .
   pytest --cov=src
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

### PR Requirements

All PRs must:
- ✅ Pass all CI checks (no exceptions)
- ✅ Include tests for new functionality
- ✅ Maintain or improve code coverage (≥85%)
- ✅ Update relevant documentation
- ✅ Follow the code style guidelines
- ✅ Have a clear description of changes
- ✅ Be small and focused (< 300 lines preferred)
- ✅ Fix issues properly, not with bandaids
- ✅ No failing tests (fix or remove them)
- ✅ No `# type: ignore` without explanation
- ✅ No skipped CI checks

## Design Principles

When contributing, keep these principles in mind:

1. **Spec-driven correctness** - openCypher semantics over performance
2. **Deterministic behavior** - Stable results across runs
3. **Inspectable** - Observable query plans and execution
4. **Minimal dependencies** - Keep the dependency tree small
5. **Python-first** - Optimize for Python workflows

See [docs/0-requirements.md](docs/0-requirements.md) for complete requirements.

## openCypher TCK Compliance

When implementing openCypher features:

1. Check the TCK coverage matrix: `tests/tck/coverage_matrix.json`
2. Mark features as "supported", "planned", or "unsupported"
3. Add corresponding TCK tests
4. Ensure semantic correctness per the openCypher specification

## Documentation

### Code Documentation

- Public APIs: Comprehensive docstrings with examples
- Internal functions: Brief docstrings explaining purpose
- Complex logic: Inline comments explaining the "why"

### Project Documentation

Update relevant docs when adding features:
- README.md - User-facing features
- docs/0-requirements.md - Requirement changes
- docs/testing-strategy.md - Testing approach changes

## Getting Help

- **Questions**: Open a [GitHub Discussion](https://github.com/DecisionNerd/graphforge/discussions)
- **Bugs**: Open a [GitHub Issue](https://github.com/DecisionNerd/graphforge/issues)
- **Security**: Email security concerns privately (see SECURITY.md if available)

## Releases and Versioning

GraphForge follows [Semantic Versioning](https://semver.org/) and maintains a detailed [CHANGELOG.md](CHANGELOG.md).

### For Contributors

When submitting PRs, update the `[Unreleased]` section of CHANGELOG.md:

```markdown
## [Unreleased]

### Added
- New feature you implemented

### Fixed
- Bug you fixed
```

### For Maintainers

See [RELEASING.md](RELEASING.md) for the release process, or [docs/RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md) for comprehensive documentation.

Quick release:
```bash
python scripts/bump_version.py minor
# Edit CHANGELOG.md
git commit -am "chore(release): bump version to X.Y.Z"
git push origin main
git tag -a vX.Y.Z -m "Release version X.Y.Z"
git push origin vX.Y.Z
gh release create vX.Y.Z --title "GraphForge vX.Y.Z"
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Your contributions help make GraphForge better for everyone. We appreciate your time and effort!
