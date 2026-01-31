# GraphForge Cypher Guide

Reference guide for the openCypher subset supported by GraphForge v0.1.1.

## Table of Contents

- [Supported Features](#supported-features)
- [MATCH - Pattern Matching](#match---pattern-matching)
- [WHERE - Filtering](#where---filtering)
- [RETURN - Projection](#return---projection)
- [CREATE - Creating Data](#create---creating-data)
- [SET - Updating Properties](#set---updating-properties)
- [DELETE - Removing Data](#delete---removing-data)
- [MERGE - Idempotent Creation](#merge---idempotent-creation)
- [ORDER BY - Sorting](#order-by---sorting)
- [LIMIT and SKIP - Pagination](#limit-and-skip---pagination)
- [Aggregation Functions](#aggregation-functions)
- [Operators and Expressions](#operators-and-expressions)
- [Planned Features](#planned-features)

---

## Supported Features

### ✅ Fully Supported

- **MATCH** - Node and relationship patterns
- **WHERE** - Boolean predicates and filtering
- **RETURN** - Projection with aliasing
- **CREATE** - Node and relationship creation
- **SET** - Property updates
- **DELETE** - Node and relationship deletion
- **MERGE** - Idempotent node creation
- **ORDER BY** - Multi-key sorting with ASC/DESC
- **LIMIT**, **SKIP** - Pagination
- **Aggregations** - COUNT, SUM, AVG, MIN, MAX
- **Operators** - Arithmetic, comparison, boolean, NULL handling
- **Multi-label nodes** - `:Person:Employee`

### 🔄 Planned (Not Yet Supported)

- **WITH** - Query chaining and subqueries
- **OPTIONAL MATCH** - Left outer joins
- **Variable-length paths** - `[*1..3]`
- **UNWIND** - List expansion
- **UNION** - Query combination
- **CASE** - Conditional expressions
- **String functions** - substring, regex, etc.
- **List functions** - head, tail, range, etc.
- **Map projections**
- **Parameter binding** - `$param`

---

## MATCH - Pattern Matching

### Node Patterns

```cypher
-- All nodes
MATCH (n)
RETURN n

-- Nodes with label
MATCH (p:Person)
RETURN p

-- Multiple labels (AND semantics)
MATCH (e:Person:Employee)
RETURN e

-- With property filter
MATCH (p:Person {name: 'Alice'})
RETURN p
```

### Relationship Patterns

```cypher
-- Outgoing relationship
MATCH (a:Person)-[:KNOWS]->(b:Person)
RETURN a, b

-- Incoming relationship
MATCH (a:Person)<-[:KNOWS]-(b:Person)
RETURN a, b

-- Undirected relationship
MATCH (a:Person)-[:KNOWS]-(b:Person)
RETURN a, b

-- Any relationship type
MATCH (a)-[r]->(b)
RETURN a, r, b

-- Multiple relationship types
MATCH (a)-[r:KNOWS|LIKES]->(b)
RETURN a, r, b
```

### Multi-Hop Patterns

```cypher
-- Two hops
MATCH (a)-[:KNOWS]->(b)-[:KNOWS]->(c)
RETURN a, b, c

-- Anonymous intermediate nodes
MATCH (a:Person)-[:KNOWS]->(:Person)-[:KNOWS]->(c:Person)
RETURN a, c

-- Variable-length paths (NOT YET SUPPORTED)
-- MATCH (a)-[:KNOWS*1..3]->(b)
-- RETURN a, b
```

### Multiple MATCH Clauses

```cypher
-- Cartesian product
MATCH (a:Person)
MATCH (b:Person)
WHERE a.name < b.name
RETURN a.name, b.name
```

---

## WHERE - Filtering

### Comparison Operators

```cypher
-- Numeric comparisons
MATCH (p:Person)
WHERE p.age > 25
RETURN p

-- String equality
MATCH (p:Person)
WHERE p.name = 'Alice'
RETURN p

-- Multiple conditions
MATCH (p:Person)
WHERE p.age >= 25 AND p.age <= 35
RETURN p
```

### Boolean Logic

```cypher
-- AND
MATCH (p:Person)
WHERE p.age > 25 AND p.city = 'NYC'
RETURN p

-- OR
MATCH (p:Person)
WHERE p.age < 20 OR p.age > 60
RETURN p

-- NOT
MATCH (p:Person)
WHERE NOT p.active
RETURN p
```

### NULL Handling

```cypher
-- IS NULL
MATCH (p:Person)
WHERE p.email IS NULL
RETURN p

-- IS NOT NULL
MATCH (p:Person)
WHERE p.email IS NOT NULL
RETURN p

-- NULL propagation in comparisons
MATCH (p:Person)
WHERE p.age > 25  -- Excludes NULL ages
RETURN p
```

### Property Access

```cypher
-- Property comparison
MATCH (a:Person)-[r:KNOWS]->(b:Person)
WHERE a.age > b.age
RETURN a.name, b.name

-- Relationship properties
MATCH (a)-[r:KNOWS]->(b)
WHERE r.since > 2020
RETURN a, b
```

---

## RETURN - Projection

### Basic Return

```cypher
-- Return nodes
MATCH (p:Person)
RETURN p

-- Return properties
MATCH (p:Person)
RETURN p.name, p.age

-- Return relationships
MATCH (a)-[r:KNOWS]->(b)
RETURN a, r, b
```

### Aliasing

```cypher
-- Column aliases
MATCH (p:Person)
RETURN p.name AS person_name, p.age AS age

-- Required for aggregations
MATCH (p:Person)
RETURN count(*) AS total
```

### DISTINCT

```cypher
-- Unique results
MATCH (p:Person)
RETURN DISTINCT p.city
```

---

## CREATE - Creating Data

### Creating Nodes

```cypher
-- Single node
CREATE (p:Person {name: 'Alice', age: 30})

-- Multiple nodes
CREATE (a:Person {name: 'Alice'}),
       (b:Person {name: 'Bob'})

-- Multiple labels
CREATE (e:Person:Employee {name: 'Charlie', id: 'E001'})

-- No labels
CREATE ({data: 'anonymous'})
```

### Creating Relationships

```cypher
-- With existing nodes
MATCH (a:Person {name: 'Alice'})
MATCH (b:Person {name: 'Bob'})
CREATE (a)-[:KNOWS {since: 2020}]->(b)

-- Create nodes and relationship together
CREATE (a:Person {name: 'Alice'})-[:KNOWS {since: 2020}]->(b:Person {name: 'Bob'})

-- Multiple patterns
CREATE (a:Person {name: 'Alice'}),
       (b:Person {name: 'Bob'}),
       (a)-[:KNOWS]->(b)
```

### CREATE with RETURN

```cypher
-- Return created nodes
CREATE (p:Person {name: 'Alice', age: 30})
RETURN p.name AS name, p.age AS age

-- Return created relationships
CREATE (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person {name: 'Bob'})
RETURN a, r, b
```

---

## SET - Updating Properties

### Setting Properties

```cypher
-- Single property
MATCH (p:Person {name: 'Alice'})
SET p.age = 31

-- Multiple properties
MATCH (p:Person {name: 'Alice'})
SET p.age = 31, p.city = 'Boston', p.active = true

-- Relationship properties
MATCH (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person {name: 'Bob'})
SET r.strength = 'strong', r.updated = 2024
```

### SET with RETURN

```cypher
MATCH (p:Person {name: 'Alice'})
SET p.age = 31
RETURN p.name AS name, p.age AS new_age
```

---

## DELETE - Removing Data

### Deleting Nodes

```cypher
-- Delete specific node (relationships must be deleted first)
MATCH (p:Person {name: 'Alice'})
DELETE p

-- Delete multiple nodes
MATCH (p:Person)
WHERE p.age < 18
DELETE p
```

### Deleting Relationships

```cypher
-- Delete specific relationship
MATCH (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person {name: 'Bob'})
DELETE r

-- Delete all relationships of a type
MATCH ()-[r:KNOWS]->()
DELETE r
```

### Delete Nodes with Relationships

```cypher
-- Must delete relationships first
MATCH (p:Person {name: 'Alice'})-[r]-()
DELETE r, p

-- DETACH DELETE (NOT YET SUPPORTED)
-- MATCH (p:Person {name: 'Alice'})
-- DETACH DELETE p
```

---

## MERGE - Idempotent Creation

### Basic MERGE

```cypher
-- Create if doesn't exist, otherwise match
MERGE (p:Person {name: 'Alice'})

-- Multiple calls won't create duplicates
MERGE (p:Person {name: 'Alice'})
MERGE (p:Person {name: 'Alice'})
-- Only one Alice node exists
```

### MERGE with RETURN

```cypher
MERGE (p:Person {email: 'alice@example.com'})
RETURN p
```

### MERGE Use Cases

```cypher
-- ETL pipelines - safe to re-run
MERGE (p:Person {id: '12345'})
SET p.name = 'Alice', p.updated = 2024

-- Building graphs incrementally
MERGE (a:Person {name: 'Alice'})
MERGE (b:Person {name: 'Bob'})
CREATE (a)-[:KNOWS]->(b)
```

**Note:** MERGE currently only supports nodes. Relationship MERGE is planned.

---

## ORDER BY - Sorting

### Single Key

```cypher
-- Ascending (default)
MATCH (p:Person)
RETURN p.name AS name
ORDER BY p.age

-- Descending
MATCH (p:Person)
RETURN p.name AS name
ORDER BY p.age DESC

-- Explicit ascending
MATCH (p:Person)
RETURN p.name AS name
ORDER BY p.age ASC
```

### Multiple Keys

```cypher
-- Sort by city, then by age
MATCH (p:Person)
RETURN p.name AS name, p.city AS city, p.age AS age
ORDER BY p.city ASC, p.age DESC
```

### NULL Handling

```cypher
-- NULLs last in ASC (default)
MATCH (p:Person)
RETURN p.name, p.age
ORDER BY p.age ASC

-- NULLs first in DESC (default)
MATCH (p:Person)
RETURN p.name, p.age
ORDER BY p.age DESC
```

---

## LIMIT and SKIP - Pagination

### LIMIT

```cypher
-- Top 10
MATCH (p:Person)
RETURN p.name AS name
ORDER BY p.age DESC
LIMIT 10

-- Single result
MATCH (p:Person {name: 'Alice'})
RETURN p
LIMIT 1
```

### SKIP

```cypher
-- Skip first 10
MATCH (p:Person)
RETURN p.name AS name
ORDER BY p.age DESC
SKIP 10
```

### Pagination

```cypher
-- Page 1 (first 10 items)
MATCH (p:Person)
RETURN p.name AS name
ORDER BY p.name
LIMIT 10

-- Page 2 (next 10 items)
MATCH (p:Person)
RETURN p.name AS name
ORDER BY p.name
SKIP 10
LIMIT 10

-- Page 3
MATCH (p:Person)
RETURN p.name AS name
ORDER BY p.name
SKIP 20
LIMIT 10
```

---

## Aggregation Functions

### COUNT

```cypher
-- Count all rows
MATCH (p:Person)
RETURN count(*) AS total

-- Count non-NULL values
MATCH (p:Person)
RETURN count(p.age) AS with_age

-- Count DISTINCT
MATCH (p:Person)
RETURN count(DISTINCT p.city) AS cities
```

### SUM

```cypher
-- Sum numeric property
MATCH (p:Person)
RETURN sum(p.salary) AS total_salary
```

### AVG

```cypher
-- Average
MATCH (p:Person)
RETURN avg(p.age) AS average_age
```

### MIN / MAX

```cypher
-- Minimum and maximum
MATCH (p:Person)
RETURN min(p.age) AS youngest, max(p.age) AS oldest
```

### Grouping

```cypher
-- Implicit GROUP BY
MATCH (p:Person)
RETURN p.city AS city, count(*) AS population
ORDER BY population DESC

-- Multiple aggregations
MATCH (p:Person)
RETURN p.city AS city,
       count(*) AS count,
       avg(p.age) AS avg_age,
       min(p.age) AS min_age,
       max(p.age) AS max_age
```

---

## Operators and Expressions

### Arithmetic Operators

```cypher
-- Basic arithmetic
MATCH (p:Person)
RETURN p.name, p.age + 1 AS next_year_age

-- Supported: +, -, *, /, %
MATCH (p:Person)
RETURN p.salary * 1.1 AS after_raise
```

### Comparison Operators

```cypher
-- Supported: =, <>, <, <=, >, >=
MATCH (p:Person)
WHERE p.age >= 18 AND p.age < 65
RETURN p.name

-- NULL-safe comparisons
MATCH (p:Person)
WHERE p.age IS NULL OR p.age > 25
RETURN p
```

### Boolean Operators

```cypher
-- AND, OR, NOT
MATCH (p:Person)
WHERE (p.age > 25 AND p.city = 'NYC') OR (p.salary > 100000)
RETURN p.name
```

### NULL Behavior

```cypher
-- NULL propagates through operations
-- NULL = NULL → NULL (not true!)
-- NULL + 5 → NULL
-- NULL > 10 → NULL

-- Check explicitly with IS NULL / IS NOT NULL
MATCH (p:Person)
WHERE p.email IS NULL
RETURN p.name
```

### Property Access

```cypher
-- Node properties
MATCH (p:Person)
RETURN p.name, p.age

-- Relationship properties
MATCH (a)-[r:KNOWS]->(b)
RETURN r.since, r.strength
```

---

## Planned Features

The following openCypher features are on the roadmap but not yet implemented:

### WITH Clause

```cypher
-- NOT YET SUPPORTED
-- Query chaining and subqueries
MATCH (p:Person)
WITH p.name AS name, count(*) AS connections
WHERE connections > 10
RETURN name, connections
```

### OPTIONAL MATCH

```cypher
-- NOT YET SUPPORTED
-- Left outer join semantics
MATCH (person:Person)
OPTIONAL MATCH (person)-[:KNOWS]->(friend)
RETURN person.name, friend.name  -- friend.name can be NULL
```

### Variable-Length Paths

```cypher
-- NOT YET SUPPORTED
-- Graph traversal
MATCH path = (a:Person)-[:KNOWS*1..3]->(b:Person)
RETURN path
```

### UNWIND

```cypher
-- NOT YET SUPPORTED
-- List expansion
UNWIND [1, 2, 3] AS num
RETURN num
```

### UNION

```cypher
-- NOT YET SUPPORTED
-- Combine queries
MATCH (p:Person) RETURN p.name
UNION
MATCH (c:Company) RETURN c.name
```

### CASE Expressions

```cypher
-- NOT YET SUPPORTED
-- Conditional logic
MATCH (p:Person)
RETURN p.name,
       CASE
         WHEN p.age < 18 THEN 'Minor'
         WHEN p.age < 65 THEN 'Adult'
         ELSE 'Senior'
       END AS category
```

### String Functions

```cypher
-- NOT YET SUPPORTED
RETURN substring('hello', 1, 3)  -- 'ell'
RETURN toLower('HELLO')          -- 'hello'
RETURN toUpper('hello')          -- 'HELLO'
```

### List Functions

```cypher
-- NOT YET SUPPORTED
RETURN head([1,2,3])     -- 1
RETURN tail([1,2,3])     -- [2,3]
RETURN range(1, 10, 2)   -- [1,3,5,7,9]
```

### Parameter Binding

```cypher
-- NOT YET SUPPORTED
-- Secure parameterization
MATCH (p:Person {name: $name})
RETURN p
```

---

## Best Practices

### 1. Use Labels for Performance

```cypher
-- Fast (uses label index)
MATCH (p:Person)
WHERE p.name = 'Alice'
RETURN p

-- Slow (scans all nodes)
MATCH (n)
WHERE n.name = 'Alice'
RETURN n
```

### 2. Order Before Limit

```cypher
-- Always combine ORDER BY with LIMIT
MATCH (p:Person)
RETURN p.name
ORDER BY p.age DESC
LIMIT 10
```

### 3. Use MERGE for Idempotent Operations

```cypher
-- Safe to run multiple times
MERGE (p:Person {email: 'alice@example.com'})

-- Creates duplicates
CREATE (p:Person {email: 'alice@example.com'})
```

### 4. Delete Relationships Before Nodes

```cypher
-- Required order
MATCH (p:Person {name: 'Alice'})-[r]-()
DELETE r  -- First delete relationships
DELETE p  -- Then delete node
```

---

## Examples

### Friend Recommendations

```cypher
-- Find friends of friends who aren't already friends
MATCH (me:Person {name: 'Alice'})-[:KNOWS]->(friend)-[:KNOWS]->(foaf)
WHERE NOT (me)-[:KNOWS]->(foaf) AND me <> foaf
RETURN DISTINCT foaf.name AS recommendation
```

### Most Connected People

```cypher
-- Find people with most connections
MATCH (p:Person)-[:KNOWS]->(friend)
RETURN p.name AS person, count(friend) AS connections
ORDER BY connections DESC
LIMIT 10
```

### Data Quality Check

```cypher
-- Find nodes missing required properties
MATCH (p:Person)
WHERE p.email IS NULL
RETURN p.name AS person
```

---

## See Also

- [Tutorial](tutorial.md) - Step-by-step guide
- [API Reference](api-reference.md) - Python API documentation
- [Examples](../examples/) - Real-world use cases
- [TCK Compliance](tck-compliance.md) - openCypher conformance status

---

**Questions or Feedback?**

Report issues on [GitHub](https://github.com/DecisionNerd/graphforge/issues).
