"""Integration tests for arithmetic operators (issue #26).

Tests for +, -, *, /, % operators with proper precedence, type coercion, and NULL handling.
"""

import pytest

from graphforge import GraphForge
from graphforge.types.values import CypherFloat, CypherNull, CypherString


class TestBasicArithmetic:
    """Tests for basic arithmetic operations."""

    def test_addition(self):
        """Test addition operator."""
        gf = GraphForge()
        results = gf.execute("RETURN 2 + 3 AS result")

        assert len(results) == 1
        assert results[0]["result"].value == 5

    def test_subtraction(self):
        """Test subtraction operator."""
        gf = GraphForge()
        results = gf.execute("RETURN 10 - 3 AS result")

        assert len(results) == 1
        assert results[0]["result"].value == 7

    def test_multiplication(self):
        """Test multiplication operator."""
        gf = GraphForge()
        results = gf.execute("RETURN 4 * 5 AS result")

        assert len(results) == 1
        assert results[0]["result"].value == 20

    def test_division(self):
        """Test division operator (always returns float)."""
        gf = GraphForge()
        results = gf.execute("RETURN 10 / 2 AS result")

        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherFloat)
        assert results[0]["result"].value == pytest.approx(5.0)

    def test_division_non_exact(self):
        """Test division with non-exact result."""
        gf = GraphForge()
        results = gf.execute("RETURN 7 / 2 AS result")

        assert len(results) == 1
        assert results[0]["result"].value == pytest.approx(3.5)

    def test_modulo(self):
        """Test modulo operator."""
        gf = GraphForge()
        results = gf.execute("RETURN 10 % 3 AS result")

        assert len(results) == 1
        assert results[0]["result"].value == 1

    def test_unary_minus(self):
        """Test unary minus."""
        gf = GraphForge()
        results = gf.execute("RETURN -5 AS result")

        assert len(results) == 1
        assert results[0]["result"].value == -5


class TestTypeCoercion:
    """Tests for type coercion in arithmetic."""

    def test_int_plus_float(self):
        """Int + Float returns Float."""
        gf = GraphForge()
        results = gf.execute("RETURN 2 + 3.5 AS result")

        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherFloat)
        assert results[0]["result"].value == pytest.approx(5.5)

    def test_float_times_int(self):
        """Float * Int returns Float."""
        gf = GraphForge()
        results = gf.execute("RETURN 2.5 * 4 AS result")

        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherFloat)
        assert results[0]["result"].value == pytest.approx(10.0)

    def test_int_minus_float(self):
        """Int - Float returns Float."""
        gf = GraphForge()
        results = gf.execute("RETURN 10 - 2.5 AS result")

        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherFloat)
        assert results[0]["result"].value == pytest.approx(7.5)


class TestOperatorPrecedence:
    """Tests for operator precedence."""

    def test_multiplication_before_addition(self):
        """Multiplication has higher precedence than addition."""
        gf = GraphForge()
        results = gf.execute("RETURN 2 + 3 * 4 AS result")

        assert len(results) == 1
        # Should be 2 + (3 * 4) = 2 + 12 = 14
        assert results[0]["result"].value == 14

    def test_division_before_subtraction(self):
        """Division has higher precedence than subtraction."""
        gf = GraphForge()
        results = gf.execute("RETURN 10 - 6 / 2 AS result")

        assert len(results) == 1
        # Should be 10 - (6 / 2) = 10 - 3.0 = 7.0
        assert results[0]["result"].value == pytest.approx(7.0)

    def test_unary_minus_precedence(self):
        """Unary minus has higher precedence than binary operators."""
        gf = GraphForge()
        results = gf.execute("RETURN -2 * 3 AS result")

        assert len(results) == 1
        # Should be (-2) * 3 = -6
        assert results[0]["result"].value == -6

    def test_complex_expression(self):
        """Test complex expression with multiple operators."""
        gf = GraphForge()
        results = gf.execute("RETURN 2 + 3 * 4 - 10 / 2 AS result")

        assert len(results) == 1
        # Should be 2 + (3 * 4) - (10 / 2) = 2 + 12 - 5.0 = 9.0
        assert results[0]["result"].value == pytest.approx(9.0)

    def test_left_associativity(self):
        """Test left associativity of operators."""
        gf = GraphForge()
        results = gf.execute("RETURN 10 - 3 - 2 AS result")

        assert len(results) == 1
        # Should be (10 - 3) - 2 = 7 - 2 = 5
        assert results[0]["result"].value == 5


class TestNullHandling:
    """Tests for NULL handling in arithmetic."""

    def test_null_plus_number(self):
        """NULL + number returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (n:Node {val: null})")
        results = gf.execute("MATCH (n:Node) RETURN n.val + 5 AS result")

        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherNull)

    def test_number_minus_null(self):
        """number - NULL returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (n:Node {val: null})")
        results = gf.execute("MATCH (n:Node) RETURN 10 - n.val AS result")

        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherNull)

    def test_null_times_number(self):
        """NULL * number returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (n:Node {val: null})")
        results = gf.execute("MATCH (n:Node) RETURN n.val * 3 AS result")

        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherNull)

    def test_unary_minus_null(self):
        """Unary minus on NULL returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (n:Node {val: null})")
        results = gf.execute("MATCH (n:Node) RETURN -n.val AS result")

        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherNull)


class TestEdgeCases:
    """Tests for edge cases."""

    def test_division_by_zero(self):
        """Division by zero returns NULL."""
        gf = GraphForge()
        results = gf.execute("RETURN 10 / 0 AS result")

        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherNull)

    def test_modulo_by_zero(self):
        """Modulo by zero returns NULL."""
        gf = GraphForge()
        results = gf.execute("RETURN 10 % 0 AS result")

        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherNull)

    def test_string_concatenation(self):
        """String concatenation with + operator."""
        gf = GraphForge()
        results = gf.execute("RETURN 'Hello ' + 'World' AS result")

        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherString)
        assert results[0]["result"].value == "Hello World"

    def test_string_plus_number(self):
        """String concatenation with number."""
        gf = GraphForge()
        results = gf.execute("RETURN 'Age: ' + 30 AS result")

        assert len(results) == 1
        assert isinstance(results[0]["result"], CypherString)
        assert results[0]["result"].value == "Age: 30"


class TestArithmeticWithProperties:
    """Tests for arithmetic with node properties."""

    def test_addition_with_property(self):
        """Arithmetic with node property."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {age: 25})")
        results = gf.execute("MATCH (p:Person) RETURN p.age + 5 AS new_age")

        assert len(results) == 1
        assert results[0]["new_age"].value == 30

    def test_multiplication_with_property(self):
        """Multiplication with node property."""
        gf = GraphForge()
        gf.execute("CREATE (p:Product {price: 10.0})")
        results = gf.execute("MATCH (p:Product) RETURN p.price * 2 AS doubled")

        assert len(results) == 1
        assert results[0]["doubled"].value == pytest.approx(20.0)

    def test_arithmetic_in_where_clause(self):
        """Arithmetic in WHERE clause."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {age: 25}),
                   (b:Person {age: 30}),
                   (c:Person {age: 35})
        """)
        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.age + 5 > 30
            RETURN p.age AS age
            ORDER BY age
        """)

        assert len(results) == 2
        assert results[0]["age"].value == 30
        assert results[1]["age"].value == 35

    def test_complex_property_arithmetic(self):
        """Complex arithmetic with multiple properties."""
        gf = GraphForge()
        gf.execute("CREATE (p:Product {price: 10.0, quantity: 3})")
        results = gf.execute("""
            MATCH (p:Product)
            RETURN p.price * p.quantity AS total
        """)

        assert len(results) == 1
        assert results[0]["total"].value == pytest.approx(30.0)


class TestArithmeticWithMultipleNodes:
    """Tests for arithmetic across multiple nodes."""

    def test_sum_multiple_values(self):
        """Arithmetic with multiple nodes."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {value: 10}),
                   (b:Item {value: 20}),
                   (c:Item {value: 30})
        """)
        results = gf.execute("""
            MATCH (i:Item)
            RETURN i.value * 2 AS doubled
            ORDER BY doubled
        """)

        assert len(results) == 3
        assert results[0]["doubled"].value == 20
        assert results[1]["doubled"].value == 40
        assert results[2]["doubled"].value == 60

    def test_filter_with_arithmetic(self):
        """Filter nodes with arithmetic in WHERE."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {salary: 40000}),
                   (b:Person {salary: 60000}),
                   (c:Person {salary: 80000})
        """)
        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.salary / 1000 > 50
            RETURN p.salary AS salary
            ORDER BY salary
        """)

        assert len(results) == 2
        assert results[0]["salary"].value == 60000
        assert results[1]["salary"].value == 80000


class TestArithmeticWithAggregations:
    """Tests for arithmetic with aggregation functions."""

    def test_arithmetic_before_aggregation(self):
        """Arithmetic before aggregation."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {price: 10}),
                   (b:Item {price: 20}),
                   (c:Item {price: 30})
        """)
        results = gf.execute("""
            MATCH (i:Item)
            RETURN SUM(i.price * 2) AS total
        """)

        assert len(results) == 1
        assert results[0]["total"].value == 120
