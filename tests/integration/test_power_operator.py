"""Integration tests for ^ (power/exponentiation) arithmetic operator.

Tests for basic exponentiation, right-associativity, precedence,
negative and fractional exponents, NULL handling, type coercion,
and usage in WHERE clauses.
"""

import pytest

from graphforge import GraphForge
from graphforge.types.values import CypherFloat, CypherInt, CypherNull


@pytest.fixture
def gf():
    """Create a fresh GraphForge instance."""
    return GraphForge()


@pytest.fixture
def number_graph():
    """Create a graph with numeric data for testing power in queries."""
    gf = GraphForge()
    gf.create_node(["Number"], name="two", value=2)
    gf.create_node(["Number"], name="three", value=3)
    gf.create_node(["Number"], name="four", value=4)
    gf.create_node(["Number"], name="ten", value=10)
    return gf


@pytest.mark.integration
class TestPowerBasic:
    """Basic power operator tests."""

    def test_two_cubed(self, gf):
        """2^3 = 8."""
        result = gf.execute("RETURN 2^3 AS result")
        assert result[0]["result"].value == 8

    def test_three_squared(self, gf):
        """3^2 = 9."""
        result = gf.execute("RETURN 3^2 AS result")
        assert result[0]["result"].value == 9

    def test_power_of_one(self, gf):
        """n^1 = n."""
        result = gf.execute("RETURN 5^1 AS result")
        assert result[0]["result"].value == 5

    def test_power_of_zero(self, gf):
        """n^0 = 1."""
        result = gf.execute("RETURN 5^0 AS result")
        assert result[0]["result"].value == 1

    def test_zero_to_power(self, gf):
        """0^n = 0 for positive n."""
        result = gf.execute("RETURN 0^5 AS result")
        assert result[0]["result"].value == 0

    def test_one_to_any_power(self, gf):
        """1^n = 1 for any n."""
        result = gf.execute("RETURN 1^100 AS result")
        assert result[0]["result"].value == 1

    def test_large_exponent(self, gf):
        """Test larger exponents."""
        result = gf.execute("RETURN 2^10 AS result")
        assert result[0]["result"].value == 1024


@pytest.mark.integration
class TestPowerRightAssociativity:
    """Right-associativity tests - THE critical feature."""

    def test_right_associative_basic(self, gf):
        """2^3^2 = 2^(3^2) = 2^9 = 512, NOT (2^3)^2 = 64."""
        result = gf.execute("RETURN 2^3^2 AS result")
        assert result[0]["result"].value == 512

    def test_right_associative_triple(self, gf):
        """2^2^2^2 = 2^(2^(2^2)) = 2^(2^4) = 2^16 = 65536."""
        result = gf.execute("RETURN 2^2^2^2 AS result")
        assert result[0]["result"].value == 65536

    def test_right_associative_with_parentheses_override(self, gf):
        """(2^3)^2 = 8^2 = 64 (parentheses override right-associativity)."""
        result = gf.execute("RETURN (2^3)^2 AS result")
        assert result[0]["result"].value == 64

    def test_right_associative_explicit_grouping(self, gf):
        """2^(3^2) = 2^9 = 512 (explicit right grouping, same as default)."""
        result = gf.execute("RETURN 2^(3^2) AS result")
        assert result[0]["result"].value == 512


@pytest.mark.integration
class TestPowerPrecedence:
    """Precedence tests - ^ should bind tighter than +, -, *, /."""

    def test_addition_with_power(self, gf):
        """2 + 3^2 = 2 + 9 = 11, NOT (2+3)^2 = 25."""
        result = gf.execute("RETURN 2 + 3^2 AS result")
        assert result[0]["result"].value == 11

    def test_subtraction_with_power(self, gf):
        """10 - 2^3 = 10 - 8 = 2."""
        result = gf.execute("RETURN 10 - 2^3 AS result")
        assert result[0]["result"].value == 2

    def test_multiplication_with_power(self, gf):
        """2 * 3^2 = 2 * 9 = 18, NOT (2*3)^2 = 36."""
        result = gf.execute("RETURN 2 * 3^2 AS result")
        assert result[0]["result"].value == 18

    def test_division_with_power(self, gf):
        """27 / 3^2 = 27 / 9 = 3.0."""
        result = gf.execute("RETURN 27 / 3^2 AS result")
        assert result[0]["result"].value == 3.0

    def test_complex_precedence(self, gf):
        """1 + 2 * 3^2 = 1 + 2*9 = 1 + 18 = 19."""
        result = gf.execute("RETURN 1 + 2 * 3^2 AS result")
        assert result[0]["result"].value == 19


@pytest.mark.integration
class TestPowerNegativeExponents:
    """Negative exponent tests."""

    def test_negative_exponent(self, gf):
        """2^-1 = 0.5."""
        result = gf.execute("RETURN 2^-1 AS result")
        assert result[0]["result"].value == 0.5
        assert isinstance(result[0]["result"], CypherFloat)

    def test_negative_exponent_squared(self, gf):
        """2^-2 = 0.25."""
        result = gf.execute("RETURN 2^-2 AS result")
        assert result[0]["result"].value == 0.25

    def test_negative_base_even_exponent(self, gf):
        """(-2)^2 = 4."""
        result = gf.execute("RETURN (-2)^2 AS result")
        assert result[0]["result"].value == 4

    def test_negative_base_odd_exponent(self, gf):
        """(-2)^3 = -8."""
        result = gf.execute("RETURN (-2)^3 AS result")
        assert result[0]["result"].value == -8


@pytest.mark.integration
class TestPowerFractionalExponents:
    """Fractional exponent tests (square roots, etc.)."""

    def test_square_root(self, gf):
        """4^0.5 = 2.0."""
        result = gf.execute("RETURN 4^0.5 AS result")
        assert result[0]["result"].value == 2.0
        assert isinstance(result[0]["result"], CypherFloat)

    def test_cube_root(self, gf):
        """27^(1.0/3.0) is approximately 3.0."""
        result = gf.execute("RETURN 27^(1.0/3.0) AS result")
        assert abs(result[0]["result"].value - 3.0) < 1e-10

    def test_float_base_int_exponent(self, gf):
        """2.5^2 = 6.25."""
        result = gf.execute("RETURN 2.5^2 AS result")
        assert result[0]["result"].value == 6.25
        assert isinstance(result[0]["result"], CypherFloat)

    def test_float_base_float_exponent(self, gf):
        """2.0^3.0 = 8.0."""
        result = gf.execute("RETURN 2.0^3.0 AS result")
        assert result[0]["result"].value == 8.0
        assert isinstance(result[0]["result"], CypherFloat)


@pytest.mark.integration
class TestPowerTypeCoercion:
    """Type coercion tests for power operator."""

    def test_int_int_returns_int(self, gf):
        """int^int with whole result returns CypherInt."""
        result = gf.execute("RETURN 2^3 AS result")
        assert isinstance(result[0]["result"], CypherInt)
        assert result[0]["result"].value == 8

    def test_int_negative_int_returns_float(self, gf):
        """int^(negative int) returns CypherFloat when result is fractional."""
        result = gf.execute("RETURN 2^-1 AS result")
        assert isinstance(result[0]["result"], CypherFloat)
        assert result[0]["result"].value == 0.5

    def test_float_int_returns_float(self, gf):
        """float^int returns CypherFloat."""
        result = gf.execute("RETURN 2.0^3 AS result")
        assert isinstance(result[0]["result"], CypherFloat)

    def test_int_float_returns_float(self, gf):
        """int^float returns CypherFloat."""
        result = gf.execute("RETURN 4^0.5 AS result")
        assert isinstance(result[0]["result"], CypherFloat)


@pytest.mark.integration
class TestPowerNullHandling:
    """NULL propagation tests."""

    def test_null_base(self, gf):
        """null^2 = null."""
        result = gf.execute("RETURN null^2 AS result")
        assert isinstance(result[0]["result"], CypherNull)

    def test_null_exponent(self, gf):
        """2^null = null."""
        result = gf.execute("RETURN 2^null AS result")
        assert isinstance(result[0]["result"], CypherNull)

    def test_null_both(self, gf):
        """null^null = null."""
        result = gf.execute("RETURN null^null AS result")
        assert isinstance(result[0]["result"], CypherNull)


@pytest.mark.integration
class TestPowerWithProperties:
    """Tests using power operator with node properties."""

    def test_power_with_property(self, number_graph):
        """Use property as base in power expression."""
        result = number_graph.execute(
            "MATCH (n:Number) WHERE n.name = 'two' RETURN n.value^3 AS result"
        )
        assert result[0]["result"].value == 8

    def test_power_in_where_clause(self, number_graph):
        """Use power in WHERE clause for filtering."""
        result = number_graph.execute(
            "MATCH (n:Number) WHERE n.value^2 > 5 RETURN n.name AS name ORDER BY name"
        )
        names = [r["name"].value for r in result]
        # 2^2=4 (no), 3^2=9 (yes), 4^2=16 (yes), 10^2=100 (yes)
        assert names == ["four", "ten", "three"]

    def test_power_with_two_properties(self, number_graph):
        """Use properties as both base and exponent."""
        result = number_graph.execute(
            "MATCH (a:Number), (b:Number) "
            "WHERE a.name = 'two' AND b.name = 'three' "
            "RETURN a.value^b.value AS result"
        )
        assert result[0]["result"].value == 8

    def test_power_in_return_expression(self, number_graph):
        """Use power in RETURN with alias."""
        result = number_graph.execute(
            "MATCH (n:Number) WHERE n.name = 'three' RETURN n.value^2 AS squared"
        )
        assert result[0]["squared"].value == 9


@pytest.mark.integration
class TestPowerEdgeCases:
    """Edge case tests."""

    def test_zero_to_zero(self, gf):
        """0^0 = 1 (mathematical convention)."""
        result = gf.execute("RETURN 0^0 AS result")
        assert result[0]["result"].value == 1

    def test_power_with_parentheses(self, gf):
        """Parenthesized expressions work correctly."""
        result = gf.execute("RETURN (2+1)^(1+1) AS result")
        assert result[0]["result"].value == 9

    def test_power_in_complex_expression(self, gf):
        """Power works in complex arithmetic expressions."""
        # (2^3 + 1) * 2 = (8 + 1) * 2 = 18
        result = gf.execute("RETURN (2^3 + 1) * 2 AS result")
        assert result[0]["result"].value == 18

    def test_power_with_unary_minus_base(self, gf):
        """Unary minus on the result of power: -2^3 = -(2^3) = -8."""
        result = gf.execute("RETURN -2^3 AS result")
        assert result[0]["result"].value == -8

    def test_zero_to_negative_power_returns_null(self, gf):
        """0^-1 should return NULL (division by zero)."""
        result = gf.execute("RETURN 0 ^ -1 AS result")
        assert isinstance(result[0]["result"], CypherNull)

    def test_unary_minus_lower_precedence_than_power(self, gf):
        """-1 ^ 0.5 parses as -(1 ^ 0.5) = -1.0, not (-1)^0.5."""
        # With correct precedence, power binds tighter than unary minus
        result = gf.execute("RETURN -1 ^ 0.5 AS result")
        assert result[0]["result"].value == -1.0

    def test_parenthesized_negative_base_fractional_exponent_returns_null(self, gf):
        """(-1)^0.5 should return NULL (complex result) when parenthesized."""
        result = gf.execute("RETURN (-1) ^ 0.5 AS result")
        assert isinstance(result[0]["result"], CypherNull)

    def test_float_overflow_returns_null(self, gf):
        """Float overflow should return NULL (result is inf)."""
        # 10.0 ^ 1000 will overflow to inf
        result = gf.execute("RETURN 10.0 ^ 1000 AS result")
        assert isinstance(result[0]["result"], CypherNull)
