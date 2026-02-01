# Installation

## Requirements

- Python 3.10 or newer
- pip or [uv](https://github.com/astral-sh/uv)

## Install from PyPI

```bash
pip install graphforge
```

Or using uv (recommended):

```bash
uv pip install graphforge
```

## Install from Source

For development or to get the latest changes:

```bash
git clone https://github.com/DecisionNerd/graphforge.git
cd graphforge

# Using uv (recommended)
uv sync --all-extras

# Or using pip
pip install -e ".[dev]"
```

## Verify Installation

```bash
python -c "import graphforge; print(graphforge.__version__)"
```

## Next Steps

- [Quick Start](quickstart.md) - Your first graph queries
- [Cypher Guide](../guide/cypher-guide.md) - Learn the query language
