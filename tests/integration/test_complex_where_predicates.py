"""Integration tests for complex WHERE predicates.

Tests for multiple AND conditions and complex predicate combinations.
"""

import pytest

from graphforge import GraphForge


@pytest.fixture
def graph_with_people():
    """Create a graph with people for testing predicates."""
    gf = GraphForge()
    gf.execute("""
        CREATE (a:Person {name: 'Alice', age: 30, city: 'NYC'}),
               (b:Person {name: 'Bob', age: 25, city: 'LA'}),
               (c:Person {name: 'Charlie', age: 35, city: 'NYC'}),
               (d:Person {name: 'Dave', age: 28, city: 'SF'})
    """)
    return gf


class TestComplexWherePredicates:
    """Tests for complex WHERE clause predicates."""

    def test_multiple_and_conditions(self, graph_with_people):
        """WHERE with multiple AND conditions."""
        results = graph_with_people.execute("""
            MATCH (p:Person)
            WHERE p.age > 25 AND p.city = 'NYC'
            RETURN p.name AS name
            ORDER BY name
        """)

        assert len(results) == 2
        assert results[0]["name"].value == "Alice"
        assert results[1]["name"].value == "Charlie"

    def test_three_and_conditions(self, graph_with_people):
        """WHERE with three AND conditions."""
        results = graph_with_people.execute("""
            MATCH (p:Person)
            WHERE p.age > 25 AND p.age < 35 AND p.city = 'NYC'
            RETURN p.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_four_and_conditions(self, graph_with_people):
        """WHERE with four AND conditions."""
        results = graph_with_people.execute("""
            MATCH (p:Person)
            WHERE p.age >= 25 AND p.age <= 35 AND p.city = 'NYC' AND p.name <> 'Charlie'
            RETURN p.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_five_and_conditions(self):
        """WHERE with five AND conditions to thoroughly exercise predicate combining."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {name: 'A', val1: 10, val2: 20, val3: 30, val4: 40, val5: 50})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WHERE i.val1 = 10 AND i.val2 = 20 AND i.val3 = 30 AND i.val4 = 40 AND i.val5 = 50
            RETURN i.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "A"

    def test_multiple_predicates_with_or(self, graph_with_people):
        """WHERE with AND and OR combination."""
        results = graph_with_people.execute("""
            MATCH (p:Person)
            WHERE (p.city = 'NYC' OR p.city = 'LA') AND p.age > 25
            RETURN p.name AS name
            ORDER BY name
        """)

        assert len(results) == 2
        assert results[0]["name"].value == "Alice"
        assert results[1]["name"].value == "Charlie"

    def test_complex_nested_predicates(self, graph_with_people):
        """WHERE with complex nested conditions."""
        results = graph_with_people.execute("""
            MATCH (p:Person)
            WHERE p.age > 20 AND p.age < 40 AND (p.city = 'NYC' OR p.city = 'LA')
            RETURN p.name AS name
            ORDER BY name
        """)

        assert len(results) == 3
        names = [r["name"].value for r in results]
        assert names == ["Alice", "Bob", "Charlie"]

    def test_empty_result_with_multiple_predicates(self, graph_with_people):
        """WHERE with multiple AND conditions that match nothing."""
        results = graph_with_people.execute("""
            MATCH (p:Person)
            WHERE p.age > 100 AND p.city = 'NYC' AND p.name = 'Nobody'
            RETURN p.name AS name
        """)

        assert len(results) == 0
