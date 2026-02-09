"""Integration tests for size() function."""

import pytest

from graphforge import GraphForge


@pytest.mark.integration
class TestSizeFunction:
    """Test size() function on lists and strings."""

    def test_size_of_node_property_list(self):
        """Test size() on node property that is a list."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice', scores: [90, 85, 95]})")

        results = gf.execute("""
            MATCH (p:Person)
            RETURN size(p.scores) AS num_scores
        """)

        assert len(results) == 1
        assert results[0]["num_scores"].value == 3

    def test_size_in_where_clause(self):
        """Test size() function in WHERE clause filtering."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice', scores: [90, 85, 95]})")
        gf.execute("CREATE (:Person {name: 'Bob', scores: [70, 65]})")
        gf.execute("CREATE (:Person {name: 'Carol', scores: [88]})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE size(p.scores) > 2
            RETURN p.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_size_of_string_property(self):
        """Test size() on string property."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person)
            RETURN size(p.name) AS name_length
        """)

        assert len(results) == 1
        assert results[0]["name_length"].value == 5
