"""Integration tests for string functions (Feature 2).

Tests for LENGTH, SUBSTRING, UPPER, LOWER, and TRIM functions.
"""

import pytest

from graphforge import GraphForge


@pytest.fixture
def simple_graph():
    """Create a simple graph with string properties for testing."""
    gf = GraphForge()

    # Create nodes with various string properties
    gf.create_node(["Person"], name="Alice", title="  Senior Engineer  ")
    gf.create_node(["Person"], name="Bob", title="Junior Developer")
    gf.create_node(["Person"], name="Charlie Brown", title="")

    return gf


@pytest.mark.integration
class TestLengthFunction:
    """Tests for LENGTH() function."""

    def test_length_function_basic(self, simple_graph):
        """LENGTH returns string length."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN LENGTH(n.name) AS len
        """)

        assert len(results) == 1
        assert results[0]["len"].value == 5

    def test_length_function_in_where(self, simple_graph):
        """LENGTH can be used in WHERE clause."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE LENGTH(n.name) > 5
            RETURN n.name AS name
        """)

        # Only "Charlie Brown" has name length > 5
        assert len(results) == 1
        assert results[0]["name"].value == "Charlie Brown"

    def test_length_function_with_null(self, simple_graph):
        """LENGTH with NULL property returns NULL."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN LENGTH(n.missing_property) AS len
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["len"], CypherNull)


@pytest.mark.integration
class TestSubstringFunction:
    """Tests for SUBSTRING() function."""

    def test_substring_two_args(self, simple_graph):
        """SUBSTRING with start index."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN SUBSTRING(n.name, 1) AS sub
        """)

        assert len(results) == 1
        assert results[0]["sub"].value == "lice"

    def test_substring_three_args(self, simple_graph):
        """SUBSTRING with start and length."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN SUBSTRING(n.name, 0, 2) AS sub
        """)

        assert len(results) == 1
        assert results[0]["sub"].value == "Al"

    def test_substring_full_name(self, simple_graph):
        """SUBSTRING extracts first and last name."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Charlie Brown'})
            RETURN
                SUBSTRING(n.name, 0, 7) AS first,
                SUBSTRING(n.name, 8) AS last
        """)

        assert len(results) == 1
        assert results[0]["first"].value == "Charlie"
        assert results[0]["last"].value == "Brown"

    def test_substring_with_null(self, simple_graph):
        """SUBSTRING with NULL returns NULL."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN SUBSTRING(n.missing, 0, 2) AS sub
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["sub"], CypherNull)


@pytest.mark.integration
class TestUpperFunction:
    """Tests for UPPER() function."""

    def test_upper_function_basic(self, simple_graph):
        """UPPER converts to uppercase."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN UPPER(n.name) AS upper_name
        """)

        assert len(results) == 1
        assert results[0]["upper_name"].value == "ALICE"

    def test_upper_function_multiple(self, simple_graph):
        """UPPER works on multiple rows."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE n.name = 'Alice' OR n.name = 'Bob'
            RETURN UPPER(n.name) AS upper_name
        """)

        assert len(results) == 2
        names = {results[0]["upper_name"].value, results[1]["upper_name"].value}
        assert names == {"ALICE", "BOB"}

    def test_upper_with_null(self, simple_graph):
        """UPPER with NULL returns NULL."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN UPPER(n.missing) AS result
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["result"], CypherNull)


@pytest.mark.integration
class TestLowerFunction:
    """Tests for LOWER() function."""

    def test_lower_function_basic(self, simple_graph):
        """LOWER converts to lowercase."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN LOWER(n.name) AS lower_name
        """)

        assert len(results) == 1
        assert results[0]["lower_name"].value == "bob"

    def test_lower_function_title(self, simple_graph):
        """LOWER works on title field."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN LOWER(n.title) AS lower_title
        """)

        assert len(results) == 1
        assert results[0]["lower_title"].value == "junior developer"

    def test_lower_with_null(self, simple_graph):
        """LOWER with NULL returns NULL."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN LOWER(n.missing) AS result
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["result"], CypherNull)


@pytest.mark.integration
class TestTrimFunction:
    """Tests for TRIM() function."""

    def test_trim_function_basic(self, simple_graph):
        """TRIM removes leading/trailing whitespace."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN TRIM(n.title) AS trimmed
        """)

        assert len(results) == 1
        assert results[0]["trimmed"].value == "Senior Engineer"

    def test_trim_function_no_whitespace(self, simple_graph):
        """TRIM on string without whitespace returns unchanged."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN TRIM(n.title) AS trimmed
        """)

        assert len(results) == 1
        assert results[0]["trimmed"].value == "Junior Developer"

    def test_trim_with_null(self, simple_graph):
        """TRIM with NULL returns NULL."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN TRIM(n.missing) AS result
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["result"], CypherNull)


@pytest.mark.integration
class TestStringFunctionsCombined:
    """Tests combining multiple string functions."""

    def test_nested_string_functions(self, simple_graph):
        """String functions can be nested."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN UPPER(TRIM(n.title)) AS result
        """)

        assert len(results) == 1
        assert results[0]["result"].value == "SENIOR ENGINEER"

    def test_substring_of_lower(self, simple_graph):
        """SUBSTRING of LOWER result."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Charlie Brown'})
            RETURN SUBSTRING(LOWER(n.name), 0, 7) AS result
        """)

        assert len(results) == 1
        assert results[0]["result"].value == "charlie"

    def test_length_of_trim(self, simple_graph):
        """LENGTH of TRIM result."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN LENGTH(TRIM(n.title)) AS len
        """)

        assert len(results) == 1
        assert results[0]["len"].value == 15  # "Senior Engineer" without spaces
