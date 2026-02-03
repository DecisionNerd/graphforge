# Dataset Integration

GraphForge provides built-in support for loading popular graph datasets from various public repositories, making it easy to experiment, benchmark, and learn with real-world data.

## Overview

The dataset system allows you to:
- Load pre-configured graph datasets with a single command
- Explore standard benchmark datasets
- Test queries on realistic data
- Compare performance with other graph databases
- Learn Cypher with meaningful examples

## Supported Sources

GraphForge supports datasets from four major sources:

### 1. [LDBC (Linked Data Benchmark Council)](ldbc.md)
Standard benchmark datasets for graph databases, including the Social Network Benchmark (SNB) at various scale factors.

**Use cases:** Performance benchmarking, complex query testing, social network analysis

### 2. [NetworkRepository](networkrepository.md)
Large collection of network datasets including social networks, citations, collaborations, and infrastructure graphs.

**Use cases:** Network analysis, algorithm testing, research

### 3. [Neo4j Graph Examples](neo4j-examples.md)
Curated collection of example datasets from Neo4j, including movie graphs, Northwind database, Game of Thrones, and more.

**Use cases:** Learning Cypher, demonstrations, tutorials

### 4. [SNAP (Stanford Network Analysis Project)](snap.md)
Comprehensive collection of real-world network datasets from Stanford, covering social networks, web graphs, citation networks, and more.

**Use cases:** Research, graph algorithm development, academic projects

## Quick Start

### Loading a Dataset

```python
from graphforge import GraphForge
from graphforge.datasets import load_dataset

# Create a GraphForge instance
gf = GraphForge()

# Load a dataset by name
load_dataset(gf, "neo4j-movie-graph")

# Query the loaded data
results = gf.execute("MATCH (p:Person)-[:ACTED_IN]->(m:Movie) RETURN p.name, m.title LIMIT 10")
```

### Using the Convenience Method

```python
from graphforge import GraphForge

# Load dataset during initialization
gf = GraphForge.from_dataset("neo4j-movie-graph")

# Start querying immediately
results = gf.execute("MATCH (m:Movie) RETURN m.title ORDER BY m.title")
```

### Listing Available Datasets

```python
from graphforge.datasets import list_datasets

# Get all available datasets
datasets = list_datasets()

for ds in datasets:
    print(f"{ds.name}: {ds.description}")
    print(f"  Source: {ds.source}")
    print(f"  Nodes: {ds.nodes:,}, Edges: {ds.edges:,}")
    print(f"  Size: {ds.size_mb:.1f} MB")
    print()
```

### Filtering by Source

```python
from graphforge.datasets import list_datasets

# Get only Neo4j example datasets
neo4j_datasets = list_datasets(source="neo4j-examples")

# Get only small datasets (< 10 MB)
small_datasets = [ds for ds in list_datasets() if ds.size_mb < 10]
```

## CLI Usage

GraphForge provides command-line tools for working with datasets:

```bash
# List all available datasets
graphforge list-datasets

# Show detailed information about a dataset
graphforge dataset-info neo4j-movie-graph

# Load a dataset
graphforge load-dataset neo4j-movie-graph

# List datasets by source
graphforge list-datasets --source neo4j-examples

# Clear dataset cache
graphforge clear-cache
```

## Dataset Caching

Datasets are automatically cached locally after the first download to improve load times:

- **Cache location:** `~/.graphforge/datasets/`
- **Cache behavior:** Downloaded once, reused on subsequent loads
- **Cache management:** Use `graphforge clear-cache` to remove cached datasets

## Dataset Metadata

Each dataset includes comprehensive metadata:

```python
from graphforge.datasets import get_dataset_info

info = get_dataset_info("neo4j-movie-graph")

print(f"Name: {info.name}")
print(f"Description: {info.description}")
print(f"Source: {info.source}")
print(f"URL: {info.url}")
print(f"Nodes: {info.nodes:,}")
print(f"Edges: {info.edges:,}")
print(f"Labels: {', '.join(info.labels)}")
print(f"Relationship Types: {', '.join(info.relationship_types)}")
print(f"Size: {info.size_mb:.1f} MB")
print(f"License: {info.license}")
print(f"Category: {info.category}")
```

## Jupyter Notebook Integration

Datasets work seamlessly in Jupyter notebooks:

```python
# In a Jupyter notebook cell
from graphforge import GraphForge
from graphforge.datasets import load_dataset

gf = GraphForge()
load_dataset(gf, "neo4j-movie-graph")

# Explore the data
gf.execute("MATCH (n) RETURN labels(n) AS label, count(*) AS count")
```

<!-- See the [examples/notebooks/datasets.ipynb](../../examples/notebooks/datasets.ipynb) for interactive examples (coming soon). -->

## Contributing Datasets

To add a new dataset source or specific dataset:

1. Create a loader in `src/graphforge/datasets/`
2. Register the dataset in the registry
3. Add tests in `tests/integration/test_datasets.py`
4. Update documentation

See the [development guide](../development/workflow.md) for details.

## Troubleshooting

### Download Failures

If a dataset download fails:
- Check your internet connection
- Try clearing the cache: `graphforge clear-cache`
- Manually download from the source URL

### Memory Issues

Large datasets may require significant memory:
- Start with smaller scale factors (e.g., LDBC SF0.001)
- Use a machine with sufficient RAM
- Consider using SQLite persistence for large datasets

### Import Errors

If dataset import fails:
- Check the dataset format compatibility
- Verify the source URL is accessible
- Report issues on GitHub

## Related Documentation

- [LDBC Datasets](ldbc.md)
- [NetworkRepository Datasets](networkrepository.md)
- [Neo4j Examples](neo4j-examples.md)
- [SNAP Datasets](snap.md)
- [API Reference](../reference/api.md)

## License Information

Each dataset has its own license. Always check the dataset metadata for licensing information before using in production or research.

## Next Steps

- Explore [Neo4j Examples](neo4j-examples.md) for learning datasets
- Try [LDBC](ldbc.md) for benchmarking
- Use [SNAP](snap.md) for research datasets
- Check [NetworkRepository](networkrepository.md) for diverse networks
