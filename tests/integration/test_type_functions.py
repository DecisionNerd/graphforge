"""Integration tests for type conversion functions (Feature 3).

Tests for toInteger, toFloat, toString, and type functions.
"""

import pytest

from graphforge import GraphForge


@pytest.fixture
def simple_graph():
    """Create a simple graph with various property types for testing."""
    gf = GraphForge()

    # Create nodes with various types
    gf.create_node(["Person"], name="Alice", age=30, score=98.5, active=True)
    gf.create_node(["Person"], name="Bob", age_str="25", score_str="87.3")

    # Create relationship for type() function testing
    alice = gf.execute("MATCH (p:Person {name: 'Alice'}) RETURN p")[0]["p"]
    bob = gf.execute("MATCH (p:Person {name: 'Bob'}) RETURN p")[0]["p"]
    gf.create_relationship(alice, bob, "KNOWS", since=2020)

    return gf


@pytest.mark.integration
class TestToIntegerFunction:
    """Tests for toInteger() function."""

    def test_to_integer_from_string(self, simple_graph):
        """toInteger converts string to integer."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN toInteger(n.age_str) AS age
        """)

        assert len(results) == 1
        assert results[0]["age"].value == 25

    def test_to_integer_from_float(self, simple_graph):
        """toInteger converts float to integer (truncates)."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN toInteger(n.score) AS score_int
        """)

        assert len(results) == 1
        assert results[0]["score_int"].value == 98

    def test_to_integer_from_integer(self, simple_graph):
        """toInteger with integer returns same value."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN toInteger(n.age) AS age
        """)

        assert len(results) == 1
        assert results[0]["age"].value == 30

    def test_to_integer_from_boolean_true(self, simple_graph):
        """toInteger converts true to 1."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN toInteger(n.active) AS active_int
        """)

        assert len(results) == 1
        assert results[0]["active_int"].value == 1

    def test_to_integer_from_literal(self, simple_graph):
        """toInteger converts string literal."""
        # Create a dummy node to enable RETURN
        simple_graph.execute("CREATE (:Dummy)")
        results = simple_graph.execute("""
            MATCH (d:Dummy)
            RETURN toInteger('42') AS num
        """)

        assert len(results) == 1
        assert results[0]["num"].value == 42

    def test_to_integer_invalid_string_returns_null(self, simple_graph):
        """toInteger with invalid string returns NULL."""
        # Create a dummy node to enable RETURN
        simple_graph.execute("CREATE (:Dummy)")
        results = simple_graph.execute("""
            MATCH (d:Dummy)
            RETURN toInteger('not a number') AS result
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["result"], CypherNull)

    def test_to_integer_with_null(self, simple_graph):
        """toInteger with NULL returns NULL."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN toInteger(n.missing) AS result
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["result"], CypherNull)


@pytest.mark.integration
class TestToFloatFunction:
    """Tests for toFloat() function."""

    def test_to_float_from_string(self, simple_graph):
        """toFloat converts string to float."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN toFloat(n.score_str) AS score
        """)

        assert len(results) == 1
        assert abs(results[0]["score"].value - 87.3) < 0.001

    def test_to_float_from_integer(self, simple_graph):
        """toFloat converts integer to float."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN toFloat(n.age) AS age_float
        """)

        assert len(results) == 1
        assert abs(results[0]["age_float"].value - 30.0) < 0.001

    def test_to_float_from_float(self, simple_graph):
        """toFloat with float returns same value."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN toFloat(n.score) AS score
        """)

        assert len(results) == 1
        assert abs(results[0]["score"].value - 98.5) < 0.001

    def test_to_float_from_boolean_true(self, simple_graph):
        """toFloat converts true to 1.0."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN toFloat(n.active) AS active_float
        """)

        assert len(results) == 1
        assert abs(results[0]["active_float"].value - 1.0) < 0.001

    def test_to_float_from_literal(self, simple_graph):
        """toFloat converts string literal."""
        # Create a dummy node to enable RETURN
        simple_graph.execute("CREATE (:Dummy)")
        results = simple_graph.execute("""
            MATCH (d:Dummy)
            RETURN toFloat('3.14159') AS pi
        """)

        assert len(results) == 1
        assert abs(results[0]["pi"].value - 3.14159) < 0.00001

    def test_to_float_invalid_string_returns_null(self, simple_graph):
        """toFloat with invalid string returns NULL."""
        # Create a dummy node to enable RETURN
        simple_graph.execute("CREATE (:Dummy)")
        results = simple_graph.execute("""
            MATCH (d:Dummy)
            RETURN toFloat('not a number') AS result
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["result"], CypherNull)

    def test_to_float_with_null(self, simple_graph):
        """toFloat with NULL returns NULL."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN toFloat(n.missing) AS result
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["result"], CypherNull)


@pytest.mark.integration
class TestToStringFunction:
    """Tests for toString() function."""

    def test_to_string_from_integer(self, simple_graph):
        """toString converts integer to string."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN toString(n.age) AS age_str
        """)

        assert len(results) == 1
        assert results[0]["age_str"].value == "30"

    def test_to_string_from_float(self, simple_graph):
        """toString converts float to string."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN toString(n.score) AS score_str
        """)

        assert len(results) == 1
        assert results[0]["score_str"].value == "98.5"

    def test_to_string_from_string(self, simple_graph):
        """toString with string returns same value."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN toString(n.name) AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_to_string_from_boolean_true(self, simple_graph):
        """toString converts true to 'true'."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN toString(n.active) AS active_str
        """)

        assert len(results) == 1
        assert results[0]["active_str"].value == "true"

    def test_to_string_from_literal(self, simple_graph):
        """toString converts integer literal."""
        # Create a dummy node to enable RETURN
        simple_graph.execute("CREATE (:Dummy)")
        results = simple_graph.execute("""
            MATCH (d:Dummy)
            RETURN toString(42) AS num_str
        """)

        assert len(results) == 1
        assert results[0]["num_str"].value == "42"

    def test_to_string_with_null(self, simple_graph):
        """toString with NULL returns NULL."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN toString(n.missing) AS result
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["result"], CypherNull)


@pytest.mark.integration
class TestTypeFunction:
    """Tests for type() function."""

    def test_type_function_on_string(self, simple_graph):
        """type() returns type name for string value."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN type(n.name) AS type_name
        """)

        assert len(results) == 1
        # Should return "String" (stripped "Cypher" prefix)
        assert results[0]["type_name"].value == "String"

    def test_type_function_on_integer(self, simple_graph):
        """type() returns type name for integer value."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN type(n.age) AS type_name
        """)

        assert len(results) == 1
        assert results[0]["type_name"].value == "Int"


@pytest.mark.integration
class TestTypeFunctionsCombined:
    """Tests combining multiple type functions."""

    def test_nested_type_conversions(self, simple_graph):
        """Type functions can be nested."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN toString(toInteger(n.age_str)) AS age_str
        """)

        assert len(results) == 1
        assert results[0]["age_str"].value == "25"

    def test_conversion_in_where_clause(self, simple_graph):
        """Type conversion in WHERE clause."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE toInteger(n.age_str) > 20
            RETURN n.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Bob"

    def test_conversion_for_comparison(self, simple_graph):
        """Type conversion for comparison."""
        # Test conversion in WHERE clause for comparison
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE toInteger(n.age_str) = 25
            RETURN n.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Bob"
