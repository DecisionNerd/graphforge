"""Integration tests for hexadecimal and octal integer literals (#247).

Tests end-to-end query execution with hex (0x/0X) and octal (0o/0O) integer literals.
"""

import pytest

from graphforge import GraphForge


@pytest.fixture
def gf():
    return GraphForge()


class TestHexLiteralsEndToEnd:
    """End-to-end tests for hexadecimal integer literals."""

    def test_return_hex_literal(self, gf):
        result = gf.execute("RETURN 0xFF AS n")
        assert result[0]["n"].value == 255

    def test_return_hex_zero(self, gf):
        result = gf.execute("RETURN 0x0 AS n")
        assert result[0]["n"].value == 0

    def test_return_negative_hex(self, gf):
        result = gf.execute("RETURN -0x1 AS n")
        assert result[0]["n"].value == -1

    def test_return_negative_hex_zero(self, gf):
        result = gf.execute("RETURN -0x0 AS n")
        assert result[0]["n"].value == 0

    def test_hex_upper_case_prefix(self, gf):
        result = gf.execute("RETURN 0XFF AS n")
        assert result[0]["n"].value == 255

    def test_hex_lower_case_digits(self, gf):
        result = gf.execute("RETURN 0x1a2b3c4d5e6f7 AS n")
        assert result[0]["n"].value == 460367961908983

    def test_hex_upper_case_digits(self, gf):
        result = gf.execute("RETURN 0x1A2B3C4D5E6F7 AS n")
        assert result[0]["n"].value == 460367961908983

    def test_hex_in_arithmetic(self, gf):
        """Hex literals work in arithmetic expressions."""
        result = gf.execute("RETURN 0x10 + 0x10 AS n")
        assert result[0]["n"].value == 32

    def test_hex_in_where_clause(self, gf):
        """Hex literals work in WHERE predicates."""
        gf.execute("CREATE (:Item {value: 255})")
        result = gf.execute("MATCH (i:Item) WHERE i.value = 0xFF RETURN i.value AS v")
        assert len(result) == 1
        assert result[0]["v"].value == 255

    def test_hex_in_property_creation(self, gf):
        """Hex literals work as property values in CREATE."""
        gf.execute("CREATE (:Config {flags: 0xA5})")
        result = gf.execute("MATCH (c:Config) RETURN c.flags AS f")
        assert result[0]["f"].value == 0xA5


class TestOctalLiteralsEndToEnd:
    """End-to-end tests for octal integer literals."""

    def test_return_octal_literal(self, gf):
        result = gf.execute("RETURN 0o17 AS n")
        assert result[0]["n"].value == 15

    def test_return_octal_zero(self, gf):
        result = gf.execute("RETURN 0o0 AS n")
        assert result[0]["n"].value == 0

    def test_return_negative_octal(self, gf):
        result = gf.execute("RETURN -0o1 AS n")
        assert result[0]["n"].value == -1

    def test_return_negative_octal_zero(self, gf):
        result = gf.execute("RETURN -0o0 AS n")
        assert result[0]["n"].value == 0

    def test_octal_upper_case_prefix(self, gf):
        result = gf.execute("RETURN 0O17 AS n")
        assert result[0]["n"].value == 15

    def test_octal_in_arithmetic(self, gf):
        result = gf.execute("RETURN 0o10 + 0o10 AS n")
        assert result[0]["n"].value == 16

    def test_octal_large_value(self, gf):
        result = gf.execute("RETURN 0o2613152366 AS n")
        assert result[0]["n"].value == 372036854


class TestIntegerOverflowEndToEnd:
    """INT64 overflow errors are surfaced at query execution time."""

    def test_hex_overflow_raises(self, gf):
        with pytest.raises(ValueError, match="[Oo]verflow"):
            gf.execute("RETURN 0x8000000000000000 AS n")

    def test_hex_underflow_raises(self, gf):
        with pytest.raises(ValueError, match="[Oo]verflow"):
            gf.execute("RETURN -0x8000000000000001 AS n")

    def test_octal_overflow_raises(self, gf):
        with pytest.raises(ValueError, match="[Oo]verflow"):
            gf.execute("RETURN 0o1000000000000000000000 AS n")

    def test_decimal_overflow_raises(self, gf):
        with pytest.raises(ValueError, match="[Oo]verflow"):
            gf.execute("RETURN 9223372036854775808 AS n")

    def test_int64_max_is_valid(self, gf):
        result = gf.execute("RETURN 9223372036854775807 AS n")
        assert result[0]["n"].value == 9223372036854775807

    def test_hex_int64_max_is_valid(self, gf):
        result = gf.execute("RETURN 0x7FFFFFFFFFFFFFFF AS n")
        assert result[0]["n"].value == 9223372036854775807

    def test_hex_int64_min_is_valid(self, gf):
        """The critical edge case: -0x8000000000000000 = INT64_MIN is valid."""
        result = gf.execute("RETURN -0x8000000000000000 AS n")
        assert result[0]["n"].value == -9223372036854775808
