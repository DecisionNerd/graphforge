"""Integration tests for XOR logical operator.

Tests for XOR operator with basic combinations, NULL propagation,
precedence with AND/OR, WHERE clauses, and chained XOR.
"""

import pytest

from graphforge import GraphForge
from graphforge.types.values import CypherNull


@pytest.fixture
def simple_graph():
    """Create a simple graph for testing XOR operator."""
    gf = GraphForge()

    gf.create_node(["Person"], name="Alice", age=30, active=True)
    gf.create_node(["Person"], name="Bob", age=25, active=False)
    gf.create_node(["Person"], name="Charlie", age=35)  # Missing active

    return gf


@pytest.mark.integration
class TestXorBasicCombinations:
    """Tests for basic XOR truth table."""

    def test_true_xor_true(self):
        """true XOR true = false."""
        gf = GraphForge()
        results = gf.execute("RETURN true XOR true AS result")
        assert len(results) == 1
        assert results[0]["result"].value is False

    def test_true_xor_false(self):
        """true XOR false = true."""
        gf = GraphForge()
        results = gf.execute("RETURN true XOR false AS result")
        assert len(results) == 1
        assert results[0]["result"].value is True

    def test_false_xor_true(self):
        """false XOR true = true."""
        gf = GraphForge()
        results = gf.execute("RETURN false XOR true AS result")
        assert len(results) == 1
        assert results[0]["result"].value is True

    def test_false_xor_false(self):
        """false XOR false = false."""
        gf = GraphForge()
        results = gf.execute("RETURN false XOR false AS result")
        assert len(results) == 1
        assert results[0]["result"].value is False


@pytest.mark.integration
class TestXorNullHandling:
    """Tests for XOR with NULL operands."""

    def test_true_xor_null(self):
        """true XOR null = null."""
        gf = GraphForge()
        results = gf.execute("RETURN true XOR null AS result")
        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherNull)

    def test_false_xor_null(self):
        """false XOR null = null."""
        gf = GraphForge()
        results = gf.execute("RETURN false XOR null AS result")
        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherNull)

    def test_null_xor_true(self):
        """null XOR true = null."""
        gf = GraphForge()
        results = gf.execute("RETURN null XOR true AS result")
        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherNull)

    def test_null_xor_false(self):
        """null XOR false = null."""
        gf = GraphForge()
        results = gf.execute("RETURN null XOR false AS result")
        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherNull)

    def test_null_xor_null(self):
        """null XOR null = null."""
        gf = GraphForge()
        results = gf.execute("RETURN null XOR null AS result")
        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherNull)


@pytest.mark.integration
class TestXorWithProperties:
    """Tests for XOR with node properties."""

    def test_xor_in_where_clause(self, simple_graph):
        """XOR in WHERE filters correctly."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE n.active XOR (n.age > 30)
            RETURN n.name AS name
        """)

        # Alice: true XOR false = true (included)
        # Bob: false XOR false = false (excluded)
        # Charlie: NULL XOR true = NULL (excluded by WHERE)
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_xor_in_return(self, simple_graph):
        """XOR can be used in RETURN clause."""
        results = simple_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN n.active XOR (n.age > 30) AS result
        """)

        # Alice: true XOR false = true
        assert len(results) == 1
        assert results[0]["result"].value is True

    def test_xor_null_property_filtered(self, simple_graph):
        """XOR with NULL property is filtered out in WHERE."""
        results = simple_graph.execute("""
            MATCH (n:Person)
            WHERE n.active XOR true
            RETURN n.name AS name
        """)

        # Alice: true XOR true = false (excluded)
        # Bob: false XOR true = true (included)
        # Charlie: NULL XOR true = NULL (excluded by WHERE)
        assert len(results) == 1
        assert results[0]["name"].value == "Bob"


@pytest.mark.integration
class TestXorPrecedence:
    """Tests for XOR precedence: NOT > AND > XOR > OR."""

    def test_xor_lower_than_and(self):
        """AND binds tighter than XOR: true XOR true AND false = true XOR false = true."""
        gf = GraphForge()
        results = gf.execute("RETURN true XOR true AND false AS result")
        # Parses as: true XOR (true AND false) = true XOR false = true
        assert len(results) == 1
        assert results[0]["result"].value is True

    def test_xor_higher_than_or(self):
        """XOR binds tighter than OR: false OR true XOR true = false OR false = false."""
        gf = GraphForge()
        results = gf.execute("RETURN false OR true XOR true AS result")
        # Parses as: false OR (true XOR true) = false OR false = false
        assert len(results) == 1
        assert results[0]["result"].value is False

    def test_not_higher_than_xor(self):
        """NOT binds tighter than XOR: NOT true XOR false = false XOR false = false."""
        gf = GraphForge()
        results = gf.execute("RETURN NOT true XOR false AS result")
        # Parses as: (NOT true) XOR false = false XOR false = false
        assert len(results) == 1
        assert results[0]["result"].value is False

    def test_parentheses_override_precedence(self):
        """Parentheses override natural precedence."""
        gf = GraphForge()
        results = gf.execute("RETURN true XOR (true AND false) AS result")
        # true XOR false = true
        assert len(results) == 1
        assert results[0]["result"].value is True

    def test_complex_precedence(self):
        """Complex expression with all logical operators."""
        gf = GraphForge()
        results = gf.execute("RETURN true AND false XOR true OR false AS result")
        # Parses as: ((true AND false) XOR true) OR false
        # = (false XOR true) OR false
        # = true OR false
        # = true
        assert len(results) == 1
        assert results[0]["result"].value is True


@pytest.mark.integration
class TestXorChained:
    """Tests for chained XOR (left-associative)."""

    def test_chained_xor_three(self):
        """Chained XOR: true XOR true XOR true = (true XOR true) XOR true = false XOR true = true."""
        gf = GraphForge()
        results = gf.execute("RETURN true XOR true XOR true AS result")
        assert len(results) == 1
        assert results[0]["result"].value is True

    def test_chained_xor_four(self):
        """Chained XOR with four operands."""
        gf = GraphForge()
        results = gf.execute("RETURN true XOR true XOR true XOR true AS result")
        # ((true XOR true) XOR true) XOR true
        # = (false XOR true) XOR true
        # = true XOR true
        # = false
        assert len(results) == 1
        assert results[0]["result"].value is False

    def test_chained_xor_with_null(self):
        """Chained XOR with NULL propagates."""
        gf = GraphForge()
        results = gf.execute("RETURN true XOR null XOR false AS result")
        # (true XOR null) XOR false = null XOR false = null
        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherNull)


@pytest.mark.integration
class TestXorCaseInsensitive:
    """Tests for case insensitivity of XOR keyword."""

    def test_xor_lowercase(self):
        """XOR keyword is case-insensitive (lowercase)."""
        gf = GraphForge()
        results = gf.execute("RETURN true xor false AS result")
        assert results[0]["result"].value is True

    def test_xor_mixed_case(self):
        """XOR keyword is case-insensitive (mixed case)."""
        gf = GraphForge()
        results = gf.execute("RETURN true Xor false AS result")
        assert results[0]["result"].value is True
