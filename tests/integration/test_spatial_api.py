"""Integration tests for spatial API support (Issue #97).

Tests end-to-end workflows with Point types via Python API.
"""

import datetime

from graphforge import GraphForge
from graphforge.types.values import CypherDistance, CypherPoint, CypherType


class TestSpatialAPIIntegration:
    """Test spatial types work end-to-end via Python API."""

    def test_create_node_with_cartesian_point(self):
        """Test creating node with Cartesian Point and querying it."""
        gf = GraphForge()

        # Create node with Point via Python API
        office = gf.create_node(["Place"], name="Office", location={"x": 1.0, "y": 2.0})

        # Verify node was created
        assert office.properties["location"].type == CypherType.POINT

        # Query the node
        results = gf.execute("MATCH (p:Place) RETURN p.name AS name, p.location AS loc")
        assert len(results) == 1
        assert results[0]["name"].value == "Office"
        assert isinstance(results[0]["loc"], CypherPoint)
        assert results[0]["loc"].value["x"] == 1.0
        assert results[0]["loc"].value["y"] == 2.0

    def test_create_node_with_geographic_point(self):
        """Test creating node with Geographic Point."""
        gf = GraphForge()

        # Create node with Geographic Point
        sf = gf.create_node(
            ["City"], name="San Francisco", location={"latitude": 37.7749, "longitude": -122.4194}
        )

        # Verify point was created correctly
        assert sf.properties["location"].type == CypherType.POINT
        assert sf.properties["location"].value["crs"] == "wgs-84"

        # Query the node
        results = gf.execute("MATCH (c:City) RETURN c.location AS loc")
        assert len(results) == 1
        assert isinstance(results[0]["loc"], CypherPoint)
        assert results[0]["loc"].value["latitude"] == 37.7749
        assert results[0]["loc"].value["longitude"] == -122.4194

    def test_create_node_with_3d_point(self):
        """Test creating node with 3D Cartesian Point."""
        gf = GraphForge()

        # Create node with 3D Point
        point = gf.create_node(["Location"], name="Point", coords={"x": 1.0, "y": 2.0, "z": 3.0})

        # Verify 3D point
        assert point.properties["coords"].value["z"] == 3.0
        assert point.properties["coords"].value["crs"] == "cartesian-3d"

        # Query it
        results = gf.execute("MATCH (l:Location) RETURN l.coords AS coords")
        assert results[0]["coords"].value["z"] == 3.0

    def test_distance_function_with_api_points(self):
        """Test distance() function works with Points created via API."""
        gf = GraphForge()

        # Create two places with Point locations
        gf.create_node(["Place"], name="Office", location={"x": 0.0, "y": 0.0})
        gf.create_node(["Place"], name="Home", location={"x": 3.0, "y": 4.0})

        # Calculate distance
        results = gf.execute(
            """
            MATCH (a:Place {name: 'Office'}), (b:Place {name: 'Home'})
            RETURN distance(a.location, b.location) AS dist
            """
        )

        assert len(results) == 1
        # Euclidean distance: sqrt(3^2 + 4^2) = 5.0
        assert isinstance(results[0]["dist"], CypherDistance)
        assert results[0]["dist"].value == 5.0

    def test_create_relationship_with_point_property(self):
        """Test creating relationship with Point property."""
        gf = GraphForge()

        # Create nodes
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")

        # Create relationship with Point property
        rel = gf.create_relationship(alice, bob, "TRAVELS_TO", meeting_point={"x": 10.0, "y": 20.0})

        # Verify Point was created
        assert isinstance(rel.properties["meeting_point"], CypherPoint)

        # Query relationship
        results = gf.execute(
            """
            MATCH (a:Person)-[r:TRAVELS_TO]->(b:Person)
            RETURN r.meeting_point AS point
            """
        )
        assert len(results) == 1
        assert isinstance(results[0]["point"], CypherPoint)
        assert results[0]["point"].value["x"] == 10.0
        assert results[0]["point"].value["y"] == 20.0

    def test_query_return_point_properties(self):
        """Test returning Point properties."""
        gf = GraphForge()

        # Create nodes with different locations
        gf.create_node(["Place"], name="A", location={"x": 1.0, "y": 1.0})
        gf.create_node(["Place"], name="B", location={"x": 5.0, "y": 5.0})

        # Query and return all points
        results = gf.execute(
            """
            MATCH (p:Place)
            RETURN p.name AS name, p.location AS location
            ORDER BY name
            """
        )

        assert len(results) == 2
        assert results[0]["name"].value == "A"
        assert isinstance(results[0]["location"], CypherPoint)
        assert results[0]["location"].value["x"] == 1.0
        assert results[1]["name"].value == "B"
        assert results[1]["location"].value["x"] == 5.0

    def test_spatial_and_temporal_properties(self):
        """Test node with both spatial and temporal properties."""
        gf = GraphForge()

        # Create node with both Point and temporal properties
        event_time = datetime.datetime(2024, 1, 15, 10, 30)
        gf.create_node(
            ["Event"],
            name="Meeting",
            location={"x": 10.0, "y": 20.0},
            timestamp=event_time,
        )

        # Query both properties
        results = gf.execute(
            """
            MATCH (e:Event)
            RETURN e.location AS loc, e.timestamp AS time
            """
        )

        assert len(results) == 1
        assert isinstance(results[0]["loc"], CypherPoint)
        assert results[0]["loc"].value["x"] == 10.0
        assert results[0]["time"].value == event_time

    def test_invalid_coordinates_create_map(self):
        """Test that invalid coordinates create CypherMap instead of Point."""
        gf = GraphForge()

        # Create node with invalid latitude
        node = gf.create_node(
            ["Place"], name="Invalid", location={"latitude": 100.0, "longitude": 50.0}
        )

        # Should have created CypherMap, not CypherPoint
        assert node.properties["location"].type == CypherType.MAP

        # Query it - should be a map
        results = gf.execute("MATCH (p:Place) RETURN p.location AS loc")
        assert results[0]["loc"].type == CypherType.MAP

    def test_multiple_points_distance_comparison(self):
        """Test distance calculations with multiple points."""
        gf = GraphForge()

        # Create origin and several destinations
        gf.create_node(["Place"], name="Origin", location={"x": 0.0, "y": 0.0})
        gf.create_node(["Place"], name="Near", location={"x": 1.0, "y": 1.0})
        gf.create_node(["Place"], name="Far", location={"x": 10.0, "y": 10.0})

        # Find closest place to origin
        results = gf.execute(
            """
            MATCH (origin:Place {name: 'Origin'}), (dest:Place)
            WHERE dest.name <> 'Origin'
            WITH dest, distance(origin.location, dest.location) AS dist
            RETURN dest.name AS name, dist
            ORDER BY dist
            LIMIT 1
            """
        )

        assert len(results) == 1
        assert results[0]["name"].value == "Near"

    def test_point_in_list_property(self):
        """Test list of Points as property."""
        gf = GraphForge()

        # Create node with list of Point dicts
        gf.create_node(
            ["Route"],
            name="Path",
            waypoints=[{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 1.0}, {"x": 2.0, "y": 2.0}],
        )

        # Query the list
        results = gf.execute("MATCH (r:Route) RETURN r.waypoints AS points")
        assert len(results) == 1
        waypoints = results[0]["points"].value
        assert len(waypoints) == 3
        # Each waypoint should be a CypherPoint
        assert all(isinstance(wp, CypherPoint) for wp in waypoints)
        assert waypoints[0].value["x"] == 0.0
        assert waypoints[1].value["x"] == 1.0
        assert waypoints[2].value["x"] == 2.0


class TestSpatialAPIPersistence:
    """Test spatial types persist correctly to SQLite."""

    def test_point_persists_to_sqlite(self, tmp_path):
        """Test Point properties persist and reload from SQLite."""
        db_path = tmp_path / "test.db"

        # Create graph with Point
        gf1 = GraphForge(str(db_path))
        gf1.create_node(["Place"], name="Office", location={"x": 10.0, "y": 20.0})
        gf1.close()

        # Reload graph
        gf2 = GraphForge(str(db_path))
        results = gf2.execute("MATCH (p:Place) RETURN p.location AS loc")

        assert len(results) == 1
        assert isinstance(results[0]["loc"], CypherPoint)
        assert results[0]["loc"].value["x"] == 10.0
        assert results[0]["loc"].value["y"] == 20.0

        gf2.close()
