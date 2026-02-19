"""Unit tests for GraphForge.clone() method.

Tests that clone() creates independent copies of GraphForge instances
while sharing parser/planner/executor infrastructure.
"""

import pytest

from graphforge import GraphForge


@pytest.mark.unit
class TestCloneBasicBehavior:
    """Test that clone() creates independent graph copies."""

    def test_clone_copies_nodes(self):
        """Clone should copy all nodes from the original."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")

        cloned = gf.clone()

        # Both have same node count
        original_count = gf.execute("MATCH (n) RETURN count(n) AS c")[0]["c"].value
        cloned_count = cloned.execute("MATCH (n) RETURN count(n) AS c")[0]["c"].value
        assert original_count == 2
        assert cloned_count == 2

    def test_clone_copies_edges(self):
        """Clone should copy all edges from the original."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})-[:KNOWS]->(:Person {name: 'Bob'})")

        cloned = gf.clone()

        # Both have same edge count
        original_edges = gf.execute("MATCH ()-[r]->() RETURN count(r) AS c")[0][
            "c"
        ].value
        cloned_edges = cloned.execute("MATCH ()-[r]->() RETURN count(r) AS c")[0][
            "c"
        ].value
        assert original_edges == 1
        assert cloned_edges == 1

    def test_clone_copies_properties(self):
        """Clone should copy node and edge properties."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")

        cloned = gf.clone()

        # Properties preserved in clone
        result = cloned.execute("MATCH (n:Person) RETURN n.name AS name, n.age AS age")
        assert result[0]["name"].value == "Alice"
        assert result[0]["age"].value == 30


@pytest.mark.unit
class TestCloneIsolation:
    """Test that cloned instances are independent."""

    def test_mutations_dont_affect_original(self):
        """Changes to clone should not affect original."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")

        cloned = gf.clone()
        cloned.execute("CREATE (:Person {name: 'Bob'})")

        # Original still has 1 node
        original_count = gf.execute("MATCH (n) RETURN count(n) AS c")[0]["c"].value
        assert original_count == 1

        # Clone has 2 nodes
        cloned_count = cloned.execute("MATCH (n) RETURN count(n) AS c")[0]["c"].value
        assert cloned_count == 2

    def test_mutations_dont_affect_clone(self):
        """Changes to original after cloning should not affect clone."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")

        cloned = gf.clone()

        # Modify original
        gf.execute("CREATE (:Person {name: 'Bob'})")

        # Clone still has 1 node
        cloned_count = cloned.execute("MATCH (n) RETURN count(n) AS c")[0]["c"].value
        assert cloned_count == 1

        # Original has 2 nodes
        original_count = gf.execute("MATCH (n) RETURN count(n) AS c")[0]["c"].value
        assert original_count == 2

    def test_clone_empty_graph(self):
        """Cloning an empty graph should work."""
        gf = GraphForge()
        cloned = gf.clone()

        # Both empty
        original_count = gf.execute("MATCH (n) RETURN count(n) AS c")[0]["c"].value
        cloned_count = cloned.execute("MATCH (n) RETURN count(n) AS c")[0]["c"].value
        assert original_count == 0
        assert cloned_count == 0

    def test_multiple_clones_independent(self):
        """Multiple clones should be independent from each other."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")

        clone1 = gf.clone()
        clone2 = gf.clone()

        clone1.execute("CREATE (:Person {name: 'Bob'})")
        clone2.execute("CREATE (:Person {name: 'Charlie'})")

        # Original: 1 node
        assert gf.execute("MATCH (n) RETURN count(n) AS c")[0]["c"].value == 1

        # Clone1: 2 nodes
        assert clone1.execute("MATCH (n) RETURN count(n) AS c")[0]["c"].value == 2

        # Clone2: 2 nodes (different from clone1)
        assert clone2.execute("MATCH (n) RETURN count(n) AS c")[0]["c"].value == 2

        # Verify they have different data
        clone1_names = [
            r["name"].value
            for r in clone1.execute("MATCH (n:Person) RETURN n.name AS name")
        ]
        clone2_names = [
            r["name"].value
            for r in clone2.execute("MATCH (n:Person) RETURN n.name AS name")
        ]
        assert "Bob" in clone1_names
        assert "Bob" not in clone2_names
        assert "Charlie" in clone2_names
        assert "Charlie" not in clone1_names


@pytest.mark.unit
class TestCloneInfrastructure:
    """Test that clone shares parser/planner/executor."""

    def test_clone_shares_parser(self):
        """Clone should share the same parser instance (via global cache)."""
        gf = GraphForge()
        cloned = gf.clone()

        # Both use the globally cached parser
        assert gf.parser._lark is cloned.parser._lark

    def test_clone_independent_graph_object(self):
        """Clone should have a different Graph object."""
        gf = GraphForge()
        cloned = gf.clone()

        # Different Graph instances
        assert gf.graph is not cloned.graph

    def test_clone_works_after_queries(self):
        """Clone should work after running queries on original."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("MATCH (n) RETURN n")  # Run a query

        cloned = gf.clone()

        # Clone has same data
        result = cloned.execute("MATCH (n:Person) RETURN n.name AS name")
        assert result[0]["name"].value == "Alice"


@pytest.mark.unit
class TestCloneIdCounters:
    """Test that clone copies ID counters correctly."""

    def test_clone_copies_next_node_id(self):
        """Clone should copy _next_node_id counter."""
        gf = GraphForge()
        gf.execute("CREATE (:A)")
        gf.execute("CREATE (:B)")

        cloned = gf.clone()

        # Create node in clone - should use next ID
        new_node = cloned.create_node(["C"])
        assert new_node.id == 3

    def test_clone_copies_next_edge_id(self):
        """Clone should copy _next_edge_id counter."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(alice, bob, "KNOWS")

        cloned = gf.clone()

        # Create edge in clone - should use next ID
        charlie = cloned.create_node(["Person"], name="Charlie")
        new_edge = cloned.create_relationship(alice, charlie, "KNOWS")
        assert new_edge.id == 2


@pytest.mark.unit
class TestCloneErrors:
    """Test clone() error conditions."""

    def test_clone_closed_instance_raises(self, tmp_path):
        """clone() should raise RuntimeError if instance is closed."""
        db_path = tmp_path / "test.db"
        gf = GraphForge(str(db_path))
        gf.close()

        with pytest.raises(RuntimeError, match="closed"):
            gf.clone()

    def test_clone_persistent_instance_raises(self, tmp_path):
        """clone() should raise RuntimeError for persistent instances."""
        db_path = tmp_path / "test.db"
        gf = GraphForge(str(db_path))

        with pytest.raises(RuntimeError, match="persistent storage"):
            gf.clone()

        gf.close()
