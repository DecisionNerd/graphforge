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
- Pass all CI checks
- Include tests for new functionality
- Maintain or improve code coverage (≥85%)
- Update relevant documentation
- Follow the code style guidelines
- Have a clear description of changes

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

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Your contributions help make GraphForge better for everyone. We appreciate your time and effort!
