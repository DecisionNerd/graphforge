# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GraphForge is an embedded, openCypher-compatible graph database for Python, designed for research and analysis workflows. It prioritizes **correctness over performance** and provides declarative querying with automatic persistence via SQLite.

**Not a production database** - optimized for interactive analysis on small-to-medium graphs (< 10M nodes).

**Core Use Cases:**
- **AI Agent Grounding**: Ground LLM agents in ontologies with tool definitions for semantic, deterministic action (see `docs/use-cases/agent-grounding.md`)
- **Knowledge Graph Construction**: Extract and refine entities/relationships from unstructured data
- **Network Analysis**: Analyze social networks, dependencies, citation graphs in notebooks
- **LLM-Powered Workflows**: Store and query structured outputs from language models

## Development Workflow (CRITICAL)

**Every piece of work MUST follow this workflow. No exceptions.**

### 1. Create an Issue First

```bash
gh issue create --title "feat: add UNWIND clause support" \
  --body "Description..." --label "enhancement"
```

Never start work without an issue. If you discover out-of-scope work, create a NEW issue and continue with current work.

### 2. Create Branch with Issue Number

**Format:** `<type>/<issue-number>-<short-description>`

```bash
git checkout -b feature/42-unwind-clause

# Branch types: feature/, fix/, docs/, refactor/, test/
```

### 3. Do the Work with Comprehensive Tests

- Unit tests for each layer (parser, planner, executor)
- Integration tests for end-to-end behavior
- Aim for 100% coverage on new code (90% minimum)

### 4. Run Pre-Push Checks

```bash
make pre-push
```

Runs: format-check, lint, type-check, coverage (85% total, 90% patch).

### 5. Commit with Issue Number

```bash
git commit -m "feat: implement UNWIND clause (#42)

- Add UNWIND grammar rule to cypher.lark
- Implement UnwindClause AST node
- Add planner support for Unwind operator
- Implement executor logic for list iteration
- Add 15 unit tests + 8 integration tests

All tests passing, coverage at 100% for new code."
```

### 6. Create PR with "Closes #XX"

```bash
gh pr create --title "feat: implement UNWIND clause" \
  --body "Closes #42"
```

GitHub automatically closes the issue when PR merges.

## Development Commands

```bash
make pre-push          # Run all checks (mirrors CI)
make test              # All tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make coverage          # Run with coverage
make coverage-report   # View HTML coverage report
make coverage-diff     # Coverage for changed files only

# Run tests in parallel (4x faster for TCK)
pytest tests/ -n auto
```

**Coverage Requirements:**
- Total: 85% minimum
- Patch: 90% minimum for changed files
- Best practice: Aim for 100% on new code

## Architecture: 4-Layer System

```
User Code (Python API / Cypher)
          ↓
┌─────────────────────────────────────────────────┐
│ 1. Parser (src/graphforge/parser/)             │
│    - cypher.lark: Grammar                       │
│    - parser.py: Transformer (Lark → AST)        │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│ 2. Planner (src/graphforge/planner/)           │
│    - planner.py: AST → Logical operators        │
│    - operators.py: Operator definitions         │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│ 3. Executor (src/graphforge/executor/)         │
│    - executor.py: Operator execution            │
│    - evaluator.py: Expression evaluation        │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│ 4. Storage (src/graphforge/storage/)           │
│    - memory.py: In-memory graph                 │
│    - sqlite_backend.py: SQLite persistence      │
│    - serialization.py: MessagePack encoding     │
└─────────────────────────────────────────────────┘
```

### Key Principles

1. **Each layer is independent** - Parser knows nothing about execution
2. **AST is the contract** - Parser produces AST, planner consumes it
3. **Operators are composable** - Planner emits list, executor chains them
4. **Storage is pluggable** - Executor uses Graph interface

### Adding Cypher Features

**You must modify ALL four layers:**

1. **Parser:** Add grammar to `cypher.lark` + transformer in `parser.py`
2. **AST:** Add/modify dataclasses in `src/graphforge/ast/`
3. **Planner:** Update `planner.py` to emit operators
4. **Executor:** Implement execution in `executor.py`

**Decision matrix:**
- 1-2 layers affected: Simpler, focused changes
- 3-4 layers affected: More complex, comprehensive changes
- Extensive tests needed: Plan for thorough test coverage
- New to feature: Take time to understand the architecture

## Critical Code Patterns

### Value Types System

All query results use `CypherValue` wrappers:

```python
# src/graphforge/types/values.py
CypherString, CypherInt, CypherFloat, CypherBool, CypherNull
CypherList, CypherMap

# Always wrap results in executor
return CypherString("hello")
```

### Pydantic Validation

All AST nodes, operators, and metadata use **Pydantic v2 BaseModel**:

```python
class BinaryOp(BaseModel):
    op: str = Field(...)
    left: Any = Field(...)
    right: Any = Field(...)

    @field_validator("op")
    @classmethod
    def validate_op(cls, v: str) -> str:
        if v not in {"=", "<>", "<", ">", "<=", ">=", "AND", "OR", ...}:
            raise ValueError(f"Unsupported operator: {v}")
        return v

    model_config = {"frozen": True}  # Immutable
```

**Key patterns:**
- Always use keyword arguments (Pydantic v2 requirement)
- Use `@field_validator` for single-field validation
- Use `@model_validator(mode="after")` for cross-field validation
- All AST nodes are frozen (immutable)

**When to use:**
- Pydantic: AST nodes, operators, metadata (needs validation)
- Dataclasses: NodeRef, EdgeRef, CypherValue (performance-critical)

### Two Serialization Systems

**System 1: SQLite + MessagePack (Graph Data)**
- Purpose: Store nodes, edges, properties
- Location: `src/graphforge/storage/serialization.py`
- Format: Binary (fast, compact)
- Use for: Runtime graph operations

**System 2: Pydantic + JSON (Metadata)**
- Purpose: Store dataset metadata, schemas, ontologies
- Location: `src/graphforge/storage/pydantic_serialization.py`
- Format: JSON (human-readable, validatable)
- Use for: Configuration, dataset definitions

**CRITICAL:** Never mix these systems. Graph data → MessagePack. Metadata → JSON.

### Graph Storage Duality

```python
# In-memory (fast, volatile)
gf = GraphForge()

# Persistent (SQLite backend)
gf = GraphForge("path/to/db.db")
```

### Transaction Handling

```python
# Auto-commit (default)
gf.execute("CREATE (n:Person)")

# Explicit transactions
gf.begin()
gf.execute("CREATE (n:Person)")
gf.execute("CREATE (m:Person)")
gf.commit()  # or rollback()
```

### Dataset System

Registry pattern in `src/graphforge/datasets/`:

```
datasets/
├── base.py          # DatasetInfo model
├── registry.py      # Global registry
├── loaders/         # Format-specific loaders
│   ├── csv.py
│   └── cypher.py
└── sources/         # Dataset registrations
    ├── snap.py
    └── __init__.py  # Auto-registers
```

## Testing Strategy

### Test Organization

```
tests/
├── unit/              # Fast, isolated (< 1ms)
│   ├── parser/
│   ├── planner/
│   ├── executor/
│   └── storage/
├── integration/       # End-to-end Cypher queries
├── tck/               # OpenCypher TCK compliance
│   ├── features/      # Gherkin scenarios
│   └── steps/         # pytest-bdd steps
└── property/          # Hypothesis property tests
```

### Writing Tests

**Unit tests** - Test ONE component in isolation:
```python
def test_parse_simple_match():
    query = "MATCH (n:Person) RETURN n"
    ast = parse_cypher(query)
    assert isinstance(ast.clauses[0], MatchClause)
```

**Integration tests** - Test end-to-end:
```python
def test_match_returns_nodes():
    gf = GraphForge()
    gf.execute("CREATE (:Person {name: 'Alice'})")
    results = gf.execute("MATCH (p:Person) RETURN p.name AS name")
    assert results[0]['name'].value == 'Alice'
```

**TCK tests** - Gherkin syntax:
```gherkin
Scenario: Match simple node
  Given an empty graph
  When executing query:
    """
    CREATE (n:Person {name: 'Alice'})
    """
  Then the result should be empty
```

### Test Parametrization

Use for testing same logic with different inputs:

```python
@pytest.mark.parametrize("op,left,right,expected", [
    ("=", 5, 5, True),
    ("<>", 5, 10, True),
    ("<", 5, 10, True),
])
def test_comparison_operators(op, left, right, expected):
    gf = GraphForge()
    result = gf.execute(f"RETURN {left} {op} {right} AS result")
    assert result[0]['result'].value == expected
```

### Property-Based Testing

Use Hypothesis for testing invariants:

```python
from hypothesis import given
from hypothesis import strategies as st

@given(st.integers(), st.text(), st.booleans())
def test_cypher_value_roundtrip(int_val, str_val, bool_val):
    """CypherValues serialize and deserialize correctly."""
    values = [CypherInt(int_val), CypherString(str_val), CypherBool(bool_val)]
    for val in values:
        serialized = serialize_value(val)
        deserialized = deserialize_value(serialized)
        assert deserialized == val
```

### Test Isolation

Always use fresh fixtures:

```python
# ✅ Good - Each test gets fresh graph
def test_create_node(empty_graph):
    empty_graph.execute("CREATE (:Person)")
    assert len(empty_graph.execute("MATCH (n) RETURN n")) == 1

# ❌ Bad - Shared mutable state
graph = GraphForge()
def test_create_node():
    graph.execute("CREATE (:Person)")  # Pollutes state
```

## Common Development Tasks

### Adding a New Cypher Clause

1. Grammar: Add to `cypher.lark`
2. AST: Add dataclass to `ast/clause.py`
3. Transformer: Add method to `parser.py`
4. Planner: Update to emit operator
5. Operator: Add to `operators.py`
6. Executor: Implement execution
7. Tests: Unit + integration tests

### Adding a New Function

1. Grammar: Add to `function_call` rule in `cypher.lark`
2. Evaluator: Implement in `executor/evaluator.py`
3. Tests: Unit + integration tests

### Fixing Parser Issues

1. Check grammar: `src/graphforge/parser/cypher.lark` (EBNF syntax)
2. Check transformer: `parser.py` (methods match rule names)
3. Debug with: `tree.pretty()` to see parse tree structure

### Fixing Executor Issues

**Common problems:**
1. Not wrapping values as `CypherValue` instances
2. Not handling NULL (use ternary logic)
3. Mutating input rows (always create new contexts)
4. Not checking bound variables

**Debug with logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
gf.execute("MATCH (n) RETURN n")  # See operator pipeline
```

## Important Files

### Entry Points
- `src/graphforge/api.py` - Main `GraphForge` class
- `src/graphforge/__init__.py` - Public exports

### Core Grammar
- `src/graphforge/parser/cypher.lark` - Complete Cypher grammar

### Type Definitions
- `src/graphforge/types/values.py` - CypherValue type system
- `src/graphforge/types/graph.py` - NodeRef/EdgeRef handles

### Storage
- `src/graphforge/storage/memory.py` - Graph interface + in-memory
- `src/graphforge/storage/sqlite_backend.py` - SQLite persistence
- `src/graphforge/storage/serialization.py` - MessagePack encoding

## Documentation

Full docs in `docs/`:
- `docs/reference/opencypher-compatibility.md` - Feature matrix
- `docs/datasets/` - Dataset integration docs
- `docs/tutorial.md` - Getting started guide

Generated docs: `mkdocs serve` (requires `uv sync --group docs`)

## CI/CD

GitHub Actions (`.github/workflows/`):
- `test.yml` - Runs on all PRs (same as `make pre-push`)
- `codecov.yml` - Coverage reporting
- `test-analytics.yml` - Test performance tracking

All tests must pass + coverage thresholds met before merge.

## Project Philosophy

1. **Correctness over performance** - Match openCypher semantics exactly
2. **Inspectability** - Simple, debuggable code over clever optimizations
3. **Modularity** - Each layer independent and replaceable
4. **Developer experience** - Clear errors, good defaults, zero config

**Not goals:** High throughput, massive graphs, production deployment
