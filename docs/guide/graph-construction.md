# Graph Construction

Learn how to build graphs programmatically using GraphForge's Python API.

## Creating Nodes

### Using Cypher

```python
from graphforge import GraphForge

graph = GraphForge()

# Create individual nodes
graph.execute("CREATE (n:Person {name: 'Alice', age: 30})")

# Create multiple nodes
graph.execute("""
    CREATE (alice:Person {name: 'Alice'})
    CREATE (bob:Person {name: 'Bob'})
    CREATE (charlie:Person {name: 'Charlie'})
""")
```

### Node Properties

Properties can be any JSON-serializable value:

```python
graph.execute("""
    CREATE (product:Product {
        name: 'Laptop',
        price: 999.99,
        in_stock: true,
        tags: ['electronics', 'computer']
    })
""")
```

## Creating Relationships

### Basic Relationships

```python
# Connect existing nodes
graph.execute("""
    MATCH (a:Person {name: 'Alice'})
    MATCH (b:Person {name: 'Bob'})
    CREATE (a)-[:KNOWS]->(b)
""")
```

### Relationships with Properties

```python
graph.execute("""
    MATCH (a:Person {name: 'Alice'})
    MATCH (b:Person {name: 'Bob'})
    CREATE (a)-[:KNOWS {since: 2020, strength: 'strong'}]->(b)
""")
```

### Create Nodes and Relationships Together

```python
graph.execute("""
    CREATE (a:Person {name: 'Alice'})
    CREATE (b:Person {name: 'Bob'})
    CREATE (a)-[:KNOWS]->(b)
""")
```

## Updating Nodes

### Using SET

```python
# Update properties
graph.execute("""
    MATCH (p:Person {name: 'Alice'})
    SET p.age = 31, p.city = 'New York'
""")

# Add new label
graph.execute("""
    MATCH (p:Person {name: 'Alice'})
    SET p:Employee
""")
```

## Deleting Elements

### Delete Nodes

```python
# Delete node (must have no relationships)
graph.execute("""
    MATCH (p:Person {name: 'Alice'})
    DELETE p
""")

# Delete node and all relationships
graph.execute("""
    MATCH (p:Person {name: 'Alice'})
    DETACH DELETE p
""")
```

### Delete Relationships

```python
graph.execute("""
    MATCH (a:Person)-[r:KNOWS]->(b:Person)
    WHERE a.name = 'Alice' AND b.name = 'Bob'
    DELETE r
""")
```

## Best Practices

### Use Parameters

Avoid string concatenation for security and performance:

```python
# Good - using parameters
graph.execute(
    "CREATE (p:Person {name: $name, age: $age})",
    parameters={'name': 'Alice', 'age': 30}
)

# Bad - string concatenation
name = 'Alice'
graph.execute(f"CREATE (p:Person {{name: '{name}'}})")  # Don't do this!
```

### Batch Operations

Create multiple elements efficiently:

```python
# Efficient batch creation
graph.execute("""
    UNWIND $people AS person
    CREATE (p:Person)
    SET p = person
""", parameters={
    'people': [
        {'name': 'Alice', 'age': 30},
        {'name': 'Bob', 'age': 25},
        {'name': 'Charlie', 'age': 35}
    ]
})
```

## Next Steps

- [Cypher Guide](cypher-guide.md) - Full query language reference
- [API Documentation](../reference/api.md) - Complete API reference
