<h1 align="center">GraphForge</h1>

<p align="center">
  <a href="https://pypi.org/project/graphforge/"><img src="https://img.shields.io/pypi/v/graphforge.svg?label=PyPI&logo=pypi" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/graphforge/"><img src="https://img.shields.io/pypi/pyversions/graphforge.svg?logo=python&logoColor=white" alt="Python versions" /></a>
  <a href="https://github.com/DecisionNerd/graphforge/actions"><img src="https://github.com/DecisionNerd/graphforge/workflows/Test%20Suite/badge.svg" alt="Build status" /></a>
  <a href="https://codecov.io/gh/DecisionNerd/graphforge"><img src="https://codecov.io/gh/DecisionNerd/graphforge/graph/badge.svg" alt="Coverage" /></a>
  <a href="https://github.com/DecisionNerd/graphforge/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
  <a href="https://pypi.org/project/graphforge/"><img src="https://img.shields.io/pypi/dm/graphforge.svg?label=PyPI%20downloads" alt="PyPI downloads" /></a>
</p>
<p align="center">
  <strong>Composable graph tooling for analysis, construction, and refinement</strong>
</p>

<p align="center">
  A lightweight, embedded, openCypher-compatible graph engine for research and investigative workflows
</p>

---

## Table of Contents

- [Why GraphForge?](#why-graphforge)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Python API Reference](#python-api-reference)
- [Cypher Query Language](#cypher-query-language)
- [Usage Patterns](#usage-patterns)
- [Examples](#examples)
- [Advanced Features](#advanced-features)
- [Design Principles](#design-principles)
- [Contributing](#contributing)
- [License](#license)

---

## Why GraphForge?

Modern data science and ML workflows increasingly produce **graph-shaped data**—entities and relationships extracted from text, tables, and LLM outputs. Yet practitioners face a painful choice:

| | NetworkX | GraphForge | Production DBs (Neo4j, Memgraph) |
|:---|:---|:---|:---|
| **Durability** | Manual serialization | ✓ SQLite backend | ✓ Persistent |
| **Query language** | None | openCypher subset | Full Cypher |
| **Operational overhead** | Minimal | Minimal (embedded) | High (services, config) |
| **Notebook-friendly** | ✓ | ✓ | ✗ |
| **Iterative analysis** | ✓ | ✓ | Poor |

**GraphForge** fills the gap—embedded, durable, and declarative—without running external services.

> *We are not building a database for applications.*
> *We are building a graph execution environment for thinking.*

### Latest Release: v0.3.0

Version 0.3.0 brings major Cypher features and 109+ real-world datasets:

- **OPTIONAL MATCH** - Left outer joins with NULL preservation
- **UNION / UNION ALL** - Combine query results with deduplication
- **List comprehensions** - Transform and filter lists: `[x IN list WHERE x > 3 | x * 2]`
- **EXISTS / COUNT subqueries** - Correlated subqueries in expressions
- **Variable-length paths** - Recursive traversal: `-[:KNOWS*1..3]->`
- **109+ datasets** - SNAP, LDBC, NetworkRepository with automatic caching
- **Spatial types** - Point, Distance for geographic queries
- **Temporal types** - Date, DateTime, Time, Duration

**TCK Coverage**: 29% openCypher compatibility (up from 16.6%)

See [CHANGELOG.md](CHANGELOG.md) for complete release notes.

### Use Cases

**Knowledge Graph Construction**
- Extract entities and relationships from unstructured text
- Build and query knowledge graphs from documents
- Iteratively refine graph structures during analysis

**Data Lineage and Provenance**
- Track data transformations and dependencies
- Query upstream and downstream impacts
- Maintain audit trails of analytical workflows

**Network Analysis in Notebooks**
- Analyze social networks, citation graphs, dependency graphs
- Persist analysis results alongside code
- Share reproducible graph analyses

**LLM-Powered Graph Generation**
- Store LLM-extracted entities and relationships
- Query structured outputs from language models
- Build hybrid retrieval systems with graph context

---

## Installation

```bash
# Using uv (recommended)
uv add graphforge

# Using pip
pip install graphforge
```

**Requirements:** Python 3.10+

**Core Dependencies:**
- `pydantic>=2.6` - Data validation and type safety
- `lark>=1.1` - Cypher query parsing
- `msgpack>=1.0` - Efficient graph serialization

**Optional Dependencies:**
- `defusedxml` - Secure XML parsing for GraphML datasets
- `zstandard` - Support for .tar.zst compression (LDBC datasets)

---

## Quick Start

### 5-Minute Introduction

```python
from graphforge import GraphForge

# Create an in-memory graph
db = GraphForge()

# Option 1: Python API (imperative)
alice = db.create_node(['Person'], name='Alice', age=30)
bob = db.create_node(['Person'], name='Bob', age=25)
db.create_relationship(alice, bob, 'KNOWS', since=2020)

# Option 2: Cypher queries (declarative)
db.execute("CREATE (c:Person {name: 'Charlie', age: 35})")
db.execute("MATCH (a:Person {name: 'Alice'}), (c:Person {name: 'Charlie'}) CREATE (a)-[:KNOWS]->(c)")

# Query the graph
results = db.execute("""
    MATCH (p:Person)-[:KNOWS]->(friend:Person)
    WHERE p.age > 25
    RETURN p.name AS person, friend.name AS friend
    ORDER BY p.age DESC
""")

for row in results:
    print(f"{row['person'].value} knows {row['friend'].value}")
# Output:
# Charlie knows Alice
# Alice knows Bob
# Alice knows Charlie
```

### Spatial and Temporal Types

GraphForge supports spatial types (Point, Distance) and temporal types (Date, DateTime, Time, Duration):

```python
from graphforge import GraphForge

db = GraphForge()

# Create nodes with spatial properties using Cypher
db.execute("CREATE (:Place {name: 'Office', location: point({x: 1.0, y: 2.0})})")
db.execute("CREATE (:Place {name: 'Home', location: point({x: 5.0, y: 3.0})})")

# Or use the Python API with coordinate dictionaries
db.create_node(['Place'], name='Cafe', location={"x": 3.0, "y": 4.0})

# Geographic coordinates (latitude, longitude)
db.create_node(['City'], name='SF', location={"latitude": 37.7749, "longitude": -122.4194})

# Calculate distances between points
results = db.execute("""
    MATCH (a:Place {name: 'Office'}), (b:Place {name: 'Home'})
    RETURN distance(a.location, b.location) AS dist
""")
print(f"Distance: {results[0]['dist'].value:.2f} units")

# Temporal types for dates and times
db.execute("""
    CREATE (:Event {
        name: 'Meeting',
        date: date('2024-01-15'),
        start_time: datetime('2024-01-15T14:00:00'),
        duration: duration({hours: 2, minutes: 30})
    })
""")

# Query events in a date range
results = db.execute("""
    MATCH (e:Event)
    WHERE e.date >= date('2024-01-01')
    RETURN e.name, e.date, e.duration
""")
```

### Persistent Graphs

```python
# Create a persistent graph
db = GraphForge("my-research.db")

# Add data (persists automatically on close)
db.execute("CREATE (p:Paper {title: 'Graph Neural Networks', year: 2021})")
db.close()

# Later: reload the same graph
db = GraphForge("my-research.db")
results = db.execute("MATCH (p:Paper) RETURN p.title AS title")
print(results[0]['title'].value)  # Graph Neural Networks
```

### Load Real-World Datasets

Analyze real networks instantly with built-in datasets:

```python
from graphforge import GraphForge
from graphforge.datasets import load_dataset

# Create graph and load a dataset (automatically downloads and caches)
db = GraphForge()
load_dataset(db, "snap-ego-facebook")

# Analyze the social network
results = db.execute("""
    MATCH (n)-[r]->()
    RETURN n.id AS user, count(r) AS connections
    ORDER BY connections DESC
    LIMIT 5
""")

for row in results:
    print(f"User {row['user'].value}: {row['connections'].value} connections")
```

**Available datasets:**
- **SNAP** (Stanford): 95 real-world networks (social, web, email, collaboration, citation)
- **LDBC** (Linked Data Benchmark Council): 10 social network benchmark datasets
- **NetworkRepository**: 10 pre-registered datasets + load thousands more via direct URL

**Load from URL:**
```python
# Load any NetworkRepository dataset by URL
load_dataset(db, "https://nrvis.com/download/data/labeled/karate.zip")
```

Browse and filter datasets:
```python
from graphforge.datasets import list_datasets

# List all datasets (109+ available)
datasets = list_datasets()
print(f"Total datasets: {len(datasets)}")

# Filter by source
snap_datasets = list_datasets(source="snap")       # 95 SNAP datasets
ldbc_datasets = list_datasets(source="ldbc")       # 10 LDBC benchmarks
netrepo_datasets = list_datasets(source="netrepo") # 10 NetworkRepository

# View dataset details
for ds in ldbc_datasets[:3]:
    print(f"{ds.name}: {ds.nodes:,} nodes, {ds.edges:,} edges ({ds.size_mb:.1f} MB)")
```

**Dataset Sources:**

1. **SNAP (Stanford Network Analysis Project)** - 95 datasets
   - Social networks (Facebook, Twitter, email)
   - Collaboration networks (arXiv, DBLP)
   - Web graphs (Google, Wikipedia)
   - Citation networks (patents, papers)

2. **LDBC (Linked Data Benchmark Council)** - 10 datasets
   - Social Network Benchmark (SNB) with varying scale factors
   - Realistic social network schemas with temporal data
   - Used for performance benchmarking

3. **NetworkRepository** - 10 pre-registered + thousands via URL
   - Biological networks (protein interactions, gene regulation)
   - Infrastructure networks (power grids, road networks)
   - Social and collaboration networks
   - Load any dataset directly via URL without pre-registration

---

## Core Concepts

### Nodes and Relationships

**Nodes** represent entities with:
- **Labels**: Categories like `Person`, `Document`, `Gene`
- **Properties**: Key-value attributes (strings, integers, booleans, lists, maps)
- **IDs**: Auto-generated unique identifiers

**Relationships** connect nodes with:
- **Type**: Semantic connection like `KNOWS`, `CITES`, `REGULATES`
- **Direction**: From source node to destination node
- **Properties**: Attributes on the relationship itself

```python
# Python API
alice = db.create_node(['Person', 'Employee'],
                       name='Alice',
                       age=30,
                       skills=['Python', 'ML'])

bob = db.create_node(['Person'], name='Bob', age=25)

knows = db.create_relationship(alice, bob, 'KNOWS',
                               since=2020,
                               strength='strong')

# Cypher equivalent
db.execute("""
    CREATE (a:Person:Employee {name: 'Alice', age: 30, skills: ['Python', 'ML']})
    CREATE (b:Person {name: 'Bob', age: 25})
    CREATE (a)-[:KNOWS {since: 2020, strength: 'strong'}]->(b)
""")
```

### Graph Patterns

GraphForge uses **graph patterns** for both matching and creating:

```
(n:Person)                          # Node with label
(n:Person {age: 30})               # Node with properties
(a)-[r:KNOWS]->(b)                 # Directed relationship
(a)-[r:KNOWS]-(b)                  # Undirected relationship
(a)-[:KNOWS|LIKES]->(b)            # Multiple relationship types
```

---

## Python API Reference

### GraphForge Class

#### `__init__(path: str | Path | None = None)`

Initialize a GraphForge instance.

**Parameters:**
- `path` (optional): Path to SQLite database file. If `None`, uses in-memory storage.

**Example:**
```python
# In-memory (data lost on exit)
db = GraphForge()

# Persistent (data saved to disk)
db = GraphForge("graphs/social-network.db")
```

#### `create_node(labels: list[str] | None = None, **properties) -> NodeRef`

Create a node with labels and properties.

**Parameters:**
- `labels`: List of label strings (e.g., `['Person', 'Employee']`)
- `**properties`: Property key-value pairs. Values are automatically converted to CypherValue types:
  - `str`, `int`, `float`, `bool`, `None` → Primitive types
  - `list` → `CypherList`
  - `dict` → `CypherMap` or `CypherPoint` (if coordinate dict)
  - Coordinate dicts (`{"x": 1.0, "y": 2.0}`) → `CypherPoint`
  - Date/time objects → Temporal types

**Returns:** `NodeRef` for the created node

**Example:**
```python
# Standard properties
alice = db.create_node(
    ['Person', 'Employee'],
    name='Alice',
    age=30,
    active=True,
    skills=['Python', 'SQL'],
    metadata={'department': 'Engineering'}
)

# Spatial properties (auto-detected)
office = db.create_node(
    ['Place'],
    name='Office',
    location={"x": 1.0, "y": 2.0}  # Automatically becomes CypherPoint
)

# Geographic coordinates
city = db.create_node(
    ['City'],
    name='San Francisco',
    location={"latitude": 37.7749, "longitude": -122.4194}
)
```

#### `create_relationship(src: NodeRef, dst: NodeRef, rel_type: str, **properties) -> EdgeRef`

Create a directed relationship between two nodes.

**Parameters:**
- `src`: Source node (NodeRef)
- `dst`: Destination node (NodeRef)
- `rel_type`: Relationship type string (e.g., `'KNOWS'`, `'WORKS_AT'`)
- `**properties`: Property key-value pairs

**Returns:** `EdgeRef` for the created relationship

**Example:**
```python
alice = db.create_node(['Person'], name='Alice')
company = db.create_node(['Company'], name='Acme Corp')

works_at = db.create_relationship(
    alice,
    company,
    'WORKS_AT',
    since=2020,
    role='Engineer'
)
```

#### `execute(query: str) -> list[dict]`

Execute an openCypher query.

**Parameters:**
- `query`: openCypher query string

**Returns:** List of result rows as dictionaries

**Example:**
```python
results = db.execute("""
    MATCH (p:Person)-[r:KNOWS]->(friend:Person)
    WHERE p.age > 25
    RETURN p.name AS person, count(friend) AS friend_count
    ORDER BY friend_count DESC
    LIMIT 10
""")

for row in results:
    print(f"{row['person'].value}: {row['friend_count'].value} friends")
```

#### `begin()`

Start an explicit transaction.

**Example:**
```python
db.begin()
db.execute("CREATE (n:Person {name: 'Alice'})")
db.commit()  # or db.rollback()
```

#### `commit()`

Commit the current transaction. Saves changes to disk if using persistence.

**Raises:** `RuntimeError` if not in a transaction

#### `rollback()`

Roll back the current transaction. Reverts all changes made since `begin()`.

**Raises:** `RuntimeError` if not in a transaction

#### `close()`

Save graph and close database. Safe to call multiple times.

**Example:**
```python
db = GraphForge("my-graph.db")
# ... make changes ...
db.close()  # Saves to disk
```

### Accessing Result Values

Query results contain `CypherValue` objects. Access the underlying Python value with `.value`:

```python
results = db.execute("MATCH (p:Person) RETURN p.name AS name, p.age AS age")

for row in results:
    name = row['name'].value      # str
    age = row['age'].value        # int
    print(f"{name} is {age} years old")
```

**Supported Value Types:**
- `CypherString`: Python `str`
- `CypherInt`: Python `int`
- `CypherFloat`: Python `float`
- `CypherBool`: Python `bool`
- `CypherNull`: Python `None`
- `CypherList`: Python `list` (nested CypherValues)
- `CypherMap`: Python `dict` (string keys, CypherValue values)
- `CypherPoint`: Spatial point with coordinates
- `CypherDistance`: Distance between points
- `CypherDate`: Date (year, month, day)
- `CypherDateTime`: Date and time with timezone
- `CypherTime`: Time of day
- `CypherDuration`: Time duration (years, months, days, hours, etc.)

---

## Cypher Query Language

GraphForge supports a subset of openCypher for declarative graph queries and mutations.

### MATCH - Pattern Matching

Find nodes and relationships matching a pattern.

```cypher
-- Match all nodes
MATCH (n)
RETURN n

-- Match nodes by label
MATCH (p:Person)
RETURN p.name

-- Match with multiple labels
MATCH (p:Person:Employee)
RETURN p

-- Match relationships
MATCH (a:Person)-[r:KNOWS]->(b:Person)
RETURN a.name, b.name, r.since

-- Match specific direction
MATCH (a)-[:FOLLOWS]->(b)    -- Outgoing
MATCH (a)<-[:FOLLOWS]-(b)    -- Incoming
MATCH (a)-[:FOLLOWS]-(b)     -- Either direction

-- Multiple relationship types
MATCH (a)-[r:KNOWS|LIKES]->(b)
RETURN type(r), a.name, b.name
```

### WHERE - Filtering

Filter matched patterns with predicates.

```cypher
-- Property comparisons
MATCH (p:Person)
WHERE p.age > 30
RETURN p.name

-- Logical operators
MATCH (p:Person)
WHERE p.age > 25 AND p.city = 'NYC'
RETURN p.name

MATCH (p:Person)
WHERE p.age < 30 OR p.active = true
RETURN p.name

-- Property existence (returns false for null)
MATCH (p:Person)
WHERE p.email <> null
RETURN p.name
```

### RETURN - Projection

Select and transform query results.

```cypher
-- Return specific properties
MATCH (p:Person)
RETURN p.name, p.age

-- With aliases
MATCH (p:Person)
RETURN p.name AS person_name, p.age AS person_age

-- Return entire nodes/relationships
MATCH (p:Person)-[r:KNOWS]->(friend)
RETURN p, r, friend
```

### CREATE - Graph Construction

Create new nodes and relationships.

```cypher
-- Create single node
CREATE (n:Person {name: 'Alice', age: 30})

-- Create multiple nodes
CREATE (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})

-- Create nodes with relationship
CREATE (a:Person {name: 'Alice'})-[r:KNOWS {since: 2020}]->(b:Person {name: 'Bob'})

-- Create with RETURN
CREATE (n:Person {name: 'Alice'})
RETURN n.name AS name
```

### SET - Update Properties

Update properties on existing nodes and relationships.

```cypher
-- Update single property
MATCH (p:Person {name: 'Alice'})
SET p.age = 31

-- Update multiple properties
MATCH (p:Person {name: 'Alice'})
SET p.age = 31, p.city = 'NYC', p.active = true

-- Update relationship properties
MATCH (a)-[r:KNOWS]->(b)
WHERE a.name = 'Alice'
SET r.strength = 'strong'
```

### DELETE - Remove Elements

Delete nodes and relationships.

```cypher
-- Delete specific node (and its relationships)
MATCH (p:Person {name: 'Alice'})
DELETE p

-- Delete relationship only
MATCH (a)-[r:KNOWS]->(b)
WHERE a.name = 'Alice' AND b.name = 'Bob'
DELETE r

-- Delete multiple elements
MATCH (a)-[r:KNOWS]->(b)
WHERE b.name = 'Bob'
DELETE r, b
```

### MERGE - Idempotent Creation

Create nodes if they don't exist, or match existing ones.

```cypher
-- Create or match
MERGE (p:Person {name: 'Alice'})

-- Always matches same node (idempotent)
MERGE (p:Person {name: 'Alice', age: 30})
MERGE (p:Person {name: 'Alice', age: 30})
-- Results in only 1 node

-- With RETURN
MERGE (p:Person {name: 'Alice'})
RETURN p.name
```

### ORDER BY - Sorting

Sort query results.

```cypher
-- Ascending (default)
MATCH (p:Person)
RETURN p.name, p.age
ORDER BY p.age

-- Descending
MATCH (p:Person)
RETURN p.name, p.age
ORDER BY p.age DESC

-- Multiple sort keys
MATCH (p:Person)
RETURN p.name, p.age, p.city
ORDER BY p.city ASC, p.age DESC
```

### LIMIT and SKIP - Pagination

Limit and paginate results.

```cypher
-- Get first 10 results
MATCH (p:Person)
RETURN p.name
ORDER BY p.name
LIMIT 10

-- Skip first 20, return next 10
MATCH (p:Person)
RETURN p.name
ORDER BY p.name
SKIP 20
LIMIT 10
```

### Aggregations

Compute aggregate functions over groups.

```cypher
-- Count all
MATCH (p:Person)
RETURN count(*) AS total

-- Count with grouping
MATCH (p:Person)
RETURN p.city, count(*) AS population
ORDER BY population DESC

-- Multiple aggregations
MATCH (p:Person)
RETURN
    count(*) AS total,
    sum(p.age) AS total_age,
    avg(p.age) AS avg_age,
    min(p.age) AS youngest,
    max(p.age) AS oldest

-- Aggregation with WHERE
MATCH (p:Person)
WHERE p.active = true
RETURN p.department, count(*) AS active_count
```

**Supported Functions:**
- `count(*)` - Count all rows
- `count(expr)` - Count non-null values
- `sum(expr)` - Sum numeric values
- `avg(expr)` - Average of numeric values
- `min(expr)` - Minimum value
- `max(expr)` - Maximum value

---

## Usage Patterns

### Pattern 1: Exploratory Analysis

Use in-memory graphs for quick exploration, then persist interesting results.

```python
# Start with in-memory for speed
db = GraphForge()

# Load and explore data
db.execute("CREATE (:Author {name: 'Alice', h_index: 42})")
db.execute("CREATE (:Author {name: 'Bob', h_index: 38})")
# ... load more data ...

# Explore interactively
results = db.execute("""
    MATCH (a:Author)
    WHERE a.h_index > 40
    RETURN a.name, a.h_index
    ORDER BY a.h_index DESC
""")

# If analysis is valuable, save it
if len(results) > 0:
    db_persistent = GraphForge("high-impact-authors.db")
    # Copy relevant subgraph...
    db_persistent.close()
```

### Pattern 2: Incremental Construction

Build graphs incrementally across sessions.

```python
# Session 1: Initial data
db = GraphForge("knowledge-graph.db")
db.execute("CREATE (:Concept {name: 'Machine Learning'})")
db.close()

# Session 2: Add related concepts
db = GraphForge("knowledge-graph.db")
db.execute("""
    MATCH (ml:Concept {name: 'Machine Learning'})
    CREATE (dl:Concept {name: 'Deep Learning'})
    CREATE (ml)-[:SPECIALIZES_TO]->(dl)
""")
db.close()

# Session 3: Add more relationships
db = GraphForge("knowledge-graph.db")
db.execute("""
    MATCH (dl:Concept {name: 'Deep Learning'})
    CREATE (cv:Concept {name: 'Computer Vision'})
    CREATE (dl)-[:APPLIED_IN]->(cv)
""")
db.close()
```

### Pattern 3: Transactional Updates

Use transactions for atomic updates.

```python
db = GraphForge("production-graph.db")

try:
    db.begin()

    # Update multiple related entities
    db.execute("MATCH (p:Person {id: 123}) SET p.status = 'inactive'")
    db.execute("MATCH (p:Person {id: 123})-[r:WORKS_AT]->() DELETE r")
    db.execute("CREATE (:AuditLog {action: 'deactivate', user_id: 123, timestamp: 1234567890})")

    db.commit()
except Exception as e:
    db.rollback()
    print(f"Transaction failed: {e}")
finally:
    db.close()
```

### Pattern 4: ETL Pipelines

Extract, transform, and load data into graph format.

```python
import pandas as pd

# Load tabular data
papers = pd.read_csv("papers.csv")
citations = pd.read_csv("citations.csv")

# Transform to graph
db = GraphForge("citation-network.db")

# Create nodes from DataFrame
for _, row in papers.iterrows():
    db.execute("""
        CREATE (:Paper {
            id: $id,
            title: $title,
            year: $year,
            citations: $citations
        })
    """, {'id': row['id'], 'title': row['title'],
          'year': int(row['year']), 'citations': int(row['citation_count'])})

# Create relationships from edges DataFrame
for _, row in citations.iterrows():
    db.execute("""
        MATCH (citing:Paper {id: $citing_id})
        MATCH (cited:Paper {id: $cited_id})
        CREATE (citing)-[:CITES]->(cited)
    """, {'citing_id': row['citing_paper'], 'cited_id': row['cited_paper']})

db.close()
```

### Pattern 5: Testing and Validation

Use transactions for isolated testing.

```python
def test_graph_algorithm():
    db = GraphForge()

    # Setup test data
    db.execute("CREATE (a:Node {id: 1})-[:LINKS]->(b:Node {id: 2})")
    db.execute("CREATE (b)-[:LINKS]->(c:Node {id: 3})")

    # Test query
    results = db.execute("""
        MATCH path = (a:Node {id: 1})-[:LINKS*]->(c:Node)
        RETURN count(*) AS path_count
    """)

    assert results[0]['path_count'].value == 2
```

---

## Examples

### Example 1: Social Network Analysis

```python
from graphforge import GraphForge

# Create social network
db = GraphForge("social-network.db")

# Add people
people = [
    ("Alice", 30, "NYC"),
    ("Bob", 25, "NYC"),
    ("Charlie", 35, "LA"),
    ("Diana", 28, "NYC"),
]

for name, age, city in people:
    db.execute(f"""
        CREATE (:Person {{name: '{name}', age: {age}, city: '{city}'}})
    """)

# Add friendships
friendships = [
    ("Alice", "Bob", 2015),
    ("Alice", "Charlie", 2018),
    ("Bob", "Diana", 2019),
    ("Charlie", "Diana", 2020),
]

for person1, person2, since in friendships:
    db.execute(f"""
        MATCH (a:Person {{name: '{person1}'}})
        MATCH (b:Person {{name: '{person2}'}})
        CREATE (a)-[:KNOWS {{since: {since}}}]->(b)
    """)

# Analysis: Who has the most friends?
results = db.execute("""
    MATCH (p:Person)-[:KNOWS]-(friend:Person)
    RETURN p.name AS person, count(DISTINCT friend) AS friend_count
    ORDER BY friend_count DESC
""")

print("Friend counts:")
for row in results:
    print(f"  {row['person'].value}: {row['friend_count'].value} friends")

# Analysis: People in NYC who know each other
results = db.execute("""
    MATCH (a:Person)-[:KNOWS]-(b:Person)
    WHERE a.city = 'NYC' AND b.city = 'NYC'
    RETURN DISTINCT a.name AS person1, b.name AS person2
""")

print("\nNYC connections:")
for row in results:
    print(f"  {row['person1'].value} ↔ {row['person2'].value}")

db.close()
```

### Example 2: Document Citation Network

```python
from graphforge import GraphForge

db = GraphForge("citations.db")

# Create papers
papers = [
    ("P1", "Graph Neural Networks", 2021, "Smith"),
    ("P2", "Deep Learning Fundamentals", 2019, "Jones"),
    ("P3", "GNN Applications", 2022, "Smith"),
]

for paper_id, title, year, author in papers:
    db.execute("""
        MERGE (p:Paper {id: $id})
        SET p.title = $title, p.year = $year
        MERGE (a:Author {name: $author})
        CREATE (a)-[:AUTHORED]->(p)
    """, {'id': paper_id, 'title': title, 'year': year, 'author': author})

# Add citations
db.execute("""
    MATCH (p1:Paper {id: 'P3'})
    MATCH (p2:Paper {id: 'P1'})
    CREATE (p1)-[:CITES]->(p2)
""")

db.execute("""
    MATCH (p1:Paper {id: 'P1'})
    MATCH (p2:Paper {id: 'P2'})
    CREATE (p1)-[:CITES]->(p2)
""")

# Find most cited papers
results = db.execute("""
    MATCH (p:Paper)<-[:CITES]-(citing:Paper)
    RETURN p.title AS paper, count(citing) AS citation_count
    ORDER BY citation_count DESC
""")

print("Most cited papers:")
for row in results:
    print(f"  {row['paper'].value}: {row['citation_count'].value} citations")

# Find papers by prolific authors
results = db.execute("""
    MATCH (a:Author)-[:AUTHORED]->(p:Paper)
    RETURN a.name AS author, count(p) AS paper_count
    ORDER BY paper_count DESC
""")

print("\nAuthor productivity:")
for row in results:
    print(f"  {row['author'].value}: {row['paper_count'].value} papers")

db.close()
```

### Example 3: Knowledge Graph from LLM Output

```python
from graphforge import GraphForge
import json

db = GraphForge("knowledge-graph.db")

# Simulated LLM extraction result
llm_output = {
    "entities": [
        {"name": "Python", "type": "Language", "properties": {"paradigm": "multi"}},
        {"name": "Java", "type": "Language", "properties": {"paradigm": "OOP"}},
        {"name": "Django", "type": "Framework", "properties": {"category": "web"}},
    ],
    "relationships": [
        {"source": "Django", "target": "Python", "type": "WRITTEN_IN"},
        {"source": "Python", "target": "Java", "type": "INFLUENCED_BY"},
    ]
}

# Import entities
for entity in llm_output["entities"]:
    props_str = ", ".join([f"{k}: '{v}'" for k, v in entity["properties"].items()])
    db.execute(f"""
        CREATE (:{entity['type']} {{name: '{entity['name']}', {props_str}}})
    """)

# Import relationships
for rel in llm_output["relationships"]:
    db.execute(f"""
        MATCH (source {{name: '{rel['source']}'}})
        MATCH (target {{name: '{rel['target']}'}})
        CREATE (source)-[:{rel['type']}]->(target)
    """)

# Query the knowledge graph
results = db.execute("""
    MATCH (f:Framework)-[:WRITTEN_IN]->(l:Language)
    RETURN f.name AS framework, l.name AS language
""")

print("Frameworks and their languages:")
for row in results:
    print(f"  {row['framework'].value} is written in {row['language'].value}")

# Find influence chains
results = db.execute("""
    MATCH (a:Language)-[:INFLUENCED_BY]->(b:Language)
    RETURN a.name AS language, b.name AS influenced_by
""")

print("\nLanguage influences:")
for row in results:
    print(f"  {row['language'].value} was influenced by {row['influenced_by'].value}")

db.close()
```

---

## Advanced Features

### Transaction Isolation

Transactions provide snapshot isolation—queries within a transaction see uncommitted changes.

```python
db = GraphForge("test.db")

db.execute("CREATE (:Person {name: 'Alice'})")

db.begin()
db.execute("CREATE (:Person {name: 'Bob'})")

# Query sees uncommitted Bob
results = db.execute("MATCH (p:Person) RETURN count(*) AS count")
print(results[0]['count'].value)  # 2

db.rollback()

# After rollback, Bob is gone
results = db.execute("MATCH (p:Person) RETURN count(*) AS count")
print(results[0]['count'].value)  # 1
```

### Deep Property Access

Access nested properties in complex structures.

```python
db.execute("""
    CREATE (:Document {
        metadata: {
            author: 'Alice',
            tags: ['ML', 'Python'],
            version: {major: 1, minor: 2}
        }
    })
""")

results = db.execute("""
    MATCH (d:Document)
    RETURN d.metadata AS metadata
""")

metadata = results[0]['metadata'].value
print(metadata['author'].value)              # 'Alice'
print(metadata['tags'].value[0].value)      # 'ML'
print(metadata['version'].value['major'].value)  # 1
```

### Dataset Import and Export

GraphForge supports multiple dataset formats and compression schemes:

**Supported Loaders:**
- **CSV**: Edge-list format (SNAP datasets)
- **Cypher**: Cypher script format (LDBC datasets)
- **GraphML**: XML-based format with type-aware parsing (NetworkRepository)
- **JSON Graph**: JSON interchange format for graph data

**Supported Compression:**
- `.tar.gz` - Gzip compressed tar archives
- `.tar.zst` - Zstandard compressed tar archives (LDBC)
- `.zip` - Zip archives (NetworkRepository)
- Direct `.graphml` files

**Example: Load from various sources**
```python
from graphforge import GraphForge
from graphforge.datasets import load_dataset

db = GraphForge()

# Load pre-registered dataset (auto-detects format)
load_dataset(db, "snap-email-enron")  # CSV format
load_dataset(db, "ldbc-snb-sf0.1")    # Cypher script format
load_dataset(db, "netrepo-karate")    # GraphML format

# Load from direct URLs
load_dataset(db, "https://nrvis.com/download/data/labeled/karate.zip")

# All formats support automatic caching
```

### Graph Export

Export subgraphs for sharing or archival.

```python
def export_subgraph(db, query, output_file):
    """Export query results to JSON."""
    results = db.execute(query)

    nodes = set()
    edges = []

    for row in results:
        # Extract nodes and relationships from result
        # (Implementation depends on your export format)
        pass

    with open(output_file, 'w') as f:
        json.dump({'nodes': list(nodes), 'edges': edges}, f)

# Export high-impact authors
export_subgraph(
    db,
    "MATCH (a:Author) WHERE a.h_index > 40 RETURN a",
    "high-impact-authors.json"
)
```

---

## Design Principles

### Spec-Driven Correctness

GraphForge prioritizes **semantic correctness** over raw performance. All query behavior is validated against the openCypher TCK (Technology Compatibility Kit).

**What this means:**
- Queries behave predictably and correctly
- Null handling follows openCypher semantics
- Aggregations produce deterministic results
- Type coercion is explicit and safe

### Deterministic & Reproducible

GraphForge produces **stable, reproducible results** across runs.

**What this means:**
- Same query on same data always produces same results
- Transaction isolation guarantees snapshot consistency
- No hidden state or random behavior
- Ideal for scientific workflows and testing

### Inspectable

GraphForge makes query execution **observable and debuggable**.

**What this means:**
- Query plans can be inspected (future feature)
- Storage layout is simple SQLite (readable with any SQLite tool)
- Execution behavior is predictable and traceable
- No magic or hidden optimizations

### Replaceable Internals

GraphForge components are **modular and replaceable**.

**What this means:**
- Parser, planner, executor, storage are independent
- SQLite backend can be swapped for other storage
- Minimal operational dependencies
- Zero configuration required

---

## Architecture

GraphForge is built in four layers:

```
┌─────────────────────────────────┐
│  Parser (Lark + AST)            │  Cypher → Abstract Syntax Tree
├─────────────────────────────────┤
│  Planner (Logical Operators)    │  AST → Logical Plan
├─────────────────────────────────┤
│  Executor (Pipeline Engine)     │  Plan → Results
├─────────────────────────────────┤
│  Storage (Graph + SQLite)       │  In-Memory + Persistence
└─────────────────────────────────┘
```

**Parser:** Lark-based openCypher parser with full AST generation
**Planner:** Logical plan generation (ScanNodes, ExpandEdges, Filter, Project, Sort, Aggregate)
**Executor:** Pipeline-based query execution with streaming rows
**Storage:** Dual-mode storage—in-memory graphs with optional SQLite persistence

### Storage Backend

GraphForge uses SQLite with Write-Ahead Logging (WAL) for durability:

- **ACID guarantees**: Atomicity, Consistency, Isolation, Durability
- **Zero configuration**: No server setup or connection management
- **Single-file databases**: Easy to version control and share
- **Concurrent reads**: Multiple readers, single writer
- **MessagePack serialization**: Efficient binary encoding for complex types

The architecture prioritizes **correctness** and **developer experience** over raw performance, with all components designed to be testable, inspectable, and replaceable.

---

## Performance Characteristics

GraphForge is optimized for **interactive analysis** on small-to-medium graphs (thousands to millions of nodes).

**Expected Performance:**
- Node/edge creation: ~10-50K operations/sec (in-memory)
- Simple traversals: ~100K-1M edges/sec
- Complex queries: Depends on query complexity and graph size
- Persistence overhead: ~2-5x slower than in-memory

**When to Use GraphForge:**
- Graphs with < 10M nodes
- Interactive analysis in notebooks
- Iterative graph construction
- Research and exploration workflows

**When NOT to Use GraphForge:**
- Production applications requiring high throughput
- Graphs with > 100M nodes
- Real-time query serving
- Multi-user concurrent writes

For production workloads, consider Neo4j, Memgraph, or other production graph databases.

---

## Roadmap

**Completed (v0.3.0 - Full Dataset Integration):**
- ✅ MATCH, WHERE, RETURN, ORDER BY, LIMIT, SKIP, WITH
- ✅ Aggregations (COUNT, SUM, AVG, MIN, MAX, COLLECT)
- ✅ CREATE, SET, DELETE, MERGE, REMOVE clauses
- ✅ UNWIND for list iteration
- ✅ CASE expressions and arithmetic operators (+, -, *, /, %)
- ✅ String matching (STARTS WITH, ENDS WITH, CONTAINS)
- ✅ Spatial types (Point, Distance) with automatic detection in Python API
- ✅ Temporal types (Date, DateTime, Time, Duration)
- ✅ Graph introspection functions (id, labels, type)
- ✅ Python builder API with full type support
- ✅ SQLite persistence with ACID transactions
- ✅ 115+ datasets (95 SNAP + 10 LDBC + 10 NetworkRepository)
- ✅ Dynamic dataset loading via URL
- ✅ GraphML loader with type-aware parsing
- ✅ Compression support (.tar.gz, .tar.zst, .zip)
- ✅ 1,277/7,722 TCK scenarios (16.5%)

**Planned (v0.4.0 - Advanced Patterns):**
- ⏳ Variable-length patterns `-[*1..5]->` ([#24](https://github.com/DecisionNerd/graphforge/issues/24))
- ⏳ OPTIONAL MATCH (left outer joins)
- ⏳ List comprehensions `[x IN list WHERE ...]`
- ⏳ Subqueries (EXISTS, COUNT)
- ⏳ UNION / UNION ALL
- 🎯 Target: ~1,500 TCK scenarios (~39%)

**Future Considerations:**
- v0.5+: Additional functions, performance optimization
- v1.0: Full OpenCypher (>99% TCK compliance - complete production platform)
- Query plan visualization and EXPLAIN
- Performance profiling tools
- Modern APIs (REST, GraphQL, WebSocket)
- Analytical integrations (NetworkX, iGraph, QuantumFusion)
- Ontology support and schema validation

**See [OpenCypher Compatibility](docs/reference/opencypher-compatibility.md) for detailed feature matrix.**

---

## Cypher Compatibility

GraphForge implements a **practical subset of OpenCypher** focused on common graph operations. It is **not** a full OpenCypher implementation.

### ✅ Supported (v0.2.0)

**Reading & Writing:**
- MATCH, WHERE, RETURN, WITH, ORDER BY, LIMIT, SKIP
- CREATE, SET, DELETE, REMOVE, MERGE, DETACH DELETE
- Pattern matching (nodes and relationships)
- Property filtering and updates

**Expressions:**
- CASE expressions (conditional logic)
- Arithmetic operators: +, -, *, /, %
- Comparison operators: =, <>, <, >, <=, >=
- Logical operators: AND, OR, NOT
- String matching: STARTS WITH, ENDS WITH, CONTAINS

**Aggregations:**
- COUNT, SUM, AVG, MIN, MAX, COLLECT
- Implicit GROUP BY
- DISTINCT modifier

**Functions:**
- String: length, substring, toUpper, toLower, trim
- Type conversion: toInteger, toFloat, toString
- Spatial: point, distance
- Temporal: date, datetime, time, duration
- Graph: id, labels, type
- Utility: coalesce

**Data Types:**
- Primitives: Integer, float, string, boolean, null
- Collections: Lists, maps (nested structures)
- Spatial types: Point (cartesian, geographic), Distance
- Temporal types: Date, DateTime, Time, Duration
- Graph elements: Nodes, relationships

**Other:**
- UNWIND (list iteration)
- List and map literals
- NULL handling with ternary logic

### ⏳ Planned (v0.3+)

- OPTIONAL MATCH (left outer joins)
- Variable-length patterns: `-[*1..5]->`
- List comprehensions: `[x IN list WHERE ...]`
- Subqueries: EXISTS, COUNT
- UNION / UNION ALL
- 50+ additional functions

### ❌ Out of Scope

- Full-text search and advanced indexing
- Multi-database features
- User management / security
- Stored procedures and user-defined functions
- Distributed queries and sharding

### TCK Compliance

GraphForge tracks compliance using the openCypher Technology Compatibility Kit (TCK):

| Version | Scenarios | Percentage |
|---------|-----------|------------|
| v0.1.4 | 1,277/7,722 | 16.5% |
| v0.2.0 | ~1,900/7,722 | ~25% |
| v0.3.0 | ~3,000/7,722 | ~39% |
| v0.4.0 (target) | ~4,250/7,722 | ~55% |
| v0.5.0 (target) | ~5,400/7,722 | ~70% |
| v0.6.0 (target) | ~6,300/7,722 | ~82% |
| v0.7.0 (target) | ~7,100/7,722 | ~92% |
| v1.0 (target) | >7,650/7,722 | >99% |

**See [OpenCypher Compatibility](docs/reference/opencypher-compatibility.md) for complete details.**

---

## Contributing

GraphForge is in active development. Contributions are welcome!

### Development Workflow

Before pushing code, run:

```bash
make pre-push
```

This runs:
- Code formatting checks (ruff format --check)
- Linting (ruff check)
- Type checking (mypy)
- Security scanning (bandit)
- Tests with coverage measurement
- Coverage threshold validation (minimum 85%)

### Coverage

View detailed coverage report:

```bash
make coverage-report
```

Check coverage for your changes only:

```bash
make coverage-diff
```

Run tests with coverage manually:

```bash
make coverage
```

For new features, optionally check against a stricter 90% threshold:

```bash
make coverage-strict
```

### Coverage Requirements

- **Project coverage**: 85% of entire codebase (checked by `make pre-push`)
- **Patch coverage**: 80% of new/changed lines (checked by codecov in CI)

**Best practice**: Aim for 100% coverage of new code to ensure both thresholds pass.

### Test Analytics

GraphForge uses [Codecov Test Analytics](https://docs.codecov.com/docs/test-analytics) to monitor test performance and reliability across our **8,203 tests** (481 unit/integration + 7,722 TCK compliance tests).

**What we track:**
- ⏱️ Test execution time and performance trends
- 🔄 Flaky tests (tests that intermittently fail)
- ❌ Test failure rates and patterns
- 📊 Test suite health over time

**Benefits:**
- Identify slow tests that need optimization
- Catch flaky tests before they become problematic
- Track test performance degradation
- Improve CI/CD reliability

Test analytics data is automatically collected in CI and viewable on the [Codecov dashboard](https://app.codecov.io/gh/DecisionNerd/graphforge).

### Areas for Contribution

- Additional Cypher features
- Performance optimizations
- Documentation and examples
- Bug reports and fixes
- Integration with data science tools

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Documentation

Full documentation is available at **[decisionnerd.github.io/graphforge](https://decisionnerd.github.io/graphforge/)**

Quick links:
- **[Quick Start Tutorial](docs/getting-started/tutorial.md)** — Step-by-step guide for new users
- **[API Reference](docs/reference/api.md)** — Complete Python API documentation
- **[Cypher Language Guide](docs/guide/cypher-guide.md)** — openCypher subset reference
- **[Architecture Overview](docs/architecture/overview.md)** — System design and internals
- **[OpenCypher Compatibility](docs/reference/opencypher-compatibility.md)** — Feature matrix and compliance

---

## Testing

GraphForge has **1,721 tests** covering:
- Unit tests for parser, planner, executor, storage (comprehensive layer-by-layer testing)
- Integration tests for end-to-end workflows and real-world scenarios
- openCypher TCK compliance tests (~950 scenarios passing, ~25% of full TCK suite)
- Security tests for archive extraction and input validation

**Current test coverage: 93.24%**

Run the test suite:

```bash
# Install dev dependencies
uv sync --dev

# Run all tests
pytest

# Run with coverage
pytest --cov=graphforge --cov-report=html

# Run specific test categories
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m tck            # TCK compliance tests

# Run pre-push checks (format, lint, type-check, security, tests, coverage)
make pre-push
```

---

## FAQ

**Q: How does GraphForge differ from NetworkX?**
A: GraphForge adds declarative querying (openCypher), automatic persistence (SQLite), and ACID transactions. NetworkX is great for algorithms; GraphForge is great for data management.

**Q: Can I use GraphForge in production?**
A: GraphForge is designed for research and analysis, not production applications. For production workloads, use Neo4j or Memgraph.

**Q: Does GraphForge support distributed queries?**
A: No. GraphForge is embedded and single-node only.

**Q: Can I import data from Neo4j?**
A: Not directly yet. You can export from Neo4j to CSV or Cypher scripts and import via Python. GraphForge also supports GraphML format which many tools can export.

**Q: What's the maximum graph size?**
A: Practical limit is ~10M nodes. Beyond that, query performance degrades significantly.

**Q: Is GraphForge thread-safe?**
A: No. Use one GraphForge instance per thread, or use external synchronization.

---

## License

MIT © David Spencer

GraphForge is open source software released under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgments

GraphForge is built on excellent open-source projects:
- **Lark** — Fast, modern parsing library
- **Pydantic** — Data validation and settings management
- **MessagePack** — Efficient binary serialization
- **openCypher** — Declarative graph query language

Special thanks to the openCypher community for the TCK suite and language specification.

---

**Happy Graph Forging! 🔨📊**
