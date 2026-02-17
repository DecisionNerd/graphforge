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

## Agent Teams Workflow

**Agent teams let you coordinate multiple Claude Code sessions working together on complex tasks.** Enable by setting `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `~/.claude/settings.json`.

### How Agent Teams Work Technically

**Architecture:**
- **Team lead**: The main Claude Code session that creates the team and coordinates work
- **Teammates**: Separate, independent Claude Code instances (full sessions with own context windows)
- **Task list**: Shared file system at `~/.claude/tasks/{team-name}/` that coordinates work
- **Team config**: `~/.claude/teams/{team-name}/config.json` with member roster
- **Mailbox**: Messaging system for inter-agent communication (automatic delivery)

**Key mechanics:**
- Each teammate is a **separate Claude Code process** with its own context window
- Teammates load project context automatically (CLAUDE.md, MCP servers, skills)
- Teammates **DO NOT** inherit the lead's conversation history
- Messages between agents are delivered automatically - no polling required
- Task claiming uses file locking to prevent race conditions
- Going idle after every turn is normal - the system sends automatic idle notifications

**Resources are stored locally:**
- Team config: `~/.claude/teams/{team-name}/config.json`
- Task list: `~/.claude/tasks/{team-name}/`

**Display modes:**
- **In-process** (default): All teammates run in your main terminal
  - Use Shift+Up/Down to select a teammate
  - Type to message them directly
  - Press Enter to view their session, Escape to interrupt
  - Press Ctrl+T to toggle task list
- **Split panes**: Each teammate gets its own pane (requires tmux or iTerm2)
  - Click into a pane to interact with that teammate
  - See everyone's output simultaneously
  - Set `teammateMode: "in-process"` or `"tmux"` in ~/.claude/settings.json
  - Or use flag: `claude --teammate-mode in-process`

### Instructions for Teammate Agents

**If you are a teammate agent (spawned by a team lead), follow this protocol:**

#### Critical Context Understanding

**What you receive at spawn:**
- Your spawn message includes the team name, your role, and task assignment
- You automatically load project context: CLAUDE.md, MCP servers, and skills
- **You DO NOT inherit the lead's conversation history** - any context you need must be in your spawn prompt or gathered by you

**About idle state:**
- **Going idle after every turn is NORMAL and EXPECTED** - this does NOT mean you're done or broken
- The system automatically sends idle notifications to the team lead when your turn ends
- Being idle simply means you're waiting for new instructions or task assignments
- You will be woken up when you receive messages or new task assignments

#### 1. Startup Protocol
When you receive your spawn message with task assignment:
1. **Read your assigned task**: Use `TaskGet` to read full task details including description and dependencies
2. **Check blockers**: Use `TaskList` to see if your task has `blockedBy` dependencies
3. **Claim if unblocked**: If no blockers, use `TaskUpdate` to:
   - Set `status="in_progress"`
   - Set `owner` to your agent name (from spawn message)
4. **Report if blocked**: If blocked, use `SendMessage` to tell team-lead you're waiting for dependencies
5. **Gather context if needed**: If your spawn prompt lacks details, read relevant files or ask the lead for clarification

#### 2. Work Execution
- **Do the work**: Create files, write code, read documentation as needed for your task
- **Use all available tools**: Read, Write, Edit, Bash, Grep, Glob, Task subagents, etc.
- **Communicate using SendMessage**: Your plain text output is NOT visible to anyone
  - Send progress updates if your task is complex or long-running
  - Report blockers immediately - don't wait
  - Ask questions if requirements are unclear
- **DO NOT worry about going idle**: Going idle after completing work is normal and expected

#### 3. Completion Protocol
When you finish your task:
1. **Mark task complete**: Use `TaskUpdate(taskId="X", status="completed")`
2. **Report completion**: Use `SendMessage` with:
   - `type="message"`
   - `recipient="team-lead"` (or the lead's actual agent name)
   - `content`: Detailed summary of what you completed, where files were created, any issues encountered
   - `summary`: Brief 5-10 word preview (e.g., "Task #1 complete: OpenCypher spec documented")
3. **Check for more work**: Use `TaskList` to find newly unblocked tasks
4. **Claim next task or go idle**: If available work exists, claim it. Otherwise, go idle and wait.

**CRITICAL**: The system automatically notifies the lead when you go idle - you don't need to send a separate "I'm done" message.

#### 4. Communication Rules

**Your text output is NOT visible to the team lead or other teammates.**

To communicate, you **MUST** use the `SendMessage` tool:

- **type="message"**: Send to one specific teammate (most common)
  ```
  SendMessage(
    type="message",
    recipient="team-lead",
    content="Completed parser work. Found issue: grammar conflicts with OPTIONAL MATCH.",
    summary="Parser complete with issue found"
  )
  ```

- **type="broadcast"**: Send to ALL teammates (use sparingly - scales with team size)
  - Only use for critical issues affecting everyone
  - Examples: "blocking bug found, stop work" or "requirements changed"

**Message delivery is automatic**: You don't need to poll for messages - they arrive automatically as new conversation turns.

#### 5. Shutdown Protocol

When you receive a shutdown request (JSON message with `type="shutdown_request"`):

**You MUST respond using SendMessage** - do NOT just acknowledge in text:

```
SendMessage(
  type="shutdown_response",
  request_id="<requestId from the shutdown request>",
  approve=True  # or False with explanation in content field
)
```

- **approve=True**: You exit gracefully
- **approve=False**: You continue working - include `content` explaining why (e.g., "Still working on task #3, need 5 more minutes")

**Extracting requestId from shutdown request:**
The shutdown request arrives as a JSON message. Extract the `requestId` field and pass it as `request_id` to SendMessage:
```
Received: {"type": "shutdown_request", "requestId": "abc-123", ...}
Use: SendMessage(type="shutdown_response", request_id="abc-123", approve=True)
```

#### 7. Error Handling and Recovery

**When you encounter errors:**
- **DO NOT** give up and go idle immediately
- Try to fix the error (read error messages, check file paths, adjust approach)
- If blocked, use `SendMessage` to report the issue to team-lead with details
- The lead can give you guidance or reassign the task

**When you can't complete a task:**
- Create a new task describing the blocker: `TaskCreate(...)`
- Report to team-lead that you're blocked and why
- Either wait for the blocker to be resolved or ask for a different task

**Quality over speed:**
- Run tests before marking tasks complete
- If tests fail, fix them - don't mark the task done
- If implementation is partial, keep status as `in_progress`

#### 6. Example Workflow
```
1. RECEIVE spawn message:
   - Team: "graphforge-unwind-feature"
   - Your name: "spec-researcher"
   - Task assignment: "Task #1"
   - Context: "Research OpenCypher spec and create docs/reference/opencypher-spec-features.md"

2. READ task details:
   TaskGet(taskId="1")
   # Returns full description, blockedBy list, etc.

3. CHECK for blockers:
   TaskList()
   # Verify task #1 has empty blockedBy list

4. CLAIM the task:
   TaskUpdate(taskId="1", status="in_progress", owner="spec-researcher")

5. DO THE WORK:
   - Read existing docs to understand format
   - Research opencypher.org documentation
   - Create markdown file with comprehensive feature list
   - Organize by category (clauses, functions, operators, etc.)

6. MARK COMPLETE:
   TaskUpdate(taskId="1", status="completed")

7. REPORT to lead using SendMessage:
   SendMessage(
     type="message",
     recipient="team-lead",
     content="Completed task #1. Created docs/reference/opencypher-spec-features.md with 200+ OpenCypher features organized by category. Ready for next task.",
     summary="Task #1 complete: spec features documented"
   )

8. CHECK for more work:
   TaskList()
   # Look for newly unblocked tasks

9. CLAIM next task OR go idle:
   - If tasks available: Repeat from step 2
   - If no tasks: Go idle (system automatically notifies lead)
```

**Key principles:**
- **Take initiative**: Claim your task, do the work, report completion. Don't wait for permission.
- **Communicate explicitly**: The lead can't read your mind. Use SendMessage for all communication.
- **Going idle is normal**: After reporting completion, going idle is expected behavior, not an error.

### Instructions for Team Lead Agents

**If you are the team lead (the agent that created the team), follow this protocol:**

#### Team Lead Responsibilities

1. **Create clear tasks**: Break work into self-contained units with clear deliverables
   - Include ALL necessary context in task descriptions (teammates don't see your conversation history)
   - Specify dependencies between tasks (blockedBy)
   - Size appropriately: 5-6 tasks per teammate

2. **Spawn teammates with full context**: Include detailed instructions in spawn prompts
   - Specify exactly what files to modify and where
   - Include architectural context and constraints
   - Mention relevant patterns from CLAUDE.md

3. **Track progress actively**:
   - Messages from teammates arrive automatically (no polling needed)
   - Check `TaskList()` periodically to see task status
   - Redirect teammates if they're going off track

4. **Wait for teammates**: Don't implement tasks yourself unless explicitly intended
   - If you find yourself coding, ask: "Should a teammate do this?"
   - Consider using delegate mode (Shift+Tab) to restrict yourself to coordination only

5. **Handle idle notifications**: Teammates go idle after EVERY turn - this is normal
   - Idle doesn't mean "done" or "broken"
   - Check if they completed their task, then assign new work or acknowledge completion

6. **Synthesize results**: Collect findings from teammates and create coherent summary

7. **Clean up gracefully**:
   - Shut down all teammates first using shutdown requests:
     ```
     SendMessage(type="shutdown_request", recipient="parser-agent", content="Task complete, wrapping up")
     ```
   - Wait for shutdown confirmations (approve=True responses)
   - Then clean up team resources (removes ~/.claude/teams/ and ~/.claude/tasks/ for this team)
   - **CRITICAL**: Only the lead should clean up, not teammates
   - If cleanup fails, check for active teammates and shut them down first

8. **Use delegate mode for coordination-only**: Press Shift+Tab to cycle into delegate mode
   - Restricts you to coordination tools only (spawn, message, tasks, shutdown)
   - Prevents you from implementing tasks yourself
   - Useful when you want to focus purely on orchestration

#### Common Lead Mistakes to Avoid

- **Starting implementation too early**: Wait for teammates to report back
- **Insufficient spawn context**: Teammates can't read your mind or conversation history
- **Treating idle as an error**: Idle after every turn is expected behavior
- **Skipping cleanup**: Always clean up team resources when done

### When to Use Agent Teams (Team Lead Instructions)

**Ideal for teams:**
- Adding new Cypher features (parser, planner, executor work in parallel)
- Cross-layer refactoring
- Comprehensive testing (unit, integration, TCK in parallel)
- Multi-module features
- Code review from multiple perspectives
- Debugging with competing hypotheses

**NOT ideal for teams:**
- Single-file changes
- Simple bug fixes
- Sequential work with many dependencies
- Documentation-only changes

**Rule of thumb:** If teammates can work independently for 80%+ of the time, teams add value. Otherwise, solo work is faster.

### Team Best Practices

1. **Split by architectural layer** - GraphForge's 4-layer architecture (parser → planner → executor → storage) naturally supports parallel work
2. **Avoid file conflicts** - Use layer boundaries as natural file ownership. Two teammates editing the same file leads to overwrites.
3. **Give teammates full context** - Include ALL specifics in spawn prompts:
   - **Bad**: "Implement the parser"
   - **Good**: "Add UNWIND grammar to cypher.lark at line 42 after the WITH clause rule. Create UnwindClause AST node with 'expression' and 'alias' fields. Update parser.py transformer with unwind() method."
   - Remember: Teammates don't inherit lead's conversation history
4. **Size tasks appropriately**:
   - **Too small**: Coordination overhead exceeds benefit
   - **Too large**: Teammates work too long without check-ins
   - **Just right**: Self-contained units (function, test file, review) with clear deliverables
   - **Rule of thumb**: 5-6 tasks per teammate keeps everyone productive
5. **Token awareness** - Teams use ~2-3x more tokens but complete 2-3x faster
6. **Monitor and steer** - Check in on teammates' progress, redirect approaches that aren't working
7. **Wait for teammates** - If the lead starts implementing tasks itself, remind it to wait for teammates to complete their work

**Example spawn prompt:**
```
Create an agent team to implement UNWIND (#42). Spawn teammates:
- parser-agent: Add UNWIND grammar rule to cypher.lark after the WITH clause.
  Create UnwindClause AST node with expression and alias fields. Update
  parser.py transformer with unwind() method that returns UnwindClause.
- planner-agent: Add Unwind operator to operators.py with expression and alias
  fields. Update planner.py to emit Unwind operator when it sees UnwindClause.
- executor-agent: Implement _execute_unwind() in executor.py that evaluates
  the expression, iterates the resulting list, and binds each element to the
  alias. Add 15 unit tests + 8 integration tests.

Each works independently on their layer. Task dependencies: parser → planner → executor.
```

### Troubleshooting Agent Teams

**Teammates not doing work / going idle immediately:**
- This is NORMAL behavior after completing tasks
- Check task list with `TaskList()` to see if tasks are actually complete
- If a task appears stuck, check whether the work is actually done
- If yes, manually mark as complete: `TaskUpdate(taskId="X", status="completed")`

**Teammates not communicating:**
- Reminder: Teammates' plain text output is NOT visible to the lead
- Teammates must use `SendMessage` tool explicitly
- If you're a teammate and the lead isn't responding, check that you actually called `SendMessage` (don't just type text)

**Lead implementing tasks instead of delegating:**
- Tell the lead: "Wait for your teammates to complete their tasks before proceeding"
- Consider using delegate mode (Shift+Tab to cycle modes)

**Task claiming race conditions:**
- The system uses file locking to prevent race conditions
- If two teammates try to claim the same task, only one succeeds
- The other gets an error and should claim a different task

**Orphaned resources after team ends:**
- Always use the lead to clean up, not teammates
- Shut down all teammates first, then call team cleanup
- If cleanup fails due to active teammates, manually shut them down and retry

**Context limitations:**
- Teammates don't inherit the lead's conversation history
- Include ALL necessary context in spawn prompts
- Teammates can read CLAUDE.md, which provides project context automatically

### Known Limitations

Agent teams are experimental. Be aware of these limitations:

1. **No session resumption with in-process teammates**: `/resume` and `/rewind` don't restore teammates
   - After resuming, the lead may try to message teammates that no longer exist
   - Solution: Tell the lead to spawn new teammates

2. **Task status can lag**: Teammates sometimes forget to mark tasks as completed
   - Blocks dependent tasks unnecessarily
   - Solution: Manually update task status or remind the teammate

3. **Shutdown can be slow**: Teammates finish their current request before shutting down

4. **One team per session**: Clean up current team before starting a new one

5. **No nested teams**: Only the lead can spawn teammates (teammates can't create sub-teams)

6. **Lead is fixed**: Can't transfer leadership or promote a teammate to lead

7. **Permissions set at spawn**: All teammates inherit lead's permission mode at creation
   - Can change individual modes after spawning
   - Can't set per-teammate modes at spawn time

8. **Display mode limitations**:
   - In-process mode: Works in any terminal
   - Split panes: Requires tmux or iTerm2 (not supported in VS Code, Windows Terminal, or Ghostty)

### Quick Reference: Key Tools and Commands

**For Teammates:**
```python
# Read task details
TaskGet(taskId="1")

# Check all tasks and their status
TaskList()

# Claim a task
TaskUpdate(taskId="1", status="in_progress", owner="your-agent-name")

# Mark task complete
TaskUpdate(taskId="1", status="completed")

# Send message to lead
SendMessage(
  type="message",
  recipient="team-lead",
  content="Detailed message here",
  summary="Brief 5-10 word summary"
)

# Respond to shutdown request
SendMessage(
  type="shutdown_response",
  request_id="abc-123",  # Extract from shutdown request
  approve=True  # or False with content explaining why
)
```

**For Team Lead:**
```python
# Create task
TaskCreate(
  subject="Brief title",
  description="Detailed description with context",
  activeForm="Present continuous (e.g., 'Implementing parser')"
)

# Assign task
TaskUpdate(taskId="1", owner="parser-agent")

# Request teammate shutdown
SendMessage(
  type="shutdown_request",
  recipient="parser-agent",
  content="Task complete, wrapping up the session"
)

# Read team member roster
# Use Read tool on: ~/.claude/teams/{team-name}/config.json
```

**Remember:**
- Teammates: Your text output is NOT visible - ALWAYS use SendMessage
- Going idle after every turn is NORMAL - not an error
- Team lead: Wait for teammates, don't implement tasks yourself
- Everyone: Include full context in messages (no shared conversation history)

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
- 1-2 layers affected: Use solo workflow
- 3-4 layers affected: Consider agent team
- Extensive tests needed: Use agent team
- New to feature: Use solo workflow

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

**Sequential (solo):**
1. Grammar: Add to `cypher.lark`
2. AST: Add dataclass to `ast/clause.py`
3. Transformer: Add method to `parser.py`
4. Planner: Update to emit operator
5. Operator: Add to `operators.py`
6. Executor: Implement execution
7. Tests: Unit + integration tests

**Parallel (team):**
```
Create agent team for WITH clause (#47):
- parser-agent: Grammar + AST + transformer
- planner-agent: Operator definition + planning logic
- executor-agent: Execution + tests
```

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
5. **Right tool for the task** - Use agent teams for parallel work, solo for sequential

**Not goals:** High throughput, massive graphs, production deployment

## Agent Teams vs Solo: Decision Framework

**Use agent teams when:**
- Work parallelizes across GraphForge's 4 layers
- Multiple perspectives add value (review, research)
- Different teammates own different files/modules
- Comprehensive test suites need parallel development
- Time-to-completion matters and parallel work is faster

**Use solo workflow when:**
- Single file or single layer changes
- Sequential work with cross-layer dependencies
- Simple bug fixes or maintenance
- Learning a new area of the codebase
- Token cost matters more than speed

**Token cost awareness:**
- Solo workflow: ~50K tokens (sequential)
- Team workflow: ~120K tokens (parallel, 2-3x faster)

**GraphForge's architecture enables teams:**
- Clear interfaces (AST, operators, results)
- Minimal coupling between layers
- File ownership (separate directories)
- Independent testing (unit tests per layer)
- Natural parallelism (4 layers = 4 teammates)

**Start simple, scale to teams:**
1. Start with solo workflow to learn architecture
2. Try team-based code review (low risk, high value)
3. Graduate to team-based feature implementation
4. Use teams routinely for multi-layer work

**Remember:** Agent teams are a tool, not a requirement. Choose based on task structure, not habit.
