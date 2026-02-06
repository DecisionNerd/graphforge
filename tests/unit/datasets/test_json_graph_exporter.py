"""Unit tests for JSON Graph exporter helper functions."""

import pytest

from graphforge.datasets.exporters.json_graph import cypher_value_to_property_value
from graphforge.datasets.formats.json_graph import PropertyValue
from graphforge.types.values import (
    CypherBool,
    CypherDate,
    CypherDateTime,
    CypherDistance,
    CypherDuration,
    CypherFloat,
    CypherInt,
    CypherList,
    CypherMap,
    CypherNull,
    CypherPoint,
    CypherString,
    CypherTime,
)


@pytest.mark.unit
class TestCypherValueToPropertyValue:
    """Tests for cypher_value_to_property_value conversion function."""

    def test_convert_null(self):
        """Test converting CypherNull."""
        cv = CypherNull()
        result = cypher_value_to_property_value(cv)
        assert isinstance(result, PropertyValue)
        assert result.t == "null"
        assert result.v is None

    def test_convert_bool(self):
        """Test converting CypherBool."""
        cv_true = CypherBool(True)
        result_true = cypher_value_to_property_value(cv_true)
        assert result_true.t == "bool"
        assert result_true.v is True

        cv_false = CypherBool(False)
        result_false = cypher_value_to_property_value(cv_false)
        assert result_false.v is False

    def test_convert_int(self):
        """Test converting CypherInt."""
        cv = CypherInt(42)
        result = cypher_value_to_property_value(cv)
        assert result.t == "int"
        assert result.v == 42

    def test_convert_float(self):
        """Test converting CypherFloat."""
        cv = CypherFloat(3.14)
        result = cypher_value_to_property_value(cv)
        assert result.t == "float"
        assert result.v == 3.14

    def test_convert_string(self):
        """Test converting CypherString."""
        cv = CypherString("hello")
        result = cypher_value_to_property_value(cv)
        assert result.t == "string"
        assert result.v == "hello"

    def test_convert_date(self):
        """Test converting CypherDate."""
        cv = CypherDate("2023-01-15")
        result = cypher_value_to_property_value(cv)
        assert result.t == "date"
        assert result.v == "2023-01-15"

    def test_convert_datetime(self):
        """Test converting CypherDateTime."""
        cv = CypherDateTime("2023-01-15T10:30:00+00:00")
        result = cypher_value_to_property_value(cv)
        assert result.t == "datetime"
        # Should be ISO 8601 string
        assert "2023-01-15" in result.v
        assert "T" in result.v

    def test_convert_time(self):
        """Test converting CypherTime."""
        cv = CypherTime("10:30:00")
        result = cypher_value_to_property_value(cv)
        assert result.t == "time"
        assert "10:30:00" in result.v

    def test_convert_duration(self):
        """Test converting CypherDuration."""
        cv = CypherDuration("P1Y2M3DT4H5M6S")
        result = cypher_value_to_property_value(cv)
        assert result.t == "duration"
        # Should be ISO 8601 duration string
        assert result.v.startswith("P")

    def test_convert_point_cartesian(self):
        """Test converting CypherPoint (cartesian)."""
        cv = CypherPoint({"x": 1.0, "y": 2.0})
        result = cypher_value_to_property_value(cv)
        assert result.t == "point"
        assert result.v["x"] == 1.0
        assert result.v["y"] == 2.0

    def test_convert_point_geographic(self):
        """Test converting CypherPoint (geographic)."""
        cv = CypherPoint({"latitude": 37.7749, "longitude": -122.4194})
        result = cypher_value_to_property_value(cv)
        assert result.t == "point"
        assert result.v["latitude"] == 37.7749
        assert result.v["longitude"] == -122.4194

    def test_convert_distance(self):
        """Test converting CypherDistance."""
        cv = CypherDistance(42.5)
        result = cypher_value_to_property_value(cv)
        assert result.t == "distance"
        assert result.v == 42.5

    def test_convert_list(self):
        """Test converting CypherList."""
        cv = CypherList([CypherInt(1), CypherInt(2), CypherString("three")])
        result = cypher_value_to_property_value(cv)
        assert result.t == "list"
        assert len(result.v) == 3
        assert result.v[0]["t"] == "int"
        assert result.v[0]["v"] == 1
        assert result.v[1]["t"] == "int"
        assert result.v[1]["v"] == 2
        assert result.v[2]["t"] == "string"
        assert result.v[2]["v"] == "three"

    def test_convert_map(self):
        """Test converting CypherMap."""
        cv = CypherMap({"name": CypherString("Alice"), "age": CypherInt(30)})
        result = cypher_value_to_property_value(cv)
        assert result.t == "map"
        assert "name" in result.v
        assert "age" in result.v
        assert result.v["name"]["t"] == "string"
        assert result.v["name"]["v"] == "Alice"
        assert result.v["age"]["t"] == "int"
        assert result.v["age"]["v"] == 30

    def test_nested_list(self):
        """Test converting nested CypherList."""
        cv = CypherList([CypherInt(1), CypherList([CypherInt(2), CypherInt(3)])])
        result = cypher_value_to_property_value(cv)
        assert result.t == "list"
        assert result.v[0]["t"] == "int"
        assert result.v[1]["t"] == "list"
        assert len(result.v[1]["v"]) == 2

    def test_nested_map(self):
        """Test converting nested CypherMap."""
        cv = CypherMap({"outer": CypherMap({"inner": CypherString("value")})})
        result = cypher_value_to_property_value(cv)
        assert result.t == "map"
        assert result.v["outer"]["t"] == "map"
        assert result.v["outer"]["v"]["inner"]["v"] == "value"
