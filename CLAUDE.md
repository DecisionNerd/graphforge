# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GraphForge is an embedded, openCypher-compatible graph database for Python, designed for research and analysis workflows. It prioritizes **correctness over performance** and provides declarative querying with automatic persistence via SQLite.

**Not a production database** - optimized for interactive analysis on small-to-medium graphs (< 10M nodes).

## Development Workflow (CRITICAL - Follow This Always)

**Every piece of work MUST follow this workflow. No exceptions.**

### 1. Create an Issue First

Before starting ANY work, create an issue:

```bash
gh issue create --title "feat: add UNWIND clause support" --body "Description of the work..." --label "enhancement"
```

**Even if you discover something mid-work:**
- If it's in scope: Continue with current issue
- If it's out of scope: Create a NEW issue, note it, continue with current work

**Never:**
- Start work without an issue
- Close issues manually (PRs do this automatically)
- Expand scope mid-work without creating new issues

### 2. Create a Branch Associated with the Issue

**REQUIRED:** Branch name MUST include issue number.

**Format:** `<type>/<issue-number>-<short-description>`

```bash
# For issue #42: Add UNWIND clause
git checkout main
git pull origin main
git checkout -b feature/42-unwind-clause

# Branch types:
# feature/  - New features
# fix/      - Bug fixes
# docs/     - Documentation only
# refactor/ - Code refactoring
# test/     - Test additions/fixes
```

**Examples:**
- `feature/42-unwind-clause` ✅
- `fix/89-null-handling-bug` ✅
- `docs/80-add-claude-md` ✅
- `feature/add-unwind` ❌ (missing issue number)
- `42-unwind` ❌ (missing type prefix)

### 3. Do the Work with Comprehensive Tests

Write code following the architecture patterns below. **Always include comprehensive tests:**

- Unit tests for each layer (parser, planner, executor)
- Integration tests for end-to-end behavior
- Aim for 100% coverage on new code (90% minimum)

### 4. Run Pre-Push Checks

Before committing:

```bash
make pre-push
```

This catches issues before CI:
- Format checks
- Linting
- Type checking
- All tests
- Coverage validation (85% total, 90% patch)

### 5. Commit and Push

**Commit message format:**

```
<type>: <subject> (#<issue-number>)

<body>

<footer>
```

**Types:** feat, fix, docs, refactor, test, chore

**Examples:**

```bash
# Good commit messages
git commit -m "feat: implement UNWIND clause (#42)

- Add UNWIND grammar rule to cypher.lark
- Implement UnwindClause AST node
- Add planner support for Unwind operator
- Implement executor logic for list iteration
- Add 15 unit tests + 8 integration tests

All tests passing, coverage at 100% for new code."

git commit -m "fix: handle NULL in AND operator (#89)

Fixes ternary logic for NULL AND expressions.
Previously returned NULL for any NULL operand.
Now correctly handles: NULL AND false → false

Closes #89"

# Bad commit messages
git commit -m "fix bug" ❌ (no issue number, vague)
git commit -m "changes" ❌ (not descriptive)
git commit -m "WIP" ❌ (not final commit message)
```

### 6. Create PR Referencing the Issue

```bash
git push origin feature/42-unwind-clause

gh pr create --title "feat: implement UNWIND clause" \
  --body "## Summary

Implements UNWIND clause for list iteration...

## Changes
- Grammar updates
- AST changes
- Planner logic
- Executor implementation
- Comprehensive tests

## Testing
- 15 unit tests
- 8 integration tests
- 100% coverage on new code
- All pre-push checks passing

Closes #42" \
  --label "enhancement"
```

**CRITICAL:** Use "Closes #XX" or "Fixes #XX" in PR body so GitHub automatically closes the issue when PR merges.

### 7. Handling Discovered Issues

If you discover problems while working:

**In Scope (related to current work):**
- Fix it as part of current PR
- Mention in commit message
- Document in PR description

**Out of Scope (different feature/bug):**
```bash
# Create new issue for tracking
gh issue create --title "bug: parser fails on nested lists" \
  --body "Discovered while working on #42..." \
  --label "bug"
# Created issue #43

# Continue with current work (#42)
# Don't try to fix #43 in this PR
```

**When to create new issues:**
- Missing features blocking your work
- Bugs discovered during development
- Technical debt worth tracking
- Documentation gaps
- Future enhancements

**Never:**
- Expand PR scope to fix discovered issues
- Close issues you didn't fully address
- Leave discoveries untracked

### Example Workflow

```bash
# User asks: "Add support for UNWIND"

# 1. Create issue
gh issue create --title "feat: add UNWIND clause support" \
  --body "Implement UNWIND for list iteration..." \
  --label "enhancement"
# Created issue #42

# 2. Create branch
git checkout -b feature/42-unwind-clause

# 3. Do work (parser, AST, planner, executor, tests)
# Edit files...
make pre-push  # Verify everything passes

# 4. Commit and push
git add .
git commit -m "feat: implement UNWIND clause (#42)"
git push origin feature/42-unwind-clause

# 5. Create PR
gh pr create --title "feat: implement UNWIND clause" \
  --body "Closes #42"

# Issue #42 automatically closes when PR merges
```

## Development Commands

### Primary Workflow

```bash
# Run all pre-push checks (mirrors CI)
make pre-push

# This runs in order:
# 1. format-check - ruff format --check .
# 2. lint         - ruff check .
# 3. type-check   - mypy src/graphforge --strict-optional --show-error-codes
# 4. coverage     - pytest with coverage measurement
# 5. check-coverage - validate 85% total coverage
# 6. check-patch-coverage - validate 90% coverage on changed files
```

### Testing

```bash
# Run all tests (unit + integration)
make test

# Run specific test categories
make test-unit           # Unit tests only (~200 tests)
make test-integration    # Integration tests only (~300 tests)

# Run single test file
pytest tests/unit/parser/test_parser.py -v

# Run single test function
pytest tests/unit/parser/test_parser.py::TestMatchParsing::test_simple_match -v

# Run tests in parallel (much faster for large test suites)
pytest tests/ -n auto          # Auto-detect CPU count
pytest tests/tck/ -n 8          # Use 8 workers
# Note: TCK tests run ~4x faster with parallel execution (54s vs 3.5min)

# Run with coverage
make coverage

# View coverage report in browser
make coverage-report

# Check coverage for changed files only
make coverage-diff
```

### Code Quality

```bash
# Format code
make format

# Check formatting without modifying
make format-check

# Run linter
make lint

# Run type checker
make type-check
```

### Coverage Requirements

- **Total coverage:** 85% minimum (enforced by `make pre-push`)
- **Patch coverage:** 90% minimum for changed files (enforced by `make pre-push`)
- **Best practice:** Aim for 100% coverage on new code to satisfy both thresholds

If patch coverage fails, run `make coverage-report` to see detailed line-by-line coverage.

### Coverage Configuration

Coverage is measured using `pytest-cov` with branch coverage enabled:

```bash
# Run tests with coverage
pytest --cov=src/graphforge --cov-report=html --cov-report=term

# Or use make target
make coverage
```

**Branch coverage**: Ensures both `if` and `else` branches are tested:
```python
# This function requires 2 tests for 100% branch coverage:
def absolute_value(x):
    if x < 0:
        return -x  # Branch 1
    else:
        return x   # Branch 2
```

**Excluding lines from coverage**:
```python
def debug_only():
    if __name__ == "__main__":  # Excluded by pyproject.toml
        print("Debug mode")
    raise NotImplementedError  # Excluded by pyproject.toml
```

**Coverage thresholds**:
- Total coverage: 85% minimum (`make check-coverage`)
- Patch coverage: 90% minimum (`make check-patch-coverage`)
- Both enforced by `make pre-push` (runs before every push)

**CI/CD coverage**:
- GitHub Actions checks total coverage (85% threshold) on all PRs
- Results uploaded to CodeCov for project (85%) and patch (80%) analysis
- CodeCov comments on PRs with coverage reports (informational, non-blocking)
- **Local enforcement**: Always run `make pre-push` to ensure 90% patch coverage before pushing

### Understanding Coverage Metrics

GraphForge tracks **two types of coverage**:

1. **Total Coverage** (~90% currently)
   - Measures: All lines covered / All lines in source
   - Reported by: Local pytest with `make coverage`
   - Target: 85% minimum (enforced by `make pre-push`)
   - Purpose: Ensure overall codebase health

2. **Patch Coverage** (varies by PR)
   - Measures: Covered lines in diff / Changed lines in diff
   - Reported by: CodeCov on pull requests
   - Target: 90% minimum (enforced by `make check-patch-coverage`)
   - Purpose: Ensure new code is well-tested

**Why they differ**:
- New features may have 100% integration coverage but miss unit-level edge cases
- Defensive error handling branches often lack explicit tests
- Complex operator combinations may not exercise all code paths

**How to improve patch coverage**:
```bash
# 1. Run coverage on your branch
make coverage

# 2. View HTML report to see uncovered lines
make coverage-report
# Opens htmlcov/index.html in browser

# 3. Check patch coverage for changed files only
make coverage-diff
# Shows coverage for files modified in current branch

# 4. Add unit tests for uncovered branches
# Focus on:
# - Error handling paths (missing variables, invalid types)
# - Edge cases (empty lists, NULL values, cycle detection)
# - Operator combinations (filter+map, ALL with mixed True/False/NULL)
```

**Best practices**:
- Integration tests validate end-to-end behavior
- Unit tests validate edge cases and error paths
- Aim for 100% coverage on new code to satisfy both metrics
- Use property-based tests (Hypothesis) for exhaustive edge case testing

## Architecture: 4-Layer System

GraphForge is built as a pipeline with four distinct layers. **Understanding this flow is critical** for making changes:

```
User Code (Python API / Cypher)
          ↓
┌─────────────────────────────────────────────────┐
│ 1. Parser (src/graphforge/parser/)             │
│    - cypher.lark: Lark grammar definition       │
│    - parser.py: Transformer (Lark tree → AST)  │
│    Output: AST nodes (src/graphforge/ast/)     │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│ 2. Planner (src/graphforge/planner/)           │
│    - planner.py: AST → Logical operators        │
│    - operators.py: Operator definitions         │
│    Output: Logical plan (list of operators)     │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│ 3. Executor (src/graphforge/executor/)         │
│    - executor.py: Operator execution engine     │
│    - evaluator.py: Expression evaluation        │
│    Output: Query results (list of dicts)        │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│ 4. Storage (src/graphforge/storage/)           │
│    - memory.py: In-memory graph (adjacency)     │
│    - sqlite_backend.py: SQLite persistence      │
│    - serialization.py: MessagePack encoding     │
└─────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Each layer is independent** - Parser knows nothing about execution, executor knows nothing about storage implementation
2. **AST is the contract** - Parser produces AST, planner consumes AST. Changing grammar requires AST changes
3. **Operators are composable** - Planner emits list of operators, executor chains them together
4. **Storage is pluggable** - Executor operates on Graph interface, doesn't care about SQLite vs in-memory

### When Adding Cypher Features

**You must modify ALL four layers:**

1. **Parser:** Add grammar rules to `cypher.lark` + transformer methods in `parser.py`
2. **AST:** Add/modify dataclasses in `src/graphforge/ast/` (clause.py, expression.py, pattern.py)
3. **Planner:** Update `planner.py` to handle new AST nodes → emit operators
4. **Executor:** Update `executor.py` to execute new operators

**Example:** Adding `UNWIND` clause requires:
- Grammar: `unwind_clause: "UNWIND"i expression "AS" variable`
- AST: `@dataclass class UnwindClause: expression: Expression, variable: str`
- Planner: Convert `UnwindClause` → `Unwind` operator
- Executor: Implement `_execute_unwind()` method

## Critical Code Patterns

### Value Types System

All query results use `CypherValue` wrappers (not raw Python types):

```python
# src/graphforge/types/values.py
CypherString, CypherInt, CypherFloat, CypherBool, CypherNull
CypherList, CypherMap  # Nested structures
```

**Why:** Preserves type information, handles NULL semantics, enables property access chains

**Usage in executor:**
```python
# Always wrap results
return CypherString("hello")
# Access underlying value
result.value  # Returns Python type
```

### Pydantic Validation System

All AST nodes, operators, and dataset metadata use **Pydantic v2 BaseModel** for validation:

```python
# AST nodes (src/graphforge/ast/)
class BinaryOp(BaseModel):
    op: str = Field(..., description="Operator")
    left: Any = Field(..., description="Left expression")
    right: Any = Field(..., description="Right expression")

    @field_validator("op")
    @classmethod
    def validate_op(cls, v: str) -> str:
        valid_ops = {"=", "<>", "<", ">", "<=", ">=", "AND", "OR", "+", "-", "*", "/", ...}
        if v not in valid_ops:
            raise ValueError(f"Unsupported binary operator: {v}")
        return v

    model_config = {"frozen": True}  # Immutable after creation
```

**Key patterns:**

1. **Always use keyword arguments** - Pydantic v2 requires keyword args:
   ```python
   # ✅ Correct
   BinaryOp(op="=", left=Variable(name="x"), right=Literal(value=5))

   # ❌ Wrong - will raise TypeError
   BinaryOp("=", Variable("x"), Literal(5))
   ```

2. **Field validators** - Use `@field_validator` for single-field validation:
   ```python
   @field_validator("name")
   @classmethod
   def validate_name(cls, v: str) -> str:
       if not v.strip():
           raise ValueError("Name cannot be empty")
       return v
   ```

3. **Model validators** - Use `@model_validator` for cross-field validation:
   ```python
   @model_validator(mode="after")
   def validate_limits(self) -> "LimitClause":
       if self.count < 0:
           raise ValueError("LIMIT must be non-negative")
       return self
   ```

4. **Frozen models** - All AST nodes and operators are immutable:
   ```python
   model_config = {"frozen": True}
   ```

5. **API validation** - Validate user inputs with dedicated models:
   ```python
   # src/graphforge/api.py
   class QueryInput(BaseModel):
       query: str = Field(..., min_length=1)

       @field_validator("query")
       @classmethod
       def validate_query(cls, v: str) -> str:
           if not v.strip():
               raise ValueError("Query cannot be empty")
           return v

   def execute(self, query: str) -> list[dict]:
       QueryInput(query=query)  # Validates input
       # ... proceed with execution
   ```

6. **Serialization** - Use Pydantic's built-in serialization for metadata:
   ```python
   from graphforge.storage import serialize_model, deserialize_model

   # Serialize to dict
   data = serialize_model(dataset_info)

   # Deserialize from dict
   restored = deserialize_model(DatasetInfo, data)

   # Save to JSON file
   save_model_to_file(dataset_info, "dataset.json")

   # Load from JSON file
   loaded = load_model_from_file(DatasetInfo, "dataset.json")
   ```

**When to use Pydantic vs plain classes:**
- **Use Pydantic:** AST nodes, operators, dataset metadata, API inputs (anything that needs validation)
- **Use dataclasses:** NodeRef, EdgeRef, CypherValue types (performance-critical, no validation needed)

**Testing Pydantic models:**
```python
from pydantic import ValidationError
import pytest

def test_invalid_operator():
    # Pydantic validates at construction time
    with pytest.raises(ValidationError, match="Unsupported binary operator"):
        BinaryOp(op="INVALID", left=Literal(value=1), right=Literal(value=2))
```

### Two Serialization Systems (Critical Architecture)

GraphForge uses **two separate serialization systems** for different purposes. Understanding this separation is critical for maintaining correctness and performance.

#### System 1: SQLite + MessagePack (Graph Data Storage)

**Purpose:** Store actual graph data (nodes, edges, properties)

**Location:** `src/graphforge/storage/serialization.py`

**Format:** Binary MessagePack (compact, fast)

**What it serializes:**
- CypherValue types (CypherInt, CypherString, CypherBool, etc.)
- Node labels (frozenset of strings)
- Node/edge properties (dict of CypherValues)
- Graph structure stored in SQLite tables

**Used by:**
- `SQLiteBackend` (src/graphforge/storage/sqlite_backend.py)
- Persistent graph storage
- Transaction management
- Graph snapshots for rollback

**Example:**
```python
# User creates a node
gf = GraphForge("my-graph.db")
gf.create_node(['Person'], name='Alice', age=30)

# Behind the scenes:
# 1. Properties converted to CypherValues: {name: CypherString('Alice'), age: CypherInt(30)}
# 2. Serialized with MessagePack: serialize_properties({...})
# 3. Stored in SQLite: INSERT INTO nodes (id, labels, properties) VALUES (...)
# 4. Binary format optimized for speed and space

gf.close()  # Commits to SQLite
```

**Why MessagePack:**
- Binary format (smaller than JSON)
- Fast serialization/deserialization
- Efficient for frequent read/write operations
- No human readability needed (internal storage)

**Do NOT use for:** Metadata, schemas, dataset definitions (use Pydantic instead)

#### System 2: Pydantic + JSON (Metadata & Schema Storage)

**Purpose:** Store metadata, schemas, dataset definitions, ontologies

**Location:** `src/graphforge/storage/pydantic_serialization.py`

**Format:** JSON (human-readable, validatable)

**What it serializes:**
- DatasetInfo models (dataset metadata)
- AST nodes (query plan caching - future)
- Ontology definitions (schemas, constraints - future)
- LDBC dataset metadata (future)
- User-defined class schemas (future)

**Used by:**
- Dataset registry (metadata files)
- Configuration files
- Schema definitions
- Future ontology system

**Example:**
```python
from graphforge.storage import save_model_to_file, load_model_from_file

# Define dataset metadata
dataset_info = DatasetInfo(
    name="ldbc-snb-sf0.1",
    description="LDBC Social Network Benchmark",
    url="https://repository.surfsara.nl/...",
    nodes=327588,
    edges=1800000,
    labels=["Person", "Post", "Comment"],
    size_mb=50.0,
    license="CC BY 4.0",
    category="social",
    loader_class="ldbc"
)

# Save to JSON file (human-readable)
save_model_to_file(dataset_info, "datasets/ldbc-sf0.1.json")

# Later, load with validation
loaded = load_model_from_file(DatasetInfo, "datasets/ldbc-sf0.1.json")
# Pydantic validates: URL scheme, field types, required fields, etc.
```

**Why Pydantic + JSON:**
- Human-readable (can edit metadata files)
- Validatable (catches errors at load time)
- Versionable (can track changes in git)
- Self-documenting (field names and descriptions)
- Extensible (easy to add new fields)

**Do NOT use for:** Actual graph data (use SQLite + MessagePack instead)

#### Critical: Never Mix These Systems

**❌ Wrong - Don't serialize graph data with Pydantic:**
```python
# DON'T DO THIS - Performance disaster
node = gf.create_node(['Person'], name='Alice')
save_model_to_file(node, "node.json")  # Wrong! Use SQLite instead
```

**❌ Wrong - Don't serialize metadata with MessagePack:**
```python
# DON'T DO THIS - Loses validation and readability
dataset_info = DatasetInfo(...)
blob = msgpack.packb(serialize_model(dataset_info))  # Wrong! Use JSON instead
```

**✅ Correct - Use the right system for each purpose:**
```python
# Graph data → SQLite + MessagePack
gf = GraphForge("graph.db")
gf.create_node(['Person'], name='Alice')
gf.close()  # Stored efficiently in SQLite

# Metadata → Pydantic + JSON
dataset_info = DatasetInfo(...)
save_model_to_file(dataset_info, "metadata.json")  # Readable and validated
```

#### Future: Ontology Support

When ontology support is added, the separation becomes even more important:

**Ontology Schema (Pydantic + JSON):**
```python
# Define a Person class schema (future)
person_schema = ClassSchema(
    name="Person",
    properties=[
        PropertyDef(name="name", type="string", required=True),
        PropertyDef(name="age", type="integer", min=0, max=150),
        PropertyDef(name="email", type="string", format="email"),
    ],
    constraints=[
        UniqueConstraint(property="email"),
    ]
)

# Save schema definition (human-readable, validatable)
save_model_to_file(person_schema, "ontologies/person.json")
```

**Graph Instances (SQLite + MessagePack):**
```python
# Create actual Person nodes (uses schema for validation)
gf = GraphForge("graph.db", ontology="ontologies/")
gf.create_node(['Person'], name='Alice', age=30, email='alice@example.com')
# Still stored in SQLite with MessagePack (unchanged)
gf.close()
```

**Benefits:**
1. **Schema definitions** are versioned, readable, shareable (JSON)
2. **Graph data** remains fast and compact (MessagePack)
3. **Validation** happens at graph operation time (Pydantic models)
4. **Storage** remains optimized for graph operations (SQLite)

#### Summary Table

| Aspect | SQLite + MessagePack | Pydantic + JSON |
|--------|---------------------|----------------|
| **Purpose** | Graph data storage | Metadata & schemas |
| **Data Types** | CypherValues, nodes, edges | DatasetInfo, AST, ontologies |
| **Format** | Binary (MessagePack) | Text (JSON) |
| **Readable** | No (binary) | Yes (human-readable) |
| **Validation** | At write time | At load time |
| **Performance** | Optimized for speed | Optimized for safety |
| **Versioning** | Not intended | Git-friendly |
| **Use Case** | Runtime graph operations | Configuration & definitions |
| **Files** | `serialization.py` | `pydantic_serialization.py` |
| **Storage** | `*.db` SQLite files | `*.json` metadata files |

**Key Takeaway:** These systems are complementary, not competing. Use MessagePack for data, JSON for metadata. Never mix them.

### Graph Storage Duality

Storage has TWO modes (no configuration required):

```python
# In-memory (fast, volatile)
gf = GraphForge()

# Persistent (SQLite backend)
gf = GraphForge("path/to/db.db")
```

**Implementation:** Both use `Graph` interface (`src/graphforge/storage/memory.py`). SQLite backend (`sqlite_backend.py`) serializes graph state with MessagePack on commit.

### Transaction Handling

**Auto-commit by default** - each `execute()` is implicitly committed:

```python
gf.execute("CREATE (n:Person)")  # Automatically committed
```

**Explicit transactions** for atomic updates:

```python
gf.begin()
gf.execute("CREATE (n:Person)")
gf.execute("CREATE (m:Person)")
gf.commit()  # or rollback()
```

**Critical:** Executor must respect transaction boundaries. Never auto-commit inside `_execute_*()` methods.

### Dataset System

Datasets are loaded via registry pattern (`src/graphforge/datasets/`):

```
datasets/
├── base.py          # DatasetInfo Pydantic model
├── registry.py      # Global registry + API functions
├── loaders/         # Format-specific loaders
│   ├── csv.py       # Edge list format (SNAP)
│   └── cypher.py    # Cypher script format
└── sources/         # Dataset registrations
    ├── snap.py      # Stanford datasets
    └── __init__.py  # Auto-registers on import
```

**To add datasets:**
1. Create loader in `loaders/` if needed
2. Register loader: `register_loader("name", LoaderClass)`
3. Register datasets: `register_dataset(DatasetInfo(...))`
4. Sources auto-register on import via `datasets/sources/__init__.py`

## Testing Strategy

### Test Organization

```
tests/
├── unit/              # Fast, isolated (< 1ms each)
│   ├── parser/        # Grammar + AST validation
│   ├── planner/       # Logical plan generation
│   ├── executor/      # Operator execution
│   └── storage/       # Graph operations
├── integration/       # End-to-end Cypher queries
│   ├── test_*.py      # Feature-based integration tests
│   └── datasets/      # Dataset loading tests
├── tck/               # OpenCypher TCK compliance
│   ├── features/      # Gherkin scenarios (.feature)
│   └── steps/         # pytest-bdd step definitions
└── property/          # Hypothesis property tests
```

### Test Markers

```python
@pytest.mark.unit         # Fast unit tests
@pytest.mark.integration  # Slower integration tests
@pytest.mark.tck          # TCK compliance tests
@pytest.mark.slow         # Tests > 1s
```

### Writing Tests

**Unit tests** should test ONE component in isolation:

```python
# tests/unit/parser/test_match.py
def test_parse_simple_match():
    query = "MATCH (n:Person) RETURN n"
    ast = parse_cypher(query)
    assert isinstance(ast.clauses[0], MatchClause)
```

**Integration tests** should test end-to-end behavior:

```python
# tests/integration/test_match.py
def test_match_returns_nodes():
    gf = GraphForge()
    gf.execute("CREATE (:Person {name: 'Alice'})")
    results = gf.execute("MATCH (p:Person) RETURN p.name AS name")
    assert results[0]['name'].value == 'Alice'
```

### TCK Tests

OpenCypher TCK tests use Gherkin syntax (`tests/tck/features/*.feature`):

```gherkin
Scenario: Match simple node
  Given an empty graph
  When executing query:
    """
    CREATE (n:Person {name: 'Alice'})
    """
  Then the result should be empty
```

Step definitions in `tests/tck/steps/` map Gherkin to pytest code.

**Current status:** ~950/3,837 TCK scenarios passing (~25%)

## Advanced Testing Patterns

### Fixture Scoping & Dependencies

**Function scope** (default) - Use for most fixtures:
```python
@pytest.fixture
def empty_graph():
    """Fresh GraphForge instance for each test."""
    return GraphForge()
```

**Module scope** - Use for expensive setup shared across test class:
```python
@pytest.fixture(scope="module")
def loaded_dataset():
    """Load LDBC dataset once for all tests in module."""
    gf = GraphForge()
    load_dataset(gf, "ldbc-snb-sf0.1")
    return gf
```

**Session scope** - Use for global resources (rare):
```python
@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "data"
```

**Fixture dependencies**:
```python
@pytest.fixture
def graph_with_person(empty_graph):
    """Graph with a Person node (depends on empty_graph)."""
    empty_graph.execute("CREATE (:Person {name: 'Alice'})")
    return empty_graph
```

### Test Parametrization Patterns

**Use parametrize for**:
- Testing same logic with different inputs
- Boundary conditions and edge cases
- Operator variations (=, <>, <, >, etc.)

```python
@pytest.mark.parametrize("op,left,right,expected", [
    ("=", 5, 5, True),
    ("<>", 5, 10, True),
    ("<", 5, 10, True),
    ("<=", 5, 5, True),
    (">", 10, 5, True),
    (">=", 5, 5, True),
])
def test_comparison_operators(op, left, right, expected):
    gf = GraphForge()
    result = gf.execute(f"RETURN {left} {op} {right} AS result")
    assert result[0]['result'].value == expected
```

**Use separate tests for**:
- Different features or behaviors
- Complex setup that doesn't share logic
- Tests with different failure modes

**Parametrize IDs for readability**:
```python
@pytest.mark.parametrize("query,expected", [
    ("MATCH (n) RETURN n", []),
    ("MATCH (n:Person) RETURN n", []),
], ids=["match-all", "match-label"])
def test_match_patterns(query, expected):
    ...
```

### Property-Based Testing with Hypothesis

Use Hypothesis (`tests/property/`) for testing invariants and edge cases:

**When to use property tests**:
- Testing mathematical properties (commutativity, associativity)
- Serialization round-trips (serialize → deserialize → equal)
- Parser fuzzing (generate random valid/invalid queries)
- NULL handling across all operators

**Example - Serialization round-trip**:
```python
from hypothesis import given
from hypothesis import strategies as st

@given(st.integers(), st.text(), st.booleans())
def test_cypher_value_roundtrip(int_val, str_val, bool_val):
    """CypherValues serialize and deserialize correctly."""
    values = [
        CypherInt(int_val),
        CypherString(str_val),
        CypherBool(bool_val),
    ]
    for val in values:
        serialized = serialize_value(val)
        deserialized = deserialize_value(serialized)
        assert deserialized == val
```

**Example - NULL propagation property**:
```python
@given(st.sampled_from(["AND", "OR", "+", "-", "*", "/"]))
def test_binary_op_null_propagation(op):
    """Binary operators with NULL operand return NULL (except AND/OR)."""
    gf = GraphForge()
    result = gf.execute(f"RETURN null {op} 5 AS result")

    if op in ["AND", "OR"]:
        # Three-valued logic
        assert result[0]['result'] in [CypherBool(False), CypherNull()]
    else:
        # NULL propagation
        assert isinstance(result[0]['result'], CypherNull)
```

**Running property tests**:
```bash
# Run property tests with more examples
pytest tests/property/ --hypothesis-show-statistics

# Reproduce a failure
pytest tests/property/ --hypothesis-seed=12345
```

### Test Isolation Best Practices

**Always use fresh fixtures**:
```python
# ✅ Good - Each test gets fresh graph
def test_create_node(empty_graph):
    empty_graph.execute("CREATE (:Person)")
    assert len(empty_graph.execute("MATCH (n) RETURN n")) == 1

def test_create_another_node(empty_graph):
    empty_graph.execute("CREATE (:Company)")
    # Independent - starts with empty graph
    assert len(empty_graph.execute("MATCH (n) RETURN n")) == 1

# ❌ Bad - Shared mutable state
graph = GraphForge()

def test_create_node():
    graph.execute("CREATE (:Person)")
    assert len(graph.execute("MATCH (n) RETURN n")) == 1

def test_create_another_node():
    graph.execute("CREATE (:Company)")
    # FAILS - sees node from previous test
    assert len(graph.execute("MATCH (n) RETURN n")) == 1
```

**Transaction isolation**:
```python
@pytest.fixture
def transactional_graph():
    """Graph that rolls back after each test."""
    gf = GraphForge("test.db")
    gf.begin()
    yield gf
    gf.rollback()  # Undo all changes
    gf.close()
```

**File system isolation**:
```python
@pytest.fixture
def temp_db(tmp_path):
    """Temporary database file."""
    db_path = tmp_path / "test.db"
    gf = GraphForge(str(db_path))
    yield gf
    gf.close()
    # tmp_path automatically cleaned up by pytest
```

### TCK Testing with pytest-bdd

GraphForge uses pytest-bdd for openCypher TCK compliance testing.

**File structure**:
```
tests/tck/
├── features/          # Gherkin scenarios (.feature files)
│   ├── Match.feature
│   └── Create.feature
└── steps/            # Step definitions (.py files)
    └── steps.py      # Shared step implementations
```

**Writing Gherkin scenarios**:
```gherkin
# tests/tck/features/Example.feature
Feature: Example Feature

  Scenario: Simple node creation
    Given an empty graph
    When executing query:
      """
      CREATE (n:Person {name: 'Alice'})
      """
    Then the result should be empty

  Scenario: Match returns created node
    Given an empty graph
    And having executed:
      """
      CREATE (n:Person {name: 'Alice'})
      """
    When executing query:
      """
      MATCH (p:Person) RETURN p.name AS name
      """
    Then the result should be:
      | name    |
      | 'Alice' |
```

**Implementing step definitions**:
```python
# tests/tck/steps/steps.py
from pytest_bdd import given, when, then, parsers

@given("an empty graph")
def empty_graph():
    return GraphForge()

@when(parsers.parse('executing query:\n{query}'))
def execute_query(empty_graph, query):
    empty_graph._last_result = empty_graph.execute(query)
    return empty_graph

@then("the result should be empty")
def result_is_empty(empty_graph):
    assert len(empty_graph._last_result) == 0
```

**Running TCK tests**:
```bash
# Run all TCK tests
pytest tests/tck/ -v

# Run specific feature
pytest tests/tck/features/Match.feature

# Run specific scenario
pytest tests/tck/features/Match.feature -k "simple_node_creation"

# Parallel execution
pytest tests/tck/ -n auto
```

**TCK coverage reporting**:
```bash
# Count passing scenarios
pytest tests/tck/ --tb=no -q | grep passed
```

## Common Development Tasks

### Adding a New Cypher Clause

1. **Grammar:** Add to `src/graphforge/parser/cypher.lark`
2. **AST:** Add dataclass to `src/graphforge/ast/clause.py`
3. **Transformer:** Add method to `src/graphforge/parser/parser.py`
4. **Planner:** Update `src/graphforge/planner/planner.py` to emit operator
5. **Operator:** Add to `src/graphforge/planner/operators.py`
6. **Executor:** Implement in `src/graphforge/executor/executor.py`
7. **Tests:** Unit tests for each layer + integration test

### Adding a New Function

1. **Grammar:** Add to `function_call` rule in `cypher.lark`
2. **Evaluator:** Implement in `src/graphforge/executor/evaluator.py`
3. **Tests:** Unit tests in `tests/unit/executor/test_functions.py`
4. **Integration:** Test in `tests/integration/test_functions.py`

### Fixing Parser Issues

**Check grammar first:** `src/graphforge/parser/cypher.lark`
- Lark uses EBNF syntax with PEG semantics
- Rules are case-insensitive by default (use `i` suffix)
- Use `?` prefix to inline rules (avoid extra tree nodes)

**Then check transformer:** `src/graphforge/parser/parser.py`
- Methods match grammar rule names
- Must handle all children in parse tree
- Return AST nodes, not Lark trees

**Debugging tips:**
```python
from lark import Lark
grammar = open("src/graphforge/parser/cypher.lark").read()
parser = Lark(grammar, start="query", debug=True)
tree = parser.parse("MATCH (n) RETURN n")
print(tree.pretty())  # See parse tree structure
```

### Fixing Executor Issues

**Common problems:**
1. **Not wrapping values:** All results must be `CypherValue` instances
2. **Not handling NULL:** Use ternary logic (AND/OR/NOT with NULL)
3. **Mutating input rows:** Always create new contexts, never modify in-place
4. **Not checking bound variables:** Variables must exist before use

**Debugging:**
```python
# Add logging to see operator execution
import logging
logging.basicConfig(level=logging.DEBUG)
gf.execute("MATCH (n) RETURN n")  # See operator pipeline
```

## Important Files

### Entry Points

- `src/graphforge/api.py` - Main `GraphForge` class (user-facing API)
- `src/graphforge/__init__.py` - Public exports

### Core Grammar

- `src/graphforge/parser/cypher.lark` - Complete Cypher grammar (Lark EBNF)

### Type Definitions

- `src/graphforge/types/values.py` - CypherValue type system
- `src/graphforge/types/graph.py` - NodeRef/EdgeRef handles

### Storage

- `src/graphforge/storage/memory.py` - Graph interface + in-memory implementation
- `src/graphforge/storage/sqlite_backend.py` - SQLite persistence layer
- `src/graphforge/storage/serialization.py` - MessagePack encoding/decoding

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
