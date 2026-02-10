"""Unit tests for list function error handling and edge cases."""

import pytest

from graphforge.ast.expression import FunctionCall, Literal
from graphforge.executor.evaluator import (
    ExecutionContext,
    evaluate_expression,
)


class TestListFunctionErrors:
    """Tests for error handling in list functions."""

    def test_tail_wrong_arg_count(self):
        """Test tail() with wrong number of arguments."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="tail",
            args=[Literal(value=[1, 2]), Literal(value=[3, 4])],
        )
        with pytest.raises(TypeError, match="TAIL expects 1 argument, got 2"):
            evaluate_expression(expr, ctx)

    def test_tail_invalid_type(self):
        """Test tail() with non-list argument."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="tail",
            args=[Literal(value=42)],
        )
        with pytest.raises(TypeError, match="TAIL expects list argument"):
            evaluate_expression(expr, ctx)

    def test_head_list_wrong_arg_count(self):
        """Test head() with wrong number of arguments."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="head",
            args=[Literal(value=[1, 2]), Literal(value=[3, 4])],
        )
        with pytest.raises(TypeError, match="HEAD expects 1 argument, got 2"):
            evaluate_expression(expr, ctx)

    def test_head_invalid_type(self):
        """Test head() with invalid type (not list or path)."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="head",
            args=[Literal(value=42)],
        )
        with pytest.raises(TypeError, match="HEAD expects list or path argument"):
            evaluate_expression(expr, ctx)

    def test_last_list_wrong_arg_count(self):
        """Test last() with wrong number of arguments."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="last",
            args=[Literal(value=[1, 2]), Literal(value=[3, 4])],
        )
        with pytest.raises(TypeError, match="LAST expects 1 argument, got 2"):
            evaluate_expression(expr, ctx)

    def test_last_invalid_type(self):
        """Test last() with invalid type (not list or path)."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="last",
            args=[Literal(value=42)],
        )
        with pytest.raises(TypeError, match="LAST expects list or path argument"):
            evaluate_expression(expr, ctx)

    def test_reverse_wrong_arg_count(self):
        """Test reverse() with wrong number of arguments."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="reverse",
            args=[Literal(value=[1, 2]), Literal(value=[3, 4])],
        )
        with pytest.raises(TypeError, match="REVERSE expects 1 argument, got 2"):
            evaluate_expression(expr, ctx)

    def test_reverse_invalid_type(self):
        """Test reverse() with invalid type (not list or string)."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="reverse",
            args=[Literal(value=42)],
        )
        with pytest.raises(TypeError, match="REVERSE expects list or string argument"):
            evaluate_expression(expr, ctx)

    def test_range_wrong_arg_count_too_few(self):
        """Test range() with too few arguments."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value=1)],
        )
        with pytest.raises(TypeError, match="RANGE expects 2 or 3 arguments, got 1"):
            evaluate_expression(expr, ctx)

    def test_range_wrong_arg_count_too_many(self):
        """Test range() with too many arguments."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[
                Literal(value=1),
                Literal(value=2),
                Literal(value=3),
                Literal(value=4),
            ],
        )
        with pytest.raises(TypeError, match="RANGE expects 2 or 3 arguments, got 4"):
            evaluate_expression(expr, ctx)

    def test_size_invalid_type(self):
        """Test size() with invalid type (not list or string)."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="size",
            args=[Literal(value=42)],
        )
        with pytest.raises(TypeError, match="SIZE expects list or string"):
            evaluate_expression(expr, ctx)


class TestListFunctionTypeErrors:
    """Tests for type validation in list functions."""

    def test_tail_with_dict(self):
        """Test tail() rejects dict."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="tail",
            args=[Literal(value={"key": "value"})],
        )
        with pytest.raises(TypeError, match="TAIL expects list argument"):
            evaluate_expression(expr, ctx)

    def test_head_with_number(self):
        """Test head() rejects number."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="head",
            args=[Literal(value=123)],
        )
        with pytest.raises(TypeError, match="HEAD expects list or path argument"):
            evaluate_expression(expr, ctx)

    def test_last_with_boolean(self):
        """Test last() rejects boolean."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="last",
            args=[Literal(value=True)],
        )
        with pytest.raises(TypeError, match="LAST expects list or path argument"):
            evaluate_expression(expr, ctx)

    def test_reverse_with_number(self):
        """Test reverse() rejects number."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="reverse",
            args=[Literal(value=42)],
        )
        with pytest.raises(TypeError, match="REVERSE expects list or string argument"):
            evaluate_expression(expr, ctx)

    def test_reverse_with_dict(self):
        """Test reverse() rejects dict."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="reverse",
            args=[Literal(value={"a": 1})],
        )
        with pytest.raises(TypeError, match="REVERSE expects list or string argument"):
            evaluate_expression(expr, ctx)

    def test_size_with_boolean(self):
        """Test size() rejects boolean."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="size",
            args=[Literal(value=False)],
        )
        with pytest.raises(TypeError, match="SIZE expects list or string"):
            evaluate_expression(expr, ctx)


class TestRangeFunctionEdgeCases:
    """Additional edge case tests for range() function."""

    def test_range_large_step(self):
        """Test range() with step larger than range."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value=1), Literal(value=5), Literal(value=10)],
        )
        result = evaluate_expression(expr, ctx)
        assert len(result.value) == 1
        assert result.value[0].value == 1

    def test_range_negative_numbers(self):
        """Test range() with negative numbers."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value=-5), Literal(value=-1)],
        )
        result = evaluate_expression(expr, ctx)
        assert len(result.value) == 5
        assert [x.value for x in result.value] == [-5, -4, -3, -2, -1]

    def test_range_negative_to_positive(self):
        """Test range() crossing zero."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value=-2), Literal(value=2)],
        )
        result = evaluate_expression(expr, ctx)
        assert [x.value for x in result.value] == [-2, -1, 0, 1, 2]

    def test_range_large_negative_step(self):
        """Test range() with large negative step."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value=10), Literal(value=1), Literal(value=-3)],
        )
        result = evaluate_expression(expr, ctx)
        assert [x.value for x in result.value] == [10, 7, 4, 1]

    def test_range_backwards_with_positive_step(self):
        """Test range() with start > end and positive step."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value=10), Literal(value=1), Literal(value=1)],
        )
        result = evaluate_expression(expr, ctx)
        assert len(result.value) == 0


class TestListFunctionWithMixedTypes:
    """Tests for list functions with heterogeneous lists."""

    def test_tail_mixed_types(self):
        """Test tail() with mixed type list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="tail",
            args=[Literal(value=[1, "hello", True, 3.14])],
        )
        result = evaluate_expression(expr, ctx)
        assert len(result.value) == 3
        assert result.value[0].value == "hello"
        assert result.value[1].value is True
        assert result.value[2].value == 3.14

    def test_head_mixed_types(self):
        """Test head() with mixed type list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="head",
            args=[Literal(value=["first", 2, False])],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "first"

    def test_last_mixed_types(self):
        """Test last() with mixed type list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="last",
            args=[Literal(value=[1, 2, "last"])],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "last"

    def test_reverse_deeply_nested(self):
        """Test reverse() with deeply nested lists."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="reverse",
            args=[Literal(value=[[[1]], [[2]], [[3]]])],
        )
        result = evaluate_expression(expr, ctx)
        assert len(result.value) == 3
        # Should reverse outer list only
        assert result.value[0].value[0].value[0].value == 3

    def test_size_with_null_elements(self):
        """Test size() counts NULL elements."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="size",
            args=[Literal(value=[1, None, 3, None, 5])],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == 5


class TestStringReverseEdgeCases:
    """Additional tests for reverse() with strings."""

    def test_reverse_unicode_string(self):
        """Test reverse() with Unicode characters."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="reverse",
            args=[Literal(value="Hello 🌍")],
        )
        result = evaluate_expression(expr, ctx)
        # Python string reversal with emoji
        assert result.value == "🌍 olleH"

    def test_reverse_single_char(self):
        """Test reverse() with single character."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="reverse",
            args=[Literal(value="a")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "a"

    def test_reverse_whitespace(self):
        """Test reverse() with whitespace."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="reverse",
            args=[Literal(value="  hello  ")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "  olleh  "
