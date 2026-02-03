"""Integration tests for relationship direction matching.

Tests for incoming, outgoing, and undirected relationship patterns.
"""

import pytest

from graphforge import GraphForge


@pytest.fixture
def graph_with_directed_relationships():
    """Create a graph with various directed relationships."""
    gf = GraphForge()
    gf.execute("""
        CREATE (a:Person {name: 'Alice'}),
               (b:Person {name: 'Bob'}),
               (c:Person {name: 'Charlie'}),
               (a)-[:KNOWS]->(b),
               (b)-[:KNOWS]->(c),
               (c)-[:LIKES]->(a)
    """)
    return gf


class TestRelationshipDirections:
    """Tests for relationship direction patterns."""

    def test_match_incoming_relationships(self, graph_with_directed_relationships):
        """Match incoming relationships with <- arrow."""
        results = graph_with_directed_relationships.execute("""
            MATCH (a)<-[:KNOWS]-(b)
            RETURN a.name AS target, b.name AS source
            ORDER BY target
        """)

        assert len(results) == 2
        # Alice <- Bob and Bob <- Charlie (reversed from creation)
        assert results[0]["target"].value == "Bob"
        assert results[0]["source"].value == "Alice"
        assert results[1]["target"].value == "Charlie"
        assert results[1]["source"].value == "Bob"

    def test_match_outgoing_relationships(self, graph_with_directed_relationships):
        """Match outgoing relationships with -> arrow."""
        results = graph_with_directed_relationships.execute("""
            MATCH (a)-[:KNOWS]->(b)
            RETURN a.name AS source, b.name AS target
            ORDER BY source
        """)

        assert len(results) == 2
        assert results[0]["source"].value == "Alice"
        assert results[0]["target"].value == "Bob"
        assert results[1]["source"].value == "Bob"
        assert results[1]["target"].value == "Charlie"

    def test_match_undirected_relationships(self, graph_with_directed_relationships):
        """Match undirected relationships with - (no arrows)."""
        results = graph_with_directed_relationships.execute("""
            MATCH (a)-[:KNOWS]-(b)
            WHERE a.name = 'Bob'
            RETURN b.name AS other
            ORDER BY other
        """)

        # Bob has KNOWS relationships with both Alice and Charlie
        # (Alice->Bob and Bob->Charlie, so undirected matches both)
        assert len(results) == 2
        names = [r["other"].value for r in results]
        assert set(names) == {"Alice", "Charlie"}

    def test_match_any_relationship_undirected(self, graph_with_directed_relationships):
        """Match any relationship type undirected."""
        results = graph_with_directed_relationships.execute("""
            MATCH (a)-[r]-(b)
            WHERE a.name = 'Alice'
            RETURN b.name AS other, type(r) AS rel_type
            ORDER BY other
        """)

        # Alice has: Alice->Bob (KNOWS) and Charlie->Alice (LIKES)
        assert len(results) == 2
        names = [r["other"].value for r in results]
        assert set(names) == {"Bob", "Charlie"}

    def test_incoming_with_multiple_types(self, graph_with_directed_relationships):
        """Match incoming relationships of specific types."""
        results = graph_with_directed_relationships.execute("""
            MATCH (a)<-[:LIKES]-(b)
            RETURN a.name AS target, b.name AS source
        """)

        # Only Charlie->Alice with LIKES
        assert len(results) == 1
        assert results[0]["target"].value == "Alice"
        assert results[0]["source"].value == "Charlie"

    @pytest.mark.skip(reason="Multi-hop chain patterns not yet supported")
    def test_match_chain_with_directions(self, graph_with_directed_relationships):
        """Match chain of relationships with mixed directions."""
        results = graph_with_directed_relationships.execute("""
            MATCH (a)-[:KNOWS]->(b)-[:KNOWS]->(c)
            RETURN a.name AS first, b.name AS middle, c.name AS last
        """)

        # Alice->Bob->Charlie
        assert len(results) == 1
        assert results[0]["first"].value == "Alice"
        assert results[0]["middle"].value == "Bob"
        assert results[0]["last"].value == "Charlie"

    def test_undirected_finds_both_directions(self):
        """Undirected pattern finds relationships regardless of direction."""
        gf = GraphForge()
        gf.execute("CREATE (a:Node {id: 1})-[:CONNECTED]->(b:Node {id: 2})")

        # Undirected should find it from either side
        results1 = gf.execute("""
            MATCH (a:Node {id: 1})-[:CONNECTED]-(b)
            RETURN b.id AS other_id
        """)
        assert len(results1) == 1
        assert results1[0]["other_id"].value == 2

        results2 = gf.execute("""
            MATCH (a:Node {id: 2})-[:CONNECTED]-(b)
            RETURN b.id AS other_id
        """)
        assert len(results2) == 1
        assert results2[0]["other_id"].value == 1

    def test_incoming_with_no_matches(self, graph_with_directed_relationships):
        """Incoming pattern with no matching relationships."""
        results = graph_with_directed_relationships.execute("""
            MATCH (a)<-[:NONEXISTENT]-(b)
            RETURN a, b
        """)

        assert len(results) == 0

    def test_complex_undirected_pattern(self):
        """Complex undirected pattern matching."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'A'}),
                   (b:Person {name: 'B'}),
                   (c:Person {name: 'C'}),
                   (a)-[:FRIEND]->(b),
                   (b)-[:FRIEND]->(c)
        """)

        # Find all friends of B (both directions)
        results = gf.execute("""
            MATCH (b:Person {name: 'B'})-[:FRIEND]-(other)
            RETURN other.name AS friend
            ORDER BY friend
        """)

        assert len(results) == 2
        friends = [r["friend"].value for r in results]
        assert friends == ["A", "C"]
