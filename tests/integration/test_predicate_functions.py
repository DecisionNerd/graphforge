"""Integration tests for predicate functions: all(), any(), none(), single()."""

import pytest

from graphforge import GraphForge


class TestAllPredicate:
    """Test all() predicate function."""

    @pytest.mark.parametrize(
        "list_expr,predicate,expected",
        [
            ("[2, 4, 6]", "x % 2 = 0", True),  # All elements satisfy
            ("[2, 3, 4]", "x % 2 = 0", False),  # Not all satisfy
            ("[]", "x > 0", True),  # Empty list (vacuous truth)
            ("[1, 2, NULL]", "x > 2", False),  # Has False, dominates NULL
            ("[3, 4, NULL]", "x > 2", None),  # All True + NULL = NULL
            ("[1, 2, NULL]", "x > 1", False),  # False dominates NULL
        ],
    )
    def test_all_parametrized(self, list_expr, predicate, expected):
        """Test all() with various list/predicate combinations."""
        gf = GraphForge()
        result = gf.execute(f"RETURN all(x IN {list_expr} WHERE {predicate}) AS result")
        assert result[0]["result"].value == expected

    def test_all_in_where_clause(self):
        """All() used in WHERE clause."""
        gf = GraphForge()
        gf.execute("""
            CREATE (:Person {name: 'Alice', scores: [90, 95, 88]}),
                   (:Person {name: 'Bob', scores: [70, 65, 72]}),
                   (:Person {name: 'Carol', scores: [85, 88, 90]})
        """)
        result = gf.execute("""
            MATCH (p:Person)
            WHERE all(score IN p.scores WHERE score >= 85)
            RETURN p.name AS name
            ORDER BY name
        """)
        assert len(result) == 2
        assert [r["name"].value for r in result] == ["Alice", "Carol"]

    def test_all_with_property_access(self):
        """All() with property access in predicate."""
        gf = GraphForge()
        gf.execute("""
            CREATE (:Team {name: 'TeamA', members: [
                {name: 'Alice', age: 30},
                {name: 'Bob', age: 35}
            ]})
        """)
        result = gf.execute("""
            MATCH (t:Team)
            RETURN all(m IN t.members WHERE m.age >= 30) AS result
        """)
        assert result[0]["result"].value is True


class TestAnyPredicate:
    """Test any() predicate function."""

    @pytest.mark.parametrize(
        "list_expr,predicate,expected",
        [
            ("[1, 2, 3]", "x > 2", True),  # Some elements satisfy
            ("[1, 2, 3]", "x > 5", False),  # No elements satisfy
            ("[]", "x > 0", False),  # Empty list
            ("[NULL, NULL]", "x > 0", None),  # All NULL, no True
            ("[1, NULL, NULL]", "x = 1", True),  # True dominates NULL
            ("[2, 4, 6]", "x % 2 = 0", True),  # Multiple True values
        ],
    )
    def test_any_parametrized(self, list_expr, predicate, expected):
        """Test any() with various list/predicate combinations."""
        gf = GraphForge()
        result = gf.execute(f"RETURN any(x IN {list_expr} WHERE {predicate}) AS result")
        assert result[0]["result"].value == expected

    def test_any_in_where_clause(self):
        """Any() used in WHERE clause."""
        gf = GraphForge()
        gf.execute("""
            CREATE (:Person {name: 'Alice', scores: [60, 65, 95]}),
                   (:Person {name: 'Bob', scores: [70, 65, 72]}),
                   (:Person {name: 'Carol', scores: [50, 55, 60]})
        """)
        result = gf.execute("""
            MATCH (p:Person)
            WHERE any(score IN p.scores WHERE score >= 90)
            RETURN p.name AS name
        """)
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"


class TestNonePredicate:
    """Test none() predicate function."""

    @pytest.mark.parametrize(
        "list_expr,predicate,expected",
        [
            ("[1, 3, 5]", "x % 2 = 0", True),  # No elements satisfy
            ("[1, 2, 3]", "x % 2 = 0", False),  # At least one satisfies
            ("[]", "x > 0", True),  # Empty list
            ("[NULL, NULL]", "x > 0", None),  # All NULL, no True
            ("[1, NULL, NULL]", "x = 1", False),  # True makes NONE false
        ],
    )
    def test_none_parametrized(self, list_expr, predicate, expected):
        """Test none() with various list/predicate combinations."""
        gf = GraphForge()
        result = gf.execute(f"RETURN none(x IN {list_expr} WHERE {predicate}) AS result")
        assert result[0]["result"].value == expected

    def test_none_in_where_clause(self):
        """None() used in WHERE clause."""
        gf = GraphForge()
        gf.execute("""
            CREATE (:Person {name: 'Alice', scores: [60, 65, 70]}),
                   (:Person {name: 'Bob', scores: [95, 90, 92]}),
                   (:Person {name: 'Carol', scores: [75, 80, 78]})
        """)
        result = gf.execute("""
            MATCH (p:Person)
            WHERE none(score IN p.scores WHERE score >= 90)
            RETURN p.name AS name
            ORDER BY name
        """)
        assert len(result) == 2
        assert [r["name"].value for r in result] == ["Alice", "Carol"]


class TestSinglePredicate:
    """Test single() predicate function."""

    @pytest.mark.parametrize(
        "list_expr,predicate,expected",
        [
            ("[1, 2, 3]", "x = 2", True),  # Exactly one satisfies
            ("[1, 2, 3]", "x > 5", False),  # None satisfy
            ("[2, 4, 6]", "x % 2 = 0", False),  # Multiple satisfy
            ("[]", "x > 0", False),  # Empty list
            ("[NULL, NULL]", "x > 0", None),  # NULL, no True
            ("[1, NULL]", "x = 1", None),  # One True + NULL (can't determine)
            ("[1, 2, 3, 4, 5]", "x = 3", True),  # Exactly one, no NULLs
        ],
    )
    def test_single_parametrized(self, list_expr, predicate, expected):
        """Test single() with various list/predicate combinations."""
        gf = GraphForge()
        result = gf.execute(f"RETURN single(x IN {list_expr} WHERE {predicate}) AS result")
        assert result[0]["result"].value == expected

    def test_single_in_where_clause(self):
        """Single() used in WHERE clause."""
        gf = GraphForge()
        gf.execute("""
            CREATE (:Person {name: 'Alice', scores: [95, 85, 90]}),
                   (:Person {name: 'Bob', scores: [95, 90, 92]}),
                   (:Person {name: 'Carol', scores: [75, 80, 78]})
        """)
        result = gf.execute("""
            MATCH (p:Person)
            WHERE single(score IN p.scores WHERE score >= 95)
            RETURN p.name AS name
            ORDER BY name
        """)
        assert len(result) == 2
        assert [r["name"].value for r in result] == ["Alice", "Bob"]


class TestQuantifierEdgeCases:
    """Test edge cases and interactions between quantifiers."""

    def test_nested_quantifiers(self):
        """Nested quantifier expressions."""
        gf = GraphForge()
        result = gf.execute("""
            RETURN all(x IN [[1,2], [3,4], [5,6]]
                   WHERE any(y IN x WHERE y > 2)) AS result
        """)
        # [1,2]: any(y > 2) = False
        # [3,4]: any(y > 2) = True
        # [5,6]: any(y > 2) = True
        # Not all sublists have any > 2 -> False
        assert result[0]["result"].value is False

    def test_quantifier_with_string_comparison(self):
        """Quantifiers with string predicates."""
        gf = GraphForge()
        result = gf.execute("""
            RETURN all(s IN ['alice', 'bob', 'charlie']
                   WHERE size(s) >= 3) AS result
        """)
        assert result[0]["result"].value is True

    def test_quantifier_with_null_list(self):
        """Quantifier with NULL as list returns NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN all(x IN NULL WHERE x > 0) AS result")
        assert result[0]["result"].value is None

    def test_all_quantifiers_on_same_data(self):
        """Compare all quantifiers on the same dataset."""
        gf = GraphForge()
        result = gf.execute("""
            WITH [1, 2, 3, 4, 5] AS numbers
            RETURN all(x IN numbers WHERE x > 0) AS all_positive,
                   any(x IN numbers WHERE x > 3) AS any_gt_3,
                   none(x IN numbers WHERE x > 10) AS none_gt_10,
                   single(x IN numbers WHERE x = 3) AS single_eq_3
        """)
        assert result[0]["all_positive"].value is True
        assert result[0]["any_gt_3"].value is True
        assert result[0]["none_gt_10"].value is True
        assert result[0]["single_eq_3"].value is True

    def test_quantifier_in_with_clause(self):
        """Quantifiers in WITH clause projection."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', scores: [85, 90, 95]})")
        result = gf.execute("""
            MATCH (p:Person)
            WITH p, all(s IN p.scores WHERE s >= 80) AS passed
            WHERE passed = true
            RETURN p.name AS name
        """)
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"
