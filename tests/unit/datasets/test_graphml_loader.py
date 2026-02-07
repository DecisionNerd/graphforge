"""Unit tests for GraphML loader.

Tests the GraphMLLoader implementation for parsing NetworkRepository and other
GraphML-format datasets.
"""

import gzip
from pathlib import Path

import pytest

from graphforge import GraphForge
from graphforge.datasets.loaders.graphml import GraphMLLoader


@pytest.mark.unit
class TestGraphMLLoaderBasics:
    """Test basic GraphML loading functionality."""

    def test_get_format(self):
        """Test format identifier."""
        loader = GraphMLLoader()
        assert loader.get_format() == "graphml"

    def test_load_nonexistent_file_raises_error(self):
        """Test that loading non-existent file raises FileNotFoundError."""
        loader = GraphMLLoader()
        gf = GraphForge()

        with pytest.raises(FileNotFoundError, match="GraphML file not found"):
            loader.load(gf, Path("/nonexistent/file.graphml"))

    def test_load_invalid_xml_raises_error(self, tmp_path):
        """Test that invalid XML raises ValueError."""
        loader = GraphMLLoader()
        gf = GraphForge()

        # Create invalid XML file
        graphml_file = tmp_path / "invalid.graphml"
        graphml_file.write_text("<graphml><node>unclosed")

        with pytest.raises(ValueError, match="Invalid GraphML XML"):
            loader.load(gf, graphml_file)

    def test_load_empty_graphml(self, tmp_path):
        """Test loading empty GraphML (no nodes or edges)."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <graph edgedefault="directed">
    </graph>
</graphml>"""

        graphml_file = tmp_path / "empty.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        # Verify no nodes or edges loaded
        results = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert results[0]["count"].value == 0

    def test_load_no_graph_element_raises_error(self, tmp_path):
        """Test that missing <graph> element raises ValueError."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
</graphml>"""

        graphml_file = tmp_path / "no_graph.graphml"
        graphml_file.write_text(graphml_content)

        with pytest.raises(ValueError, match="No <graph> element found"):
            loader.load(gf, graphml_file)


@pytest.mark.unit
class TestGraphMLNodeParsing:
    """Test node parsing from GraphML."""

    def test_load_single_node_no_properties(self, tmp_path):
        """Test loading a single node without properties."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <graph edgedefault="directed">
        <node id="n0"/>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "single_node.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert results[0]["count"].value == 1

    def test_load_multiple_nodes(self, tmp_path):
        """Test loading multiple nodes."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <graph edgedefault="directed">
        <node id="n0"/>
        <node id="n1"/>
        <node id="n2"/>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "multi_nodes.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert results[0]["count"].value == 3

    def test_duplicate_node_id_raises_error(self, tmp_path):
        """Test that duplicate node IDs raise ValueError."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <graph edgedefault="directed">
        <node id="n0"/>
        <node id="n0"/>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "duplicate_nodes.graphml"
        graphml_file.write_text(graphml_content)

        with pytest.raises(ValueError, match="Duplicate node ID"):
            loader.load(gf, graphml_file)


@pytest.mark.unit
class TestGraphMLEdgeParsing:
    """Test edge parsing from GraphML."""

    def test_load_single_edge(self, tmp_path):
        """Test loading a single edge."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <graph edgedefault="directed">
        <node id="n0"/>
        <node id="n1"/>
        <edge source="n0" target="n1"/>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "single_edge.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert results[0]["count"].value == 1

    def test_edge_with_invalid_source_raises_error(self, tmp_path):
        """Test that edge with invalid source node raises ValueError."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <graph edgedefault="directed">
        <node id="n1"/>
        <edge source="n0" target="n1"/>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "invalid_source.graphml"
        graphml_file.write_text(graphml_content)

        with pytest.raises(ValueError, match="Edge references non-existent source node"):
            loader.load(gf, graphml_file)

    def test_edge_with_invalid_target_raises_error(self, tmp_path):
        """Test that edge with invalid target node raises ValueError."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <graph edgedefault="directed">
        <node id="n0"/>
        <edge source="n0" target="n1"/>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "invalid_target.graphml"
        graphml_file.write_text(graphml_content)

        with pytest.raises(ValueError, match="Edge references non-existent target node"):
            loader.load(gf, graphml_file)


@pytest.mark.unit
class TestGraphMLPropertyParsing:
    """Test property parsing with types."""

    def test_parse_string_property(self, tmp_path):
        """Test parsing string properties."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="node" attr.name="name" attr.type="string"/>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">Alice</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "string_prop.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n) RETURN n.name AS name")
        assert results[0]["name"].value == "Alice"

    def test_parse_int_property(self, tmp_path):
        """Test parsing integer properties."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="node" attr.name="age" attr.type="int"/>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">30</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "int_prop.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n) RETURN n.age AS age")
        assert results[0]["age"].value == 30
        assert isinstance(results[0]["age"].value, int)

    def test_parse_long_property(self, tmp_path):
        """Test parsing long properties (treated as int)."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="node" attr.name="id" attr.type="long"/>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">1234567890</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "long_prop.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n) RETURN n.id AS id")
        assert results[0]["id"].value == 1234567890

    def test_parse_float_property(self, tmp_path):
        """Test parsing float properties."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="node" attr.name="weight" attr.type="float"/>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">3.14</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "float_prop.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n) RETURN n.weight AS weight")
        assert results[0]["weight"].value == 3.14
        assert isinstance(results[0]["weight"].value, float)

    def test_parse_double_property(self, tmp_path):
        """Test parsing double properties (treated as float)."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="node" attr.name="value" attr.type="double"/>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">2.71828</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "double_prop.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n) RETURN n.value AS value")
        assert abs(results[0]["value"].value - 2.71828) < 0.0001

    def test_parse_boolean_property_true_false(self, tmp_path):
        """Test parsing boolean properties with true/false."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="node" attr.name="active" attr.type="boolean"/>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">true</data>
        </node>
        <node id="n1">
            <data key="d0">false</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "bool_prop.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n) RETURN n.active AS active ORDER BY id(n)")
        assert results[0]["active"].value is True
        assert results[1]["active"].value is False

    def test_parse_boolean_property_1_0(self, tmp_path):
        """Test parsing boolean properties with 1/0."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="node" attr.name="flag" attr.type="boolean"/>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">1</data>
        </node>
        <node id="n1">
            <data key="d0">0</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "bool_10.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n) RETURN n.flag AS flag ORDER BY id(n)")
        assert results[0]["flag"].value is True
        assert results[1]["flag"].value is False

    def test_parse_default_property_value(self, tmp_path):
        """Test that default values from key declarations are used."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="node" attr.name="status" attr.type="string">
        <default>active</default>
    </key>
    <graph edgedefault="directed">
        <node id="n0"/>
        <node id="n1">
            <data key="d0">inactive</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "default_value.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n) RETURN n.status AS status ORDER BY id(n)")
        assert results[0]["status"].value == "active"  # default
        assert results[1]["status"].value == "inactive"  # explicit

    def test_parse_multiple_properties(self, tmp_path):
        """Test parsing multiple properties on a node."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="node" attr.name="name" attr.type="string"/>
    <key id="d1" for="node" attr.name="age" attr.type="int"/>
    <key id="d2" for="node" attr.name="score" attr.type="float"/>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">Alice</data>
            <data key="d1">30</data>
            <data key="d2">95.5</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "multi_props.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n) RETURN n.name AS name, n.age AS age, n.score AS score")
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30
        assert results[0]["score"].value == 95.5

    def test_undefined_key_raises_error(self, tmp_path):
        """Test that data referencing undefined key raises ValueError."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">value</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "undefined_key.graphml"
        graphml_file.write_text(graphml_content)

        with pytest.raises(ValueError, match="Data references undefined key"):
            loader.load(gf, graphml_file)


@pytest.mark.unit
class TestGraphMLLabelExtraction:
    """Test label extraction from properties."""

    def test_default_label(self, tmp_path):
        """Test that default label is used when no label property."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <graph edgedefault="directed">
        <node id="n0"/>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "default_label.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n:Node) RETURN count(n) AS count")
        assert results[0]["count"].value == 1

    def test_custom_default_label(self, tmp_path):
        """Test custom default label."""
        loader = GraphMLLoader(default_label="Entity")
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <graph edgedefault="directed">
        <node id="n0"/>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "custom_default.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n:Entity) RETURN count(n) AS count")
        assert results[0]["count"].value == 1

    def test_single_label(self, tmp_path):
        """Test extracting single label from property."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="node" attr.name="label" attr.type="string"/>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">Person</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "single_label.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n:Person) RETURN count(n) AS count")
        assert results[0]["count"].value == 1

    def test_multi_label_comma_separated(self, tmp_path):
        """Test extracting multiple labels from comma-separated string."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="node" attr.name="label" attr.type="string"/>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">Person,Customer</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "multi_label.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        # Check both labels exist
        results = gf.execute("MATCH (n:Person:Customer) RETURN count(n) AS count")
        assert results[0]["count"].value == 1

    def test_label_with_spaces_trimmed(self, tmp_path):
        """Test that labels with spaces are trimmed."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="node" attr.name="label" attr.type="string"/>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">Person , Customer , Employee</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "label_spaces.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n:Person:Customer:Employee) RETURN count(n) AS count")
        assert results[0]["count"].value == 1

    def test_custom_label_key(self, tmp_path):
        """Test using custom label key."""
        loader = GraphMLLoader(label_key="type")
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="node" attr.name="type" attr.type="string"/>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">Account</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "custom_key.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (n:Account) RETURN count(n) AS count")
        assert results[0]["count"].value == 1

    def test_label_property_removed_after_extraction(self, tmp_path):
        """Test that label property is removed after extraction."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="node" attr.name="label" attr.type="string"/>
    <key id="d1" for="node" attr.name="name" attr.type="string"/>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">Person</data>
            <data key="d1">Alice</data>
        </node>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "label_removed.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        # Check node has name but not label property
        results = gf.execute("MATCH (n) RETURN n.name AS name, n.label AS label")
        assert results[0]["name"].value == "Alice"
        assert results[0]["label"].type.value == "NULL"


@pytest.mark.unit
class TestGraphMLCompression:
    """Test support for compressed GraphML files."""

    def test_load_gzipped_file(self, tmp_path):
        """Test loading .graphml.gz files."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <graph edgedefault="directed">
        <node id="n0"/>
        <node id="n1"/>
        <edge source="n0" target="n1"/>
    </graph>
</graphml>"""

        # Write gzipped file
        graphml_file = tmp_path / "compressed.graphml.gz"
        with gzip.open(graphml_file, "wt", encoding="utf-8") as f:
            f.write(graphml_content)

        loader.load(gf, graphml_file)

        # Verify loaded correctly
        node_results = gf.execute("MATCH (n) RETURN count(n) AS count")
        edge_results = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert node_results[0]["count"].value == 2
        assert edge_results[0]["count"].value == 1


@pytest.mark.unit
class TestGraphMLNamespace:
    """Test GraphML with XML namespaces."""

    def test_load_with_namespace(self, tmp_path):
        """Test loading GraphML with explicit namespace."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
    <graph edgedefault="directed">
        <node id="n0"/>
        <node id="n1"/>
        <edge source="n0" target="n1"/>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "namespace.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        node_results = gf.execute("MATCH (n) RETURN count(n) AS count")
        edge_results = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert node_results[0]["count"].value == 2
        assert edge_results[0]["count"].value == 1


@pytest.mark.unit
class TestGraphMLEdgeCases:
    """Test edge cases and error handling."""

    def test_nested_graph_raises_error(self, tmp_path):
        """Test that nested graphs raise ValueError."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <graph edgedefault="directed">
        <node id="n0"/>
        <graph id="g1">
            <node id="n1"/>
        </graph>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "nested.graphml"
        graphml_file.write_text(graphml_content)

        with pytest.raises(ValueError, match="Nested graphs are not supported"):
            loader.load(gf, graphml_file)

    def test_edge_properties(self, tmp_path):
        """Test parsing properties on edges."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="edge" attr.name="weight" attr.type="float"/>
    <graph edgedefault="directed">
        <node id="n0"/>
        <node id="n1"/>
        <edge source="n0" target="n1">
            <data key="d0">0.8</data>
        </edge>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "edge_props.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH ()-[r]->() RETURN r.weight AS weight")
        assert results[0]["weight"].value == 0.8

    def test_key_for_all_applies_to_both(self, tmp_path):
        """Test that keys with for='all' apply to both nodes and edges."""
        loader = GraphMLLoader()
        gf = GraphForge()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml>
    <key id="d0" for="all" attr.name="id" attr.type="string"/>
    <graph edgedefault="directed">
        <node id="n0">
            <data key="d0">node1</data>
        </node>
        <node id="n1">
            <data key="d0">node2</data>
        </node>
        <edge source="n0" target="n1">
            <data key="d0">edge1</data>
        </edge>
    </graph>
</graphml>"""

        graphml_file = tmp_path / "for_all.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        node_results = gf.execute("MATCH (n) RETURN n.id AS id ORDER BY n.id")
        assert node_results[0]["id"].value == "node1"
        assert node_results[1]["id"].value == "node2"

        edge_results = gf.execute("MATCH ()-[r]->() RETURN r.id AS id")
        assert edge_results[0]["id"].value == "edge1"


@pytest.mark.unit
class TestGraphMLEmptyDefaultValues:
    """Test that empty string default values are preserved."""

    def test_empty_string_default_preserved(self, tmp_path: Path):
        """Test that empty string default values are not skipped."""
        gf = GraphForge()
        loader = GraphMLLoader()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="label" attr.type="string"/>
  <key id="d1" for="node" attr.name="name" attr.type="string">
    <default></default>
  </key>
  <key id="d2" for="node" attr.name="status" attr.type="string">
    <default>active</default>
  </key>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d0">Person</data>
    </node>
  </graph>
</graphml>"""

        graphml_file = tmp_path / "empty_default.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        results = gf.execute("MATCH (p:Person) RETURN p.name AS name, p.status AS status")
        assert len(results) == 1
        # Empty string default should be preserved
        assert results[0]["name"].value == ""
        # Non-empty default should work
        assert results[0]["status"].value == "active"


@pytest.mark.unit
class TestGraphMLErrorHandling:
    """Test error handling and error messages in type conversion."""

    def test_invalid_int_conversion_error_message(self, tmp_path: Path):
        """Test that invalid int values produce descriptive error messages."""
        gf = GraphForge()
        loader = GraphMLLoader()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="label" attr.type="string"/>
  <key id="d1" for="node" attr.name="age" attr.type="int"/>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d0">Person</data>
      <data key="d1">not_a_number</data>
    </node>
  </graph>
</graphml>"""

        graphml_file = tmp_path / "invalid_int.graphml"
        graphml_file.write_text(graphml_content)

        with pytest.raises(ValueError, match=r"Failed to convert value 'not_a_number'"):
            loader.load(gf, graphml_file)

        with pytest.raises(ValueError, match=r"to type 'int'"):
            loader.load(gf, graphml_file)

        with pytest.raises(ValueError, match=r"for key 'd1'"):
            loader.load(gf, graphml_file)

        with pytest.raises(ValueError, match=r"property 'age'"):
            loader.load(gf, graphml_file)

    def test_invalid_float_conversion_error_message(self, tmp_path: Path):
        """Test that invalid float values produce descriptive error messages."""
        gf = GraphForge()
        loader = GraphMLLoader()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="label" attr.type="string"/>
  <key id="d1" for="node" attr.name="score" attr.type="double"/>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d0">Person</data>
      <data key="d1">invalid_float</data>
    </node>
  </graph>
</graphml>"""

        graphml_file = tmp_path / "invalid_float.graphml"
        graphml_file.write_text(graphml_content)

        with pytest.raises(ValueError, match=r"Failed to convert value 'invalid_float'"):
            loader.load(gf, graphml_file)

        with pytest.raises(ValueError, match=r"to type 'double'"):
            loader.load(gf, graphml_file)

    def test_invalid_default_value_error_message(self, tmp_path: Path):
        """Test that invalid default values produce descriptive error messages."""
        gf = GraphForge()
        loader = GraphMLLoader()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="label" attr.type="string"/>
  <key id="d1" for="node" attr.name="count" attr.type="int">
    <default>not_an_int</default>
  </key>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d0">Person</data>
    </node>
  </graph>
</graphml>"""

        graphml_file = tmp_path / "invalid_default.graphml"
        graphml_file.write_text(graphml_content)

        with pytest.raises(ValueError, match=r"Failed to convert value 'not_an_int'"):
            loader.load(gf, graphml_file)

        with pytest.raises(ValueError, match=r"for key 'd1'"):
            loader.load(gf, graphml_file)


@pytest.mark.unit
class TestGraphMLUndirectedGraphs:
    """Test undirected graph support."""

    def test_directed_graph_creates_single_edge(self, tmp_path: Path):
        """Test that directed graphs create a single directed edge."""
        gf = GraphForge()
        loader = GraphMLLoader()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="label" attr.type="string"/>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d0">Person</data>
    </node>
    <node id="n1">
      <data key="d0">Person</data>
    </node>
    <edge source="n0" target="n1"/>
  </graph>
</graphml>"""

        graphml_file = tmp_path / "directed.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        # Should have 2 nodes
        node_results = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert node_results[0]["count"].value == 2

        # Should have 1 edge (n0 -> n1)
        edge_results = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert edge_results[0]["count"].value == 1

    def test_undirected_graph_creates_reciprocal_edges(self, tmp_path: Path):
        """Test that undirected graphs create reciprocal edges."""
        gf = GraphForge()
        loader = GraphMLLoader()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="label" attr.type="string"/>

  <graph edgedefault="undirected">
    <node id="n0">
      <data key="d0">Person</data>
    </node>
    <node id="n1">
      <data key="d0">Person</data>
    </node>
    <edge source="n0" target="n1"/>
  </graph>
</graphml>"""

        graphml_file = tmp_path / "undirected.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        # Should have 2 nodes
        node_results = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert node_results[0]["count"].value == 2

        # Should have 2 edges (n0 -> n1 and n1 -> n0)
        edge_results = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert edge_results[0]["count"].value == 2

        # Verify both directions exist
        forward = gf.execute(
            """MATCH (n0)-[r]->(n1)
               WHERE id(n0) < id(n1)
               RETURN count(r) AS count"""
        )
        assert forward[0]["count"].value == 1

        backward = gf.execute(
            """MATCH (n0)<-[r]-(n1)
               WHERE id(n0) < id(n1)
               RETURN count(r) AS count"""
        )
        assert backward[0]["count"].value == 1

    def test_undirected_graph_with_properties(self, tmp_path: Path):
        """Test that undirected graphs preserve edge properties on both edges."""
        gf = GraphForge()
        loader = GraphMLLoader()

        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="label" attr.type="string"/>
  <key id="d1" for="edge" attr.name="weight" attr.type="double"/>

  <graph edgedefault="undirected">
    <node id="n0">
      <data key="d0">Person</data>
    </node>
    <node id="n1">
      <data key="d0">Person</data>
    </node>
    <edge source="n0" target="n1">
      <data key="d1">0.8</data>
    </edge>
  </graph>
</graphml>"""

        graphml_file = tmp_path / "undirected_props.graphml"
        graphml_file.write_text(graphml_content)

        loader.load(gf, graphml_file)

        # Both edges should have the weight property
        edge_results = gf.execute("MATCH ()-[r]->() RETURN r.weight AS weight")
        assert len(edge_results) == 2
        assert edge_results[0]["weight"].value == 0.8
        assert edge_results[1]["weight"].value == 0.8


@pytest.mark.unit
class TestGraphMLLoaderRegistration:
    """Test that GraphML loader is properly registered."""

    def test_graphml_loader_registered(self):
        """Test that GraphML loader is registered in the global registry."""
        from graphforge.datasets.registry import _LOADER_REGISTRY

        assert "graphml" in _LOADER_REGISTRY
        assert _LOADER_REGISTRY["graphml"] == GraphMLLoader
