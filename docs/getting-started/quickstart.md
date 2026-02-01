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

## Next Steps

- [Cypher Guide](../guide/cypher-guide.md) - Complete query language reference
- [Graph Construction](../guide/graph-construction.md) - Advanced graph building
- [API Documentation](../reference/api.md) - Full API reference
