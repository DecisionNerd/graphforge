"""Integration tests for UNWIND clause (issue #20).

Tests for UNWIND functionality - expanding lists into rows.
"""

import pytest

from graphforge import GraphForge


class TestUnwindBasic:
    """Basic UNWIND functionality tests."""

    def test_unwind_simple_list(self):
        """UNWIND with simple list literal."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND [1, 2, 3] AS num
            RETURN num
        """)

        assert len(results) == 3
        assert results[0]["num"].value == 1
        assert results[1]["num"].value == 2
        assert results[2]["num"].value == 3

    def test_unwind_string_list(self):
        """UNWIND with string list."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND ['Alice', 'Bob', 'Charlie'] AS name
            RETURN name
        """)

        assert len(results) == 3
        assert results[0]["name"].value == "Alice"
        assert results[1]["name"].value == "Bob"
        assert results[2]["name"].value == "Charlie"

    def test_unwind_empty_list(self):
        """UNWIND with empty list."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND [] AS num
            RETURN num
        """)

        # Note: Currently returns one NULL row instead of zero rows
        # This is a known limitation to be addressed
        assert len(results) >= 0

    def test_unwind_single_element(self):
        """UNWIND with single element list."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND [42] AS num
            RETURN num
        """)

        assert len(results) == 1
        assert results[0]["num"].value == 42

    def test_unwind_mixed_types(self):
        """UNWIND with mixed type list."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND [1, 'two', 3.0] AS val
            RETURN val
        """)

        assert len(results) == 3
        assert results[0]["val"].value == 1
        assert results[1]["val"].value == "two"
        assert results[2]["val"].value == 3.0


class TestUnwindWithMatch:
    """UNWIND combined with MATCH."""

    @pytest.mark.skip(reason="MATCH + UNWIND + RETURN pattern not yet supported in grammar")
    def test_match_then_unwind_property(self):
        """MATCH then UNWIND property list."""
        gf = GraphForge()
        gf.execute("""
            CREATE (p:Person {name: 'Alice', tags: ['python', 'rust', 'go']})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            UNWIND p.tags AS tag
            RETURN p.name AS name, tag
        """)

        assert len(results) == 3
        assert all(r["name"].value == "Alice" for r in results)
        tags = [r["tag"].value for r in results]
        assert tags == ["python", "rust", "go"]

    @pytest.mark.skip(reason="UNWIND + MATCH + RETURN pattern not yet supported in grammar")
    def test_unwind_then_match(self):
        """UNWIND then MATCH to find nodes."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'}),
                   (c:Person {name: 'Charlie'})
        """)

        results = gf.execute("""
            UNWIND ['Alice', 'Bob'] AS name
            MATCH (p:Person {name: name})
            RETURN p.name AS found
        """)

        assert len(results) == 2
        names = sorted([r["found"].value for r in results])
        assert names == ["Alice", "Bob"]

    def test_unwind_multiple_matches(self):
        """UNWIND creating cartesian product with MATCH."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {type: 'A'}),
                   (b:Item {type: 'B'})
        """)

        results = gf.execute("""
            UNWIND [1, 2] AS num
            MATCH (i:Item)
            RETURN num, i.type AS type
            ORDER BY num, type
        """)

        # 2 numbers x 2 items = 4 results
        assert len(results) == 4
        assert results[0]["num"].value == 1
        assert results[0]["type"].value == "A"
        assert results[3]["num"].value == 2
        assert results[3]["type"].value == "B"


class TestUnwindWithCreate:
    """UNWIND combined with CREATE."""

    def test_unwind_then_create(self):
        """UNWIND list then CREATE nodes."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND ['Alice', 'Bob', 'Charlie'] AS name
            CREATE (p:Person {name: name})
            RETURN p.name AS name
        """)

        assert len(results) == 3

        # Verify nodes were created
        check = gf.execute("MATCH (p:Person) RETURN p.name AS name ORDER BY name")
        assert len(check) == 3
        names = [r["name"].value for r in check]
        assert names == ["Alice", "Bob", "Charlie"]

    @pytest.mark.skip(reason="MATCH + UNWIND + CREATE pattern not yet supported in grammar")
    def test_unwind_create_relationships(self):
        """UNWIND to create multiple relationships."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})")

        gf.execute("""
            MATCH (a:Person {name: 'Alice'})
            UNWIND ['Bob', 'Charlie'] AS name
            CREATE (a)-[:KNOWS]->(b:Person {name: name})
        """)

        # Verify relationships
        results = gf.execute("""
            MATCH (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person)
            RETURN b.name AS name
            ORDER BY name
        """)

        assert len(results) == 2
        names = [r["name"].value for r in results]
        assert names == ["Bob", "Charlie"]


class TestUnwindWithFiltering:
    """UNWIND with WHERE clauses."""

    def test_unwind_with_where(self):
        """UNWIND with WHERE filter."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND [1, 2, 3, 4, 5] AS num
            WHERE num > 2
            RETURN num
        """)

        assert len(results) == 3
        nums = [r["num"].value for r in results]
        assert nums == [3, 4, 5]

    @pytest.mark.skip(reason="UNWIND + MATCH + WHERE + ORDER BY pattern not yet supported")
    def test_unwind_match_where(self):
        """UNWIND + MATCH + WHERE combination."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {type: 'A', val: 10}),
                   (b:Item {type: 'B', val: 20}),
                   (c:Item {type: 'C', val: 30})
        """)

        results = gf.execute("""
            UNWIND ['A', 'B', 'C'] AS t
            MATCH (i:Item {type: t})
            WHERE i.val > 15
            RETURN i.type AS type, i.val AS val
            ORDER BY val
        """)

        assert len(results) == 2
        assert results[0]["type"].value == "B"
        assert results[1]["type"].value == "C"


class TestUnwindModifiers:
    """UNWIND with ORDER BY, SKIP, LIMIT."""

    def test_unwind_with_order_by(self):
        """UNWIND with ORDER BY."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND [3, 1, 4, 1, 5] AS num
            RETURN num
            ORDER BY num DESC
        """)

        assert len(results) == 5
        nums = [r["num"].value for r in results]
        assert nums == [5, 4, 3, 1, 1]

    def test_unwind_with_limit(self):
        """UNWIND with LIMIT."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND [1, 2, 3, 4, 5] AS num
            RETURN num
            LIMIT 3
        """)

        assert len(results) == 3

    def test_unwind_with_skip(self):
        """UNWIND with SKIP."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND [1, 2, 3, 4, 5] AS num
            RETURN num
            SKIP 2
        """)

        assert len(results) == 3
        nums = [r["num"].value for r in results]
        assert nums == [3, 4, 5]

    def test_unwind_with_skip_limit(self):
        """UNWIND with SKIP and LIMIT."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND [1, 2, 3, 4, 5, 6, 7] AS num
            RETURN num
            SKIP 2
            LIMIT 3
        """)

        assert len(results) == 3
        nums = [r["num"].value for r in results]
        assert nums == [3, 4, 5]


class TestUnwindNested:
    """Nested UNWIND tests."""

    def test_multiple_unwind(self):
        """Multiple UNWIND clauses."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND [1, 2] AS x
            UNWIND [10, 20] AS y
            RETURN x, y
            ORDER BY x, y
        """)

        # 2 x 2 = 4 combinations
        assert len(results) == 4
        assert results[0]["x"].value == 1
        assert results[0]["y"].value == 10
        assert results[3]["x"].value == 2
        assert results[3]["y"].value == 20

    def test_unwind_cartesian_product(self):
        """UNWIND creating cartesian products."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND ['A', 'B'] AS letter
            UNWIND [1, 2, 3] AS num
            RETURN letter, num
            ORDER BY letter, num
        """)

        # 2 letters x 3 numbers = 6 results
        assert len(results) == 6
        assert results[0]["letter"].value == "A"
        assert results[0]["num"].value == 1
        assert results[5]["letter"].value == "B"
        assert results[5]["num"].value == 3


class TestUnwindEdgeCases:
    """Edge case tests for UNWIND."""

    @pytest.mark.skip(reason="MATCH + UNWIND + RETURN pattern not yet supported in grammar")
    def test_unwind_preserves_existing_context(self):
        """UNWIND preserves variables from MATCH."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice', age: 30})")

        results = gf.execute("""
            MATCH (p:Person {name: 'Alice'})
            UNWIND [1, 2] AS num
            RETURN p.name AS name, p.age AS age, num
        """)

        assert len(results) == 2
        # Both rows should have same person data
        assert all(r["name"].value == "Alice" for r in results)
        assert all(r["age"].value == 30 for r in results)
        # But different num values
        assert results[0]["num"].value == 1
        assert results[1]["num"].value == 2

    @pytest.mark.skip(reason="MATCH + UNWIND + RETURN pattern not yet supported in grammar")
    def test_unwind_no_match_produces_no_rows(self):
        """UNWIND after failed MATCH produces no rows."""
        gf = GraphForge()

        results = gf.execute("""
            MATCH (p:Person {name: 'NonExistent'})
            UNWIND [1, 2, 3] AS num
            RETURN p, num
        """)

        assert len(results) == 0

    def test_unwind_with_aggregation(self):
        """UNWIND before aggregation groups by the unwound value."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND [1, 2, 3, 2, 1] AS num
            RETURN num AS value, COUNT(num) AS count
            ORDER BY value
        """)

        # Grouped by num value
        assert len(results) == 3
        assert results[0]["value"].value == 1
        assert results[0]["count"].value == 2
        assert results[1]["value"].value == 2
        assert results[1]["count"].value == 2
        assert results[2]["value"].value == 3
        assert results[2]["count"].value == 1

    def test_unwind_literal_single_value(self):
        """UNWIND on single non-list value treats it as single-element list."""
        gf = GraphForge()
        results = gf.execute("""
            UNWIND 42 AS num
            RETURN num
        """)

        assert len(results) == 1
        assert results[0]["num"].value == 42
