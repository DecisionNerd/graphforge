# GraphForge

**Composable graph tooling for analysis, construction, and refinement**

[![Python Version](https://img.shields.io/pypi/pyversions/graphforge.svg)](https://pypi.org/project/graphforge/)
[![PyPI Version](https://img.shields.io/pypi/v/graphforge.svg)](https://pypi.org/project/graphforge/)
[![License](https://img.shields.io/github/license/DecisionNerd/graphforge.svg)](https://github.com/DecisionNerd/graphforge/blob/main/LICENSE)
[![Test Status](https://github.com/DecisionNerd/graphforge/workflows/Test%20Suite/badge.svg)](https://github.com/DecisionNerd/graphforge/actions)

## What is GraphForge?

GraphForge is a Python library that provides composable graph tooling for analysis, construction, and refinement. It implements the openCypher query language, allowing you to work with graph data using a familiar, SQL-like syntax.

## Key Features

- **openCypher Query Language** - Industry-standard graph query language
- **Type-Safe** - Built with Pydantic for data validation
- **Pure Python** - No external database dependencies
- **TCK Compliant** - Implements openCypher specification
- **Composable** - Designed for Python workflows

## Quick Example

```python
from graphforge import GraphForge

# Create a graph
graph = GraphForge()

# Query with openCypher
result = graph.execute("""
    MATCH (p:Person {name: 'Alice'})-[:KNOWS]->(friend)
    RETURN friend.name
""")

for row in result:
    print(row['friend.name'])
```

## Getting Started

- [Installation](getting-started/installation.md) - Install GraphForge
- [Quick Start](getting-started/quickstart.md) - Your first graph queries
- [Cypher Guide](guide/cypher-guide.md) - Learn the query language

## Design Principles

1. **Spec-driven correctness** - openCypher semantics over performance
2. **Deterministic behavior** - Stable results across runs
3. **Inspectable** - Observable query plans and execution
4. **Minimal dependencies** - Keep the dependency tree small
5. **Python-first** - Optimize for Python workflows

## Project Status

GraphForge is under active development. Current openCypher TCK compliance: **16.6%** (638/3,837 scenarios).

See the [Changelog](reference/changelog.md) for recent updates.

## Contributing

We welcome contributions! See our [Contributing Guide](development/contributing.md) to get started.

## License

MIT License - see [LICENSE](https://github.com/DecisionNerd/graphforge/blob/main/LICENSE) for details.
