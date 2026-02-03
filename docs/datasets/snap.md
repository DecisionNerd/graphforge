# SNAP Datasets

> **Status:** Planned for v0.3.0 (Issue #54)

Support for SNAP (Stanford Network Analysis Project) datasets.

## Overview

SNAP provides an extensive collection of real-world network datasets from Stanford University, widely used in research and education.

## Dataset Source

- **URL:** https://snap.stanford.edu/data/
- **License:** Varies by dataset
- **Category:** Research, Academic

## Available Categories

- **Social Networks:** Facebook, Twitter, Google+, ego networks
- **Citation Networks:** arXiv, DBLP, patent citations
- **Collaboration Networks:** Amazon co-purchasing, co-authorship
- **Web Graphs:** Web page links, Wikipedia links
- **Road Networks:** US roads, European roads
- **Communication Networks:** Email, messaging

## Popular Datasets

| Dataset | Nodes | Edges | Description |
|---------|-------|-------|-------------|
| ego-Facebook | 4K | 88K | Facebook social circles |
| web-Google | 875K | 5.1M | Google web graph |
| email-Enron | 36K | 183K | Enron email network |
| ca-AstroPh | 18K | 198K | Astrophysics collaboration |

## Usage

```python
from graphforge import GraphForge
from graphforge.datasets import load_dataset

gf = GraphForge()
load_dataset(gf, "snap-ego-facebook")

# Analyze social network
results = gf.execute("""
    MATCH (n)-[r]->(m)
    RETURN count(DISTINCT n) AS users, count(r) AS connections
""")
```

## Example Queries

### Network Statistics

```cypher
MATCH (n)-[r]-(m)
RETURN
    count(DISTINCT n) AS nodes,
    count(r)/2 AS edges,
    count(r)/count(DISTINCT n) AS avgDegree
```

### Find Influential Nodes

```cypher
MATCH (n)-[r]->()
RETURN n, count(r) AS degree
ORDER BY degree DESC
LIMIT 10
```

## CLI Usage

```bash
# List SNAP datasets
graphforge list-datasets --source snap

# Load a dataset
graphforge load-dataset snap-ego-facebook
```

## References

- [SNAP Website](https://snap.stanford.edu/data/)
- [SNAP Documentation](https://snap.stanford.edu/data/index.html)
- [Issue #54](https://github.com/DecisionNerd/graphforge/issues/54)

## Related

- [Dataset Overview](overview.md)
<!-- - [Network Analysis Guide](../guide/network-analysis.md) (Coming soon) -->
