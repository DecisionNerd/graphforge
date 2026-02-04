# Quick Start

Get started with GraphForge in minutes.

## Create Your First Graph

```python
from graphforge import GraphForge

# Initialize a graph
graph = GraphForge()
```

## Create Nodes

```python
# Create nodes with labels and properties
graph.execute("""
    CREATE (alice:Person {name: 'Alice', age: 30})
    CREATE (bob:Person {name: 'Bob', age: 25})
    CREATE (charlie:Person {name: 'Charlie', age: 35})
""")
```

## Create Relationships

```python
# Connect nodes with relationships
graph.execute("""
    MATCH (alice:Person {name: 'Alice'})
    MATCH (bob:Person {name: 'Bob'})
    CREATE (alice)-[:KNOWS {since: 2020}]->(bob)
""")
```

## Query the Graph

```python
# Find all people Alice knows
result = graph.execute("""
    MATCH (alice:Person {name: 'Alice'})-[:KNOWS]->(friend)
    RETURN friend.name, friend.age
""")

for row in result:
    print(f"{row['friend.name']} is {row['friend.age']} years old")
```

## Pattern Matching

```python
# Find paths between people
result = graph.execute("""
    MATCH (a:Person)-[:KNOWS*1..3]->(b:Person)
    WHERE a.name = 'Alice'
    RETURN DISTINCT b.name AS connection
""")
```

## Aggregation

```python
# Count relationships per person
result = graph.execute("""
    MATCH (p:Person)-[:KNOWS]->(friend)
    RETURN p.name, COUNT(friend) AS num_friends
    ORDER BY num_friends DESC
""")
```

## Load a Dataset

Start analyzing real-world networks instantly:

```python
from graphforge import GraphForge

# Load a dataset (automatically downloads and caches)
graph = GraphForge.from_dataset("snap-ego-facebook")

# Analyze the network
result = graph.execute("""
    MATCH (n)-[r]->()
    RETURN n.id AS user, count(r) AS connections
    ORDER BY connections DESC
    LIMIT 5
""")

for row in result:
    print(f"User {row['user']}: {row['connections']} connections")
```

### Available Datasets

```python
from graphforge.datasets import list_datasets

# Browse available datasets
datasets = list_datasets(source="snap")

for ds in datasets:
    print(f"{ds.name}: {ds.nodes:,} nodes, {ds.edges:,} edges")
```

See the [Dataset Documentation](../datasets/overview.md) for more datasets and examples.

## Next Steps

- [Tutorial](tutorial.md) - Complete step-by-step guide
- [Dataset Overview](../datasets/overview.md) - Work with real-world data
- [Cypher Guide](../guide/cypher-guide.md) - Complete query language reference
- [API Documentation](../reference/api.md) - Full API reference
