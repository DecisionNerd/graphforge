"""Integration tests for predicate functions: all(), any(), none(), single()."""

import pytest

from graphforge import GraphForge


class TestAllPredicate:
    """Test all() predicate function."""

    def test_all_basic_true(self):
        """All elements satisfy predicate."""
        gf = GraphForge()
        result = gf.execute("RETURN all(x IN [2, 4, 6] WHERE x % 2 = 0) AS result")
        assert result[0]["result"].value is True

    def test_all_basic_false(self):
        """Not all elements satisfy predicate."""
        gf = GraphForge()
        result = gf.execute("RETURN all(x IN [2, 3, 4] WHERE x % 2 = 0) AS result")
        assert result[0]["result"].value is False

    def test_all_empty_list(self):
        """All on empty list returns true (vacuous truth)."""
        gf = GraphForge()
        result = gf.execute("RETURN all(x IN [] WHERE x > 0) AS result")
        assert result[0]["result"].value is True

    def test_all_with_null_in_list(self):
        """All with NULL in list where predicate on NULL returns NULL."""
        gf = GraphForge()
        # Explicitly create a list with NULL using literal
        result = gf.execute("RETURN all(x IN [1, 2, NULL] WHERE x > 2) AS result")
        # x=1: 1 > 2 = False -> Has a False, so result is False
        assert result[0]["result"].value is False

    def test_all_true_with_null_gives_null(self):
        """All returns NULL when all non-NULL are True but list contains NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN all(x IN [3, 4, NULL] WHERE x > 2) AS result")
        # x=3: 3 > 2 = True
        # x=4: 4 > 2 = True
        # x=NULL: NULL > 2 = NULL
        # No False, not all satisfied (NULL exists) -> NULL
        assert result[0]["result"].value is None

    def test_all_single_false_dominates_null(self):
        """Single False dominates NULL values."""
        gf = GraphForge()
        result = gf.execute("RETURN all(x IN [1, 2, NULL] WHERE x > 1) AS result")
        # x=1 gives False, x=2 gives True, x=NULL gives NULL
        # False dominates -> False
        assert result[0]["result"].value is False

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

    def test_any_basic_true(self):
        """Any element satisfies predicate."""
        gf = GraphForge()
        result = gf.execute("RETURN any(x IN [1, 2, 3] WHERE x > 2) AS result")
        assert result[0]["result"].value is True

    def test_any_basic_false(self):
        """No element satisfies predicate."""
        gf = GraphForge()
        result = gf.execute("RETURN any(x IN [1, 2, 3] WHERE x > 5) AS result")
        assert result[0]["result"].value is False

    def test_any_empty_list(self):
        """Any on empty list returns false."""
        gf = GraphForge()
        result = gf.execute("RETURN any(x IN [] WHERE x > 0) AS result")
        assert result[0]["result"].value is False

    def test_any_with_null_predicate(self):
        """Any with NULL predicate returns NULL when no True."""
        gf = GraphForge()
        result = gf.execute("RETURN any(x IN [NULL, NULL] WHERE x > 0) AS result")
        # All predicates return NULL, no True found -> NULL
        assert result[0]["result"].value is None

    def test_any_true_dominates_null(self):
        """Single True dominates NULL values."""
        gf = GraphForge()
        result = gf.execute("RETURN any(x IN [1, NULL, NULL] WHERE x = 1) AS result")
        # x=1 gives True, others give NULL
        # True dominates -> True
        assert result[0]["result"].value is True

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

    def test_any_multiple_true(self):
        """Any with multiple true values still returns true."""
        gf = GraphForge()
        result = gf.execute("RETURN any(x IN [2, 4, 6] WHERE x % 2 = 0) AS result")
        assert result[0]["result"].value is True


class TestNonePredicate:
    """Test none() predicate function."""

    def test_none_basic_true(self):
        """No elements satisfy predicate."""
        gf = GraphForge()
        result = gf.execute("RETURN none(x IN [1, 3, 5] WHERE x % 2 = 0) AS result")
        assert result[0]["result"].value is True

    def test_none_basic_false(self):
        """At least one element satisfies predicate."""
        gf = GraphForge()
        result = gf.execute("RETURN none(x IN [1, 2, 3] WHERE x % 2 = 0) AS result")
        assert result[0]["result"].value is False

    def test_none_empty_list(self):
        """None on empty list returns true."""
        gf = GraphForge()
        result = gf.execute("RETURN none(x IN [] WHERE x > 0) AS result")
        assert result[0]["result"].value is True

    def test_none_with_null_predicate(self):
        """None with NULL predicate returns NULL when no True."""
        gf = GraphForge()
        result = gf.execute("RETURN none(x IN [NULL, NULL] WHERE x > 0) AS result")
        # All predicates return NULL, no True found -> NULL
        assert result[0]["result"].value is None

    def test_none_false_dominates_null(self):
        """Single True (making NONE false) dominates NULL values."""
        gf = GraphForge()
        result = gf.execute("RETURN none(x IN [1, NULL, NULL] WHERE x = 1) AS result")
        # x=1 gives True, which makes NONE false
        # False dominates -> False
        assert result[0]["result"].value is False

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

    def test_single_basic_true(self):
        """Exactly one element satisfies predicate."""
        gf = GraphForge()
        result = gf.execute("RETURN single(x IN [1, 2, 3] WHERE x = 2) AS result")
        assert result[0]["result"].value is True

    def test_single_none_match(self):
        """No elements satisfy predicate."""
        gf = GraphForge()
        result = gf.execute("RETURN single(x IN [1, 2, 3] WHERE x > 5) AS result")
        assert result[0]["result"].value is False

    def test_single_multiple_match(self):
        """Multiple elements satisfy predicate."""
        gf = GraphForge()
        result = gf.execute("RETURN single(x IN [2, 4, 6] WHERE x % 2 = 0) AS result")
        assert result[0]["result"].value is False

    def test_single_empty_list(self):
        """Single on empty list returns false."""
        gf = GraphForge()
        result = gf.execute("RETURN single(x IN [] WHERE x > 0) AS result")
        assert result[0]["result"].value is False

    def test_single_with_null_no_true(self):
        """Single with NULL and no True returns NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN single(x IN [NULL, NULL] WHERE x > 0) AS result")
        # No True values, but has NULL -> NULL
        assert result[0]["result"].value is None

    def test_single_one_true_with_null(self):
        """Single True with NULL returns NULL (can't determine uniqueness)."""
        gf = GraphForge()
        result = gf.execute("RETURN single(x IN [1, NULL] WHERE x = 1) AS result")
        # x=1: 1 = 1 = True (satisfied)
        # x=NULL: NULL = 1 = NULL
        # satisfied_count = 1, null_count = 1
        # According to line 622-629: if satisfied_count == 1 and null_count == 0: True
        # elif satisfied_count == 0 and null_count > 0: NULL
        # else: False
        # With satisfied_count=1 and null_count=1, falls to else -> False
        assert result[0]["result"].value is False

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

    def test_single_exactly_one_no_nulls(self):
        """Single returns true only when exactly one and no NULLs."""
        gf = GraphForge()
        result = gf.execute("RETURN single(x IN [1, 2, 3, 4, 5] WHERE x = 3) AS result")
        assert result[0]["result"].value is True


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
        """Quantifier with NULL as list should error."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="Quantifier requires a list"):
            gf.execute("RETURN all(x IN NULL WHERE x > 0) AS result")

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
