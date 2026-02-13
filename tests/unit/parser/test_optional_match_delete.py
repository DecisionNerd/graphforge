"""Unit tests for OPTIONAL MATCH followed by DELETE clause parsing."""

from graphforge.ast.clause import DeleteClause, MatchClause, OptionalMatchClause
from graphforge.parser.parser import CypherParser


class TestOptionalMatchDeleteParsing:
    """Tests for parsing DELETE after OPTIONAL MATCH clauses."""

    def test_parse_optional_match_delete(self):
        """Parse OPTIONAL MATCH followed by DELETE."""
        parser = CypherParser()
        ast = parser.parse("OPTIONAL MATCH (n:Person) DELETE n")

        assert len(ast.clauses) == 2
        assert isinstance(ast.clauses[0], OptionalMatchClause)
        assert isinstance(ast.clauses[1], DeleteClause)
        assert ast.clauses[1].variables == ["n"]
        assert ast.clauses[1].detach is False

    def test_parse_optional_match_detach_delete(self):
        """Parse OPTIONAL MATCH followed by DETACH DELETE."""
        parser = CypherParser()
        ast = parser.parse("OPTIONAL MATCH (n:Person) DETACH DELETE n")

        assert len(ast.clauses) == 2
        assert isinstance(ast.clauses[0], OptionalMatchClause)
        assert isinstance(ast.clauses[1], DeleteClause)
        assert ast.clauses[1].variables == ["n"]
        assert ast.clauses[1].detach is True

    def test_parse_optional_match_delete_multiple_variables(self):
        """Parse OPTIONAL MATCH followed by DELETE with multiple variables."""
        parser = CypherParser()
        ast = parser.parse("OPTIONAL MATCH (a)-[r]->(b) DELETE a, r, b")

        assert len(ast.clauses) == 2
        assert isinstance(ast.clauses[0], OptionalMatchClause)
        delete_clause = ast.clauses[1]
        assert isinstance(delete_clause, DeleteClause)
        assert delete_clause.variables == ["a", "r", "b"]
        assert delete_clause.detach is False

    def test_parse_match_then_optional_match_delete(self):
        """Parse MATCH followed by OPTIONAL MATCH and DELETE."""
        parser = CypherParser()
        ast = parser.parse("MATCH (a) OPTIONAL MATCH (a)-[r]->(b) DELETE r, b")

        assert len(ast.clauses) == 3
        assert isinstance(ast.clauses[0], MatchClause)
        assert isinstance(ast.clauses[1], OptionalMatchClause)
        assert isinstance(ast.clauses[2], DeleteClause)
        assert ast.clauses[2].variables == ["r", "b"]

    def test_parse_optional_match_where_delete(self):
        """Parse OPTIONAL MATCH with WHERE followed by DELETE."""
        parser = CypherParser()
        ast = parser.parse("OPTIONAL MATCH (n:Person) WHERE n.age > 30 DELETE n")

        assert len(ast.clauses) == 3  # OptionalMatch, Where, Delete
        assert isinstance(ast.clauses[0], OptionalMatchClause)
        assert isinstance(ast.clauses[2], DeleteClause)

    def test_parse_optional_match_detach_delete_with_return(self):
        """Parse OPTIONAL MATCH + DETACH DELETE + RETURN."""
        parser = CypherParser()
        ast = parser.parse("OPTIONAL MATCH (n:Person) DETACH DELETE n RETURN count(*) AS deleted")

        # Should have OptionalMatch, Delete, Return clauses
        assert len(ast.clauses) >= 2
        assert isinstance(ast.clauses[0], OptionalMatchClause)
        assert isinstance(ast.clauses[1], DeleteClause)
        assert ast.clauses[1].detach is True

    def test_existing_match_delete_still_works(self):
        """Regression: ensure MATCH + DELETE still works."""
        parser = CypherParser()
        ast = parser.parse("MATCH (n:Person) DELETE n")

        assert len(ast.clauses) == 2
        assert isinstance(ast.clauses[0], MatchClause)
        assert isinstance(ast.clauses[1], DeleteClause)

    def test_existing_match_detach_delete_still_works(self):
        """Regression: ensure MATCH + DETACH DELETE still works."""
        parser = CypherParser()
        ast = parser.parse("MATCH (n:Person) DETACH DELETE n")

        assert len(ast.clauses) == 2
        assert isinstance(ast.clauses[0], MatchClause)
        assert isinstance(ast.clauses[1], DeleteClause)
        assert ast.clauses[1].detach is True
