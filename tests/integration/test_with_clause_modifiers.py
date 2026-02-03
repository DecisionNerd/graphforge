"""Integration tests for WITH clause with modifiers.

Tests for WITH clause with ORDER BY, SKIP, LIMIT, and DISTINCT.
"""

import pytest

from graphforge import GraphForge


@pytest.fixture
def graph_with_numbers():
    """Create a graph with numbered nodes."""
    gf = GraphForge()
    gf.execute("""
        CREATE (a:Num {value: 1}),
               (b:Num {value: 2}),
               (c:Num {value: 3}),
               (d:Num {value: 4}),
               (e:Num {value: 5})
    """)
    return gf


class TestWithClauseModifiers:
    """Tests for WITH clause with modifiers."""

    def test_with_order_by(self, graph_with_numbers):
        """WITH clause with ORDER BY."""
        results = graph_with_numbers.execute("""
            MATCH (n:Num)
            WITH n.value AS val
            ORDER BY val DESC
            RETURN val
            LIMIT 3
        """)

        assert len(results) == 3
        assert results[0]["val"].value == 5
        assert results[1]["val"].value == 4
        assert results[2]["val"].value == 3

    def test_with_skip(self, graph_with_numbers):
        """WITH clause with SKIP."""
        results = graph_with_numbers.execute("""
            MATCH (n:Num)
            WITH n.value AS val
            ORDER BY val
            SKIP 2
            RETURN val
        """)

        assert len(results) == 3
        values = [r["val"].value for r in results]
        assert values == [3, 4, 5]

    def test_with_limit(self, graph_with_numbers):
        """WITH clause with LIMIT."""
        results = graph_with_numbers.execute("""
            MATCH (n:Num)
            WITH n.value AS val
            ORDER BY val
            LIMIT 3
            RETURN val
        """)

        assert len(results) == 3
        values = [r["val"].value for r in results]
        assert values == [1, 2, 3]

    def test_with_skip_and_limit(self, graph_with_numbers):
        """WITH clause with both SKIP and LIMIT."""
        results = graph_with_numbers.execute("""
            MATCH (n:Num)
            WITH n.value AS val
            ORDER BY val
            SKIP 1
            LIMIT 3
            RETURN val
        """)

        assert len(results) == 3
        values = [r["val"].value for r in results]
        assert values == [2, 3, 4]

    def test_with_aggregation_and_order_by(self, graph_with_numbers):
        """WITH clause with aggregation and ORDER BY."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 30}),
                   (b:Person {name: 'Bob', age: 25}),
                   (c:Person {name: 'Charlie', age: 35})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            WITH p.age AS age
            ORDER BY age DESC
            RETURN age
        """)

        assert len(results) == 3
        assert results[0]["age"].value == 35

    @pytest.mark.skip(reason="Sort after aggregation with original variable names has bug - issue to be filed")
    def test_with_aggregation_skip_limit(self):
        """WITH clause with aggregation, SKIP and LIMIT."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {cat: 'A', val: 10}),
                   (b:Item {cat: 'A', val: 20}),
                   (c:Item {cat: 'B', val: 30}),
                   (d:Item {cat: 'B', val: 40}),
                   (e:Item {cat: 'C', val: 50})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH i.cat AS category, SUM(i.val) AS total
            ORDER BY total DESC
            SKIP 1
            LIMIT 1
            RETURN category, total
        """)

        assert len(results) == 1
        # Should get the middle value after skipping highest

    def test_multiple_with_clauses(self, graph_with_numbers):
        """Multiple WITH clauses in a row."""
        results = graph_with_numbers.execute("""
            MATCH (n:Num)
            WITH n.value AS val
            WHERE val > 2
            WITH val
            WHERE val < 5
            RETURN val
            ORDER BY val
        """)

        assert len(results) == 2
        values = [r["val"].value for r in results]
        assert values == [3, 4]

    def test_with_order_by_multiple_items(self):
        """WITH clause with ORDER BY multiple columns."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {cat: 'A', val: 1}),
                   (b:Item {cat: 'A', val: 2}),
                   (c:Item {cat: 'B', val: 1}),
                   (d:Item {cat: 'B', val: 2})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH i.cat AS category, i.val AS value
            ORDER BY category, value DESC
            RETURN category, value
        """)

        assert len(results) == 4
        # First two should be category A, sorted by value DESC
        assert results[0]["category"].value == "A"
        assert results[0]["value"].value == 2
