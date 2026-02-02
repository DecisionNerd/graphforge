# GitHub Issue Workflow for GraphForge v0.2

This document describes the issue-branch-PR workflow for GraphForge v0.2 development.

## Created Issues

### v0.2.0 Issues (Core Cypher Complete)

The following issues target the [v0.2.0 milestone](https://github.com/DecisionNerd/graphforge/milestone/1):

- [#20](https://github.com/DecisionNerd/graphforge/issues/20) - `feat: implement UNWIND clause for list iteration` (good first issue, 2-3h)
- [#21](https://github.com/DecisionNerd/graphforge/issues/21) - `feat: implement DETACH DELETE for cascading deletion` (1-2h)
- [#22](https://github.com/DecisionNerd/graphforge/issues/22) - `feat: implement CASE expressions for conditional logic` (complex, 4-5h)
- [#23](https://github.com/DecisionNerd/graphforge/issues/23) - `feat: formalize and test MATCH-CREATE combinations` (testing, 3-4h)
- [#25](https://github.com/DecisionNerd/graphforge/issues/25) - `feat: implement REMOVE clause for property/label removal` (2h)
- [#26](https://github.com/DecisionNerd/graphforge/issues/26) - `feat: implement arithmetic operators (+, -, *, /, %)` (2-3h)
- [#27](https://github.com/DecisionNerd/graphforge/issues/27) - `feat: implement COLLECT aggregation function` (3-4h)
- [#28](https://github.com/DecisionNerd/graphforge/issues/28) - `feat: implement string matching operators (STARTS WITH, ENDS WITH, CONTAINS)` (2-3h)
- [#29](https://github.com/DecisionNerd/graphforge/issues/29) - `feat: implement NOT logical operator` (1-2h)

**Total Effort:** 20-28 hours
**Target:** ~950 TCK scenarios (~25% compliance)

### v0.3.0 Issues (Advanced Patterns)

The following issues target the [v0.3.0 milestone](https://github.com/DecisionNerd/graphforge/milestone/2):

- [#24](https://github.com/DecisionNerd/graphforge/issues/24) - `feat: implement path expressions and variable-length patterns` (complex, 10-15h)

Additional v0.3 issues to be created:
- OPTIONAL MATCH (left outer joins)
- List comprehensions
- Subqueries (EXISTS, COUNT)
- UNION / UNION ALL

## Recommended Implementation Order

Based on complexity, dependencies, and user value:

### Quick Wins (Start Here)
1. **NOT operator (#29)** - 1-2h, simple operator, enables many queries
2. **DETACH DELETE (#21)** - 1-2h, small change, high user value
3. **REMOVE clause (#25)** - 2h, straightforward implementation
4. **String matching (#28)** - 2-3h, very common in WHERE clauses

### Core Features
5. **UNWIND (#20)** - 2-3h, good first issue, validates workflow
6. **Arithmetic operators (#26)** - 2-3h, fundamental operators
7. **COLLECT aggregation (#27)** - 3-4h, most requested after basic aggregations

### Complex Features
8. **MATCH-CREATE (#23)** - 3-4h, already works, needs comprehensive tests
9. **CASE expressions (#22)** - 4-5h, complex but commonly requested

### v0.3 (Deferred)
10. **Path expressions (#24)** - 10-15h, deferred to v0.3 for focus on breadth in v0.2

## Workflow: Issue → Branch → PR → Merge

### 1. Starting Work on an Issue

```bash
# Example: Starting work on UNWIND (issue #20)
git checkout main
git pull origin main
git checkout -b feature/20-unwind-clause

# Work on the feature following the implementation checklist in the issue...
```

### 2. Branch Naming Convention

```
feature/{issue-number}-{slug}

Examples:
- feature/20-unwind-clause
- feature/21-detach-delete
- feature/22-case-expressions
- feature/23-match-create
- feature/24-path-expressions
```

### 3. Commit Messages

Reference the issue in your commit messages:

```bash
git commit -m "feat: add UNWIND grammar and AST

Implements basic UNWIND clause structure with grammar rules
and AST nodes for representing UNWIND operations.

Part of #20"
```

For the final commit that completes the feature:

```bash
git commit -m "feat: implement UNWIND clause

Implements list iteration with UNWIND clause, including:
- Grammar rules for UNWIND syntax
- AST nodes and parser transformations
- Executor implementation
- Comprehensive test suite

Fixes #20

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

### 4. Creating a Pull Request

Push your branch and create a PR:

```bash
# Push the branch
git push -u origin feature/20-unwind-clause

# Create PR with automatic issue linking
gh pr create \
  --title "feat: implement UNWIND clause for list iteration" \
  --body "Closes #20

## Summary
- Implements UNWIND clause for list iteration
- Adds grammar, AST, parser, and executor support
- Includes comprehensive test suite (13 tests)
- Maintains >85% code coverage

## Testing
- Unit tests: Parser validation (5 tests)
- Integration tests: End-to-end scenarios (8 tests)
- All existing tests pass

## Checklist
- [x] Grammar updates
- [x] AST nodes
- [x] Parser transformer
- [x] Executor implementation
- [x] Unit tests
- [x] Integration tests
- [x] Documentation updated
- [x] CHANGELOG updated" \
  --label "enhancement,v0.2"
```

### 5. Automatic Linking

Using `Fixes #20` or `Closes #20` in the PR description will:
- Automatically link the PR to the issue
- Close the issue when the PR is merged
- Update the milestone progress

## Labels Reference

- `enhancement` - New feature or request
- `v0.2` - Target for v0.2 release
- `good first issue` - Good for newcomers
- `complex` - Requires deep understanding
- `testing` - Testing and test improvements
- `future` - Future consideration
- `parser` - Changes to Cypher parser
- `executor` - Changes to query executor
- `planner` - Changes to query planner
- `tests` - Test suite changes

## Issue Structure

Each issue includes:

1. **Feature Description** - Brief user-facing description
2. **Use Case** - Why users need this feature
3. **Cypher Syntax** - Example queries
4. **Implementation Checklist** - Step-by-step tasks
5. **Files to Modify** - Specific file paths and line numbers
6. **Implementation Pattern** - Code examples
7. **Testing Strategy** - Unit and integration test scenarios
8. **Acceptance Criteria** - Must-have requirements
9. **References** - Links to specs and documentation
10. **Estimated Effort** - Time estimate

## Development Tips

- Start with the simpler issues (UNWIND, DETACH DELETE) to validate the workflow
- Follow the implementation checklist in each issue
- Maintain test coverage >85%
- Update both README.md and CHANGELOG.md
- Run the full test suite before creating a PR
- Use the CI/CD pipeline to catch issues early

## Milestone Progress

Track progress at: https://github.com/DecisionNerd/graphforge/milestone/1

## Questions?

If you have questions about any issue:
1. Comment on the issue to discuss the approach
2. Tag @DecisionNerd for clarification
3. Reference related issues or Neo4j documentation
