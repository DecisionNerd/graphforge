"""Integration tests for JSON Graph loader."""

import json
from pathlib import Path

import pytest

from graphforge import GraphForge
from graphforge.datasets.loaders.json_graph import JSONGraphLoader
from graphforge.types.values import CypherDate, CypherList, CypherMap


@pytest.mark.integration
class TestJSONGraphLoader:
    """Integration tests for JSONGraphLoader class."""

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
