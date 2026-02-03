"""Unit tests for arithmetic operator evaluation."""

import pytest

from graphforge.ast.expression import BinaryOp, Literal, UnaryOp, Variable
from graphforge.executor.evaluator import evaluate_expression
from graphforge.executor.executor import ExecutionContext
from graphforge.types.values import CypherFloat, CypherInt, CypherNull, CypherString


class TestArithmeticEvaluation:
    """Tests for evaluating arithmetic operators."""

    def test_addition_int(self):
        """Evaluate integer addition."""
        expr = BinaryOp(op="+", left=Literal(value=2), right=Literal(value=3))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 5

    def test_addition_float(self):
        """Evaluate float addition."""
        expr = BinaryOp(op="+", left=Literal(value=2.5), right=Literal(value=3.7))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherFloat)
        assert result.value == pytest.approx(6.2)

    def test_addition_mixed_types(self):
        """Evaluate addition with mixed int and float (type coercion)."""
        expr = BinaryOp(op="+", left=Literal(value=2), right=Literal(value=3.5))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherFloat)
        assert result.value == pytest.approx(5.5)

    def test_string_concatenation(self):
        """Evaluate string concatenation with +."""
        expr = BinaryOp(op="+", left=Literal(value="Hello "), right=Literal(value="World"))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherString)
        assert result.value == "Hello World"

    def test_string_plus_number(self):
        """Evaluate string concatenation with number."""
        expr = BinaryOp(op="+", left=Literal(value="Age: "), right=Literal(value=30))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherString)
        assert result.value == "Age: 30"

    def test_subtraction(self):
        """Evaluate subtraction."""
        expr = BinaryOp(op="-", left=Literal(value=10), right=Literal(value=3))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 7

    def test_multiplication(self):
        """Evaluate multiplication."""
        expr = BinaryOp(op="*", left=Literal(value=4), right=Literal(value=5))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 20

    def test_division(self):
        """Evaluate division (always returns float)."""
        expr = BinaryOp(op="/", left=Literal(value=10), right=Literal(value=2))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherFloat)
        assert result.value == pytest.approx(5.0)

    def test_division_by_zero(self):
        """Evaluate division by zero (returns NULL)."""
        expr = BinaryOp(op="/", left=Literal(value=10), right=Literal(value=0))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_modulo(self):
        """Evaluate modulo."""
        expr = BinaryOp(op="%", left=Literal(value=10), right=Literal(value=3))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 1

    def test_modulo_by_zero(self):
        """Evaluate modulo by zero (returns NULL)."""
        expr = BinaryOp(op="%", left=Literal(value=10), right=Literal(value=0))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_unary_minus_int(self):
        """Evaluate unary minus on integer."""
        expr = UnaryOp(op="-", operand=Literal(value=5))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == -5

    def test_unary_minus_float(self):
        """Evaluate unary minus on float."""
        expr = UnaryOp(op="-", operand=Literal(value=3.14))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherFloat)
        assert result.value == pytest.approx(-3.14)

    def test_null_propagation_addition(self):
        """NULL propagates through addition."""
        expr = BinaryOp(op="+", left=Literal(value=None), right=Literal(value=5))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_null_propagation_subtraction(self):
        """NULL propagates through subtraction."""
        expr = BinaryOp(op="-", left=Literal(value=10), right=Literal(value=None))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_null_propagation_unary_minus(self):
        """NULL propagates through unary minus."""
        expr = UnaryOp(op="-", operand=Literal(value=None))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_operator_precedence(self):
        """Evaluate expression with operator precedence."""
        # 2 + 3 * 4 = 2 + 12 = 14
        mult = BinaryOp(op="*", left=Literal(value=3), right=Literal(value=4))
        expr = BinaryOp(op="+", left=Literal(value=2), right=mult)
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 14

    def test_type_error_non_numeric(self):
        """Raise TypeError for non-numeric operands."""
        expr = BinaryOp(op="-", left=Literal(value="text"), right=Literal(value=5))
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="requires numeric operands"):
            evaluate_expression(expr, ctx)

    def test_type_error_unary_minus_non_numeric(self):
        """Raise TypeError for unary minus on non-numeric operand."""
        expr = UnaryOp(op="-", operand=Literal(value="text"))
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="requires numeric operand"):
            evaluate_expression(expr, ctx)

    def test_type_error_string_concat_with_noderef(self):
        """Raise TypeError when trying to concatenate NodeRef with string."""
        from graphforge.types.graph import NodeRef

        # Create a NodeRef
        node = NodeRef(id=1, labels=frozenset(["Person"]), properties={"name": "Alice"})
        ctx = ExecutionContext()
        ctx.bind("n", node)

        # Try to concatenate node with string: n + "text"
        expr = BinaryOp(op="+", left=Variable(name="n"), right=Literal(value="text"))

        with pytest.raises(TypeError, match="String concatenation requires CypherValue operands"):
            evaluate_expression(expr, ctx)

    def test_negative_number_multiplication(self):
        """Evaluate unary minus with multiplication."""
        # -2 * 3 = -6
        unary = UnaryOp(op="-", operand=Literal(value=2))
        expr = BinaryOp(op="*", left=unary, right=Literal(value=3))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == -6

    def test_complex_expression(self):
        """Evaluate complex arithmetic expression."""
        # 2 + 3 * 4 - 10 / 2 = 2 + 12 - 5.0 = 9.0
        mult = BinaryOp(op="*", left=Literal(value=3), right=Literal(value=4))
        div = BinaryOp(op="/", left=Literal(value=10), right=Literal(value=2))
        add = BinaryOp(op="+", left=Literal(value=2), right=mult)
        expr = BinaryOp(op="-", left=add, right=div)
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherFloat)
        assert result.value == pytest.approx(9.0)

    def test_arithmetic_with_variables(self):
        """Evaluate arithmetic with variables."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherInt(10))
        ctx.bind("y", CypherInt(3))

        expr = BinaryOp(op="+", left=Variable(name="x"), right=Variable(name="y"))
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 13

    def test_float_division_result(self):
        """Division of two integers returns float."""
        expr = BinaryOp(op="/", left=Literal(value=7), right=Literal(value=2))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherFloat)
        assert result.value == pytest.approx(3.5)

    def test_modulo_float(self):
        """Modulo with floats."""
        expr = BinaryOp(op="%", left=Literal(value=10.5), right=Literal(value=3.0))
        ctx = ExecutionContext()
        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherFloat)
        assert result.value == pytest.approx(1.5)
