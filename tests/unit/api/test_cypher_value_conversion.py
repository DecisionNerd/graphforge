"""Unit tests for Python value to CypherValue conversion in API.

Tests the _to_cypher_value() method in GraphForge, with focus on spatial type support.
"""

import datetime

import pytest

from graphforge import GraphForge
from graphforge.types.values import (
    CypherBool,
    CypherDate,
    CypherDateTime,
    CypherDuration,
    CypherFloat,
    CypherInt,
    CypherList,
    CypherMap,
    CypherNull,
    CypherPoint,
    CypherString,
    CypherTime,
    CypherType,
)


@pytest.mark.unit
class TestBasicTypeConversion:
    """Test conversion of basic Python types to CypherValue types."""

    def test_none_to_cypher_null(self):
        """Test None converts to CypherNull."""
        gf = GraphForge()
        result = gf._to_cypher_value(None)
        assert isinstance(result, CypherNull)
        assert result.type == CypherType.NULL

    def test_bool_to_cypher_bool(self):
        """Test bool converts to CypherBool."""
        gf = GraphForge()
        result_true = gf._to_cypher_value(True)
        result_false = gf._to_cypher_value(False)
        assert isinstance(result_true, CypherBool)
        assert result_true.value is True
        assert isinstance(result_false, CypherBool)
        assert result_false.value is False

    def test_int_to_cypher_int(self):
        """Test int converts to CypherInt."""
        gf = GraphForge()
        result = gf._to_cypher_value(42)
        assert isinstance(result, CypherInt)
        assert result.value == 42

    def test_float_to_cypher_float(self):
        """Test float converts to CypherFloat."""
        gf = GraphForge()
        result = gf._to_cypher_value(3.14)
        assert isinstance(result, CypherFloat)
        assert result.value == 3.14

    def test_str_to_cypher_string(self):
        """Test str converts to CypherString."""
        gf = GraphForge()
        result = gf._to_cypher_value("hello")
        assert isinstance(result, CypherString)
        assert result.value == "hello"


@pytest.mark.unit
class TestTemporalTypeConversion:
    """Test conversion of temporal Python types to CypherValue types."""

    def test_date_to_cypher_date(self):
        """Test datetime.date converts to CypherDate."""
        gf = GraphForge()
        date_value = datetime.date(2024, 1, 15)
        result = gf._to_cypher_value(date_value)
        assert isinstance(result, CypherDate)
        assert result.value == date_value

    def test_datetime_to_cypher_datetime(self):
        """Test datetime.datetime converts to CypherDateTime."""
        gf = GraphForge()
        dt_value = datetime.datetime(2024, 1, 15, 10, 30, 45)
        result = gf._to_cypher_value(dt_value)
        assert isinstance(result, CypherDateTime)
        assert result.value == dt_value

    def test_time_to_cypher_time(self):
        """Test datetime.time converts to CypherTime."""
        gf = GraphForge()
        time_value = datetime.time(10, 30, 45)
        result = gf._to_cypher_value(time_value)
        assert isinstance(result, CypherTime)
        assert result.value == time_value

    def test_timedelta_to_cypher_duration(self):
        """Test datetime.timedelta converts to CypherDuration."""
        gf = GraphForge()
        td_value = datetime.timedelta(days=5, hours=3)
        result = gf._to_cypher_value(td_value)
        assert isinstance(result, CypherDuration)


@pytest.mark.unit
class TestSpatialTypeConversion:
    """Test conversion of coordinate dicts to CypherPoint (Issue #97)."""

    def test_cartesian_2d_to_cypher_point(self):
        """Test dict with {x, y} converts to CypherPoint."""
        gf = GraphForge()
        coords = {"x": 1.0, "y": 2.0}
        result = gf._to_cypher_value(coords)
        assert isinstance(result, CypherPoint)
        assert result.type == CypherType.POINT
        assert result.value["x"] == 1.0
        assert result.value["y"] == 2.0
        assert result.value["crs"] == "cartesian"

    def test_cartesian_3d_to_cypher_point(self):
        """Test dict with {x, y, z} converts to CypherPoint."""
        gf = GraphForge()
        coords = {"x": 1.0, "y": 2.0, "z": 3.0}
        result = gf._to_cypher_value(coords)
        assert isinstance(result, CypherPoint)
        assert result.type == CypherType.POINT
        assert result.value["x"] == 1.0
        assert result.value["y"] == 2.0
        assert result.value["z"] == 3.0
        assert result.value["crs"] == "cartesian-3d"

    def test_geographic_to_cypher_point(self):
        """Test dict with {latitude, longitude} converts to CypherPoint."""
        gf = GraphForge()
        coords = {"latitude": 37.7749, "longitude": -122.4194}
        result = gf._to_cypher_value(coords)
        assert isinstance(result, CypherPoint)
        assert result.type == CypherType.POINT
        assert result.value["latitude"] == 37.7749
        assert result.value["longitude"] == -122.4194
        assert result.value["crs"] == "wgs-84"

    def test_invalid_latitude_falls_back_to_map(self):
        """Test invalid latitude (>90) falls back to CypherMap."""
        gf = GraphForge()
        coords = {"latitude": 100.0, "longitude": 50.0}  # latitude > 90
        result = gf._to_cypher_value(coords)
        # Should fall back to CypherMap since CypherPoint validation fails
        assert isinstance(result, CypherMap)
        assert result.value["latitude"].value == 100.0
        assert result.value["longitude"].value == 50.0

    def test_invalid_latitude_negative_falls_back_to_map(self):
        """Test invalid latitude (<-90) falls back to CypherMap."""
        gf = GraphForge()
        coords = {"latitude": -100.0, "longitude": 50.0}  # latitude < -90
        result = gf._to_cypher_value(coords)
        assert isinstance(result, CypherMap)

    def test_invalid_longitude_falls_back_to_map(self):
        """Test invalid longitude (>180) falls back to CypherMap."""
        gf = GraphForge()
        coords = {"latitude": 50.0, "longitude": 200.0}  # longitude > 180
        result = gf._to_cypher_value(coords)
        assert isinstance(result, CypherMap)

    def test_invalid_longitude_negative_falls_back_to_map(self):
        """Test invalid longitude (<-180) falls back to CypherMap."""
        gf = GraphForge()
        coords = {"latitude": 50.0, "longitude": -200.0}  # longitude < -180
        result = gf._to_cypher_value(coords)
        assert isinstance(result, CypherMap)

    def test_mixed_dict_with_x_only_to_cypher_map(self):
        """Test dict with x but not y converts to CypherMap."""
        gf = GraphForge()
        data = {"x": 1.0, "name": "test"}
        result = gf._to_cypher_value(data)
        assert isinstance(result, CypherMap)
        assert result.value["x"].value == 1.0
        assert result.value["name"].value == "test"

    def test_mixed_dict_with_y_only_to_cypher_map(self):
        """Test dict with y but not x converts to CypherMap."""
        gf = GraphForge()
        data = {"y": 2.0, "name": "test"}
        result = gf._to_cypher_value(data)
        assert isinstance(result, CypherMap)

    def test_mixed_dict_with_latitude_only_to_cypher_map(self):
        """Test dict with latitude but not longitude converts to CypherMap."""
        gf = GraphForge()
        data = {"latitude": 37.7, "name": "test"}
        result = gf._to_cypher_value(data)
        assert isinstance(result, CypherMap)

    def test_regular_dict_to_cypher_map(self):
        """Test regular dict (no coordinates) converts to CypherMap."""
        gf = GraphForge()
        data = {"name": "Alice", "age": 30}
        result = gf._to_cypher_value(data)
        assert isinstance(result, CypherMap)
        assert result.value["name"].value == "Alice"
        assert result.value["age"].value == 30

    def test_empty_dict_to_empty_cypher_map(self):
        """Test empty dict converts to empty CypherMap."""
        gf = GraphForge()
        result = gf._to_cypher_value({})
        assert isinstance(result, CypherMap)
        assert len(result.value) == 0

    def test_cartesian_with_int_coordinates(self):
        """Test Cartesian coordinates with integers (should convert to float)."""
        gf = GraphForge()
        coords = {"x": 1, "y": 2}
        result = gf._to_cypher_value(coords)
        assert isinstance(result, CypherPoint)
        assert result.value["x"] == 1.0
        assert result.value["y"] == 2.0

    def test_cartesian_with_crs_to_cypher_point(self):
        """Test dict with {x, y, crs} converts to CypherPoint."""
        gf = GraphForge()
        coords = {"x": 1.0, "y": 2.0, "crs": "cartesian"}
        result = gf._to_cypher_value(coords)
        assert isinstance(result, CypherPoint)
        assert result.value["x"] == 1.0
        assert result.value["y"] == 2.0
        assert result.value["crs"] == "cartesian"

    def test_cartesian_3d_with_crs_to_cypher_point(self):
        """Test dict with {x, y, z, crs} converts to CypherPoint."""
        gf = GraphForge()
        coords = {"x": 1.0, "y": 2.0, "z": 3.0, "crs": "cartesian-3d"}
        result = gf._to_cypher_value(coords)
        assert isinstance(result, CypherPoint)
        assert result.value["x"] == 1.0
        assert result.value["y"] == 2.0
        assert result.value["z"] == 3.0
        assert result.value["crs"] == "cartesian-3d"

    def test_geographic_with_crs_to_cypher_point(self):
        """Test dict with {latitude, longitude, crs} converts to CypherPoint."""
        gf = GraphForge()
        coords = {"latitude": 37.7749, "longitude": -122.4194, "crs": "wgs-84"}
        result = gf._to_cypher_value(coords)
        assert isinstance(result, CypherPoint)
        assert result.value["latitude"] == 37.7749
        assert result.value["longitude"] == -122.4194
        assert result.value["crs"] == "wgs-84"

    def test_cartesian_with_extra_keys_to_cypher_map(self):
        """Test dict with x, y and extra keys converts to CypherMap (not CypherPoint)."""
        gf = GraphForge()
        data = {"x": 1.0, "y": 2.0, "name": "test"}
        result = gf._to_cypher_value(data)
        # Should be CypherMap because of extra "name" key
        assert isinstance(result, CypherMap)
        assert result.value["x"].value == 1.0
        assert result.value["y"].value == 2.0
        assert result.value["name"].value == "test"

    def test_geographic_with_extra_keys_to_cypher_map(self):
        """Test dict with latitude, longitude and extra keys converts to CypherMap."""
        gf = GraphForge()
        data = {"latitude": 37.7749, "longitude": -122.4194, "name": "SF"}
        result = gf._to_cypher_value(data)
        # Should be CypherMap because of extra "name" key
        assert isinstance(result, CypherMap)
        assert result.value["latitude"].value == 37.7749
        assert result.value["longitude"].value == -122.4194
        assert result.value["name"].value == "SF"

    def test_cartesian_3d_with_extra_keys_to_cypher_map(self):
        """Test dict with x, y, z and extra keys converts to CypherMap."""
        gf = GraphForge()
        data = {"x": 1.0, "y": 2.0, "z": 3.0, "id": "point1"}
        result = gf._to_cypher_value(data)
        # Should be CypherMap because of extra "id" key
        assert isinstance(result, CypherMap)
        assert result.value["x"].value == 1.0
        assert result.value["y"].value == 2.0
        assert result.value["z"].value == 3.0
        assert result.value["id"].value == "point1"


@pytest.mark.unit
class TestListConversion:
    """Test conversion of lists to CypherList."""

    def test_list_to_cypher_list(self):
        """Test list converts to CypherList with recursive conversion."""
        gf = GraphForge()
        data = [1, "hello", 3.14, True, None]
        result = gf._to_cypher_value(data)
        assert isinstance(result, CypherList)
        assert isinstance(result.value[0], CypherInt)
        assert isinstance(result.value[1], CypherString)
        assert isinstance(result.value[2], CypherFloat)
        assert isinstance(result.value[3], CypherBool)
        assert isinstance(result.value[4], CypherNull)

    def test_nested_list_conversion(self):
        """Test nested list converts recursively."""
        gf = GraphForge()
        data = [[1, 2], [3, 4]]
        result = gf._to_cypher_value(data)
        assert isinstance(result, CypherList)
        assert isinstance(result.value[0], CypherList)
        assert isinstance(result.value[1], CypherList)

    def test_list_with_point_dicts(self):
        """Test list containing coordinate dicts converts to list of CypherPoints."""
        gf = GraphForge()
        data = [{"x": 1.0, "y": 2.0}, {"x": 3.0, "y": 4.0}]
        result = gf._to_cypher_value(data)
        assert isinstance(result, CypherList)
        assert isinstance(result.value[0], CypherPoint)
        assert isinstance(result.value[1], CypherPoint)


@pytest.mark.unit
class TestNestedDictConversion:
    """Test conversion of nested dicts."""

    def test_nested_dict_with_coordinates(self):
        """Test dict with nested coordinate dict."""
        gf = GraphForge()
        data = {"location": {"x": 1.0, "y": 2.0}, "name": "test"}
        result = gf._to_cypher_value(data)
        assert isinstance(result, CypherMap)
        # Nested coordinate dict should be converted to CypherPoint
        assert isinstance(result.value["location"], CypherPoint)
        assert isinstance(result.value["name"], CypherString)

    def test_nested_dict_no_coordinates(self):
        """Test nested dict without coordinates."""
        gf = GraphForge()
        data = {"user": {"name": "Alice", "age": 30}}
        result = gf._to_cypher_value(data)
        assert isinstance(result, CypherMap)
        assert isinstance(result.value["user"], CypherMap)


@pytest.mark.unit
class TestUnsupportedTypes:
    """Test error handling for unsupported types."""

    def test_unsupported_type_raises_typeerror(self):
        """Test unsupported type raises TypeError."""
        gf = GraphForge()

        class CustomClass:
            pass

        with pytest.raises(TypeError, match="Unsupported property value type"):
            gf._to_cypher_value(CustomClass())
