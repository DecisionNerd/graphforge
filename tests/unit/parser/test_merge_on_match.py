"""Unit tests for parsing MERGE ON MATCH SET syntax."""

from graphforge.ast.clause import MergeClause, SetClause
from graphforge.ast.expression import Literal, PropertyAccess
from graphforge.parser.parser import parse_cypher


class TestMergeOnMatchParsing:
    """Test parsing of MERGE with ON MATCH SET clause."""

    def test_merge_on_match_single_property(self):
        """Parse MERGE with ON MATCH SET single property."""
        query = "MERGE (n:Person {id: 1}) ON MATCH SET n.updated = true"
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert isinstance(merge, MergeClause)
        assert len(merge.patterns) == 1
        assert merge.on_create is None
        assert merge.on_match is not None
        assert isinstance(merge.on_match, SetClause)
        assert len(merge.on_match.items) == 1

        # Check the SET item
        prop_access, value_expr = merge.on_match.items[0]
        assert isinstance(prop_access, PropertyAccess)
        assert prop_access.variable == "n"
        assert prop_access.property == "updated"
        assert isinstance(value_expr, Literal)
        assert value_expr.value is True

    def test_merge_on_match_multiple_properties(self):
        """Parse MERGE with ON MATCH SET multiple properties."""
        query = """
        MERGE (n:Person {id: 1})
        ON MATCH SET n.updated = true, n.counter = 2
        """
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert isinstance(merge, MergeClause)
        assert merge.on_match is not None
        assert len(merge.on_match.items) == 2

        # Check first SET item
        prop_access1, value_expr1 = merge.on_match.items[0]
        assert prop_access1.variable == "n"
        assert prop_access1.property == "updated"
        assert value_expr1.value is True

        # Check second SET item
        prop_access2, value_expr2 = merge.on_match.items[1]
        assert prop_access2.variable == "n"
        assert prop_access2.property == "counter"
        assert value_expr2.value == 2

    def test_merge_on_create_and_on_match(self):
        """Parse MERGE with both ON CREATE SET and ON MATCH SET."""
        query = """
        MERGE (n:Person {id: 1})
        ON CREATE SET n.created = true
        ON MATCH SET n.updated = true
        """
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert isinstance(merge, MergeClause)
        assert merge.on_create is not None
        assert merge.on_match is not None

        # Check ON CREATE
        assert len(merge.on_create.items) == 1
        prop1, _val1 = merge.on_create.items[0]
        assert prop1.property == "created"

        # Check ON MATCH
        assert len(merge.on_match.items) == 1
        prop2, _val2 = merge.on_match.items[0]
        assert prop2.property == "updated"

    def test_merge_on_create_and_on_match_multiple_properties(self):
        """Parse MERGE with both ON CREATE and ON MATCH with multiple properties."""
        query = """
        MERGE (n:Person {id: 1})
        ON CREATE SET n.created = true, n.createdAt = 100
        ON MATCH SET n.updated = true, n.updatedAt = 200
        """
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert merge.on_create is not None
        assert merge.on_match is not None
        assert len(merge.on_create.items) == 2
        assert len(merge.on_match.items) == 2

    def test_merge_case_insensitive(self):
        """Test ON MATCH keywords are case-insensitive."""
        queries = [
            "MERGE (n:Test {id: 1}) ON MATCH SET n.val = 1",
            "MERGE (n:Test {id: 1}) on match set n.val = 1",
            "MERGE (n:Test {id: 1}) On Match Set n.val = 1",
            "MERGE (n:Test {id: 1}) oN mAtCh sEt n.val = 1",
        ]

        for query in queries:
            ast = parse_cypher(query)
            merge = ast.clauses[0]
            assert isinstance(merge, MergeClause)
            assert merge.on_match is not None
            assert isinstance(merge.on_match, SetClause)

    def test_merge_without_on_clauses(self):
        """Parse MERGE without ON CREATE or ON MATCH (backward compatibility)."""
        query = "MERGE (n:Person {id: 1})"
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert isinstance(merge, MergeClause)
        assert len(merge.patterns) == 1
        assert merge.on_create is None
        assert merge.on_match is None

    def test_merge_on_match_with_return(self):
        """Parse MERGE with ON MATCH SET and RETURN clause."""
        query = """
        MERGE (n:Person {id: 1})
        ON MATCH SET n.updated = true
        RETURN n
        """
        ast = parse_cypher(query)

        # Should have MERGE and RETURN clauses
        assert len(ast.clauses) == 2
        merge = ast.clauses[0]
        assert isinstance(merge, MergeClause)
        assert merge.on_match is not None

    def test_merge_on_match_with_string_value(self):
        """Parse MERGE with ON MATCH SET with string value."""
        query = "MERGE (m:Movie {title: 'The Matrix'}) ON MATCH SET m.status = 'watched'"
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert merge.on_match is not None
        prop_access, value_expr = merge.on_match.items[0]
        assert prop_access.property == "status"
        assert value_expr.value == "watched"

    def test_merge_on_match_with_expression(self):
        """Parse MERGE with ON MATCH SET with expression."""
        query = "MERGE (n:Node {id: 1}) ON MATCH SET n.counter = 2 * 5"
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert merge.on_match is not None
        assert len(merge.on_match.items) == 1

    def test_merge_multiple_patterns_with_on_match(self):
        """Parse MERGE with multiple patterns and ON MATCH."""
        query = """
        MERGE (a:Person {id: 1}), (b:Person {id: 2})
        ON MATCH SET a.updated = true
        """
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert isinstance(merge, MergeClause)
        assert len(merge.patterns) == 2
        assert merge.on_match is not None
