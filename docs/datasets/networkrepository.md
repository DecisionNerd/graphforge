# NetworkRepository Datasets

GraphForge provides seamless integration with [NetworkRepository](https://networkrepository.com/), a comprehensive collection of network datasets widely used in network science research.

## Overview

NetworkRepository offers 1,000+ network datasets covering diverse domains including social networks, biological networks, infrastructure graphs, collaboration networks, and more. GraphForge includes 10 carefully selected datasets that are:

- **Small size** (< 1 MB) - Fast downloads and quick loading
- **Diverse categories** - Social, biological, infrastructure, collaboration, communication
- **Well-documented** - Clear metadata and provenance
- **Classic datasets** - Widely cited in research literature

## Available Datasets

### Social Networks

#### Zachary's Karate Club (`netrepo-karate`)
Classic social network showing the fission of a university karate club into two groups.

- **Nodes:** 34
- **Edges:** 78
- **Category:** Social
- **Use case:** Community detection, network visualization

```python
from graphforge import GraphForge
from graphforge.datasets import load_dataset

gf = GraphForge()
load_dataset(gf, "netrepo-karate")

# Find nodes with highest degree (most connections)
results = gf.execute("""
    MATCH (n)-[r]-()
    RETURN n, count(r) AS degree
    ORDER BY degree DESC
    LIMIT 5
""")
```

#### Political Books Network (`netrepo-polbooks`)
Co-purchasing network of political books on Amazon, with books as nodes and co-purchases as edges.

- **Nodes:** 105
- **Edges:** 441
- **Category:** Social
- **Use case:** Community structure, political alignment clustering

#### College Football Network (`netrepo-football`)
Network of Division IA college football games in Fall 2000. Nodes are teams, edges are games played.

- **Nodes:** 115
- **Edges:** 613
- **Category:** Social
- **Use case:** Community detection (conferences), network structure

#### Les Miserables Network (`netrepo-lesmis`)
Character co-appearance network from Victor Hugo's *Les Misérables*. Characters appear as nodes, co-appearances in chapters as edges.

- **Nodes:** 77
- **Edges:** 254
- **Category:** Social
- **Use case:** Character importance analysis, story structure

### Biological Networks

#### Dolphin Social Network (`netrepo-dolphins`)
Social relationships between 62 dolphins in a community living off Doubtful Sound, New Zealand.

- **Nodes:** 62
- **Edges:** 159
- **Category:** Biological
- **Use case:** Animal social networks, community structure

```python
# Find most connected dolphins
gf = GraphForge()
load_dataset(gf, "netrepo-dolphins")

results = gf.execute("""
    MATCH (d)-[r]-()
    RETURN d, count(DISTINCT r) AS connections
    ORDER BY connections DESC
    LIMIT 10
""")
```

#### C. elegans Neural Network (`netrepo-celegans`)
Neural network of the nematode worm *Caenorhabditis elegans*. Neurons are nodes, synaptic connections are edges.

- **Nodes:** 297
- **Edges:** 2,148
- **Category:** Biological
- **Use case:** Neural network analysis, biological networks, connectomics

### Collaboration Networks

#### Network Science Coauthorship (`netrepo-netscience`)
Collaboration network of scientists working on network science. Nodes are authors, edges are coauthorships.

- **Nodes:** 1,589
- **Edges:** 2,742
- **Category:** Collaboration
- **Use case:** Scientific collaboration patterns, community detection

```python
# Find most prolific collaborators
gf = GraphForge()
load_dataset(gf, "netrepo-netscience")

results = gf.execute("""
    MATCH (author)-[:CONNECTED_TO]-(coauthor)
    RETURN author, count(DISTINCT coauthor) AS collaborators
    ORDER BY collaborators DESC
    LIMIT 10
""")
```

#### Jazz Musicians Collaboration (`netrepo-jazz`)
Collaboration network between jazz musicians. Nodes are musicians, edges are collaborations on albums.

- **Nodes:** 198
- **Edges:** 2,742
- **Category:** Collaboration
- **Use case:** Music collaboration networks, artist communities

### Infrastructure Networks

#### US Western Power Grid (`netrepo-power`)
Topology of the Western States Power Grid of the United States. Nodes are generators/transformers/substations, edges are transmission lines.

- **Nodes:** 4,941
- **Edges:** 6,594
- **Category:** Infrastructure
- **Use case:** Network resilience, infrastructure analysis, graph topology

### Communication Networks

#### European Email Network (`netrepo-email-eu`)
Email communication network from a large European research institution. Nodes are email addresses (anonymized), edges are email exchanges.

- **Nodes:** 1,005
- **Edges:** 25,571
- **Category:** Communication
- **Use case:** Communication patterns, information flow, organizational structure

## Basic Usage

### Loading a Dataset

```python
from graphforge import GraphForge
from graphforge.datasets import load_dataset

# Create a GraphForge instance
gf = GraphForge()

# Load a NetworkRepository dataset
load_dataset(gf, "netrepo-karate")

# Query the data
results = gf.execute("MATCH (n) RETURN count(n) AS node_count")
print(f"Loaded {results[0]['node_count'].value} nodes")
```

### Discovering Datasets

```python
from graphforge.datasets import list_datasets, get_dataset_info

# List all NetworkRepository datasets
all_datasets = list_datasets()
netrepo_datasets = [d for d in all_datasets if d.startswith("netrepo-")]
print(f"Found {len(netrepo_datasets)} NetworkRepository datasets")

# Get metadata for a specific dataset
info = get_dataset_info("netrepo-karate")
print(f"Dataset: {info.name}")
print(f"Description: {info.description}")
print(f"Nodes: {info.nodes}, Edges: {info.edges}")
print(f"Category: {info.category}")
print(f"Size: {info.size_mb} MB")
```

### Filtering by Category

```python
from graphforge.datasets import list_datasets, get_dataset_info

# Get all biological network datasets
all_datasets = list_datasets()
biological = [
    d for d in all_datasets
    if d.startswith("netrepo-") and get_dataset_info(d).category == "biological"
]

for dataset_name in biological:
    info = get_dataset_info(dataset_name)
    print(f"- {info.name}: {info.description}")
```

## Advanced Usage

### Analyzing Network Structure

```python
from graphforge import GraphForge
from graphforge.datasets import load_dataset

gf = GraphForge()
load_dataset(gf, "netrepo-karate")

# Calculate degree distribution
degree_dist = gf.execute("""
    MATCH (n)
    OPTIONAL MATCH (n)-[r]-()
    WITH n, count(r) AS degree
    RETURN degree, count(n) AS frequency
    ORDER BY degree
""")

for row in degree_dist:
    print(f"Degree {row['degree'].value}: {row['frequency'].value} nodes")
```

### Finding Communities

```python
# Find triangles in the network (3-node cliques)
triangles = gf.execute("""
    MATCH (a)-[:CONNECTED_TO]-(b)-[:CONNECTED_TO]-(c)-[:CONNECTED_TO]-(a)
    WHERE id(a) < id(b) AND id(b) < id(c)
    RETURN count(*) AS triangle_count
""")

print(f"Found {triangles[0]['triangle_count'].value} triangles")
```

### Comparing Datasets

```python
from graphforge import GraphForge
from graphforge.datasets import load_dataset

def get_network_stats(dataset_name):
    gf = GraphForge()
    load_dataset(gf, dataset_name)

    # Count nodes and edges
    nodes = gf.execute("MATCH (n) RETURN count(n) AS count")[0]["count"].value
    edges = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")[0]["count"].value

    # Calculate average degree
    avg_degree = (2 * edges) / nodes if nodes > 0 else 0

    return {
        "dataset": dataset_name,
        "nodes": nodes,
        "edges": edges,
        "avg_degree": round(avg_degree, 2),
    }

# Compare several datasets
datasets = ["netrepo-karate", "netrepo-dolphins", "netrepo-football"]
for ds in datasets:
    stats = get_network_stats(ds)
    print(f"{stats['dataset']}: {stats['nodes']} nodes, {stats['edges']} edges, "
          f"avg degree {stats['avg_degree']}")
```

## Data Format

NetworkRepository datasets are provided in **GraphML** format, an XML-based standard for graph data. GraphForge's GraphML loader automatically:

- Parses node and edge attributes with type preservation
- Converts GraphML types (int, double, boolean, string) to Cypher types
- Handles compressed `.graphml.gz` files
- Supports multi-label nodes
- Preserves all property metadata

Example GraphML structure:

```xml
<graphml>
  <key id="d0" for="node" attr.name="label" attr.type="string"/>
  <key id="d1" for="node" attr.name="name" attr.type="string"/>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d0">Node</data>
      <data key="d1">Alice</data>
    </node>
    <node id="n1">
      <data key="d0">Node</data>
      <data key="d1">Bob</data>
    </node>
    <edge source="n0" target="n1"/>
  </graph>
</graphml>
```

## Caching

Downloaded datasets are automatically cached in `~/.cache/graphforge/datasets/` to avoid redundant downloads:

```python
from graphforge.datasets import load_dataset

# First load downloads the file
load_dataset(gf, "netrepo-karate")  # Downloads ~10 KB

# Second load uses cached file (instant)
load_dataset(gf, "netrepo-karate")  # Loads from cache
```

## Performance

All NetworkRepository datasets in GraphForge are optimized for quick loading:

| Dataset | Nodes | Edges | Size | Load Time |
|---------|-------|-------|------|-----------|
| karate | 34 | 78 | ~10 KB | < 0.1s |
| dolphins | 62 | 159 | ~10 KB | < 0.1s |
| polbooks | 105 | 441 | ~20 KB | < 0.1s |
| football | 115 | 613 | ~20 KB | < 0.1s |
| lesmis | 77 | 254 | ~10 KB | < 0.1s |
| celegans | 297 | 2,148 | ~50 KB | < 0.2s |
| netscience | 1,589 | 2,742 | ~100 KB | < 0.3s |
| jazz | 198 | 2,742 | ~50 KB | < 0.2s |
| power | 4,941 | 6,594 | ~200 KB | < 0.5s |
| email-eu | 1,005 | 25,571 | ~500 KB | < 1.0s |

*Load times are approximate and measured on a modern laptop.*

## Persistence

Datasets can be loaded into persistent GraphForge instances:

```python
from graphforge import GraphForge
from graphforge.datasets import load_dataset

# Load into persistent database
gf = GraphForge("karate.db")
load_dataset(gf, "netrepo-karate")
gf.close()

# Later, reopen and query (data persisted)
gf2 = GraphForge("karate.db")
results = gf2.execute("MATCH (n) RETURN count(n) AS count")
print(f"Loaded {results[0]['count'].value} nodes from persistent storage")
gf2.close()
```

## Citation

If you use NetworkRepository datasets in your research, please cite:

> Ryan A. Rossi and Nesreen K. Ahmed. (2015). The Network Data Repository with Interactive Graph Analytics and Visualization. In Proceedings of the Twenty-Ninth AAAI Conference on Artificial Intelligence. http://networkrepository.com/

Individual datasets may have their own citations. Check the NetworkRepository website for dataset-specific attribution requirements.

## Related Documentation

- [SNAP Datasets](./snap.md)
- [LDBC Datasets](./ldbc.md)

## See Also

- [NetworkRepository Website](https://networkrepository.com/)
- [GraphML Format Specification](http://graphml.graphdrawing.org/)
- [Network Science Resources](https://networkrepository.com/resources.php)
