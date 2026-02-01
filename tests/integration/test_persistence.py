"""Integration tests for SQLite persistence.

Tests the ability to save and load graphs from SQLite databases.
"""

from pathlib import Path
import tempfile

from graphforge import GraphForge


class TestBasicPersistence:
    """Tests for basic save/load functionality."""

    def test_save_and_load_empty_graph(self):
        """Save and load an empty graph."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create and save empty graph
            gf = GraphForge(db_path)
            gf.close()

            # Load and verify empty
            gf2 = GraphForge(db_path)
            results = gf2.execute("MATCH (n) RETURN n")
            assert len(results) == 0
            gf2.close()

    def test_save_and_load_nodes(self):
        """Save nodes and reload them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create nodes
            gf = GraphForge(db_path)
            gf.create_node(["Person"], name="Alice", age=30)
            gf.create_node(["Person"], name="Bob", age=25)
            gf.create_node(["Person"], name="Charlie", age=35)
            gf.close()

            # Load in new instance
            gf2 = GraphForge(db_path)
            results = gf2.execute("MATCH (p:Person) RETURN p.name AS name ORDER BY name")
            assert len(results) == 3
            names = [r["name"].value for r in results]
            assert names == ["Alice", "Bob", "Charlie"]
            gf2.close()

    def test_save_and_load_edges(self):
        """Save relationships and reload them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create graph
            gf = GraphForge(db_path)
            alice = gf.create_node(["Person"], name="Alice")
            bob = gf.create_node(["Person"], name="Bob")
            gf.create_relationship(alice, bob, "KNOWS", since=2020)
            gf.close()

            # Load and verify
            gf2 = GraphForge(db_path)
            results = gf2.execute("""
                MATCH (a:Person)-[r:KNOWS]->(b:Person)
                RETURN a.name AS a_name, b.name AS b_name, r.since AS since
            """)
            assert len(results) == 1
            assert results[0]["a_name"].value == "Alice"
            assert results[0]["b_name"].value == "Bob"
            assert results[0]["since"].value == 2020
            gf2.close()

    def test_incremental_additions(self):
        """Add data across multiple sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Session 1: Create Alice
            gf1 = GraphForge(db_path)
            gf1.create_node(["Person"], name="Alice", age=30)
            gf1.close()

            # Session 2: Add Bob
            gf2 = GraphForge(db_path)
            gf2.create_node(["Person"], name="Bob", age=25)
            gf2.close()

            # Session 3: Add Charlie and verify all three
            gf3 = GraphForge(db_path)
            gf3.create_node(["Person"], name="Charlie", age=35)

            results = gf3.execute("MATCH (p:Person) RETURN p.name AS name ORDER BY name")
            assert len(results) == 3
            names = [r["name"].value for r in results]
            assert names == ["Alice", "Bob", "Charlie"]
            gf3.close()


class TestPropertyTypes:
    """Tests for persisting different property types."""

    def test_persist_all_property_types(self):
        """Persist all CypherValue types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create node with all types
            gf = GraphForge(db_path)
            gf.create_node(
                ["Test"],
                string_prop="text",
                int_prop=42,
                float_prop=3.14,
                bool_prop=True,
                null_prop=None,
                list_prop=[1, 2, 3],
                dict_prop={"key": "value"},
            )
            gf.close()

            # Load and verify
            gf2 = GraphForge(db_path)
            results = gf2.execute("MATCH (t:Test) RETURN t")
            node = results[0]["col_0"]

            assert node.properties["string_prop"].value == "text"
            assert node.properties["int_prop"].value == 42
            assert node.properties["float_prop"].value == 3.14
            assert node.properties["bool_prop"].value is True
            assert node.properties["null_prop"].value is None
            assert [v.value for v in node.properties["list_prop"].value] == [1, 2, 3]
            assert node.properties["dict_prop"].value["key"].value == "value"
            gf2.close()

    def test_persist_nested_structures(self):
        """Persist nested lists and dicts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create node with nested data
            gf = GraphForge(db_path)
            gf.create_node(
                ["Test"],
                nested_list=[[1, 2], [3, 4]],
                nested_dict={"outer": {"inner": "value"}},
            )
            gf.close()

            # Load and verify
            gf2 = GraphForge(db_path)
            results = gf2.execute("MATCH (t:Test) RETURN t")
            node = results[0]["col_0"]

            nested_list = node.properties["nested_list"].value
            assert nested_list[0].value[0].value == 1
            assert nested_list[1].value[1].value == 4

            nested_dict = node.properties["nested_dict"].value
            assert nested_dict["outer"].value["inner"].value == "value"
            gf2.close()


class TestMultipleLabels:
    """Tests for persisting nodes with multiple labels."""

    def test_persist_multiple_labels(self):
        """Persist and reload nodes with multiple labels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create node with multiple labels
            gf = GraphForge(db_path)
            gf.create_node(["Person", "Employee", "Manager"], name="Alice")
            gf.close()

            # Load and verify
            gf2 = GraphForge(db_path)
            results = gf2.execute("MATCH (p:Person) RETURN p")
            node = results[0]["col_0"]

            assert "Person" in node.labels
            assert "Employee" in node.labels
            assert "Manager" in node.labels
            assert len(node.labels) == 3
            gf2.close()


class TestIDGeneration:
    """Tests for ID generation across sessions."""

    def test_id_continues_across_sessions(self):
        """IDs should continue incrementing across sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Session 1: Create node with ID 1
            gf1 = GraphForge(db_path)
            node1 = gf1.create_node(["Person"], name="Alice")
            assert node1.id == 1
            gf1.close()

            # Session 2: Next node should be ID 2
            gf2 = GraphForge(db_path)
            node2 = gf2.create_node(["Person"], name="Bob")
            assert node2.id == 2
            gf2.close()

            # Session 3: Next node should be ID 3
            gf3 = GraphForge(db_path)
            node3 = gf3.create_node(["Person"], name="Charlie")
            assert node3.id == 3
            gf3.close()


class TestComplexGraphs:
    """Tests for persisting complex graph structures."""

    def test_social_network_persistence(self):
        """Persist and reload a social network graph."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create social network
            gf = GraphForge(db_path)
            alice = gf.create_node(["Person"], name="Alice", age=30, city="NYC")
            bob = gf.create_node(["Person"], name="Bob", age=25, city="NYC")
            charlie = gf.create_node(["Person"], name="Charlie", age=35, city="LA")

            gf.create_relationship(alice, bob, "KNOWS", since=2015)
            gf.create_relationship(alice, charlie, "KNOWS", since=2018)
            gf.create_relationship(bob, charlie, "KNOWS", since=2020)
            gf.close()

            # Load and query
            gf2 = GraphForge(db_path)

            # Query: Find Alice's friends
            results = gf2.execute("""
                MATCH (alice:Person)-[r:KNOWS]->(friend:Person)
                WHERE alice.name = 'Alice'
                RETURN friend.name AS name
                ORDER BY name
            """)
            assert len(results) == 2
            names = [r["name"].value for r in results]
            assert names == ["Bob", "Charlie"]

            # Query: Count people by city
            results = gf2.execute("""
                MATCH (p:Person)
                RETURN p.city AS city, COUNT(*) AS count
                ORDER BY city
            """)
            assert len(results) == 2
            assert results[0]["city"].value == "LA"
            assert results[0]["count"].value == 1
            assert results[1]["city"].value == "NYC"
            assert results[1]["count"].value == 2

            gf2.close()


class TestInMemoryMode:
    """Tests for in-memory mode (no persistence)."""

    def test_in_memory_mode_no_persistence(self):
        """In-memory graphs should not persist."""
        # Create in-memory graph
        gf1 = GraphForge()  # No path
        gf1.create_node(["Person"], name="Alice")
        # No close() call, just let it go out of scope

        # Create new in-memory graph (should be empty)
        gf2 = GraphForge()
        results = gf2.execute("MATCH (n) RETURN n")
        assert len(results) == 0


class TestErrorCases:
    """Tests for error handling."""

    def test_can_open_same_database_multiple_times(self):
        """Opening the same database multiple times should work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create initial data
            gf1 = GraphForge(db_path)
            gf1.create_node(["Person"], name="Alice")
            gf1.close()

            # Open same database again (after close)
            gf2 = GraphForge(db_path)
            results = gf2.execute("MATCH (p:Person) RETURN p.name AS name")
            assert len(results) == 1
            assert results[0]["name"].value == "Alice"
            gf2.close()

    def test_multiple_close_calls_safe(self):
        """Calling close() multiple times should be safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            gf = GraphForge(db_path)
            gf.create_node(["Person"], name="Alice")
            gf.close()
            gf.close()  # Second close should not error
