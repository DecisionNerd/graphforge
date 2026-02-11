"""Integration tests for logical operators (NOT, AND, OR).

Tests for NOT operator with basic negation, NULL propagation, and complex expressions.
"""

import pytest

from graphforge import GraphForge
from graphforge.types.values import CypherNull


@pytest.fixture
def simple_graph():
    """Create a simple graph for testing logical operators."""
    gf = GraphForge()

    # Create nodes with various properties
    gf.create_node(["Person"], name="Alice", age=30, active=True)
    gf.create_node(["Person"], name="Bob", age=25, active=False)
    gf.create_node(["Person"], name="Charlie", age=35)  # Missing active

    return gf


@pytest.mark.integration
class TestNotOperator:
    """Tests for NOT operator."""

    def test_not_true_equals_false(self, simple_graph):
        """NOT true returns false."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            WHERE NOT n.active
            RETURN n.name AS name
        """)

        # Alice has active=true, so NOT true = false, filters out
        assert len(results) == 0

    def test_not_false_equals_true(self, simple_graph):
        """NOT false returns true."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Bob'})
            WHERE NOT n.active
            RETURN n.name AS name
        """)

        # Bob has active=false, so NOT false = true, passes filter
        assert len(results) == 1
        assert results[0]["name"].value == "Bob"

    def test_not_with_comparison(self, simple_graph):
        """NOT with comparison expression."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE NOT n.age > 30
            RETURN n.name AS name
        """)

        # NOT (age > 30) means age <= 30
        # Alice: 30 <= 30 (true), Bob: 25 <= 30 (true), Charlie: 35 <= 30 (false)
        assert len(results) == 2
        names = {r["name"].value for r in results}
        assert names == {"Alice", "Bob"}

    def test_not_with_equality(self, simple_graph):
        """NOT with equality comparison."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE NOT n.name = 'Alice'
            RETURN n.name AS name
        """)

        # All except Alice
        assert len(results) == 2
        names = {r["name"].value for r in results}
        assert names == {"Bob", "Charlie"}

    def test_not_null_propagation(self, simple_graph):
        """NOT NULL returns NULL (filters out in WHERE)."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE NOT n.active
            RETURN n.name AS name
        """)

        # Alice: active=true → NOT true = false (filtered out)
        # Bob: active=false → NOT false = true (included)
        # Charlie: active=NULL → NOT NULL = NULL (filtered out by WHERE)
        assert len(results) == 1
        assert results[0]["name"].value == "Bob"

    def test_double_not(self, simple_graph):
        """Double NOT cancels out."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            WHERE NOT NOT n.active
            RETURN n.name AS name
        """)

        # NOT NOT true = NOT false = true
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_not_with_and(self, simple_graph):
        """NOT with AND operator."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE NOT (n.age < 30 AND n.active)
            RETURN n.name AS name
        """)

        # NOT (age < 30 AND active)
        # Alice: NOT (false AND true) = NOT false = true (included)
        # Bob: NOT (true AND false) = NOT false = true (included)
        # Charlie: NOT (false AND NULL) = NOT false = true (included)
        #   With three-valued short-circuit: false AND NULL = false (not NULL)
        assert len(results) == 3
        names = {r["name"].value for r in results}
        assert names == {"Alice", "Bob", "Charlie"}

    def test_not_with_or(self, simple_graph):
        """NOT with OR operator."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE NOT (n.age > 30 OR n.active = false)
            RETURN n.name AS name
        """)

        # NOT (age > 30 OR active = false)
        # Alice: NOT (false OR false) = NOT false = true
        # Bob: NOT (false OR true) = NOT true = false
        # Charlie: NOT (true OR NULL) = NOT NULL = NULL (filtered)
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_not_in_return(self, simple_graph):
        """NOT can be used in RETURN clause."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN NOT n.active AS not_active
        """)

        assert len(results) == 1
        assert results[0]["not_active"].value is False

    def test_not_in_return_with_null(self, simple_graph):
        """NOT in RETURN with NULL value."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Charlie'})
            RETURN NOT n.active AS not_active
        """)

        assert len(results) == 1
        assert isinstance(results[0]["not_active"], CypherNull)
