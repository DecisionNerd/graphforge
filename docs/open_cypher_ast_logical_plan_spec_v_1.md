# openCypher AST & Logical Plan Spec

## v1 (TCK-Aligned Subset)

---

## 1. Scope

This spec defines:
- The **internal AST** representation for a declared openCypher subset
- The **semantic lowering** rules from AST → **Logical Plan**
- The **Logical Plan operator set** used by the execution engine

This is **not** a full openCypher spec. It targets the v1 supported surface area:
- `MATCH`
- `WHERE`
- `RETURN`
- `SKIP`
- `LIMIT`

Unsupported constructs MUST be rejected during validation.

---

## 2. Guiding Invariants

1. **Semantics first**: If a feature is supported, its semantics MUST match openCypher expectations.
2. **Planner purity**: The planner MUST NOT depend on storage implementation details.
3. **Deterministic lowering**: The AST → Plan transform MUST be deterministic.
4. **Minimal operator set**: Prefer a small, orthogonal set of operators.
5. **Schema orthogonality**: Pydantic/JSON Schema models MUST NOT affect query semantics.

---

## 3. AST Model (Internal)

### 3.1 Top-Level

#### `CypherQuery`
- `clauses: list[Clause]`

#### `Clause` (sum type)
- `MatchClause`
- `WhereClause`
- `ReturnClause`
- `SkipClause`
- `LimitClause`

> Note: Although openCypher allows flexible clause ordering and `WITH` pipelines, v1 enforces a simplified, valid subset ordering:
> `MATCH` → optional `WHERE` → `RETURN` → optional `SKIP` / `LIMIT`.

---

### 3.2 MATCH

#### `MatchClause`
- `patterns: list[Pattern]`

#### `Pattern`
- `parts: list[PatternPart]`

#### `PatternPart`
- `NodePattern` | `RelationshipPattern`

#### `NodePattern`
- `var: VarName | None`  (e.g., `n` in `(n:Person)`)
- `labels: set[str]`  (e.g., `Person`)
- `properties: dict[str, Expr] | None`

**Property Map Semantics (v1)**
- Property maps in node patterns (e.g. `(n:Person {age: 30})`) ARE SUPPORTED
- Property keys MUST be static identifiers
- Property values MUST be expressions evaluable at match time
- Property maps are semantic sugar for conjunctions of equality predicates

#### `RelationshipPattern`
- `var: VarName | None`
- `types: set[str]`
- `direction: Direction`
- `properties: dict[str, Expr] | None`

**Property Map Semantics (v1)**
- Property maps in relationship patterns ARE SUPPORTED
- Semantics mirror node property maps

#### `Direction`
- `OUT` (e.g. `-[:R]->`)
- `IN` (e.g. `<-[:R]-`)
- `UNDIRECTED` (e.g. `-[:R]-`)

**Explicit v1 Constraints**
- Variable-length relationships (`*`) are NOT supported
- Path variables (e.g. `p = (a)-[:R]->(b)`) are NOT supported

---

### 3.3 WHERE

#### `WhereClause`
- `predicate: Expr`

---

### 3.4 RETURN

#### `ReturnClause`
- `items: list[ReturnItem]`
- `distinct: bool`

**DISTINCT Semantics (v1)**
- `RETURN DISTINCT` IS SUPPORTED
- DISTINCT applies to the full projected row
- DISTINCT is implemented as a logical operator after projection

#### `ReturnItem`
- `expr: Expr`
- `alias: str | None`

---

### 3.5 Expressions

Expressions are a typed tree.

#### `Expr` (sum type)
- `Literal`
- `VarRef`
- `PropertyAccess`
- `BinaryOp`
- `UnaryOp`
- `FunctionCall` (optional; initially very limited)

#### `Literal`
- `value: int | float | bool | str | None | list | dict`

#### `VarRef`
- `name: str`

#### `PropertyAccess`
- `base: Expr` (typically `VarRef`)
- `key: str` (e.g., `n.age`)

#### `BinaryOp`
- `op: str` one of: `= != < <= > >= AND OR`
- `left: Expr`
- `right: Expr`

#### `UnaryOp`
- `op: str` one of: `NOT`
- `expr: Expr`

#### `FunctionCall` (v1 minimal)
- `name: str`
- `args: list[Expr]`

**Explicit v1 constraint**
- No aggregations
- No list comprehensions
- No pattern expressions in WHERE

---

## 4. Validation Rules (AST-Level)

Validation MUST reject queries that:
- Use unsupported clauses (`WITH`, `OPTIONAL MATCH`, `MERGE`, etc.)
- Use variable-length relationships (`*`)
- Use write clauses (`CREATE`, `SET`, `DELETE`)
- Use aggregations
- Use features not covered by the declared subset

Validation MUST also ensure:
- Variables referenced in WHERE/RETURN are introduced in MATCH (per v1 scope rules)
- Relationship directionality and types are well-formed

---

## 5. Logical Plan Model

The logical plan is a small operator graph (pipeline) that the execution engine can run.

### 5.1 Core Operator Set (v1)

#### `NodeScan`
- Inputs: none
- Outputs: rows with bound variable for node (e.g., `{a: Node}`)
- Params:
  - `var: str`
  - `labels: set[str] | None`

#### `Expand`
- Inputs: rows with bound node var (e.g., `{a: Node}`)
- Outputs: rows with added bindings (e.g., `{a: Node, b: Node}`)
- Params:
  - `from_var: str`
  - `rel_var: str | None`
  - `to_var: str`
  - `types: set[str] | None`
  - `direction: Direction`

**UNDIRECTED Expansion Semantics (v1)**
- For `UNDIRECTED`, expansion MUST consider both outgoing and incoming edges
- The same relationship MUST NOT be returned twice for a single expansion

#### `Filter`
- Inputs: rows
- Outputs: rows where predicate evaluates to TRUE
- Params:
  - `predicate: CompiledExpr`

#### `Project`
- Inputs: rows
- Outputs: projected rows
- Params:
  - `items: list[ProjectedItem]`

#### `Distinct`
- Inputs: projected rows
- Outputs: rows with duplicate projections removed
- Params: none

#### `Skip`
- Inputs: rows
- Outputs: rows after skipping N
- Params:
  - `count: int`

#### `Limit`
- Inputs: rows
- Outputs: first N rows
- Params:
  - `count: int`

---

## 6. Lowering Rules: AST → Logical Plan

Given a supported query of the form:

```
MATCH <pattern>
[WHERE <predicate>]
RETURN <items>
[SKIP n]
[LIMIT m]
```

Lowering MUST produce a plan in the following shape:

1. Choose an anchoring `NodeScan` for the first node variable in the first pattern (v1 heuristic)
2. Apply `Expand` steps following relationship direction for each hop in the pattern
3. Apply label constraints as early as possible:
   - Prefer pushing node label checks into `NodeScan` when the node is the scan anchor
   - Otherwise apply a `Filter` immediately after the binding is introduced
4. Compile `WHERE` into a `Filter` (if present)
5. Compile `RETURN` into `Project`
6. Apply `SKIP` then `LIMIT` if present

### 6.1 Example Lowering

Cypher:
```cypher
MATCH (a:Person)-[:KNOWS]->(b:Person)
WHERE a.age > 30 AND b.city = "Lehi"
RETURN b.name AS name
LIMIT 10
```

Plan:
- `NodeScan(var="a", labels={"Person"})`
- `Expand(from_var="a", to_var="b", types={"KNOWS"}, direction=OUT)`
- `Filter(predicate = (label(b) == "Person"))` *(if labels not enforced elsewhere)*
- `Filter(predicate = (a.age > 30 AND b.city = "Lehi"))`
- `Project(items=[b.name AS name])`
- `Limit(10)`

---

## 7. Expression Compilation

Expressions in WHERE and RETURN MUST be compiled into an evaluable form (`CompiledExpr`) that:
- Correctly implements openCypher null semantics (3-valued logic)
- Supports property access on node/relationship refs
- Avoids Python `eval`

A simple approach is an expression VM or a compiled callable tree.

---

## 8. Extension Points

### 8.1 DISTINCT
- If supported, implement as a `Distinct` operator after `Project`.
- If unsupported in v1, reject during validation.

### 8.2 Multiple MATCH Patterns
- v1 may initially support single linear patterns.
- Future: introduce `Join` / `CartesianProduct` operators.

### 8.3 Optional MATCH
- Future: introduce `LeftJoin` semantics.

---

## 9. Deliverables for Implementation Phase

1. AST dataclasses / Pydantic models for internal representation
2. Parser adapter: openCypher parse tree → AST
3. Validator for v1 subset
4. Lowering: AST → Logical Plan
5. Expression compiler with null semantics
6. Golden tests + initial TCK subset wiring

