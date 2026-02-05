"""Unit tests for spatial type serialization.

Tests MessagePack serialization/deserialization of spatial types:
- POINT, DISTANCE
- Round-trip preservation of values
- Coordinate format
"""

import pytest

from graphforge.storage.serialization import (
    deserialize_cypher_value,
    deserialize_properties,
    serialize_cypher_value,
    serialize_properties,
)
from graphforge.types.values import CypherDistance, CypherPoint

pytestmark = pytest.mark.unit


class TestSpatialSerialization:
    """Tests for spatial type serialization."""

    def test_serialize_2d_cartesian_point(self):
        """Test 2D Cartesian point serialization."""
        point = CypherPoint({"x": 1.0, "y": 2.0})
        serialized = serialize_cypher_value(point)

        assert serialized["type"] == "point"
        assert serialized["value"]["x"] == 1.0
        assert serialized["value"]["y"] == 2.0
        assert serialized["value"]["crs"] == "cartesian"

    def test_deserialize_2d_cartesian_point(self):
        """Test 2D Cartesian point deserialization."""
        data = {"type": "point", "value": {"x": 1.0, "y": 2.0, "crs": "cartesian"}}
        deserialized = deserialize_cypher_value(data)

        assert isinstance(deserialized, CypherPoint)
        assert deserialized.value["x"] == 1.0
        assert deserialized.value["y"] == 2.0
        assert deserialized.value["crs"] == "cartesian"

    def test_2d_cartesian_point_roundtrip(self):
        """Test 2D Cartesian point round-trip serialization."""
        original = CypherPoint({"x": 1.0, "y": 2.0})
        serialized = serialize_cypher_value(original)
        deserialized = deserialize_cypher_value(serialized)

        assert isinstance(deserialized, CypherPoint)
        assert deserialized.value == original.value

    def test_serialize_3d_cartesian_point(self):
        """Test 3D Cartesian point serialization."""
        point = CypherPoint({"x": 1.0, "y": 2.0, "z": 3.0})
        serialized = serialize_cypher_value(point)

        assert serialized["type"] == "point"
        assert serialized["value"]["x"] == 1.0
        assert serialized["value"]["y"] == 2.0
        assert serialized["value"]["z"] == 3.0
        assert serialized["value"]["crs"] == "cartesian-3d"

    def test_3d_cartesian_point_roundtrip(self):
        """Test 3D Cartesian point round-trip serialization."""
        original = CypherPoint({"x": 1.0, "y": 2.0, "z": 3.0})
        serialized = serialize_cypher_value(original)
        deserialized = deserialize_cypher_value(serialized)

        assert isinstance(deserialized, CypherPoint)
        assert deserialized.value == original.value

    def test_serialize_wgs84_point(self):
        """Test WGS-84 geographic point serialization."""
        point = CypherPoint({"latitude": 51.5074, "longitude": -0.1278})
        serialized = serialize_cypher_value(point)

        assert serialized["type"] == "point"
        assert serialized["value"]["latitude"] == 51.5074
        assert serialized["value"]["longitude"] == -0.1278
        assert serialized["value"]["crs"] == "wgs-84"

    def test_wgs84_point_roundtrip(self):
        """Test WGS-84 point round-trip serialization."""
        original = CypherPoint({"latitude": 51.5074, "longitude": -0.1278})
        serialized = serialize_cypher_value(original)
        deserialized = deserialize_cypher_value(serialized)

        assert isinstance(deserialized, CypherPoint)
        assert deserialized.value == original.value

    def test_serialize_distance(self):
        """Test distance serialization."""
        distance = CypherDistance(5.0)
        serialized = serialize_cypher_value(distance)

        assert serialized["type"] == "distance"
        assert serialized["value"] == 5.0

    def test_deserialize_distance(self):
        """Test distance deserialization."""
        data = {"type": "distance", "value": 5.0}
        deserialized = deserialize_cypher_value(data)

        assert isinstance(deserialized, CypherDistance)
        assert deserialized.value == 5.0

    def test_distance_roundtrip(self):
        """Test distance round-trip serialization."""
        original = CypherDistance(5.0)
        serialized = serialize_cypher_value(original)
        deserialized = deserialize_cypher_value(serialized)

        assert isinstance(deserialized, CypherDistance)
        assert deserialized.value == original.value


class TestSpatialPropertiesSerialization:
    """Tests for properties dict with spatial types."""

    def test_serialize_properties_with_point(self):
        """Test serializing properties containing POINT."""
        from graphforge.types.values import CypherString

        properties = {
            "location": CypherPoint({"x": 1.0, "y": 2.0}),
            "name": CypherString("Home"),
        }

        serialized = serialize_properties(properties)
        assert isinstance(serialized, bytes)

        deserialized = deserialize_properties(serialized)
        assert isinstance(deserialized["location"], CypherPoint)
        assert deserialized["location"].value["x"] == 1.0
        assert deserialized["location"].value["y"] == 2.0

    def test_serialize_properties_with_distance(self):
        """Test serializing properties containing DISTANCE."""
        from graphforge.types.values import CypherString

        properties = {
            "distance_km": CypherDistance(5.5),
            "route": CypherString("A to B"),
        }

        serialized = serialize_properties(properties)
        deserialized = deserialize_properties(serialized)

        assert isinstance(deserialized["distance_km"], CypherDistance)
        assert deserialized["distance_km"].value == 5.5

    def test_serialize_mixed_spatial_properties(self):
        """Test serializing properties with multiple spatial types."""
        from graphforge.types.values import CypherInt, CypherString

        properties = {
            "start": CypherPoint({"x": 0.0, "y": 0.0}),
            "end": CypherPoint({"x": 3.0, "y": 4.0}),
            "distance": CypherDistance(5.0),
            "name": CypherString("Route"),
            "stops": CypherInt(2),
        }

        serialized = serialize_properties(properties)
        deserialized = deserialize_properties(serialized)

        # Verify all types preserved
        assert isinstance(deserialized["start"], CypherPoint)
        assert isinstance(deserialized["end"], CypherPoint)
        assert isinstance(deserialized["distance"], CypherDistance)
        assert isinstance(deserialized["name"], CypherString)
        assert isinstance(deserialized["stops"], CypherInt)

        # Verify values
        assert deserialized["start"].value["x"] == 0.0
        assert deserialized["end"].value["x"] == 3.0
        assert deserialized["distance"].value == 5.0
