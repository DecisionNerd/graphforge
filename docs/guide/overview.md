# User Guide Overview

This guide covers how to use GraphForge for graph analysis and construction.

## Topics

### [Cypher Query Language](cypher-guide.md)
Learn the openCypher query language - GraphForge's primary interface for working with graphs.

### [Graph Construction](graph-construction.md)
Build graphs programmatically using the Python API.

## Core Concepts

### Graphs
A graph consists of **nodes** (vertices) and **relationships** (edges) connecting them.

### Nodes
Nodes represent entities in your graph. They can have:
- **Labels** - Types or categories (e.g., `Person`, `Product`)
- **Properties** - Key-value pairs with data

### Relationships
Relationships connect nodes and can have:
- **Type** - The nature of the connection (e.g., `KNOWS`, `PURCHASED`)
- **Direction** - From one node to another
- **Properties** - Additional data about the relationship

### Patterns
Cypher uses ASCII-art patterns to describe graph structures:

```cypher
(a:Person)-[:KNOWS]->(b:Person)
```

This pattern matches two Person nodes connected by a KNOWS relationship.

## Query Flow

1. **MATCH** - Find patterns in the graph
2. **WHERE** - Filter results
3. **RETURN** - Specify what to return
4. **ORDER BY** - Sort results
5. **LIMIT** - Limit number of results

## Next Steps

- [Cypher Guide](cypher-guide.md) - Complete query language reference
- [Graph Construction](graph-construction.md) - Build graphs with Python
