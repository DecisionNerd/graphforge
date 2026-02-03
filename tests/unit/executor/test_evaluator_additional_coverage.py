"""Additional evaluator tests for remaining coverage gaps.

Tests for specific uncovered lines in evaluator.py.
"""


from graphforge.ast.expression import BinaryOp, FunctionCall, Variable
from graphforge.executor.evaluator import ExecutionContext, evaluate_expression
from graphforge.types.values import CypherInt, CypherNull, CypherString


class TestEvaluatorAdditionalCoverage:
    """Tests for remaining evaluator coverage gaps."""

    def test_not_equals_with_null_propagation(self):
        """<> operator with NULL comparison returns NULL."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherInt(5))
        ctx.bind("y", CypherNull())

        # x <> NULL should return NULL (not true or false)
        ne_expr = BinaryOp(op="<>", left=Variable(name="x"), right=Variable(name="y"))
        result = evaluate_expression(ne_expr, ctx)

        assert isinstance(result, CypherNull)

    def test_not_equals_with_both_null(self):
        """<> operator with NULL <> NULL returns NULL."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherNull())
        ctx.bind("y", CypherNull())

        # NULL <> NULL should return NULL
        ne_expr = BinaryOp(op="<>", left=Variable(name="x"), right=Variable(name="y"))
        result = evaluate_expression(ne_expr, ctx)

        assert isinstance(result, CypherNull)

    def test_tointeger_with_null_returns_null(self):
        """toInteger(NULL) returns NULL."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherNull())

        # toInteger(NULL) -> NULL
        func = FunctionCall(name="toInteger", args=[Variable(name="x")], distinct=False)
        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherNull)

    def test_tofloat_with_null_returns_null(self):
        """toFloat(NULL) returns NULL."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherNull())

        # toFloat(NULL) -> NULL
        func = FunctionCall(name="toFloat", args=[Variable(name="x")], distinct=False)
        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherNull)

    def test_tostring_with_null_returns_null(self):
        """toString(NULL) returns NULL."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherNull())

        # toString(NULL) -> NULL
        func = FunctionCall(name="toString", args=[Variable(name="x")], distinct=False)
        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherNull)

    def test_not_equals_with_different_values_returns_true(self):
        """<> operator with different values returns true."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherInt(5))
        ctx.bind("y", CypherInt(10))

        # 5 <> 10 should return true
        ne_expr = BinaryOp(op="<>", left=Variable(name="x"), right=Variable(name="y"))
        result = evaluate_expression(ne_expr, ctx)

        assert result.value is True

    def test_not_equals_with_same_values_returns_false(self):
        """<> operator with same values returns false."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherString("hello"))
        ctx.bind("y", CypherString("hello"))

        # "hello" <> "hello" should return false
        ne_expr = BinaryOp(op="<>", left=Variable(name="x"), right=Variable(name="y"))
        result = evaluate_expression(ne_expr, ctx)

        assert result.value is False
