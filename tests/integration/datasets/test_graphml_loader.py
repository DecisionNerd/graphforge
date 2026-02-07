"""Integration tests for GraphML loader.

Tests end-to-end loading of GraphML datasets into GraphForge, querying, and validation.
"""

import gzip
from pathlib import Path
import time

import pytest

from graphforge import GraphForge
from graphforge.datasets.loaders.graphml import GraphMLLoader


@pytest.mark.integration
class TestGraphMLLoaderIntegration:
    """Integration tests for GraphML loader end-to-end workflows."""

    def test_load_simple_graph_and_query(self, tmp_path: Path):
        """Test loading a simple GraphML file and querying the data."""
        # Create a simple GraphML file
        graphml_path = tmp_path / "simple.graphml"
        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="label" attr.type="string"/>
  <key id="d1" for="node" attr.name="name" attr.type="string"/>
  <key id="d2" for="node" attr.name="age" attr.type="int"/>
  <key id="d3" for="edge" attr.name="weight" attr.type="double"/>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d0">Person</data>
      <data key="d1">Alice</data>
      <data key="d2">30</data>
    </node>
    <node id="n1">
      <data key="d0">Person</data>
      <data key="d1">Bob</data>
      <data key="d2">25</data>
    </node>
    <edge source="n0" target="n1">
      <data key="d3">0.8</data>
    </edge>
  </graph>
</graphml>"""
        graphml_path.write_text(graphml_content)

        # Load into GraphForge
        gf = GraphForge()
        loader = GraphMLLoader()
        loader.load(gf, graphml_path)

        # Query nodes
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name, p.age AS age ORDER BY p.age")
        assert len(results) == 2
        assert results[0]["name"].value == "Bob"
        assert results[0]["age"].value == 25
        assert results[1]["name"].value == "Alice"
        assert results[1]["age"].value == 30

        # Query edges
        results = gf.execute(
            "MATCH (a:Person)-[r:RELATED_TO]->(b:Person) "
            "RETURN a.name AS from, b.name AS to, r.weight AS weight"
        )
        assert len(results) == 1
        assert results[0]["from"].value == "Alice"
        assert results[0]["to"].value == "Bob"
        assert results[0]["weight"].value == 0.8

    def test_load_with_multi_labels_and_query(self, tmp_path: Path):
        """Test loading nodes with comma-separated multi-labels."""
        graphml_path = tmp_path / "multi_labels.graphml"
        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="label" attr.type="string"/>
  <key id="d1" for="node" attr.name="name" attr.type="string"/>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d0">Person,Customer</data>
      <data key="d1">Alice</data>
    </node>
    <node id="n1">
      <data key="d0">Person,Employee</data>
      <data key="d1">Bob</data>
    </node>
  </graph>
</graphml>"""
        graphml_path.write_text(graphml_content)

        # Load and query
        gf = GraphForge()
        loader = GraphMLLoader()
        loader.load(gf, graphml_path)

        # Query by first label
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name ORDER BY p.name")
        assert len(results) == 2

        # Query by second label (Customer)
        results = gf.execute("MATCH (c:Customer) RETURN c.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

        # Query by second label (Employee)
        results = gf.execute("MATCH (e:Employee) RETURN e.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Bob"

    def test_load_with_custom_label_key(self, tmp_path: Path):
        """Test loading with custom label key configuration."""
        graphml_path = tmp_path / "custom_label.graphml"
        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="type" attr.type="string"/>
  <key id="d1" for="node" attr.name="name" attr.type="string"/>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d0">Entity</data>
      <data key="d1">Alice</data>
    </node>
  </graph>
</graphml>"""
        graphml_path.write_text(graphml_content)

        # Load with custom label key
        gf = GraphForge()
        loader = GraphMLLoader(label_key="type", default_label="Unknown")
        loader.load(gf, graphml_path)

        # Query with extracted label
        results = gf.execute("MATCH (e:Entity) RETURN e.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_load_with_default_label(self, tmp_path: Path):
        """Test that nodes without labels use default label."""
        graphml_path = tmp_path / "no_labels.graphml"
        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="name" attr.type="string"/>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d0">Alice</data>
    </node>
  </graph>
</graphml>"""
        graphml_path.write_text(graphml_content)

        # Load with default label
        gf = GraphForge()
        loader = GraphMLLoader(default_label="Entity")
        loader.load(gf, graphml_path)

        # Query with default label
        results = gf.execute("MATCH (e:Entity) RETURN e.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_load_compressed_graphml_gz(self, tmp_path: Path):
        """Test loading compressed .graphml.gz files."""
        graphml_gz_path = tmp_path / "compressed.graphml.gz"
        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="label" attr.type="string"/>
  <key id="d1" for="node" attr.name="name" attr.type="string"/>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d0">Person</data>
      <data key="d1">Alice</data>
    </node>
    <node id="n1">
      <data key="d0">Person</data>
      <data key="d1">Bob</data>
    </node>
    <edge source="n0" target="n1"/>
  </graph>
</graphml>"""

        # Write compressed file
        with gzip.open(graphml_gz_path, "wt", encoding="utf-8") as f:
            f.write(graphml_content)

        # Load compressed file
        gf = GraphForge()
        loader = GraphMLLoader()
        loader.load(gf, graphml_gz_path)

        # Verify data loaded correctly
        results = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert results[0]["count"].value == 2

        results = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert results[0]["count"].value == 1

    def test_load_with_all_property_types(self, tmp_path: Path):
        """Test loading all GraphML property types and querying them."""
        graphml_path = tmp_path / "all_types.graphml"
        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="label" attr.type="string"/>
  <key id="d1" for="node" attr.name="name" attr.type="string"/>
  <key id="d2" for="node" attr.name="age" attr.type="int"/>
  <key id="d3" for="node" attr.name="score" attr.type="double"/>
  <key id="d4" for="node" attr.name="active" attr.type="boolean"/>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d0">Person</data>
      <data key="d1">Alice</data>
      <data key="d2">30</data>
      <data key="d3">95.5</data>
      <data key="d4">true</data>
    </node>
  </graph>
</graphml>"""
        graphml_path.write_text(graphml_content)

        # Load and query
        gf = GraphForge()
        loader = GraphMLLoader()
        loader.load(gf, graphml_path)

        results = gf.execute(
            "MATCH (p:Person) "
            "RETURN p.name AS name, p.age AS age, p.score AS score, p.active AS active"
        )
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30
        assert results[0]["score"].value == 95.5
        assert results[0]["active"].value is True

    def test_load_with_default_values(self, tmp_path: Path):
        """Test that default values from key declarations are applied."""
        graphml_path = tmp_path / "defaults.graphml"
        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="label" attr.type="string">
    <default>Person</default>
  </key>
  <key id="d1" for="node" attr.name="name" attr.type="string"/>
  <key id="d2" for="node" attr.name="status" attr.type="string">
    <default>active</default>
  </key>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d1">Alice</data>
    </node>
  </graph>
</graphml>"""
        graphml_path.write_text(graphml_content)

        # Load and query
        gf = GraphForge()
        loader = GraphMLLoader()
        loader.load(gf, graphml_path)

        # Check label default was applied
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name, p.status AS status")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["status"].value == "active"

    def test_load_and_persist_to_sqlite(self, tmp_path: Path):
        """Test loading GraphML and persisting to SQLite backend."""
        graphml_path = tmp_path / "persist.graphml"
        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="label" attr.type="string"/>
  <key id="d1" for="node" attr.name="name" attr.type="string"/>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d0">Person</data>
      <data key="d1">Alice</data>
    </node>
    <node id="n1">
      <data key="d0">Person</data>
      <data key="d1">Bob</data>
    </node>
    <edge source="n0" target="n1"/>
  </graph>
</graphml>"""
        graphml_path.write_text(graphml_content)

        db_path = tmp_path / "graph.db"

        # Load into persistent GraphForge
        gf = GraphForge(str(db_path))
        loader = GraphMLLoader()
        loader.load(gf, graphml_path)
        gf.close()

        # Reopen and verify data persisted
        gf2 = GraphForge(str(db_path))
        results = gf2.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert results[0]["count"].value == 2

        results = gf2.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert results[0]["count"].value == 1
        gf2.close()

    def test_load_large_graph_performance(self, tmp_path: Path):
        """Test performance benchmark for loading larger GraphML files."""
        # Create a GraphML file with 1000 nodes and 2000 edges
        graphml_path = tmp_path / "large.graphml"

        nodes_xml = []
        for i in range(1000):
            nodes_xml.append(f"""    <node id="n{i}">
      <data key="d0">Node</data>
      <data key="d1">node_{i}</data>
      <data key="d2">{i}</data>
    </node>""")

        edges_xml = []
        for i in range(2000):
            source = i % 1000
            target = (i + 1) % 1000
            edges_xml.append(f'    <edge source="n{source}" target="n{target}"/>')

        graphml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="d0" for="node" attr.name="label" attr.type="string"/>
  <key id="d1" for="node" attr.name="name" attr.type="string"/>
  <key id="d2" for="node" attr.name="index" attr.type="int"/>

  <graph edgedefault="directed">
{chr(10).join(nodes_xml)}
{chr(10).join(edges_xml)}
  </graph>
</graphml>"""
        graphml_path.write_text(graphml_content)

        # Load and time it
        gf = GraphForge()
        loader = GraphMLLoader()

        start_time = time.time()
        loader.load(gf, graphml_path)
        load_time = time.time() - start_time

        # Verify counts
        results = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert results[0]["count"].value == 1000

        results = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert results[0]["count"].value == 2000

        # Performance check: should load 1000 nodes + 2000 edges quickly
        # File is ~150KB, should be well under 5s
        assert load_time < 5.0, f"Load took {load_time:.2f}s, expected <5s"

    def test_load_with_namespace_and_query(self, tmp_path: Path):
        """Test loading GraphML with namespace and querying data."""
        graphml_path = tmp_path / "with_namespace.graphml"
        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns
           http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  <key id="d0" for="node" attr.name="label" attr.type="string"/>
  <key id="d1" for="node" attr.name="name" attr.type="string"/>

  <graph edgedefault="directed">
    <node id="n0">
      <data key="d0">Person</data>
      <data key="d1">Alice</data>
    </node>
    <node id="n1">
      <data key="d0">Person</data>
      <data key="d1">Bob</data>
    </node>
    <edge source="n0" target="n1"/>
  </graph>
</graphml>"""
        graphml_path.write_text(graphml_content)

        # Load and query
        gf = GraphForge()
        loader = GraphMLLoader()
        loader.load(gf, graphml_path)

        results = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert results[0]["count"].value == 2

    def test_empty_graph_loads_successfully(self, tmp_path: Path):
        """Test that empty GraphML files load without errors."""
        graphml_path = tmp_path / "empty.graphml"
        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph edgedefault="directed">
  </graph>
</graphml>"""
        graphml_path.write_text(graphml_content)

        # Load empty graph
        gf = GraphForge()
        loader = GraphMLLoader()
        loader.load(gf, graphml_path)

        # Verify counts are zero
        results = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert results[0]["count"].value == 0

        results = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert results[0]["count"].value == 0
