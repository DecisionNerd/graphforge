"""Unit tests for temporal truncate() and arithmetic operations."""

import pytest

from graphforge.api import GraphForge
from graphforge.types.values import (
    CypherDate,
    CypherDateTime,
    CypherDuration,
    CypherNull,
    CypherTime,
)


class TestTemporalTruncate:
    """Test truncate() function for temporal types."""

    def test_truncate_datetime_year(self):
        """Truncate datetime to year."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN truncate('year', datetime('2023-06-15T14:30:45Z')) AS truncated"
        )
        assert isinstance(result[0]["truncated"], CypherDateTime)
        assert result[0]["truncated"].value.isoformat() == "2023-01-01T00:00:00+00:00"

    def test_truncate_datetime_month(self):
        """Truncate datetime to month."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN truncate('month', datetime('2023-06-15T14:30:45Z')) AS truncated"
        )
        assert isinstance(result[0]["truncated"], CypherDateTime)
        assert result[0]["truncated"].value.isoformat() == "2023-06-01T00:00:00+00:00"

    def test_truncate_datetime_day(self):
        """Truncate datetime to day."""
        gf = GraphForge()
        result = gf.execute("RETURN truncate('day', datetime('2023-06-15T14:30:45Z')) AS truncated")
        assert isinstance(result[0]["truncated"], CypherDateTime)
        assert result[0]["truncated"].value.isoformat() == "2023-06-15T00:00:00+00:00"

    def test_truncate_datetime_hour(self):
        """Truncate datetime to hour."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN truncate('hour', datetime('2023-06-15T14:30:45Z')) AS truncated"
        )
        assert isinstance(result[0]["truncated"], CypherDateTime)
        assert result[0]["truncated"].value.isoformat() == "2023-06-15T14:00:00+00:00"

    def test_truncate_datetime_minute(self):
        """Truncate datetime to minute."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN truncate('minute', datetime('2023-06-15T14:30:45Z')) AS truncated"
        )
        assert isinstance(result[0]["truncated"], CypherDateTime)
        assert result[0]["truncated"].value.isoformat() == "2023-06-15T14:30:00+00:00"

    def test_truncate_datetime_second(self):
        """Truncate datetime to second."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN truncate('second', datetime('2023-06-15T14:30:45.123456Z')) AS truncated"
        )
        assert isinstance(result[0]["truncated"], CypherDateTime)
        assert result[0]["truncated"].value.isoformat() == "2023-06-15T14:30:45+00:00"

    def test_truncate_datetime_millisecond(self):
        """Truncate datetime to millisecond."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN truncate('millisecond', datetime('2023-06-15T14:30:45.123456Z')) AS truncated"
        )
        assert isinstance(result[0]["truncated"], CypherDateTime)
        # Should round to nearest ms: 123456µs → 123000µs
        assert result[0]["truncated"].value.isoformat() == "2023-06-15T14:30:45.123000+00:00"

    def test_truncate_datetime_microsecond(self):
        """Truncate datetime to microsecond (no-op)."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN truncate('microsecond', datetime('2023-06-15T14:30:45.123456Z')) AS truncated"
        )
        assert isinstance(result[0]["truncated"], CypherDateTime)
        assert result[0]["truncated"].value.isoformat() == "2023-06-15T14:30:45.123456+00:00"

    def test_truncate_date_year(self):
        """Truncate date to year."""
        gf = GraphForge()
        result = gf.execute("RETURN truncate('year', date('2023-06-15')) AS truncated")
        assert isinstance(result[0]["truncated"], CypherDate)
        assert result[0]["truncated"].value.isoformat() == "2023-01-01"

    def test_truncate_date_month(self):
        """Truncate date to month."""
        gf = GraphForge()
        result = gf.execute("RETURN truncate('month', date('2023-06-15')) AS truncated")
        assert isinstance(result[0]["truncated"], CypherDate)
        assert result[0]["truncated"].value.isoformat() == "2023-06-01"

    def test_truncate_date_day(self):
        """Truncate date to day (no-op)."""
        gf = GraphForge()
        result = gf.execute("RETURN truncate('day', date('2023-06-15')) AS truncated")
        assert isinstance(result[0]["truncated"], CypherDate)
        assert result[0]["truncated"].value.isoformat() == "2023-06-15"

    def test_truncate_time_hour(self):
        """Truncate time to hour."""
        gf = GraphForge()
        result = gf.execute("RETURN truncate('hour', time('14:30:45')) AS truncated")
        assert isinstance(result[0]["truncated"], CypherTime)
        # Time includes timezone info, check hour component
        assert result[0]["truncated"].value.hour == 14
        assert result[0]["truncated"].value.minute == 0
        assert result[0]["truncated"].value.second == 0

    def test_truncate_time_minute(self):
        """Truncate time to minute."""
        gf = GraphForge()
        result = gf.execute("RETURN truncate('minute', time('14:30:45')) AS truncated")
        assert isinstance(result[0]["truncated"], CypherTime)
        assert result[0]["truncated"].value.hour == 14
        assert result[0]["truncated"].value.minute == 30
        assert result[0]["truncated"].value.second == 0

    def test_truncate_time_second(self):
        """Truncate time to second."""
        gf = GraphForge()
        result = gf.execute("RETURN truncate('second', time('14:30:45.123456')) AS truncated")
        assert isinstance(result[0]["truncated"], CypherTime)
        assert result[0]["truncated"].value.hour == 14
        assert result[0]["truncated"].value.minute == 30
        assert result[0]["truncated"].value.second == 45
        assert result[0]["truncated"].value.microsecond == 0

    def test_truncate_null_returns_null(self):
        """truncate() with NULL returns NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN truncate('year', null) AS truncated")
        assert isinstance(result[0]["truncated"], CypherNull)


class TestTemporalArithmeticAddition:
    """Test temporal + duration arithmetic."""

    def test_datetime_plus_duration_days(self):
        """datetime + duration (days)."""
        gf = GraphForge()
        result = gf.execute("RETURN datetime('2023-06-15T12:00:00Z') + duration('P7D') AS result")
        assert isinstance(result[0]["result"], CypherDateTime)
        assert result[0]["result"].value.isoformat() == "2023-06-22T12:00:00+00:00"

    def test_datetime_plus_duration_months(self):
        """datetime + duration (months)."""
        gf = GraphForge()
        result = gf.execute("RETURN datetime('2023-01-15T12:00:00Z') + duration('P1M') AS result")
        assert isinstance(result[0]["result"], CypherDateTime)
        assert result[0]["result"].value.isoformat() == "2023-02-15T12:00:00+00:00"

    def test_datetime_plus_duration_years(self):
        """datetime + duration (years)."""
        gf = GraphForge()
        result = gf.execute("RETURN datetime('2023-06-15T12:00:00Z') + duration('P1Y') AS result")
        assert isinstance(result[0]["result"], CypherDateTime)
        assert result[0]["result"].value.isoformat() == "2024-06-15T12:00:00+00:00"

    def test_datetime_plus_duration_hours(self):
        """datetime + duration (hours)."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN datetime('2023-06-15T12:00:00Z') + duration('PT2H30M') AS result"
        )
        assert isinstance(result[0]["result"], CypherDateTime)
        assert result[0]["result"].value.isoformat() == "2023-06-15T14:30:00+00:00"

    def test_datetime_plus_duration_complex(self):
        """datetime + duration (complex)."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN datetime('2023-01-15T10:00:00Z') + duration('P1Y2M10DT2H30M') AS result"
        )
        assert isinstance(result[0]["result"], CypherDateTime)
        # 1 year 2 months = 2024-03-15, + 10 days = 2024-03-25, + 2h30m = 2024-03-25T12:30:00Z
        assert result[0]["result"].value.isoformat() == "2024-03-25T12:30:00+00:00"

    def test_duration_plus_datetime(self):
        """duration + datetime (commutative)."""
        gf = GraphForge()
        result = gf.execute("RETURN duration('P7D') + datetime('2023-06-15T12:00:00Z') AS result")
        assert isinstance(result[0]["result"], CypherDateTime)
        assert result[0]["result"].value.isoformat() == "2023-06-22T12:00:00+00:00"

    def test_date_plus_duration(self):
        """date + duration."""
        gf = GraphForge()
        result = gf.execute("RETURN date('2023-06-15') + duration('P7D') AS result")
        assert isinstance(result[0]["result"], CypherDate)
        assert result[0]["result"].value.isoformat() == "2023-06-22"

    def test_date_plus_duration_month_boundary(self):
        """date + duration with month boundary handling."""
        gf = GraphForge()
        # Jan 31 + 1 month should be Feb 28 (or Feb 29 in leap year)
        result = gf.execute("RETURN date('2023-01-31') + duration('P1M') AS result")
        assert isinstance(result[0]["result"], CypherDate)
        # isodate handles this as Feb 28, 2023
        assert result[0]["result"].value.month == 2

    def test_time_plus_duration(self):
        """time + duration (ignores date components)."""
        gf = GraphForge()
        result = gf.execute("RETURN time('14:30:00') + duration('PT2H30M') AS result")
        assert isinstance(result[0]["result"], CypherTime)
        assert result[0]["result"].value.hour == 17
        assert result[0]["result"].value.minute == 0


class TestTemporalArithmeticSubtraction:
    """Test temporal - duration and temporal - temporal arithmetic."""

    def test_datetime_minus_duration_days(self):
        """datetime - duration (days)."""
        gf = GraphForge()
        result = gf.execute("RETURN datetime('2023-06-15T12:00:00Z') - duration('P7D') AS result")
        assert isinstance(result[0]["result"], CypherDateTime)
        assert result[0]["result"].value.isoformat() == "2023-06-08T12:00:00+00:00"

    def test_datetime_minus_duration_hours(self):
        """datetime - duration (hours)."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN datetime('2023-06-15T14:30:00Z') - duration('PT2H30M') AS result"
        )
        assert isinstance(result[0]["result"], CypherDateTime)
        assert result[0]["result"].value.isoformat() == "2023-06-15T12:00:00+00:00"

    def test_date_minus_duration(self):
        """date - duration."""
        gf = GraphForge()
        result = gf.execute("RETURN date('2023-06-15') - duration('P7D') AS result")
        assert isinstance(result[0]["result"], CypherDate)
        assert result[0]["result"].value.isoformat() == "2023-06-08"

    def test_time_minus_duration(self):
        """time - duration."""
        gf = GraphForge()
        result = gf.execute("RETURN time('14:30:00') - duration('PT2H30M') AS result")
        assert isinstance(result[0]["result"], CypherTime)
        assert result[0]["result"].value.hour == 12
        assert result[0]["result"].value.minute == 0

    def test_datetime_minus_datetime(self):
        """datetime - datetime returns duration."""
        gf = GraphForge()
        result = gf.execute(
            """
            RETURN datetime('2023-06-15T14:30:00Z') - datetime('2023-06-15T12:00:00Z') AS result
            """
        )
        assert isinstance(result[0]["result"], CypherDuration)
        # Duration should be 2h30m = PT2H30M
        duration_val = result[0]["result"].value
        assert duration_val.total_seconds() == 2.5 * 3600  # 2.5 hours in seconds

    def test_date_minus_date(self):
        """date - date returns duration."""
        gf = GraphForge()
        result = gf.execute("RETURN date('2023-06-15') - date('2023-06-08') AS result")
        assert isinstance(result[0]["result"], CypherDuration)
        duration_val = result[0]["result"].value
        assert duration_val.days == 7

    def test_datetime_minus_datetime_zero(self):
        """datetime - datetime (same time) returns zero duration."""
        gf = GraphForge()
        result = gf.execute(
            """
            RETURN datetime('2023-06-15T12:00:00Z') - datetime('2023-06-15T12:00:00Z') AS result
            """
        )
        assert isinstance(result[0]["result"], CypherDuration)
        duration_val = result[0]["result"].value
        assert duration_val.total_seconds() == 0


class TestTemporalArithmeticNullHandling:
    """Test NULL handling in temporal arithmetic."""

    def test_datetime_plus_null_returns_null(self):
        """datetime + NULL returns NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN datetime('2023-06-15T12:00:00Z') + null AS result")
        assert isinstance(result[0]["result"], CypherNull)

    def test_null_plus_duration_returns_null(self):
        """NULL + duration returns NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN null + duration('P7D') AS result")
        assert isinstance(result[0]["result"], CypherNull)

    def test_datetime_minus_null_returns_null(self):
        """datetime - NULL returns NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN datetime('2023-06-15T12:00:00Z') - null AS result")
        assert isinstance(result[0]["result"], CypherNull)

    def test_null_minus_datetime_returns_null(self):
        """NULL - datetime returns NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN null - datetime('2023-06-15T12:00:00Z') AS result")
        assert isinstance(result[0]["result"], CypherNull)


class TestTemporalArithmeticErrors:
    """Test error handling in temporal arithmetic."""

    def test_datetime_plus_int_raises_error(self):
        """datetime + int raises TypeError."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="numeric operands"):
            gf.execute("RETURN datetime('2023-06-15T12:00:00Z') + 5 AS result")

    def test_truncate_invalid_unit_raises_error(self):
        """truncate() with invalid unit raises ValueError."""
        gf = GraphForge()
        with pytest.raises(ValueError, match="Invalid truncation unit"):
            gf.execute("RETURN truncate('invalid', datetime('2023-06-15T12:00:00Z')) AS result")

    def test_truncate_date_with_hour_raises_error(self):
        """truncate() date to hour raises TypeError."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="Date only supports"):
            gf.execute("RETURN truncate('hour', date('2023-06-15')) AS result")

    def test_truncate_time_with_year_raises_error(self):
        """truncate() time to year raises TypeError."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="Time only supports"):
            gf.execute("RETURN truncate('year', time('14:30:00')) AS result")
