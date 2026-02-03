"""Integration tests for executor edge cases.

Tests for edge cases in query execution operators.
"""

from graphforge import GraphForge
from graphforge.types.values import CypherNull


class TestExecutorEdgeCases:
    """Tests for executor edge case handling."""

    def test_aggregation_with_no_rows(self):
        """Aggregation on empty result set."""
        gf = GraphForge()
        gf.execute("CREATE (a:Node {value: 1})")

        # Match nothing, then aggregate
        results = gf.execute("""
            MATCH (n:NonExistent)
            RETURN COUNT(n) AS count, SUM(n.value) AS sum
        """)

        # COUNT of empty set is 0, SUM returns NULL
        assert len(results) == 1
        assert results[0]["count"].value == 0

    def test_limit_zero(self):
        """LIMIT 0 returns no rows."""
        gf = GraphForge()
        gf.execute("CREATE (a:Node), (b:Node), (c:Node)")

        results = gf.execute("""
            MATCH (n:Node)
            RETURN n
            LIMIT 0
        """)

        assert len(results) == 0

    def test_skip_beyond_result_size(self):
        """SKIP more rows than exist."""
        gf = GraphForge()
        gf.execute("CREATE (a:Node), (b:Node)")

        results = gf.execute("""
            MATCH (n:Node)
            RETURN n
            SKIP 10
        """)

        assert len(results) == 0

    def test_merge_with_existing_node(self):
        """MERGE finds existing node instead of creating."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})")

        # MERGE should find the existing node
        results = gf.execute("""
            MERGE (p:Person {name: 'Alice'})
            RETURN p.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

        # Verify we still have only one node
        all_results = gf.execute("MATCH (p:Person) RETURN p")
        assert len(all_results) == 1

    def test_merge_creates_new_node(self):
        """MERGE creates node when not found."""
        gf = GraphForge()

        results = gf.execute("""
            MERGE (p:Person {name: 'Bob'})
            RETURN p.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Bob"

    def test_set_property_to_null(self):
        """SET can set property to NULL."""
        gf = GraphForge()
        gf.execute("CREATE (a:Node {value: 42})")

        gf.execute("""
            MATCH (n:Node)
            SET n.value = NULL
        """)

        results = gf.execute("""
            MATCH (n:Node)
            RETURN n.value AS value
        """)

        assert len(results) == 1
        assert isinstance(results[0]["value"], CypherNull)

    def test_where_with_null_property(self):
        """WHERE clause with NULL property comparison."""
        gf = GraphForge()
        gf.execute("CREATE (a:Node {name: 'A'}), (b:Node)")

        # WHERE with NULL comparison (NULL = NULL is NULL, not true)
        results = gf.execute("""
            MATCH (n:Node)
            WHERE n.missing = NULL
            RETURN n.name AS name
        """)

        # NULL comparisons don't match anything
        assert len(results) == 0

    def test_order_by_null_values(self):
        """ORDER BY with NULL values."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Node {name: 'A', value: 3}),
                   (b:Node {name: 'B'}),
                   (c:Node {name: 'C', value: 1})
        """)

        results = gf.execute("""
            MATCH (n:Node)
            RETURN n.name AS name, n.value AS value
            ORDER BY n.value
        """)

        # NULLs typically sort to end
        assert len(results) == 3
        # Verify ordering: non-NULL values first (ascending), then NULL
        assert results[0]["name"].value == "C"
        assert results[0]["value"].value == 1
        assert results[1]["name"].value == "A"
        assert results[1]["value"].value == 3
        assert results[2]["name"].value == "B"
        # B has NULL value, should be at the end
        assert isinstance(results[2]["value"], CypherNull)

    def test_with_clause_filters_rows(self):
        """WITH clause filters and passes rows."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {age: 25}), (b:Person {age: 35})")

        results = gf.execute("""
            MATCH (p:Person)
            WITH p WHERE p.age > 30
            RETURN p.age AS age
        """)

        assert len(results) == 1
        assert results[0]["age"].value == 35

    def test_with_clause_aggregation(self):
        """WITH clause with aggregation."""
        gf = GraphForge()
        gf.execute("CREATE (a:Item {val: 10}), (b:Item {val: 20}), (c:Item {val: 30})")

        results = gf.execute("""
            MATCH (i:Item)
            WITH SUM(i.val) AS total
            RETURN total
        """)

        assert len(results) == 1
        assert results[0]["total"].value == 60

    def test_create_node_with_multiple_labels(self):
        """CREATE node with multiple labels."""
        gf = GraphForge()

        gf.execute("CREATE (a:Person:Employee {name: 'Alice'})")

        results = gf.execute("MATCH (n:Person:Employee) RETURN n.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_match_with_no_pattern(self):
        """MATCH with minimal pattern."""
        gf = GraphForge()
        gf.execute("CREATE (a), (b), (c)")

        results = gf.execute("MATCH (n) RETURN n")
        assert len(results) == 3

    def test_aggregation_with_null_values(self):
        """Aggregation functions with NULL values."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {value: 10}),
                   (b:Item),
                   (c:Item {value: 20})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            RETURN SUM(i.value) AS sum, AVG(i.value) AS avg,
                   MIN(i.value) AS min, MAX(i.value) AS max
        """)

        # Aggregations should skip NULL values
        assert len(results) == 1
        assert results[0]["sum"].value == 30
        assert results[0]["min"].value == 10
        assert results[0]["max"].value == 20
