"""Integration tests for WITH DISTINCT with SKIP and LIMIT.

Tests for WITH DISTINCT combined with pagination modifiers.
"""

import pytest

from graphforge import GraphForge


class TestWithDistinctSkipLimit:
    """Tests for WITH DISTINCT with SKIP/LIMIT."""

    def test_with_distinct_basic(self):
        """Basic WITH DISTINCT functionality."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {city: 'NYC'}),
                   (b:Person {city: 'NYC'}),
                   (c:Person {city: 'LA'}),
                   (d:Person {city: 'LA'}),
                   (e:Person {city: 'SF'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            WITH DISTINCT p.city AS city
            RETURN city
            ORDER BY city
        """)

        # Should get 3 unique cities
        assert len(results) == 3
        cities = [r["city"].value for r in results]
        assert cities == ["LA", "NYC", "SF"]

    def test_with_distinct_and_skip(self):
        """WITH DISTINCT with SKIP."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {val: 1}),
                   (b:Item {val: 1}),
                   (c:Item {val: 2}),
                   (d:Item {val: 2}),
                   (e:Item {val: 3})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH DISTINCT i.val AS value
            ORDER BY value
            SKIP 1
            RETURN value
        """)

        # Should skip first unique value
        assert len(results) == 2
        values = [r["value"].value for r in results]
        assert values == [2, 3]

    def test_with_distinct_and_limit(self):
        """WITH DISTINCT with LIMIT."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {val: 1}),
                   (b:Item {val: 1}),
                   (c:Item {val: 2}),
                   (d:Item {val: 2}),
                   (e:Item {val: 3})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH DISTINCT i.val AS value
            ORDER BY value
            LIMIT 2
            RETURN value
        """)

        # Should get first 2 unique values
        assert len(results) == 2
        values = [r["value"].value for r in results]
        assert values == [1, 2]

    def test_with_distinct_skip_and_limit(self):
        """WITH DISTINCT with both SKIP and LIMIT."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {val: 1}),
                   (b:Item {val: 1}),
                   (c:Item {val: 2}),
                   (d:Item {val: 2}),
                   (e:Item {val: 3}),
                   (f:Item {val: 3}),
                   (g:Item {val: 4})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH DISTINCT i.val AS value
            ORDER BY value
            SKIP 1
            LIMIT 2
            RETURN value
        """)

        # Should skip 1, then take 2
        assert len(results) == 2
        values = [r["value"].value for r in results]
        assert values == [2, 3]

    def test_with_distinct_where_skip_limit(self):
        """WITH DISTINCT with WHERE, SKIP, and LIMIT."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', city: 'NYC', age: 30}),
                   (b:Person {name: 'Bob', city: 'NYC', age: 25}),
                   (c:Person {name: 'Charlie', city: 'LA', age: 35}),
                   (d:Person {name: 'David', city: 'LA', age: 40}),
                   (e:Person {name: 'Eve', city: 'SF', age: 28})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.age > 26
            WITH DISTINCT p.city AS city
            ORDER BY city
            SKIP 1
            LIMIT 1
            RETURN city
        """)

        # Filter to age > 26, get distinct cities, skip 1, take 1
        assert len(results) == 1

    def test_with_order_by_skip(self):
        """WITH with ORDER BY and SKIP (no DISTINCT)."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {val: 1}),
                   (b:Item {val: 2}),
                   (c:Item {val: 3}),
                   (d:Item {val: 4}),
                   (e:Item {val: 5})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH i.val AS value
            ORDER BY value DESC
            SKIP 2
            RETURN value
        """)

        # Should skip first 2 (5, 4) and return (3, 2, 1)
        assert len(results) == 3
        values = [r["value"].value for r in results]
        assert values == [3, 2, 1]

    def test_with_order_by_limit(self):
        """WITH with ORDER BY and LIMIT (no DISTINCT)."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {val: 1}),
                   (b:Item {val: 2}),
                   (c:Item {val: 3}),
                   (d:Item {val: 4}),
                   (e:Item {val: 5})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH i.val AS value
            ORDER BY value DESC
            LIMIT 3
            RETURN value
        """)

        # Should get first 3 (5, 4, 3)
        assert len(results) == 3
        values = [r["value"].value for r in results]
        assert values == [5, 4, 3]

    def test_with_skip_limit_no_order(self):
        """WITH with SKIP and LIMIT but no ORDER BY."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {val: 1}),
                   (b:Item {val: 2}),
                   (c:Item {val: 3}),
                   (d:Item {val: 4}),
                   (e:Item {val: 5})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH i.val AS value
            SKIP 1
            LIMIT 3
            RETURN value
        """)

        # Order undefined, but should skip 1 and take 3
        assert len(results) == 3

    def test_with_where_skip_limit(self):
        """WITH with WHERE, SKIP, and LIMIT."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {val: 1}),
                   (b:Item {val: 2}),
                   (c:Item {val: 3}),
                   (d:Item {val: 4}),
                   (e:Item {val: 5}),
                   (f:Item {val: 6})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH i.val AS value
            WHERE value > 2
            ORDER BY value
            SKIP 1
            LIMIT 2
            RETURN value
        """)

        # Filter to > 2: [3,4,5,6], skip 1: [4,5,6], limit 2: [4,5]
        assert len(results) == 2
        values = [r["value"].value for r in results]
        assert values == [4, 5]
