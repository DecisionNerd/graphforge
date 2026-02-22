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
        # Should truncate to milliseconds: 123456µs → 123000µs
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
        assert result[0]["result"].value.day == 28

    def test_time_plus_duration(self):
        """time + duration (ignores date components)."""
        gf = GraphForge()
        result = gf.execute("RETURN time('14:30:00') + duration('PT2H30M') AS result")
        assert isinstance(result[0]["result"], CypherTime)
        assert result[0]["result"].value.hour == 17
        assert result[0]["result"].value.minute == 0

    def test_time_plus_duration_preserves_timezone(self):
        """time + duration preserves timezone information."""
        gf = GraphForge()
        result = gf.execute("RETURN time('14:30:00+02:00') + duration('PT2H30M') AS result")
        assert isinstance(result[0]["result"], CypherTime)
        # Should be 17:00:00+02:00
        assert result[0]["result"].value.hour == 17
        assert result[0]["result"].value.minute == 0
        # Verify timezone is preserved
        assert result[0]["result"].value.tzinfo is not None
        # UTC offset should be +2 hours
        import datetime

        assert result[0]["result"].value.utcoffset() == datetime.timedelta(hours=2)


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


class TestNamespacedTruncate:
    """Test date.truncate(), datetime.truncate(), etc. namespaced forms."""

    def test_date_truncate_month(self):
        """date.truncate('month', date) returns first day of month."""
        gf = GraphForge()
        result = gf.execute("RETURN date.truncate('month', date('2023-06-15')) AS d")
        assert result[0]["d"].value.isoformat() == "2023-06-01"

    def test_date_truncate_year(self):
        """date.truncate('year', date) returns first day of year."""
        gf = GraphForge()
        result = gf.execute("RETURN date.truncate('year', date('2023-06-15')) AS d")
        assert result[0]["d"].value.isoformat() == "2023-01-01"

    def test_date_truncate_week(self):
        """date.truncate('week', date) returns preceding Monday."""
        gf = GraphForge()
        # 2020-01-15 is a Wednesday; Monday before is 2020-01-13
        result = gf.execute("RETURN date.truncate('week', date('2020-01-15')) AS d")
        assert result[0]["d"].value.isoformat() == "2020-01-13"

    def test_date_truncate_quarter(self):
        """date.truncate('quarter', date) returns first day of quarter."""
        gf = GraphForge()
        result = gf.execute("RETURN date.truncate('quarter', date('2023-08-15')) AS d")
        assert result[0]["d"].value.isoformat() == "2023-07-01"

    def test_date_truncate_decade(self):
        """date.truncate('decade', date) returns first year of decade."""
        gf = GraphForge()
        result = gf.execute("RETURN date.truncate('decade', date('2023-06-15')) AS d")
        assert result[0]["d"].value.isoformat() == "2020-01-01"

    def test_date_truncate_century(self):
        """date.truncate('century', date) returns first year of century."""
        gf = GraphForge()
        result = gf.execute("RETURN date.truncate('century', date('2023-06-15')) AS d")
        assert result[0]["d"].value.isoformat() == "2001-01-01"

    def test_date_truncate_millennium(self):
        """date.truncate('millennium', date) returns first year of millennium."""
        gf = GraphForge()
        result = gf.execute("RETURN date.truncate('millennium', date('2023-06-15')) AS d")
        assert result[0]["d"].value.isoformat() == "2001-01-01"

    def test_datetime_truncate_day(self):
        """datetime.truncate('day', datetime) zeroes out time part."""
        gf = GraphForge()
        result = gf.execute("RETURN datetime.truncate('day', datetime('2023-06-15T14:30:45')) AS d")
        assert result[0]["d"].value.isoformat() == "2023-06-15T00:00:00"

    def test_localtime_truncate_hour(self):
        """localtime.truncate('hour', localtime) zeroes minutes/seconds."""
        gf = GraphForge()
        result = gf.execute("RETURN localtime.truncate('hour', localtime('14:30:45')) AS t")
        t = result[0]["t"].value
        assert t.hour == 14
        assert t.minute == 0
        assert t.second == 0


class TestDurationBetween:
    """Test duration.between(), duration.inMonths(), etc."""

    def test_duration_between_dates(self):
        """duration.between returns calendar duration between dates."""
        gf = GraphForge()
        result = gf.execute("RETURN duration.between(date('2020-01-01'), date('2020-03-01')) AS d")
        assert isinstance(result[0]["d"], CypherDuration)

    def test_duration_in_months_two_years(self):
        """duration.inMonths returns duration in whole months."""
        gf = GraphForge()
        result = gf.execute("RETURN duration.inMonths(date('2020-01-01'), date('2022-07-01')) AS d")
        # From Jan 2020 to Jul 2022 = 2.5 years = 30 months
        import isodate

        dur = result[0]["d"].value
        assert isinstance(dur, isodate.Duration)
        assert dur.months == 30

    def test_duration_in_days(self):
        """duration.inDays returns duration in whole days."""
        gf = GraphForge()
        result = gf.execute("RETURN duration.inDays(date('2020-01-01'), date('2020-01-15')) AS d")
        import datetime

        assert result[0]["d"].value == datetime.timedelta(days=14)

    def test_duration_in_seconds(self):
        """duration.inSeconds returns duration in seconds."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN duration.inSeconds(datetime('2020-01-01T00:00:00'), "
            "datetime('2020-01-01T01:30:00')) AS d"
        )
        import datetime

        assert result[0]["d"].value == datetime.timedelta(seconds=5400)


class TestDurationPlusDuration:
    """Test duration + duration and duration - duration arithmetic."""

    def test_duration_plus_duration_simple(self):
        """duration + duration combines timedelta components."""
        gf = GraphForge()
        result = gf.execute("RETURN duration('P7D') + duration('P3D') AS d")
        assert isinstance(result[0]["d"], CypherDuration)
        import datetime

        assert result[0]["d"].value == datetime.timedelta(days=10)

    def test_duration_plus_duration_with_months(self):
        """duration + duration with year/month components."""
        gf = GraphForge()
        result = gf.execute("RETURN duration('P1Y') + duration('P6M') AS d")
        assert isinstance(result[0]["d"], CypherDuration)

    def test_duration_minus_duration(self):
        """duration - duration subtracts components."""
        gf = GraphForge()
        result = gf.execute("RETURN duration('P10D') - duration('P3D') AS d")
        assert isinstance(result[0]["d"], CypherDuration)
        import datetime

        assert result[0]["d"].value == datetime.timedelta(days=7)


class TestTimezoneOffsetParsing:
    """Test parsing of ±HH:MM timezone offsets."""

    def test_datetime_with_positive_offset(self):
        """datetime with +HH:MM offset is parsed correctly."""
        gf = GraphForge()
        result = gf.execute("RETURN datetime('2020-01-01T12:00:00+01:00') AS d")
        import datetime

        assert result[0]["d"].value.utcoffset() == datetime.timedelta(hours=1)

    def test_datetime_with_negative_offset(self):
        """datetime with -HH:MM offset is parsed correctly."""
        gf = GraphForge()
        result = gf.execute("RETURN datetime('2020-01-01T12:00:00-05:00') AS d")
        import datetime

        assert result[0]["d"].value.utcoffset() == datetime.timedelta(hours=-5)

    def test_time_with_offset(self):
        """time with +HH:MM offset is parsed correctly."""
        gf = GraphForge()
        result = gf.execute("RETURN time('12:00:00+02:00') AS t")
        import datetime

        assert result[0]["t"].value.utcoffset() == datetime.timedelta(hours=2)


class TestTemporalSelectForm:
    """Test select form temporal constructors: date({date: base, ...overrides})."""

    def test_date_select_form(self):
        """date({date: base, month: override}) overrides specific component."""
        gf = GraphForge()
        result = gf.execute("RETURN date({date: date('2020-06-15'), month: 1}) AS d")
        assert result[0]["d"].value.isoformat() == "2020-01-15"

    def test_date_select_form_year_override(self):
        """date({date: base, year: override}) overrides year component."""
        gf = GraphForge()
        result = gf.execute("RETURN date({date: date('2020-06-15'), year: 2021}) AS d")
        assert result[0]["d"].value.isoformat() == "2021-06-15"

    def test_date_select_form_day_override(self):
        """date({date: base, day: override}) overrides day component."""
        gf = GraphForge()
        result = gf.execute("RETURN date({date: date('2020-06-15'), day: 1}) AS d")
        assert result[0]["d"].value.isoformat() == "2020-06-01"

    def test_date_select_form_quarter_override(self):
        """date({date: base, quarter: n}) adjusts to the same day in a different quarter."""
        gf = GraphForge()
        # Jan 15 (Q1 day 15) → Q2 (April 15)
        result = gf.execute("RETURN date({date: date('2020-01-15'), quarter: 2}) AS d")
        assert isinstance(result[0]["d"], CypherDate)
        assert result[0]["d"].value.month == 4

    def test_date_from_cypher_date(self):
        """date(date_value) returns the date unchanged."""
        gf = GraphForge()
        result = gf.execute("RETURN date(date('2020-06-15')) AS d")
        assert result[0]["d"].value.isoformat() == "2020-06-15"

    def test_date_from_cypher_datetime(self):
        """date(datetime_value) extracts the date component."""
        gf = GraphForge()
        result = gf.execute("RETURN date(datetime('2020-06-15T12:30:00')) AS d")
        assert result[0]["d"].value.isoformat() == "2020-06-15"

    def test_localdatetime_select_form(self):
        """localdatetime({localdatetime: base, day: override}) works."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN localdatetime({localdatetime: localdatetime('2020-06-15T12:30:00'), day: 1}) AS d"
        )
        assert result[0]["d"].value.isoformat() == "2020-06-01T12:30:00"


class TestMultiStatementScript:
    """Test that multi-statement Cypher scripts are executed correctly."""

    def test_multi_statement_creates(self):
        """Multiple CREATE statements separated by newlines all execute."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")
        result = gf.execute("MATCH (p:Person) RETURN p.name AS name ORDER BY name")
        assert [r["name"].value for r in result] == ["Alice", "Bob"]


class TestNamespacedTruncateWithComponents:
    """Test date.truncate(unit, temporal, {components}) third-argument form."""

    def test_date_truncate_with_day_override(self):
        """date.truncate with component map overrides day after truncation."""
        gf = GraphForge()
        result = gf.execute("RETURN date.truncate('month', date('2020-06-15'), {day: 5}) AS d")
        assert result[0]["d"].value.isoformat() == "2020-06-05"

    def test_datetime_truncate_with_hour_override(self):
        """datetime.truncate with component map overrides hour."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN datetime.truncate('day', datetime('2020-06-15T12:30:00'), {hour: 9}) AS d"
        )
        assert result[0]["d"].value.isoformat() == "2020-06-15T09:00:00"

    def test_time_truncate_with_minute_override(self):
        """time.truncate with component map overrides minute."""
        gf = GraphForge()
        result = gf.execute("RETURN time.truncate('hour', time('14:30:45'), {minute: 15}) AS t")
        t = result[0]["t"].value
        assert t.hour == 14
        assert t.minute == 15
        assert t.second == 0


class TestDatetimeSelectFormAdvanced:
    """Test DATETIME select form with week/ordinalDay/quarter/timezone overrides."""

    def test_datetime_select_form_with_week_override(self):
        """datetime({datetime: base, week: n}) adjusts to the correct week."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN datetime({datetime: datetime('2020-01-15T12:00:00'), week: 5}) AS d"
        )
        assert isinstance(result[0]["d"], CypherDateTime)

    def test_datetime_select_form_with_ordinal_day(self):
        """datetime({datetime: base, ordinalDay: n}) adjusts to the correct day of year."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN datetime({datetime: datetime('2020-06-15T12:00:00'), ordinalDay: 1}) AS d"
        )
        assert result[0]["d"].value.month == 1
        assert result[0]["d"].value.day == 1

    def test_datetime_select_form_from_date_base(self):
        """datetime({date: base_date}) uses date base with zero time."""
        gf = GraphForge()
        result = gf.execute("RETURN datetime({date: date('2020-06-15')}) AS d")
        assert result[0]["d"].value.date().isoformat() == "2020-06-15"
        assert result[0]["d"].value.hour == 0

    def test_datetime_select_form_with_timezone(self):
        """datetime({datetime: base, timezone: '+01:00'}) applies timezone."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN datetime({datetime: datetime('2020-01-01T12:00:00'), timezone: '+01:00'}) AS d"
        )
        import datetime

        assert result[0]["d"].value.utcoffset() == datetime.timedelta(hours=1)

    def test_localdatetime_select_form_from_datetime_base(self):
        """localdatetime({datetime: base, day: 5}) uses datetime base and strips tz."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN localdatetime({datetime: datetime('2020-06-15T12:00:00'), day: 5}) AS d"
        )
        assert result[0]["d"].value.day == 5
        assert result[0]["d"].value.hour == 12
        assert result[0]["d"].value.tzinfo is None

    def test_localdatetime_select_form_from_date_base(self):
        """localdatetime({date: base}) uses date base with zero time."""
        gf = GraphForge()
        result = gf.execute("RETURN localdatetime({date: date('2020-06-15')}) AS d")
        assert result[0]["d"].value.date().isoformat() == "2020-06-15"
        assert result[0]["d"].value.hour == 0

    def test_duration_between_with_datetime(self):
        """duration.between works with datetime arguments."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN duration.between(datetime('2020-01-01T00:00:00'), "
            "datetime('2020-01-01T02:30:00')) AS d"
        )
        assert isinstance(result[0]["d"], CypherDuration)

    def test_date_select_form_with_ordinal_day(self):
        """date select form with ordinalDay override."""
        gf = GraphForge()
        result = gf.execute("RETURN date({date: date('2020-06-15'), ordinalDay: 10}) AS d")
        assert result[0]["d"].value.month == 1
        assert result[0]["d"].value.day == 10

    def test_date_select_form_with_week(self):
        """date select form with week override."""
        gf = GraphForge()
        result = gf.execute("RETURN date({date: date('2020-06-15'), week: 1}) AS d")
        # Week 1 of 2020 starts on Dec 30 2019 (ISO week date)
        assert isinstance(result[0]["d"], CypherDate)

    def test_datetime_select_form_year_month_day_overrides(self):
        """datetime select form with year, month, and day overrides."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN datetime({datetime: datetime('2020-06-15T12:00:00'), "
            "year: 2021, month: 3, day: 5}) AS d"
        )
        assert result[0]["d"].value.year == 2021
        assert result[0]["d"].value.month == 3
        assert result[0]["d"].value.day == 5
        assert result[0]["d"].value.hour == 12  # time preserved

    def test_datetime_select_form_with_quarter_override(self):
        """datetime({datetime: base, quarter: n}) adjusts to the correct quarter."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN datetime({datetime: datetime('2020-01-15T10:00:00'), quarter: 3}) AS d"
        )
        # Q3 starts in July; day 15 into Q3 from Q1 day 15 → July 15
        assert isinstance(result[0]["d"], CypherDateTime)
        assert result[0]["d"].value.month == 7

    def test_localdatetime_select_form_year_month_overrides(self):
        """localdatetime select form with year and month overrides."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN localdatetime({localdatetime: localdatetime('2020-06-15T12:00:00'), "
            "year: 2021, month: 3}) AS d"
        )
        assert result[0]["d"].value.year == 2021
        assert result[0]["d"].value.month == 3
        assert result[0]["d"].value.day == 15

    def test_localdatetime_select_form_with_week_override(self):
        """localdatetime({localdatetime: base, week: n}) adjusts week."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN localdatetime({localdatetime: localdatetime('2020-01-15T12:00:00'), "
            "week: 5}) AS d"
        )
        assert isinstance(result[0]["d"], CypherDateTime)

    def test_localdatetime_select_form_with_ordinal_day_override(self):
        """localdatetime({localdatetime: base, ordinalDay: n}) adjusts day of year."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN localdatetime({localdatetime: localdatetime('2020-06-15T10:00:00'), "
            "ordinalDay: 1}) AS d"
        )
        assert result[0]["d"].value.month == 1
        assert result[0]["d"].value.day == 1
        assert result[0]["d"].value.hour == 10

    def test_localdatetime_select_form_with_quarter_override(self):
        """localdatetime({localdatetime: base, quarter: n}) adjusts quarter."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN localdatetime({localdatetime: localdatetime('2020-01-15T09:00:00'), "
            "quarter: 2}) AS d"
        )
        # Q2 starts April; Jan 15 → day 15 of Q1, so Q2 day 15 = April 15
        assert isinstance(result[0]["d"], CypherDateTime)
        assert result[0]["d"].value.month == 4

    def test_duration_between_times(self):
        """duration.between works with time arguments (CypherTime branch)."""
        gf = GraphForge()
        result = gf.execute("RETURN duration.between(time('10:00:00'), time('12:30:00')) AS d")
        assert isinstance(result[0]["d"], CypherDuration)

    def test_duration_between_month_overflow_edge_case(self):
        """duration.between handles month-day overflow (e.g. Jan 31 → Feb 28)."""
        gf = GraphForge()
        # Jan 31 → Feb 28: adding 1 month to Jan 31 would give Feb 31 (invalid)
        result = gf.execute("RETURN duration.between(date('2020-01-31'), date('2020-02-28')) AS d")
        assert isinstance(result[0]["d"], CypherDuration)

    def test_duration_in_days_with_datetime(self):
        """duration.inDays works with datetime arguments (tz-aware case)."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN duration.inDays(datetime('2020-01-01T00:00:00Z'), "
            "datetime('2020-01-08T00:00:00Z')) AS d"
        )
        import datetime

        assert result[0]["d"].value == datetime.timedelta(days=7)

    def test_duration_in_seconds_with_datetime(self):
        """duration.inSeconds works with datetime arguments (tz-aware case)."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN duration.inSeconds(datetime('2020-01-01T00:00:00Z'), "
            "datetime('2020-01-01T01:00:00Z')) AS d"
        )
        import datetime

        assert result[0]["d"].value == datetime.timedelta(seconds=3600)


class TestNamespacedFunctionErrors:
    """Test error handling in namespaced functions."""

    def test_date_truncate_wrong_arg_count(self):
        """date.truncate with too few args raises TypeError."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="expects at least 2 arguments"):
            gf.execute("RETURN date.truncate('month') AS d")

    def test_date_truncate_non_string_unit(self):
        """date.truncate with non-string unit raises TypeError."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="first argument.*must be a string"):
            gf.execute("RETURN date.truncate(5, date('2020-01-01')) AS d")

    def test_date_truncate_non_temporal_value(self):
        """date.truncate with non-temporal second arg raises TypeError."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="second argument must be a temporal"):
            gf.execute("RETURN date.truncate('month', 'not-a-date') AS d")

    def test_duration_between_wrong_arg_count(self):
        """duration.between with wrong arg count raises TypeError."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="expects 2 arguments"):
            gf.execute("RETURN duration.between(date('2020-01-01')) AS d")

    def test_duration_in_months_wrong_arg_count(self):
        """duration.inMonths with wrong arg count raises TypeError."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="expects 2 arguments"):
            gf.execute("RETURN duration.inMonths(date('2020-01-01')) AS d")

    def test_duration_in_days_wrong_arg_count(self):
        """duration.inDays with wrong arg count raises TypeError."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="expects 2 arguments"):
            gf.execute("RETURN duration.inDays(date('2020-01-01')) AS d")

    def test_duration_in_seconds_wrong_arg_count(self):
        """duration.inSeconds with wrong arg count raises TypeError."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="expects 2 arguments"):
            gf.execute("RETURN duration.inSeconds(date('2020-01-01')) AS d")

    def test_unknown_namespaced_function_raises_error(self):
        """Calling an unknown namespaced function raises ValueError."""
        gf = GraphForge()
        with pytest.raises(ValueError, match="Unknown namespaced function"):
            gf.execute("RETURN foo.bar() AS result")

    def test_duration_between_mixed_timezone(self):
        """duration.between with one tz-aware and one naive datetime normalizes tz."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN duration.between("
            "localdatetime('2020-01-01T00:00:00'), "
            "datetime('2020-03-01T00:00:00Z')) AS d"
        )
        assert isinstance(result[0]["d"], CypherDuration)

    def test_duration_in_days_mixed_timezone(self):
        """duration.inDays with mixed tz-aware/naive normalizes timezone."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN duration.inDays("
            "localdatetime('2020-01-01T00:00:00'), "
            "datetime('2020-01-08T00:00:00Z')) AS d"
        )
        assert isinstance(result[0]["d"], CypherDuration)

    def test_duration_in_seconds_mixed_timezone(self):
        """duration.inSeconds with mixed tz-aware/naive normalizes timezone."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN duration.inSeconds("
            "localdatetime('2020-01-01T00:00:00'), "
            "datetime('2020-01-01T01:00:00Z')) AS d"
        )
        assert isinstance(result[0]["d"], CypherDuration)

    def test_duration_between_mixed_timezone_reversed(self):
        """duration.between(tz-aware, naive) covers the elif tz branch."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN duration.between("
            "datetime('2020-01-01T00:00:00Z'), "
            "localdatetime('2020-03-01T00:00:00')) AS d"
        )
        assert isinstance(result[0]["d"], CypherDuration)

    def test_duration_in_days_mixed_timezone_reversed(self):
        """duration.inDays(tz-aware, naive) covers the elif tz branch."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN duration.inDays("
            "datetime('2020-01-08T00:00:00Z'), "
            "localdatetime('2020-01-01T00:00:00')) AS d"
        )
        assert isinstance(result[0]["d"], CypherDuration)

    def test_duration_in_seconds_mixed_timezone_reversed(self):
        """duration.inSeconds(tz-aware, naive) covers the elif tz branch."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN duration.inSeconds("
            "datetime('2020-01-01T01:00:00Z'), "
            "localdatetime('2020-01-01T00:00:00')) AS d"
        )
        assert isinstance(result[0]["d"], CypherDuration)


class TestLocalDateTimeStandardForms:
    """Test LOCALDATETIME standard map constructor forms."""

    def test_localdatetime_quarter_form(self):
        """localdatetime({year, quarter, dayOfQuarter}) constructs datetime."""
        gf = GraphForge()
        result = gf.execute("RETURN localdatetime({year: 2020, quarter: 1, dayOfQuarter: 15}) AS d")
        assert isinstance(result[0]["d"], CypherDateTime)
        assert result[0]["d"].value.month == 1
        assert result[0]["d"].value.day == 15

    def test_localdatetime_ordinal_form(self):
        """localdatetime({year, ordinalDay}) constructs datetime."""
        gf = GraphForge()
        result = gf.execute("RETURN localdatetime({year: 2020, ordinalDay: 100}) AS d")
        assert isinstance(result[0]["d"], CypherDateTime)
        # Day 100 of 2020 = April 9 (leap year)
        assert result[0]["d"].value.month == 4

    def test_localdatetime_hour_overflow(self):
        """localdatetime with hour >= 24 carries overflow into next day."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN localdatetime({year: 2020, month: 1, day: 1, hour: 25, minute: 0}) AS d"
        )
        assert isinstance(result[0]["d"], CypherDateTime)
        assert result[0]["d"].value.day == 2
        assert result[0]["d"].value.hour == 1

    def test_localtime_no_args(self):
        """localtime() with no args returns current local time."""
        gf = GraphForge()
        result = gf.execute("RETURN localtime() AS t")
        assert isinstance(result[0]["t"], CypherTime)
        assert result[0]["t"].value.tzinfo is None
