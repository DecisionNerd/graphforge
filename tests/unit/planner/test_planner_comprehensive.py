"""Comprehensive tests for query planner.

This module tests the QueryPlanner's ability to convert AST nodes
into logical plan operators, covering complex patterns and edge cases.
"""

import pytest

from graphforge.ast.clause import (
    CreateClause,
    DeleteClause,
    LimitClause,
    MatchClause,
    MergeClause,
    OptionalMatchClause,
    OrderByClause,
    OrderByItem,
    ReturnClause,
    ReturnItem,
    SetClause,
    SkipClause,
    UnwindClause,
    WhereClause,
    WithClause,
)
from graphforge.ast.expression import (
    BinaryOp,
    FunctionCall,
    Literal,
    PropertyAccess,
    Variable,
)
from graphforge.ast.pattern import Direction, NodePattern, RelationshipPattern
from graphforge.ast.query import CypherQuery
from graphforge.planner.operators import (
    Aggregate,
    Create,
    Delete,
    Distinct,
    ExpandEdges,
    ExpandMultiHop,
    ExpandVariableLength,
    Filter,
    Limit,
    Merge,
    OptionalExpandEdges,
    OptionalScanNodes,
    Project,
    ScanNodes,
    Set,
    Skip,
    Sort,
    Unwind,
    With,
)
from graphforge.planner.planner import QueryPlanner


@pytest.mark.unit
class TestBasicQueryPlanning:
    """Test basic query planning scenarios."""

    def test_plan_unwind_clause(self):
        """Plan UNWIND clause."""
        unwind = UnwindClause(
            expression=Literal(value=[1, 2, 3]),
            variable="x",
        )
        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="x"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[unwind, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        assert isinstance(operators[0], Unwind)
        assert operators[0].variable == "x"
        assert isinstance(operators[1], Project)

    def test_plan_create_clause(self):
        """Plan CREATE clause."""
        node_pattern = NodePattern(variable="n", labels=["Person"])
        create = CreateClause(patterns=[node_pattern])

        query = CypherQuery(clauses=[create])
        planner = QueryPlanner()
        operators = planner.plan(query)

        assert isinstance(operators[0], Create)
        assert len(operators[0].patterns) == 1

    def test_plan_merge_clause(self):
        """Plan MERGE clause."""
        node_pattern = NodePattern(variable="n", labels=["Person"])
        merge = MergeClause(patterns=[node_pattern], on_create=None, on_match=None)

        query = CypherQuery(clauses=[merge])
        planner = QueryPlanner()
        operators = planner.plan(query)

        assert isinstance(operators[0], Merge)
        assert len(operators[0].patterns) == 1

    def test_plan_merge_with_on_create(self):
        """Plan MERGE with ON CREATE SET."""
        node_pattern = NodePattern(variable="n", labels=["Person"])
        prop = PropertyAccess(variable="n", property="created")
        set_clause = SetClause(items=[(prop, Literal(value=True))])
        merge = MergeClause(patterns=[node_pattern], on_create=set_clause, on_match=None)

        query = CypherQuery(clauses=[merge])
        planner = QueryPlanner()
        operators = planner.plan(query)

        assert isinstance(operators[0], Merge)
        assert operators[0].on_create is not None

    def test_plan_set_clause(self):
        """Plan SET clause."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        prop = PropertyAccess(variable="n", property="age")
        set_clause = SetClause(items=[(prop, Literal(value=30))])

        query = CypherQuery(clauses=[match, set_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        assert isinstance(operators[0], ScanNodes)
        assert isinstance(operators[1], Set)
        assert len(operators[1].items) == 1

    def test_plan_delete_clause(self):
        """Plan DELETE clause."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])
        delete = DeleteClause(variables=["n"], detach=False)

        query = CypherQuery(clauses=[match, delete])
        planner = QueryPlanner()
        operators = planner.plan(query)

        assert isinstance(operators[0], ScanNodes)
        assert isinstance(operators[1], Delete)
        assert operators[1].detach is False

    def test_plan_detach_delete_clause(self):
        """Plan DETACH DELETE clause."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])
        delete = DeleteClause(variables=["n"], detach=True)

        query = CypherQuery(clauses=[match, delete])
        planner = QueryPlanner()
        operators = planner.plan(query)

        assert isinstance(operators[1], Delete)
        assert operators[1].detach is True


@pytest.mark.unit
class TestOptionalMatchPlanning:
    """Test OPTIONAL MATCH clause planning."""

    def test_plan_optional_match_single_node(self):
        """Plan OPTIONAL MATCH with single node."""
        node_pattern = NodePattern(variable="n", labels=["Person"])
        optional_match = OptionalMatchClause(patterns=[[node_pattern]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[optional_match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        assert isinstance(operators[0], OptionalScanNodes)
        assert operators[0].variable == "n"
        assert operators[0].labels == ["Person"]

    def test_plan_optional_match_with_properties(self):
        """Plan OPTIONAL MATCH with inline properties."""
        properties = {"name": Literal(value="Alice")}
        node_pattern = NodePattern(variable="n", labels=["Person"], properties=properties)
        optional_match = OptionalMatchClause(patterns=[[node_pattern]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[optional_match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have OptionalScanNodes + Filter for properties
        assert isinstance(operators[0], OptionalScanNodes)
        assert isinstance(operators[1], Filter)

    def test_plan_optional_match_relationship(self):
        """Plan OPTIONAL MATCH with relationship."""
        src_node = NodePattern(variable="a")
        rel = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        dst_node = NodePattern(variable="b")

        # First establish source node
        match = MatchClause(patterns=[[src_node]])

        # Then optional match the relationship
        optional_match = OptionalMatchClause(patterns=[[src_node, rel, dst_node]])

        return_clause = ReturnClause(
            items=[
                ReturnItem(expression=Variable(name="a"), alias=None),
                ReturnItem(expression=Variable(name="b"), alias=None),
            ],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, optional_match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have ScanNodes for first match, then ScanNodes + OptionalExpandEdges
        assert any(isinstance(op, OptionalExpandEdges) for op in operators)

    def test_plan_optional_match_with_anonymous_node(self):
        """Plan OPTIONAL MATCH with anonymous node."""
        src_node = NodePattern(variable="a")
        rel = RelationshipPattern(
            variable=None,
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        dst_node = NodePattern(variable=None)  # Anonymous destination

        match = MatchClause(patterns=[[src_node]])
        optional_match = OptionalMatchClause(patterns=[[src_node, rel, dst_node]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="a"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, optional_match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should generate anonymous variable for destination
        optional_expand = next(op for op in operators if isinstance(op, OptionalExpandEdges))
        assert optional_expand.dst_var.startswith("__anon_")


@pytest.mark.unit
class TestWithClausePlanning:
    """Test WITH clause planning."""

    def test_plan_simple_with(self):
        """Plan simple WITH clause."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        with_clause = WithClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
            where=None,
            order_by=None,
            skip=None,
            limit=None,
        )

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, with_clause, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have ScanNodes, With, Project
        assert isinstance(operators[0], ScanNodes)
        assert isinstance(operators[1], With)
        assert isinstance(operators[2], Project)

    def test_plan_with_distinct(self):
        """Plan WITH DISTINCT."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        with_clause = WithClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=True,
            where=None,
            order_by=None,
            skip=None,
            limit=None,
        )

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, with_clause, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have With operator with distinct=True + Distinct operator
        with_op = next(op for op in operators if isinstance(op, With))
        assert with_op.distinct is True
        assert any(isinstance(op, Distinct) for op in operators)

    def test_plan_with_where(self):
        """Plan WITH with WHERE clause."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        predicate = BinaryOp(
            op=">",
            left=PropertyAccess(variable="n", property="age"),
            right=Literal(value=30),
        )

        with_clause = WithClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
            where=WhereClause(predicate=predicate),
            order_by=None,
            skip=None,
            limit=None,
        )

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, with_clause, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have With operator with predicate
        with_op = next(op for op in operators if isinstance(op, With))
        assert with_op.predicate is not None

    def test_plan_with_order_by(self):
        """Plan WITH with ORDER BY."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        order_item = OrderByItem(
            expression=PropertyAccess(variable="n", property="age"),
            ascending=True,
        )

        with_clause = WithClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
            where=None,
            order_by=OrderByClause(items=[order_item]),
            skip=None,
            limit=None,
        )

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, with_clause, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have With operator with sort_items
        with_op = next(op for op in operators if isinstance(op, With))
        assert with_op.sort_items is not None

    def test_plan_with_skip_limit(self):
        """Plan WITH with SKIP and LIMIT."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        with_clause = WithClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
            where=None,
            order_by=None,
            skip=SkipClause(count=5),
            limit=LimitClause(count=10),
        )

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, with_clause, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have With operator with skip and limit
        with_op = next(op for op in operators if isinstance(op, With))
        assert with_op.skip_count == 5
        assert with_op.limit_count == 10

    def test_plan_with_distinct_skip_limit(self):
        """Plan WITH DISTINCT with SKIP and LIMIT."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        with_clause = WithClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=True,
            where=None,
            order_by=None,
            skip=SkipClause(count=5),
            limit=LimitClause(count=10),
        )

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, with_clause, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have: With (with skip_count/limit_count=None), Distinct, Skip, Limit
        with_op = next(op for op in operators if isinstance(op, With))
        assert with_op.distinct is True
        # When DISTINCT is used, SKIP/LIMIT should be separate operators
        assert any(isinstance(op, Distinct) for op in operators)
        assert any(isinstance(op, Skip) for op in operators)
        assert any(isinstance(op, Limit) for op in operators)

    def test_plan_with_aggregation(self):
        """Plan WITH with aggregation function."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        count_expr = FunctionCall(
            name="COUNT",
            args=[Variable(name="n")],
            distinct=False,
        )

        with_clause = WithClause(
            items=[ReturnItem(expression=count_expr, alias="cnt")],
            distinct=False,
            where=None,
            order_by=None,
            skip=None,
            limit=None,
        )

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="cnt"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, with_clause, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have Aggregate operator instead of With
        assert any(isinstance(op, Aggregate) for op in operators)

    def test_plan_with_mixed_grouping_and_aggregation(self):
        """Plan WITH with both grouping and aggregation."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        name_expr = PropertyAccess(variable="n", property="name")
        count_expr = FunctionCall(
            name="COUNT",
            args=[Variable(name="n")],
            distinct=False,
        )

        with_clause = WithClause(
            items=[
                ReturnItem(expression=name_expr, alias="name"),
                ReturnItem(expression=count_expr, alias="cnt"),
            ],
            distinct=False,
            where=None,
            order_by=None,
            skip=None,
            limit=None,
        )

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="name"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, with_clause, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have Aggregate operator with both grouping and agg expressions
        agg_op = next(op for op in operators if isinstance(op, Aggregate))
        assert len(agg_op.grouping_exprs) == 1
        assert len(agg_op.agg_exprs) == 1


@pytest.mark.unit
class TestComplexMatchPlanning:
    """Test complex MATCH pattern planning."""

    def test_plan_match_with_inline_properties(self):
        """Plan MATCH with inline property predicates."""
        properties = {"name": Literal(value="Alice"), "age": Literal(value=30)}
        node_pattern = NodePattern(variable="n", labels=["Person"], properties=properties)
        match = MatchClause(patterns=[[node_pattern]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have ScanNodes + Filter for properties
        assert isinstance(operators[0], ScanNodes)
        assert isinstance(operators[1], Filter)
        # Filter should combine both properties with AND
        assert operators[1].predicate.op == "AND"

    def test_plan_match_single_property(self):
        """Plan MATCH with single inline property."""
        properties = {"name": Literal(value="Alice")}
        node_pattern = NodePattern(variable="n", labels=["Person"], properties=properties)
        match = MatchClause(patterns=[[node_pattern]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have ScanNodes + Filter
        assert isinstance(operators[0], ScanNodes)
        assert isinstance(operators[1], Filter)
        # Single property should not use AND
        assert operators[1].predicate.op == "="

    def test_plan_match_with_anonymous_nodes(self):
        """Plan MATCH with anonymous node patterns."""
        src_node = NodePattern(variable=None)  # Anonymous
        rel = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        dst_node = NodePattern(variable=None)  # Anonymous

        match = MatchClause(patterns=[[src_node, rel, dst_node]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="r"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should generate anonymous variables
        scan_op = operators[0]
        assert isinstance(scan_op, ScanNodes)
        assert scan_op.variable.startswith("__anon_")

        expand_op = operators[1]
        assert isinstance(expand_op, ExpandEdges)
        assert expand_op.dst_var.startswith("__anon_")

    def test_plan_match_with_path_variable(self):
        """Plan MATCH with path variable assignment."""
        src_node = NodePattern(variable="a")
        rel = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        dst_node = NodePattern(variable="b")

        pattern_dict = {
            "path_variable": "p",
            "parts": [src_node, rel, dst_node],
        }

        match = MatchClause(patterns=[pattern_dict])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="p"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should pass path_var to ExpandEdges
        expand_op = next(op for op in operators if isinstance(op, ExpandEdges))
        assert expand_op.path_var == "p"

    def test_plan_match_multi_hop_with_path(self):
        """Plan MATCH with multi-hop pattern and path variable."""
        src_node = NodePattern(variable="a")
        rel1 = RelationshipPattern(
            variable="r1",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        mid_node = NodePattern(variable="b")
        rel2 = RelationshipPattern(
            variable="r2",
            types=["LIKES"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        dst_node = NodePattern(variable="c")

        pattern_dict = {
            "path_variable": "p",
            "parts": [src_node, rel1, mid_node, rel2, dst_node],
        }

        match = MatchClause(patterns=[pattern_dict])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="p"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should use ExpandMultiHop operator
        assert any(isinstance(op, ExpandMultiHop) for op in operators)
        multi_hop = next(op for op in operators if isinstance(op, ExpandMultiHop))
        assert multi_hop.path_var == "p"
        assert len(multi_hop.hops) == 2

    def test_plan_match_multi_hop_with_inline_properties(self):
        """Plan MATCH with multi-hop pattern and inline properties on destination."""
        src_node = NodePattern(variable="a")
        rel1 = RelationshipPattern(
            variable="r1",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        mid_node = NodePattern(variable="b", properties={"age": Literal(value=25)})
        rel2 = RelationshipPattern(
            variable="r2",
            types=["LIKES"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        dst_node = NodePattern(variable="c", properties={"name": Literal(value="Charlie")})

        pattern_dict = {
            "path_variable": "p",
            "parts": [src_node, rel1, mid_node, rel2, dst_node],
        }

        match = MatchClause(patterns=[pattern_dict])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="p"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have ExpandMultiHop + Filters for properties
        assert any(isinstance(op, ExpandMultiHop) for op in operators)
        # Count filters (one for mid_node, one for dst_node)
        filter_ops = [op for op in operators if isinstance(op, Filter)]
        assert len(filter_ops) == 2

    def test_plan_match_variable_length(self):
        """Plan MATCH with variable-length path."""
        src_node = NodePattern(variable="a")
        rel = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=1,
            max_hops=3,
            predicate=None,
        )
        dst_node = NodePattern(variable="b")

        match = MatchClause(patterns=[[src_node, rel, dst_node]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="b"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should use ExpandVariableLength
        assert any(isinstance(op, ExpandVariableLength) for op in operators)
        var_len_op = next(op for op in operators if isinstance(op, ExpandVariableLength))
        assert var_len_op.min_hops == 1
        assert var_len_op.max_hops == 3

    def test_plan_match_multi_hop_without_path(self):
        """Plan MATCH with multi-hop pattern but no path variable."""
        src_node = NodePattern(variable="a")
        rel1 = RelationshipPattern(
            variable=None,
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        mid_node = NodePattern(variable="b")
        rel2 = RelationshipPattern(
            variable=None,
            types=["LIKES"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        dst_node = NodePattern(variable="c")

        match = MatchClause(patterns=[[src_node, rel1, mid_node, rel2, dst_node]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="c"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should use individual ExpandEdges operators (not ExpandMultiHop)
        expand_ops = [op for op in operators if isinstance(op, ExpandEdges)]
        assert len(expand_ops) == 2

    def test_plan_match_with_relationship_predicate(self):
        """Plan MATCH with WHERE predicate on relationship."""
        src_node = NodePattern(variable="a")
        predicate = BinaryOp(
            op=">",
            left=PropertyAccess(variable="r", property="weight"),
            right=Literal(value=0.5),
        )
        rel = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=predicate,
        )
        dst_node = NodePattern(variable="b")

        match = MatchClause(patterns=[[src_node, rel, dst_node]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="b"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # ExpandEdges should have the predicate
        expand_op = next(op for op in operators if isinstance(op, ExpandEdges))
        assert expand_op.predicate is not None


@pytest.mark.unit
class TestAggregationPlanning:
    """Test aggregation and grouping planning."""

    def test_plan_return_with_aggregation(self):
        """Plan RETURN with aggregation function."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        count_expr = FunctionCall(
            name="COUNT",
            args=[Variable(name="n")],
            distinct=False,
        )

        return_clause = ReturnClause(
            items=[ReturnItem(expression=count_expr, alias="cnt")],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have Aggregate operator
        assert isinstance(operators[0], ScanNodes)
        assert isinstance(operators[1], Aggregate)
        assert len(operators[1].agg_exprs) == 1

    def test_plan_return_with_grouping(self):
        """Plan RETURN with GROUP BY behavior."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        name_expr = PropertyAccess(variable="n", property="name")
        count_expr = FunctionCall(
            name="COUNT",
            args=[Variable(name="n")],
            distinct=False,
        )

        return_clause = ReturnClause(
            items=[
                ReturnItem(expression=name_expr, alias="name"),
                ReturnItem(expression=count_expr, alias="cnt"),
            ],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have Aggregate operator with grouping
        agg_op = operators[1]
        assert isinstance(agg_op, Aggregate)
        assert len(agg_op.grouping_exprs) == 1
        assert len(agg_op.agg_exprs) == 1

    def test_plan_return_distinct(self):
        """Plan RETURN DISTINCT."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=True,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have Project + Distinct
        assert any(isinstance(op, Project) for op in operators)
        assert any(isinstance(op, Distinct) for op in operators)


@pytest.mark.unit
class TestOrderByPlanning:
    """Test ORDER BY planning."""

    def test_plan_order_by_with_return_alias(self):
        """Plan ORDER BY referencing RETURN alias."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias="node")],
            distinct=False,
        )

        order_item = OrderByItem(
            expression=Variable(name="node"),
            ascending=True,
        )
        order_by = OrderByClause(items=[order_item])

        query = CypherQuery(clauses=[match, return_clause, order_by])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Sort should come before Project and have return_items for alias resolution
        sort_op = next(op for op in operators if isinstance(op, Sort))
        assert sort_op.return_items is not None


@pytest.mark.unit
class TestSkipLimitPlanning:
    """Test SKIP and LIMIT planning."""

    def test_plan_skip_and_limit(self):
        """Plan SKIP and LIMIT together."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        skip_clause = SkipClause(count=10)
        limit_clause = LimitClause(count=5)

        query = CypherQuery(clauses=[match, return_clause, skip_clause, limit_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have Skip and Limit operators at the end
        assert any(isinstance(op, Skip) for op in operators)
        assert any(isinstance(op, Limit) for op in operators)

        skip_op = next(op for op in operators if isinstance(op, Skip))
        limit_op = next(op for op in operators if isinstance(op, Limit))

        assert skip_op.count == 10
        assert limit_op.count == 5


@pytest.mark.unit
class TestMixedClausesPlanning:
    """Test planning with mixed reading/writing clauses."""

    def test_plan_unwind_then_match(self):
        """Plan UNWIND followed by MATCH."""
        unwind = UnwindClause(
            expression=Literal(value=[1, 2, 3]),
            variable="x",
        )

        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        return_clause = ReturnClause(
            items=[
                ReturnItem(expression=Variable(name="x"), alias=None),
                ReturnItem(expression=Variable(name="n"), alias=None),
            ],
            distinct=False,
        )

        query = CypherQuery(clauses=[unwind, match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have Unwind, then ScanNodes
        assert isinstance(operators[0], Unwind)
        assert isinstance(operators[1], ScanNodes)

    def test_plan_match_then_unwind(self):
        """Plan MATCH followed by UNWIND."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        unwind = UnwindClause(
            expression=Literal(value=[1, 2, 3]),
            variable="x",
        )

        return_clause = ReturnClause(
            items=[
                ReturnItem(expression=Variable(name="n"), alias=None),
                ReturnItem(expression=Variable(name="x"), alias=None),
            ],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, unwind, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have ScanNodes, then Unwind
        assert isinstance(operators[0], ScanNodes)
        assert isinstance(operators[1], Unwind)
