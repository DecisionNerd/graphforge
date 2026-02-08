"""Integration tests for EXISTS and COUNT subquery expressions."""

import pytest

from graphforge import GraphForge


@pytest.mark.integration
class TestExistsSubquery:
    """Test EXISTS subquery expressions."""

    def test_exists_with_match(self):
        """Test EXISTS returns true when subquery matches."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})-[:KNOWS]->(:Person {name: 'Bob'})")

        results = gf.execute("""
            MATCH (p:Person {name: 'Alice'})
            WHERE EXISTS { MATCH (p)-[:KNOWS]->() }
            RETURN p.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_exists_returns_false_when_no_match(self):
        """Test EXISTS returns false when subquery doesn't match."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")

        results = gf.execute("""
            MATCH (p:Person {name: 'Alice'})
            WHERE EXISTS { MATCH (p)-[:KNOWS]->() }
            RETURN p.name AS name
        """)

        assert len(results) == 0

    def test_exists_with_multiple_patterns(self):
        """Test EXISTS with more complex subquery."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})-[:KNOWS]->(:Person {name: 'Bob', age: 30})")
        gf.execute("CREATE (:Person {name: 'Charlie'})-[:KNOWS]->(:Person {name: 'Dave', age: 25})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE EXISTS { MATCH (p)-[:KNOWS]->(f) WHERE f.age > 28 }
            RETURN p.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_exists_in_return_clause(self):
        """Test EXISTS in RETURN clause."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})-[:KNOWS]->(:Person {name: 'Bob'})")
        gf.execute("CREATE (:Person {name: 'Charlie'})")

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.name AS name, EXISTS { MATCH (p)-[:KNOWS]->() } AS has_friends
        """)

        assert len(results) == 3
        # Sort by name for consistent assertion
        results_sorted = sorted(results, key=lambda r: r["name"].value)

        assert results_sorted[0]["name"].value == "Alice"
        assert results_sorted[0]["has_friends"].value is True

        assert results_sorted[1]["name"].value == "Bob"
        assert results_sorted[1]["has_friends"].value is False

        assert results_sorted[2]["name"].value == "Charlie"
        assert results_sorted[2]["has_friends"].value is False


@pytest.mark.integration
class TestCountSubquery:
    """Test COUNT subquery expressions."""

    def test_count_relationships(self):
        """Test COUNT subquery counts relationships."""
        gf = GraphForge()

        # Use graph-level API to create nodes and relationships directly
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        charlie = gf.create_node(["Person"], name="Charlie")

        # Create relationships
        gf.create_relationship(alice, bob, "KNOWS")
        gf.create_relationship(alice, charlie, "KNOWS")

        results = gf.execute("""
            MATCH (p:Person {name: 'Alice'})
            RETURN p.name AS name, COUNT { MATCH (p)-[:KNOWS]->() } AS friend_count
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["friend_count"].value == 2

    def test_count_zero_when_no_match(self):
        """Test COUNT returns 0 when subquery doesn't match."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person {name: 'Alice'})
            RETURN p.name AS name, COUNT { MATCH (p)-[:KNOWS]->() } AS friend_count
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["friend_count"].value == 0

    def test_count_with_filter(self):
        """Test COUNT subquery with WHERE filter."""
        gf = GraphForge()

        # Use graph-level API
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob", age=30)
        charlie = gf.create_node(["Person"], name="Charlie", age=25)
        dave = gf.create_node(["Person"], name="Dave", age=35)

        # Create relationships
        gf.create_relationship(alice, bob, "KNOWS")
        gf.create_relationship(alice, charlie, "KNOWS")
        gf.create_relationship(alice, dave, "KNOWS")

        results = gf.execute("""
            MATCH (p:Person {name: 'Alice'})
            RETURN p.name AS name, COUNT { MATCH (p)-[:KNOWS]->(f) WHERE f.age > 28 } AS older_friends
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["older_friends"].value == 2

    def test_count_for_multiple_nodes(self):
        """Test COUNT subquery for multiple nodes."""
        gf = GraphForge()

        # Use graph-level API
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        charlie = gf.create_node(["Person"], name="Charlie")
        dave = gf.create_node(["Person"], name="Dave")
        eve = gf.create_node(["Person"], name="Eve")

        # Create relationships
        gf.create_relationship(alice, bob, "KNOWS")
        gf.create_relationship(alice, charlie, "KNOWS")
        gf.create_relationship(dave, eve, "KNOWS")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.name = 'Alice' OR p.name = 'Dave'
            RETURN p.name AS name, COUNT { MATCH (p)-[:KNOWS]->() } AS friend_count
        """)

        assert len(results) == 2
        # Sort by name for consistent assertion
        results_sorted = sorted(results, key=lambda r: r["name"].value)

        assert results_sorted[0]["name"].value == "Alice"
        assert results_sorted[0]["friend_count"].value == 2

        assert results_sorted[1]["name"].value == "Dave"
        assert results_sorted[1]["friend_count"].value == 1


@pytest.mark.integration
class TestSubqueryEdgeCases:
    """Test edge cases for subquery expressions."""

    def test_exists_with_no_nodes(self):
        """Test EXISTS on empty graph."""
        gf = GraphForge()

        results = gf.execute("""
            MATCH (p:Person)
            WHERE EXISTS { MATCH (p)-[:KNOWS]->() }
            RETURN p.name AS name
        """)

        assert len(results) == 0

    def test_count_with_no_nodes(self):
        """Test COUNT on empty graph."""
        gf = GraphForge()

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.name AS name, COUNT { MATCH (p)-[:KNOWS]->() } AS friend_count
        """)

        assert len(results) == 0

    def test_nested_subqueries_not_supported(self):
        """Test that nested subqueries are properly handled."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})-[:KNOWS]->(:Person {name: 'Bob'})")

        # This should work - EXISTS with inner pattern
        results = gf.execute("""
            MATCH (p:Person)
            WHERE EXISTS { MATCH (p)-[:KNOWS]->(f:Person) }
            RETURN p.name AS name
        """)

        assert len(results) == 1

    def test_exists_with_multiple_matches(self):
        """Test EXISTS returns true even with multiple matches."""
        gf = GraphForge()

        # Use graph-level API
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        charlie = gf.create_node(["Person"], name="Charlie")
        dave = gf.create_node(["Person"], name="Dave")

        # Create relationships
        gf.create_relationship(alice, bob, "KNOWS")
        gf.create_relationship(alice, charlie, "KNOWS")
        gf.create_relationship(alice, dave, "KNOWS")

        results = gf.execute("""
            MATCH (p:Person {name: 'Alice'})
            WHERE EXISTS { MATCH (p)-[:KNOWS]->() }
            RETURN p.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_count_in_where_clause(self):
        """Test using COUNT result in WHERE clause."""
        gf = GraphForge()

        # Use graph-level API
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        charlie = gf.create_node(["Person"], name="Charlie")
        dave = gf.create_node(["Person"], name="Dave")
        eve = gf.create_node(["Person"], name="Eve")

        # Create relationships
        gf.create_relationship(alice, bob, "KNOWS")
        gf.create_relationship(alice, charlie, "KNOWS")
        gf.create_relationship(dave, eve, "KNOWS")

        # Filter people who have more than 1 friend
        results = gf.execute("""
            MATCH (p:Person)
            WITH p, COUNT { MATCH (p)-[:KNOWS]->() } AS friend_count
            WHERE friend_count > 1
            RETURN p.name AS name, friend_count
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["friend_count"].value == 2
