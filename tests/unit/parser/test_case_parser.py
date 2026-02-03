"""Unit tests for CASE expression parsing."""

from graphforge.ast.expression import BinaryOp, CaseExpression, Literal, PropertyAccess
from graphforge.parser.parser import parse_cypher


class TestCaseParser:
    """Tests for parsing CASE expressions."""

    def test_parse_simple_case_with_one_when(self):
        """Parse CASE with single WHEN clause."""
        query = "MATCH (p) RETURN CASE WHEN p.age < 18 THEN 'minor' END AS status"
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, CaseExpression)
        assert len(expr.when_clauses) == 1
        assert expr.else_expr is None

    def test_parse_case_with_multiple_whens(self):
        """Parse CASE with multiple WHEN clauses."""
        query = """
            MATCH (p)
            RETURN CASE
                WHEN p.age < 18 THEN 'minor'
                WHEN p.age < 65 THEN 'adult'
                WHEN p.age >= 65 THEN 'senior'
            END AS category
        """
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, CaseExpression)
        assert len(expr.when_clauses) == 3
        assert expr.else_expr is None

    def test_parse_case_with_else(self):
        """Parse CASE with ELSE clause."""
        query = """
            MATCH (p)
            RETURN CASE
                WHEN p.age < 18 THEN 'minor'
                ELSE 'adult'
            END AS category
        """
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, CaseExpression)
        assert len(expr.when_clauses) == 1
        assert expr.else_expr is not None
        assert isinstance(expr.else_expr, Literal)

    def test_parse_case_without_else(self):
        """Parse CASE without ELSE clause returns NULL."""
        query = "MATCH (p) RETURN CASE WHEN p.active THEN 1 END AS status"
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, CaseExpression)
        assert expr.else_expr is None

    def test_parse_case_with_complex_conditions(self):
        """Parse CASE with complex boolean conditions."""
        query = """
            MATCH (p)
            RETURN CASE
                WHEN p.age >= 18 AND p.citizen THEN 'voter'
                ELSE 'non-voter'
            END AS status
        """
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, CaseExpression)
        assert len(expr.when_clauses) == 1
        condition, _result = expr.when_clauses[0]
        assert isinstance(condition, BinaryOp)
        assert condition.op == "AND"

    def test_parse_case_in_where_clause(self):
        """Parse CASE used in WHERE clause."""
        query = """
            MATCH (p)
            WHERE CASE WHEN p.status = 'active' THEN true ELSE false END
            RETURN p
        """
        ast = parse_cypher(query)

        where_clause = ast.clauses[1]
        assert isinstance(where_clause.predicate, CaseExpression)

    def test_parse_case_with_property_access(self):
        """Parse CASE with property access in conditions and results."""
        query = """
            MATCH (p)
            RETURN CASE
                WHEN p.active THEN p.email
                ELSE 'no-email'
            END AS contact
        """
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, CaseExpression)
        _condition, result = expr.when_clauses[0]
        assert isinstance(result, PropertyAccess)

    def test_parse_case_with_numeric_results(self):
        """Parse CASE returning numeric values."""
        query = """
            MATCH (p)
            RETURN CASE
                WHEN p.level = 'high' THEN 3
                WHEN p.level = 'medium' THEN 2
                ELSE 1
            END AS priority
        """
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, CaseExpression)
        assert len(expr.when_clauses) == 2
        assert expr.else_expr is not None

    def test_parse_nested_case(self):
        """Parse nested CASE expressions."""
        query = """
            MATCH (p)
            RETURN CASE
                WHEN p.age < 18 THEN 'minor'
                ELSE CASE
                    WHEN p.age >= 65 THEN 'senior'
                    ELSE 'adult'
                END
            END AS category
        """
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, CaseExpression)
        assert expr.else_expr is not None
        assert isinstance(expr.else_expr, CaseExpression)

    def test_parse_case_case_insensitive(self):
        """Parse CASE with mixed case keywords."""
        query = "MATCH (p) RETURN CaSe WhEn p.x = 1 ThEn 'one' ElSe 'other' EnD"
        ast = parse_cypher(query)

        return_clause = ast.clauses[1]
        expr = return_clause.items[0].expression

        assert isinstance(expr, CaseExpression)
