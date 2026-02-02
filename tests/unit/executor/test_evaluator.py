"""Tests for expression evaluator.

Tests cover evaluation of AST expressions in an execution context.
"""

import pytest

from graphforge.ast.expression import BinaryOp, FunctionCall, Literal, PropertyAccess, Variable
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


@pytest.mark.unit
class TestFunctionCalls:
    """Tests for function call evaluation."""

    def test_coalesce_returns_first_non_null(self):
        """COALESCE returns first non-NULL value."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="COALESCE",
            args=[Literal(None), Literal(42), Literal(100)],
        )
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 42

    def test_coalesce_all_null(self):
        """COALESCE with all NULL returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="COALESCE",
            args=[Literal(None), Literal(None)],
        )
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_coalesce_no_null(self):
        """COALESCE returns first value when none are NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="COALESCE",
            args=[Literal("first"), Literal("second")],
        )
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherString)
        assert result.value == "first"

    def test_function_null_propagation(self):
        """Regular functions propagate NULL."""
        ctx = ExecutionContext()
        # LENGTH(NULL) should return NULL
        expr = FunctionCall(
            name="LENGTH",
            args=[Literal(None)],
        )
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_unknown_function_raises_error(self):
        """Unknown function raises ValueError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="UNKNOWN_FUNC",
            args=[Literal(42)],
        )

        with pytest.raises(ValueError, match="Unknown function"):
            evaluate_expression(expr, ctx)

    def test_function_with_property_access(self):
        """Function can evaluate property access arguments."""
        node = NodeRef(id=1, labels=frozenset(), properties={"name": CypherString("Alice")})
        ctx = ExecutionContext()
        ctx.bind("n", node)

        # COALESCE(n.missing, n.name) should return "Alice"
        expr = FunctionCall(
            name="COALESCE",
            args=[
                PropertyAccess(variable="n", property="missing"),
                PropertyAccess(variable="n", property="name"),
            ],
        )
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherString)
        assert result.value == "Alice"

    def test_string_function_length(self):
        """LENGTH string function returns string length."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LENGTH",
            args=[Literal("test")],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 4

    def test_to_integer_from_string(self):
        """toInteger converts string to integer."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toInteger",
            args=[Literal("42")],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 42

    def test_to_float_from_string(self):
        """toFloat converts string to float."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toFloat",
            args=[Literal("3.14")],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherFloat

        assert isinstance(result, CypherFloat)
        assert abs(result.value - 3.14) < 0.001

    def test_to_string_from_integer(self):
        """toString converts integer to string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toString",
            args=[Literal(42)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "42"

    def test_to_integer_invalid_string_returns_null(self):
        """toInteger with invalid string returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toInteger",
            args=[Literal("not a number")],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_to_float_invalid_string_returns_null(self):
        """toFloat with invalid string returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toFloat",
            args=[Literal("not a number")],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_to_integer_from_boolean_true(self):
        """toInteger converts True to 1."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toInteger",
            args=[Literal(True)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 1

    def test_to_integer_from_boolean_false(self):
        """toInteger converts False to 0."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toInteger",
            args=[Literal(False)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 0

    def test_to_float_from_boolean_true(self):
        """toFloat converts True to 1.0."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toFloat",
            args=[Literal(True)],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherFloat

        assert isinstance(result, CypherFloat)
        assert abs(result.value - 1.0) < 0.001

    def test_to_float_from_boolean_false(self):
        """toFloat converts False to 0.0."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toFloat",
            args=[Literal(False)],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherFloat

        assert isinstance(result, CypherFloat)
        assert abs(result.value - 0.0) < 0.001

    def test_to_string_from_boolean_true(self):
        """toString converts True to 'true'."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toString",
            args=[Literal(True)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "true"

    def test_to_string_from_boolean_false(self):
        """toString converts False to 'false'."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toString",
            args=[Literal(False)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "false"

    def test_to_string_from_float(self):
        """toString converts float to string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toString",
            args=[Literal(3.14)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "3.14"

    def test_type_function_returns_type_name(self):
        """type() function returns type name."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="type",
            args=[Literal("hello")],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "String"

    def test_to_integer_with_null_returns_null(self):
        """toInteger with NULL returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toInteger",
            args=[Literal(None)],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_to_float_with_null_returns_null(self):
        """toFloat with NULL returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toFloat",
            args=[Literal(None)],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_to_string_with_null_returns_null(self):
        """toString with NULL returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toString",
            args=[Literal(None)],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_substring_negative_start_raises_error(self):
        """SUBSTRING with negative start raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SUBSTRING",
            args=[Literal("hello"), Literal(-1)],
        )

        with pytest.raises(TypeError, match="SUBSTRING start must be non-negative"):
            evaluate_expression(expr, ctx)

    def test_substring_negative_length_raises_error(self):
        """SUBSTRING with negative length raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SUBSTRING",
            args=[Literal("hello"), Literal(0), Literal(-1)],
        )

        with pytest.raises(TypeError, match="SUBSTRING length must be non-negative"):
            evaluate_expression(expr, ctx)

    def test_length_with_non_string_raises_error(self):
        """LENGTH with non-string raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LENGTH",
            args=[Literal(123)],
        )

        with pytest.raises(TypeError, match="LENGTH expects string"):
            evaluate_expression(expr, ctx)

    def test_substring_with_non_string_raises_error(self):
        """SUBSTRING with non-string raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SUBSTRING",
            args=[Literal(123), Literal(0)],
        )

        with pytest.raises(TypeError, match="SUBSTRING expects string"):
            evaluate_expression(expr, ctx)

    def test_substring_with_non_integer_start_raises_error(self):
        """SUBSTRING with non-integer start raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SUBSTRING",
            args=[Literal("hello"), Literal("0")],
        )

        with pytest.raises(TypeError, match="SUBSTRING start must be integer"):
            evaluate_expression(expr, ctx)

    def test_substring_with_non_integer_length_raises_error(self):
        """SUBSTRING with non-integer length raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SUBSTRING",
            args=[Literal("hello"), Literal(0), Literal("2")],
        )

        with pytest.raises(TypeError, match="SUBSTRING length must be integer"):
            evaluate_expression(expr, ctx)

    def test_upper_with_non_string_raises_error(self):
        """UPPER with non-string raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="UPPER",
            args=[Literal(123)],
        )

        with pytest.raises(TypeError, match="UPPER expects string"):
            evaluate_expression(expr, ctx)

    def test_lower_with_non_string_raises_error(self):
        """LOWER with non-string raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LOWER",
            args=[Literal(123)],
        )

        with pytest.raises(TypeError, match="LOWER expects string"):
            evaluate_expression(expr, ctx)

    def test_trim_with_non_string_raises_error(self):
        """TRIM with non-string raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="TRIM",
            args=[Literal(123)],
        )

        with pytest.raises(TypeError, match="TRIM expects string"):
            evaluate_expression(expr, ctx)
