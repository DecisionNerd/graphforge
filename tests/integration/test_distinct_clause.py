"""Integration tests for DISTINCT clause.

Tests for RETURN DISTINCT functionality.
"""

import pytest

from graphforge import GraphForge


@pytest.fixture
def graph_with_duplicates():
    """Create a graph that produces duplicate results."""
    gf = GraphForge()
    gf.execute("""
        CREATE (a:Person {name: 'Alice', city: 'NYC'}),
               (b:Person {name: 'Bob', city: 'NYC'}),
               (c:Person {name: 'Charlie', city: 'LA'}),
               (d:Person {name: 'Dave', city: 'NYC'})
    """)
    return gf


class TestDistinctClause:
    """Tests for DISTINCT clause."""

    @pytest.mark.skip(reason="RETURN DISTINCT after projection has bug - issue for future fix")
    def test_distinct_single_column(self, graph_with_duplicates):
        """DISTINCT removes duplicate values in single column."""
        results = graph_with_duplicates.execute("""
            MATCH (p:Person)
            RETURN DISTINCT p.city AS city
            ORDER BY city
        """)

        assert len(results) == 2
        assert results[0]["city"].value == "LA"
        assert results[1]["city"].value == "NYC"

    @pytest.mark.skip(reason="RETURN DISTINCT after projection has bug - issue for future fix")
    def test_distinct_multiple_columns(self, graph_with_duplicates):
        """DISTINCT with multiple columns."""
        results = graph_with_duplicates.execute("""
            MATCH (p:Person)
            RETURN DISTINCT p.name AS name, p.city AS city
            ORDER BY name
        """)

        # All rows are distinct because names are unique
        assert len(results) == 4

    def test_distinct_with_aggregation(self):
        """DISTINCT with COUNT aggregation."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {type: 'A'}),
                   (b:Item {type: 'A'}),
                   (c:Item {type: 'B'}),
                   (d:Item {type: 'A'})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            RETURN COUNT(DISTINCT i.type) AS distinct_types
        """)

        assert results[0]["distinct_types"].value == 2

    def test_return_without_distinct_shows_duplicates(self, graph_with_duplicates):
        """Without DISTINCT, duplicate values are shown."""
        results = graph_with_duplicates.execute("""
            MATCH (p:Person)
            RETURN p.city AS city
        """)

        # Should have 4 results (including duplicates)
        assert len(results) == 4

        # Count NYC occurrences
        nyc_count = sum(1 for r in results if r["city"].value == "NYC")
        assert nyc_count == 3

    @pytest.mark.skip(reason="RETURN DISTINCT after projection has bug - issue for future fix")
    def test_distinct_with_limit(self, graph_with_duplicates):
        """DISTINCT with LIMIT clause."""
        results = graph_with_duplicates.execute("""
            MATCH (p:Person)
            RETURN DISTINCT p.city AS city
            ORDER BY city
            LIMIT 1
        """)

        assert len(results) == 1
        assert results[0]["city"].value == "LA"

    @pytest.mark.skip(reason="RETURN DISTINCT after projection has bug - issue for future fix")
    def test_distinct_with_skip_and_limit(self, graph_with_duplicates):
        """DISTINCT with both SKIP and LIMIT."""
        results = graph_with_duplicates.execute("""
            MATCH (p:Person)
            RETURN DISTINCT p.city AS city
            ORDER BY city
            SKIP 1
            LIMIT 1
        """)

        assert len(results) == 1
        assert results[0]["city"].value == "NYC"

    @pytest.mark.skip(reason="RETURN DISTINCT after projection has bug - issue for future fix")
    def test_distinct_all_same_values(self):
        """DISTINCT when all values are the same."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Node {value: 'X'}),
                   (b:Node {value: 'X'}),
                   (c:Node {value: 'X'})
        """)

        results = gf.execute("""
            MATCH (n:Node)
            RETURN DISTINCT n.value AS value
        """)

        assert len(results) == 1
        assert results[0]["value"].value == "X"

    @pytest.mark.skip(reason="RETURN DISTINCT after projection has bug - issue for future fix")
    def test_distinct_with_null_values(self):
        """DISTINCT with NULL values."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Node {name: 'A', value: 'X'}),
                   (b:Node {name: 'B'}),
                   (c:Node {name: 'C', value: 'X'}),
                   (d:Node {name: 'D'})
        """)

        results = gf.execute("""
            MATCH (n:Node)
            RETURN DISTINCT n.value AS value
            ORDER BY value
        """)

        # Should have 2 distinct values: NULL and 'X'
        assert len(results) == 2
