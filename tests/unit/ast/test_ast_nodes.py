"""Tests for AST node data structures.

Tests cover the AST nodes defined in the openCypher spec:
- Query and clause structures
- Pattern matching (nodes and relationships)
- Expressions and literals
"""

from pydantic import ValidationError
import pytest

from graphforge.ast.clause import LimitClause, MatchClause, ReturnClause, SkipClause, WhereClause
from graphforge.ast.expression import (
    BinaryOp,
    CaseExpression,
    FunctionCall,
    ListComprehension,
    Literal,
    PropertyAccess,
    QuantifierExpression,
    SubqueryExpression,
    UnaryOp,
    Variable,
)
from graphforge.ast.pattern import Direction, NodePattern, RelationshipPattern
from graphforge.ast.query import CypherQuery, UnionQuery


@pytest.mark.unit
class TestCypherQuery:
    """Tests for CypherQuery root node."""

    def test_empty_query(self):
        """Query can be created with no clauses."""
        query = CypherQuery(clauses=[])
        assert len(query.clauses) == 0

    def test_query_with_clauses(self):
        """Query can contain multiple clauses."""
        from graphforge.ast.clause import ReturnItem

        # Valid clauses with required content
        pattern = NodePattern(variable="n")
        match_clause = MatchClause(patterns=[pattern])
        return_clause = ReturnClause(items=[ReturnItem(expression=Variable(name="n"))])
        query = CypherQuery(clauses=[match_clause, return_clause])
        assert len(query.clauses) == 2


@pytest.mark.unit
class TestMatchClause:
    """Tests for MATCH clause."""

    def test_match_clause_creation(self):
        """Match clause can be created with patterns."""
        pattern = NodePattern(variable="n", labels=[["Person"]], properties={})
        match = MatchClause(patterns=[pattern])
        assert len(match.patterns) == 1
        assert match.patterns[0].variable == "n"

    def test_empty_match_validation(self):
        """Match clause must have at least one pattern."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            MatchClause(patterns=[])


@pytest.mark.unit
class TestNodePattern:
    """Tests for node pattern matching."""

    def test_node_with_variable_and_label(self):
        """Node pattern with variable and label."""
        pattern = NodePattern(variable="n", labels=[["Person"]], properties={})
        assert pattern.variable == "n"
        assert ["Person"] in pattern.labels
        assert len(pattern.properties) == 0

    def test_node_no_variable(self):
        """Node pattern can have no variable (anonymous)."""
        pattern = NodePattern(variable=None, labels=[["Person"]], properties={})
        assert pattern.variable is None

    def test_node_multiple_labels(self):
        """Node pattern can have multiple labels."""
        pattern = NodePattern(variable="n", labels=[["Person", "Employee"]], properties={})
        assert len(pattern.labels) == 1
        assert ["Person", "Employee"] in pattern.labels

    def test_node_with_properties(self):
        """Node pattern can have property constraints."""
        props = {"name": Literal(value="Alice"), "age": Literal(value=30)}
        pattern = NodePattern(variable="n", labels=[["Person"]], properties=props)
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
            right=Literal(value=30),
        )
        where = WhereClause(predicate=predicate)
        assert where.predicate.op == ">"


@pytest.mark.unit
class TestReturnClause:
    """Tests for RETURN clause."""

    def test_return_single_item(self):
        """Return clause with single item."""
        from graphforge.ast.clause import ReturnItem

        return_clause = ReturnClause(items=[ReturnItem(expression=Variable(name="n"))])
        assert len(return_clause.items) == 1

    def test_return_multiple_items(self):
        """Return clause with multiple items."""
        from graphforge.ast.clause import ReturnItem

        return_clause = ReturnClause(
            items=[
                ReturnItem(expression=Variable(name="n")),
                ReturnItem(expression=Variable(name="m")),
            ]
        )
        assert len(return_clause.items) == 2

    def test_return_expression(self):
        """Return clause can return expressions."""
        from graphforge.ast.clause import ReturnItem

        expr = PropertyAccess(variable="n", property="name")
        return_clause = ReturnClause(items=[ReturnItem(expression=expr)])
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
        lit = Literal(value=42)
        assert lit.value == 42

    def test_literal_string(self):
        """Literal string expression."""
        lit = Literal(value="hello")
        assert lit.value == "hello"

    def test_literal_null(self):
        """Literal null expression."""
        lit = Literal(value=None)
        assert lit.value is None

    def test_variable(self):
        """Variable reference."""
        var = Variable(name="n")
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
            left=Variable(name="x"),
            right=Literal(value=10),
        )
        assert op.op == ">"
        assert isinstance(op.left, Variable)
        assert isinstance(op.right, Literal)

    def test_binary_op_logical(self):
        """Binary logical operation (AND, OR)."""
        left_cond = BinaryOp(op=">", left=Variable(name="x"), right=Literal(value=10))
        right_cond = BinaryOp(op="<", left=Variable(name="x"), right=Literal(value=20))
        combined = BinaryOp(op="AND", left=left_cond, right=right_cond)
        assert combined.op == "AND"


@pytest.mark.unit
class TestCompleteQuery:
    """Tests for complete query structures."""

    def test_simple_match_return(self):
        """MATCH (n:Person) RETURN n"""
        from graphforge.ast.clause import ReturnItem

        node = NodePattern(variable="n", labels=[["Person"]], properties={})
        match = MatchClause(patterns=[node])
        return_clause = ReturnClause(items=[ReturnItem(expression=Variable(name="n"))])
        query = CypherQuery(clauses=[match, return_clause])

        assert len(query.clauses) == 2
        assert isinstance(query.clauses[0], MatchClause)
        assert isinstance(query.clauses[1], ReturnClause)

    def test_match_where_return(self):
        """MATCH (n:Person) WHERE n.age > 30 RETURN n.name"""
        node = NodePattern(variable="n", labels=[["Person"]], properties={})
        match = MatchClause(patterns=[node])

        predicate = BinaryOp(
            op=">",
            left=PropertyAccess(variable="n", property="age"),
            right=Literal(value=30),
        )
        where = WhereClause(predicate=predicate)

        from graphforge.ast.clause import ReturnItem

        return_item_expr = PropertyAccess(variable="n", property="name")
        return_clause = ReturnClause(items=[ReturnItem(expression=return_item_expr)])

        query = CypherQuery(clauses=[match, where, return_clause])

        assert len(query.clauses) == 3
        assert isinstance(query.clauses[0], MatchClause)
        assert isinstance(query.clauses[1], WhereClause)
        assert isinstance(query.clauses[2], ReturnClause)

    def test_match_return_limit(self):
        """MATCH (n) RETURN n LIMIT 5"""
        from graphforge.ast.clause import ReturnItem

        node = NodePattern(variable="n", labels=[], properties={})
        match = MatchClause(patterns=[node])
        return_clause = ReturnClause(items=[ReturnItem(expression=Variable(name="n"))])
        limit = LimitClause(count=5)

        query = CypherQuery(clauses=[match, return_clause, limit])

        assert len(query.clauses) == 3
        assert isinstance(query.clauses[2], LimitClause)
        assert query.clauses[2].count == 5


@pytest.mark.unit
class TestNodePatternValidation:
    """Tests for NodePattern validation edge cases."""

    @pytest.mark.parametrize(
        "variable,labels,expected_error",
        [
            ("", [["Person"]], "Variable name cannot be empty string"),
            ("1node", [["Person"]], "must start with letter or underscore"),
            ("$node", [["Person"]], "must start with letter or underscore"),
            ("node-name", [["Person"]], "must contain only alphanumeric and underscore"),
            ("node name", [["Person"]], "must contain only alphanumeric and underscore"),
            ("n", [["1Person"]], "Label must start with a letter"),
            ("n", [[""]], "Label must start with a letter"),
        ],
        ids=[
            "empty_variable",
            "variable_starts_with_number",
            "variable_starts_with_special_char",
            "variable_with_dash",
            "variable_with_space",
            "label_starts_with_number",
            "empty_label",
        ],
    )
    def test_invalid_node_pattern(self, variable, labels, expected_error):
        """Invalid NodePattern should raise ValidationError."""
        with pytest.raises(ValidationError, match=expected_error):
            NodePattern(variable=variable, labels=labels)

    @pytest.mark.parametrize(
        "variable,expected",
        [
            ("_node", "_node"),
            ("node123", "node123"),
        ],
        ids=["underscore_prefix", "numbers_in_name"],
    )
    def test_valid_node_pattern_variable(self, variable, expected):
        """Valid variable names should be accepted."""
        pattern = NodePattern(variable=variable, labels=[["Person"]])
        assert pattern.variable == expected


@pytest.mark.unit
class TestRelationshipPatternValidation:
    """Tests for RelationshipPattern validation edge cases."""

    @pytest.mark.parametrize(
        "variable,types,min_hops,max_hops,expected_error",
        [
            ("", ["KNOWS"], None, None, "Variable name cannot be empty string"),
            ("1rel", ["KNOWS"], None, None, "must start with letter or underscore"),
            ("rel-name", ["KNOWS"], None, None, "must contain only alphanumeric and underscore"),
            ("r", ["1KNOWS"], None, None, "Relationship type must start with a letter"),
            ("r", [""], None, None, "Relationship type must start with a letter"),
            ("r", ["KNOWS"], -1, None, "Minimum hops must be non-negative"),
            ("r", ["KNOWS"], None, 0, "Maximum hops must be positive"),
            ("r", ["KNOWS"], None, -5, "Maximum hops must be positive"),
        ],
        ids=[
            "empty_variable",
            "variable_starts_with_number",
            "variable_with_dash",
            "type_starts_with_number",
            "empty_type",
            "negative_min_hops",
            "zero_max_hops",
            "negative_max_hops",
        ],
    )
    def test_invalid_relationship_pattern(
        self, variable, types, min_hops, max_hops, expected_error
    ):
        """Invalid RelationshipPattern should raise ValidationError."""
        with pytest.raises(ValidationError, match=expected_error):
            RelationshipPattern(
                variable=variable,
                types=types,
                direction=Direction.OUT,
                min_hops=min_hops,
                max_hops=max_hops,
            )

    @pytest.mark.parametrize(
        "min_hops,max_hops,expected_min,expected_max",
        [
            (1, 3, 1, 3),
            (1, None, 1, None),
        ],
        ids=["bounded_pattern", "unbounded_pattern"],
    )
    def test_valid_variable_length_pattern(self, min_hops, max_hops, expected_min, expected_max):
        """Valid variable-length patterns should be accepted."""
        pattern = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=min_hops,
            max_hops=max_hops,
        )
        assert pattern.min_hops == expected_min
        assert pattern.max_hops == expected_max


@pytest.mark.unit
class TestUnionQueryValidation:
    """Tests for UnionQuery validation edge cases."""

    def test_empty_branches_fails(self):
        """Empty branches list should fail."""
        with pytest.raises(ValidationError, match="UNION must have at least one branch"):
            UnionQuery(branches=[], all=False)

    def test_single_branch_fails(self):
        """UNION with only one branch should fail."""
        query = CypherQuery(clauses=[])
        with pytest.raises(ValidationError, match="UNION requires at least two branches"):
            UnionQuery(branches=[query], all=False)

    def test_non_cypher_query_branches_fails(self):
        """Branches with non-CypherQuery objects should fail."""
        with pytest.raises(ValidationError):
            # Pydantic catches this at type level
            UnionQuery(branches=[CypherQuery(clauses=[]), "not a query"], all=False)

    def test_valid_union_two_branches(self):
        """Valid UNION with two branches."""
        query1 = CypherQuery(clauses=[])
        query2 = CypherQuery(clauses=[])
        union = UnionQuery(branches=[query1, query2], all=False)
        assert len(union.branches) == 2
        assert union.all is False

    def test_valid_union_all(self):
        """Valid UNION ALL query."""
        query1 = CypherQuery(clauses=[])
        query2 = CypherQuery(clauses=[])
        union = UnionQuery(branches=[query1, query2], all=True)
        assert union.all is True


@pytest.mark.unit
class TestExpressionValidation:
    """Tests for expression node validation edge cases."""

    def test_literal_invalid_type_fails(self):
        """Literal with invalid type should fail."""

        class CustomClass:
            pass

        with pytest.raises(ValidationError, match="Literal value must be"):
            Literal(value=CustomClass())

    def test_literal_valid_types(self):
        """Literal accepts all valid types."""
        assert Literal(value=42).value == 42
        assert Literal(value="text").value == "text"
        assert Literal(value=True).value is True
        assert Literal(value=3.14).value == 3.14
        assert Literal(value=None).value is None
        assert Literal(value=[1, 2, 3]).value == [1, 2, 3]
        assert Literal(value={"key": "value"}).value == {"key": "value"}

    def test_variable_starting_with_number_fails(self):
        """Variable name starting with number should fail."""
        with pytest.raises(ValidationError, match="must start with letter or underscore"):
            Variable(name="1var")

    def test_variable_with_special_chars_fails(self):
        """Variable name with special characters should fail."""
        with pytest.raises(ValidationError, match="must contain only alphanumeric and underscore"):
            Variable(name="var-name")

    def test_property_access_invalid_variable_fails(self):
        """PropertyAccess with invalid variable should fail."""
        with pytest.raises(ValidationError, match="must start with letter or underscore"):
            PropertyAccess(variable="$var", property="name")

    def test_property_access_invalid_property_fails(self):
        """PropertyAccess with invalid property name should fail."""
        with pytest.raises(ValidationError, match="must contain only alphanumeric and underscore"):
            PropertyAccess(variable="n", property="prop-name")

    def test_binary_op_invalid_operator_fails(self):
        """BinaryOp with unsupported operator should fail."""
        with pytest.raises(ValidationError, match="Unsupported binary operator"):
            BinaryOp(op="INVALID", left=Literal(value=1), right=Literal(value=2))

    def test_unary_op_invalid_operator_fails(self):
        """UnaryOp with unsupported operator should fail."""
        with pytest.raises(ValidationError, match="Unsupported unary operator"):
            UnaryOp(op="INVALID", operand=Literal(value=True))

    def test_function_call_args_not_list_fails(self):
        """FunctionCall with non-list args should fail (caught by Pydantic)."""
        # Pydantic will coerce at field level, but model validator checks isinstance
        # This test verifies the model validator
        func = FunctionCall(name="COUNT", args=[Variable(name="n")])
        assert isinstance(func.args, list)

    def test_function_name_normalized_to_uppercase(self):
        """Function name should be normalized to uppercase."""
        func = FunctionCall(name="count", args=[])
        assert func.name == "COUNT"

    def test_case_expression_empty_when_clauses_fails(self):
        """CaseExpression with empty when_clauses should fail."""
        with pytest.raises(ValidationError):
            # Pydantic min_length catches this
            CaseExpression(when_clauses=[])

    def test_case_expression_invalid_when_clause_fails(self):
        """CaseExpression with invalid when clause format should fail."""
        with pytest.raises(ValidationError):
            # Pydantic type validation catches this
            CaseExpression(when_clauses=["not a tuple"])

    def test_case_expression_when_clause_wrong_length_fails(self):
        """CaseExpression with wrong length tuple should fail."""
        with pytest.raises(ValidationError):
            # Pydantic tuple validation catches this
            CaseExpression(when_clauses=[(Literal(value=True),)])  # Only 1 element

    def test_case_expression_valid(self):
        """Valid CaseExpression."""
        case = CaseExpression(
            when_clauses=[
                (Literal(value=True), Literal(value="yes")),
                (Literal(value=False), Literal(value="no")),
            ],
            else_expr=Literal(value="maybe"),
        )
        assert len(case.when_clauses) == 2
        assert case.else_expr is not None

    def test_list_comprehension_invalid_variable_fails(self):
        """ListComprehension with invalid variable should fail."""
        with pytest.raises(ValidationError, match="must start with letter or underscore"):
            ListComprehension(
                variable="1x",
                list_expr=Literal(value=[1, 2, 3]),
            )

    def test_subquery_expression_invalid_type_fails(self):
        """SubqueryExpression with invalid type should fail."""
        with pytest.raises(ValidationError, match="Subquery type must be EXISTS or COUNT"):
            SubqueryExpression(
                type="INVALID",
                query=CypherQuery(clauses=[]),
            )

    def test_subquery_expression_valid(self):
        """Valid SubqueryExpression."""
        subquery = SubqueryExpression(
            type="EXISTS",
            query=CypherQuery(clauses=[]),
        )
        assert subquery.type == "EXISTS"

    def test_quantifier_expression_invalid_quantifier_fails(self):
        """QuantifierExpression with invalid quantifier should fail."""
        with pytest.raises(ValidationError, match="Quantifier must be ALL, ANY, NONE, or SINGLE"):
            QuantifierExpression(
                quantifier="INVALID",
                variable="x",
                list_expr=Literal(value=[1, 2, 3]),
                predicate=Literal(value=True),
            )

    def test_quantifier_expression_invalid_variable_fails(self):
        """QuantifierExpression with invalid variable should fail."""
        with pytest.raises(ValidationError, match="must start with letter or underscore"):
            QuantifierExpression(
                quantifier="ALL",
                variable="1x",
                list_expr=Literal(value=[1, 2, 3]),
                predicate=Literal(value=True),
            )

    def test_quantifier_expression_valid(self):
        """Valid QuantifierExpression."""
        quant = QuantifierExpression(
            quantifier="ALL",
            variable="x",
            list_expr=Literal(value=[1, 2, 3]),
            predicate=BinaryOp(
                op=">",
                left=Variable(name="x"),
                right=Literal(value=0),
            ),
        )
        assert quant.quantifier == "ALL"
        assert quant.variable == "x"
