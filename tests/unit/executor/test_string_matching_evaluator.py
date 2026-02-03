"""Unit tests for string matching operator evaluation."""

import pytest

from graphforge.ast.expression import BinaryOp, Literal
from graphforge.executor.evaluator import ExecutionContext, evaluate_expression
from graphforge.types.values import CypherBool, CypherNull


class TestStartsWithEvaluator:
    """Tests for STARTS WITH evaluation."""

    def test_starts_with_true(self):
        """STARTS WITH returns true for matching prefix."""
        left = Literal(value="hello world")
        right = Literal(value="hello")
        expr = BinaryOp(op="STARTS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_starts_with_false(self):
        """STARTS WITH returns false for non-matching prefix."""
        left = Literal(value="hello world")
        right = Literal(value="world")
        expr = BinaryOp(op="STARTS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_starts_with_case_sensitive(self):
        """STARTS WITH is case-sensitive."""
        left = Literal(value="Hello")
        right = Literal(value="h")
        expr = BinaryOp(op="STARTS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_starts_with_empty_prefix(self):
        """STARTS WITH empty string returns true."""
        left = Literal(value="hello")
        right = Literal(value="")
        expr = BinaryOp(op="STARTS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_starts_with_full_string(self):
        """STARTS WITH the full string returns true."""
        left = Literal(value="hello")
        right = Literal(value="hello")
        expr = BinaryOp(op="STARTS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_starts_with_longer_than_string(self):
        """STARTS WITH longer pattern returns false."""
        left = Literal(value="hi")
        right = Literal(value="hello")
        expr = BinaryOp(op="STARTS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is False


class TestEndsWithEvaluator:
    """Tests for ENDS WITH evaluation."""

    def test_ends_with_true(self):
        """ENDS WITH returns true for matching suffix."""
        left = Literal(value="hello world")
        right = Literal(value="world")
        expr = BinaryOp(op="ENDS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_ends_with_false(self):
        """ENDS WITH returns false for non-matching suffix."""
        left = Literal(value="hello world")
        right = Literal(value="hello")
        expr = BinaryOp(op="ENDS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_ends_with_case_sensitive(self):
        """ENDS WITH is case-sensitive."""
        left = Literal(value="Hello")
        right = Literal(value="LO")
        expr = BinaryOp(op="ENDS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_ends_with_empty_suffix(self):
        """ENDS WITH empty string returns true."""
        left = Literal(value="hello")
        right = Literal(value="")
        expr = BinaryOp(op="ENDS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True


class TestContainsEvaluator:
    """Tests for CONTAINS evaluation."""

    def test_contains_true(self):
        """CONTAINS returns true for matching substring."""
        left = Literal(value="hello world")
        right = Literal(value="lo wo")
        expr = BinaryOp(op="CONTAINS", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_contains_false(self):
        """CONTAINS returns false for non-matching substring."""
        left = Literal(value="hello world")
        right = Literal(value="xyz")
        expr = BinaryOp(op="CONTAINS", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_contains_case_sensitive(self):
        """CONTAINS is case-sensitive."""
        left = Literal(value="Hello World")
        right = Literal(value="hello")
        expr = BinaryOp(op="CONTAINS", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_contains_empty_substring(self):
        """CONTAINS empty string returns true."""
        left = Literal(value="hello")
        right = Literal(value="")
        expr = BinaryOp(op="CONTAINS", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_contains_at_beginning(self):
        """CONTAINS substring at beginning."""
        left = Literal(value="hello world")
        right = Literal(value="hello")
        expr = BinaryOp(op="CONTAINS", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_contains_at_end(self):
        """CONTAINS substring at end."""
        left = Literal(value="hello world")
        right = Literal(value="world")
        expr = BinaryOp(op="CONTAINS", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True


class TestNullHandling:
    """Tests for NULL handling in string matching."""

    def test_starts_with_left_null(self):
        """STARTS WITH with NULL left operand returns NULL."""
        left = Literal(value=None)
        right = Literal(value="hello")
        expr = BinaryOp(op="STARTS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_starts_with_right_null(self):
        """STARTS WITH with NULL right operand returns NULL."""
        left = Literal(value="hello")
        right = Literal(value=None)
        expr = BinaryOp(op="STARTS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_ends_with_left_null(self):
        """ENDS WITH with NULL left operand returns NULL."""
        left = Literal(value=None)
        right = Literal(value="world")
        expr = BinaryOp(op="ENDS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)

    def test_contains_right_null(self):
        """CONTAINS with NULL right operand returns NULL."""
        left = Literal(value="hello world")
        right = Literal(value=None)
        expr = BinaryOp(op="CONTAINS", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherNull)


class TestTypeErrors:
    """Tests for type errors in string matching."""

    def test_starts_with_integer_left(self):
        """STARTS WITH with integer left operand raises TypeError."""
        left = Literal(value=123)
        right = Literal(value="1")
        expr = BinaryOp(op="STARTS WITH", left=left, right=right)
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="STARTS WITH requires string operands"):
            evaluate_expression(expr, ctx)

    def test_starts_with_integer_right(self):
        """STARTS WITH with integer right operand raises TypeError."""
        left = Literal(value="123")
        right = Literal(value=1)
        expr = BinaryOp(op="STARTS WITH", left=left, right=right)
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="STARTS WITH requires string operands"):
            evaluate_expression(expr, ctx)

    def test_ends_with_integer_operand(self):
        """ENDS WITH with integer operand raises TypeError."""
        left = Literal(value="test")
        right = Literal(value=123)
        expr = BinaryOp(op="ENDS WITH", left=left, right=right)
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="ENDS WITH requires string operands"):
            evaluate_expression(expr, ctx)

    def test_contains_integer_operand(self):
        """CONTAINS with integer operand raises TypeError."""
        left = Literal(value=456)
        right = Literal(value="45")
        expr = BinaryOp(op="CONTAINS", left=left, right=right)
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="CONTAINS requires string operands"):
            evaluate_expression(expr, ctx)


class TestEmptyStrings:
    """Tests for empty string handling."""

    def test_empty_string_starts_with_pattern(self):
        """Empty string doesn't start with non-empty pattern."""
        left = Literal(value="")
        right = Literal(value="x")
        expr = BinaryOp(op="STARTS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_empty_string_starts_with_empty(self):
        """Empty string starts with empty string."""
        left = Literal(value="")
        right = Literal(value="")
        expr = BinaryOp(op="STARTS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_empty_string_ends_with_pattern(self):
        """Empty string doesn't end with non-empty pattern."""
        left = Literal(value="")
        right = Literal(value="x")
        expr = BinaryOp(op="ENDS WITH", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_empty_string_contains_pattern(self):
        """Empty string doesn't contain non-empty pattern."""
        left = Literal(value="")
        right = Literal(value="x")
        expr = BinaryOp(op="CONTAINS", left=left, right=right)
        ctx = ExecutionContext()

        result = evaluate_expression(expr, ctx)

        assert isinstance(result, CypherBool)
        assert result.value is False
