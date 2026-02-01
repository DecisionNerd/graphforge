<h1 align="center">GraphForge</h1>

<p align="center">
  <a href="https://pypi.org/project/graphforge/"><img src="https://img.shields.io/pypi/v/graphforge.svg?label=PyPI&logo=pypi" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/graphforge/"><img src="https://img.shields.io/pypi/pyversions/graphforge.svg?logo=python&logoColor=white" alt="Python versions" /></a>
  <a href="https://github.com/DecisionNerd/graphforge/actions"><img src="https://github.com/DecisionNerd/graphforge/workflows/Test%20Suite/badge.svg" alt="Build status" /></a>
  <a href="https://codecov.io/gh/DecisionNerd/graphforge"><img src="https://codecov.io/gh/DecisionNerd/graphforge/branch/main/graph/badge.svg" alt="Coverage" /></a>
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

**Dependencies:** `pydantic>=2.6`, `lark>=1.1`, `msgpack>=1.0`

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
- `**properties`: Property key-value pairs (str, int, float, bool, None, list, dict)

**Returns:** `NodeRef` for the created node

**Example:**
```python
alice = db.create_node(
    ['Person', 'Employee'],
    name='Alice',
    age=30,
    active=True,
    skills=['Python', 'SQL'],
    metadata={'department': 'Engineering'}
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

**Completed (v0.1):**
- ✅ MATCH, WHERE, RETURN, ORDER BY, LIMIT, SKIP
- ✅ Aggregations (COUNT, SUM, AVG, MIN, MAX)
- ✅ CREATE, SET, DELETE, MERGE clauses
- ✅ Python builder API
- ✅ SQLite persistence
- ✅ ACID transactions

**Planned (v0.2):**
- MATCH-CREATE combinations (connecting existing nodes)
- DETACH DELETE (cascading relationship deletion)
- Path expressions and variable-length patterns
- UNWIND for list processing
- CASE expressions

**Future Considerations:**
- Query plan visualization
- Performance profiling tools
- Import/export to standard formats (GraphML, CSV)
- Integration with popular data science libraries
- Pydantic schema validation

---

## Contributing

GraphForge is in active development. Contributions are welcome!

**Areas for Contribution:**
- Additional Cypher features
- Performance optimizations
- Documentation and examples
- Bug reports and fixes
- Integration with data science tools

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Documentation

- **[Quick Start Tutorial](docs/tutorial.md)** — Step-by-step guide for new users
- **[API Reference](docs/api-reference.md)** — Complete Python API documentation
- **[Cypher Language Guide](docs/cypher-guide.md)** — openCypher subset reference
- **[Architecture Overview](docs/architecture-overview.md)** — System design and internals
- **[Requirements Document](docs/0-requirements.md)** — Full scope and design rationale

---

## Testing

GraphForge has **368 tests** covering:
- Unit tests for parser, planner, executor, storage
- Integration tests for end-to-end workflows
- openCypher TCK compliance tests (17 passing)

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
A: Not directly yet. You can export from Neo4j to CSV and import via Python scripts.

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
