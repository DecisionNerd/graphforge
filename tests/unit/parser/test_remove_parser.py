"""Unit tests for REMOVE clause parser."""

from graphforge.ast.clause import RemoveClause, RemoveItem
from graphforge.parser.parser import parse_cypher


class TestRemoveParser:
    """Tests for parsing REMOVE clauses."""

    def test_parse_remove_single_property(self):
        """Parse REMOVE with single property."""
        query = "MATCH (n) REMOVE n.age"
        ast = parse_cypher(query)

        # Should have MatchClause and RemoveClause
        assert len(ast.clauses) == 2
        remove_clause = ast.clauses[1]
        assert isinstance(remove_clause, RemoveClause)
        assert len(remove_clause.items) == 1

        item = remove_clause.items[0]
        assert isinstance(item, RemoveItem)
        assert item.item_type == "property"
        assert item.variable == "n"
        assert item.name == "age"

    def test_parse_remove_multiple_properties(self):
        """Parse REMOVE with multiple properties."""
        query = "MATCH (n) REMOVE n.age, n.city"
        ast = parse_cypher(query)

        remove_clause = ast.clauses[1]
        assert isinstance(remove_clause, RemoveClause)
        assert len(remove_clause.items) == 2

        assert remove_clause.items[0].item_type == "property"
        assert remove_clause.items[0].name == "age"
        assert remove_clause.items[1].item_type == "property"
        assert remove_clause.items[1].name == "city"

    def test_parse_remove_single_label(self):
        """Parse REMOVE with single label."""
        query = "MATCH (n) REMOVE n:Person"
        ast = parse_cypher(query)

        remove_clause = ast.clauses[1]
        assert isinstance(remove_clause, RemoveClause)
        assert len(remove_clause.items) == 1

        item = remove_clause.items[0]
        assert isinstance(item, RemoveItem)
        assert item.item_type == "label"
        assert item.variable == "n"
        assert item.name == "Person"

    def test_parse_remove_multiple_labels(self):
        """Parse REMOVE with multiple labels."""
        query = "MATCH (n) REMOVE n:Person, n:Employee"
        ast = parse_cypher(query)

        remove_clause = ast.clauses[1]
        assert len(remove_clause.items) == 2

        assert remove_clause.items[0].item_type == "label"
        assert remove_clause.items[0].name == "Person"
        assert remove_clause.items[1].item_type == "label"
        assert remove_clause.items[1].name == "Employee"

    def test_parse_remove_mixed_property_and_label(self):
        """Parse REMOVE with mixed properties and labels."""
        query = "MATCH (n) REMOVE n.age, n:Temp, n.city"
        ast = parse_cypher(query)

        remove_clause = ast.clauses[1]
        assert len(remove_clause.items) == 3

        assert remove_clause.items[0].item_type == "property"
        assert remove_clause.items[0].name == "age"
        assert remove_clause.items[1].item_type == "label"
        assert remove_clause.items[1].name == "Temp"
        assert remove_clause.items[2].item_type == "property"
        assert remove_clause.items[2].name == "city"

    def test_parse_remove_with_where(self):
        """Parse REMOVE with WHERE clause."""
        query = "MATCH (n) WHERE n.age > 30 REMOVE n.flag"
        ast = parse_cypher(query)

        # Should have MatchClause, WhereClause, RemoveClause
        assert len(ast.clauses) == 3

    def test_parse_remove_with_return(self):
        """Parse REMOVE with RETURN clause."""
        query = "MATCH (n) REMOVE n.age RETURN n.name"
        ast = parse_cypher(query)

        # Should have MatchClause, RemoveClause, ReturnClause
        assert len(ast.clauses) == 3

    def test_parse_remove_with_set(self):
        """Parse REMOVE with SET clause."""
        query = "MATCH (n) REMOVE n.old_age SET n.age = 30"
        ast = parse_cypher(query)

        # Should have MatchClause, RemoveClause, SetClause
        assert len(ast.clauses) == 3

    def test_parse_remove_with_order_by(self):
        """Parse REMOVE with ORDER BY."""
        query = "MATCH (n) REMOVE n.score RETURN n.name ORDER BY n.name"
        ast = parse_cypher(query)

        # Should have MatchClause, RemoveClause, ReturnClause, OrderByClause
        assert len(ast.clauses) == 4

    def test_parse_remove_with_limit(self):
        """Parse REMOVE with LIMIT."""
        query = "MATCH (n) REMOVE n.flag RETURN n LIMIT 10"
        ast = parse_cypher(query)

        # Should have MatchClause, RemoveClause, ReturnClause, LimitClause
        assert len(ast.clauses) == 4

    def test_parse_multiple_remove_clauses(self):
        """Parse multiple REMOVE clauses."""
        query = "MATCH (n) REMOVE n.age REMOVE n:Temp"
        ast = parse_cypher(query)

        # Should have MatchClause and two RemoveClause instances
        assert len(ast.clauses) == 3
        assert isinstance(ast.clauses[1], RemoveClause)
        assert isinstance(ast.clauses[2], RemoveClause)

    def test_parse_set_then_remove(self):
        """Parse SET followed by REMOVE."""
        query = "MATCH (n) SET n.new = 1 REMOVE n.old"
        ast = parse_cypher(query)

        # Should have MatchClause, SetClause, RemoveClause
        assert len(ast.clauses) == 3
