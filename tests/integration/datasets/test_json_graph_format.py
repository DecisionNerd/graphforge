"""Integration tests for JSON Graph format Pydantic models."""

import pytest
from pydantic import ValidationError

from graphforge.datasets.formats.json_graph import (
    JSONGraph,
    JSONGraphEdge,
    JSONGraphNode,
    PropertyValue,
)

pytestmark = pytest.mark.integration


class TestPropertyValue:
    """Tests for PropertyValue model."""

    def test_valid_null(self):
        """Test null property value."""
        pv = PropertyValue(t="null", v=None)
        assert pv.t == "null"
        assert pv.v is None

    def test_valid_bool(self):
        """Test boolean property values."""
        pv_true = PropertyValue(t="bool", v=True)
        assert pv_true.t == "bool"
        assert pv_true.v is True

        pv_false = PropertyValue(t="bool", v=False)
        assert pv_false.v is False

    def test_valid_int(self):
        """Test integer property value."""
        pv = PropertyValue(t="int", v=42)
        assert pv.t == "int"
        assert pv.v == 42

    def test_valid_float(self):
        """Test float property value."""
        pv = PropertyValue(t="float", v=3.14)
        assert pv.t == "float"
        assert pv.v == 3.14

    def test_valid_string(self):
        """Test string property value."""
        pv = PropertyValue(t="string", v="hello")
        assert pv.t == "string"
        assert pv.v == "hello"

    def test_valid_date(self):
        """Test date property value."""
        pv = PropertyValue(t="date", v="2023-01-15")
        assert pv.t == "date"
        assert pv.v == "2023-01-15"

    def test_valid_datetime(self):
        """Test datetime property value."""
        pv = PropertyValue(t="datetime", v="2023-01-15T10:30:00+00:00")
        assert pv.t == "datetime"
        assert pv.v == "2023-01-15T10:30:00+00:00"

    def test_valid_time(self):
        """Test time property value."""
        pv = PropertyValue(t="time", v="10:30:00")
        assert pv.t == "time"
        assert pv.v == "10:30:00"

    def test_valid_duration(self):
        """Test duration property value."""
        pv = PropertyValue(t="duration", v="P1Y2M3DT4H5M6S")
        assert pv.t == "duration"
        assert pv.v == "P1Y2M3DT4H5M6S"

    def test_valid_point_cartesian(self):
        """Test cartesian point property value."""
        pv = PropertyValue(t="point", v={"x": 1.0, "y": 2.0, "crs": "cartesian"})
        assert pv.t == "point"
        assert pv.v["x"] == 1.0
        assert pv.v["y"] == 2.0

    def test_valid_point_geographic(self):
        """Test geographic point property value."""
        pv = PropertyValue(t="point", v={"latitude": 37.7749, "longitude": -122.4194})
        assert pv.t == "point"
        assert pv.v["latitude"] == 37.7749
        assert pv.v["longitude"] == -122.4194

    def test_valid_distance(self):
        """Test distance property value."""
        pv = PropertyValue(t="distance", v=42.5)
        assert pv.t == "distance"
        assert pv.v == 42.5

    def test_valid_list(self):
        """Test list property value."""
        pv = PropertyValue(
            t="list",
            v=[
                {"t": "int", "v": 1},
                {"t": "int", "v": 2},
                {"t": "string", "v": "three"},
            ],
        )
        assert pv.t == "list"
        assert len(pv.v) == 3

    def test_valid_map(self):
        """Test map property value."""
        pv = PropertyValue(
            t="map",
            v={
                "name": {"t": "string", "v": "Alice"},
                "age": {"t": "int", "v": 30},
            },
        )
        assert pv.t == "map"
        assert "name" in pv.v
        assert "age" in pv.v

    def test_invalid_type_tag(self):
        """Test invalid type tag raises error."""
        with pytest.raises(ValidationError, match="Invalid type tag"):
            PropertyValue(t="invalid_type", v="value")

    def test_null_wrong_value(self):
        """Test null with non-null value raises error."""
        with pytest.raises(ValidationError, match="Type 'null' requires value None"):
            PropertyValue(t="null", v="not null")

    def test_bool_wrong_type(self):
        """Test bool with non-boolean value raises error."""
        with pytest.raises(ValidationError, match="Type 'bool' requires boolean value"):
            PropertyValue(t="bool", v="not a bool")

    def test_int_wrong_type(self):
        """Test int with non-integer value raises error."""
        with pytest.raises(ValidationError, match="Type 'int' requires integer value"):
            PropertyValue(t="int", v="not an int")

    def test_int_rejects_bool(self):
        """Test int rejects boolean (which is subclass of int in Python)."""
        with pytest.raises(ValidationError, match="Type 'int' requires integer value"):
            PropertyValue(t="int", v=True)

    def test_float_wrong_type(self):
        """Test float with non-numeric value raises error."""
        with pytest.raises(ValidationError, match="Type 'float' requires numeric value"):
            PropertyValue(t="float", v="not a float")

    def test_string_wrong_type(self):
        """Test string with non-string value raises error."""
        with pytest.raises(ValidationError, match="Type 'string' requires string value"):
            PropertyValue(t="string", v=123)

    def test_date_wrong_type(self):
        """Test date with non-string value raises error."""
        with pytest.raises(ValidationError, match="Type 'date' requires ISO 8601 date string"):
            PropertyValue(t="date", v=123)

    def test_date_invalid_format(self):
        """Test date with invalid format raises error."""
        with pytest.raises(ValidationError, match="Type 'date' requires ISO 8601 format"):
            PropertyValue(t="date", v="not a date")

    def test_datetime_wrong_type(self):
        """Test datetime with non-string value raises error."""
        with pytest.raises(
            ValidationError, match="Type 'datetime' requires ISO 8601 datetime string"
        ):
            PropertyValue(t="datetime", v=123)

    def test_datetime_missing_time_separator(self):
        """Test datetime without T separator raises error."""
        with pytest.raises(ValidationError, match="Type 'datetime' requires ISO 8601 format"):
            PropertyValue(t="datetime", v="2023-01-15 10:30:00")

    def test_time_wrong_type(self):
        """Test time with non-string value raises error."""
        with pytest.raises(ValidationError, match="Type 'time' requires ISO 8601 time string"):
            PropertyValue(t="time", v=123)

    def test_time_invalid_format(self):
        """Test time with invalid format raises error."""
        with pytest.raises(ValidationError, match="Type 'time' requires ISO 8601 format"):
            PropertyValue(t="time", v="not a time")

    def test_duration_wrong_type(self):
        """Test duration with non-string value raises error."""
        with pytest.raises(
            ValidationError, match="Type 'duration' requires ISO 8601 duration string"
        ):
            PropertyValue(t="duration", v=123)

    def test_duration_invalid_format(self):
        """Test duration without P prefix raises error."""
        with pytest.raises(ValidationError, match="Type 'duration' requires ISO 8601 format"):
            PropertyValue(t="duration", v="1Y2M")

    def test_point_wrong_type(self):
        """Test point with non-dict value raises error."""
        with pytest.raises(ValidationError, match="Type 'point' requires coordinate object"):
            PropertyValue(t="point", v="not a point")

    def test_point_missing_coordinates(self):
        """Test point without proper coordinates raises error."""
        with pytest.raises(ValidationError, match=r"Type 'point' requires .* or .*"):
            PropertyValue(t="point", v={"invalid": "coords"})

    def test_distance_wrong_type(self):
        """Test distance with non-numeric value raises error."""
        with pytest.raises(ValidationError, match="Type 'distance' requires numeric value"):
            PropertyValue(t="distance", v="not a distance")

    def test_distance_negative(self):
        """Test negative distance raises error."""
        with pytest.raises(ValidationError, match="Type 'distance' requires non-negative value"):
            PropertyValue(t="distance", v=-1.0)

    def test_list_wrong_type(self):
        """Test list with non-list value raises error."""
        with pytest.raises(ValidationError, match="Type 'list' requires array value"):
            PropertyValue(t="list", v="not a list")

    def test_map_wrong_type(self):
        """Test map with non-dict value raises error."""
        with pytest.raises(ValidationError, match="Type 'map' requires object value"):
            PropertyValue(t="map", v="not a map")

    def test_list_invalid_nested_item_type(self):
        """Test list with non-dict nested item raises error."""
        with pytest.raises(
            ValidationError, match=r"Type 'list' item at index 1 must be PropertyValue object"
        ):
            PropertyValue(
                t="list", v=[{"t": "int", "v": 1}, "not a property value", {"t": "int", "v": 3}]
            )

    def test_list_nested_item_missing_keys(self):
        """Test list with nested item missing 't' or 'v' keys raises error."""
        with pytest.raises(
            ValidationError, match=r"Type 'list' item at index 0 must have 't' and 'v' keys"
        ):
            PropertyValue(t="list", v=[{"v": 42}])

    def test_list_nested_item_invalid_type_tag(self):
        """Test list with nested item having invalid type tag raises error."""
        with pytest.raises(ValidationError, match=r"Type 'list' item at index 1 validation failed"):
            PropertyValue(t="list", v=[{"t": "int", "v": 1}, {"t": "invalid_type", "v": 2}])

    def test_map_invalid_nested_value_type(self):
        """Test map with non-dict nested value raises error."""
        with pytest.raises(
            ValidationError, match=r"Type 'map' value at key 'age' must be PropertyValue object"
        ):
            PropertyValue(
                t="map",
                v={"name": {"t": "string", "v": "Alice"}, "age": 30},  # 30 is not a PropertyValue
            )

    def test_map_nested_value_missing_keys(self):
        """Test map with nested value missing 't' or 'v' keys raises error."""
        with pytest.raises(
            ValidationError, match=r"Type 'map' value at key 'score' must have 't' and 'v' keys"
        ):
            PropertyValue(t="map", v={"score": {"v": 100}})

    def test_map_nested_value_invalid_type_tag(self):
        """Test map with nested value having invalid type tag raises error."""
        with pytest.raises(
            ValidationError, match=r"Type 'map' value at key 'count' validation failed"
        ):
            PropertyValue(
                t="map",
                v={"name": {"t": "string", "v": "Alice"}, "count": {"t": "bad_type", "v": 5}},
            )

    def test_deeply_nested_list_validation(self):
        """Test validation works for deeply nested lists."""
        # Valid deeply nested structure
        valid = PropertyValue(
            t="list",
            v=[
                {"t": "int", "v": 1},
                {"t": "list", "v": [{"t": "string", "v": "nested"}, {"t": "int", "v": 2}]},
            ],
        )
        assert valid.t == "list"

        # Invalid deeply nested structure
        with pytest.raises(ValidationError, match=r"Type 'list' item at index 1 validation failed"):
            PropertyValue(
                t="list",
                v=[
                    {"t": "int", "v": 1},
                    {
                        "t": "list",
                        "v": [{"t": "string", "v": "ok"}, "invalid"],
                    },  # Invalid nested item
                ],
            )

    def test_deeply_nested_map_validation(self):
        """Test validation works for deeply nested maps."""
        # Valid deeply nested structure
        valid = PropertyValue(
            t="map",
            v={
                "simple": {"t": "int", "v": 42},
                "nested": {"t": "map", "v": {"inner": {"t": "string", "v": "value"}}},
            },
        )
        assert valid.t == "map"

        # Invalid deeply nested structure
        with pytest.raises(
            ValidationError, match=r"Type 'map' value at key 'data' validation failed"
        ):
            PropertyValue(
                t="map",
                v={
                    "simple": {"t": "int", "v": 42},
                    "data": {
                        "t": "map",
                        "v": {"bad": 123},
                    },  # Invalid nested value (not PropertyValue)
                },
            )

    def test_immutable(self):
        """Test PropertyValue is immutable."""
        pv = PropertyValue(t="int", v=42)
        with pytest.raises(ValidationError):
            pv.t = "string"  # type: ignore


class TestJSONGraphNode:
    """Tests for JSONGraphNode model."""

    def test_valid_node(self):
        """Test creating a valid node."""
        node = JSONGraphNode(
            id="n0",
            labels=["Person"],
            properties={"name": PropertyValue(t="string", v="Alice")},
        )
        assert node.id == "n0"
        assert node.labels == ["Person"]
        assert "name" in node.properties

    def test_node_without_labels(self):
        """Test node without labels (empty list)."""
        node = JSONGraphNode(id="n0", properties={})
        assert node.labels == []

    def test_node_without_properties(self):
        """Test node without properties (empty dict)."""
        node = JSONGraphNode(id="n0", labels=["Person"])
        assert node.properties == {}

    def test_node_multiple_labels(self):
        """Test node with multiple labels."""
        node = JSONGraphNode(id="n0", labels=["Person", "Customer"])
        assert len(node.labels) == 2

    def test_empty_id(self):
        """Test empty node ID raises error."""
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            JSONGraphNode(id="", labels=[])

    def test_whitespace_id(self):
        """Test whitespace-only node ID raises error."""
        with pytest.raises(ValidationError, match="Node ID cannot be empty"):
            JSONGraphNode(id="   ", labels=[])

    def test_empty_label(self):
        """Test empty label string raises error."""
        with pytest.raises(ValidationError, match="Node labels cannot be empty"):
            JSONGraphNode(id="n0", labels=[""])

    def test_whitespace_label(self):
        """Test whitespace-only label raises error."""
        with pytest.raises(ValidationError, match="Node labels cannot be empty"):
            JSONGraphNode(id="n0", labels=["   "])

    def test_immutable(self):
        """Test JSONGraphNode is immutable."""
        node = JSONGraphNode(id="n0", labels=["Person"])
        with pytest.raises(ValidationError):
            node.id = "n1"  # type: ignore


class TestJSONGraphEdge:
    """Tests for JSONGraphEdge model."""

    def test_valid_edge(self):
        """Test creating a valid edge."""
        edge = JSONGraphEdge(
            id="e0",
            source="n0",
            target="n1",
            type="KNOWS",
            properties={"weight": PropertyValue(t="float", v=0.8)},
        )
        assert edge.id == "e0"
        assert edge.source == "n0"
        assert edge.target == "n1"
        assert edge.type == "KNOWS"
        assert "weight" in edge.properties

    def test_edge_default_type(self):
        """Test edge with default type."""
        edge = JSONGraphEdge(id="e0", source="n0", target="n1")
        assert edge.type == "RELATED_TO"

    def test_edge_without_properties(self):
        """Test edge without properties."""
        edge = JSONGraphEdge(id="e0", source="n0", target="n1", type="KNOWS")
        assert edge.properties == {}

    def test_empty_edge_id(self):
        """Test empty edge ID raises error."""
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            JSONGraphEdge(id="", source="n0", target="n1")

    def test_empty_source(self):
        """Test empty source ID raises error."""
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            JSONGraphEdge(id="e0", source="", target="n1")

    def test_empty_target(self):
        """Test empty target ID raises error."""
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            JSONGraphEdge(id="e0", source="n0", target="")

    def test_empty_type(self):
        """Test empty edge type raises error."""
        with pytest.raises(ValidationError, match="Edge type cannot be empty"):
            JSONGraphEdge(id="e0", source="n0", target="n1", type="")

    def test_immutable(self):
        """Test JSONGraphEdge is immutable."""
        edge = JSONGraphEdge(id="e0", source="n0", target="n1")
        with pytest.raises(ValidationError):
            edge.type = "LOVES"  # type: ignore


class TestJSONGraph:
    """Tests for JSONGraph model."""

    def test_valid_graph(self):
        """Test creating a valid graph."""
        nodes = [
            JSONGraphNode(id="n0", labels=["Person"]),
            JSONGraphNode(id="n1", labels=["Person"]),
        ]
        edges = [
            JSONGraphEdge(id="e0", source="n0", target="n1", type="KNOWS"),
        ]
        graph = JSONGraph(nodes=nodes, edges=edges)
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.directed is True

    def test_empty_graph(self):
        """Test creating an empty graph."""
        graph = JSONGraph()
        assert graph.nodes == []
        assert graph.edges == []
        assert graph.directed is True

    def test_undirected_graph(self):
        """Test creating an undirected graph."""
        nodes = [JSONGraphNode(id="n0"), JSONGraphNode(id="n1")]
        edges = [JSONGraphEdge(id="e0", source="n0", target="n1")]
        graph = JSONGraph(nodes=nodes, edges=edges, directed=False)
        assert graph.directed is False

    def test_graph_with_metadata(self):
        """Test graph with metadata."""
        graph = JSONGraph(metadata={"name": "Test Graph", "version": "1.0"})
        assert graph.metadata["name"] == "Test Graph"
        assert graph.metadata["version"] == "1.0"

    def test_invalid_edge_source_reference(self):
        """Test edge referencing non-existent source node raises error."""
        nodes = [JSONGraphNode(id="n0")]
        edges = [JSONGraphEdge(id="e0", source="n999", target="n0")]
        with pytest.raises(ValidationError, match="references non-existent source node"):
            JSONGraph(nodes=nodes, edges=edges)

    def test_invalid_edge_target_reference(self):
        """Test edge referencing non-existent target node raises error."""
        nodes = [JSONGraphNode(id="n0")]
        edges = [JSONGraphEdge(id="e0", source="n0", target="n999")]
        with pytest.raises(ValidationError, match="references non-existent target node"):
            JSONGraph(nodes=nodes, edges=edges)

    def test_duplicate_node_ids(self):
        """Test duplicate node IDs raise error."""
        nodes = [
            JSONGraphNode(id="n0", labels=["Person"]),
            JSONGraphNode(id="n0", labels=["Customer"]),  # Duplicate ID
        ]
        with pytest.raises(ValidationError, match="Duplicate node IDs found"):
            JSONGraph(nodes=nodes)

    def test_duplicate_edge_ids(self):
        """Test duplicate edge IDs raise error."""
        nodes = [JSONGraphNode(id="n0"), JSONGraphNode(id="n1")]
        edges = [
            JSONGraphEdge(id="e0", source="n0", target="n1"),
            JSONGraphEdge(id="e0", source="n1", target="n0"),  # Duplicate ID
        ]
        with pytest.raises(ValidationError, match="Duplicate edge IDs found"):
            JSONGraph(nodes=nodes, edges=edges)

    def test_self_loop(self):
        """Test self-loop edge is allowed."""
        nodes = [JSONGraphNode(id="n0")]
        edges = [JSONGraphEdge(id="e0", source="n0", target="n0")]
        graph = JSONGraph(nodes=nodes, edges=edges)
        assert len(graph.edges) == 1

    def test_immutable(self):
        """Test JSONGraph is immutable."""
        graph = JSONGraph()
        with pytest.raises(ValidationError):
            graph.directed = False  # type: ignore
