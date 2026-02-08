"""Integration tests for UNION and UNION ALL."""

from graphforge import GraphForge


class TestUnionBasic:
    """Test basic UNION functionality."""

    def test_union_two_queries(self):
        """Test UNION combines results from two queries."""
        gf = GraphForge()

        # Create nodes
        gf.execute("CREATE (p:Person {name: 'Alice'})")
        gf.execute("CREATE (c:Company {name: 'Acme Corp'})")

        # UNION should combine and deduplicate
        results = gf.execute("""
            MATCH (p:Person) RETURN p.name AS name
            UNION
            MATCH (c:Company) RETURN c.name AS name
        """)

        assert len(results) == 2
        names = {results[0]["name"].value, results[1]["name"].value}
        assert names == {"Alice", "Acme Corp"}

    def test_union_all_preserves_duplicates(self):
        """Test UNION ALL keeps duplicate rows."""
        gf = GraphForge()

        # Create duplicate data
        gf.execute("CREATE (p:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (p:Person {name: 'Bob', age: 25})")

        # UNION ALL should keep duplicates
        results = gf.execute("""
            MATCH (p:Person) RETURN p.name AS name
            UNION ALL
            MATCH (p:Person) RETURN p.name AS name
        """)

        # Should have 4 results (2 persons x 2 queries)
        assert len(results) == 4
        names = [r["name"].value for r in results]
        assert names.count("Alice") == 2
        assert names.count("Bob") == 2

    def test_union_deduplicates(self):
        """Test UNION removes duplicate rows."""
        gf = GraphForge()

        # Create nodes
        gf.execute("CREATE (p:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (p:Person {name: 'Bob', age: 25})")

        # UNION should deduplicate
        results = gf.execute("""
            MATCH (p:Person) RETURN p.name AS name
            UNION
            MATCH (p:Person) RETURN p.name AS name
        """)

        # Should have 2 results (deduplicated)
        assert len(results) == 2
        names = {results[0]["name"].value, results[1]["name"].value}
        assert names == {"Alice", "Bob"}

    def test_union_three_queries(self):
        """Test UNION works with more than two queries."""
        gf = GraphForge()

        # Create nodes
        gf.execute("CREATE (p:Person {name: 'Alice'})")
        gf.execute("CREATE (c:Company {name: 'Acme'})")
        gf.execute("CREATE (d:Department {name: 'Engineering'})")

        results = gf.execute("""
            MATCH (p:Person) RETURN p.name AS name
            UNION
            MATCH (c:Company) RETURN c.name AS name
            UNION
            MATCH (d:Department) RETURN d.name AS name
        """)

        assert len(results) == 3
        names = {r["name"].value for r in results}
        assert names == {"Alice", "Acme", "Engineering"}


class TestUnionOrdering:
    """Test UNION with ORDER BY and other clauses."""

    def test_union_with_order_by(self):
        """Test ORDER BY applied after UNION."""
        gf = GraphForge()

        gf.execute("CREATE (p:Person {name: 'Charlie', value: 3})")
        gf.execute("CREATE (p:Person {name: 'Alice', value: 1})")
        gf.execute("CREATE (c:Company {name: 'Beta', value: 2})")

        # Note: ORDER BY after UNION needs to be in a WITH clause or subquery
        # For now, test UNION with ORDER BY in each branch
        results = gf.execute("""
            MATCH (p:Person) RETURN p.name AS name, p.value AS value ORDER BY value
            UNION ALL
            MATCH (c:Company) RETURN c.name AS name, c.value AS value ORDER BY value
        """)

        # Should have 3 results
        assert len(results) == 3

    def test_union_with_limit(self):
        """Test LIMIT in UNION branches."""
        gf = GraphForge()

        gf.execute("CREATE (p:Person {name: 'Alice'})")
        gf.execute("CREATE (p:Person {name: 'Bob'})")
        gf.execute("CREATE (p:Person {name: 'Charlie'})")
        gf.execute("CREATE (c:Company {name: 'Acme'})")
        gf.execute("CREATE (c:Company {name: 'Beta'})")

        results = gf.execute("""
            MATCH (p:Person) RETURN p.name AS name ORDER BY name LIMIT 2
            UNION ALL
            MATCH (c:Company) RETURN c.name AS name ORDER BY name LIMIT 1
        """)

        # Should have 3 results (2 persons + 1 company)
        assert len(results) == 3


class TestUnionEdgeCases:
    """Test UNION edge cases."""

    def test_union_empty_result(self):
        """Test UNION when one branch returns empty."""
        gf = GraphForge()

        gf.execute("CREATE (p:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person) RETURN p.name AS name
            UNION
            MATCH (c:Company) RETURN c.name AS name
        """)

        # Should have 1 result (only Person exists)
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_union_both_empty(self):
        """Test UNION when both branches return empty."""
        gf = GraphForge()

        results = gf.execute("""
            MATCH (p:Person) RETURN p.name AS name
            UNION
            MATCH (c:Company) RETURN c.name AS name
        """)

        # Should have 0 results
        assert len(results) == 0

    def test_union_different_value_types(self):
        """Test UNION with same column count but differing value types."""
        gf = GraphForge()

        gf.execute("CREATE (p:Person {name: 'Alice', age: 30})")

        # This should work - both return single column with same name but different types
        results = gf.execute("""
            MATCH (p:Person) RETURN p.name AS name
            UNION
            MATCH (p:Person) RETURN p.age AS name
        """)

        assert len(results) == 2  # 'Alice' and 30 (deduplicated)

    def test_union_mismatched_column_count(self):
        """Test UNION behavior with different numbers of columns.

        Note: Current implementation does not validate column count mismatch.
        This test documents the current behavior (no error raised).
        """
        gf = GraphForge()

        gf.execute("CREATE (p:Person {name: 'Alice', age: 30})")

        # Different column counts - currently allowed but may produce unexpected results
        results = gf.execute("""
            MATCH (p:Person) RETURN p.name AS name
            UNION
            MATCH (p:Person) RETURN p.name AS name, p.age AS age
        """)

        # Current behavior: both branches execute, results merged without validation
        assert len(results) == 2
