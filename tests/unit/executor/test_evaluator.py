"""Tests for expression evaluator.

Tests cover evaluation of AST expressions in an execution context.
"""

import pytest

from graphforge.ast.expression import BinaryOp, Literal, PropertyAccess, Variable
from graphforge.executor.evaluator import ExecutionContext, evaluate_expression
from graphforge.types.graph import NodeRef
from graphforge.types.values import CypherBool, CypherInt, CypherNull, CypherString


@pytest.mark.unit
class TestLiteralEvaluation:
    """Tests for evaluating literals."""

    def test_evaluate_int_literal(self):
        """Evaluate integer literal."""
        expr = Literal(42)
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 42

    def test_evaluate_string_literal(self):
        """Evaluate string literal."""
        expr = Literal("hello")
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherString)
        assert result.value == "hello"

    def test_evaluate_null_literal(self):
        """Evaluate null literal."""
        expr = Literal(None)
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)


@pytest.mark.unit
class TestVariableEvaluation:
    """Tests for evaluating variables."""

    def test_evaluate_variable(self):
        """Evaluate variable from context."""
        node = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        ctx = ExecutionContext()
        ctx.bind("n", node)

        expr = Variable("n")
        result = evaluate_expression(expr, ctx)

        assert result == node

    def test_evaluate_undefined_variable(self):
        """Evaluating undefined variable raises error."""
        ctx = ExecutionContext()
        expr = Variable("x")

        with pytest.raises(KeyError):
            evaluate_expression(expr, ctx)


@pytest.mark.unit
class TestPropertyAccess:
    """Tests for evaluating property access."""

    def test_evaluate_property_access(self):
        """Evaluate property access."""
        node = NodeRef(
            id=1,
            labels=frozenset(["Person"]),
            properties={"name": CypherString("Alice")},
        )
        ctx = ExecutionContext()
        ctx.bind("n", node)

        expr = PropertyAccess(variable="n", property="name")
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherString)
        assert result.value == "Alice"

    def test_property_access_missing_property(self):
        """Property access returns null for missing property."""
        node = NodeRef(id=1, labels=frozenset(), properties={})
        ctx = ExecutionContext()
        ctx.bind("n", node)

        expr = PropertyAccess(variable="n", property="missing")
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)


@pytest.mark.unit
class TestComparisonOperations:
    """Tests for comparison operations."""

    def test_greater_than(self):
        """Evaluate greater than comparison."""
        ctx = ExecutionContext()
        expr = BinaryOp(op=">", left=Literal(10), right=Literal(5))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_less_than(self):
        """Evaluate less than comparison."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="<", left=Literal(5), right=Literal(10))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_equals(self):
        """Evaluate equals comparison."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="=", left=Literal(5), right=Literal(5))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_not_equals(self):
        """Evaluate not equals comparison."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="<>", left=Literal(5), right=Literal(10))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True


@pytest.mark.unit
class TestLogicalOperations:
    """Tests for logical operations."""

    def test_and_true_true(self):
        """AND with both true."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="AND", left=Literal(True), right=Literal(True))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_and_true_false(self):
        """AND with one false."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="AND", left=Literal(True), right=Literal(False))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_or_false_true(self):
        """OR with one true."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="OR", left=Literal(False), right=Literal(True))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True


@pytest.mark.unit
class TestNullPropagation:
    """Tests for NULL propagation in operations."""

    def test_null_comparison(self):
        """Comparing NULL returns NULL."""
        ctx = ExecutionContext()
        expr = BinaryOp(op=">", left=Literal(None), right=Literal(10))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_null_and_true(self):
        """NULL AND true returns NULL."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="AND", left=Literal(None), right=Literal(True))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)


@pytest.mark.unit
class TestComplexExpressions:
    """Tests for complex nested expressions."""

    def test_property_comparison(self):
        """Evaluate property comparison."""
        node = NodeRef(id=1, labels=frozenset(), properties={"age": CypherInt(35)})
        ctx = ExecutionContext()
        ctx.bind("n", node)

        expr = BinaryOp(
            op=">",
            left=PropertyAccess(variable="n", property="age"),
            right=Literal(30),
        )
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_nested_logical_expression(self):
        """Evaluate nested AND/OR."""
        ctx = ExecutionContext()
        # (10 > 5) AND (20 < 30)
        expr = BinaryOp(
            op="AND",
            left=BinaryOp(op=">", left=Literal(10), right=Literal(5)),
            right=BinaryOp(op="<", left=Literal(20), right=Literal(30)),
        )
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True
