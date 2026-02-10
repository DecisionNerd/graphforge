"""Unit tests for list functions."""

import pytest

from graphforge.ast.expression import FunctionCall, Literal
from graphforge.executor.evaluator import (
    ExecutionContext,
    evaluate_expression,
)
from graphforge.types.values import (
    CypherInt,
    CypherList,
    CypherNull,
    CypherString,
)


class TestTailFunction:
    """Tests for tail() function."""

    def test_tail_basic_list(self):
        """Test tail() with a basic list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="tail",
            args=[Literal(value=[1, 2, 3, 4])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherList)
        assert len(result.value) == 3
        assert result.value[0].value == 2
        assert result.value[1].value == 3
        assert result.value[2].value == 4

    def test_tail_single_element_list(self):
        """Test tail() with a single-element list returns empty list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="tail",
            args=[Literal(value=[1])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherList)
        assert len(result.value) == 0

    def test_tail_empty_list(self):
        """Test tail() with empty list returns empty list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="tail",
            args=[Literal(value=[])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherList)
        assert len(result.value) == 0

    def test_tail_null_input(self):
        """Test tail() with NULL input returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="tail",
            args=[Literal(value=None)],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherNull)

    def test_tail_nested_lists(self):
        """Test tail() with nested lists."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="tail",
            args=[Literal(value=[[1, 2], [3, 4], [5, 6]])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherList)
        assert len(result.value) == 2
        assert isinstance(result.value[0], CypherList)
        assert result.value[0].value[0].value == 3


class TestHeadFunction:
    """Tests for head() function with lists."""

    def test_head_basic_list(self):
        """Test head() with a basic list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="head",
            args=[Literal(value=[1, 2, 3])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 1

    def test_head_empty_list(self):
        """Test head() with empty list returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="head",
            args=[Literal(value=[])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherNull)

    def test_head_null_input(self):
        """Test head() with NULL input returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="head",
            args=[Literal(value=None)],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherNull)

    def test_head_string_list(self):
        """Test head() with a list of strings."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="head",
            args=[Literal(value=["a", "b", "c"])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "a"

    def test_head_nested_list(self):
        """Test head() with nested lists."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="head",
            args=[Literal(value=[[1, 2], [3, 4]])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherList)
        assert len(result.value) == 2
        assert result.value[0].value == 1


class TestLastFunction:
    """Tests for last() function with lists."""

    def test_last_basic_list(self):
        """Test last() with a basic list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="last",
            args=[Literal(value=[1, 2, 3])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 3

    def test_last_empty_list(self):
        """Test last() with empty list returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="last",
            args=[Literal(value=[])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherNull)

    def test_last_null_input(self):
        """Test last() with NULL input returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="last",
            args=[Literal(value=None)],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherNull)

    def test_last_string_list(self):
        """Test last() with a list of strings."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="last",
            args=[Literal(value=["a", "b", "c"])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "c"

    def test_last_single_element(self):
        """Test last() with single-element list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="last",
            args=[Literal(value=[42])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 42


class TestReverseFunction:
    """Tests for reverse() function with lists and strings."""

    def test_reverse_basic_list(self):
        """Test reverse() with a basic list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="reverse",
            args=[Literal(value=[1, 2, 3])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherList)
        assert len(result.value) == 3
        assert result.value[0].value == 3
        assert result.value[1].value == 2
        assert result.value[2].value == 1

    def test_reverse_empty_list(self):
        """Test reverse() with empty list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="reverse",
            args=[Literal(value=[])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherList)
        assert len(result.value) == 0

    def test_reverse_string(self):
        """Test reverse() with a string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="reverse",
            args=[Literal(value="hello")],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == "olleh"

    def test_reverse_empty_string(self):
        """Test reverse() with empty string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="reverse",
            args=[Literal(value="")],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherString)
        assert result.value == ""

    def test_reverse_null_input(self):
        """Test reverse() with NULL input returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="reverse",
            args=[Literal(value=None)],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherNull)

    def test_reverse_nested_list(self):
        """Test reverse() with nested lists."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="reverse",
            args=[Literal(value=[[1, 2], [3, 4]])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherList)
        assert len(result.value) == 2
        # First element after reverse is [3, 4]
        assert isinstance(result.value[0], CypherList)
        assert result.value[0].value[0].value == 3


class TestRangeFunction:
    """Tests for range() function."""

    def test_range_basic_positive(self):
        """Test range() with positive integers."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value=1), Literal(value=5)],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherList)
        assert len(result.value) == 5
        assert [x.value for x in result.value] == [1, 2, 3, 4, 5]

    def test_range_with_step(self):
        """Test range() with custom step."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value=0), Literal(value=10), Literal(value=2)],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherList)
        assert [x.value for x in result.value] == [0, 2, 4, 6, 8, 10]

    def test_range_negative_step(self):
        """Test range() with negative step."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value=5), Literal(value=1), Literal(value=-1)],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherList)
        assert [x.value for x in result.value] == [5, 4, 3, 2, 1]

    def test_range_single_value(self):
        """Test range() when start equals end."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value=5), Literal(value=5)],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherList)
        assert len(result.value) == 1
        assert result.value[0].value == 5

    def test_range_empty_result(self):
        """Test range() that produces empty list (start > end with positive step)."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value=5), Literal(value=1)],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherList)
        assert len(result.value) == 0

    def test_range_zero_step_error(self):
        """Test range() with step=0 raises error."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value=1), Literal(value=5), Literal(value=0)],
        )
        with pytest.raises(ValueError, match="step cannot be zero"):
            evaluate_expression(expr, ctx)

    def test_range_invalid_start_type(self):
        """Test range() with non-integer start raises error."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value="1"), Literal(value=5)],
        )
        with pytest.raises(TypeError, match="start must be integer"):
            evaluate_expression(expr, ctx)

    def test_range_invalid_end_type(self):
        """Test range() with non-integer end raises error."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value=1), Literal(value="5")],
        )
        with pytest.raises(TypeError, match="end must be integer"):
            evaluate_expression(expr, ctx)

    def test_range_invalid_step_type(self):
        """Test range() with non-integer step raises error."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="range",
            args=[Literal(value=1), Literal(value=5), Literal(value=1.5)],
        )
        with pytest.raises(TypeError, match="step must be integer"):
            evaluate_expression(expr, ctx)


class TestSizeFunction:
    """Tests for size() function with lists."""

    def test_size_basic_list(self):
        """Test size() with a basic list."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="size",
            args=[Literal(value=[1, 2, 3])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 3

    def test_size_empty_list(self):
        """Test size() with empty list returns 0."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="size",
            args=[Literal(value=[])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 0

    def test_size_null_input(self):
        """Test size() with NULL input returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="size",
            args=[Literal(value=None)],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherNull)

    def test_size_nested_list(self):
        """Test size() with nested lists counts outer list only."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="size",
            args=[Literal(value=[[1, 2], [3]])],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 2

    def test_size_string(self):
        """Test size() with string returns length."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="size",
            args=[Literal(value="hello")],
        )
        result = evaluate_expression(expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 5


class TestListFunctionCombinations:
    """Tests for combinations of list functions."""

    def test_head_tail_composition(self):
        """Test head(tail([1, 2, 3])) = 2."""
        ctx = ExecutionContext()
        tail_expr = FunctionCall(
            name="tail",
            args=[Literal(value=[1, 2, 3])],
        )
        head_expr = FunctionCall(
            name="head",
            args=[tail_expr],
        )
        result = evaluate_expression(head_expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 2

    def test_size_tail_composition(self):
        """Test size(tail([1, 2, 3])) = 2."""
        ctx = ExecutionContext()
        tail_expr = FunctionCall(
            name="tail",
            args=[Literal(value=[1, 2, 3])],
        )
        size_expr = FunctionCall(
            name="size",
            args=[tail_expr],
        )
        result = evaluate_expression(size_expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 2

    def test_reverse_reverse_identity(self):
        """Test reverse(reverse(list)) = list."""
        ctx = ExecutionContext()
        inner_reverse = FunctionCall(
            name="reverse",
            args=[Literal(value=[1, 2, 3])],
        )
        outer_reverse = FunctionCall(
            name="reverse",
            args=[inner_reverse],
        )
        result = evaluate_expression(outer_reverse, ctx)
        assert isinstance(result, CypherList)
        assert [x.value for x in result.value] == [1, 2, 3]

    def test_last_range(self):
        """Test last(range(1, 5)) = 5."""
        ctx = ExecutionContext()
        range_expr = FunctionCall(
            name="range",
            args=[Literal(value=1), Literal(value=5)],
        )
        last_expr = FunctionCall(
            name="last",
            args=[range_expr],
        )
        result = evaluate_expression(last_expr, ctx)
        assert isinstance(result, CypherInt)
        assert result.value == 5
