"""Unit tests for WITH clause validation (Issue #172)."""

import pytest

from graphforge import GraphForge


class TestWithDuplicateAliases:
    """Test validation for duplicate aliases in WITH clause."""

    def test_duplicate_alias_same_expression(self):
        """WITH 1 AS a, 2 AS a should raise ColumnNameConflict."""
        gf = GraphForge()

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("WITH 1 AS a, 2 AS a RETURN a")

        assert "ColumnNameConflict" in str(exc_info.value)
        assert "'a'" in str(exc_info.value)

    def test_duplicate_alias_different_expressions(self):
        """WITH 1 AS x, 2 AS x should raise ColumnNameConflict."""
        gf = GraphForge()

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("WITH 1 + 1 AS result, 2 * 2 AS result RETURN result")

        assert "ColumnNameConflict" in str(exc_info.value)
        assert "'result'" in str(exc_info.value)

    def test_duplicate_alias_with_variable(self):
        """WITH n, n AS x should raise ColumnNameConflict (implicit alias 'n')."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("MATCH (n) WITH n, 1 AS n RETURN n")

        assert "ColumnNameConflict" in str(exc_info.value)

    def test_multiple_duplicates(self):
        """WITH a AS x, b AS x, c AS x should detect first duplicate."""
        gf = GraphForge()

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("WITH 1 AS x, 2 AS x, 3 AS x RETURN x")

        assert "ColumnNameConflict" in str(exc_info.value)
        assert "'x'" in str(exc_info.value)

    def test_unique_aliases_succeed(self):
        """WITH 1 AS a, 2 AS b, 3 AS c should succeed."""
        gf = GraphForge()

        result = gf.execute("WITH 1 AS a, 2 AS b, 3 AS c RETURN a, b, c")

        assert len(result) == 1
        assert result[0]["a"].value == 1
        assert result[0]["b"].value == 2
        assert result[0]["c"].value == 3


class TestWithUnaliasedExpressions:
    """Test validation for unaliased expressions in WITH clause."""

    def test_unaliased_function_call(self):
        """WITH count(*) should raise NoExpressionAlias."""
        gf = GraphForge()
        gf.execute("CREATE (:Person)")

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("MATCH (n) WITH count(*) RETURN n")

        assert "NoExpressionAlias" in str(exc_info.value)

    def test_unaliased_arithmetic_expression(self):
        """WITH 1 + 2 should raise NoExpressionAlias."""
        gf = GraphForge()

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("WITH 1 + 2 RETURN 1")

        assert "NoExpressionAlias" in str(exc_info.value)

    def test_unaliased_property_access(self):
        """WITH n.name should raise NoExpressionAlias."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("MATCH (n) WITH n.name RETURN n")

        assert "NoExpressionAlias" in str(exc_info.value)

    def test_unaliased_literal(self):
        """WITH 42 should raise NoExpressionAlias."""
        gf = GraphForge()

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("WITH 42 RETURN 1")

        assert "NoExpressionAlias" in str(exc_info.value)

    def test_unaliased_list(self):
        """WITH [1, 2, 3] should raise NoExpressionAlias."""
        gf = GraphForge()

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("WITH [1, 2, 3] RETURN 1")

        assert "NoExpressionAlias" in str(exc_info.value)

    def test_unaliased_map(self):
        """WITH {key: 'value'} should raise NoExpressionAlias."""
        gf = GraphForge()

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("WITH {key: 'value'} RETURN 1")

        assert "NoExpressionAlias" in str(exc_info.value)

    def test_mixed_aliased_and_unaliased(self):
        """WITH n, count(*) should raise NoExpressionAlias (count(*) not aliased)."""
        gf = GraphForge()
        gf.execute("CREATE (:Person)")

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("MATCH (n) WITH n, count(*) RETURN n")

        assert "NoExpressionAlias" in str(exc_info.value)

    def test_unaliased_variable_allowed(self):
        """WITH n (unaliased variable) should be allowed."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")

        result = gf.execute("MATCH (n) WITH n RETURN n.name AS name")

        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_multiple_unaliased_variables_allowed(self):
        """WITH n, m (multiple unaliased variables) should be allowed."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")

        result = gf.execute(
            "MATCH (n:Person), (m:Person) WHERE n.name < m.name WITH n, m RETURN n.name AS n1, m.name AS n2"
        )

        assert len(result) == 1
        assert result[0]["n1"].value == "Alice"
        assert result[0]["n2"].value == "Bob"


class TestWithValidationEdgeCases:
    """Test edge cases in WITH clause validation."""

    def test_validation_with_where_clause(self):
        """Validation should work with WHERE clause."""
        gf = GraphForge()

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("WITH 1 AS a, 2 AS a WHERE a > 0 RETURN a")

        assert "ColumnNameConflict" in str(exc_info.value)

    def test_validation_with_order_by(self):
        """Validation should work with ORDER BY clause."""
        gf = GraphForge()

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("WITH 1 AS a, 2 AS a ORDER BY a RETURN a")

        assert "ColumnNameConflict" in str(exc_info.value)

    def test_validation_with_limit(self):
        """Validation should work with LIMIT clause."""
        gf = GraphForge()

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("WITH 1 AS a, 2 AS a LIMIT 1 RETURN a")

        assert "ColumnNameConflict" in str(exc_info.value)

    def test_validation_with_distinct(self):
        """Validation should work with DISTINCT."""
        gf = GraphForge()

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("WITH DISTINCT 1 AS a, 2 AS a RETURN a")

        assert "ColumnNameConflict" in str(exc_info.value)

    def test_validation_in_chained_with(self):
        """Validation should apply to each WITH in chain."""
        gf = GraphForge()

        # First WITH is valid, second has duplicate
        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("WITH 1 AS a WITH a AS b, a AS b RETURN b")

        assert "ColumnNameConflict" in str(exc_info.value)

    def test_validation_after_match(self):
        """Validation should work for WITH after MATCH."""
        gf = GraphForge()
        gf.execute("CREATE (:Person)")

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("MATCH (n) WITH n AS x, n AS x RETURN x")

        assert "ColumnNameConflict" in str(exc_info.value)

    def test_validation_with_aggregation(self):
        """Validation should work with aggregation functions."""
        gf = GraphForge()
        gf.execute("CREATE (:Person)")

        with pytest.raises(SyntaxError) as exc_info:
            gf.execute("MATCH (n) WITH count(n) AS c, sum(1) AS c RETURN c")

        assert "ColumnNameConflict" in str(exc_info.value)
