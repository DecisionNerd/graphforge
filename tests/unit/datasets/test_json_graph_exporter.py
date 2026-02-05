"""Unit tests for JSON Graph exporter."""

import json

from graphforge import GraphForge
from graphforge.datasets.exporters.json_graph import (
    JSONGraphExporter,
    cypher_value_to_property_value,
)
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


class TestJSONGraphExporter:
    """Tests for JSONGraphExporter class."""

    def test_export_empty_graph(self, tmp_path):
        """Test exporting an empty graph."""
        gf = GraphForge()
        exporter = JSONGraphExporter()
        output_file = tmp_path / "empty.json"

        exporter.export(gf, output_file)

        # Load and verify JSON
        with output_file.open("r") as f:
            data = json.load(f)

        assert data["nodes"] == []
        assert data["edges"] == []
        assert data["directed"] is True
        assert data["metadata"] == {}

    def test_export_single_node(self, tmp_path):
        """Test exporting a graph with a single node."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice', age: 30})")

        exporter = JSONGraphExporter()
        output_file = tmp_path / "single_node.json"
        exporter.export(gf, output_file)

        # Load and verify JSON
        with output_file.open("r") as f:
            data = json.load(f)

        assert len(data["nodes"]) == 1
        node = data["nodes"][0]
        assert "Person" in node["labels"]
        assert node["properties"]["name"]["t"] == "string"
        assert node["properties"]["name"]["v"] == "Alice"
        assert node["properties"]["age"]["t"] == "int"
        assert node["properties"]["age"]["v"] == 30

    def test_export_multiple_nodes(self, tmp_path):
        """Test exporting a graph with multiple nodes."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice'})")
        gf.execute("CREATE (n:Person {name: 'Bob'})")
        gf.execute("CREATE (n:Person {name: 'Charlie'})")

        exporter = JSONGraphExporter()
        output_file = tmp_path / "multiple_nodes.json"
        exporter.export(gf, output_file)

        # Load and verify JSON
        with output_file.open("r") as f:
            data = json.load(f)

        assert len(data["nodes"]) == 3

    def test_export_with_edges(self, tmp_path):
        """Test exporting a graph with edges."""
        gf = GraphForge()
        gf.execute(
            "CREATE (a:Person {name: 'Alice'})-[:KNOWS {since: 2020}]->(b:Person {name: 'Bob'})"
        )

        exporter = JSONGraphExporter()
        output_file = tmp_path / "with_edges.json"
        exporter.export(gf, output_file)

        # Load and verify JSON
        with output_file.open("r") as f:
            data = json.load(f)

        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

        edge = data["edges"][0]
        assert edge["type"] == "KNOWS"
        assert edge["properties"]["since"]["t"] == "int"
        assert edge["properties"]["since"]["v"] == 2020

    def test_export_temporal_properties(self, tmp_path):
        """Test exporting nodes with temporal properties."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice', birthday: date('1990-01-15')})")

        exporter = JSONGraphExporter()
        output_file = tmp_path / "temporal.json"
        exporter.export(gf, output_file)

        # Load and verify JSON
        with output_file.open("r") as f:
            data = json.load(f)

        node = data["nodes"][0]
        assert node["properties"]["birthday"]["t"] == "date"
        assert node["properties"]["birthday"]["v"] == "1990-01-15"

    def test_export_spatial_properties(self, tmp_path):
        """Test exporting nodes with spatial properties.

        NOTE: Currently spatial properties export as 'map' instead of 'point'
        due to Issue #97 - the API doesn't support Point types directly.
        When point() is used in Cypher, it creates CypherPoint, but when stored
        via the API it gets converted to CypherMap. This will be fixed in Issue #97.
        """
        gf = GraphForge()
        gf.execute("CREATE (n:Place {name: 'Office', location: point({x: 1.0, y: 2.0})})")

        exporter = JSONGraphExporter()
        output_file = tmp_path / "spatial.json"
        exporter.export(gf, output_file)

        # Load and verify JSON
        with output_file.open("r") as f:
            data = json.load(f)

        node = data["nodes"][0]
        # TODO: Change to "point" once Issue #97 is resolved
        assert node["properties"]["location"]["t"] == "map"
        assert node["properties"]["location"]["v"]["x"]["v"] == 1.0
        assert node["properties"]["location"]["v"]["y"]["v"] == 2.0

    def test_export_with_metadata(self, tmp_path):
        """Test exporting with custom metadata."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice'})")

        exporter = JSONGraphExporter()
        output_file = tmp_path / "with_metadata.json"
        metadata = {"name": "Test Graph", "version": "1.0", "author": "GraphForge"}
        exporter.export(gf, output_file, metadata=metadata)

        # Load and verify JSON
        with output_file.open("r") as f:
            data = json.load(f)

        assert data["metadata"]["name"] == "Test Graph"
        assert data["metadata"]["version"] == "1.0"
        assert data["metadata"]["author"] == "GraphForge"

    def test_export_multiple_labels(self, tmp_path):
        """Test exporting nodes with multiple labels."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person:Customer {name: 'Alice'})")

        exporter = JSONGraphExporter()
        output_file = tmp_path / "multiple_labels.json"
        exporter.export(gf, output_file)

        # Load and verify JSON
        with output_file.open("r") as f:
            data = json.load(f)

        node = data["nodes"][0]
        assert len(node["labels"]) == 2
        assert "Person" in node["labels"]
        assert "Customer" in node["labels"]

    def test_export_complex_graph(self, tmp_path):
        """Test exporting a more complex graph structure."""
        gf = GraphForge()
        # Create nodes (must be separate statements as grammar doesn't support multiple CREATE clauses)
        gf.execute("CREATE (a:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (b:Person {name: 'Bob', age: 25})")
        gf.execute("CREATE (c:Company {name: 'Acme Corp'})")
        # Create relationships
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS {since: 2010}]->(b)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (c:Company) CREATE (a)-[:WORKS_FOR {role: 'Engineer'}]->(c)"
        )
        gf.execute(
            "MATCH (b:Person {name: 'Bob'}), (c:Company) CREATE (b)-[:WORKS_FOR {role: 'Designer'}]->(c)"
        )

        exporter = JSONGraphExporter()
        output_file = tmp_path / "complex.json"
        exporter.export(gf, output_file)

        # Load and verify JSON
        with output_file.open("r") as f:
            data = json.load(f)

        assert len(data["nodes"]) == 3
        assert len(data["edges"]) == 3

        # Verify directed
        assert data["directed"] is True

    def test_json_is_valid_utf8(self, tmp_path):
        """Test exported JSON handles unicode correctly."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: '测试', emoji: '🚀'})")

        exporter = JSONGraphExporter()
        output_file = tmp_path / "unicode.json"
        exporter.export(gf, output_file)

        # Load and verify JSON
        with output_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        node = data["nodes"][0]
        assert node["properties"]["name"]["v"] == "测试"
        assert node["properties"]["emoji"]["v"] == "🚀"
