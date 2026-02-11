"""Unit tests for three-valued logic (AND/OR with NULL)."""

from graphforge.api import GraphForge


class TestThreeValuedLogicAND:
    """Test three-valued logic for AND operator."""

    def test_false_and_false(self):
        """false AND false = false."""
        gf = GraphForge()
        result = gf.execute("RETURN false AND false AS result")
        assert result[0]["result"].value is False

    def test_false_and_true(self):
        """false AND true = false."""
        gf = GraphForge()
        result = gf.execute("RETURN false AND true AS result")
        assert result[0]["result"].value is False

    def test_false_and_null(self):
        """false AND NULL = false (NULL is not evaluated due to short-circuit)."""
        gf = GraphForge()
        result = gf.execute("RETURN false AND null AS result")
        assert result[0]["result"].value is False

    def test_true_and_false(self):
        """true AND false = false."""
        gf = GraphForge()
        result = gf.execute("RETURN true AND false AS result")
        assert result[0]["result"].value is False

    def test_true_and_true(self):
        """true AND true = true."""
        gf = GraphForge()
        result = gf.execute("RETURN true AND true AS result")
        assert result[0]["result"].value is True

    def test_true_and_null(self):
        """true AND NULL = NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN true AND null AS result")
        from graphforge.types.values import CypherNull

        assert isinstance(result[0]["result"], CypherNull)

    def test_null_and_false(self):
        """NULL AND false = false."""
        gf = GraphForge()
        result = gf.execute("RETURN null AND false AS result")
        assert result[0]["result"].value is False

    def test_null_and_true(self):
        """NULL AND true = NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN null AND true AS result")
        from graphforge.types.values import CypherNull

        assert isinstance(result[0]["result"], CypherNull)

    def test_null_and_null(self):
        """NULL AND NULL = NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN null AND null AS result")
        from graphforge.types.values import CypherNull

        assert isinstance(result[0]["result"], CypherNull)


class TestThreeValuedLogicOR:
    """Test three-valued logic for OR operator."""

    def test_false_or_false(self):
        """false OR false = false."""
        gf = GraphForge()
        result = gf.execute("RETURN false OR false AS result")
        assert result[0]["result"].value is False

    def test_false_or_true(self):
        """false OR true = true."""
        gf = GraphForge()
        result = gf.execute("RETURN false OR true AS result")
        assert result[0]["result"].value is True

    def test_false_or_null(self):
        """false OR NULL = NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN false OR null AS result")
        from graphforge.types.values import CypherNull

        assert isinstance(result[0]["result"], CypherNull)

    def test_true_or_false(self):
        """true OR false = true."""
        gf = GraphForge()
        result = gf.execute("RETURN true OR false AS result")
        assert result[0]["result"].value is True

    def test_true_or_true(self):
        """true OR true = true."""
        gf = GraphForge()
        result = gf.execute("RETURN true OR true AS result")
        assert result[0]["result"].value is True

    def test_true_or_null(self):
        """true OR NULL = true (NULL is not evaluated due to short-circuit)."""
        gf = GraphForge()
        result = gf.execute("RETURN true OR null AS result")
        assert result[0]["result"].value is True

    def test_null_or_false(self):
        """NULL OR false = NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN null OR false AS result")
        from graphforge.types.values import CypherNull

        assert isinstance(result[0]["result"], CypherNull)

    def test_null_or_true(self):
        """NULL OR true = true."""
        gf = GraphForge()
        result = gf.execute("RETURN null OR true AS result")
        assert result[0]["result"].value is True

    def test_null_or_null(self):
        """NULL OR NULL = NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN null OR null AS result")
        from graphforge.types.values import CypherNull

        assert isinstance(result[0]["result"], CypherNull)


class TestThreeValuedLogicInPredicates:
    """Test three-valued logic in WHERE predicates."""

    def test_where_with_null_property_and(self):
        """WHERE with NULL property in AND expression."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', active: true})")
        gf.execute("CREATE (:Person {name: 'Bob'})")  # No active property (NULL)
        gf.execute("CREATE (:Person {name: 'Charlie', active: false})")

        # true AND NULL = NULL (filtered out)
        results = gf.execute(
            """
            MATCH (p:Person)
            WHERE p.name = 'Alice' AND p.active = true
            RETURN p.name AS name
            """
        )
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

        # NULL AND false = false (filtered out)
        results2 = gf.execute(
            """
            MATCH (p:Person)
            WHERE p.active = true AND false
            RETURN p.name AS name
            """
        )
        assert len(results2) == 0

    def test_where_with_null_property_or(self):
        """WHERE with NULL property in OR expression."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', active: true})")
        gf.execute("CREATE (:Person {name: 'Bob'})")  # No active property (NULL)
        gf.execute("CREATE (:Person {name: 'Charlie', active: false})")

        # For Alice: name = 'Alice' is true, so true OR anything = true (included)
        # For Bob: name = 'Bob' is false, active is NULL, so false OR NULL = NULL (filtered out)
        # For Charlie: name = 'Charlie' is false, active = false, so false OR false = false (filtered out)
        results = gf.execute(
            """
            MATCH (p:Person)
            WHERE p.name = 'Alice' OR p.active = true
            RETURN p.name AS name
            ORDER BY name
            """
        )
        assert len(results) == 1  # Only Alice
        assert results[0]["name"].value == "Alice"

    def test_pattern_predicate_with_null_and(self):
        """Pattern predicate with NULL in AND expression."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}) CREATE (a)-[:KNOWS {active: true, since: 2020}]->(:Person {name: 'Bob'})"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}) CREATE (a)-[:KNOWS {since: 2015}]->(:Person {name: 'Charlie'})"
        )  # No active property

        # true AND NULL = NULL (filtered out)
        results = gf.execute(
            """
            MATCH (a:Person)-[r:KNOWS WHERE r.since > 2018 AND r.active = true]->(b:Person)
            RETURN b.name AS name
            """
        )
        assert len(results) == 1
        assert results[0]["name"].value == "Bob"

    def test_pattern_predicate_with_null_or(self):
        """Pattern predicate with NULL in OR expression."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}) CREATE (a)-[:KNOWS {active: true, since: 2020}]->(:Person {name: 'Bob'})"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}) CREATE (a)-[:KNOWS {since: 2015}]->(:Person {name: 'Charlie'})"
        )  # No active property

        # NULL OR (since < 2018) evaluates to NULL OR true = true (included)
        results = gf.execute(
            """
            MATCH (a:Person)-[r:KNOWS WHERE r.active = true OR r.since < 2018]->(b:Person)
            RETURN b.name AS name
            ORDER BY name
            """
        )
        assert len(results) == 2
        assert results[0]["name"].value == "Bob"
        assert results[1]["name"].value == "Charlie"


class TestThreeValuedLogicNOT:
    """Test NOT operator with three-valued logic."""

    def test_not_true(self):
        """NOT true = false."""
        gf = GraphForge()
        result = gf.execute("RETURN NOT true AS result")
        assert result[0]["result"].value is False

    def test_not_false(self):
        """NOT false = true."""
        gf = GraphForge()
        result = gf.execute("RETURN NOT false AS result")
        assert result[0]["result"].value is True

    def test_not_null(self):
        """NOT NULL = NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN NOT null AS result")
        from graphforge.types.values import CypherNull

        assert isinstance(result[0]["result"], CypherNull)


class TestThreeValuedLogicComplex:
    """Test complex expressions with three-valued logic."""

    def test_chained_and(self):
        """Chained AND expressions."""
        gf = GraphForge()
        result = gf.execute("RETURN true AND true AND false AS result")
        assert result[0]["result"].value is False

    def test_chained_or(self):
        """Chained OR expressions."""
        gf = GraphForge()
        result = gf.execute("RETURN false OR false OR true AS result")
        assert result[0]["result"].value is True

    def test_mixed_and_or_with_null(self):
        """Mixed AND/OR with NULL."""
        gf = GraphForge()
        # (false OR NULL) AND true = NULL AND true = NULL
        result = gf.execute("RETURN (false OR null) AND true AS result")
        from graphforge.types.values import CypherNull

        assert isinstance(result[0]["result"], CypherNull)

    def test_short_circuit_false_and(self):
        """Short-circuit evaluation: false AND (error) should not error."""
        gf = GraphForge()
        # If short-circuit works, the division by zero won't be evaluated
        result = gf.execute("RETURN false AND (1/0 > 0) AS result")
        assert result[0]["result"].value is False

    def test_short_circuit_true_or(self):
        """Short-circuit evaluation: true OR (error) should not error."""
        gf = GraphForge()
        # If short-circuit works, the division by zero won't be evaluated
        result = gf.execute("RETURN true OR (1/0 > 0) AS result")
        assert result[0]["result"].value is True
