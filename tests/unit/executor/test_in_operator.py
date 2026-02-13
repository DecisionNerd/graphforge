"""Tests for IN operator for list membership."""

from graphforge import GraphForge


class TestInOperator:
    """Test IN operator with various value types and NULL semantics."""

    def test_in_operator_with_integers(self):
        """Basic IN operator with integer list."""
        gf = GraphForge()

        result = gf.execute("RETURN 5 IN [1, 2, 5, 10] AS result")
        assert result[0]["result"].value is True

        result = gf.execute("RETURN 3 IN [1, 2, 5, 10] AS result")
        assert result[0]["result"].value is False

    def test_in_operator_with_strings(self):
        """IN operator with string list."""
        gf = GraphForge()

        result = gf.execute("RETURN 'apple' IN ['apple', 'banana', 'cherry'] AS result")
        assert result[0]["result"].value is True

        result = gf.execute("RETURN 'grape' IN ['apple', 'banana', 'cherry'] AS result")
        assert result[0]["result"].value is False

    def test_in_operator_with_empty_list(self):
        """IN operator with empty list returns false."""
        gf = GraphForge()

        result = gf.execute("RETURN 5 IN [] AS result")
        assert result[0]["result"].value is False

    def test_in_operator_null_value(self):
        """NULL IN list returns NULL."""
        gf = GraphForge()

        result = gf.execute("RETURN null IN [1, 2, 3] AS result")
        # NULL should return NULL (ternary logic)
        from graphforge.types.values import CypherNull

        assert isinstance(result[0]["result"], CypherNull)

    def test_in_operator_null_list(self):
        """value IN NULL returns NULL."""
        gf = GraphForge()

        result = gf.execute("RETURN 5 IN null AS result")
        from graphforge.types.values import CypherNull

        assert isinstance(result[0]["result"], CypherNull)

    def test_in_operator_with_null_in_list(self):
        """IN operator with NULL values in the list."""
        gf = GraphForge()

        # 5 is not in list (even though NULL is there), and we can't compare with NULL
        # If no match and NULL present: return NULL
        result = gf.execute("RETURN 5 IN [1, 2, null, 3] AS result")
        from graphforge.types.values import CypherNull

        assert isinstance(result[0]["result"], CypherNull)

        # If there IS a match, return true regardless of NULL
        result = gf.execute("RETURN 2 IN [1, 2, null, 3] AS result")
        assert result[0]["result"].value is True

    def test_in_operator_with_node_property(self):
        """IN operator with node properties."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 25})")
        gf.execute("CREATE (:Person {name: 'Charlie', age: 35})")

        # Find people in a specific age range
        result = gf.execute(
            """
            MATCH (p:Person)
            WHERE p.age IN [25, 30]
            RETURN p.name AS name
            ORDER BY name
        """
        )

        assert len(result) == 2
        assert result[0]["name"].value == "Alice"
        assert result[1]["name"].value == "Bob"

    def test_in_operator_with_relationship_types(self):
        """IN operator for filtering relationship types."""
        gf = GraphForge()

        gf.execute("CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})")
        gf.execute("CREATE (a:Person {name: 'Alice'})-[:WORKS_WITH]->(c:Person {name: 'Charlie'})")
        gf.execute("CREATE (a:Person {name: 'Alice'})-[:LIVES_NEAR]->(d:Person {name: 'Dave'})")

        # Find relationships of specific types
        result = gf.execute(
            """
            MATCH (a:Person {name: 'Alice'})-[r]->(b:Person)
            WHERE type(r) IN ['KNOWS', 'WORKS_WITH']
            RETURN b.name AS name
            ORDER BY name
        """
        )

        assert len(result) == 2
        assert result[0]["name"].value == "Bob"
        assert result[1]["name"].value == "Charlie"

    def test_in_operator_with_boolean_values(self):
        """IN operator with boolean values."""
        gf = GraphForge()

        result = gf.execute("RETURN true IN [false, true, false] AS result")
        assert result[0]["result"].value is True

        result = gf.execute("RETURN true IN [false, false] AS result")
        assert result[0]["result"].value is False

    def test_in_operator_with_mixed_types(self):
        """IN operator behavior with mixed types in list."""
        gf = GraphForge()

        # String '5' should not match integer 5
        result = gf.execute("RETURN 5 IN [1, '5', 10] AS result")
        assert result[0]["result"].value is False

        # But matching type should work
        result = gf.execute("RETURN '5' IN [1, '5', 10] AS result")
        assert result[0]["result"].value is True

    def test_in_operator_in_where_clause(self):
        """IN operator used in WHERE clause filtering."""
        gf = GraphForge()

        gf.execute("CREATE (:City {name: 'NYC', country: 'USA'})")
        gf.execute("CREATE (:City {name: 'London', country: 'UK'})")
        gf.execute("CREATE (:City {name: 'Paris', country: 'France'})")
        gf.execute("CREATE (:City {name: 'Tokyo', country: 'Japan'})")

        result = gf.execute(
            """
            MATCH (c:City)
            WHERE c.country IN ['USA', 'UK']
            RETURN c.name AS name
            ORDER BY name
        """
        )

        assert len(result) == 2
        assert result[0]["name"].value == "London"
        assert result[1]["name"].value == "NYC"

    def test_in_operator_with_list_expression(self):
        """IN operator with dynamically created list."""
        gf = GraphForge()

        gf.execute("CREATE (:Number {value: 1})")
        gf.execute("CREATE (:Number {value: 5})")
        gf.execute("CREATE (:Number {value: 10})")

        # Use COLLECT to create list dynamically
        result = gf.execute(
            """
            MATCH (n:Number)
            WITH collect(n.value) AS numbers
            RETURN 5 IN numbers AS result
        """
        )

        assert result[0]["result"].value is True

    def test_in_operator_negation(self):
        """NOT with IN operator."""
        gf = GraphForge()

        result = gf.execute("RETURN NOT (5 IN [1, 2, 3]) AS result")
        assert result[0]["result"].value is True

        result = gf.execute("RETURN NOT (2 IN [1, 2, 3]) AS result")
        assert result[0]["result"].value is False
