# GraphForge API Reference

Complete Python API documentation for GraphForge v0.1.1.

## Table of Contents

- [GraphForge Class](#graphforge-class)
- [Node and Relationship Types](#node-and-relationship-types)
- [CypherValue Types](#cyphervalue-types)
- [Exceptions](#exceptions)
- [Type Conversion](#type-conversion)

---

## GraphForge Class

### Constructor

#### `GraphForge(path=None)`

Create a new GraphForge instance.

**Parameters:**
- `path` (str | Path | None): Optional path to SQLite database file
  - If `None`: Creates in-memory graph (data lost on exit)
  - If path provided: Creates or opens persistent graph

**Returns:** GraphForge instance

**Examples:**

```python
# In-memory graph
db = GraphForge()

# Persistent graph
db = GraphForge("my-graph.db")
db = GraphForge(Path("data/graph.db"))
```

---

### Node Operations

#### `create_node(labels=None, **properties)`

Create a new node with labels and properties.

**Parameters:**
- `labels` (list[str] | None): List of label strings (e.g., `['Person', 'Employee']`)
- `**properties`: Arbitrary keyword arguments for node properties

**Returns:** `NodeRef` - Reference to the created node

**Property Types Supported:**
- `str`, `int`, `float`, `bool`, `None`
- `list` (homogeneous)
- `dict` (nested properties)

**Examples:**

```python
# Simple node
node = db.create_node(['Person'], name='Alice', age=30)

# Multiple labels
node = db.create_node(['Person', 'Employee'],
                      name='Bob',
                      employee_id='E001',
                      salary=75000)

# No labels
node = db.create_node(name='Anonymous')

# Complex properties
node = db.create_node(['User'],
                      name='Charlie',
                      tags=['python', 'graphs'],
                      metadata={'created': '2024-01-01'})
```

---

### Relationship Operations

#### `create_relationship(src, dst, rel_type, **properties)`

Create a directed relationship between two nodes.

**Parameters:**
- `src` (NodeRef): Source node
- `dst` (NodeRef): Destination node
- `rel_type` (str): Relationship type (e.g., `'KNOWS'`, `'WORKS_AT'`)
- `**properties`: Arbitrary keyword arguments for relationship properties

**Returns:** `EdgeRef` - Reference to the created relationship

**Examples:**

```python
alice = db.create_node(['Person'], name='Alice')
bob = db.create_node(['Person'], name='Bob')

# Simple relationship
edge = db.create_relationship(alice, bob, 'KNOWS')

# With properties
edge = db.create_relationship(alice, bob, 'KNOWS',
                               since=2020,
                               strength='strong',
                               frequency='daily')
```

---

### Query Operations

#### `execute(query)`

Execute a Cypher query and return results.

**Parameters:**
- `query` (str): openCypher query string

**Returns:** `list[dict]` - List of result rows as dictionaries

**Result Format:**
- Each row is a `dict` mapping column names to `CypherValue` objects
- Access Python values using `.value` attribute
- Empty queries (no RETURN clause) return empty list `[]`

**Examples:**

```python
# Simple query
results = db.execute("MATCH (n) RETURN n")

# With WHERE clause
results = db.execute("""
    MATCH (p:Person)
    WHERE p.age > 25
    RETURN p.name AS name, p.age AS age
""")

# Access results
for row in results:
    name = row['name'].value  # Extract Python string
    age = row['age'].value    # Extract Python int
    print(f"{name}: {age} years old")

# Mutations (no RETURN)
db.execute("CREATE (p:Person {name: 'Alice'})")  # Returns []
db.execute("MATCH (p:Person) DELETE p")         # Returns []
```

**Supported Cypher Features:**
- `MATCH` - Pattern matching
- `WHERE` - Filtering
- `RETURN` - Projection
- `CREATE` - Node/relationship creation
- `SET` - Property updates
- `DELETE` - Node/relationship deletion
- `MERGE` - Idempotent creation
- `ORDER BY` - Sorting
- `LIMIT`, `SKIP` - Pagination
- Aggregations: `count()`, `sum()`, `avg()`, `min()`, `max()`

**Not Yet Supported:**
- `WITH` clause (planned)
- `OPTIONAL MATCH` (planned)
- Variable-length paths `[*1..3]` (planned)
- `UNWIND`, `UNION`, `CASE`

---

### Transaction Operations

#### `begin()`

Begin an explicit transaction.

**Returns:** None

**Raises:**
- `RuntimeError`: If already in a transaction

**Examples:**

```python
db.begin()
db.execute("CREATE (p:Person {name: 'Alice'})")
db.commit()  # Or db.rollback()
```

---

#### `commit()`

Commit the current transaction and persist changes to disk (if using SQLite backend).

**Returns:** None

**Raises:**
- `RuntimeError`: If not in a transaction

**Examples:**

```python
db.begin()
db.execute("CREATE (p:Person {name: 'Alice'})")
db.commit()  # Changes are now permanent
```

---

#### `rollback()`

Roll back the current transaction, discarding all changes since `begin()`.

**Returns:** None

**Raises:**
- `RuntimeError`: If not in a transaction

**Examples:**

```python
db.begin()
db.execute("CREATE (p:Person {name: 'Alice'})")
db.rollback()  # Alice is not created

# Verify
results = db.execute("MATCH (p:Person {name: 'Alice'}) RETURN p")
len(results)  # 0
```

---

### Storage Operations

#### `close()`

Save graph to disk and close database connection.

**Returns:** None

**Behavior:**
- If in a transaction, automatically commits before closing
- If using in-memory graph, this is a no-op
- Safe to call multiple times
- After closing, the GraphForge instance should not be used

**Examples:**

```python
db = GraphForge("my-graph.db")
db.execute("CREATE (p:Person {name: 'Alice'})")
db.close()  # Saves to disk

# Later...
db = GraphForge("my-graph.db")  # Data is still there
```

---

## Node and Relationship Types

### NodeRef

Immutable reference to a node in the graph.

**Attributes:**
- `id` (int | str): Unique node identifier
- `labels` (frozenset[str]): Set of label strings
- `properties` (dict[str, CypherValue]): Property dictionary

**Examples:**

```python
node = db.create_node(['Person'], name='Alice', age=30)

print(node.id)                    # 1
print(node.labels)                # frozenset({'Person'})
print(node.properties['name'])    # CypherString('Alice')
print(node.properties['name'].value)  # 'Alice'
```

**Note:** NodeRef objects are immutable. Use `SET` clause or direct mutation to update properties.

---

### EdgeRef

Immutable reference to a relationship in the graph.

**Attributes:**
- `id` (int | str): Unique relationship identifier
- `type` (str): Relationship type (e.g., `'KNOWS'`)
- `src` (NodeRef): Source node reference
- `dst` (NodeRef): Destination node reference
- `properties` (dict[str, CypherValue]): Property dictionary

**Examples:**

```python
alice = db.create_node(['Person'], name='Alice')
bob = db.create_node(['Person'], name='Bob')
edge = db.create_relationship(alice, bob, 'KNOWS', since=2020)

print(edge.id)                    # 1
print(edge.type)                  # 'KNOWS'
print(edge.src.id)                # alice.id
print(edge.dst.id)                # bob.id
print(edge.properties['since'].value)  # 2020
```

---

## CypherValue Types

All property values and query results are wrapped in `CypherValue` objects that implement openCypher semantics (especially NULL propagation).

### CypherNull

Represents NULL values.

**Usage:**

```python
from graphforge.types.values import CypherNull

null = CypherNull()
print(null.value)  # None
```

**NULL Semantics:**
- Any operation with NULL produces NULL
- `NULL = NULL` → `NULL` (not `true`)
- `NULL AND true` → `NULL`

---

### CypherBool

Boolean values.

**Constructor:** `CypherBool(value: bool)`

**Examples:**

```python
from graphforge.types.values import CypherBool

true_val = CypherBool(True)
false_val = CypherBool(False)

print(true_val.value)  # True
```

---

### CypherInt

Integer values.

**Constructor:** `CypherInt(value: int)`

**Examples:**

```python
from graphforge.types.values import CypherInt

age = CypherInt(30)
print(age.value)  # 30
```

---

### CypherFloat

Floating-point values.

**Constructor:** `CypherFloat(value: float)`

**Examples:**

```python
from graphforge.types.values import CypherFloat

score = CypherFloat(98.5)
print(score.value)  # 98.5
```

---

### CypherString

String values.

**Constructor:** `CypherString(value: str)`

**Examples:**

```python
from graphforge.types.values import CypherString

name = CypherString("Alice")
print(name.value)  # 'Alice'
```

---

### CypherList

List values.

**Constructor:** `CypherList(items: list[CypherValue])`

**Examples:**

```python
from graphforge.types.values import CypherList, CypherInt

numbers = CypherList([CypherInt(1), CypherInt(2), CypherInt(3)])
print(numbers.value)  # [CypherInt(1), CypherInt(2), CypherInt(3)]
```

**Note:** GraphForge automatically converts Python lists to CypherList when creating nodes.

---

### CypherMap

Map (dictionary) values.

**Constructor:** `CypherMap(items: dict[str, CypherValue])`

**Examples:**

```python
from graphforge.types.values import CypherMap, CypherString, CypherInt

metadata = CypherMap({
    'created': CypherString('2024-01-01'),
    'version': CypherInt(1)
})
```

---

## Exceptions

### GraphForgeError

Base exception class for all GraphForge errors.

**Example:**

```python
try:
    db.execute("INVALID CYPHER")
except Exception as e:
    print(f"Error: {e}")
```

**Note:** Currently, GraphForge raises generic exceptions. Custom exception hierarchy is planned.

---

## Type Conversion

### Python → CypherValue

GraphForge automatically converts Python types to CypherValue types:

| Python Type | CypherValue Type |
|-------------|------------------|
| `None` | `CypherNull` |
| `bool` | `CypherBool` |
| `int` | `CypherInt` |
| `float` | `CypherFloat` |
| `str` | `CypherString` |
| `list` | `CypherList` (recursive) |
| `dict` | `CypherMap` (recursive) |

**Examples:**

```python
# Automatic conversion
node = db.create_node(['Person'],
                      name='Alice',           # → CypherString
                      age=30,                 # → CypherInt
                      score=98.5,             # → CypherFloat
                      active=True,            # → CypherBool
                      tags=['python', 'ml'],  # → CypherList[CypherString]
                      metadata={'key': 'val'} # → CypherMap
                     )

# Access properties
print(node.properties['name'].value)  # 'Alice' (Python str)
print(node.properties['age'].value)   # 30 (Python int)
```

### CypherValue → Python

Access the `.value` attribute to extract Python types:

```python
results = db.execute("MATCH (p:Person) RETURN p.name AS name, p.age AS age")

for row in results:
    name = row['name'].value  # Python str
    age = row['age'].value    # Python int
    print(f"{name}: {age}")
```

---

## Complete Example

```python
from graphforge import GraphForge

# Create graph
db = GraphForge("example.db")

try:
    # Begin transaction
    db.begin()

    # Create nodes
    alice = db.create_node(['Person'], name='Alice', age=30)
    bob = db.create_node(['Person'], name='Bob', age=25)

    # Create relationship
    knows = db.create_relationship(alice, bob, 'KNOWS', since=2020)

    # Query
    results = db.execute("""
        MATCH (a:Person)-[r:KNOWS]->(b:Person)
        RETURN a.name AS person, b.name AS knows, r.since AS since
    """)

    for row in results:
        print(f"{row['person'].value} knows {row['knows'].value} since {row['since'].value}")

    # Commit
    db.commit()

finally:
    # Cleanup
    db.close()
```

---

## See Also

- [Tutorial](tutorial.md) - Step-by-step guide
- [Cypher Guide](cypher-guide.md) - Supported Cypher syntax
- [Examples](../examples/) - Real-world use cases
- [Architecture](architecture-overview.md) - System design

---

**Questions or Issues?**

Report problems on [GitHub Issues](https://github.com/DecisionNerd/graphforge/issues).
