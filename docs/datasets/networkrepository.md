# NetworkRepository Datasets

> **Status:** Planned for v0.3.0 (Issue #52)

Support for NetworkRepository's large collection of network datasets.

## Overview

NetworkRepository provides a comprehensive collection of real-world network datasets for research and analysis.

## Dataset Source

- **URL:** https://networkrepository.com/networks.php
- **License:** Varies by dataset
- **Category:** Research, Network Analysis

## Available Categories

- **Social Networks:** Facebook, Twitter, collaboration networks
- **Citation Networks:** Academic paper citations
- **Infrastructure:** Power grids, road networks
- **Web Graphs:** Web page link structures
- **Biological Networks:** Protein interactions

## Usage

```python
from graphforge import GraphForge
from graphforge.datasets import load_dataset

gf = GraphForge()
load_dataset(gf, "netrepo-soc-karate")

# Analyze network structure
results = gf.execute("MATCH (n) RETURN count(n) AS nodeCount")
```

## References

- [NetworkRepository](https://networkrepository.com/)
- [Issue #52](https://github.com/DecisionNerd/graphforge/issues/52)

## Related

- [Dataset Overview](overview.md)
