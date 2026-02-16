"""Integration tests for temporal map constructors."""

import pytest

from graphforge.api import GraphForge


@pytest.fixture
def gf():
    """Create a fresh GraphForge instance."""
    return GraphForge()


class TestDateMapConstructor:
    """Tests for date() map constructor."""

    def test_date_calendar(self, gf):
        """Date with calendar parameters."""
        result = gf.execute("RETURN date({year: 2015, month: 1, day: 15}) AS d")
        assert len(result) == 1
        assert str(result[0]["d"].value) == "2015-01-15"

    def test_date_week(self, gf):
        """Date with week parameters."""
        result = gf.execute("RETURN date({year: 2016, week: 1, dayOfWeek: 3}) AS d")
        assert len(result) == 1
        # Week 1 of 2016, day 3 (Wednesday)
        assert result[0]["d"].value.year == 2016

    def test_date_quarter(self, gf):
        """Date with quarter parameters."""
        result = gf.execute("RETURN date({year: 2015, quarter: 2, dayOfQuarter: 15}) AS d")
        assert len(result) == 1
        # Q2 starts April 1, day 15 is April 15
        assert result[0]["d"].value.month == 4
        assert result[0]["d"].value.day == 15

    def test_date_ordinal(self, gf):
        """Date with ordinal day parameter."""
        result = gf.execute("RETURN date({year: 2015, ordinalDay: 100}) AS d")
        assert len(result) == 1
        # 100th day of 2015
        assert result[0]["d"].value.year == 2015

    def test_date_string_still_works(self, gf):
        """Date with string parameter still works (backward compatible)."""
        result = gf.execute("RETURN date('2015-01-15') AS d")
        assert len(result) == 1
        assert str(result[0]["d"].value) == "2015-01-15"


class TestDateTimeMapConstructor:
    """Tests for datetime() map constructor."""

    def test_datetime_calendar(self, gf):
        """DateTime with calendar parameters."""
        result = gf.execute(
            "RETURN datetime({year: 1984, month: 10, day: 11, hour: 12, minute: 31, second: 14}) AS dt"
        )
        assert len(result) == 1
        dt = result[0]["dt"].value
        assert dt.year == 1984
        assert dt.month == 10
        assert dt.day == 11
        assert dt.hour == 12
        assert dt.minute == 31
        assert dt.second == 14

    def test_datetime_week(self, gf):
        """DateTime with week parameters."""
        result = gf.execute("RETURN datetime({year: 2016, week: 1, dayOfWeek: 3, hour: 10}) AS dt")
        assert len(result) == 1
        dt = result[0]["dt"].value
        assert dt.year == 2016
        assert dt.hour == 10

    def test_datetime_quarter(self, gf):
        """DateTime with quarter parameters."""
        result = gf.execute(
            "RETURN datetime({year: 2015, quarter: 2, dayOfQuarter: 15, hour: 14}) AS dt"
        )
        assert len(result) == 1
        dt = result[0]["dt"].value
        assert dt.month == 4
        assert dt.day == 15
        assert dt.hour == 14

    def test_datetime_ordinal(self, gf):
        """DateTime with ordinal day parameter."""
        result = gf.execute(
            "RETURN datetime({year: 2015, ordinalDay: 100, hour: 9, minute: 30}) AS dt"
        )
        assert len(result) == 1
        dt = result[0]["dt"].value
        assert dt.year == 2015
        assert dt.hour == 9
        assert dt.minute == 30

    def test_datetime_with_milliseconds(self, gf):
        """DateTime with millisecond precision."""
        result = gf.execute(
            "RETURN datetime({year: 2015, month: 1, day: 1, hour: 0, millisecond: 123}) AS dt"
        )
        assert len(result) == 1
        dt = result[0]["dt"].value
        assert dt.microsecond == 123000

    def test_datetime_with_microseconds(self, gf):
        """DateTime with microsecond precision."""
        result = gf.execute(
            "RETURN datetime({year: 2015, month: 1, day: 1, hour: 0, microsecond: 456}) AS dt"
        )
        assert len(result) == 1
        dt = result[0]["dt"].value
        assert dt.microsecond == 456

    def test_datetime_string_still_works(self, gf):
        """DateTime with string parameter still works (backward compatible)."""
        result = gf.execute("RETURN datetime('1984-10-11T12:31:14') AS dt")
        assert len(result) == 1
        dt = result[0]["dt"].value
        assert dt.year == 1984
        assert dt.month == 10


class TestTimeMapConstructor:
    """Tests for time() map constructor."""

    def test_time_basic(self, gf):
        """Time with basic parameters."""
        result = gf.execute("RETURN time({hour: 12, minute: 30, second: 45}) AS t")
        assert len(result) == 1
        t = result[0]["t"].value
        assert t.hour == 12
        assert t.minute == 30
        assert t.second == 45

    def test_time_with_milliseconds(self, gf):
        """Time with millisecond precision."""
        result = gf.execute("RETURN time({hour: 10, millisecond: 123}) AS t")
        assert len(result) == 1
        t = result[0]["t"].value
        assert t.hour == 10
        assert t.microsecond == 123000

    def test_time_with_microseconds(self, gf):
        """Time with microsecond precision."""
        result = gf.execute("RETURN time({hour: 10, microsecond: 456}) AS t")
        assert len(result) == 1
        t = result[0]["t"].value
        assert t.microsecond == 456

    def test_time_defaults_to_zero(self, gf):
        """Time with only hour specified defaults others to zero."""
        result = gf.execute("RETURN time({hour: 15}) AS t")
        assert len(result) == 1
        t = result[0]["t"].value
        assert t.hour == 15
        assert t.minute == 0
        assert t.second == 0

    def test_time_string_still_works(self, gf):
        """Time with string parameter still works (backward compatible)."""
        result = gf.execute("RETURN time('12:30:45') AS t")
        assert len(result) == 1
        t = result[0]["t"].value
        assert t.hour == 12
        assert t.minute == 30


class TestDurationMapConstructor:
    """Tests for duration() map constructor."""

    def test_duration_days(self, gf):
        """Duration with days."""
        result = gf.execute("RETURN duration({days: 5}) AS dur")
        assert len(result) == 1
        dur = result[0]["dur"].value
        assert dur.days == 5

    def test_duration_hours(self, gf):
        """Duration with hours."""
        result = gf.execute("RETURN duration({hours: 12}) AS dur")
        assert len(result) == 1
        dur = result[0]["dur"].value
        assert dur.seconds == 12 * 3600

    def test_duration_mixed(self, gf):
        """Duration with mixed components."""
        result = gf.execute("RETURN duration({days: 3, hours: 4, minutes: 30, seconds: 15}) AS dur")
        assert len(result) == 1
        dur = result[0]["dur"].value
        assert dur.days == 3
        assert dur.seconds == 4 * 3600 + 30 * 60 + 15

    def test_duration_with_years_months(self, gf):
        """Duration with years and months uses isodate.Duration."""
        result = gf.execute("RETURN duration({years: 1, months: 2, days: 3}) AS dur")
        assert len(result) == 1
        # Should return an isodate.Duration object
        dur = result[0]["dur"].value
        assert hasattr(dur, "years") or hasattr(dur, "months")

    def test_duration_with_milliseconds(self, gf):
        """Duration with milliseconds."""
        result = gf.execute("RETURN duration({milliseconds: 500}) AS dur")
        assert len(result) == 1
        dur = result[0]["dur"].value
        assert dur.microseconds == 500000

    def test_duration_with_microseconds(self, gf):
        """Duration with microseconds."""
        result = gf.execute("RETURN duration({microseconds: 1500}) AS dur")
        assert len(result) == 1
        dur = result[0]["dur"].value
        assert dur.microseconds == 1500

    def test_duration_string_still_works(self, gf):
        """Duration with string parameter still works (backward compatible)."""
        result = gf.execute("RETURN duration('P1DT12H') AS dur")
        assert len(result) == 1
        dur = result[0]["dur"].value
        assert dur.days == 1


class TestTemporalMapErrorCases:
    """Tests for error cases in temporal map constructors."""

    def test_date_missing_required_params(self, gf):
        """Date map without required parameters raises error."""
        with pytest.raises(TypeError, match="DATE map constructor requires"):
            gf.execute("RETURN date({year: 2015}) AS d")

    def test_datetime_missing_date_params(self, gf):
        """DateTime map without date parameters raises error."""
        with pytest.raises(TypeError, match="DATETIME map constructor requires"):
            gf.execute("RETURN datetime({hour: 12}) AS dt")

    def test_date_invalid_type(self, gf):
        """Date with invalid type raises error."""
        with pytest.raises(TypeError, match="DATE expects string or map"):
            gf.execute("RETURN date(123) AS d")

    def test_datetime_invalid_type(self, gf):
        """DateTime with invalid type raises error."""
        with pytest.raises(TypeError, match="DATETIME expects string or map"):
            gf.execute("RETURN datetime(123) AS dt")

    def test_time_invalid_type(self, gf):
        """Time with invalid type raises error."""
        with pytest.raises(TypeError, match="TIME expects string or map"):
            gf.execute("RETURN time(123) AS t")

    def test_duration_invalid_type(self, gf):
        """Duration with invalid type raises error."""
        with pytest.raises(TypeError, match="DURATION expects string or map"):
            gf.execute("RETURN duration(123) AS dur")
