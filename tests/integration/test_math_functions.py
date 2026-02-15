"""Unit tests for math functions (abs, ceil, floor, round, sign)."""

import pytest

from graphforge.api import GraphForge


@pytest.fixture
def gf():
    """Create a fresh GraphForge instance."""
    return GraphForge()


class TestAbsFunction:
    """Tests for ABS() function."""

    def test_abs_positive_int(self, gf):
        """ABS of positive integer returns same value."""
        result = gf.execute("RETURN abs(5) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 5

    def test_abs_negative_int(self, gf):
        """ABS of negative integer returns positive value."""
        result = gf.execute("RETURN abs(-5) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 5

    def test_abs_zero(self, gf):
        """ABS of zero returns zero."""
        result = gf.execute("RETURN abs(0) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 0

    def test_abs_positive_float(self, gf):
        """ABS of positive float returns same value."""
        result = gf.execute("RETURN abs(5.5) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 5.5

    def test_abs_negative_float(self, gf):
        """ABS of negative float returns positive value."""
        result = gf.execute("RETURN abs(-5.5) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 5.5

    def test_abs_null(self, gf):
        """ABS of NULL returns NULL."""
        result = gf.execute("RETURN abs(null) AS result")
        assert len(result) == 1
        assert result[0]["result"].value is None

    def test_abs_invalid_type(self, gf):
        """ABS of non-numeric type raises TypeError."""
        with pytest.raises(TypeError, match="ABS expects numeric argument"):
            gf.execute("RETURN abs('hello') AS result")


class TestCeilFunction:
    """Tests for CEIL() function."""

    def test_ceil_float_up(self, gf):
        """CEIL of float rounds up to integer."""
        result = gf.execute("RETURN ceil(5.3) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 6

    def test_ceil_float_exact(self, gf):
        """CEIL of exact float returns integer."""
        result = gf.execute("RETURN ceil(5.0) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 5

    def test_ceil_negative_float(self, gf):
        """CEIL of negative float rounds toward zero."""
        result = gf.execute("RETURN ceil(-5.3) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == -5

    def test_ceil_integer(self, gf):
        """CEIL of integer returns same integer."""
        result = gf.execute("RETURN ceil(5) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 5

    def test_ceil_null(self, gf):
        """CEIL of NULL returns NULL."""
        result = gf.execute("RETURN ceil(null) AS result")
        assert len(result) == 1
        assert result[0]["result"].value is None


class TestFloorFunction:
    """Tests for FLOOR() function."""

    def test_floor_float_down(self, gf):
        """FLOOR of float rounds down to integer."""
        result = gf.execute("RETURN floor(5.7) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 5

    def test_floor_float_exact(self, gf):
        """FLOOR of exact float returns integer."""
        result = gf.execute("RETURN floor(5.0) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 5

    def test_floor_negative_float(self, gf):
        """FLOOR of negative float rounds away from zero."""
        result = gf.execute("RETURN floor(-5.3) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == -6

    def test_floor_integer(self, gf):
        """FLOOR of integer returns same integer."""
        result = gf.execute("RETURN floor(5) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 5

    def test_floor_null(self, gf):
        """FLOOR of NULL returns NULL."""
        result = gf.execute("RETURN floor(null) AS result")
        assert len(result) == 1
        assert result[0]["result"].value is None


class TestRoundFunction:
    """Tests for ROUND() function."""

    def test_round_float_no_precision(self, gf):
        """ROUND without precision rounds to nearest integer."""
        result = gf.execute("RETURN round(5.5) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 6.0

    def test_round_float_down(self, gf):
        """ROUND rounds down when < 0.5."""
        result = gf.execute("RETURN round(5.3) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 5.0

    def test_round_float_up(self, gf):
        """ROUND rounds up when >= 0.5."""
        result = gf.execute("RETURN round(5.7) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 6.0

    def test_round_with_precision(self, gf):
        """ROUND with precision rounds to decimal places."""
        result = gf.execute("RETURN round(5.567, 2) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 5.57

    def test_round_with_zero_precision(self, gf):
        """ROUND with precision 0 rounds to integer."""
        result = gf.execute("RETURN round(5.567, 0) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 6.0

    def test_round_negative_precision(self, gf):
        """ROUND with negative precision rounds to tens, hundreds, etc."""
        result = gf.execute("RETURN round(1234, -2) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 1200

    def test_round_integer(self, gf):
        """ROUND of integer returns same integer."""
        result = gf.execute("RETURN round(5) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 5

    def test_round_null(self, gf):
        """ROUND of NULL returns NULL."""
        result = gf.execute("RETURN round(null) AS result")
        assert len(result) == 1
        assert result[0]["result"].value is None


class TestSignFunction:
    """Tests for SIGN() function."""

    def test_sign_positive_int(self, gf):
        """SIGN of positive integer returns 1."""
        result = gf.execute("RETURN sign(5) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 1

    def test_sign_negative_int(self, gf):
        """SIGN of negative integer returns -1."""
        result = gf.execute("RETURN sign(-5) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == -1

    def test_sign_zero(self, gf):
        """SIGN of zero returns 0."""
        result = gf.execute("RETURN sign(0) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 0

    def test_sign_positive_float(self, gf):
        """SIGN of positive float returns 1."""
        result = gf.execute("RETURN sign(5.5) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 1

    def test_sign_negative_float(self, gf):
        """SIGN of negative float returns -1."""
        result = gf.execute("RETURN sign(-5.5) AS result")
        assert len(result) == 1
        assert result[0]["result"].value == -1

    def test_sign_null(self, gf):
        """SIGN of NULL returns NULL."""
        result = gf.execute("RETURN sign(null) AS result")
        assert len(result) == 1
        assert result[0]["result"].value is None
