"""Unit tests for JSON Graph loader."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from graphforge import GraphForge
from graphforge.datasets.formats.json_graph import PropertyValue
from graphforge.datasets.loaders.json_graph import (
    JSONGraphLoader,
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
        """Test list with invalid item raises error."""
        pv = PropertyValue(t="list", v=["not a property value"])
        with pytest.raises(ValueError, match="List items must be PropertyValue objects"):
            property_value_to_cypher(pv)

    def test_invalid_map_value(self):
        """Test map with invalid value raises error."""
        pv = PropertyValue(t="map", v={"key": "not a property value"})
        with pytest.raises(ValueError, match="Map values must be PropertyValue objects"):
            property_value_to_cypher(pv)


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


class TestJSONGraphLoader:
    """Tests for JSONGraphLoader class."""

    def test_get_format(self):
        """Test loader returns correct format identifier."""
        loader = JSONGraphLoader()
        assert loader.get_format() == "json_graph"

    def test_load_empty_graph(self, tmp_path):
        """Test loading an empty graph."""
        json_file = tmp_path / "empty.json"
        data = {
            "nodes": [],
            "edges": [],
            "directed": True,
            "metadata": {},
        }
        json_file.write_text(json.dumps(data))

        gf = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf, json_file)

        # Verify empty graph
        results = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert results[0]["count"].value == 0

    def test_load_single_node(self, tmp_path):
        """Test loading a graph with a single node."""
        json_file = tmp_path / "single_node.json"
        data = {
            "nodes": [
                {
                    "id": "n0",
                    "labels": ["Person"],
                    "properties": {
                        "name": {"t": "string", "v": "Alice"},
                        "age": {"t": "int", "v": 30},
                    },
                }
            ],
            "edges": [],
            "directed": True,
        }
        json_file.write_text(json.dumps(data))

        gf = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf, json_file)

        # Verify node was created
        results = gf.execute("MATCH (n:Person) RETURN n.name AS name, n.age AS age")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30

    def test_load_multiple_nodes(self, tmp_path):
        """Test loading a graph with multiple nodes."""
        json_file = tmp_path / "multiple_nodes.json"
        data = {
            "nodes": [
                {
                    "id": "n0",
                    "labels": ["Person"],
                    "properties": {"name": {"t": "string", "v": "Alice"}},
                },
                {
                    "id": "n1",
                    "labels": ["Person"],
                    "properties": {"name": {"t": "string", "v": "Bob"}},
                },
                {
                    "id": "n2",
                    "labels": ["Person"],
                    "properties": {"name": {"t": "string", "v": "Charlie"}},
                },
            ],
            "edges": [],
            "directed": True,
        }
        json_file.write_text(json.dumps(data))

        gf = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf, json_file)

        # Verify nodes were created
        results = gf.execute("MATCH (n:Person) RETURN count(n) AS count")
        assert results[0]["count"].value == 3

    def test_load_with_edges(self, tmp_path):
        """Test loading a graph with edges."""
        json_file = tmp_path / "with_edges.json"
        data = {
            "nodes": [
                {
                    "id": "n0",
                    "labels": ["Person"],
                    "properties": {"name": {"t": "string", "v": "Alice"}},
                },
                {
                    "id": "n1",
                    "labels": ["Person"],
                    "properties": {"name": {"t": "string", "v": "Bob"}},
                },
            ],
            "edges": [
                {
                    "id": "e0",
                    "source": "n0",
                    "target": "n1",
                    "type": "KNOWS",
                    "properties": {"since": {"t": "int", "v": 2020}},
                }
            ],
            "directed": True,
        }
        json_file.write_text(json.dumps(data))

        gf = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf, json_file)

        # Verify edge was created
        results = gf.execute(
            "MATCH (a:Person)-[r:KNOWS]->(b:Person) "
            "RETURN a.name AS source, b.name AS target, r.since AS since"
        )
        assert len(results) == 1
        assert results[0]["source"].value == "Alice"
        assert results[0]["target"].value == "Bob"
        assert results[0]["since"].value == 2020

    def test_load_temporal_properties(self, tmp_path):
        """Test loading nodes with temporal properties."""
        json_file = tmp_path / "temporal.json"
        data = {
            "nodes": [
                {
                    "id": "n0",
                    "labels": ["Person"],
                    "properties": {
                        "name": {"t": "string", "v": "Alice"},
                        "birthday": {"t": "date", "v": "1990-01-15"},
                        "registered": {"t": "datetime", "v": "2020-05-10T10:30:00+00:00"},
                    },
                }
            ],
            "edges": [],
            "directed": True,
        }
        json_file.write_text(json.dumps(data))

        gf = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf, json_file)

        # Verify temporal properties
        results = gf.execute("MATCH (n:Person) RETURN n.birthday AS birthday")
        assert len(results) == 1
        assert isinstance(results[0]["birthday"], CypherDate)

    def test_load_spatial_properties(self, tmp_path):
        """Test loading nodes with spatial properties.

        Note: Currently, spatial types (Point, Distance) loaded via the JSON loader
        are stored as dicts and retrieved as CypherMap because the GraphForge API's
        create_node/create_relationship methods don't support Point/Distance types directly.
        They can only be created via Cypher queries (e.g., point({x: 1, y: 2})).
        """
        json_file = tmp_path / "spatial.json"
        data = {
            "nodes": [
                {
                    "id": "n0",
                    "labels": ["Place"],
                    "properties": {
                        "name": {"t": "string", "v": "Office"},
                        "location": {"t": "point", "v": {"x": 1.0, "y": 2.0, "crs": "cartesian"}},
                    },
                }
            ],
            "edges": [],
            "directed": True,
        }
        json_file.write_text(json.dumps(data))

        gf = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf, json_file)

        # Verify spatial properties (currently stored as CypherMap, not CypherPoint)
        results = gf.execute("MATCH (n:Place) RETURN n.location AS location")
        assert len(results) == 1
        # Note: Location is CypherMap because API doesn't support Point directly
        from graphforge.types.values import CypherMap

        assert isinstance(results[0]["location"], CypherMap)
        # But it has the correct coordinate data
        location = results[0]["location"].value
        assert location["x"].value == 1.0
        assert location["y"].value == 2.0
        assert location["crs"].value == "cartesian"

    def test_load_collection_properties(self, tmp_path):
        """Test loading nodes with collection properties."""
        json_file = tmp_path / "collections.json"
        data = {
            "nodes": [
                {
                    "id": "n0",
                    "labels": ["Person"],
                    "properties": {
                        "name": {"t": "string", "v": "Alice"},
                        "hobbies": {
                            "t": "list",
                            "v": [
                                {"t": "string", "v": "reading"},
                                {"t": "string", "v": "coding"},
                            ],
                        },
                    },
                }
            ],
            "edges": [],
            "directed": True,
        }
        json_file.write_text(json.dumps(data))

        gf = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf, json_file)

        # Verify collection properties
        results = gf.execute("MATCH (n:Person) RETURN n.hobbies AS hobbies")
        assert len(results) == 1
        assert isinstance(results[0]["hobbies"], CypherList)
        assert len(results[0]["hobbies"].value) == 2

    def test_file_not_found(self):
        """Test loading from non-existent file raises error."""
        gf = GraphForge()
        loader = JSONGraphLoader()
        with pytest.raises(FileNotFoundError, match="JSON Graph file not found"):
            loader.load(gf, Path("/nonexistent/file.json"))

    def test_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises error."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("not valid json {")

        gf = GraphForge()
        loader = JSONGraphLoader()
        with pytest.raises(ValueError, match="Invalid JSON"):
            loader.load(gf, json_file)

    def test_invalid_schema(self, tmp_path):
        """Test loading JSON with invalid schema raises error."""
        json_file = tmp_path / "invalid_schema.json"
        data = {
            "nodes": [
                {
                    "id": "n0",
                    "labels": ["Person"],
                    "properties": {"age": {"t": "invalid_type", "v": 30}},
                }
            ],
            "edges": [],
        }
        json_file.write_text(json.dumps(data))

        gf = GraphForge()
        loader = JSONGraphLoader()
        with pytest.raises(ValueError, match="Invalid JSON Graph format"):
            loader.load(gf, json_file)
