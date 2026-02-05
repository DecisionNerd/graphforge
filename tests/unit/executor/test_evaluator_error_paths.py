"""Unit tests for evaluator error handling paths.

Tests for defensive error handling in expression evaluation.
"""

import pytest

from graphforge.ast.expression import BinaryOp, FunctionCall, PropertyAccess, UnaryOp, Variable
from graphforge.executor.evaluator import ExecutionContext, evaluate_expression
from graphforge.types.values import CypherInt, CypherNull, CypherString


class TestEvaluatorErrorPaths:
    """Tests for evaluator error handling."""

    def test_has_method_on_context(self):
        """ExecutionContext.has() checks if variable exists."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherInt(5))

        assert ctx.has("x") is True
        assert ctx.has("y") is False

    def test_not_operator_with_non_boolean(self):
        """NOT operator with non-boolean operand raises TypeError."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherInt(5))

        # NOT requires boolean operand
        not_expr = UnaryOp(op="NOT", operand=Variable(name="x"))

        with pytest.raises(TypeError, match="NOT requires boolean operand"):
            evaluate_expression(not_expr, ctx)

    def test_unknown_unary_operator(self):
        """Unknown unary operator is rejected by Pydantic validation."""
        from pydantic import ValidationError

        # Pydantic now validates operators at construction time
        with pytest.raises(ValidationError, match="Unsupported unary operator"):
            UnaryOp(op="UNKNOWN_OP", operand=Variable(name="x"))

    def test_and_operator_with_non_boolean(self):
        """AND operator with non-boolean operands raises TypeError."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherInt(5))
        ctx.bind("y", CypherInt(10))

        # AND with non-boolean operands
        and_expr = BinaryOp(op="AND", left=Variable(name="x"), right=Variable(name="y"))

        with pytest.raises(TypeError, match="AND requires boolean operands"):
            evaluate_expression(and_expr, ctx)

    def test_or_operator_with_non_boolean(self):
        """OR operator with non-boolean operands raises TypeError."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherInt(5))
        ctx.bind("y", CypherInt(10))

        # OR with non-boolean operands
        or_expr = BinaryOp(op="OR", left=Variable(name="x"), right=Variable(name="y"))

        with pytest.raises(TypeError, match="OR requires boolean operands"):
            evaluate_expression(or_expr, ctx)

    def test_unknown_binary_operator(self):
        """Unknown binary operator is rejected by Pydantic validation."""
        from pydantic import ValidationError

        from graphforge.ast.expression import Literal

        # Pydantic now validates operators at construction time
        with pytest.raises(ValidationError, match="Unsupported binary operator"):
            BinaryOp(op="UNKNOWN_OP", left=Literal(value=1), right=Literal(value=2))

    def test_unknown_expression_type(self):
        """Unknown expression type raises TypeError."""
        ctx = ExecutionContext()

        # Create a fake expression type
        class FakeExpression:
            pass

        fake_expr = FakeExpression()

        with pytest.raises(TypeError, match="Cannot evaluate expression type"):
            evaluate_expression(fake_expr, ctx)

    def test_unknown_string_function(self):
        """Unknown string function raises ValueError."""
        ctx = ExecutionContext()
        ctx.bind("s", CypherString("hello"))

        # Unknown string function
        unknown_func = FunctionCall(
            name="UNKNOWN_STRING_FUNC", args=[Variable(name="s")], distinct=False
        )

        with pytest.raises(ValueError, match="Unknown function"):
            evaluate_expression(unknown_func, ctx)

    def test_unknown_type_function(self):
        """Unknown type conversion function raises ValueError."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherInt(5))

        # Unknown type function (not toInteger, toFloat, toString)
        unknown_func = FunctionCall(name="toUnknown", args=[Variable(name="x")], distinct=False)

        with pytest.raises(ValueError, match="Unknown function"):
            evaluate_expression(unknown_func, ctx)

    def test_property_access_on_cypher_value(self):
        """Property access on plain CypherValue (not Node/Edge) raises TypeError."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherInt(5))

        # Try to access property on a CypherInt
        prop_access = PropertyAccess(variable="x", property="some_prop")

        with pytest.raises(TypeError, match="Cannot access property on"):
            evaluate_expression(prop_access, ctx)

    def test_greater_than_with_null_returns_null(self):
        """Greater than comparison with NULL returns NULL (branch coverage)."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherInt(5))
        ctx.bind("y", CypherNull())

        # Greater than with NULL
        gt_expr = BinaryOp(op=">", left=Variable(name="x"), right=Variable(name="y"))
        result = evaluate_expression(gt_expr, ctx)

        assert isinstance(result, CypherNull)

    def test_less_than_or_equal_with_null_returns_null(self):
        """Less than or equal with NULL returns NULL (branch coverage)."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherInt(5))
        ctx.bind("y", CypherNull())

        # <= with NULL
        lte_expr = BinaryOp(op="<=", left=Variable(name="x"), right=Variable(name="y"))
        result = evaluate_expression(lte_expr, ctx)

        assert isinstance(result, CypherNull)

    def test_greater_than_or_equal_with_null_returns_null(self):
        """Greater than or equal with NULL returns NULL (branch coverage)."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherInt(5))
        ctx.bind("y", CypherNull())

        # >= with NULL
        gte_expr = BinaryOp(op=">=", left=Variable(name="x"), right=Variable(name="y"))
        result = evaluate_expression(gte_expr, ctx)

        assert isinstance(result, CypherNull)
