"""Tests for wildcard (*) parsing in RETURN and WITH clauses."""

from graphforge.ast.clause import ReturnClause, ReturnItem, WithClause
from graphforge.ast.expression import Wildcard
from graphforge.parser.parser import parse_cypher


class TestWildcardParsing:
    """Test parsing of * wildcard in RETURN and WITH clauses."""

    def test_parse_return_wildcard(self):
        """Test RETURN * parsing."""
        query = "MATCH (n) RETURN *"
        ast = parse_cypher(query)

        # Should have MATCH and RETURN clauses
        assert len(ast.clauses) == 2
        return_clause = ast.clauses[1]
        assert isinstance(return_clause, ReturnClause)

        # RETURN clause should have one item with Wildcard expression
        assert len(return_clause.items) == 1
        item = return_clause.items[0]
        assert isinstance(item, ReturnItem)
        assert isinstance(item.expression, Wildcard)
        assert item.alias is None

    def test_parse_with_wildcard(self):
        """Test WITH * parsing."""
        query = "MATCH (n) WITH * RETURN n"
        ast = parse_cypher(query)

        # Should have MATCH, WITH, and RETURN clauses
        assert len(ast.clauses) == 3
        with_clause = ast.clauses[1]
        assert isinstance(with_clause, WithClause)

        # WITH clause should have one item with Wildcard expression
        assert len(with_clause.items) == 1
        item = with_clause.items[0]
        assert isinstance(item, ReturnItem)
        assert isinstance(item.expression, Wildcard)
        assert item.alias is None

    def test_parse_with_wildcard_and_additional_items(self):
        """Test WITH *, additional_expr AS alias."""
        query = "MATCH (n) WITH *, 1 AS x RETURN n, x"
        ast = parse_cypher(query)

        with_clause = ast.clauses[1]
        assert isinstance(with_clause, WithClause)

        # WITH clause should have two items
        assert len(with_clause.items) == 2
        # First item is wildcard
        assert isinstance(with_clause.items[0].expression, Wildcard)
        # Second item is literal with alias
        assert with_clause.items[1].alias == "x"

    def test_parse_create_with_wildcard(self):
        """Test CREATE followed by WITH *."""
        query = "CREATE (n:Node) WITH * RETURN n"
        ast = parse_cypher(query)

        # Should have CREATE, WITH, and RETURN
        assert len(ast.clauses) == 3
        with_clause = ast.clauses[1]
        assert isinstance(with_clause, WithClause)
        assert isinstance(with_clause.items[0].expression, Wildcard)

    def test_parse_wildcard_with_where(self):
        """Test WITH * WHERE condition."""
        query = "MATCH (n) WITH * WHERE n.age > 20 RETURN n"
        ast = parse_cypher(query)

        with_clause = ast.clauses[1]
        assert isinstance(with_clause, WithClause)
        assert isinstance(with_clause.items[0].expression, Wildcard)
        # Should have WHERE clause
        assert with_clause.where is not None

    def test_parse_wildcard_with_order_by(self):
        """Test WITH * ORDER BY."""
        query = "MATCH (n) WITH * ORDER BY n.name RETURN n"
        ast = parse_cypher(query)

        with_clause = ast.clauses[1]
        assert isinstance(with_clause, WithClause)
        assert isinstance(with_clause.items[0].expression, Wildcard)
        # Should have ORDER BY
        assert with_clause.order_by is not None

    def test_parse_wildcard_with_limit(self):
        """Test WITH * LIMIT n."""
        query = "MATCH (n) WITH * LIMIT 5 RETURN n"
        ast = parse_cypher(query)

        with_clause = ast.clauses[1]
        assert isinstance(with_clause, WithClause)
        assert isinstance(with_clause.items[0].expression, Wildcard)
        # Should have LIMIT
        assert with_clause.limit is not None

    def test_parse_multiple_with_wildcards(self):
        """Test multiple WITH * clauses."""
        query = "MATCH (n) WITH * WITH * RETURN n"
        ast = parse_cypher(query)

        # Should have MATCH, WITH, WITH, RETURN
        assert len(ast.clauses) == 4
        # Both WITH clauses should have wildcard
        assert isinstance(ast.clauses[1].items[0].expression, Wildcard)
        assert isinstance(ast.clauses[2].items[0].expression, Wildcard)
