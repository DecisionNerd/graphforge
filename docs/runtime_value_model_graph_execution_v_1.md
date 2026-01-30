# Runtime Value Model — Graph Execution (v1)

---

## 1. Purpose

This document defines the **runtime value model** used during query execution in the openCypher-compatible graph workbench.

The runtime value model specifies:
- How nodes and relationships are represented at execution time
- How rows are structured and propagated through the execution pipeline
- How values interact with Cypher expressions, schemas, and adapters (e.g. NetworkX)

This model is intentionally **explicit, minimal, and stable**, serving as the contract between:
- Logical planning
- Execution
- Schema / ontology layers
- Downstream adapters

---

## 2. Design Goals

The runtime value model MUST:

- Preserve openCypher semantics
- Be independent of storage implementation details
- Support schema / ontology annotations
- Be efficient for adjacency-based traversal
- Be inspectable and debuggable in Python
- Map cleanly to external graph libraries

The model MUST NOT:
- Encode planner logic
- Encode query semantics
- Leak storage internals (e.g. page IDs, offsets)

---

## 3. Core Runtime Types

### 3.1 NodeRef

`NodeRef` represents a **runtime reference to a node**.

#### Required Fields
- `id: int | str`  
  Stable internal node identifier
- `labels: frozenset[str]`  
  Set of node labels
- `properties: Mapping[str, Value]`  
  Node properties (lazy or eager)

#### Optional Fields
- `schema: NodeSchema | None`  
  Associated schema / ontology model (if any)
- `provenance: Any | None`  
  Optional provenance metadata

#### Semantics
- `NodeRef` identity is defined by `id`
- Two `NodeRef`s with the same `id` MUST be treated as the same node
- `NodeRef` MUST be hashable and comparable by `id`

---

### 3.2 EdgeRef

`EdgeRef` represents a **runtime reference to a relationship**.

#### Required Fields
- `id: int | str`  
  Stable internal relationship identifier
- `type: str`  
  Relationship type
- `src: NodeRef`  
  Source node
- `dst: NodeRef`  
  Destination node
- `properties: Mapping[str, Value]`

#### Optional Fields
- `schema: RelationshipSchema | None`
- `provenance: Any | None`

#### Semantics
- `EdgeRef` identity is defined by `id`
- Directionality is intrinsic (`src → dst`)
- For undirected expansion, the same `EdgeRef` may be traversed in either direction

---

## 4. Scalar Value Model

### 4.1 Value Type

A `Value` is any of the following:

- `int`
- `float`
- `bool`
- `str`
- `None`
- `list[Value]`
- `dict[str, Value]`
- `NodeRef`
- `EdgeRef`

This aligns with openCypher value semantics.

---

### 4.2 Null Semantics

- `None` represents Cypher `null`
- Any expression involving `null` MUST follow openCypher three-valued logic
- Comparisons involving `null` evaluate to `null`, not `false`

---

## 5. Row Model

### 5.1 Row Definition

A **Row** is an immutable mapping:

```
Row := Mapping[str, Value]
```

Where:
- Keys are variable names bound during execution
- Values are runtime `Value`s

Example:
```
{ "a": NodeRef(...), "b": NodeRef(...) }
```

---

### 5.2 Row Semantics

- Rows are **logically immutable**
- Operators produce new rows rather than mutating existing ones
- Variable shadowing is not allowed in v1

---

## 6. Interaction with Execution Operators

### 6.1 NodeScan

- Emits rows of the form:
```
{ var_name: NodeRef }
```

### 6.2 Expand

- Consumes rows containing a bound `NodeRef`
- Emits rows with additional bindings:
```
{ ..., from_var: NodeRef, to_var: NodeRef [, rel_var: EdgeRef] }
```

### 6.3 Filter

- Evaluates predicates against row values
- Retains rows where predicate evaluates to `TRUE`
- Drops rows where predicate evaluates to `FALSE` or `NULL`

### 6.4 Project

- Transforms rows into projected output rows
- Output values may be scalars or property accesses

### 6.5 Distinct

- Applies set semantics over projected rows
- Equality is defined over runtime values

---

## 7. Property Access Semantics

- Property access (`n.age`) on `NodeRef` or `EdgeRef`:
  - Returns the property value if present
  - Returns `None` if missing
- Missing properties are indistinguishable from explicit `null` per openCypher

---

## 8. Schema & Ontology Interaction

- Runtime values MAY carry optional schema references
- Schemas MUST NOT alter runtime semantics
- Schemas MAY be used to:
  - Validate properties
  - Annotate values
  - Assist adapters (e.g. export)

Schema presence MUST be transparent to execution operators.

---

## 9. NetworkX Interoperability

### 9.1 Node Mapping

- `NodeRef.id` → NetworkX node key
- `labels` → node attributes
- `properties` → node attributes

### 9.2 Edge Mapping

- `EdgeRef.id` → edge key (if multigraph)
- `type` → edge attribute
- `properties` → edge attributes

The runtime model is designed to allow **lossless export** to NetworkX graphs.

---

## 10. Invariants & Guarantees

The runtime value model guarantees:

- Stable identity for nodes and relationships
- Deterministic equality and hashing
- Correct Cypher null semantics
- Clear separation from storage internals

---

## 11. Non-Goals

The runtime value model does NOT:
- Encode traversal history or paths
- Support path values in v1
- Perform lazy evaluation of expressions

---

## 12. Summary

The runtime value model provides a **clean, minimal execution contract** that:
- Supports openCypher semantics
- Integrates naturally with Pydantic schemas
- Enables analytical graph workflows
- Remains adaptable for future extensions

It is the foundation upon which execution correctness, interoperability, and extensibility depend.

