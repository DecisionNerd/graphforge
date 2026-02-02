"""Integration tests for DETACH DELETE clause.

Tests for deleting nodes with relationships using DETACH DELETE.
"""

import pytest

from graphforge import GraphForge


@pytest.fixture
def graph_with_relationships():
    """Create a graph with nodes and relationships for testing."""
    gf = GraphForge()

    # Create nodes with relationships in one go
    # Alice -> Bob -> Charlie -> Alice (cycle)
    gf.execute("""
        CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'}),
               (b)-[:KNOWS]->(c:Person {name: 'Charlie'}),
               (c)-[:KNOWS]->(a)
    """)

    return gf


@pytest.mark.integration
class TestDetachDelete:
    """Tests for DETACH DELETE functionality."""

    def test_delete_without_detach_fails_when_node_has_relationships(
        self, graph_with_relationships
    ):
        """DELETE without DETACH should fail if node has relationships."""
        with pytest.raises(ValueError, match="Cannot delete node with relationships"):
            graph_with_relationships.execute("""
                MATCH (a:Person {name: 'Alice'})
                DELETE a
            """)

    def test_detach_delete_node_with_outgoing_edges(self, graph_with_relationships):
        """DETACH DELETE removes node and its outgoing relationships."""
        # Alice has outgoing edge to Bob
        graph_with_relationships.execute("""
            MATCH (a:Person {name: 'Alice'})
            DETACH DELETE a
        """)

        # Alice should be gone
        results = graph_with_relationships.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN n
        """)
        assert len(results) == 0

        # Alice->Bob and Charlie->Alice relationships should be gone
        # Only Bob->Charlie should remain
        results = graph_with_relationships.execute("""
            MATCH ()-[r:KNOWS]->()
            RETURN r
        """)
        assert len(results) == 1

        # Bob should still exist
        results = graph_with_relationships.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN n
        """)
        assert len(results) == 1

    def test_detach_delete_node_with_incoming_edges(self, graph_with_relationships):
        """DETACH DELETE removes node and its incoming relationships."""
        # Bob has incoming edge from Alice
        graph_with_relationships.execute("""
            MATCH (b:Person {name: 'Bob'})
            DETACH DELETE b
        """)

        # Bob should be gone
        results = graph_with_relationships.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN n
        """)
        assert len(results) == 0

        # Relationship from Alice should be gone
        results = graph_with_relationships.execute("""
            MATCH (a:Person {name: 'Alice'})-[r:KNOWS]->()
            RETURN r
        """)
        assert len(results) == 0

        # Alice should still exist
        results = graph_with_relationships.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN n
        """)
        assert len(results) == 1

    def test_detach_delete_node_with_bidirectional_edges(self, graph_with_relationships):
        """DETACH DELETE removes node with both incoming and outgoing relationships."""
        # Bob has both incoming (from Alice) and outgoing (to Charlie) edges
        graph_with_relationships.execute("""
            MATCH (b:Person {name: 'Bob'})
            DETACH DELETE b
        """)

        # Bob should be gone
        results = graph_with_relationships.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN n
        """)
        assert len(results) == 0

        # Both relationships involving Bob should be gone
        results = graph_with_relationships.execute("""
            MATCH ()-[r:KNOWS]->()
            RETURN r
        """)
        # Only Charlie->Alice relationship should remain
        assert len(results) == 1

        # Alice and Charlie should still exist
        results = graph_with_relationships.execute("""
            MATCH (n:Person)
            RETURN n.name AS name
            ORDER BY name
        """)
        assert len(results) == 2
        names = {r["name"].value for r in results}
        assert names == {"Alice", "Charlie"}

    def test_detach_delete_multiple_nodes(self, graph_with_relationships):
        """DETACH DELETE can delete multiple nodes with relationships."""
        graph_with_relationships.execute("""
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            DETACH DELETE a, b
        """)

        # Only Charlie should remain
        results = graph_with_relationships.execute("""
            MATCH (n:Person)
            RETURN n.name AS name
        """)
        assert len(results) == 1
        assert results[0]["name"].value == "Charlie"

        # No relationships should remain
        results = graph_with_relationships.execute("""
            MATCH ()-[r]->()
            RETURN r
        """)
        assert len(results) == 0

    def test_delete_node_without_relationships_works(self, graph_with_relationships):
        """DELETE without DETACH works fine if node has no relationships."""
        # Create isolated node
        graph_with_relationships.execute("CREATE (d:Person {name: 'David'})")

        # Delete should work without DETACH
        graph_with_relationships.execute("""
            MATCH (d:Person {name: 'David'})
            DELETE d
        """)

        # David should be gone
        results = graph_with_relationships.execute("""
            MATCH (n:Person {name: 'David'})
            RETURN n
        """)
        assert len(results) == 0

    def test_delete_relationship_does_not_require_detach(self, graph_with_relationships):
        """DELETE can delete relationships without DETACH keyword."""
        graph_with_relationships.execute("""
            MATCH (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person {name: 'Bob'})
            DELETE r
        """)

        # Relationship should be gone
        results = graph_with_relationships.execute("""
            MATCH (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person {name: 'Bob'})
            RETURN r
        """)
        assert len(results) == 0

        # Nodes should still exist
        results = graph_with_relationships.execute("""
            MATCH (n:Person)
            WHERE n.name = 'Alice' OR n.name = 'Bob'
            RETURN n.name AS name
            ORDER BY name
        """)
        assert len(results) == 2

    def test_detach_delete_preserves_other_nodes(self, graph_with_relationships):
        """DETACH DELETE only affects specified node and its relationships."""
        # Count nodes and edges before
        nodes_before = graph_with_relationships.execute("MATCH (n) RETURN COUNT(n) AS count")
        edges_before = graph_with_relationships.execute("MATCH ()-[r]->() RETURN COUNT(r) AS count")

        assert nodes_before[0]["count"].value == 3
        assert edges_before[0]["count"].value == 3

        # Delete Alice
        graph_with_relationships.execute("""
            MATCH (a:Person {name: 'Alice'})
            DETACH DELETE a
        """)

        # Should have 2 nodes left
        nodes_after = graph_with_relationships.execute("MATCH (n) RETURN COUNT(n) AS count")
        assert nodes_after[0]["count"].value == 2

        # Alice had 1 outgoing and 1 incoming edge, should have 1 edge left (Bob->Charlie)
        edges_after = graph_with_relationships.execute("MATCH ()-[r]->() RETURN COUNT(r) AS count")
        assert edges_after[0]["count"].value == 1

    def test_delete_multiple_nodes_mixed_with_without_relationships(self):
        """DELETE multiple nodes where some have relationships should fail."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})")
        gf.execute("CREATE (c:Person {name: 'Charlie'})")  # Isolated node

        # Try to delete both - should fail because Alice has relationships
        with pytest.raises(ValueError, match="Cannot delete node with relationships"):
            gf.execute("""
                MATCH (n:Person)
                WHERE n.name = 'Alice' OR n.name = 'Charlie'
                DELETE n
            """)

    def test_detach_delete_with_self_loop(self):
        """DETACH DELETE works with self-referencing relationships."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})-[:LIKES]->(a)")

        # Delete node with self-loop
        gf.execute("""
            MATCH (a:Person {name: 'Alice'})
            DETACH DELETE a
        """)

        # Node should be gone
        results = gf.execute("MATCH (n) RETURN n")
        assert len(results) == 0

        # Relationship should be gone
        results = gf.execute("MATCH ()-[r]->() RETURN r")
        assert len(results) == 0

    def test_delete_nonexistent_variable_is_noop(self):
        """DELETE on non-existent variable is a no-op."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})")

        # Try to delete non-matching node
        gf.execute("MATCH (n:Person) WHERE n.name = 'Bob' DELETE n")

        # Alice should still exist
        results = gf.execute("MATCH (n:Person) RETURN n")
        assert len(results) == 1
