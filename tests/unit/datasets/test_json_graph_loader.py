"""Unit tests for JSON Graph loader helper functions."""

import pytest

from graphforge.datasets.formats.json_graph import PropertyValue
from graphforge.datasets.loaders.json_graph import (
    convert_properties,
    property_value_to_cypher,
)
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
class TestPropertyValueToCypher:
    """Tests for property_value_to_cypher conversion function."""

    def test_convert_null(self):
        """Test converting null property value."""
        pv = PropertyValue(t="null", v=None)
        result = property_value_to_cypher(pv)
        assert isinstance(result, CypherNull)

    def test_convert_bool(self):
        """Test converting boolean property values."""
        pv_true = PropertyValue(t="bool", v=True)
        result_true = property_value_to_cypher(pv_true)
        assert isinstance(result_true, CypherBool)
        assert result_true.value is True

        pv_false = PropertyValue(t="bool", v=False)
        result_false = property_value_to_cypher(pv_false)
        assert result_false.value is False

    def test_convert_int(self):
        """Test converting integer property value."""
        pv = PropertyValue(t="int", v=42)
        result = property_value_to_cypher(pv)
        assert isinstance(result, CypherInt)
        assert result.value == 42

    def test_convert_float(self):
        """Test converting float property value."""
        pv = PropertyValue(t="float", v=3.14)
        result = property_value_to_cypher(pv)
        assert isinstance(result, CypherFloat)
        assert result.value == 3.14

    def test_convert_float_from_int(self):
        """Test converting int to float when type is float."""
        pv = PropertyValue(t="float", v=42)
        result = property_value_to_cypher(pv)
        assert isinstance(result, CypherFloat)
        assert result.value == 42.0

    def test_convert_string(self):
        """Test converting string property value."""
        pv = PropertyValue(t="string", v="hello")
        result = property_value_to_cypher(pv)
        assert isinstance(result, CypherString)
        assert result.value == "hello"

    def test_convert_date(self):
        """Test converting date property value."""
        pv = PropertyValue(t="date", v="2023-01-15")
        result = property_value_to_cypher(pv)
        assert isinstance(result, CypherDate)
        assert result.value.isoformat() == "2023-01-15"

    def test_convert_datetime(self):
        """Test converting datetime property value."""
        pv = PropertyValue(t="datetime", v="2023-01-15T10:30:00+00:00")
        result = property_value_to_cypher(pv)
        assert isinstance(result, CypherDateTime)

    def test_convert_time(self):
        """Test converting time property value."""
        pv = PropertyValue(t="time", v="10:30:00")
        result = property_value_to_cypher(pv)
        assert isinstance(result, CypherTime)

    def test_convert_duration(self):
        """Test converting duration property value."""
        pv = PropertyValue(t="duration", v="P1Y2M3DT4H5M6S")
        result = property_value_to_cypher(pv)
        assert isinstance(result, CypherDuration)

    def test_convert_point_cartesian(self):
        """Test converting cartesian point property value."""
        pv = PropertyValue(t="point", v={"x": 1.0, "y": 2.0, "crs": "cartesian"})
        result = property_value_to_cypher(pv)
        assert isinstance(result, CypherPoint)
        assert result.value["x"] == 1.0
        assert result.value["y"] == 2.0

    def test_convert_point_geographic(self):
        """Test converting geographic point property value."""
        pv = PropertyValue(t="point", v={"latitude": 37.7749, "longitude": -122.4194})
        result = property_value_to_cypher(pv)
        assert isinstance(result, CypherPoint)
        assert result.value["latitude"] == 37.7749
        assert result.value["longitude"] == -122.4194

    def test_convert_distance(self):
        """Test converting distance property value."""
        pv = PropertyValue(t="distance", v=42.5)
        result = property_value_to_cypher(pv)
        assert isinstance(result, CypherDistance)
        assert result.value == 42.5

    def test_convert_list(self):
        """Test converting list property value."""
        pv = PropertyValue(
            t="list",
            v=[
                {"t": "int", "v": 1},
                {"t": "int", "v": 2},
                {"t": "string", "v": "three"},
            ],
        )
        result = property_value_to_cypher(pv)
        assert isinstance(result, CypherList)
        assert len(result.value) == 3
        assert isinstance(result.value[0], CypherInt)
        assert isinstance(result.value[1], CypherInt)
        assert isinstance(result.value[2], CypherString)

    def test_convert_map(self):
        """Test converting map property value."""
        pv = PropertyValue(
            t="map",
            v={
                "name": {"t": "string", "v": "Alice"},
                "age": {"t": "int", "v": 30},
            },
        )
        result = property_value_to_cypher(pv)
        assert isinstance(result, CypherMap)
        assert "name" in result.value
        assert "age" in result.value
        assert isinstance(result.value["name"], CypherString)
        assert isinstance(result.value["age"], CypherInt)

    def test_invalid_list_item(self):
        """Test list with invalid item raises error at construction time."""
        from pydantic import ValidationError

        # Validation now happens at PropertyValue construction, not during conversion
        with pytest.raises(ValidationError, match="Type 'list' item at index 0"):
            PropertyValue(t="list", v=["not a property value"])

    def test_invalid_map_value(self):
        """Test map with invalid value raises error at construction time."""
        from pydantic import ValidationError

        # Validation now happens at PropertyValue construction, not during conversion
        with pytest.raises(ValidationError, match="Type 'map' value at key 'key'"):
            PropertyValue(t="map", v={"key": "not a property value"})


@pytest.mark.unit
class TestConvertProperties:
    """Tests for convert_properties helper function."""

    def test_convert_empty_properties(self):
        """Test converting empty property dict."""
        result = convert_properties({})
        assert result == {}

    def test_convert_single_property(self):
        """Test converting single property."""
        props = {"name": PropertyValue(t="string", v="Alice")}
        result = convert_properties(props)
        assert "name" in result
        assert result["name"] == "Alice"

    def test_convert_multiple_properties(self):
        """Test converting multiple properties."""
        props = {
            "name": PropertyValue(t="string", v="Alice"),
            "age": PropertyValue(t="int", v=30),
            "active": PropertyValue(t="bool", v=True),
        }
        result = convert_properties(props)
        assert len(result) == 3
        assert result["name"] == "Alice"
        assert result["age"] == 30
        assert result["active"] is True
