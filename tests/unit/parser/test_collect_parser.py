"""Unit tests for COLLECT aggregation function parsing."""

from graphforge.ast.expression import FunctionCall
from graphforge.parser.parser import parse_cypher


class TestCollectParser:
    """Tests for parsing COLLECT aggregation function."""

    def test_parse_collect_simple(self):
        """Parse simple COLLECT function."""
        query = "MATCH (p) RETURN COLLECT(p.name) AS names"
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, FunctionCall)
        assert expr.name == "COLLECT"
        assert not expr.distinct

    def test_parse_collect_distinct(self):
        """Parse COLLECT with DISTINCT."""
        query = "MATCH (p) RETURN COLLECT(DISTINCT p.name) AS names"
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, FunctionCall)
        assert expr.name == "COLLECT"
        assert expr.distinct

    def test_parse_collect_property(self):
        """Parse COLLECT with property access."""
        query = "MATCH (p:Person) RETURN COLLECT(p.age) AS ages"
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, FunctionCall)
        assert expr.name == "COLLECT"
        assert len(expr.args) == 1

    def test_parse_collect_variable(self):
        """Parse COLLECT with variable."""
        query = "MATCH (p) RETURN COLLECT(p) AS persons"
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, FunctionCall)
        assert expr.name == "COLLECT"

    def test_parse_collect_case_insensitive(self):
        """Parse COLLECT with mixed case."""
        query = "MATCH (p) RETURN CoLLeCt(p.name) AS names"
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, FunctionCall)
        assert expr.name.upper() == "COLLECT"

    def test_parse_multiple_collects(self):
        """Parse multiple COLLECT functions."""
        query = "MATCH (p) RETURN COLLECT(p.name) AS names, COLLECT(p.age) AS ages"
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]

        assert len(return_clause.items) == 2
        assert isinstance(return_clause.items[0].expression, FunctionCall)
        assert return_clause.items[0].expression.name == "COLLECT"
        assert isinstance(return_clause.items[1].expression, FunctionCall)
        assert return_clause.items[1].expression.name == "COLLECT"

    def test_parse_collect_with_expression(self):
        """Parse COLLECT with expression argument."""
        query = "MATCH (p) RETURN COLLECT(p.age * 2) AS doubled_ages"
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, FunctionCall)
        assert expr.name == "COLLECT"

    def test_parse_collect_in_with_clause(self):
        """Parse COLLECT in WITH clause."""
        query = "MATCH (p) WITH COLLECT(p.name) AS names RETURN names"
        ast = parse_cypher(query)

        # WITH clause is at index 1
        with_clause = ast.clauses[1]
        expr = with_clause.items[0].expression

        assert isinstance(expr, FunctionCall)
        assert expr.name == "COLLECT"
