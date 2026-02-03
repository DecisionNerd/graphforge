"""Unit tests for arithmetic operator parsing."""

from graphforge.ast.expression import BinaryOp, Literal, UnaryOp
from graphforge.parser.parser import parse_cypher


class TestArithmeticParser:
    """Tests for parsing arithmetic operators."""

    def test_parse_addition(self):
        """Parse addition operator."""
        query = "RETURN 1 + 2 AS result"
        ast = parse_cypher(query)

        return_clause = ast.clauses[0]
        expr = return_clause.items[0].expression

        assert isinstance(expr, BinaryOp)
        assert expr.op == "+"

    def test_parse_subtraction(self):
        """Parse subtraction operator."""
        query = "RETURN 5 - 3 AS result"
        ast = parse_cypher(query)

        return_clause = ast.clauses[0]
        expr = return_clause.items[0].expression

        assert isinstance(expr, BinaryOp)
        assert expr.op == "-"

    def test_parse_multiplication(self):
        """Parse multiplication operator."""
        query = "RETURN 4 * 3 AS result"
        ast = parse_cypher(query)

        return_clause = ast.clauses[0]
        expr = return_clause.items[0].expression

        assert isinstance(expr, BinaryOp)
        assert expr.op == "*"

    def test_parse_division(self):
        """Parse division operator."""
        query = "RETURN 10 / 2 AS result"
        ast = parse_cypher(query)

        return_clause = ast.clauses[0]
        expr = return_clause.items[0].expression

        assert isinstance(expr, BinaryOp)
        assert expr.op == "/"

    def test_parse_modulo(self):
        """Parse modulo operator."""
        query = "RETURN 10 % 3 AS result"
        ast = parse_cypher(query)

        return_clause = ast.clauses[0]
        expr = return_clause.items[0].expression

        assert isinstance(expr, BinaryOp)
        assert expr.op == "%"

    def test_parse_unary_minus(self):
        """Parse unary minus."""
        query = "RETURN -5 AS result"
        ast = parse_cypher(query)

        return_clause = ast.clauses[0]
        expr = return_clause.items[0].expression

        assert isinstance(expr, UnaryOp)
        assert expr.op == "-"
        assert isinstance(expr.operand, Literal)
        assert expr.operand.value == 5

    def test_parse_multiplication_before_addition(self):
        """Parse multiplication with higher precedence than addition."""
        query = "RETURN 2 + 3 * 4 AS result"
        ast = parse_cypher(query)

        return_clause = ast.clauses[0]
        expr = return_clause.items[0].expression

        # Should be: 2 + (3 * 4)
        assert isinstance(expr, BinaryOp)
        assert expr.op == "+"
        assert isinstance(expr.left, Literal)
        assert expr.left.value == 2
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.op == "*"

    def test_parse_division_before_subtraction(self):
        """Parse division with higher precedence than subtraction."""
        query = "RETURN 10 - 6 / 2 AS result"
        ast = parse_cypher(query)

        return_clause = ast.clauses[0]
        expr = return_clause.items[0].expression

        # Should be: 10 - (6 / 2)
        assert isinstance(expr, BinaryOp)
        assert expr.op == "-"
        assert isinstance(expr.right, BinaryOp)
        assert expr.right.op == "/"

    def test_parse_left_associativity_addition(self):
        """Parse left-associative addition."""
        query = "RETURN 1 + 2 + 3 AS result"
        ast = parse_cypher(query)

        return_clause = ast.clauses[0]
        expr = return_clause.items[0].expression

        # Should be: (1 + 2) + 3
        assert isinstance(expr, BinaryOp)
        assert expr.op == "+"
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.op == "+"

    def test_parse_left_associativity_multiplication(self):
        """Parse left-associative multiplication."""
        query = "RETURN 2 * 3 * 4 AS result"
        ast = parse_cypher(query)

        return_clause = ast.clauses[0]
        expr = return_clause.items[0].expression

        # Should be: (2 * 3) * 4
        assert isinstance(expr, BinaryOp)
        assert expr.op == "*"
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.op == "*"

    def test_parse_unary_minus_with_multiplication(self):
        """Parse unary minus with multiplication."""
        query = "RETURN -2 * 3 AS result"
        ast = parse_cypher(query)

        return_clause = ast.clauses[0]
        expr = return_clause.items[0].expression

        # Should be: (-2) * 3
        assert isinstance(expr, BinaryOp)
        assert expr.op == "*"
        assert isinstance(expr.left, UnaryOp)
        assert expr.left.op == "-"

    def test_parse_complex_expression(self):
        """Parse complex arithmetic expression."""
        query = "RETURN 2 + 3 * 4 - 5 / 2 AS result"
        ast = parse_cypher(query)

        return_clause = ast.clauses[0]
        expr = return_clause.items[0].expression

        # Should follow operator precedence
        assert isinstance(expr, BinaryOp)
        # Root should be subtraction (last addition/subtraction)
        assert expr.op == "-"

    def test_parse_arithmetic_in_where(self):
        """Parse arithmetic in WHERE clause."""
        query = "MATCH (n) WHERE n.age + 5 > 30 RETURN n"
        ast = parse_cypher(query)

        where_clause = ast.clauses[1]
        predicate = where_clause.predicate

        # Root should be > comparison
        assert isinstance(predicate, BinaryOp)
        assert predicate.op == ">"
        # Left should be addition
        assert isinstance(predicate.left, BinaryOp)
        assert predicate.left.op == "+"

    def test_parse_arithmetic_with_property_access(self):
        """Parse arithmetic with property access."""
        query = "RETURN n.age * 2 + 10 AS doubled"
        ast = parse_cypher(query)

        return_clause = ast.clauses[0]
        expr = return_clause.items[0].expression

        # Root should be addition
        assert isinstance(expr, BinaryOp)
        assert expr.op == "+"
        # Left should be multiplication with property access
        assert isinstance(expr.left, BinaryOp)
        assert expr.left.op == "*"
