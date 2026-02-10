"""Unit tests for parsing MERGE ON CREATE SET syntax."""

from graphforge.ast.clause import MergeClause, SetClause
from graphforge.ast.expression import Literal, PropertyAccess
from graphforge.ast.pattern import NodePattern
from graphforge.parser.parser import parse_cypher


class TestMergeOnCreateParsing:
    """Test parsing of MERGE with ON CREATE SET clause."""

    def test_merge_on_create_single_property(self):
        """Parse MERGE with ON CREATE SET single property."""
        query = "MERGE (n:Person {id: 1}) ON CREATE SET n.created = true"
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert isinstance(merge, MergeClause)
        assert len(merge.patterns) == 1
        assert merge.on_create is not None
        assert isinstance(merge.on_create, SetClause)
        assert len(merge.on_create.items) == 1

        # Check the SET item
        prop_access, value_expr = merge.on_create.items[0]
        assert isinstance(prop_access, PropertyAccess)
        assert prop_access.variable == "n"
        assert prop_access.property == "created"
        assert isinstance(value_expr, Literal)
        assert value_expr.value is True

    def test_merge_on_create_multiple_properties(self):
        """Parse MERGE with ON CREATE SET multiple properties."""
        query = """
        MERGE (n:Person {id: 1})
        ON CREATE SET n.created = true, n.timestamp = 123
        """
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert isinstance(merge, MergeClause)
        assert merge.on_create is not None
        assert isinstance(merge.on_create, SetClause)
        assert len(merge.on_create.items) == 2

        # Check first SET item
        prop_access1, value_expr1 = merge.on_create.items[0]
        assert prop_access1.variable == "n"
        assert prop_access1.property == "created"
        assert value_expr1.value is True

        # Check second SET item
        prop_access2, value_expr2 = merge.on_create.items[1]
        assert prop_access2.variable == "n"
        assert prop_access2.property == "timestamp"
        assert value_expr2.value == 123

    def test_merge_without_on_create(self):
        """Parse MERGE without ON CREATE (backward compatibility)."""
        query = "MERGE (n:Person {id: 1})"
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert isinstance(merge, MergeClause)
        assert len(merge.patterns) == 1
        assert merge.on_create is None

    def test_merge_case_insensitive(self):
        """Test ON CREATE keywords are case-insensitive."""
        queries = [
            "MERGE (n:Test {id: 1}) ON CREATE SET n.val = 1",
            "MERGE (n:Test {id: 1}) on create set n.val = 1",
            "MERGE (n:Test {id: 1}) On Create Set n.val = 1",
            "MERGE (n:Test {id: 1}) oN cReAtE sEt n.val = 1",
        ]

        for query in queries:
            ast = parse_cypher(query)
            merge = ast.clauses[0]
            assert isinstance(merge, MergeClause)
            assert merge.on_create is not None
            assert isinstance(merge.on_create, SetClause)

    def test_merge_on_create_with_string_value(self):
        """Parse MERGE with ON CREATE SET with string value."""
        query = "MERGE (m:Movie {title: 'The Matrix'}) ON CREATE SET m.tagline = 'Welcome to the Real World'"
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert merge.on_create is not None
        prop_access, value_expr = merge.on_create.items[0]
        assert prop_access.variable == "m"
        assert prop_access.property == "tagline"
        assert value_expr.value == "Welcome to the Real World"

    def test_merge_on_create_neo4j_movie_pattern(self):
        """Parse real Neo4j Movie Graph pattern."""
        query = """
        MERGE (TheMatrix:Movie {title:'The Matrix'})
        ON CREATE SET TheMatrix.released=1999, TheMatrix.tagline='Welcome to the Real World'
        """
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert isinstance(merge, MergeClause)
        assert merge.on_create is not None
        assert len(merge.on_create.items) == 2

        # Check pattern
        pattern = merge.patterns[0]
        # Pattern is now a dict with 'path_variable' and 'parts'
        assert isinstance(pattern, dict)
        assert pattern["path_variable"] is None
        parts = pattern["parts"]
        assert len(parts) == 1
        node = parts[0]
        assert isinstance(node, NodePattern)
        assert node.variable == "TheMatrix"
        assert node.labels == ["Movie"]
        assert "title" in node.properties

        # Check ON CREATE SET items
        prop1, val1 = merge.on_create.items[0]
        assert prop1.variable == "TheMatrix"
        assert prop1.property == "released"
        assert val1.value == 1999

        prop2, val2 = merge.on_create.items[1]
        assert prop2.variable == "TheMatrix"
        assert prop2.property == "tagline"
        assert val2.value == "Welcome to the Real World"

    def test_merge_on_create_with_expression(self):
        """Parse MERGE with ON CREATE SET with expression."""
        query = "MERGE (n:Node {id: 1}) ON CREATE SET n.doubled = 2 * 5"
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert merge.on_create is not None
        assert len(merge.on_create.items) == 1

    def test_merge_multiple_patterns_with_on_create(self):
        """Parse MERGE with multiple patterns and ON CREATE."""
        query = """
        MERGE (a:Person {id: 1}), (b:Person {id: 2})
        ON CREATE SET a.created = true
        """
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert isinstance(merge, MergeClause)
        assert len(merge.patterns) == 2
        assert merge.on_create is not None

    def test_merge_on_create_with_return(self):
        """Parse MERGE with ON CREATE SET and RETURN clause."""
        query = """
        MERGE (n:Person {id: 1})
        ON CREATE SET n.created = true
        RETURN n
        """
        ast = parse_cypher(query)

        # Should have MERGE and RETURN clauses
        assert len(ast.clauses) == 2
        merge = ast.clauses[0]
        assert isinstance(merge, MergeClause)
        assert merge.on_create is not None

    def test_merge_on_create_null_value(self):
        """Parse MERGE with ON CREATE SET with null value."""
        query = "MERGE (n:Node {id: 1}) ON CREATE SET n.optional = null"
        ast = parse_cypher(query)

        merge = ast.clauses[0]
        assert merge.on_create is not None
        _prop_access, value_expr = merge.on_create.items[0]
        assert value_expr.value is None
