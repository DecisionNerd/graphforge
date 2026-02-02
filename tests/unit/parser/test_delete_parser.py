"""Unit tests for DELETE clause parsing."""

from graphforge.ast.clause import DeleteClause
from graphforge.parser.parser import CypherParser


class TestDeleteParsing:
    """Tests for parsing DELETE and DETACH DELETE clauses."""

    def test_parse_simple_delete(self):
        """Parse simple DELETE clause."""
        parser = CypherParser()
        ast = parser.parse("MATCH (n) DELETE n")

        assert len(ast.clauses) == 2
        delete_clause = ast.clauses[1]
        assert isinstance(delete_clause, DeleteClause)
        assert delete_clause.variables == ["n"]
        assert delete_clause.detach is False

    def test_parse_detach_delete(self):
        """Parse DETACH DELETE clause."""
        parser = CypherParser()
        ast = parser.parse("MATCH (n) DETACH DELETE n")

        assert len(ast.clauses) == 2
        delete_clause = ast.clauses[1]
        assert isinstance(delete_clause, DeleteClause)
        assert delete_clause.variables == ["n"]
        assert delete_clause.detach is True

    def test_parse_delete_multiple_variables(self):
        """Parse DELETE with multiple variables."""
        parser = CypherParser()
        ast = parser.parse("MATCH (a)-[r]->(b) DELETE a, r, b")

        delete_clause = ast.clauses[1]
        assert isinstance(delete_clause, DeleteClause)
        assert delete_clause.variables == ["a", "r", "b"]
        assert delete_clause.detach is False

    def test_parse_detach_delete_multiple_variables(self):
        """Parse DETACH DELETE with multiple variables."""
        parser = CypherParser()
        ast = parser.parse("MATCH (a)-[r]->(b) DETACH DELETE a, b")

        delete_clause = ast.clauses[1]
        assert isinstance(delete_clause, DeleteClause)
        assert delete_clause.variables == ["a", "b"]
        assert delete_clause.detach is True

    def test_parse_delete_case_insensitive(self):
        """DELETE keyword is case-insensitive."""
        parser = CypherParser()

        # Test lowercase
        ast1 = parser.parse("MATCH (n) delete n")
        assert ast1.clauses[1].detach is False

        # Test mixed case
        ast2 = parser.parse("MATCH (n) DeLeTe n")
        assert ast2.clauses[1].detach is False

    def test_parse_detach_delete_case_insensitive(self):
        """DETACH DELETE keywords are case-insensitive."""
        parser = CypherParser()

        # Test lowercase
        ast1 = parser.parse("MATCH (n) detach delete n")
        assert ast1.clauses[1].detach is True

        # Test mixed case
        ast2 = parser.parse("MATCH (n) DeTaCh DeLeTe n")
        assert ast2.clauses[1].detach is True
