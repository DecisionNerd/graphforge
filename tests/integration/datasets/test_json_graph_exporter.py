"""Integration tests for JSON Graph exporter."""

import json

import pytest

from graphforge import GraphForge
from graphforge.datasets.exporters.json_graph import JSONGraphExporter


@pytest.mark.integration
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
