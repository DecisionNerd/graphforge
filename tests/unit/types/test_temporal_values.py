"""Unit tests for temporal CypherValue types.

Tests DATE, DATETIME, TIME, and DURATION types including:
- Construction from Python objects and ISO 8601 strings
- Comparison operations
- NULL handling
- Type conversions
"""

import datetime

import pytest

from graphforge.types.values import (
    CypherBool,
    CypherDate,
    CypherDateTime,
    CypherDuration,
    CypherNull,
    CypherTime,
    CypherType,
    from_python,
)

pytestmark = pytest.mark.unit


class TestCypherDate:
    """Tests for CypherDate type."""

    def test_construct_from_date(self):
        """Test construction from datetime.date object."""
        d = datetime.date(2023, 1, 15)
        cypher_date = CypherDate(d)
        assert cypher_date.type == CypherType.DATE
        assert cypher_date.value == d

    def test_construct_from_iso_string(self):
        """Test construction from ISO 8601 date string."""
        cypher_date = CypherDate("2023-01-15")
        assert cypher_date.type == CypherType.DATE
        assert cypher_date.value == datetime.date(2023, 1, 15)

    def test_construct_from_datetime(self):
        """Test construction from datetime.datetime (extracts date)."""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 0)
        cypher_date = CypherDate(dt)
        assert cypher_date.type == CypherType.DATE
        assert cypher_date.value == datetime.date(2023, 1, 15)

    def test_equality(self):
        """Test date equality comparison."""
        d1 = CypherDate("2023-01-15")
        d2 = CypherDate("2023-01-15")
        d3 = CypherDate("2023-01-16")

        result = d1.equals(d2)
        assert isinstance(result, CypherBool)
        assert result.value is True

        result = d1.equals(d3)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_less_than(self):
        """Test date less-than comparison."""
        d1 = CypherDate("2023-01-15")
        d2 = CypherDate("2023-01-16")

        result = d1.less_than(d2)
        assert isinstance(result, CypherBool)
        assert result.value is True

        result = d2.less_than(d1)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_null_propagation(self):
        """Test NULL propagation in comparisons."""
        d = CypherDate("2023-01-15")
        null = CypherNull()

        assert isinstance(d.equals(null), CypherNull)
        assert isinstance(null.equals(d), CypherNull)
        assert isinstance(d.less_than(null), CypherNull)
        assert isinstance(null.less_than(d), CypherNull)

    def test_to_python(self):
        """Test conversion to Python type."""
        d = datetime.date(2023, 1, 15)
        cypher_date = CypherDate(d)
        assert cypher_date.to_python() == d

    def test_repr(self):
        """Test string representation."""
        cypher_date = CypherDate("2023-01-15")
        assert repr(cypher_date) == "CypherDate('2023-01-15')"


class TestCypherDateTime:
    """Tests for CypherDateTime type."""

    def test_construct_from_datetime(self):
        """Test construction from datetime.datetime object."""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 0)
        cypher_datetime = CypherDateTime(dt)
        assert cypher_datetime.type == CypherType.DATETIME
        assert cypher_datetime.value == dt

    def test_construct_from_iso_string(self):
        """Test construction from ISO 8601 datetime string."""
        cypher_datetime = CypherDateTime("2023-01-15T10:30:00")
        assert cypher_datetime.type == CypherType.DATETIME
        expected = datetime.datetime(2023, 1, 15, 10, 30, 0)
        assert cypher_datetime.value == expected

    def test_construct_with_timezone(self):
        """Test construction with timezone information."""
        cypher_datetime = CypherDateTime("2023-01-15T10:30:00+00:00")
        assert cypher_datetime.type == CypherType.DATETIME
        assert cypher_datetime.value.tzinfo is not None

    def test_equality(self):
        """Test datetime equality comparison."""
        dt1 = CypherDateTime("2023-01-15T10:30:00")
        dt2 = CypherDateTime("2023-01-15T10:30:00")
        dt3 = CypherDateTime("2023-01-15T10:30:01")

        result = dt1.equals(dt2)
        assert isinstance(result, CypherBool)
        assert result.value is True

        result = dt1.equals(dt3)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_less_than(self):
        """Test datetime less-than comparison."""
        dt1 = CypherDateTime("2023-01-15T10:30:00")
        dt2 = CypherDateTime("2023-01-15T10:30:01")

        result = dt1.less_than(dt2)
        assert isinstance(result, CypherBool)
        assert result.value is True

        result = dt2.less_than(dt1)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_null_propagation(self):
        """Test NULL propagation in comparisons."""
        dt = CypherDateTime("2023-01-15T10:30:00")
        null = CypherNull()

        assert isinstance(dt.equals(null), CypherNull)
        assert isinstance(dt.less_than(null), CypherNull)

    def test_to_python(self):
        """Test conversion to Python type."""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 0)
        cypher_datetime = CypherDateTime(dt)
        assert cypher_datetime.to_python() == dt

    def test_repr(self):
        """Test string representation."""
        cypher_datetime = CypherDateTime("2023-01-15T10:30:00")
        assert "CypherDateTime" in repr(cypher_datetime)
        assert "2023-01-15" in repr(cypher_datetime)


class TestCypherTime:
    """Tests for CypherTime type."""

    def test_construct_from_time(self):
        """Test construction from datetime.time object."""
        t = datetime.time(10, 30, 0)
        cypher_time = CypherTime(t)
        assert cypher_time.type == CypherType.TIME
        assert cypher_time.value == t

    def test_construct_from_iso_string(self):
        """Test construction from ISO 8601 time string."""
        cypher_time = CypherTime("10:30:00")
        assert cypher_time.type == CypherType.TIME
        expected = datetime.time(10, 30, 0)
        assert cypher_time.value == expected

    def test_construct_from_datetime(self):
        """Test construction from datetime.datetime (extracts time)."""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 0)
        cypher_time = CypherTime(dt)
        assert cypher_time.type == CypherType.TIME
        assert cypher_time.value == datetime.time(10, 30, 0)

    def test_equality(self):
        """Test time equality comparison."""
        t1 = CypherTime("10:30:00")
        t2 = CypherTime("10:30:00")
        t3 = CypherTime("10:30:01")

        result = t1.equals(t2)
        assert isinstance(result, CypherBool)
        assert result.value is True

        result = t1.equals(t3)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_less_than(self):
        """Test time less-than comparison."""
        t1 = CypherTime("10:30:00")
        t2 = CypherTime("10:30:01")

        result = t1.less_than(t2)
        assert isinstance(result, CypherBool)
        assert result.value is True

        result = t2.less_than(t1)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_null_propagation(self):
        """Test NULL propagation in comparisons."""
        t = CypherTime("10:30:00")
        null = CypherNull()

        assert isinstance(t.equals(null), CypherNull)
        assert isinstance(t.less_than(null), CypherNull)

    def test_to_python(self):
        """Test conversion to Python type."""
        t = datetime.time(10, 30, 0)
        cypher_time = CypherTime(t)
        assert cypher_time.to_python() == t

    def test_repr(self):
        """Test string representation."""
        cypher_time = CypherTime("10:30:00")
        assert repr(cypher_time) == "CypherTime('10:30:00')"


class TestCypherDuration:
    """Tests for CypherDuration type."""

    def test_construct_from_timedelta(self):
        """Test construction from datetime.timedelta object."""
        td = datetime.timedelta(days=1, hours=2, minutes=30)
        cypher_duration = CypherDuration(td)
        assert cypher_duration.type == CypherType.DURATION
        assert cypher_duration.value == td

    def test_construct_from_iso_string(self):
        """Test construction from ISO 8601 duration string."""
        cypher_duration = CypherDuration("P1DT2H30M")
        assert cypher_duration.type == CypherType.DURATION
        expected = datetime.timedelta(days=1, hours=2, minutes=30)
        assert cypher_duration.value == expected

    def test_equality(self):
        """Test duration equality comparison."""
        dur1 = CypherDuration("P1D")
        dur2 = CypherDuration("P1D")
        dur3 = CypherDuration("P2D")

        result = dur1.equals(dur2)
        assert isinstance(result, CypherBool)
        assert result.value is True

        result = dur1.equals(dur3)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_null_propagation(self):
        """Test NULL propagation in comparisons."""
        dur = CypherDuration("P1D")
        null = CypherNull()

        assert isinstance(dur.equals(null), CypherNull)

    def test_to_python(self):
        """Test conversion to Python type."""
        td = datetime.timedelta(days=1, hours=2)
        cypher_duration = CypherDuration(td)
        assert cypher_duration.to_python() == td

    def test_repr(self):
        """Test string representation."""
        cypher_duration = CypherDuration("P1DT2H30M")
        assert "CypherDuration" in repr(cypher_duration)
        assert "P1DT2H30M" in repr(cypher_duration)


class TestFromPython:
    """Tests for from_python() with temporal types."""

    def test_from_date(self):
        """Test converting Python date to CypherDate."""
        d = datetime.date(2023, 1, 15)
        result = from_python(d)
        assert isinstance(result, CypherDate)
        assert result.value == d

    def test_from_datetime(self):
        """Test converting Python datetime to CypherDateTime."""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 0)
        result = from_python(dt)
        assert isinstance(result, CypherDateTime)
        assert result.value == dt

    def test_from_time(self):
        """Test converting Python time to CypherTime."""
        t = datetime.time(10, 30, 0)
        result = from_python(t)
        assert isinstance(result, CypherTime)
        assert result.value == t

    def test_from_timedelta(self):
        """Test converting Python timedelta to CypherDuration."""
        td = datetime.timedelta(days=1, hours=2)
        result = from_python(td)
        assert isinstance(result, CypherDuration)
        assert result.value == td


class TestTemporalComparisons:
    """Tests for cross-type temporal comparisons."""

    def test_date_not_comparable_to_datetime(self):
        """Test that dates and datetimes are not directly comparable."""
        d = CypherDate("2023-01-15")
        dt = CypherDateTime("2023-01-15T10:30:00")

        result = d.equals(dt)
        assert isinstance(result, CypherBool)
        assert result.value is False

        result = d.less_than(dt)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_date_not_comparable_to_time(self):
        """Test that dates and times are not directly comparable."""
        d = CypherDate("2023-01-15")
        t = CypherTime("10:30:00")

        result = d.equals(t)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_datetime_not_comparable_to_time(self):
        """Test that datetimes and times are not directly comparable."""
        dt = CypherDateTime("2023-01-15T10:30:00")
        t = CypherTime("10:30:00")

        result = dt.equals(t)
        assert isinstance(result, CypherBool)
        assert result.value is False
