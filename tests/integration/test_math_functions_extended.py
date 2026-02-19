"""Integration tests for sqrt(), rand(), pow() math functions."""

import pytest

from graphforge.api import GraphForge
from graphforge.types.values import CypherFloat, CypherNull


@pytest.fixture
def gf():
    """Create a fresh GraphForge instance."""
    return GraphForge()


class TestSqrtFunction:
    """Tests for SQRT() function."""

    def test_sqrt_perfect_square(self, gf):
        """SQRT of 4 returns 2.0."""
        result = gf.execute("RETURN sqrt(4) AS r")
        assert len(result) == 1
        assert isinstance(result[0]["r"], CypherFloat)
        assert result[0]["r"].value == 2.0

    def test_sqrt_irrational(self, gf):
        """SQRT of 2.0 returns approximately 1.4142."""
        result = gf.execute("RETURN sqrt(2.0) AS r")
        assert len(result) == 1
        assert isinstance(result[0]["r"], CypherFloat)
        assert abs(result[0]["r"].value - 1.4142135623730951) < 1e-10

    def test_sqrt_zero(self, gf):
        """SQRT of 0 returns 0.0."""
        result = gf.execute("RETURN sqrt(0) AS r")
        assert len(result) == 1
        assert isinstance(result[0]["r"], CypherFloat)
        assert result[0]["r"].value == 0.0

    def test_sqrt_one(self, gf):
        """SQRT of 1 returns 1.0."""
        result = gf.execute("RETURN sqrt(1) AS r")
        assert len(result) == 1
        assert isinstance(result[0]["r"], CypherFloat)
        assert result[0]["r"].value == 1.0

    def test_sqrt_negative(self, gf):
        """SQRT of negative number returns null."""
        result = gf.execute("RETURN sqrt(-1) AS r")
        assert len(result) == 1
        assert isinstance(result[0]["r"], CypherNull)

    def test_sqrt_null(self, gf):
        """SQRT of null returns null."""
        result = gf.execute("RETURN sqrt(null) AS r")
        assert len(result) == 1
        assert isinstance(result[0]["r"], CypherNull)

    def test_sqrt_large_number(self, gf):
        """SQRT of large number works correctly."""
        result = gf.execute("RETURN sqrt(10000) AS r")
        assert len(result) == 1
        assert result[0]["r"].value == 100.0


class TestRandFunction:
    """Tests for RAND() function."""

    def test_rand_returns_float(self, gf):
        """RAND returns a CypherFloat."""
        result = gf.execute("RETURN rand() AS r")
        assert len(result) == 1
        assert isinstance(result[0]["r"], CypherFloat)

    def test_rand_in_range(self, gf):
        """RAND returns value in [0.0, 1.0)."""
        result = gf.execute("RETURN rand() AS r")
        val = result[0]["r"].value
        assert 0.0 <= val < 1.0

    def test_rand_multiplied(self, gf):
        """RAND can be used in arithmetic expressions."""
        result = gf.execute("RETURN rand() * 100 AS r")
        assert len(result) == 1
        assert isinstance(result[0]["r"], CypherFloat)
        val = result[0]["r"].value
        assert 0.0 <= val < 100.0

    def test_rand_multiple_calls(self, gf):
        """Multiple RAND calls in same query produce independent results."""
        result = gf.execute("RETURN rand() AS r1, rand() AS r2")
        assert len(result) == 1
        assert isinstance(result[0]["r1"], CypherFloat)
        assert isinstance(result[0]["r2"], CypherFloat)


class TestPowFunction:
    """Tests for POW() function."""

    def test_pow_integer_exponent(self, gf):
        """POW(2, 3) returns 8."""
        result = gf.execute("RETURN pow(2, 3) AS r")
        assert len(result) == 1
        assert result[0]["r"].value == 8

    def test_pow_zero_exponent(self, gf):
        """POW(2, 0) returns 1."""
        result = gf.execute("RETURN pow(2, 0) AS r")
        assert len(result) == 1
        assert result[0]["r"].value == 1

    def test_pow_negative_exponent(self, gf):
        """POW(2, -1) returns 0.5."""
        result = gf.execute("RETURN pow(2, -1) AS r")
        assert len(result) == 1
        assert isinstance(result[0]["r"], CypherFloat)
        assert result[0]["r"].value == 0.5

    def test_pow_fractional_exponent(self, gf):
        """POW(4, 0.5) returns 2.0 (square root)."""
        result = gf.execute("RETURN pow(4, 0.5) AS r")
        assert len(result) == 1
        assert isinstance(result[0]["r"], CypherFloat)
        assert result[0]["r"].value == 2.0

    def test_pow_null_base(self, gf):
        """POW(null, 2) returns null."""
        result = gf.execute("RETURN pow(null, 2) AS r")
        assert len(result) == 1
        assert isinstance(result[0]["r"], CypherNull)

    def test_pow_null_exponent(self, gf):
        """POW(2, null) returns null."""
        result = gf.execute("RETURN pow(2, null) AS r")
        assert len(result) == 1
        assert isinstance(result[0]["r"], CypherNull)

    def test_pow_equivalence_with_caret(self, gf):
        """POW(2, 3) equals 2^3."""
        result = gf.execute("RETURN pow(2, 3) = 2^3 AS r")
        assert len(result) == 1
        assert result[0]["r"].value is True

    def test_pow_one_exponent(self, gf):
        """POW(5, 1) returns 5."""
        result = gf.execute("RETURN pow(5, 1) AS r")
        assert len(result) == 1
        assert result[0]["r"].value == 5

    def test_pow_zero_base(self, gf):
        """POW(0, 5) returns 0."""
        result = gf.execute("RETURN pow(0, 5) AS r")
        assert len(result) == 1
        assert result[0]["r"].value == 0
