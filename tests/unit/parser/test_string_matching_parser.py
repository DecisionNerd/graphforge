"""Unit tests for string matching operator parsing."""

from graphforge.ast.expression import BinaryOp, Literal
from graphforge.parser.parser import parse_cypher


class TestStringMatchingParser:
    """Tests for parsing string matching operators."""

    def test_parse_starts_with(self):
        """Parse STARTS WITH operator."""
        query = "MATCH (p) WHERE p.name STARTS WITH 'A' RETURN p"
        ast = parse_cypher(query)

        # Get WHERE clause
        where_clause = ast.clauses[1]
        predicate = where_clause.predicate

        assert isinstance(predicate, BinaryOp)
        assert predicate.op == "STARTS WITH"

    def test_parse_ends_with(self):
        """Parse ENDS WITH operator."""
        query = "MATCH (p) WHERE p.email ENDS WITH '.com' RETURN p"
        ast = parse_cypher(query)

        where_clause = ast.clauses[1]
        predicate = where_clause.predicate

        assert isinstance(predicate, BinaryOp)
        assert predicate.op == "ENDS WITH"

    def test_parse_contains(self):
        """Parse CONTAINS operator."""
        query = "MATCH (p) WHERE p.bio CONTAINS 'engineer' RETURN p"
        ast = parse_cypher(query)

        where_clause = ast.clauses[1]
        predicate = where_clause.predicate

        assert isinstance(predicate, BinaryOp)
        assert predicate.op == "CONTAINS"

    def test_parse_starts_with_case_insensitive_keyword(self):
        """Parse STARTS WITH with mixed case keywords."""
        query = "MATCH (p) WHERE p.name StArTs WiTh 'A' RETURN p"
        ast = parse_cypher(query)

        where_clause = ast.clauses[1]
        predicate = where_clause.predicate

        assert isinstance(predicate, BinaryOp)
        assert predicate.op == "STARTS WITH"

    def test_parse_ends_with_case_insensitive_keyword(self):
        """Parse ENDS WITH with mixed case keywords."""
        query = "MATCH (p) WHERE p.email EnDs WiTh '.com' RETURN p"
        ast = parse_cypher(query)

        where_clause = ast.clauses[1]
        predicate = where_clause.predicate

        assert isinstance(predicate, BinaryOp)
        assert predicate.op == "ENDS WITH"

    def test_parse_contains_case_insensitive_keyword(self):
        """Parse CONTAINS with mixed case keyword."""
        query = "MATCH (p) WHERE p.bio CoNtAiNs 'engineer' RETURN p"
        ast = parse_cypher(query)

        where_clause = ast.clauses[1]
        predicate = where_clause.predicate

        assert isinstance(predicate, BinaryOp)
        assert predicate.op == "CONTAINS"

    def test_parse_string_match_with_literal(self):
        """Parse string matching with string literal."""
        query = "MATCH (p) WHERE p.name STARTS WITH 'Alice' RETURN p"
        ast = parse_cypher(query)

        where_clause = ast.clauses[1]
        predicate = where_clause.predicate

        assert isinstance(predicate.right, Literal)
        assert predicate.right.value == "Alice"

    def test_parse_string_match_with_variable(self):
        """Parse string matching with variable."""
        query = "MATCH (p) WHERE p.name STARTS WITH p.prefix RETURN p"
        ast = parse_cypher(query)

        where_clause = ast.clauses[1]
        predicate = where_clause.predicate

        from graphforge.ast.expression import PropertyAccess

        assert isinstance(predicate.right, PropertyAccess)
        assert predicate.right.variable == "p"
        assert predicate.right.property == "prefix"

    def test_parse_combined_string_match_and_comparison(self):
        """Parse string matching combined with other operators."""
        query = "MATCH (p) WHERE p.name STARTS WITH 'A' AND p.age > 18 RETURN p"
        ast = parse_cypher(query)

        where_clause = ast.clauses[1]
        predicate = where_clause.predicate

        # Root should be AND operator
        assert isinstance(predicate, BinaryOp)
        assert predicate.op == "AND"

        # Left should be STARTS WITH
        assert predicate.left.op == "STARTS WITH"

        # Right should be >
        assert predicate.right.op == ">"

    def test_parse_string_match_with_not(self):
        """Parse string matching with NOT."""
        query = "MATCH (p) WHERE NOT p.email ENDS WITH '@spam.com' RETURN p"
        ast = parse_cypher(query)

        where_clause = ast.clauses[1]
        predicate = where_clause.predicate

        from graphforge.ast.expression import UnaryOp

        # Root should be NOT operator
        assert isinstance(predicate, UnaryOp)
        assert predicate.op == "NOT"

        # Operand should be ENDS WITH
        assert isinstance(predicate.operand, BinaryOp)
        assert predicate.operand.op == "ENDS WITH"

    def test_parse_multiple_string_match_operators(self):
        """Parse multiple string matching operators."""
        query = "MATCH (p) WHERE p.name STARTS WITH 'A' OR p.name ENDS WITH 'son' RETURN p"
        ast = parse_cypher(query)

        where_clause = ast.clauses[1]
        predicate = where_clause.predicate

        # Root should be OR
        assert predicate.op == "OR"

        # Left should be STARTS WITH
        assert predicate.left.op == "STARTS WITH"

        # Right should be ENDS WITH
        assert predicate.right.op == "ENDS WITH"
