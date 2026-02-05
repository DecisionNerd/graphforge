"""Unit tests for spatial functions in evaluator.

Tests spatial constructor and calculation functions:
- point({x, y}) and point({latitude, longitude})
- distance(point1, point2)
"""

import pytest

from graphforge.ast.expression import FunctionCall, Literal
from graphforge.executor.evaluator import ExecutionContext, evaluate_expression
from graphforge.types.values import (
    CypherDistance,
    CypherFloat,
    CypherPoint,
)

pytestmark = pytest.mark.unit


class TestPointFunction:
    """Tests for point() constructor function."""

    def test_point_2d_cartesian(self):
        """Test point() with 2D Cartesian coordinates."""
        # Use plain dict which will be converted to CypherMap by evaluator
        coords = {"x": 1.0, "y": 2.0}
        func = FunctionCall(name="point", args=[Literal(value=coords)])
        ctx = ExecutionContext()

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherPoint)
        assert result.value["x"] == 1.0
        assert result.value["y"] == 2.0
        assert result.value["crs"] == "cartesian"

    def test_point_3d_cartesian(self):
        """Test point() with 3D Cartesian coordinates."""
        coords = {"x": 1.0, "y": 2.0, "z": 3.0}
        func = FunctionCall(name="point", args=[Literal(value=coords)])
        ctx = ExecutionContext()

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherPoint)
        assert result.value["x"] == 1.0
        assert result.value["y"] == 2.0
        assert result.value["z"] == 3.0
        assert result.value["crs"] == "cartesian-3d"

    def test_point_wgs84(self):
        """Test point() with WGS-84 geographic coordinates."""
        coords = {"latitude": 51.5074, "longitude": -0.1278}
        func = FunctionCall(name="point", args=[Literal(value=coords)])
        ctx = ExecutionContext()

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherPoint)
        assert result.value["latitude"] == 51.5074
        assert result.value["longitude"] == -0.1278
        assert result.value["crs"] == "wgs-84"

    def test_point_with_integer_coordinates(self):
        """Test point() accepts integer coordinates."""
        coords = {"x": 1, "y": 2}
        func = FunctionCall(name="point", args=[Literal(value=coords)])
        ctx = ExecutionContext()

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherPoint)
        assert result.value["x"] == 1.0
        assert result.value["y"] == 2.0

    def test_point_wrong_arg_count(self):
        """Test point() with wrong number of arguments."""
        func = FunctionCall(name="point", args=[])
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="POINT expects 1 argument"):
            evaluate_expression(func, ctx)

    def test_point_non_map_argument(self):
        """Test point() with non-map argument."""
        func = FunctionCall(name="point", args=[Literal(value="not a map")])
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="POINT expects map argument"):
            evaluate_expression(func, ctx)

    def test_point_non_numeric_coordinate(self):
        """Test point() with non-numeric coordinate value."""
        coords = {"x": "not a number", "y": 2.0}
        func = FunctionCall(name="point", args=[Literal(value=coords)])
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="coordinate 'x' must be numeric"):
            evaluate_expression(func, ctx)


class TestDistanceFunction:
    """Tests for distance() calculation function."""

    def test_distance_2d_cartesian(self):
        """Test distance() with 2D Cartesian points."""
        p1 = CypherPoint({"x": 0.0, "y": 0.0})
        p2 = CypherPoint({"x": 3.0, "y": 4.0})

        ctx = ExecutionContext()
        ctx.bind("p1", p1)
        ctx.bind("p2", p2)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="distance", args=[Variable(name="p1"), Variable(name="p2")])

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherDistance)
        assert result.value == 5.0  # 3-4-5 triangle

    def test_distance_3d_cartesian(self):
        """Test distance() with 3D Cartesian points."""
        p1 = CypherPoint({"x": 0.0, "y": 0.0, "z": 0.0})
        p2 = CypherPoint({"x": 1.0, "y": 2.0, "z": 2.0})

        ctx = ExecutionContext()
        ctx.bind("p1", p1)
        ctx.bind("p2", p2)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="distance", args=[Variable(name="p1"), Variable(name="p2")])

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherDistance)
        # sqrt(1^2 + 2^2 + 2^2) = sqrt(9) = 3.0
        assert result.value == 3.0

    def test_distance_same_point_is_zero(self):
        """Test distance() between same point is zero."""
        p1 = CypherPoint({"x": 1.0, "y": 2.0})
        p2 = CypherPoint({"x": 1.0, "y": 2.0})

        ctx = ExecutionContext()
        ctx.bind("p1", p1)
        ctx.bind("p2", p2)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="distance", args=[Variable(name="p1"), Variable(name="p2")])

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherDistance)
        assert result.value == 0.0

    def test_distance_wgs84(self):
        """Test distance() with WGS-84 geographic points (Haversine)."""
        # London and Paris (approximately 344 km apart)
        london = CypherPoint({"latitude": 51.5074, "longitude": -0.1278})
        paris = CypherPoint({"latitude": 48.8566, "longitude": 2.3522})

        ctx = ExecutionContext()
        ctx.bind("london", london)
        ctx.bind("paris", paris)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="distance", args=[Variable(name="london"), Variable(name="paris")])

        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherDistance)
        # Approximate distance should be around 340,000-350,000 meters
        assert 340000 < result.value < 350000

    def test_distance_wrong_arg_count(self):
        """Test distance() with wrong number of arguments."""
        func = FunctionCall(name="distance", args=[])
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="DISTANCE expects 2 arguments"):
            evaluate_expression(func, ctx)

    def test_distance_non_point_first_arg(self):
        """Test distance() with non-point first argument."""
        p = CypherPoint({"x": 1.0, "y": 2.0})

        ctx = ExecutionContext()
        ctx.bind("x", CypherFloat(5.0))
        ctx.bind("p", p)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="distance", args=[Variable(name="x"), Variable(name="p")])

        with pytest.raises(TypeError, match="DISTANCE first argument must be point"):
            evaluate_expression(func, ctx)

    def test_distance_non_point_second_arg(self):
        """Test distance() with non-point second argument."""
        p = CypherPoint({"x": 1.0, "y": 2.0})

        ctx = ExecutionContext()
        ctx.bind("p", p)
        ctx.bind("x", CypherFloat(5.0))

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="distance", args=[Variable(name="p"), Variable(name="x")])

        with pytest.raises(TypeError, match="DISTANCE second argument must be point"):
            evaluate_expression(func, ctx)

    def test_distance_mixed_crs_raises_error(self):
        """Test distance() with different CRS raises error."""
        cartesian = CypherPoint({"x": 1.0, "y": 2.0})
        wgs84 = CypherPoint({"latitude": 51.5, "longitude": -0.1})

        ctx = ExecutionContext()
        ctx.bind("cart", cartesian)
        ctx.bind("geo", wgs84)

        from graphforge.ast.expression import Variable

        func = FunctionCall(name="distance", args=[Variable(name="cart"), Variable(name="geo")])

        with pytest.raises(
            ValueError, match="Cannot calculate distance between points with different CRS"
        ):
            evaluate_expression(func, ctx)
