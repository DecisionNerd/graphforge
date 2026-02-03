"""Integration tests for aggregation edge cases.

Tests for edge cases in aggregation operations.
"""

import pytest

from graphforge import GraphForge


class TestAggregationEdgeCases:
    """Tests for aggregation edge cases."""

    def test_aggregation_with_empty_result_in_with(self):
        """WITH clause with aggregation over empty result set."""
        gf = GraphForge()
        gf.execute("CREATE (a:Node {value: 1})")

        # Match nothing, then aggregate in WITH
        results = gf.execute("""
            MATCH (n:NonExistent)
            WITH COUNT(n) AS count
            RETURN count
        """)

        # COUNT of empty set is 0
        assert len(results) == 1
        assert results[0]["count"].value == 0

    def test_aggregation_with_empty_result_sum_in_with(self):
        """WITH clause with SUM over empty result set."""
        gf = GraphForge()
        gf.execute("CREATE (a:Node {value: 1})")

        # Match nothing, then aggregate SUM in WITH
        results = gf.execute("""
            MATCH (n:NonExistent)
            WITH SUM(n.value) AS total
            RETURN total
        """)

        # SUM of empty set is NULL
        assert len(results) == 1
        # Result should be NULL/0 depending on Cypher semantics

    def test_multiple_aggregations_with_empty_result_in_with(self):
        """WITH clause with multiple aggregations over empty result."""
        gf = GraphForge()
        gf.execute("CREATE (a:Node {value: 1})")

        # Match nothing, aggregate multiple functions in WITH
        results = gf.execute("""
            MATCH (n:NonExistent)
            WITH COUNT(n) AS count, SUM(n.value) AS sum,
                 AVG(n.value) AS avg
            RETURN count, sum, avg
        """)

        assert len(results) == 1
        assert results[0]["count"].value == 0

    def test_aggregation_after_filter_produces_empty_in_with(self):
        """WITH aggregation when filter produces empty set."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {age: 30}),
                   (b:Person {age: 40})
        """)

        # Filter that matches nothing, then aggregate
        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.age > 100
            WITH COUNT(p) AS count, AVG(p.age) AS avg_age
            RETURN count, avg_age
        """)

        assert len(results) == 1
        assert results[0]["count"].value == 0

    def test_count_star_with_empty_result(self):
        """COUNT(*) over empty result set."""
        gf = GraphForge()
        gf.execute("CREATE (a:Node)")

        results = gf.execute("""
            MATCH (n:NonExistent)
            RETURN COUNT(*) AS count
        """)

        assert len(results) == 1
        assert results[0]["count"].value == 0

    def test_aggregation_with_grouping_and_empty_result(self):
        """Aggregation with GROUP BY over empty result."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {cat: 'A', val: 10})
        """)

        # Match nothing, group and aggregate
        results = gf.execute("""
            MATCH (i:Item)
            WHERE i.cat = 'NonExistent'
            RETURN i.cat AS category, COUNT(i) AS count, SUM(i.val) AS total
        """)

        # Empty grouping returns no rows
        assert len(results) == 0

    def test_min_max_with_empty_result(self):
        """MIN and MAX aggregations over empty result."""
        gf = GraphForge()
        gf.execute("CREATE (a:Node {value: 1})")

        results = gf.execute("""
            MATCH (n:NonExistent)
            RETURN MIN(n.value) AS min_val, MAX(n.value) AS max_val
        """)

        assert len(results) == 1
        # MIN/MAX of empty set should be NULL

    def test_avg_with_empty_result(self):
        """AVG aggregation over empty result set."""
        gf = GraphForge()
        gf.execute("CREATE (a:Node {value: 1})")

        results = gf.execute("""
            MATCH (n:NonExistent)
            RETURN AVG(n.value) AS avg_val
        """)

        assert len(results) == 1
        # AVG of empty set should be NULL

    def test_aggregation_with_all_null_values(self):
        """Aggregation when all values are NULL."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item), (b:Item), (c:Item)
        """)

        results = gf.execute("""
            MATCH (i:Item)
            RETURN SUM(i.missing_prop) AS sum_val,
                   AVG(i.missing_prop) AS avg_val,
                   MIN(i.missing_prop) AS min_val,
                   MAX(i.missing_prop) AS max_val,
                   COUNT(i.missing_prop) AS count_val
        """)

        assert len(results) == 1
        # Aggregations over NULL values:
        # COUNT should be 0 (doesn't count NULLs)
        # Others should be NULL
        assert results[0]["count_val"].value == 0

    def test_mixed_null_and_values_in_aggregation(self):
        """Aggregation with mix of NULL and real values."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {value: 10}),
                   (b:Item {value: 20}),
                   (c:Item)
        """)

        results = gf.execute("""
            MATCH (i:Item)
            RETURN SUM(i.value) AS sum_val,
                   AVG(i.value) AS avg_val,
                   COUNT(i.value) AS count_val,
                   COUNT(i) AS count_all
        """)

        assert len(results) == 1
        # SUM and AVG skip NULL values
        assert results[0]["sum_val"].value == 30
        assert results[0]["avg_val"].value == 15.0
        # COUNT(i.value) counts non-NULL
        assert results[0]["count_val"].value == 2
        # COUNT(i) counts all nodes
        assert results[0]["count_all"].value == 3
