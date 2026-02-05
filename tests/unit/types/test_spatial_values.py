"""Unit tests for spatial CypherValue types.

Tests POINT and DISTANCE types including:
- Construction from coordinate dictionaries
- Validation of coordinates
- Comparison operations
- Type conversions
"""

import pytest

from graphforge.types.values import CypherDistance, CypherPoint, CypherType

pytestmark = pytest.mark.unit


class TestCypherPoint:
    """Tests for CypherPoint type."""

    def test_construct_2d_cartesian(self):
        """Test construction with 2D Cartesian coordinates."""
        point = CypherPoint({"x": 1.0, "y": 2.0})
        assert point.type == CypherType.POINT
        assert point.value["x"] == 1.0
        assert point.value["y"] == 2.0
        assert point.value["crs"] == "cartesian"

    def test_construct_3d_cartesian(self):
        """Test construction with 3D Cartesian coordinates."""
        point = CypherPoint({"x": 1.0, "y": 2.0, "z": 3.0})
        assert point.type == CypherType.POINT
        assert point.value["x"] == 1.0
        assert point.value["y"] == 2.0
        assert point.value["z"] == 3.0
        assert point.value["crs"] == "cartesian-3d"

    def test_construct_wgs84(self):
        """Test construction with WGS-84 geographic coordinates."""
        point = CypherPoint({"latitude": 51.5074, "longitude": -0.1278})
        assert point.type == CypherType.POINT
        assert point.value["latitude"] == 51.5074
        assert point.value["longitude"] == -0.1278
        assert point.value["crs"] == "wgs-84"

    def test_integer_coordinates_converted_to_float(self):
        """Test that integer coordinates are converted to float."""
        point = CypherPoint({"x": 1, "y": 2})
        assert point.value["x"] == 1.0
        assert point.value["y"] == 2.0
        assert isinstance(point.value["x"], float)

    def test_invalid_latitude_raises_error(self):
        """Test that invalid latitude raises ValueError."""
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            CypherPoint({"latitude": 91.0, "longitude": 0.0})

        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            CypherPoint({"latitude": -91.0, "longitude": 0.0})

    def test_invalid_longitude_raises_error(self):
        """Test that invalid longitude raises ValueError."""
        with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
            CypherPoint({"latitude": 0.0, "longitude": 181.0})

        with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
            CypherPoint({"latitude": 0.0, "longitude": -181.0})

    def test_missing_coordinates_raises_error(self):
        """Test that missing coordinates raise ValueError."""
        with pytest.raises(ValueError, match="Point requires either"):
            CypherPoint({"x": 1.0})  # Missing y

        with pytest.raises(ValueError, match="Point requires either"):
            CypherPoint({"latitude": 51.5})  # Missing longitude

        with pytest.raises(ValueError, match="Point requires either"):
            CypherPoint({"foo": 1.0, "bar": 2.0})  # Invalid keys

    def test_repr(self):
        """Test string representation."""
        point = CypherPoint({"x": 1.0, "y": 2.0})
        repr_str = repr(point)
        assert "CypherPoint" in repr_str
        assert "'x': 1.0" in repr_str
        assert "'y': 2.0" in repr_str


class TestCypherDistance:
    """Tests for CypherDistance type."""

    def test_construct_positive_distance(self):
        """Test construction with positive distance."""
        distance = CypherDistance(5.0)
        assert distance.type == CypherType.DISTANCE
        assert distance.value == 5.0

    def test_construct_zero_distance(self):
        """Test construction with zero distance."""
        distance = CypherDistance(0.0)
        assert distance.type == CypherType.DISTANCE
        assert distance.value == 0.0

    def test_integer_converted_to_float(self):
        """Test that integer distance is converted to float."""
        distance = CypherDistance(5)
        assert distance.value == 5.0
        assert isinstance(distance.value, float)

    def test_negative_distance_raises_error(self):
        """Test that negative distance raises ValueError."""
        with pytest.raises(ValueError, match="Distance must be non-negative"):
            CypherDistance(-1.0)

    def test_repr(self):
        """Test string representation."""
        distance = CypherDistance(5.0)
        assert repr(distance) == "CypherDistance(5.0)"


class TestPointEquality:
    """Tests for point equality comparisons."""

    def test_same_cartesian_points_equal(self):
        """Test that identical Cartesian points are equal."""
        p1 = CypherPoint({"x": 1.0, "y": 2.0})
        p2 = CypherPoint({"x": 1.0, "y": 2.0})
        result = p1.equals(p2)
        assert result.value is True

    def test_different_cartesian_points_not_equal(self):
        """Test that different Cartesian points are not equal."""
        p1 = CypherPoint({"x": 1.0, "y": 2.0})
        p2 = CypherPoint({"x": 3.0, "y": 4.0})
        result = p1.equals(p2)
        assert result.value is False

    def test_2d_and_3d_points_not_equal(self):
        """Test that 2D and 3D points with same x,y are not equal."""
        p1 = CypherPoint({"x": 1.0, "y": 2.0})
        p2 = CypherPoint({"x": 1.0, "y": 2.0, "z": 0.0})
        result = p1.equals(p2)
        assert result.value is False

    def test_cartesian_and_wgs84_not_equal(self):
        """Test that Cartesian and WGS-84 points are not equal."""
        p1 = CypherPoint({"x": 51.5, "y": -0.1})
        p2 = CypherPoint({"latitude": 51.5, "longitude": -0.1})
        result = p1.equals(p2)
        assert result.value is False


class TestDistanceEquality:
    """Tests for distance equality comparisons."""

    def test_same_distances_equal(self):
        """Test that identical distances are equal."""
        d1 = CypherDistance(5.0)
        d2 = CypherDistance(5.0)
        result = d1.equals(d2)
        assert result.value is True

    def test_different_distances_not_equal(self):
        """Test that different distances are not equal."""
        d1 = CypherDistance(5.0)
        d2 = CypherDistance(10.0)
        result = d1.equals(d2)
        assert result.value is False
