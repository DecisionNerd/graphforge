"""Unit tests for new string functions (v0.4.0)."""

import pytest

from graphforge.ast.expression import FunctionCall, Literal
from graphforge.executor.evaluator import (
    ExecutionContext,
    evaluate_expression,
)


class TestSplitFunction:
    """Tests for split() function."""

    def test_split_basic(self):
        """Test basic string splitting."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="split",
            args=[Literal(value="a,b,c"), Literal(value=",")],
        )
        result = evaluate_expression(expr, ctx)
        assert len(result.value) == 3
        assert result.value[0].value == "a"
        assert result.value[1].value == "b"
        assert result.value[2].value == "c"

    def test_split_single_element(self):
        """Test splitting with no delimiter in string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="split",
            args=[Literal(value="hello"), Literal(value=",")],
        )
        result = evaluate_expression(expr, ctx)
        assert len(result.value) == 1
        assert result.value[0].value == "hello"

    def test_split_empty_string(self):
        """Test splitting empty string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="split",
            args=[Literal(value=""), Literal(value=",")],
        )
        result = evaluate_expression(expr, ctx)
        assert len(result.value) == 1
        assert result.value[0].value == ""

    def test_split_null_string(self):
        """Test split with NULL string returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="split",
            args=[Literal(value=None), Literal(value=",")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value is None

    def test_split_null_delimiter(self):
        """Test split with NULL delimiter returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="split",
            args=[Literal(value="a,b,c"), Literal(value=None)],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value is None

    def test_split_wrong_arg_count(self):
        """Test split with wrong number of arguments."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="split",
            args=[Literal(value="hello")],
        )
        with pytest.raises(TypeError, match="SPLIT expects 2 arguments"):
            evaluate_expression(expr, ctx)

    def test_split_invalid_type_string(self):
        """Test split with non-string first argument."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="split",
            args=[Literal(value=123), Literal(value=",")],
        )
        with pytest.raises(TypeError, match="SPLIT expects string as first argument"):
            evaluate_expression(expr, ctx)

    def test_split_invalid_type_delimiter(self):
        """Test split with non-string delimiter."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="split",
            args=[Literal(value="hello"), Literal(value=123)],
        )
        with pytest.raises(TypeError, match="SPLIT expects string as delimiter"):
            evaluate_expression(expr, ctx)

    def test_split_multichar_delimiter(self):
        """Test split with multi-character delimiter."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="split",
            args=[Literal(value="a::b::c"), Literal(value="::")],
        )
        result = evaluate_expression(expr, ctx)
        assert len(result.value) == 3
        assert result.value[0].value == "a"
        assert result.value[1].value == "b"
        assert result.value[2].value == "c"


class TestReplaceFunction:
    """Tests for replace() function."""

    def test_replace_basic(self):
        """Test basic string replacement."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="replace",
            args=[Literal(value="hello world"), Literal(value="world"), Literal(value="GraphForge")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "hello GraphForge"

    def test_replace_multiple_occurrences(self):
        """Test replacing multiple occurrences."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="replace",
            args=[Literal(value="aaa"), Literal(value="a"), Literal(value="b")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "bbb"

    def test_replace_no_match(self):
        """Test replace when search string not found."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="replace",
            args=[Literal(value="hello"), Literal(value="x"), Literal(value="y")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "hello"

    def test_replace_null_string(self):
        """Test replace with NULL string returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="replace",
            args=[Literal(value=None), Literal(value="a"), Literal(value="b")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value is None

    def test_replace_empty_search(self):
        """Test replace with empty search string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="replace",
            args=[Literal(value="hello"), Literal(value=""), Literal(value="x")],
        )
        result = evaluate_expression(expr, ctx)
        # Python's replace("", "x") inserts x between every character
        assert "x" in result.value

    def test_replace_wrong_arg_count(self):
        """Test replace with wrong number of arguments."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="replace",
            args=[Literal(value="hello"), Literal(value="l")],
        )
        with pytest.raises(TypeError, match="REPLACE expects 3 arguments"):
            evaluate_expression(expr, ctx)


class TestLeftFunction:
    """Tests for left() function."""

    def test_left_basic(self):
        """Test basic left substring."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="left",
            args=[Literal(value="hello"), Literal(value=3)],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "hel"

    def test_left_full_string(self):
        """Test left with length >= string length."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="left",
            args=[Literal(value="hello"), Literal(value=10)],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "hello"

    def test_left_zero_length(self):
        """Test left with zero length."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="left",
            args=[Literal(value="hello"), Literal(value=0)],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == ""

    def test_left_negative_length(self):
        """Test left with negative length."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="left",
            args=[Literal(value="hello"), Literal(value=-5)],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == ""

    def test_left_null_string(self):
        """Test left with NULL string returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="left",
            args=[Literal(value=None), Literal(value=3)],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value is None

    def test_left_wrong_arg_count(self):
        """Test left with wrong number of arguments."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="left",
            args=[Literal(value="hello")],
        )
        with pytest.raises(TypeError, match="LEFT expects 2 arguments"):
            evaluate_expression(expr, ctx)

    def test_left_invalid_length_type(self):
        """Test left with non-integer length."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="left",
            args=[Literal(value="hello"), Literal(value="3")],
        )
        with pytest.raises(TypeError, match="LEFT expects integer as length"):
            evaluate_expression(expr, ctx)


class TestRightFunction:
    """Tests for right() function."""

    def test_right_basic(self):
        """Test basic right substring."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="right",
            args=[Literal(value="hello"), Literal(value=2)],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "lo"

    def test_right_full_string(self):
        """Test right with length >= string length."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="right",
            args=[Literal(value="hello"), Literal(value=10)],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "hello"

    def test_right_zero_length(self):
        """Test right with zero length."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="right",
            args=[Literal(value="hello"), Literal(value=0)],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == ""

    def test_right_negative_length(self):
        """Test right with negative length."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="right",
            args=[Literal(value="hello"), Literal(value=-5)],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == ""

    def test_right_null_string(self):
        """Test right with NULL string returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="right",
            args=[Literal(value=None), Literal(value=2)],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value is None


class TestLtrimFunction:
    """Tests for ltrim() function."""

    def test_ltrim_basic(self):
        """Test basic left trim."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="ltrim",
            args=[Literal(value="  hello  ")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "hello  "

    def test_ltrim_no_leading_space(self):
        """Test ltrim with no leading whitespace."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="ltrim",
            args=[Literal(value="hello  ")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "hello  "

    def test_ltrim_empty_string(self):
        """Test ltrim with empty string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="ltrim",
            args=[Literal(value="")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == ""

    def test_ltrim_only_spaces(self):
        """Test ltrim with only spaces."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="ltrim",
            args=[Literal(value="     ")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == ""

    def test_ltrim_null(self):
        """Test ltrim with NULL returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="ltrim",
            args=[Literal(value=None)],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value is None

    def test_ltrim_tabs_newlines(self):
        """Test ltrim with tabs and newlines."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="ltrim",
            args=[Literal(value="\t\n  hello")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "hello"


class TestRtrimFunction:
    """Tests for rtrim() function."""

    def test_rtrim_basic(self):
        """Test basic right trim."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="rtrim",
            args=[Literal(value="  hello  ")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "  hello"

    def test_rtrim_no_trailing_space(self):
        """Test rtrim with no trailing whitespace."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="rtrim",
            args=[Literal(value="  hello")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "  hello"

    def test_rtrim_empty_string(self):
        """Test rtrim with empty string."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="rtrim",
            args=[Literal(value="")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == ""

    def test_rtrim_only_spaces(self):
        """Test rtrim with only spaces."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="rtrim",
            args=[Literal(value="     ")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == ""

    def test_rtrim_null(self):
        """Test rtrim with NULL returns NULL."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="rtrim",
            args=[Literal(value=None)],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value is None

    def test_rtrim_tabs_newlines(self):
        """Test rtrim with tabs and newlines."""
        ctx = ExecutionContext()
        expr = FunctionCall(
            name="rtrim",
            args=[Literal(value="hello\t\n  ")],
        )
        result = evaluate_expression(expr, ctx)
        assert result.value == "hello"
