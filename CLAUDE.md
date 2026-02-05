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

Branch naming convention: `<type>/<issue-number>-<short-description>`

```bash
# For issue #42: Add UNWIND clause
git checkout main
git pull origin main
git checkout -b feature/42-unwind-clause

# Types: feature/, fix/, docs/, refactor/, test/
```

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

### 5. Create PR Referencing the Issue

```bash
git add .
git commit -m "feat: implement UNWIND clause (#42)

Description of changes...

Closes #42"

git push origin feature/42-unwind-clause

gh pr create --title "feat: implement UNWIND clause" \
  --body "Description...

Closes #42" \
  --label "enhancement"
```

**CRITICAL:** Use "Closes #XX" or "Fixes #XX" in PR body so GitHub automatically closes the issue when PR merges.

### 6. Handling Discovered Issues

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
├── base.py          # DatasetInfo dataclass
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
