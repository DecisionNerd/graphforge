"""Unit tests for hexadecimal and octal integer literal parsing (#247).

Tests that the parser correctly handles 0x/0X hex and 0o/0O octal prefixes,
including INT64 overflow detection.
"""

import pytest

from graphforge.ast.expression import Literal
from graphforge.parser.parser import CypherParser


@pytest.fixture
def parser():
    return CypherParser()


def parse_return_literal(parser, expr):
    """Parse 'RETURN <expr> AS n' and return the Literal node."""
    ast = parser.parse(f"RETURN {expr} AS n")
    return_clause = ast.clauses[-1]
    return return_clause.items[0].expression


@pytest.mark.unit
class TestHexadecimalLiterals:
    """Hexadecimal integer literal parsing."""

    @pytest.mark.parametrize(
        "hex_str,expected",
        [
            ("0x1", 1),
            ("0x0", 0),
            ("0xFF", 255),
            ("0x162CD4F6", 372036854),
            ("0x7FFFFFFFFFFFFFFF", 9223372036854775807),
            ("0x1a2b3c4d5e6f7", 460367961908983),
            ("0x1A2B3C4D5E6F7", 460367961908983),
            ("0x1A2b3c4D5E6f7", 460367961908983),
        ],
    )
    def test_hex_positive_values(self, parser, hex_str, expected):
        lit = parse_return_literal(parser, hex_str)
        assert isinstance(lit, Literal)
        assert lit.value == expected

    def test_hex_upper_case_prefix(self, parser):
        lit = parse_return_literal(parser, "0X1A")
        assert isinstance(lit, Literal)
        assert lit.value == 26

    def test_hex_in_property(self, parser):
        """Hex literals work in node property contexts."""
        ast = parser.parse("MATCH (n {score: 0xFF}) RETURN n")
        node = ast.clauses[0].patterns[0]["parts"][0]
        assert node.properties["score"].value == 255


@pytest.mark.unit
class TestOctalLiterals:
    """Octal integer literal parsing."""

    @pytest.mark.parametrize(
        "oct_str,expected",
        [
            ("0o1", 1),
            ("0o0", 0),
            ("0o2613152366", 372036854),
            ("0o777777777777777777777", 9223372036854775807),
        ],
    )
    def test_octal_positive_values(self, parser, oct_str, expected):
        lit = parse_return_literal(parser, oct_str)
        assert isinstance(lit, Literal)
        assert lit.value == expected

    def test_octal_upper_case_prefix(self, parser):
        lit = parse_return_literal(parser, "0O17")
        assert isinstance(lit, Literal)
        assert lit.value == 15


@pytest.mark.unit
class TestIntegerOverflow:
    """INT64 overflow is caught at evaluation time (not parse time).

    The parser stores raw Python big-int values in the AST. Overflow detection
    happens in the evaluator. See integration tests for the full overflow tests.

    These unit tests only verify that the parser correctly parses out-of-range
    literals into their correct Python big-int AST values.
    """

    @pytest.mark.parametrize(
        "expr,expected_raw",
        [
            # These are INT64_MAX + 1 - valid as Python ints in the AST
            ("0x8000000000000000", 9223372036854775808),
            ("0o1000000000000000000000", 9223372036854775808),
            ("9223372036854775808", 9223372036854775808),
        ],
    )
    def test_out_of_range_parses_to_big_int(self, parser, expr, expected_raw):
        """Parser stores raw Python big-int; overflow is caught by the evaluator."""
        lit = parse_return_literal(parser, expr)
        assert isinstance(lit, Literal)
        assert lit.value == expected_raw

    def test_max_int64_parses_correctly(self, parser):
        """9223372036854775807 == 0x7FFFFFFFFFFFFFFF is exactly INT64_MAX."""
        lit = parse_return_literal(parser, "9223372036854775807")
        assert lit.value == 9223372036854775807

    def test_hex_max_int64_parses_correctly(self, parser):
        lit = parse_return_literal(parser, "0x7FFFFFFFFFFFFFFF")
        assert lit.value == 9223372036854775807

    def test_octal_max_int64_parses_correctly(self, parser):
        lit = parse_return_literal(parser, "0o777777777777777777777")
        assert lit.value == 9223372036854775807


@pytest.mark.unit
class TestDecimalLiteralsUnchanged:
    """Existing decimal integer parsing is unaffected."""

    @pytest.mark.parametrize("value", [0, 1, 42, 100, 9223372036854775807])
    def test_decimal_integers(self, parser, value):
        lit = parse_return_literal(parser, str(value))
        assert isinstance(lit, Literal)
        assert lit.value == value
