"""Integration tests for JSON Graph round-tripping.

These tests verify that data can be exported and imported without loss of type information.
"""

import pytest

from graphforge import GraphForge
from graphforge.datasets.exporters.json_graph import JSONGraphExporter
from graphforge.datasets.loaders.json_graph import JSONGraphLoader


@pytest.mark.integration
class TestJSONGraphRoundtrip:
    """Test round-trip export and import preserves data."""

    def test_roundtrip_primitives(self, tmp_path):
        """Test round-trip with primitive types."""
        # Create graph with various primitive types
        gf1 = GraphForge()
        gf1.execute("""
            CREATE (n:Person {
                name: 'Alice',
                age: 30,
                height: 1.75,
                active: true,
                middle_name: null
            })
        """)

        # Export to JSON
        output_file = tmp_path / "primitives.json"
        exporter = JSONGraphExporter()
        exporter.export(gf1, output_file)

        # Import into new graph
        gf2 = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf2, output_file)

        # Verify data matches
        results = gf2.execute("""
            MATCH (n:Person)
            RETURN n.name AS name, n.age AS age, n.height AS height,
                   n.active AS active, n.middle_name AS middle_name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30
        assert results[0]["height"].value == 1.75
        assert results[0]["active"].value is True
        assert results[0]["middle_name"].value is None

    def test_roundtrip_temporal_types(self, tmp_path):
        """Test round-trip with temporal types."""
        # Create graph with temporal properties
        gf1 = GraphForge()
        gf1.execute("""
            CREATE (n:Person {
                name: 'Alice',
                birthday: date('1990-01-15'),
                registered: datetime('2020-05-10T10:30:00+00:00'),
                preferred_time: time('14:30:00'),
                subscription: duration('P1Y')
            })
        """)

        # Export to JSON
        output_file = tmp_path / "temporal.json"
        exporter = JSONGraphExporter()
        exporter.export(gf1, output_file)

        # Import into new graph
        gf2 = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf2, output_file)

        # Verify temporal data
        results = gf2.execute("""
            MATCH (n:Person)
            RETURN n.birthday AS birthday, n.registered AS registered
        """)

        assert len(results) == 1
        # Date comparison
        birthday = results[0]["birthday"]
        assert birthday.value.year == 1990
        assert birthday.value.month == 1
        assert birthday.value.day == 15

    def test_roundtrip_spatial_types(self, tmp_path):
        """Test round-trip with spatial types."""
        # Create graph with spatial properties
        gf1 = GraphForge()
        gf1.execute("""
            CREATE (n:Place {
                name: 'Office',
                location: point({x: 1.0, y: 2.0})
            })
        """)

        # Export to JSON
        output_file = tmp_path / "spatial.json"
        exporter = JSONGraphExporter()
        exporter.export(gf1, output_file)

        # Import into new graph
        gf2 = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf2, output_file)

        # Verify spatial data
        results = gf2.execute("""
            MATCH (n:Place)
            RETURN n.location AS location
        """)

        assert len(results) == 1
        location = results[0]["location"]
        # NOTE: Due to Issue #97, spatial properties are stored as CypherMap
        # so values are CypherFloat/CypherString, not plain Python types
        assert location.value["x"].value == 1.0
        assert location.value["y"].value == 2.0
        assert location.value["crs"].value == "cartesian"

    def test_roundtrip_with_edges(self, tmp_path):
        """Test round-trip with edges and their properties."""
        # Create graph with edges
        gf1 = GraphForge()
        gf1.execute("CREATE (a:Person {name: 'Alice', age: 30})")
        gf1.execute("CREATE (b:Person {name: 'Bob', age: 25})")
        gf1.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS {since: 2010, strength: 0.8}]->(b)"
        )

        # Export to JSON
        output_file = tmp_path / "with_edges.json"
        exporter = JSONGraphExporter()
        exporter.export(gf1, output_file)

        # Import into new graph
        gf2 = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf2, output_file)

        # Verify nodes
        node_results = gf2.execute("MATCH (n:Person) RETURN count(n) AS count")
        assert node_results[0]["count"].value == 2

        # Verify edges
        edge_results = gf2.execute("""
            MATCH (a:Person)-[r:KNOWS]->(b:Person)
            RETURN a.name AS source, b.name AS target, r.since AS since, r.strength AS strength
        """)

        assert len(edge_results) == 1
        assert edge_results[0]["source"].value == "Alice"
        assert edge_results[0]["target"].value == "Bob"
        assert edge_results[0]["since"].value == 2010
        assert edge_results[0]["strength"].value == 0.8

    def test_roundtrip_multiple_labels(self, tmp_path):
        """Test round-trip preserves multiple labels."""
        # Create node with multiple labels
        gf1 = GraphForge()
        gf1.execute("CREATE (n:Person:Customer:VIP {name: 'Alice'})")

        # Export to JSON
        output_file = tmp_path / "multiple_labels.json"
        exporter = JSONGraphExporter()
        exporter.export(gf1, output_file)

        # Import into new graph
        gf2 = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf2, output_file)

        # Verify labels
        results = gf2.execute("MATCH (n:Person:Customer:VIP) RETURN count(n) AS count")
        assert results[0]["count"].value == 1

    def test_roundtrip_complex_graph(self, tmp_path):
        """Test round-trip with complex graph structure."""
        # Create a more complex graph
        gf1 = GraphForge()
        # Create nodes
        gf1.execute("CREATE (a:Person {name: 'Alice', age: 30, birthday: date('1993-05-15')})")
        gf1.execute("CREATE (b:Person {name: 'Bob', age: 25, birthday: date('1998-03-20')})")
        gf1.execute("CREATE (c:Company {name: 'Acme Corp', founded: date('2000-01-01')})")
        # Use cartesian coordinates instead of geographic to avoid negative number parsing issue
        gf1.execute(
            "CREATE (d:City {name: 'San Francisco', location: point({x: 37.7749, y: 122.4194})})"
        )
        # Create relationships
        gf1.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS {since: 2010, strength: 0.9}]->(b)"
        )
        gf1.execute(
            "MATCH (a:Person {name: 'Alice'}), (c:Company) CREATE (a)-[:WORKS_FOR {role: 'Engineer', start: date('2015-06-01')}]->(c)"
        )
        gf1.execute(
            "MATCH (b:Person {name: 'Bob'}), (c:Company) CREATE (b)-[:WORKS_FOR {role: 'Designer', start: date('2018-03-15')}]->(c)"
        )
        gf1.execute("MATCH (a:Person {name: 'Alice'}), (d:City) CREATE (a)-[:LIVES_IN]->(d)")
        gf1.execute("MATCH (b:Person {name: 'Bob'}), (d:City) CREATE (b)-[:LIVES_IN]->(d)")

        # Export to JSON
        output_file = tmp_path / "complex.json"
        exporter = JSONGraphExporter()
        exporter.export(gf1, output_file, metadata={"name": "Complex Graph", "version": "1.0"})

        # Import into new graph
        gf2 = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf2, output_file)

        # Verify node counts by label
        person_results = gf2.execute("MATCH (n:Person) RETURN count(n) AS count")
        assert person_results[0]["count"].value == 2

        company_results = gf2.execute("MATCH (n:Company) RETURN count(n) AS count")
        assert company_results[0]["count"].value == 1

        city_results = gf2.execute("MATCH (n:City) RETURN count(n) AS count")
        assert city_results[0]["count"].value == 1

        # Verify edge counts by type
        knows_results = gf2.execute("MATCH ()-[r:KNOWS]->() RETURN count(r) AS count")
        assert knows_results[0]["count"].value == 1

        works_for_results = gf2.execute("MATCH ()-[r:WORKS_FOR]->() RETURN count(r) AS count")
        assert works_for_results[0]["count"].value == 2

        lives_in_results = gf2.execute("MATCH ()-[r:LIVES_IN]->() RETURN count(r) AS count")
        assert lives_in_results[0]["count"].value == 2

        # Verify specific data
        alice_results = gf2.execute("""
            MATCH (a:Person {name: 'Alice'})-[:LIVES_IN]->(c:City)
            RETURN c.name AS city, c.location AS location
        """)
        assert alice_results[0]["city"].value == "San Francisco"
        # NOTE: Using cartesian coordinates (x, y) instead of geographic (latitude, longitude)
        # and values are CypherFloat due to Issue #97
        assert alice_results[0]["location"].value["x"].value == 37.7749

    def test_roundtrip_empty_graph(self, tmp_path):
        """Test round-trip with empty graph."""
        # Create empty graph
        gf1 = GraphForge()

        # Export to JSON
        output_file = tmp_path / "empty.json"
        exporter = JSONGraphExporter()
        exporter.export(gf1, output_file)

        # Import into new graph
        gf2 = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf2, output_file)

        # Verify empty
        results = gf2.execute("MATCH (n) RETURN count(n) AS count")
        assert results[0]["count"].value == 0

    def test_roundtrip_preserves_types(self, tmp_path):
        """Test that round-trip preserves exact types (int vs float)."""
        # Create graph with both int and float
        gf1 = GraphForge()
        gf1.execute("""
            CREATE (n:Data {
                int_value: 42,
                float_value: 42.0,
                another_float: 3.14
            })
        """)

        # Export to JSON
        output_file = tmp_path / "types.json"
        exporter = JSONGraphExporter()
        exporter.export(gf1, output_file)

        # Import into new graph
        gf2 = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf2, output_file)

        # Verify types are preserved
        results = gf2.execute("""
            MATCH (n:Data)
            RETURN n.int_value AS int_val, n.float_value AS float_val, n.another_float AS another
        """)

        assert len(results) == 1
        # int should remain int
        from graphforge.types.values import CypherFloat, CypherInt

        assert isinstance(results[0]["int_val"], CypherInt)
        # float should remain float
        assert isinstance(results[0]["float_val"], CypherFloat)
        assert isinstance(results[0]["another"], CypherFloat)

    def test_roundtrip_unicode_strings(self, tmp_path):
        """Test round-trip preserves unicode strings."""
        # Create graph with unicode
        gf1 = GraphForge()
        gf1.execute("""
            CREATE (n:Person {
                name: '测试用户',
                emoji: '🚀🌟',
                arabic: 'مرحبا',
                russian: 'Привет'
            })
        """)

        # Export to JSON
        output_file = tmp_path / "unicode.json"
        exporter = JSONGraphExporter()
        exporter.export(gf1, output_file)

        # Import into new graph
        gf2 = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf2, output_file)

        # Verify unicode preserved
        results = gf2.execute("""
            MATCH (n:Person)
            RETURN n.name AS name, n.emoji AS emoji, n.arabic AS arabic, n.russian AS russian
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "测试用户"
        assert results[0]["emoji"].value == "🚀🌟"
        assert results[0]["arabic"].value == "مرحبا"
        assert results[0]["russian"].value == "Привет"
