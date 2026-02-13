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
        expr = Literal(value=42)
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 42

    def test_evaluate_string_literal(self):
        """Evaluate string literal."""
        expr = Literal(value="hello")
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherString)
        assert result.value == "hello"

    def test_evaluate_null_literal(self):
        """Evaluate null literal."""
        expr = Literal(value=None)
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

        expr = Variable(name="n")
        result = evaluate_expression(expr, ctx)

        assert result == node

    def test_evaluate_undefined_variable(self):
        """Evaluating undefined variable raises error."""
        ctx = ExecutionContext()
        expr = Variable(name="x")

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
        expr = BinaryOp(op=">", left=Literal(value=10), right=Literal(value=5))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_less_than(self):
        """Evaluate less than comparison."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="<", left=Literal(value=5), right=Literal(value=10))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_equals(self):
        """Evaluate equals comparison."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="=", left=Literal(value=5), right=Literal(value=5))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_not_equals(self):
        """Evaluate not equals comparison."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="<>", left=Literal(value=5), right=Literal(value=10))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True


@pytest.mark.unit
class TestLogicalOperations:
    """Tests for logical operations."""

    def test_and_true_true(self):
        """AND with both true."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="AND", left=Literal(value=True), right=Literal(value=True))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_and_true_false(self):
        """AND with one false."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="AND", left=Literal(value=True), right=Literal(value=False))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_or_false_true(self):
        """OR with one true."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="OR", left=Literal(value=False), right=Literal(value=True))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True


@pytest.mark.unit
class TestNullPropagation:
    """Tests for NULL propagation in operations."""

    def test_null_comparison(self):
        """Comparing NULL returns NULL."""
        ctx = ExecutionContext()
        expr = BinaryOp(op=">", left=Literal(value=None), right=Literal(value=10))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_null_and_true(self):
        """NULL AND true returns NULL."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="AND", left=Literal(value=None), right=Literal(value=True))
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
            right=Literal(value=30),
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
            left=BinaryOp(op=">", left=Literal(value=10), right=Literal(value=5)),
            right=BinaryOp(op="<", left=Literal(value=20), right=Literal(value=30)),
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
            args=[Literal(value=None), Literal(value=42), Literal(value=100)],
        )
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 42

    def test_coalesce_all_null(self):
        """COALESCE with all NULL returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="COALESCE",
            args=[Literal(value=None), Literal(value=None)],
        )
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_coalesce_no_null(self):
        """COALESCE returns first value when none are NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="COALESCE",
            args=[Literal(value="first"), Literal(value="second")],
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
            args=[Literal(value=None)],
        )
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_unknown_function_raises_error(self):
        """Unknown function raises ValueError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="UNKNOWN_FUNC",
            args=[Literal(value=42)],
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
            args=[Literal(value="test")],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 4

    def test_to_integer_from_string(self):
        """toInteger converts string to integer."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toInteger",
            args=[Literal(value="42")],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 42

    def test_to_float_from_string(self):
        """toFloat converts string to float."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toFloat",
            args=[Literal(value="3.14")],
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
            args=[Literal(value=42)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "42"

    def test_to_integer_invalid_string_returns_null(self):
        """toInteger with invalid string returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toInteger",
            args=[Literal(value="not a number")],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_to_float_invalid_string_returns_null(self):
        """toFloat with invalid string returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toFloat",
            args=[Literal(value="not a number")],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_to_integer_from_boolean_true(self):
        """toInteger converts True to 1."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toInteger",
            args=[Literal(value=True)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 1

    def test_to_integer_from_boolean_false(self):
        """toInteger converts False to 0."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toInteger",
            args=[Literal(value=False)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 0

    def test_to_float_from_boolean_true(self):
        """toFloat converts True to 1.0."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toFloat",
            args=[Literal(value=True)],
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
            args=[Literal(value=False)],
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
            args=[Literal(value=True)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "true"

    def test_to_string_from_boolean_false(self):
        """toString converts False to 'false'."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toString",
            args=[Literal(value=False)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "false"

    def test_to_string_from_float(self):
        """toString converts float to string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toString",
            args=[Literal(value=3.14)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "3.14"

    def test_type_function_returns_type_name(self):
        """type() function returns type name."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="type",
            args=[Literal(value="hello")],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "String"

    def test_to_integer_with_null_returns_null(self):
        """toInteger with NULL returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toInteger",
            args=[Literal(value=None)],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_to_float_with_null_returns_null(self):
        """toFloat with NULL returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toFloat",
            args=[Literal(value=None)],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_to_string_with_null_returns_null(self):
        """toString with NULL returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toString",
            args=[Literal(value=None)],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_to_integer_from_float_truncates(self):
        """toInteger from float truncates decimal."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toInteger",
            args=[Literal(value=3.99)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 3

    def test_to_integer_returns_same_for_int(self):
        """toInteger with integer returns same value."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toInteger",
            args=[Literal(value=42)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 42

    def test_to_float_returns_same_for_float(self):
        """toFloat with float returns same value."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toFloat",
            args=[Literal(value=3.14)],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherFloat

        assert isinstance(result, CypherFloat)
        assert abs(result.value - 3.14) < 0.001

    def test_to_float_from_integer(self):
        """toFloat converts integer to float."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toFloat",
            args=[Literal(value=42)],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherFloat

        assert isinstance(result, CypherFloat)
        assert abs(result.value - 42.0) < 0.001

    def test_to_string_returns_same_for_string(self):
        """toString with string returns same value."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toString",
            args=[Literal(value="hello")],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "hello"

    def test_to_string_unsupported_type_returns_null(self):
        """toString with unsupported type returns NULL."""
        ctx = ExecutionContext()
        # Pass a list (unsupported type)
        expr = FunctionCall(
            name="toString",
            args=[Literal(value=[1, 2, 3])],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_unknown_type_function_raises_error(self):
        """Unknown type function raises ValueError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toUnknown",  # Not implemented
            args=[Literal(value="true")],
        )

        with pytest.raises(ValueError, match="Unknown function: TOUNKNOWN"):
            evaluate_expression(expr, ctx)

    def test_to_integer_unsupported_type_returns_null(self):
        """toInteger with unsupported type returns NULL (else branch)."""
        ctx = ExecutionContext()

        # Create a CypherList (unsupported for conversion)
        expr = FunctionCall(
            name="toInteger",
            args=[Literal(value=[1, 2, 3])],  # List - unsupported type
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_to_float_unsupported_type_returns_null(self):
        """toFloat with unsupported type returns NULL (else branch)."""
        ctx = ExecutionContext()
        # Create a CypherList (unsupported for conversion)
        expr = FunctionCall(
            name="toFloat",
            args=[Literal(value=[1, 2, 3])],  # List - unsupported type
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_type_function_without_cypher_prefix(self):
        """type() on type without Cypher prefix."""
        ctx = ExecutionContext()

        # Test with CypherInt - should strip "Cypher" prefix
        expr = FunctionCall(
            name="type",
            args=[Literal(value=123)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "Int"  # "Cypher" prefix stripped

    def test_substring_negative_start_raises_error(self):
        """SUBSTRING with negative start raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SUBSTRING",
            args=[Literal(value="hello"), Literal(value=-1)],
        )

        with pytest.raises(TypeError, match="SUBSTRING start must be non-negative"):
            evaluate_expression(expr, ctx)

    def test_substring_negative_length_raises_error(self):
        """SUBSTRING with negative length raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SUBSTRING",
            args=[Literal(value="hello"), Literal(value=0), Literal(value=-1)],
        )

        with pytest.raises(TypeError, match="SUBSTRING length must be non-negative"):
            evaluate_expression(expr, ctx)

    def test_length_with_non_string_raises_error(self):
        """LENGTH with non-string raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LENGTH",
            args=[Literal(value=123)],
        )

        with pytest.raises(TypeError, match="LENGTH expects string"):
            evaluate_expression(expr, ctx)

    def test_substring_with_non_string_raises_error(self):
        """SUBSTRING with non-string raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SUBSTRING",
            args=[Literal(value=123), Literal(value=0)],
        )

        with pytest.raises(TypeError, match="SUBSTRING expects string"):
            evaluate_expression(expr, ctx)

    def test_substring_with_non_integer_start_raises_error(self):
        """SUBSTRING with non-integer start raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SUBSTRING",
            args=[Literal(value="hello"), Literal(value="0")],
        )

        with pytest.raises(TypeError, match="SUBSTRING start must be integer"):
            evaluate_expression(expr, ctx)

    def test_substring_with_non_integer_length_raises_error(self):
        """SUBSTRING with non-integer length raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SUBSTRING",
            args=[Literal(value="hello"), Literal(value=0), Literal(value="2")],
        )

        with pytest.raises(TypeError, match="SUBSTRING length must be integer"):
            evaluate_expression(expr, ctx)

    def test_upper_with_non_string_raises_error(self):
        """UPPER with non-string raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="UPPER",
            args=[Literal(value=123)],
        )

        with pytest.raises(TypeError, match="UPPER expects string"):
            evaluate_expression(expr, ctx)

    def test_lower_with_non_string_raises_error(self):
        """LOWER with non-string raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LOWER",
            args=[Literal(value=123)],
        )

        with pytest.raises(TypeError, match="LOWER expects string"):
            evaluate_expression(expr, ctx)

    def test_trim_with_non_string_raises_error(self):
        """TRIM with non-string raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="TRIM",
            args=[Literal(value=123)],
        )

        with pytest.raises(TypeError, match="TRIM expects string"):
            evaluate_expression(expr, ctx)


@pytest.mark.unit
class TestQuantifierExpressions:
    """Tests for quantifier expressions (ALL, ANY, NONE, SINGLE)."""

    def test_all_with_all_true(self):
        """ALL returns true when all predicates are true."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        # ALL(x IN [1, 2, 3] WHERE x > 0)
        expr = QuantifierExpression(
            quantifier="ALL",
            variable="x",
            list_expr=Literal(value=[1, 2, 3]),
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherBool

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_all_with_one_false(self):
        """ALL returns false when one predicate is false."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        # ALL(x IN [1, -2, 3] WHERE x > 0)
        expr = QuantifierExpression(
            quantifier="ALL",
            variable="x",
            list_expr=Literal(value=[1, -2, 3]),
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherBool

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_all_with_null_predicate(self):
        """ALL returns NULL when no false but at least one NULL."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        # ALL(x IN [1, NULL, 3] WHERE x > 0)
        expr = QuantifierExpression(
            quantifier="ALL",
            variable="x",
            list_expr=Literal(value=[1, None, 3]),
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_all_with_empty_list(self):
        """ALL returns true for empty list."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        expr = QuantifierExpression(
            quantifier="ALL",
            variable="x",
            list_expr=Literal(value=[]),
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherBool

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_any_with_one_true(self):
        """ANY returns true when at least one predicate is true."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        # ANY(x IN [1, -2, 3] WHERE x > 0)
        expr = QuantifierExpression(
            quantifier="ANY",
            variable="x",
            list_expr=Literal(value=[1, -2, 3]),
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherBool

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_any_with_all_false(self):
        """ANY returns false when all predicates are false."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        # ANY(x IN [-1, -2, -3] WHERE x > 0)
        expr = QuantifierExpression(
            quantifier="ANY",
            variable="x",
            list_expr=Literal(value=[-1, -2, -3]),
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherBool

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_any_with_null_and_no_true(self):
        """ANY returns NULL when no true but at least one NULL."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        # ANY(x IN [-1, NULL, -3] WHERE x > 0)
        expr = QuantifierExpression(
            quantifier="ANY",
            variable="x",
            list_expr=Literal(value=[-1, None, -3]),
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_none_with_all_false(self):
        """NONE returns true when all predicates are false."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        # NONE(x IN [-1, -2, -3] WHERE x > 0)
        expr = QuantifierExpression(
            quantifier="NONE",
            variable="x",
            list_expr=Literal(value=[-1, -2, -3]),
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherBool

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_none_with_one_true(self):
        """NONE returns false when at least one predicate is true."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        # NONE(x IN [1, -2, -3] WHERE x > 0)
        expr = QuantifierExpression(
            quantifier="NONE",
            variable="x",
            list_expr=Literal(value=[1, -2, -3]),
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherBool

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_none_with_null_and_no_true(self):
        """NONE returns NULL when no true but at least one NULL."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        # NONE(x IN [-1, NULL, -3] WHERE x > 0)
        expr = QuantifierExpression(
            quantifier="NONE",
            variable="x",
            list_expr=Literal(value=[-1, None, -3]),
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_single_with_exactly_one_true(self):
        """SINGLE returns true when exactly one predicate is true."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        # SINGLE(x IN [1, -2, -3] WHERE x > 0)
        expr = QuantifierExpression(
            quantifier="SINGLE",
            variable="x",
            list_expr=Literal(value=[1, -2, -3]),
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherBool

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_single_with_multiple_true(self):
        """SINGLE returns false when more than one predicate is true."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        # SINGLE(x IN [1, 2, -3] WHERE x > 0)
        expr = QuantifierExpression(
            quantifier="SINGLE",
            variable="x",
            list_expr=Literal(value=[1, 2, -3]),
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherBool

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_single_with_zero_true_and_null(self):
        """SINGLE returns NULL when zero true and at least one NULL."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        # SINGLE(x IN [-1, NULL, -3] WHERE x > 0)
        expr = QuantifierExpression(
            quantifier="SINGLE",
            variable="x",
            list_expr=Literal(value=[-1, None, -3]),
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_single_with_all_false(self):
        """SINGLE returns false when all predicates are false."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        # SINGLE(x IN [-1, -2, -3] WHERE x > 0)
        expr = QuantifierExpression(
            quantifier="SINGLE",
            variable="x",
            list_expr=Literal(value=[-1, -2, -3]),
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherBool

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_quantifier_with_non_list_raises_error(self):
        """Quantifier with non-list raises TypeError."""
        from graphforge.ast.expression import QuantifierExpression

        ctx = ExecutionContext()
        expr = QuantifierExpression(
            quantifier="ALL",
            variable="x",
            list_expr=Literal(value=123),  # Not a list
            predicate=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
        )

        with pytest.raises(TypeError, match="Quantifier requires a list"):
            evaluate_expression(expr, ctx)


@pytest.mark.unit
class TestListFunctions:
    """Tests for list functions."""

    def test_tail_function(self):
        """TAIL returns all elements except first."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="TAIL",
            args=[Literal(value=[1, 2, 3, 4])],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherList

        assert isinstance(result, CypherList)
        assert len(result.value) == 3

    def test_tail_empty_list(self):
        """TAIL of empty list returns empty list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="TAIL",
            args=[Literal(value=[])],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherList

        assert isinstance(result, CypherList)
        assert len(result.value) == 0

    def test_tail_with_null(self):
        """TAIL with NULL returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="TAIL",
            args=[Literal(value=None)],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_head_list_function(self):
        """HEAD returns first element of list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="HEAD",
            args=[Literal(value=[1, 2, 3])],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 1

    def test_head_empty_list(self):
        """HEAD of empty list returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="HEAD",
            args=[Literal(value=[])],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_last_list_function(self):
        """LAST returns last element of list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LAST",
            args=[Literal(value=[1, 2, 3])],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 3

    def test_last_empty_list(self):
        """LAST of empty list returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LAST",
            args=[Literal(value=[])],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherNull

        assert isinstance(result, CypherNull)

    def test_reverse_list_function(self):
        """REVERSE returns list in reverse order."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="REVERSE",
            args=[Literal(value=[1, 2, 3])],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherList

        assert isinstance(result, CypherList)
        assert len(result.value) == 3
        assert result.value[0].value == 3
        assert result.value[2].value == 1

    def test_range_function_basic(self):
        """RANGE generates list of integers."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RANGE",
            args=[Literal(value=1), Literal(value=5)],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherList

        assert isinstance(result, CypherList)
        assert len(result.value) == 5  # 1, 2, 3, 4, 5

    def test_range_with_step(self):
        """RANGE with step."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RANGE",
            args=[Literal(value=0), Literal(value=10), Literal(value=2)],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherList

        assert isinstance(result, CypherList)
        assert len(result.value) == 6  # 0, 2, 4, 6, 8, 10

    def test_range_with_negative_step(self):
        """RANGE with negative step."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RANGE",
            args=[Literal(value=10), Literal(value=0), Literal(value=-2)],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherList

        assert isinstance(result, CypherList)
        assert len(result.value) == 6  # 10, 8, 6, 4, 2, 0

    def test_range_with_zero_step_raises_error(self):
        """RANGE with step=0 raises ValueError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RANGE",
            args=[Literal(value=1), Literal(value=5), Literal(value=0)],
        )

        with pytest.raises(ValueError, match="RANGE step cannot be zero"):
            evaluate_expression(expr, ctx)

    def test_range_with_non_integer_start_raises_error(self):
        """RANGE with non-integer start raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RANGE",
            args=[Literal(value="1"), Literal(value=5)],
        )

        with pytest.raises(TypeError, match="RANGE start must be integer"):
            evaluate_expression(expr, ctx)

    def test_range_with_non_integer_end_raises_error(self):
        """RANGE with non-integer end raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RANGE",
            args=[Literal(value=1), Literal(value="5")],
        )

        with pytest.raises(TypeError, match="RANGE end must be integer"):
            evaluate_expression(expr, ctx)

    def test_range_with_non_integer_step_raises_error(self):
        """RANGE with non-integer step raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RANGE",
            args=[Literal(value=1), Literal(value=5), Literal(value="2")],
        )

        with pytest.raises(TypeError, match="RANGE step must be integer"):
            evaluate_expression(expr, ctx)

    def test_size_function_list(self):
        """SIZE returns length of list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SIZE",
            args=[Literal(value=[1, 2, 3])],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 3

    def test_size_function_string(self):
        """SIZE returns length of string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SIZE",
            args=[Literal(value="hello")],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 5


@pytest.mark.unit
class TestStringFunctions:
    """Tests for string functions."""

    def test_split_function(self):
        """SPLIT splits string by delimiter."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SPLIT",
            args=[Literal(value="a,b,c"), Literal(value=",")],
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherList

        assert isinstance(result, CypherList)
        assert len(result.value) == 3
        assert result.value[0].value == "a"
        assert result.value[2].value == "c"

    def test_split_with_wrong_arg_count_raises_error(self):
        """SPLIT with wrong arg count raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SPLIT",
            args=[Literal(value="a,b,c")],
        )

        with pytest.raises(TypeError, match="SPLIT expects 2 arguments"):
            evaluate_expression(expr, ctx)

    def test_split_with_non_string_first_arg_raises_error(self):
        """SPLIT with non-string first arg raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SPLIT",
            args=[Literal(value=123), Literal(value=",")],
        )

        with pytest.raises(TypeError, match="SPLIT expects string as first argument"):
            evaluate_expression(expr, ctx)

    def test_split_with_non_string_delimiter_raises_error(self):
        """SPLIT with non-string delimiter raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SPLIT",
            args=[Literal(value="a,b,c"), Literal(value=123)],
        )

        with pytest.raises(TypeError, match="SPLIT expects string as delimiter"):
            evaluate_expression(expr, ctx)

    def test_replace_function(self):
        """REPLACE replaces all occurrences."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="REPLACE",
            args=[Literal(value="hello world"), Literal(value="world"), Literal(value="there")],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "hello there"

    def test_replace_with_wrong_arg_count_raises_error(self):
        """REPLACE with wrong arg count raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="REPLACE",
            args=[Literal(value="hello"), Literal(value="world")],
        )

        with pytest.raises(TypeError, match="REPLACE expects 3 arguments"):
            evaluate_expression(expr, ctx)

    def test_replace_with_non_string_first_arg_raises_error(self):
        """REPLACE with non-string first arg raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="REPLACE",
            args=[Literal(value=123), Literal(value="a"), Literal(value="b")],
        )

        with pytest.raises(TypeError, match="REPLACE expects string as first argument"):
            evaluate_expression(expr, ctx)

    def test_replace_with_non_string_search_raises_error(self):
        """REPLACE with non-string search raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="REPLACE",
            args=[Literal(value="hello"), Literal(value=123), Literal(value="b")],
        )

        with pytest.raises(TypeError, match="REPLACE expects string as search argument"):
            evaluate_expression(expr, ctx)

    def test_replace_with_non_string_replacement_raises_error(self):
        """REPLACE with non-string replacement raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="REPLACE",
            args=[Literal(value="hello"), Literal(value="a"), Literal(value=123)],
        )

        with pytest.raises(TypeError, match="REPLACE expects string as replacement argument"):
            evaluate_expression(expr, ctx)

    def test_left_function(self):
        """LEFT returns leftmost characters."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LEFT",
            args=[Literal(value="hello"), Literal(value=2)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "he"

    def test_left_with_negative_length(self):
        """LEFT with negative length returns empty string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LEFT",
            args=[Literal(value="hello"), Literal(value=-1)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == ""

    def test_left_with_wrong_arg_count_raises_error(self):
        """LEFT with wrong arg count raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LEFT",
            args=[Literal(value="hello")],
        )

        with pytest.raises(TypeError, match="LEFT expects 2 arguments"):
            evaluate_expression(expr, ctx)

    def test_left_with_non_string_raises_error(self):
        """LEFT with non-string raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LEFT",
            args=[Literal(value=123), Literal(value=2)],
        )

        with pytest.raises(TypeError, match="LEFT expects string as first argument"):
            evaluate_expression(expr, ctx)

    def test_left_with_non_integer_length_raises_error(self):
        """LEFT with non-integer length raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LEFT",
            args=[Literal(value="hello"), Literal(value="2")],
        )

        with pytest.raises(TypeError, match="LEFT expects integer as length"):
            evaluate_expression(expr, ctx)

    def test_right_function(self):
        """RIGHT returns rightmost characters."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RIGHT",
            args=[Literal(value="hello"), Literal(value=2)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "lo"

    def test_right_with_negative_length(self):
        """RIGHT with negative length returns empty string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RIGHT",
            args=[Literal(value="hello"), Literal(value=-1)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == ""

    def test_right_with_length_exceeding_string(self):
        """RIGHT with length > string length returns entire string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RIGHT",
            args=[Literal(value="hello"), Literal(value=10)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "hello"

    def test_right_with_wrong_arg_count_raises_error(self):
        """RIGHT with wrong arg count raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RIGHT",
            args=[Literal(value="hello")],
        )

        with pytest.raises(TypeError, match="RIGHT expects 2 arguments"):
            evaluate_expression(expr, ctx)

    def test_right_with_non_string_raises_error(self):
        """RIGHT with non-string raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RIGHT",
            args=[Literal(value=123), Literal(value=2)],
        )

        with pytest.raises(TypeError, match="RIGHT expects string as first argument"):
            evaluate_expression(expr, ctx)

    def test_right_with_non_integer_length_raises_error(self):
        """RIGHT with non-integer length raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RIGHT",
            args=[Literal(value="hello"), Literal(value="2")],
        )

        with pytest.raises(TypeError, match="RIGHT expects integer as length"):
            evaluate_expression(expr, ctx)

    def test_ltrim_function(self):
        """LTRIM removes leading whitespace."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LTRIM",
            args=[Literal(value="  hello  ")],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "hello  "

    def test_ltrim_with_wrong_arg_count_raises_error(self):
        """LTRIM with wrong arg count raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LTRIM",
            args=[Literal(value="hello"), Literal(value="extra")],
        )

        with pytest.raises(TypeError, match="LTRIM expects 1 argument"):
            evaluate_expression(expr, ctx)

    def test_ltrim_with_non_string_raises_error(self):
        """LTRIM with non-string raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="LTRIM",
            args=[Literal(value=123)],
        )

        with pytest.raises(TypeError, match="LTRIM expects string"):
            evaluate_expression(expr, ctx)

    def test_rtrim_function(self):
        """RTRIM removes trailing whitespace."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RTRIM",
            args=[Literal(value="  hello  ")],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "  hello"

    def test_rtrim_with_wrong_arg_count_raises_error(self):
        """RTRIM with wrong arg count raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RTRIM",
            args=[Literal(value="hello"), Literal(value="extra")],
        )

        with pytest.raises(TypeError, match="RTRIM expects 1 argument"):
            evaluate_expression(expr, ctx)

    def test_rtrim_with_non_string_raises_error(self):
        """RTRIM with non-string raises TypeError."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="RTRIM",
            args=[Literal(value=123)],
        )

        with pytest.raises(TypeError, match="RTRIM expects string"):
            evaluate_expression(expr, ctx)

    def test_reverse_string_function(self):
        """REVERSE reverses a string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="REVERSE",
            args=[Literal(value="hello")],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "olleh"

    def test_substring_without_length(self):
        """SUBSTRING without length returns substring to end."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="SUBSTRING",
            args=[Literal(value="hello"), Literal(value=2)],
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "llo"


@pytest.mark.unit
class TestTypeConversionEdgeCases:
    """Tests for edge cases in type conversion functions."""

    @pytest.mark.parametrize(
        "input_value,expected_type,expected_value",
        [
            # NULL-returning cases
            ([1, 2, 3], "CypherNull", None),
            ({"key": "value"}, "CypherNull", None),
            ("maybe", "CypherNull", None),
            # Valid conversions
            ("true", "CypherBool", True),
            ("false", "CypherBool", False),
            ("TrUe", "CypherBool", True),  # case-insensitive
            (True, "CypherBool", True),  # identity
            (False, "CypherBool", False),  # identity
        ],
        ids=[
            "list_returns_null",
            "map_returns_null",
            "invalid_string_returns_null",
            "true_string",
            "false_string",
            "mixed_case_true",
            "boolean_identity_true",
            "boolean_identity_false",
        ],
    )
    def test_toboolean_conversion(self, input_value, expected_type, expected_value):
        """Test toBoolean function with various inputs."""
        from graphforge.types.values import CypherBool, CypherNull

        ctx = ExecutionContext()
        expr = FunctionCall(
            name="toBoolean",
            args=[Literal(value=input_value)],
        )

        result = evaluate_expression(expr, ctx)

        if expected_type == "CypherNull":
            assert isinstance(result, CypherNull)
        elif expected_type == "CypherBool":
            assert isinstance(result, CypherBool)
            assert result.value is expected_value


@pytest.mark.unit
class TestAdditionalEdgeCases:
    """Tests for additional edge cases and error paths."""

    def test_property_access_on_null_returns_null(self):
        """Property access on NULL returns NULL."""
        ctx = ExecutionContext()
        ctx.bind("n", CypherNull())

        expr = PropertyAccess(variable="n", property="name")
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_property_access_on_non_node_raises_error(self):
        """Property access on non-node/edge raises TypeError."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherInt(42))

        expr = PropertyAccess(variable="x", property="name")

        with pytest.raises(TypeError, match="Cannot access property"):
            evaluate_expression(expr, ctx)

    def test_unary_not_on_non_boolean_raises_error(self):
        """NOT operator on non-boolean raises TypeError."""
        from graphforge.ast.expression import UnaryOp

        ctx = ExecutionContext()
        expr = UnaryOp(op="NOT", operand=Literal(value=42))

        with pytest.raises(TypeError, match="NOT requires boolean operand"):
            evaluate_expression(expr, ctx)

    def test_unary_minus_on_null_returns_null(self):
        """Unary minus on NULL returns NULL."""
        from graphforge.ast.expression import UnaryOp

        ctx = ExecutionContext()
        expr = UnaryOp(op="-", operand=Literal(value=None))

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherNull)

    def test_unary_minus_on_non_numeric_raises_error(self):
        """Unary minus on non-numeric raises TypeError."""
        from graphforge.ast.expression import UnaryOp

        ctx = ExecutionContext()
        expr = UnaryOp(op="-", operand=Literal(value="hello"))

        with pytest.raises(TypeError, match="Unary minus requires numeric operand"):
            evaluate_expression(expr, ctx)

    def test_and_with_non_boolean_right_raises_error(self):
        """AND with non-boolean right operand raises TypeError."""
        ctx = ExecutionContext()
        expr = BinaryOp(
            op="AND",
            left=Literal(value=True),
            right=Literal(value=42),  # Not a boolean
        )

        with pytest.raises(TypeError, match="AND requires boolean operands"):
            evaluate_expression(expr, ctx)

    def test_and_with_non_boolean_left_raises_error(self):
        """AND with non-boolean left operand raises TypeError."""
        ctx = ExecutionContext()
        expr = BinaryOp(
            op="AND",
            left=Literal(value=42),  # Not a boolean
            right=Literal(value=True),
        )

        with pytest.raises(TypeError, match="AND requires boolean operands"):
            evaluate_expression(expr, ctx)

    def test_or_with_non_boolean_right_raises_error(self):
        """OR with non-boolean right operand raises TypeError."""
        ctx = ExecutionContext()
        expr = BinaryOp(
            op="OR",
            left=Literal(value=False),
            right=Literal(value=42),  # Not a boolean
        )

        with pytest.raises(TypeError, match="OR requires boolean operands"):
            evaluate_expression(expr, ctx)

    def test_or_with_non_boolean_left_raises_error(self):
        """OR with non-boolean left operand raises TypeError."""
        ctx = ExecutionContext()
        expr = BinaryOp(
            op="OR",
            left=Literal(value=42),  # Not a boolean
            right=Literal(value=False),
        )

        with pytest.raises(TypeError, match="OR requires boolean operands"):
            evaluate_expression(expr, ctx)

    def test_greater_than_or_equal(self):
        """Greater than or equal comparison."""
        ctx = ExecutionContext()
        expr = BinaryOp(op=">=", left=Literal(value=10), right=Literal(value=10))
        result = evaluate_expression(expr, ctx)

        from graphforge.types.values import CypherBool

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_less_than_or_equal(self):
        """Less than or equal comparison."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="<=", left=Literal(value=5), right=Literal(value=10))
        result = evaluate_expression(expr, ctx)

        from graphforge.types.values import CypherBool

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_modulo_operator(self):
        """Modulo operator."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="%", left=Literal(value=10), right=Literal(value=3))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 1

    def test_modulo_by_zero_returns_null(self):
        """Modulo by zero returns NULL."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="%", left=Literal(value=10), right=Literal(value=0))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_string_concatenation_with_plus(self):
        """String concatenation with + operator."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="+", left=Literal(value="hello"), right=Literal(value=" world"))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherString)
        assert result.value == "hello world"

    def test_string_concatenation_with_mixed_types(self):
        """String concatenation with mixed types."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="+", left=Literal(value="value: "), right=Literal(value=42))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherString)
        assert result.value == "value: 42"

    def test_arithmetic_with_non_numeric_raises_error(self):
        """Arithmetic with non-numeric operands raises TypeError."""
        ctx = ExecutionContext()
        expr = BinaryOp(op="*", left=Literal(value="hello"), right=Literal(value=2))

        with pytest.raises(TypeError, match="Arithmetic operator .* requires numeric operands"):
            evaluate_expression(expr, ctx)

    def test_case_expression_no_match_no_else(self):
        """CASE with no match and no ELSE returns NULL."""
        from graphforge.ast.expression import CaseExpression

        ctx = ExecutionContext()
        expr = CaseExpression(
            when_clauses=[
                (Literal(value=False), Literal(value="result1")),
            ],
            else_expr=None,
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherNull)

    def test_case_expression_with_match(self):
        """CASE returns first matching WHEN result."""
        from graphforge.ast.expression import CaseExpression

        ctx = ExecutionContext()
        expr = CaseExpression(
            when_clauses=[
                (Literal(value=False), Literal(value="result1")),
                (Literal(value=True), Literal(value="result2")),
                (Literal(value=True), Literal(value="result3")),
            ],
            else_expr=Literal(value="default"),
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "result2"

    def test_case_expression_with_else(self):
        """CASE returns ELSE when no match."""
        from graphforge.ast.expression import CaseExpression

        ctx = ExecutionContext()
        expr = CaseExpression(
            when_clauses=[
                (Literal(value=False), Literal(value="result1")),
            ],
            else_expr=Literal(value="default"),
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "default"

    def test_case_expression_null_condition_treated_as_false(self):
        """CASE treats NULL condition as false."""
        from graphforge.ast.expression import CaseExpression

        ctx = ExecutionContext()
        expr = CaseExpression(
            when_clauses=[
                (Literal(value=None), Literal(value="result1")),
            ],
            else_expr=Literal(value="default"),
        )

        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "default"

    def test_list_comprehension_with_filter(self):
        """List comprehension with filter expression."""
        from graphforge.ast.expression import ListComprehension

        ctx = ExecutionContext()
        # [x IN [1, 2, 3, 4] WHERE x > 2]
        expr = ListComprehension(
            variable="x",
            list_expr=Literal(value=[1, 2, 3, 4]),
            filter_expr=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=2)),
            map_expr=None,
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherList

        assert isinstance(result, CypherList)
        assert len(result.value) == 2  # 3 and 4

    def test_list_comprehension_with_map(self):
        """List comprehension with map expression."""
        from graphforge.ast.expression import ListComprehension

        ctx = ExecutionContext()
        # [x IN [1, 2, 3] | x * 2]
        expr = ListComprehension(
            variable="x",
            list_expr=Literal(value=[1, 2, 3]),
            filter_expr=None,
            map_expr=BinaryOp(op="*", left=Variable(name="x"), right=Literal(value=2)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherList

        assert isinstance(result, CypherList)
        assert len(result.value) == 3
        assert result.value[0].value == 2
        assert result.value[2].value == 6

    def test_list_comprehension_with_filter_and_map(self):
        """List comprehension with both filter and map."""
        from graphforge.ast.expression import ListComprehension

        ctx = ExecutionContext()
        # [x IN [1, 2, 3, 4] WHERE x > 2 | x * 2]
        expr = ListComprehension(
            variable="x",
            list_expr=Literal(value=[1, 2, 3, 4]),
            filter_expr=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=2)),
            map_expr=BinaryOp(op="*", left=Variable(name="x"), right=Literal(value=2)),
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherList

        assert isinstance(result, CypherList)
        assert len(result.value) == 2
        assert result.value[0].value == 6  # 3 * 2
        assert result.value[1].value == 8  # 4 * 2

    def test_list_comprehension_filter_with_null_skips(self):
        """List comprehension skips items where filter is NULL."""
        from graphforge.ast.expression import ListComprehension

        ctx = ExecutionContext()
        # [x IN [1, NULL, 3] WHERE x > 0]
        expr = ListComprehension(
            variable="x",
            list_expr=Literal(value=[1, None, 3]),
            filter_expr=BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=0)),
            map_expr=None,
        )

        result = evaluate_expression(expr, ctx)
        from graphforge.types.values import CypherList

        assert isinstance(result, CypherList)
        assert len(result.value) == 2  # NULL is skipped

    def test_list_comprehension_with_non_list_raises_error(self):
        """List comprehension with non-list raises TypeError."""
        from graphforge.ast.expression import ListComprehension

        ctx = ExecutionContext()
        expr = ListComprehension(
            variable="x",
            list_expr=Literal(value=42),  # Not a list
            filter_expr=None,
            map_expr=None,
        )

        with pytest.raises(TypeError, match="IN requires a list"):
            evaluate_expression(expr, ctx)

    def test_unknown_expression_type_raises_error(self):
        """Unknown expression type raises TypeError."""
        ctx = ExecutionContext()

        # Create a fake expression type
        class UnknownExpr:
            pass

        expr = UnknownExpr()

        with pytest.raises(TypeError, match="Cannot evaluate expression type"):
            evaluate_expression(expr, ctx)
