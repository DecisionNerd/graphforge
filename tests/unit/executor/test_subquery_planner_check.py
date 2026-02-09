"""Unit tests for subquery planner null checks."""

import pytest

from graphforge.ast.expression import SubqueryExpression
from graphforge.ast.query import CypherQuery
from graphforge.executor.evaluator import ExecutionContext, evaluate_expression


class TestSubqueryPlannerCheck:
    """Test that subquery expressions validate executor.planner exists."""

    def test_subquery_without_executor_raises_error(self):
        """Test subquery expression without executor raises TypeError."""
        ctx = ExecutionContext()

        # Create a minimal subquery expression
        subquery = SubqueryExpression(
            type="EXISTS", query=CypherQuery(clauses=[])  # type: ignore[arg-type]
        )

        with pytest.raises(TypeError, match="Subquery expressions require executor parameter"):
            evaluate_expression(subquery, ctx, executor=None)

    def test_subquery_without_planner_raises_error(self):
        """Test subquery expression without executor.planner raises TypeError."""
        ctx = ExecutionContext()

        # Create a minimal executor mock without planner
        class MockExecutor:
            planner = None

        executor = MockExecutor()

        subquery = SubqueryExpression(
            type="EXISTS", query=CypherQuery(clauses=[])  # type: ignore[arg-type]
        )

        with pytest.raises(
            TypeError, match="Subquery expressions require executor with planner configured"
        ):
            evaluate_expression(subquery, ctx, executor=executor)
