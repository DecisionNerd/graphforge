"""Tests for AST node data structures.

Tests cover the AST nodes defined in the openCypher spec:
- Query and clause structures
- Pattern matching (nodes and relationships)
- Expressions and literals
"""

import pytest

from graphforge.ast.clause import LimitClause, MatchClause, ReturnClause, SkipClause, WhereClause
from graphforge.ast.expression import (
    BinaryOp,
    Literal,
    PropertyAccess,
    Variable,
)
from graphforge.ast.pattern import Direction, NodePattern, RelationshipPattern
from graphforge.ast.query import CypherQuery


@pytest.mark.unit
class TestCypherQuery:
    """Tests for CypherQuery root node."""

    def test_empty_query(self):
        """Query can be created with no clauses."""
        query = CypherQuery(clauses=[])
        assert len(query.clauses) == 0

    def test_query_with_clauses(self):
        """Query can contain multiple clauses."""
        match_clause = MatchClause(patterns=[])
        return_clause = ReturnClause(items=[])
        query = CypherQuery(clauses=[match_clause, return_clause])
        assert len(query.clauses) == 2


@pytest.mark.unit
class TestMatchClause:
    """Tests for MATCH clause."""

    def test_match_clause_creation(self):
        """Match clause can be created with patterns."""
        pattern = NodePattern(variable="n", labels=["Person"], properties={})
        match = MatchClause(patterns=[pattern])
        assert len(match.patterns) == 1
        assert match.patterns[0].variable == "n"

    def test_empty_match(self):
        """Match clause can have no patterns (invalid but parseable)."""
        match = MatchClause(patterns=[])
        assert len(match.patterns) == 0


@pytest.mark.unit
class TestNodePattern:
    """Tests for node pattern matching."""

    def test_node_with_variable_and_label(self):
        """Node pattern with variable and label."""
        pattern = NodePattern(variable="n", labels=["Person"], properties={})
        assert pattern.variable == "n"
        assert "Person" in pattern.labels
        assert len(pattern.properties) == 0

    def test_node_no_variable(self):
        """Node pattern can have no variable (anonymous)."""
        pattern = NodePattern(variable=None, labels=["Person"], properties={})
        assert pattern.variable is None

    def test_node_multiple_labels(self):
        """Node pattern can have multiple labels."""
        pattern = NodePattern(variable="n", labels=["Person", "Employee"], properties={})
        assert len(pattern.labels) == 2
        assert "Person" in pattern.labels
        assert "Employee" in pattern.labels

    def test_node_with_properties(self):
        """Node pattern can have property constraints."""
        props = {"name": Literal("Alice"), "age": Literal(30)}
        pattern = NodePattern(variable="n", labels=["Person"], properties=props)
        assert len(pattern.properties) == 2
        assert "name" in pattern.properties


@pytest.mark.unit
class TestRelationshipPattern:
    """Tests for relationship pattern matching."""

    def test_relationship_outgoing(self):
        """Relationship pattern with outgoing direction."""
        pattern = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.OUT,
            properties={},
        )
        assert pattern.variable == "r"
        assert "KNOWS" in pattern.types
        assert pattern.direction == Direction.OUT

    def test_relationship_incoming(self):
        """Relationship pattern with incoming direction."""
        pattern = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.IN,
            properties={},
        )
        assert pattern.direction == Direction.IN

    def test_relationship_undirected(self):
        """Relationship pattern with no direction."""
        pattern = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.UNDIRECTED,
            properties={},
        )
        assert pattern.direction == Direction.UNDIRECTED

    def test_relationship_multiple_types(self):
        """Relationship can match multiple types."""
        pattern = RelationshipPattern(
            variable="r",
            types=["KNOWS", "LIKES"],
            direction=Direction.OUT,
            properties={},
        )
        assert len(pattern.types) == 2

    def test_relationship_no_variable(self):
        """Relationship can be anonymous."""
        pattern = RelationshipPattern(
            variable=None,
            types=["KNOWS"],
            direction=Direction.OUT,
            properties={},
        )
        assert pattern.variable is None


@pytest.mark.unit
class TestWhereClause:
    """Tests for WHERE clause."""

    def test_where_with_expression(self):
        """Where clause contains a predicate expression."""
        predicate = BinaryOp(
            op=">",
            left=PropertyAccess(variable="n", property="age"),
            right=Literal(30),
        )
        where = WhereClause(predicate=predicate)
        assert where.predicate.op == ">"


@pytest.mark.unit
class TestReturnClause:
    """Tests for RETURN clause."""

    def test_return_single_item(self):
        """Return clause with single item."""
        return_clause = ReturnClause(items=[Variable("n")])
        assert len(return_clause.items) == 1

    def test_return_multiple_items(self):
        """Return clause with multiple items."""
        return_clause = ReturnClause(items=[Variable("n"), Variable("m")])
        assert len(return_clause.items) == 2

    def test_return_expression(self):
        """Return clause can return expressions."""
        expr = PropertyAccess(variable="n", property="name")
        return_clause = ReturnClause(items=[expr])
        assert len(return_clause.items) == 1


@pytest.mark.unit
class TestLimitSkipClauses:
    """Tests for LIMIT and SKIP clauses."""

    def test_limit_clause(self):
        """Limit clause specifies row limit."""
        limit = LimitClause(count=10)
        assert limit.count == 10

    def test_skip_clause(self):
        """Skip clause specifies offset."""
        skip = SkipClause(count=5)
        assert skip.count == 5


@pytest.mark.unit
class TestExpressions:
    """Tests for expression nodes."""

    def test_literal_int(self):
        """Literal integer expression."""
        lit = Literal(42)
        assert lit.value == 42

    def test_literal_string(self):
        """Literal string expression."""
        lit = Literal("hello")
        assert lit.value == "hello"

    def test_literal_null(self):
        """Literal null expression."""
        lit = Literal(None)
        assert lit.value is None

    def test_variable(self):
        """Variable reference."""
        var = Variable("n")
        assert var.name == "n"

    def test_property_access(self):
        """Property access expression."""
        prop = PropertyAccess(variable="n", property="name")
        assert prop.variable == "n"
        assert prop.property == "name"

    def test_binary_op_comparison(self):
        """Binary comparison operation."""
        op = BinaryOp(
            op=">",
            left=Variable("x"),
            right=Literal(10),
        )
        assert op.op == ">"
        assert isinstance(op.left, Variable)
        assert isinstance(op.right, Literal)

    def test_binary_op_logical(self):
        """Binary logical operation (AND, OR)."""
        left_cond = BinaryOp(op=">", left=Variable("x"), right=Literal(10))
        right_cond = BinaryOp(op="<", left=Variable("x"), right=Literal(20))
        combined = BinaryOp(op="AND", left=left_cond, right=right_cond)
        assert combined.op == "AND"


@pytest.mark.unit
class TestCompleteQuery:
    """Tests for complete query structures."""

    def test_simple_match_return(self):
        """MATCH (n:Person) RETURN n"""
        node = NodePattern(variable="n", labels=["Person"], properties={})
        match = MatchClause(patterns=[node])
        return_clause = ReturnClause(items=[Variable("n")])
        query = CypherQuery(clauses=[match, return_clause])

        assert len(query.clauses) == 2
        assert isinstance(query.clauses[0], MatchClause)
        assert isinstance(query.clauses[1], ReturnClause)

    def test_match_where_return(self):
        """MATCH (n:Person) WHERE n.age > 30 RETURN n.name"""
        node = NodePattern(variable="n", labels=["Person"], properties={})
        match = MatchClause(patterns=[node])

        predicate = BinaryOp(
            op=">",
            left=PropertyAccess(variable="n", property="age"),
            right=Literal(30),
        )
        where = WhereClause(predicate=predicate)

        return_item = PropertyAccess(variable="n", property="name")
        return_clause = ReturnClause(items=[return_item])

        query = CypherQuery(clauses=[match, where, return_clause])

        assert len(query.clauses) == 3
        assert isinstance(query.clauses[0], MatchClause)
        assert isinstance(query.clauses[1], WhereClause)
        assert isinstance(query.clauses[2], ReturnClause)

    def test_match_return_limit(self):
        """MATCH (n) RETURN n LIMIT 5"""
        node = NodePattern(variable="n", labels=[], properties={})
        match = MatchClause(patterns=[node])
        return_clause = ReturnClause(items=[Variable("n")])
        limit = LimitClause(count=5)

        query = CypherQuery(clauses=[match, return_clause, limit])

        assert len(query.clauses) == 3
        assert isinstance(query.clauses[2], LimitClause)
        assert query.clauses[2].count == 5
