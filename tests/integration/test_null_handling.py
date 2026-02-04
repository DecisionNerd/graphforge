"""Integration tests for NULL handling (Feature 4).

Tests for COALESCE, NULL comparisons, and NULL in WHERE clauses.
"""

import pytest

from graphforge import GraphForge


@pytest.fixture
def simple_graph():
    """Create a simple graph with NULL properties for testing."""
    gf = GraphForge()

    # Create nodes with some NULL properties
    gf.create_node(["Person"], name="Alice", age=30, city="NYC")
    gf.create_node(["Person"], name="Bob", age=25)  # Missing city
    gf.create_node(["Person"], name="Charlie", city="LA")  # Missing age

    return gf


@pytest.mark.integration
class TestCoalesceFunction:
    """Tests for COALESCE() function."""

    def test_coalesce_returns_first_non_null(self, simple_graph):
        """COALESCE returns first non-NULL value."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN COALESCE(n.city, 'Unknown') AS city
        """)

        assert len(results) == 1
        assert results[0]["city"].value == "Unknown"

    def test_coalesce_returns_existing_value(self, simple_graph):
        """COALESCE returns existing value when not NULL."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN COALESCE(n.city, 'Unknown') AS city
        """)

        assert len(results) == 1
        assert results[0]["city"].value == "NYC"

    def test_coalesce_multiple_nulls(self, simple_graph):
        """COALESCE with multiple NULL values."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN COALESCE(n.city, n.missing, 'Default') AS value
        """)

        assert len(results) == 1
        assert results[0]["value"].value == "Default"

    def test_coalesce_all_null_returns_null(self, simple_graph):
        """COALESCE with all NULL returns NULL."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN COALESCE(n.city, n.missing) AS value
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["value"], CypherNull)

    def test_coalesce_in_where_clause(self, simple_graph):
        """COALESCE can be used in WHERE clause."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE COALESCE(n.city, 'Unknown') = 'Unknown'
            RETURN n.name AS name
        """)

        # Only Bob has NULL city
        assert len(results) == 1
        assert results[0]["name"].value == "Bob"


@pytest.mark.integration
class TestNullComparisons:
    """Tests for NULL in comparison operations."""

    def test_null_equals_comparison_filters_out(self, simple_graph):
        """NULL = value filters out row."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE n.age = NULL
            RETURN n.name AS name
        """)

        # NULL comparison returns NULL, filtered by WHERE
        assert len(results) == 0

    def test_null_greater_than_comparison_filters_out(self, simple_graph):
        """NULL > value filters out row."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE n.age > NULL
            RETURN n.name AS name
        """)

        assert len(results) == 0

    def test_null_less_than_comparison_filters_out(self, simple_graph):
        """NULL < value filters out row."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE n.age < NULL
            RETURN n.name AS name
        """)

        assert len(results) == 0

    def test_comparison_with_missing_property(self, simple_graph):
        """Comparison with missing property (NULL) filters out."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE n.age > 20
            RETURN n.name AS name
        """)

        # Charlie has NULL age, so filtered out
        # Alice (30) and Bob (25) pass
        assert len(results) == 2
        names = {results[0]["name"].value, results[1]["name"].value}
        assert names == {"Alice", "Bob"}


@pytest.mark.integration
class TestNullPropagation:
    """Tests for NULL propagation in expressions."""

    def test_null_in_arithmetic_propagates(self, simple_graph):
        """NULL in arithmetic expression propagates."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Charlie'})
            RETURN n.age + 10 AS result
        """)

        # Charlie has NULL age, arithmetic should propagate NULL
        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["result"], CypherNull)

    def test_null_with_string_function(self, simple_graph):
        """NULL with string function returns NULL."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN UPPER(n.city) AS city_upper
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["city_upper"], CypherNull)

    def test_null_with_type_conversion(self, simple_graph):
        """NULL with type conversion returns NULL."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Charlie'})
            RETURN toString(n.age) AS age_str
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["age_str"], CypherNull)


@pytest.mark.integration
class TestNullEdgeCases:
    """Tests for NULL edge cases."""

    def test_coalesce_with_multiple_args(self, simple_graph):
        """COALESCE with many arguments."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN COALESCE(n.missing1, n.missing2, n.city, n.name, 'Final') AS value
        """)

        # Should skip NULL values and return name "Bob"
        assert len(results) == 1
        assert results[0]["value"].value == "Bob"

    def test_null_property_access_returns_null(self, simple_graph):
        """Accessing missing property returns NULL."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN n.nonexistent AS value
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["value"], CypherNull)

    def test_coalesce_with_expressions(self, simple_graph):
        """COALESCE with computed expressions."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN COALESCE(n.nickname, UPPER(n.name)) AS display_name
        """)

        # nickname is NULL, so use UPPER(name)
        assert len(results) == 1
        assert results[0]["display_name"].value == "ALICE"
