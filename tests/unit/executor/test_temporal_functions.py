"""Unit tests for temporal functions in evaluator.

Tests temporal constructor and accessor functions:
- date(), datetime(), time(), duration()
- year(), month(), day(), hour(), minute(), second()
"""

import datetime

import pytest

from graphforge.ast.expression import FunctionCall, Literal
from graphforge.executor.evaluator import ExecutionContext, evaluate_expression
from graphforge.types.values import (
    CypherDate,
    CypherDateTime,
    CypherDuration,
    CypherInt,
    CypherString,
    CypherTime,
)

pytestmark = pytest.mark.unit


class TestTemporalConstructors:
    """Tests for temporal constructor functions."""

    def test_date_with_string(self):
        """Test date(string) function."""
        func = FunctionCall(name="date", args=[Literal(value="2023-01-15")])
        ctx = ExecutionContext()

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherDate)
        assert result.value == datetime.date(2023, 1, 15)

    def test_date_no_args(self):
        """Test date() function returns current date."""
        func = FunctionCall(name="date", args=[])
        ctx = ExecutionContext()

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherDate)
        # Check it's a reasonable date (today's date)
        assert result.value == datetime.date.today()

    def test_datetime_with_string(self):
        """Test datetime(string) function."""
        func = FunctionCall(name="datetime", args=[Literal(value="2023-01-15T10:30:00")])
        ctx = ExecutionContext()

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherDateTime)
        expected = datetime.datetime(2023, 1, 15, 10, 30, 0)
        assert result.value == expected

    def test_datetime_with_timezone(self):
        """Test datetime(string) with timezone."""
        func = FunctionCall(name="datetime", args=[Literal(value="2023-01-15T10:30:00+00:00")])
        ctx = ExecutionContext()

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherDateTime)
        assert result.value.tzinfo is not None

    def test_datetime_no_args(self):
        """Test datetime() function returns current datetime."""
        func = FunctionCall(name="datetime", args=[])
        ctx = ExecutionContext()

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherDateTime)
        # Check it's within 1 second of now (reasonable tolerance for test)
        now = datetime.datetime.now()
        diff = abs((result.value.replace(tzinfo=None) - now).total_seconds())
        assert diff < 1.0

    def test_time_with_string(self):
        """Test time(string) function."""
        func = FunctionCall(name="time", args=[Literal(value="10:30:00")])
        ctx = ExecutionContext()

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherTime)
        assert result.value == datetime.time(10, 30, 0)

    def test_time_no_args(self):
        """Test time() function returns current time."""
        func = FunctionCall(name="time", args=[])
        ctx = ExecutionContext()

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherTime)
        # Check it's a reasonable time
        assert isinstance(result.value, datetime.time)

    def test_duration_with_string(self):
        """Test duration(string) function."""
        func = FunctionCall(name="duration", args=[Literal(value="P1DT2H30M")])
        ctx = ExecutionContext()

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherDuration)
        expected = datetime.timedelta(days=1, hours=2, minutes=30)
        assert result.value == expected

    def test_duration_requires_argument(self):
        """Test duration() requires an argument."""
        func = FunctionCall(name="duration", args=[])
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="DURATION expects 1 argument"):
            evaluate_expression(func, ctx)


class TestTemporalAccessors:
    """Tests for temporal accessor functions."""

    def test_year_from_date(self):
        """Test year() extraction from date."""
        date_val = CypherDate("2023-01-15")
        ctx = ExecutionContext()
        ctx.bind("d", date_val)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="year", args=[Variable(name="d")])

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 2023

    def test_year_from_datetime(self):
        """Test year() extraction from datetime."""
        dt_val = CypherDateTime("2023-01-15T10:30:00")
        ctx = ExecutionContext()
        ctx.bind("dt", dt_val)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="year", args=[Variable(name="dt")])

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 2023

    def test_month_from_date(self):
        """Test month() extraction from date."""
        date_val = CypherDate("2023-05-15")
        ctx = ExecutionContext()
        ctx.bind("d", date_val)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="month", args=[Variable(name="d")])

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 5

    def test_day_from_date(self):
        """Test day() extraction from date."""
        date_val = CypherDate("2023-01-25")
        ctx = ExecutionContext()
        ctx.bind("d", date_val)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="day", args=[Variable(name="d")])

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 25

    def test_hour_from_datetime(self):
        """Test hour() extraction from datetime."""
        dt_val = CypherDateTime("2023-01-15T14:30:00")
        ctx = ExecutionContext()
        ctx.bind("dt", dt_val)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="hour", args=[Variable(name="dt")])

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 14

    def test_hour_from_time(self):
        """Test hour() extraction from time."""
        time_val = CypherTime("14:30:00")
        ctx = ExecutionContext()
        ctx.bind("t", time_val)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="hour", args=[Variable(name="t")])

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 14

    def test_minute_from_datetime(self):
        """Test minute() extraction from datetime."""
        dt_val = CypherDateTime("2023-01-15T14:35:00")
        ctx = ExecutionContext()
        ctx.bind("dt", dt_val)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="minute", args=[Variable(name="dt")])

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 35

    def test_minute_from_time(self):
        """Test minute() extraction from time."""
        time_val = CypherTime("14:35:00")
        ctx = ExecutionContext()
        ctx.bind("t", time_val)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="minute", args=[Variable(name="t")])

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 35

    def test_second_from_datetime(self):
        """Test second() extraction from datetime."""
        dt_val = CypherDateTime("2023-01-15T14:30:45")
        ctx = ExecutionContext()
        ctx.bind("dt", dt_val)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="second", args=[Variable(name="dt")])

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 45

    def test_second_from_time(self):
        """Test second() extraction from time."""
        time_val = CypherTime("14:30:45")
        ctx = ExecutionContext()
        ctx.bind("t", time_val)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="second", args=[Variable(name="t")])

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 45


class TestTemporalFunctionErrors:
    """Tests for temporal function error handling."""

    def test_date_invalid_type(self):
        """Test date() with invalid argument type."""
        func = FunctionCall(name="date", args=[Literal(value=123)])
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="DATE expects string"):
            evaluate_expression(func, ctx)

    def test_datetime_invalid_type(self):
        """Test datetime() with invalid argument type."""
        func = FunctionCall(name="datetime", args=[Literal(value=123)])
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="DATETIME expects string"):
            evaluate_expression(func, ctx)

    def test_time_invalid_type(self):
        """Test time() with invalid argument type."""
        func = FunctionCall(name="time", args=[Literal(value=123)])
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="TIME expects string"):
            evaluate_expression(func, ctx)

    def test_duration_invalid_type(self):
        """Test duration() with invalid argument type."""
        func = FunctionCall(name="duration", args=[Literal(value=123)])
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="DURATION expects string"):
            evaluate_expression(func, ctx)

    def test_year_invalid_type(self):
        """Test year() with invalid argument type."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherString("not a date"))

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="year", args=[Variable(name="x")])

        with pytest.raises(TypeError, match="YEAR expects date or datetime"):
            evaluate_expression(func, ctx)

    def test_hour_invalid_type(self):
        """Test hour() with invalid argument type."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherString("not a time"))

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="hour", args=[Variable(name="x")])

        with pytest.raises(TypeError, match="HOUR expects datetime or time"):
            evaluate_expression(func, ctx)

    def test_year_wrong_arg_count(self):
        """Test year() with wrong number of arguments."""
        func = FunctionCall(name="year", args=[])
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="YEAR expects 1 argument, got 0"):
            evaluate_expression(func, ctx)

    def test_month_wrong_arg_count(self):
        """Test month() with wrong number of arguments."""
        func = FunctionCall(
            name="month", args=[Literal(value="2023-01-15"), Literal(value="extra")]
        )
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="MONTH expects 1 argument, got 2"):
            evaluate_expression(func, ctx)

    def test_hour_wrong_arg_count(self):
        """Test hour() with wrong number of arguments."""
        func = FunctionCall(name="hour", args=[])
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="HOUR expects 1 argument, got 0"):
            evaluate_expression(func, ctx)
