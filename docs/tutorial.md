# GraphForge Tutorial

**A step-by-step guide to building, querying, and analyzing graphs with GraphForge.**

---

## Table of Contents

1. [Installation](#installation)
2. [Your First Graph](#your-first-graph)
3. [Querying with Cypher](#querying-with-cypher)
4. [Working with Persistence](#working-with-persistence)
5. [Using Transactions](#using-transactions)
6. [Advanced Queries](#advanced-queries)
7. [Real-World Example: Citation Network](#real-world-example-citation-network)
8. [Best Practices](#best-practices)
9. [Next Steps](#next-steps)

---

## Installation

Install GraphForge using uv (recommended) or pip:

```bash
# Using uv
uv add graphforge

# Using pip
pip install graphforge
```

Verify the installation:

```python
from graphforge import GraphForge
print("GraphForge installed successfully!")
```

---

## Your First Graph

Let's build a simple social network.

### Step 1: Create an In-Memory Graph

```python
from graphforge import GraphForge

# Create an in-memory graph (data is not persisted)
db = GraphForge()
```

### Step 2: Add Nodes

Nodes represent entities in your graph. Use the Python API to create nodes:

```python
# Create people with labels and properties
alice = db.create_node(
    labels=['Person'],           # Node labels
    name='Alice',                # Properties
    age=30,
    city='NYC'
)

bob = db.create_node(
    labels=['Person'],
    name='Bob',
    age=25,
    city='NYC'
)

charlie = db.create_node(
    labels=['Person'],
    name='Charlie',
    age=35,
    city='LA'
)

print(f"Created node with ID: {alice.id}")  # Auto-generated ID
```

### Step 3: Add Relationships

Relationships connect nodes:

```python
# Create directed relationships
knows_bob = db.create_relationship(
    src=alice,
    dst=bob,
    rel_type='KNOWS',
    since=2015,                  # Relationship properties
    strength='strong'
)

knows_charlie = db.create_relationship(
    src=alice,
    dst=charlie,
    rel_type='KNOWS',
    since=2018,
    strength='medium'
)

print(f"Created relationship with ID: {knows_bob.id}")
```

### Step 4: Query the Graph

Use Cypher queries to explore your graph:

```python
# Find all people Alice knows
results = db.execute("""
    MATCH (a:Person)-[r:KNOWS]->(friend:Person)
    WHERE a.name = 'Alice'
    RETURN friend.name AS name, r.since AS since
    ORDER BY r.since
""")

print("Alice knows:")
for row in results:
    name = row['name'].value      # Access .value to get Python types
    since = row['since'].value
    print(f"  - {name} (since {since})")
```

**Output:**
```
Alice knows:
  - Bob (since 2015)
  - Charlie (since 2018)
```

---

## Querying with Cypher

GraphForge supports a subset of openCypher for declarative graph queries.

### Basic Pattern Matching

```python
# Match all nodes
results = db.execute("MATCH (n) RETURN n")
print(f"Total nodes: {len(results)}")

# Match nodes by label
results = db.execute("""
    MATCH (p:Person)
    RETURN p.name AS name, p.age AS age
""")

for row in results:
    print(f"{row['name'].value} is {row['age'].value} years old")
```

### Filtering with WHERE

```python
# Find people over 25
results = db.execute("""
    MATCH (p:Person)
    WHERE p.age > 25
    RETURN p.name AS name
""")

# Multiple conditions
results = db.execute("""
    MATCH (p:Person)
    WHERE p.age > 25 AND p.city = 'NYC'
    RETURN p.name AS name
""")
```

### Traversing Relationships

```python
# Find who knows whom
results = db.execute("""
    MATCH (a:Person)-[r:KNOWS]->(b:Person)
    RETURN a.name AS from, b.name AS to, r.since AS since
""")

# Two-hop traversal
results = db.execute("""
    MATCH (a:Person)-[:KNOWS]->(:Person)-[:KNOWS]->(c:Person)
    WHERE a.name = 'Alice'
    RETURN c.name AS friend_of_friend
""")
```

### Aggregations

```python
# Count nodes
results = db.execute("""
    MATCH (p:Person)
    RETURN count(*) AS total
""")
print(f"Total people: {results[0]['total'].value}")

# Group and aggregate
results = db.execute("""
    MATCH (p:Person)
    RETURN p.city AS city, count(*) AS population
    ORDER BY population DESC
""")

for row in results:
    print(f"{row['city'].value}: {row['population'].value} people")

# Multiple aggregations
results = db.execute("""
    MATCH (p:Person)
    RETURN
        count(*) AS total,
        avg(p.age) AS avg_age,
        min(p.age) AS youngest,
        max(p.age) AS oldest
""")

row = results[0]
print(f"Total: {row['total'].value}")
print(f"Average age: {row['avg_age'].value:.1f}")
print(f"Age range: {row['youngest'].value}-{row['oldest'].value}")
```

---

## Working with Persistence

So far, we've used in-memory graphs that disappear when the program exits. Let's persist data to disk.

### Creating a Persistent Graph

```python
from pathlib import Path

# Specify a file path for SQLite storage
db = GraphForge("my-research-graph.db")

# Add data (works the same as in-memory)
db.execute("CREATE (p:Person {name: 'Alice', age: 30})")
db.execute("CREATE (p:Person {name: 'Bob', age: 25})")

# Save to disk
db.close()
```

### Loading an Existing Graph

```python
# Later, in a new session...
db = GraphForge("my-research-graph.db")

# Data is still there!
results = db.execute("MATCH (p:Person) RETURN p.name AS name")
for row in results:
    print(f"Found: {row['name'].value}")

db.close()
```

### Incremental Updates

```python
# Session 1: Initial data
db = GraphForge("knowledge-base.db")
db.execute("CREATE (:Concept {name: 'Graph Databases'})")
db.close()

# Session 2: Add more data
db = GraphForge("knowledge-base.db")
db.execute("CREATE (:Concept {name: 'SQL Databases'})")
db.execute("""
    MATCH (gdb:Concept {name: 'Graph Databases'})
    MATCH (sql:Concept {name: 'SQL Databases'})
    CREATE (gdb)-[:DIFFERENT_FROM]->(sql)
""")
db.close()

# Session 3: Query accumulated data
db = GraphForge("knowledge-base.db")
results = db.execute("MATCH (c:Concept) RETURN count(*) AS count")
print(f"Total concepts: {results[0]['count'].value}")  # 2
db.close()
```

---

## Using Transactions

Transactions provide ACID guarantees—atomicity, consistency, isolation, and durability.

### Basic Transaction

```python
db = GraphForge("my-graph.db")

# Begin a transaction
db.begin()

# Make changes
db.execute("CREATE (p:Person {name: 'Diana', age: 28})")
db.execute("CREATE (p:Person {name: 'Eve', age: 32})")

# Commit to save changes
db.commit()

db.close()
```

### Rollback on Error

```python
db = GraphForge("my-graph.db")

try:
    db.begin()

    db.execute("CREATE (p:Person {name: 'Frank', age: 40})")

    # Some operation that might fail
    if some_validation_fails:
        raise ValueError("Validation failed!")

    db.commit()
except Exception as e:
    print(f"Error: {e}")
    db.rollback()  # Discard all changes since begin()
finally:
    db.close()
```

### Atomic Multi-Step Operations

```python
db = GraphForge("production-db.db")

try:
    db.begin()

    # Multi-step operation that must succeed or fail atomically
    db.execute("MATCH (p:Person {id: 123}) SET p.status = 'inactive'")
    db.execute("MATCH (p:Person {id: 123})-[r:WORKS_AT]->() DELETE r")
    db.execute("CREATE (:AuditLog {action: 'deactivate', user_id: 123})")

    db.commit()
    print("User deactivated successfully")
except Exception as e:
    db.rollback()
    print(f"Deactivation failed: {e}")
finally:
    db.close()
```

---

## Advanced Queries

### CREATE: Building Graphs with Cypher

You can use Cypher CREATE instead of the Python API:

```python
# Create nodes
db.execute("CREATE (p:Person {name: 'Alice', age: 30})")

# Create nodes with relationships in one statement
db.execute("""
    CREATE (a:Person {name: 'Alice'})-[:KNOWS {since: 2020}]->(b:Person {name: 'Bob'})
""")

# Create with RETURN
results = db.execute("""
    CREATE (p:Person {name: 'Charlie', age: 35})
    RETURN p.name AS name, p.age AS age
""")
print(f"Created: {results[0]['name'].value}")
```

### SET: Updating Properties

```python
# Update single property
db.execute("""
    MATCH (p:Person {name: 'Alice'})
    SET p.age = 31
""")

# Update multiple properties
db.execute("""
    MATCH (p:Person {name: 'Alice'})
    SET p.age = 31, p.city = 'Boston', p.active = true
""")

# Update relationship properties
db.execute("""
    MATCH (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person {name: 'Bob'})
    SET r.strength = 'strong'
""")
```

### DELETE: Removing Data

```python
# Delete a node (and its relationships automatically)
db.execute("""
    MATCH (p:Person {name: 'Charlie'})
    DELETE p
""")

# Delete only a relationship
db.execute("""
    MATCH (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person {name: 'Bob'})
    DELETE r
""")

# Delete multiple elements
db.execute("""
    MATCH (p:Person)
    WHERE p.age < 25
    DELETE p
""")
```

### MERGE: Idempotent Creation

MERGE creates nodes if they don't exist, or matches them if they do:

```python
# Safe to run multiple times
db.execute("MERGE (p:Person {name: 'Alice'})")
db.execute("MERGE (p:Person {name: 'Alice'})")  # Matches existing node

# Check result
results = db.execute("MATCH (p:Person {name: 'Alice'}) RETURN count(*) AS count")
print(results[0]['count'].value)  # 1, not 2!

# Useful for ETL pipelines
db.execute("MERGE (p:Person {name: 'Bob', email: 'bob@example.com'})")
```

---

## Real-World Example: Citation Network

Let's build a realistic citation network graph.

### Setup

```python
from graphforge import GraphForge

db = GraphForge("citation-network.db")
```

### Load Papers

```python
papers = [
    {"id": "P1", "title": "Graph Neural Networks", "year": 2021, "citations": 150},
    {"id": "P2", "title": "Deep Learning Fundamentals", "year": 2019, "citations": 500},
    {"id": "P3", "title": "GNN Applications in NLP", "year": 2022, "citations": 80},
    {"id": "P4", "title": "Attention Is All You Need", "year": 2017, "citations": 2000},
]

for paper in papers:
    db.execute(f"""
        CREATE (:Paper {{
            id: '{paper['id']}',
            title: '{paper['title']}',
            year: {paper['year']},
            citations: {paper['citations']}
        }})
    """)

print(f"Loaded {len(papers)} papers")
```

### Add Authors

```python
authors = [
    {"name": "Alice Smith", "affiliation": "MIT"},
    {"name": "Bob Jones", "affiliation": "Stanford"},
    {"name": "Charlie Brown", "affiliation": "MIT"},
]

for author in authors:
    db.execute(f"""
        MERGE (a:Author {{name: '{author['name']}'}})
        SET a.affiliation = '{author['affiliation']}'
    """)
```

### Link Authors to Papers

```python
authorships = [
    ("Alice Smith", "P1"),
    ("Alice Smith", "P3"),
    ("Bob Jones", "P2"),
    ("Charlie Brown", "P1"),
    ("Charlie Brown", "P4"),
]

for author_name, paper_id in authorships:
    db.execute(f"""
        MATCH (a:Author {{name: '{author_name}'}})
        MATCH (p:Paper {{id: '{paper_id}'}})
        CREATE (a)-[:AUTHORED]->(p)
    """)
```

### Add Citation Links

```python
citations = [
    ("P1", "P2"),  # P1 cites P2
    ("P1", "P4"),  # P1 cites P4
    ("P3", "P1"),  # P3 cites P1
    ("P3", "P2"),  # P3 cites P2
]

for citing_id, cited_id in citations:
    db.execute(f"""
        MATCH (citing:Paper {{id: '{citing_id}'}})
        MATCH (cited:Paper {{id: '{cited_id}'}})
        CREATE (citing)-[:CITES]->(cited)
    """)
```

### Analysis 1: Most Prolific Authors

```python
results = db.execute("""
    MATCH (a:Author)-[:AUTHORED]->(p:Paper)
    RETURN a.name AS author, count(p) AS paper_count
    ORDER BY paper_count DESC
""")

print("Most prolific authors:")
for row in results:
    print(f"  {row['author'].value}: {row['paper_count'].value} papers")
```

**Output:**
```
Most prolific authors:
  Alice Smith: 2 papers
  Charlie Brown: 2 papers
  Bob Jones: 1 papers
```

### Analysis 2: Most Cited Papers

```python
results = db.execute("""
    MATCH (p:Paper)<-[:CITES]-(citing:Paper)
    RETURN p.title AS paper, count(citing) AS citation_count
    ORDER BY citation_count DESC
""")

print("\nMost cited papers (in-network):")
for row in results:
    print(f"  {row['paper'].value}: {row['citation_count'].value} citations")
```

### Analysis 3: Collaboration Network

```python
results = db.execute("""
    MATCH (a1:Author)-[:AUTHORED]->(p:Paper)<-[:AUTHORED]-(a2:Author)
    WHERE a1.name < a2.name
    RETURN a1.name AS author1, a2.name AS author2, count(p) AS papers
    ORDER BY papers DESC
""")

print("\nAuthor collaborations:")
for row in results:
    print(f"  {row['author1'].value} & {row['author2'].value}: {row['papers'].value} papers")
```

### Analysis 4: Papers by MIT Authors

```python
results = db.execute("""
    MATCH (a:Author)-[:AUTHORED]->(p:Paper)
    WHERE a.affiliation = 'MIT'
    RETURN p.title AS paper, a.name AS author
""")

print("\nMIT papers:")
for row in results:
    print(f"  {row['paper'].value} by {row['author'].value}")
```

### Cleanup

```python
db.close()
```

---

## Best Practices

### 1. Choose Storage Mode Appropriately

**Use in-memory graphs for:**
- Quick exploration and prototyping
- Throwaway analyses
- Testing

**Use persistent graphs for:**
- Long-running analyses
- Incremental graph construction
- Shared datasets
- Production workflows

```python
# Exploration
db = GraphForge()

# Production
db = GraphForge("production-graph.db")
```

### 2. Always Close Persistent Graphs

```python
# Good: Using try-finally
db = GraphForge("my-graph.db")
try:
    # ... work with graph ...
    pass
finally:
    db.close()

# Better: Using context manager (if implemented)
# with GraphForge("my-graph.db") as db:
#     ... work with graph ...
```

### 3. Use Transactions for Multi-Step Operations

```python
# Atomic updates
db.begin()
try:
    db.execute("CREATE (p:Person {name: 'Alice'})")
    db.execute("CREATE (p:Person {name: 'Bob'})")
    db.execute("""
        MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
        CREATE (a)-[:KNOWS]->(b)
    """)
    db.commit()
except Exception as e:
    db.rollback()
    raise
```

### 4. Use MERGE for Idempotent Operations

```python
# Safe to run multiple times
db.execute("MERGE (p:Person {email: 'alice@example.com'})")
db.execute("MERGE (p:Person {email: 'alice@example.com'})")  # No duplicates

# Avoid this pattern
db.execute("CREATE (p:Person {email: 'alice@example.com'})")
db.execute("CREATE (p:Person {email: 'alice@example.com'})")  # Creates duplicate!
```

### 5. Remember to Access `.value` on Results

```python
results = db.execute("MATCH (p:Person) RETURN p.name AS name, p.age AS age")

for row in results:
    # Correct
    name = row['name'].value
    age = row['age'].value

    # Incorrect (returns CypherValue object)
    # name = row['name']
```

### 6. Use WHERE for Complex Filtering

```python
# Prefer this
db.execute("""
    MATCH (p:Person)
    WHERE p.age > 25 AND p.city = 'NYC'
    RETURN p
""")

# Over this (inline property matching is limited)
db.execute("""
    MATCH (p:Person {city: 'NYC'})
    WHERE p.age > 25
    RETURN p
""")
```

### 7. Order Results Before Using LIMIT

```python
# Always order when using LIMIT
db.execute("""
    MATCH (p:Person)
    RETURN p.name AS name, p.age AS age
    ORDER BY p.age DESC
    LIMIT 10
""")

# Without ORDER BY, results are non-deterministic
```

---

## Next Steps

Congratulations! You've learned the fundamentals of GraphForge.

### Learn More

- **[API Reference](api-reference.md)** — Complete Python API documentation
- **[Cypher Guide](cypher-guide.md)** — Full openCypher subset reference
- **[Architecture Overview](architecture-overview.md)** — System design and internals
- **[README](../README.md)** — Full feature list and examples

### Try These Exercises

1. **Social Network**: Build a graph of friends and their relationships. Find mutual friends.

2. **Knowledge Graph**: Extract entities from a document and link them with relationships.

3. **Time Series**: Model temporal data as a graph and query time-based patterns.

4. **Recommendation System**: Build a user-item graph and find similar users or items.

5. **Data Lineage**: Track transformations in a data pipeline and query dependencies.

### Join the Community

- Report issues on [GitHub](https://github.com/DecisionNerd/graphforge/issues)
- Read the [Requirements Document](0-requirements.md) for design rationale
- Explore example notebooks (coming soon!)

---

**Happy Graph Forging! 🔨📊**
