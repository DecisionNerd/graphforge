"""Tests for Cypher parser with AST transformation.

Tests that the parser correctly transforms query strings into AST nodes.
"""

import pytest

from graphforge.ast.clause import (
    LimitClause,
    MatchClause,
    OrderByClause,
    OrderByItem,
    ReturnClause,
    ReturnItem,
    SkipClause,
    WhereClause,
)
from graphforge.ast.expression import BinaryOp, FunctionCall, Literal, PropertyAccess, Variable
from graphforge.ast.pattern import Direction, NodePattern, RelationshipPattern
from graphforge.ast.query import CypherQuery
from graphforge.parser.parser import CypherParser, parse_cypher


@pytest.fixture
def parser():
    """Create a parser instance."""
    return CypherParser()


@pytest.mark.unit
class TestParserBasics:
    """Basic parser functionality tests."""

    def test_parse_simple_match_return(self, parser):
        """Parse: MATCH (n) RETURN n"""
        ast = parser.parse("MATCH (n) RETURN n")

        assert isinstance(ast, CypherQuery)
        assert len(ast.clauses) == 2

        match = ast.clauses[0]
        assert isinstance(match, MatchClause)
        assert len(match.patterns) > 0

        return_clause = ast.clauses[1]
        assert isinstance(return_clause, ReturnClause)

    def test_convenience_function(self):
        """parse_cypher convenience function works."""
        ast = parse_cypher("MATCH (n) RETURN n")
        assert isinstance(ast, CypherQuery)


@pytest.mark.unit
class TestNodePatterns:
    """Node pattern parsing tests."""

    def test_node_with_variable(self, parser):
        """Parse node with variable."""
        ast = parser.parse("MATCH (n) RETURN n")
        match = ast.clauses[0]
        node = match.patterns[0][0]  # First element of pattern

        assert isinstance(node, NodePattern)
        assert node.variable == "n"

    def test_node_with_label(self, parser):
        """Parse node with label."""
        ast = parser.parse("MATCH (n:Person) RETURN n")
        match = ast.clauses[0]
        node = match.patterns[0][0]

        assert isinstance(node, NodePattern)
        assert node.variable == "n"
        assert "Person" in node.labels

    def test_node_multiple_labels(self, parser):
        """Parse node with multiple labels."""
        ast = parser.parse("MATCH (n:Person:Employee) RETURN n")
        match = ast.clauses[0]
        node = match.patterns[0][0]

        assert len(node.labels) == 2
        assert "Person" in node.labels
        assert "Employee" in node.labels

    def test_node_with_properties(self, parser):
        """Parse node with property constraints."""
        ast = parser.parse('MATCH (n {name: "Alice", age: 30}) RETURN n')
        match = ast.clauses[0]
        node = match.patterns[0][0]

        assert len(node.properties) == 2
        assert "name" in node.properties
        assert "age" in node.properties

    def test_anonymous_node(self, parser):
        """Parse anonymous node."""
        ast = parser.parse("MATCH (:Person) RETURN 1")
        match = ast.clauses[0]
        node = match.patterns[0][0]

        assert node.variable is None
        assert "Person" in node.labels


@pytest.mark.unit
class TestRelationshipPatterns:
    """Relationship pattern parsing tests."""

    def test_relationship_outgoing(self, parser):
        """Parse outgoing relationship."""
        ast = parser.parse("MATCH (a)-[r:KNOWS]->(b) RETURN a")
        match = ast.clauses[0]
        pattern = match.patterns[0]

        # Pattern contains: node, rel, node
        assert len(pattern) == 3
        rel = pattern[1]

        assert isinstance(rel, RelationshipPattern)
        assert rel.variable == "r"
        assert "KNOWS" in rel.types
        assert rel.direction == Direction.OUT

    def test_relationship_incoming(self, parser):
        """Parse incoming relationship."""
        ast = parser.parse("MATCH (a)<-[r:KNOWS]-(b) RETURN a")
        match = ast.clauses[0]
        rel = match.patterns[0][1]

        assert rel.direction == Direction.IN

    def test_relationship_undirected(self, parser):
        """Parse undirected relationship."""
        ast = parser.parse("MATCH (a)-[r:KNOWS]-(b) RETURN a")
        match = ast.clauses[0]
        rel = match.patterns[0][1]

        assert rel.direction == Direction.UNDIRECTED

    def test_anonymous_relationship(self, parser):
        """Parse anonymous relationship."""
        ast = parser.parse("MATCH (a)-[:KNOWS]->(b) RETURN a")
        match = ast.clauses[0]
        rel = match.patterns[0][1]

        assert rel.variable is None
        assert "KNOWS" in rel.types


@pytest.mark.unit
class TestWhereClause:
    """WHERE clause parsing tests."""

    def test_simple_comparison(self, parser):
        """Parse simple comparison."""
        ast = parser.parse("MATCH (n) WHERE n.age > 30 RETURN n")

        where = ast.clauses[1]
        assert isinstance(where, WhereClause)

        predicate = where.predicate
        assert isinstance(predicate, BinaryOp)
        assert predicate.op == ">"

    def test_and_expression(self, parser):
        """Parse AND expression."""
        ast = parser.parse("MATCH (n) WHERE n.age > 30 AND n.age < 50 RETURN n")

        where = ast.clauses[1]
        predicate = where.predicate

        assert isinstance(predicate, BinaryOp)
        assert predicate.op == "AND"

    def test_or_expression(self, parser):
        """Parse OR expression."""
        ast = parser.parse("MATCH (n) WHERE n.age < 20 OR n.age > 60 RETURN n")

        where = ast.clauses[1]
        predicate = where.predicate

        assert isinstance(predicate, BinaryOp)
        assert predicate.op == "OR"


@pytest.mark.unit
class TestReturnClause:
    """RETURN clause parsing tests."""

    def test_return_variable(self, parser):
        """Parse RETURN with variable."""
        ast = parser.parse("MATCH (n) RETURN n")

        return_clause = ast.clauses[1]
        assert len(return_clause.items) == 1

        return_item = return_clause.items[0]
        assert isinstance(return_item, ReturnItem)
        assert isinstance(return_item.expression, Variable)
        assert return_item.expression.name == "n"
        assert return_item.alias is None

    def test_return_property(self, parser):
        """Parse RETURN with property access."""
        ast = parser.parse("MATCH (n) RETURN n.name")

        return_clause = ast.clauses[1]
        return_item = return_clause.items[0]

        assert isinstance(return_item, ReturnItem)
        assert isinstance(return_item.expression, PropertyAccess)
        assert return_item.expression.variable == "n"
        assert return_item.expression.property == "name"
        assert return_item.alias is None

    def test_return_multiple_items(self, parser):
        """Parse RETURN with multiple items."""
        ast = parser.parse("MATCH (n) RETURN n.name, n.age")

        return_clause = ast.clauses[1]
        assert len(return_clause.items) == 2

        # Check both items are ReturnItems
        assert all(isinstance(item, ReturnItem) for item in return_clause.items)

    def test_return_with_alias(self, parser):
        """Parse RETURN with AS alias."""
        ast = parser.parse("MATCH (n) RETURN n AS node")

        return_clause = ast.clauses[1]
        return_item = return_clause.items[0]

        assert isinstance(return_item, ReturnItem)
        assert isinstance(return_item.expression, Variable)
        assert return_item.expression.name == "n"
        assert return_item.alias == "node"

    def test_return_property_with_alias(self, parser):
        """Parse RETURN with property and alias."""
        ast = parser.parse("MATCH (n) RETURN n.name AS name")

        return_clause = ast.clauses[1]
        return_item = return_clause.items[0]

        assert isinstance(return_item, ReturnItem)
        assert isinstance(return_item.expression, PropertyAccess)
        assert return_item.expression.variable == "n"
        assert return_item.expression.property == "name"
        assert return_item.alias == "name"

    def test_return_multiple_with_aliases(self, parser):
        """Parse RETURN with multiple items with mixed aliases."""
        ast = parser.parse("MATCH (n) RETURN n.name AS name, n.age, n.city AS city")

        return_clause = ast.clauses[1]
        assert len(return_clause.items) == 3

        # First item has alias
        assert return_clause.items[0].alias == "name"
        # Second item has no alias
        assert return_clause.items[1].alias is None
        # Third item has alias
        assert return_clause.items[2].alias == "city"


@pytest.mark.unit
class TestLimitSkip:
    """LIMIT and SKIP clause parsing tests."""

    def test_limit_clause(self, parser):
        """Parse LIMIT clause."""
        ast = parser.parse("MATCH (n) RETURN n LIMIT 10")

        limit = ast.clauses[2]
        assert isinstance(limit, LimitClause)
        assert limit.count == 10

    def test_skip_clause(self, parser):
        """Parse SKIP clause."""
        ast = parser.parse("MATCH (n) RETURN n SKIP 5")

        skip = ast.clauses[2]
        assert isinstance(skip, SkipClause)
        assert skip.count == 5

    def test_skip_and_limit(self, parser):
        """Parse SKIP and LIMIT together."""
        ast = parser.parse("MATCH (n) RETURN n SKIP 5 LIMIT 10")

        assert len(ast.clauses) == 4
        skip = ast.clauses[2]
        limit = ast.clauses[3]

        assert isinstance(skip, SkipClause)
        assert isinstance(limit, LimitClause)
        assert skip.count == 5
        assert limit.count == 10


@pytest.mark.unit
class TestOrderBy:
    """ORDER BY clause parsing tests."""

    def test_order_by_single_item_default_asc(self, parser):
        """Parse ORDER BY with single item (default ASC)."""
        ast = parser.parse("MATCH (n) RETURN n ORDER BY n.name")

        order_by = ast.clauses[2]
        assert isinstance(order_by, OrderByClause)
        assert len(order_by.items) == 1

        item = order_by.items[0]
        assert isinstance(item, OrderByItem)
        assert isinstance(item.expression, PropertyAccess)
        assert item.expression.property == "name"
        assert item.ascending is True

    def test_order_by_explicit_asc(self, parser):
        """Parse ORDER BY with explicit ASC."""
        ast = parser.parse("MATCH (n) RETURN n ORDER BY n.name ASC")

        order_by = ast.clauses[2]
        item = order_by.items[0]
        assert item.ascending is True

    def test_order_by_desc(self, parser):
        """Parse ORDER BY with DESC."""
        ast = parser.parse("MATCH (n) RETURN n ORDER BY n.age DESC")

        order_by = ast.clauses[2]
        item = order_by.items[0]
        assert isinstance(item.expression, PropertyAccess)
        assert item.expression.property == "age"
        assert item.ascending is False

    def test_order_by_multiple_items(self, parser):
        """Parse ORDER BY with multiple items."""
        ast = parser.parse("MATCH (n) RETURN n ORDER BY n.age DESC, n.name ASC")

        order_by = ast.clauses[2]
        assert len(order_by.items) == 2

        # First item: age DESC
        assert order_by.items[0].expression.property == "age"
        assert order_by.items[0].ascending is False

        # Second item: name ASC
        assert order_by.items[1].expression.property == "name"
        assert order_by.items[1].ascending is True

    def test_order_by_with_limit(self, parser):
        """Parse ORDER BY with LIMIT."""
        ast = parser.parse("MATCH (n) RETURN n ORDER BY n.name LIMIT 10")

        assert len(ast.clauses) == 4
        order_by = ast.clauses[2]
        limit = ast.clauses[3]

        assert isinstance(order_by, OrderByClause)
        assert isinstance(limit, LimitClause)

    def test_order_by_with_skip_limit(self, parser):
        """Parse ORDER BY with SKIP and LIMIT."""
        ast = parser.parse("MATCH (n) RETURN n ORDER BY n.name SKIP 5 LIMIT 10")

        assert len(ast.clauses) == 5
        order_by = ast.clauses[2]
        skip = ast.clauses[3]
        limit = ast.clauses[4]

        assert isinstance(order_by, OrderByClause)
        assert isinstance(skip, SkipClause)
        assert isinstance(limit, LimitClause)


@pytest.mark.unit
class TestAggregationFunctions:
    """Aggregation function parsing tests."""

    def test_count_star(self, parser):
        """Parse COUNT(*)."""
        ast = parser.parse("MATCH (n) RETURN COUNT(*)")

        return_clause = ast.clauses[1]
        return_item = return_clause.items[0]

        assert isinstance(return_item.expression, FunctionCall)
        assert return_item.expression.name == "COUNT"
        assert return_item.expression.args == []
        assert return_item.expression.distinct is False

    def test_count_variable(self, parser):
        """Parse COUNT(n)."""
        ast = parser.parse("MATCH (n) RETURN COUNT(n)")

        return_clause = ast.clauses[1]
        return_item = return_clause.items[0]

        func = return_item.expression
        assert isinstance(func, FunctionCall)
        assert func.name == "COUNT"
        assert len(func.args) == 1
        assert isinstance(func.args[0], Variable)
        assert func.args[0].name == "n"

    def test_count_distinct(self, parser):
        """Parse COUNT(DISTINCT n)."""
        ast = parser.parse("MATCH (n) RETURN COUNT(DISTINCT n)")

        return_clause = ast.clauses[1]
        func = return_clause.items[0].expression

        assert isinstance(func, FunctionCall)
        assert func.name == "COUNT"
        assert func.distinct is True
        assert len(func.args) == 1

    def test_sum_function(self, parser):
        """Parse SUM(n.age)."""
        ast = parser.parse("MATCH (n) RETURN SUM(n.age)")

        return_clause = ast.clauses[1]
        func = return_clause.items[0].expression

        assert isinstance(func, FunctionCall)
        assert func.name == "SUM"
        assert len(func.args) == 1
        assert isinstance(func.args[0], PropertyAccess)

    def test_avg_function(self, parser):
        """Parse AVG(n.age)."""
        ast = parser.parse("MATCH (n) RETURN AVG(n.age)")

        return_clause = ast.clauses[1]
        func = return_clause.items[0].expression

        assert isinstance(func, FunctionCall)
        assert func.name == "AVG"

    def test_min_function(self, parser):
        """Parse MIN(n.age)."""
        ast = parser.parse("MATCH (n) RETURN MIN(n.age)")

        return_clause = ast.clauses[1]
        func = return_clause.items[0].expression

        assert isinstance(func, FunctionCall)
        assert func.name == "MIN"

    def test_max_function(self, parser):
        """Parse MAX(n.age)."""
        ast = parser.parse("MATCH (n) RETURN MAX(n.age)")

        return_clause = ast.clauses[1]
        func = return_clause.items[0].expression

        assert isinstance(func, FunctionCall)
        assert func.name == "MAX"

    def test_mixed_aggregates_and_grouping(self, parser):
        """Parse mixed grouping and aggregates."""
        ast = parser.parse("MATCH (n) RETURN n.name, COUNT(n)")

        return_clause = ast.clauses[1]
        assert len(return_clause.items) == 2

        # First item is grouping expression
        assert isinstance(return_clause.items[0].expression, PropertyAccess)

        # Second item is aggregate
        assert isinstance(return_clause.items[1].expression, FunctionCall)
        assert return_clause.items[1].expression.name == "COUNT"


@pytest.mark.unit
class TestLiterals:
    """Literal value parsing tests."""

    def test_integer_literal(self, parser):
        """Parse integer literal."""
        ast = parser.parse("MATCH (n {age: 42}) RETURN n")
        match = ast.clauses[0]
        node = match.patterns[0][0]

        age_literal = node.properties["age"]
        assert isinstance(age_literal, Literal)
        assert age_literal.value == 42

    def test_string_literal(self, parser):
        """Parse string literal."""
        ast = parser.parse('MATCH (n {name: "Alice"}) RETURN n')
        match = ast.clauses[0]
        node = match.patterns[0][0]

        name_literal = node.properties["name"]
        assert isinstance(name_literal, Literal)
        assert name_literal.value == "Alice"

    def test_boolean_true(self, parser):
        """Parse true literal."""
        ast = parser.parse("MATCH (n {active: true}) RETURN n")
        match = ast.clauses[0]
        node = match.patterns[0][0]

        active_literal = node.properties["active"]
        assert isinstance(active_literal, Literal)
        assert active_literal.value is True

    def test_boolean_false(self, parser):
        """Parse false literal."""
        ast = parser.parse("MATCH (n {active: false}) RETURN n")
        match = ast.clauses[0]
        node = match.patterns[0][0]

        active_literal = node.properties["active"]
        assert isinstance(active_literal, Literal)
        assert active_literal.value is False

    def test_null_literal(self, parser):
        """Parse null literal."""
        ast = parser.parse("MATCH (n {value: null}) RETURN n")
        match = ast.clauses[0]
        node = match.patterns[0][0]

        value_literal = node.properties["value"]
        assert isinstance(value_literal, Literal)
        assert value_literal.value is None


@pytest.mark.unit
class TestComplexQueries:
    """Complex query parsing tests."""

    def test_full_query(self, parser):
        """Parse complete query with all clauses."""
        query = """
        MATCH (n:Person)
        WHERE n.age > 30 AND n.age < 50
        RETURN n.name, n.age
        SKIP 10
        LIMIT 20
        """
        ast = parser.parse(query)

        assert len(ast.clauses) == 5
        assert isinstance(ast.clauses[0], MatchClause)
        assert isinstance(ast.clauses[1], WhereClause)
        assert isinstance(ast.clauses[2], ReturnClause)
        assert isinstance(ast.clauses[3], SkipClause)
        assert isinstance(ast.clauses[4], LimitClause)

    def test_case_insensitive(self, parser):
        """Keywords are case insensitive."""
        ast = parser.parse("match (n) where n.age > 30 return n limit 10")
        assert len(ast.clauses) == 4
