"""Unit tests for temporal type serialization.

Tests MessagePack serialization/deserialization of temporal types:
- DATE, DATETIME, TIME, DURATION
- Round-trip preservation of values
- ISO 8601 string format
"""

import datetime

import pytest

from graphforge.storage.serialization import (
    deserialize_cypher_value,
    deserialize_properties,
    serialize_cypher_value,
    serialize_properties,
)
from graphforge.types.values import (
    CypherDate,
    CypherDateTime,
    CypherDuration,
    CypherTime,
)

pytestmark = pytest.mark.unit


class TestTemporalSerialization:
    """Tests for temporal type serialization."""

    def test_serialize_date(self):
        """Test DATE serialization to ISO 8601 string."""
        date = CypherDate("2023-01-15")
        serialized = serialize_cypher_value(date)

        assert serialized["type"] == "date"
        assert serialized["value"] == "2023-01-15"

    def test_deserialize_date(self):
        """Test DATE deserialization from ISO 8601 string."""
        data = {"type": "date", "value": "2023-01-15"}
        deserialized = deserialize_cypher_value(data)

        assert isinstance(deserialized, CypherDate)
        assert deserialized.value == datetime.date(2023, 1, 15)

    def test_date_roundtrip(self):
        """Test DATE round-trip serialization."""
        original = CypherDate("2023-01-15")
        serialized = serialize_cypher_value(original)
        deserialized = deserialize_cypher_value(serialized)

        assert isinstance(deserialized, CypherDate)
        assert deserialized.value == original.value

    def test_serialize_datetime(self):
        """Test DATETIME serialization to ISO 8601 string."""
        dt = CypherDateTime("2023-01-15T10:30:00")
        serialized = serialize_cypher_value(dt)

        assert serialized["type"] == "datetime"
        assert "2023-01-15" in serialized["value"]
        assert "10:30:00" in serialized["value"]

    def test_deserialize_datetime(self):
        """Test DATETIME deserialization from ISO 8601 string."""
        data = {"type": "datetime", "value": "2023-01-15T10:30:00"}
        deserialized = deserialize_cypher_value(data)

        assert isinstance(deserialized, CypherDateTime)
        expected = datetime.datetime(2023, 1, 15, 10, 30, 0)
        assert deserialized.value == expected

    def test_datetime_roundtrip(self):
        """Test DATETIME round-trip serialization."""
        original = CypherDateTime("2023-01-15T10:30:00")
        serialized = serialize_cypher_value(original)
        deserialized = deserialize_cypher_value(serialized)

        assert isinstance(deserialized, CypherDateTime)
        # Compare timestamps since timezone info might differ
        assert deserialized.value.replace(tzinfo=None) == original.value.replace(tzinfo=None)

    def test_datetime_with_timezone(self):
        """Test DATETIME with timezone round-trip."""
        original = CypherDateTime("2023-01-15T10:30:00+00:00")
        serialized = serialize_cypher_value(original)
        deserialized = deserialize_cypher_value(serialized)

        assert isinstance(deserialized, CypherDateTime)
        assert deserialized.value.tzinfo is not None

    def test_serialize_time(self):
        """Test TIME serialization to ISO 8601 string."""
        time = CypherTime("10:30:00")
        serialized = serialize_cypher_value(time)

        assert serialized["type"] == "time"
        assert serialized["value"] == "10:30:00"

    def test_deserialize_time(self):
        """Test TIME deserialization from ISO 8601 string."""
        data = {"type": "time", "value": "10:30:00"}
        deserialized = deserialize_cypher_value(data)

        assert isinstance(deserialized, CypherTime)
        assert deserialized.value == datetime.time(10, 30, 0)

    def test_time_roundtrip(self):
        """Test TIME round-trip serialization."""
        original = CypherTime("10:30:00")
        serialized = serialize_cypher_value(original)
        deserialized = deserialize_cypher_value(serialized)

        assert isinstance(deserialized, CypherTime)
        assert deserialized.value == original.value

    def test_serialize_duration(self):
        """Test DURATION serialization to ISO 8601 string."""
        duration = CypherDuration("P1DT2H30M")
        serialized = serialize_cypher_value(duration)

        assert serialized["type"] == "duration"
        assert "P" in serialized["value"]  # ISO 8601 duration format

    def test_deserialize_duration(self):
        """Test DURATION deserialization from ISO 8601 string."""
        data = {"type": "duration", "value": "P1DT2H30M"}
        deserialized = deserialize_cypher_value(data)

        assert isinstance(deserialized, CypherDuration)
        expected = datetime.timedelta(days=1, hours=2, minutes=30)
        assert deserialized.value == expected

    def test_duration_roundtrip(self):
        """Test DURATION round-trip serialization."""
        original = CypherDuration("P1DT2H30M")
        serialized = serialize_cypher_value(original)
        deserialized = deserialize_cypher_value(serialized)

        assert isinstance(deserialized, CypherDuration)
        assert deserialized.value == original.value


class TestTemporalPropertiesSerialization:
    """Tests for properties dict with temporal types."""

    def test_serialize_properties_with_date(self):
        """Test serializing properties containing DATE."""
        properties = {
            "birthday": CypherDate("1990-05-15"),
            "name": from_python("Alice"),
        }

        serialized = serialize_properties(properties)
        assert isinstance(serialized, bytes)

        deserialized = deserialize_properties(serialized)
        assert isinstance(deserialized["birthday"], CypherDate)
        assert deserialized["birthday"].value == datetime.date(1990, 5, 15)

    def test_serialize_properties_with_datetime(self):
        """Test serializing properties containing DATETIME."""
        from graphforge.types.values import CypherString

        properties = {
            "createdAt": CypherDateTime("2023-01-15T10:30:00"),
            "title": CypherString("Post Title"),
        }

        serialized = serialize_properties(properties)
        deserialized = deserialize_properties(serialized)

        assert isinstance(deserialized["createdAt"], CypherDateTime)

    def test_serialize_properties_with_time(self):
        """Test serializing properties containing TIME."""
        from graphforge.types.values import CypherInt

        properties = {
            "meetingTime": CypherTime("14:30:00"),
            "room": CypherInt(101),
        }

        serialized = serialize_properties(properties)
        deserialized = deserialize_properties(serialized)

        assert isinstance(deserialized["meetingTime"], CypherTime)
        assert deserialized["meetingTime"].value == datetime.time(14, 30, 0)

    def test_serialize_properties_with_duration(self):
        """Test serializing properties containing DURATION."""
        from graphforge.types.values import CypherString

        properties = {
            "elapsed": CypherDuration("PT2H30M"),
            "taskName": CypherString("Build"),
        }

        serialized = serialize_properties(properties)
        deserialized = deserialize_properties(serialized)

        assert isinstance(deserialized["elapsed"], CypherDuration)
        expected = datetime.timedelta(hours=2, minutes=30)
        assert deserialized["elapsed"].value == expected

    def test_serialize_mixed_temporal_properties(self):
        """Test serializing properties with multiple temporal types."""
        from graphforge.types.values import CypherInt, CypherString

        properties = {
            "birthday": CypherDate("1990-05-15"),
            "lastLogin": CypherDateTime("2023-01-15T10:30:00"),
            "preferredMeetingTime": CypherTime("09:00:00"),
            "sessionDuration": CypherDuration("PT1H"),
            "name": CypherString("Alice"),
            "age": CypherInt(33),
        }

        serialized = serialize_properties(properties)
        deserialized = deserialize_properties(serialized)

        # Verify all types preserved
        assert isinstance(deserialized["birthday"], CypherDate)
        assert isinstance(deserialized["lastLogin"], CypherDateTime)
        assert isinstance(deserialized["preferredMeetingTime"], CypherTime)
        assert isinstance(deserialized["sessionDuration"], CypherDuration)
        assert isinstance(deserialized["name"], CypherString)
        assert isinstance(deserialized["age"], CypherInt)

        # Verify values
        assert deserialized["birthday"].value == datetime.date(1990, 5, 15)
        assert deserialized["preferredMeetingTime"].value == datetime.time(9, 0, 0)
        assert deserialized["sessionDuration"].value == datetime.timedelta(hours=1)


# Helper to avoid import issues in tests
def from_python(value):
    """Simple conversion for test purposes."""
    from graphforge.types.values import from_python as convert

    return convert(value)
