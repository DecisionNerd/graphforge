"""Additional tests to improve branch coverage in planner.

These tests target specific branch conditions that weren't fully covered.
"""

import pytest

from graphforge.ast.clause import (
    LimitClause,
    MatchClause,
    OptionalMatchClause,
    OrderByClause,
    OrderByItem,
    ReturnClause,
    ReturnItem,
    SkipClause,
    WhereClause,
    WithClause,
)
from graphforge.ast.expression import BinaryOp, FunctionCall, Literal, Variable
from graphforge.ast.pattern import Direction, NodePattern, RelationshipPattern
from graphforge.ast.query import CypherQuery
from graphforge.planner.planner import QueryPlanner


@pytest.mark.unit
class TestBranchCoverage:
    """Tests to improve branch coverage."""

    def test_with_aggregation_and_where(self):
        """Plan WITH with aggregation and WHERE clause."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        count_expr = FunctionCall(
            name="COUNT",
            args=[Variable(name="n")],
            distinct=False,
        )

        predicate = BinaryOp(
            op=">",
            left=Variable(name="cnt"),
            right=Literal(value=0),
        )

        with_clause = WithClause(
            items=[ReturnItem(expression=count_expr, alias="cnt")],
            distinct=False,
            where=WhereClause(predicate=predicate),
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

        # Should have Aggregate + Filter
        from graphforge.planner.operators import Aggregate, Filter

        assert any(isinstance(op, Aggregate) for op in operators)
        # Filter should come after Aggregate
        agg_idx = next(i for i, op in enumerate(operators) if isinstance(op, Aggregate))
        filter_idx = next(i for i, op in enumerate(operators) if isinstance(op, Filter))
        assert filter_idx > agg_idx

    def test_with_aggregation_and_order_by(self):
        """Plan WITH with aggregation and ORDER BY."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        count_expr = FunctionCall(
            name="COUNT",
            args=[Variable(name="n")],
            distinct=False,
        )

        order_item = OrderByItem(
            expression=Variable(name="cnt"),
            ascending=False,
        )

        with_clause = WithClause(
            items=[ReturnItem(expression=count_expr, alias="cnt")],
            distinct=False,
            where=None,
            order_by=OrderByClause(items=[order_item]),
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

        # Should have Aggregate + Sort
        from graphforge.planner.operators import Aggregate, Sort

        assert any(isinstance(op, Aggregate) for op in operators)
        assert any(isinstance(op, Sort) for op in operators)

    def test_with_aggregation_distinct_skip_limit(self):
        """Plan WITH with aggregation, DISTINCT, SKIP, and LIMIT."""
        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        count_expr = FunctionCall(
            name="COUNT",
            args=[Variable(name="n")],
            distinct=False,
        )

        with_clause = WithClause(
            items=[ReturnItem(expression=count_expr, alias="cnt")],
            distinct=True,
            where=None,
            order_by=None,
            skip=SkipClause(count=2),
            limit=LimitClause(count=5),
        )

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="cnt"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, with_clause, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have Aggregate, Distinct, Skip, Limit
        from graphforge.planner.operators import Aggregate, Distinct, Limit, Skip

        assert any(isinstance(op, Aggregate) for op in operators)
        assert any(isinstance(op, Distinct) for op in operators)
        assert any(isinstance(op, Skip) for op in operators)
        assert any(isinstance(op, Limit) for op in operators)

    def test_optional_match_followed_by_regular_match(self):
        """Plan OPTIONAL MATCH followed by regular MATCH."""
        node_a = NodePattern(variable="a")
        optional_match = OptionalMatchClause(patterns=[[node_a]])

        node_b = NodePattern(variable="b")
        match = MatchClause(patterns=[[node_b]])

        return_clause = ReturnClause(
            items=[
                ReturnItem(expression=Variable(name="a"), alias=None),
                ReturnItem(expression=Variable(name="b"), alias=None),
            ],
            distinct=False,
        )

        query = CypherQuery(clauses=[optional_match, match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have OptionalScanNodes and ScanNodes
        from graphforge.planner.operators import OptionalScanNodes, ScanNodes

        assert any(isinstance(op, OptionalScanNodes) for op in operators)
        assert any(isinstance(op, ScanNodes) for op in operators)

    def test_match_multi_hop_variable_length_in_chain(self):
        """Plan multi-hop MATCH where one hop is variable-length."""
        src_node = NodePattern(variable="a")
        rel1 = RelationshipPattern(
            variable="r1",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=1,  # Variable length
            max_hops=3,
            predicate=None,
        )
        mid_node = NodePattern(variable="b")
        rel2 = RelationshipPattern(
            variable="r2",
            types=["LIKES"],
            direction=Direction.OUT,
            min_hops=None,  # Fixed length
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

        # Should NOT use ExpandMultiHop (because of variable-length)
        # Should use individual operators
        from graphforge.planner.operators import ExpandEdges, ExpandMultiHop, ExpandVariableLength

        assert not any(isinstance(op, ExpandMultiHop) for op in operators)
        assert any(isinstance(op, ExpandVariableLength) for op in operators)
        assert any(isinstance(op, ExpandEdges) for op in operators)

    def test_match_relationship_with_incomplete_parts(self):
        """Plan MATCH with relationship pattern that has fewer parts than expected."""
        src_node = NodePattern(variable="a")
        rel = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        # Pattern with only 2 elements (should be 3 for node-rel-node)
        match = MatchClause(patterns=[[src_node, rel]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="a"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Incomplete pattern is skipped, only returns Project
        from graphforge.planner.operators import Project, ScanNodes

        # No ScanNodes since pattern is incomplete
        scan_ops = [op for op in operators if isinstance(op, ScanNodes)]
        assert len(scan_ops) == 0
        # Should still have Project for RETURN
        assert any(isinstance(op, Project) for op in operators)

    def test_optional_match_relationship_incomplete_parts(self):
        """Plan OPTIONAL MATCH with incomplete relationship pattern."""
        src_node = NodePattern(variable="a")
        rel = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )

        match = MatchClause(patterns=[[src_node]])
        # OPTIONAL MATCH with incomplete pattern
        optional_match = OptionalMatchClause(patterns=[[src_node, rel]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="a"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, optional_match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should handle incomplete pattern gracefully
        from graphforge.planner.operators import OptionalExpandEdges

        # No OptionalExpandEdges since pattern is incomplete
        assert not any(isinstance(op, OptionalExpandEdges) for op in operators)

    def test_match_with_non_node_first_element(self):
        """Plan MATCH where first element is not a NodePattern."""
        # This tests the branch where pattern_parts[0] is not NodePattern
        rel = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        dst_node = NodePattern(variable="b")

        # Start with relationship (unusual but tests the branch)
        match = MatchClause(patterns=[[rel, dst_node]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="b"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should handle gracefully (no scan node for first element)
        assert len(operators) >= 1

    def test_match_multi_hop_loop_break_conditions(self):
        """Plan multi-hop MATCH to test loop break conditions."""
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

        # Pattern with only 2 hops total (3 nodes, 2 rels)
        pattern_dict = {
            "path_variable": None,
            "parts": [src_node, rel1, mid_node],
        }

        match = MatchClause(patterns=[pattern_dict])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="b"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have single ExpandEdges
        from graphforge.planner.operators import ExpandEdges

        expand_ops = [op for op in operators if isinstance(op, ExpandEdges)]
        assert len(expand_ops) == 1

    def test_optional_match_non_node_first_element(self):
        """Plan OPTIONAL MATCH where first element is not NodePattern."""
        rel = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        dst_node = NodePattern(variable="b")

        match = MatchClause(patterns=[[NodePattern(variable="a")]])
        # OPTIONAL MATCH starting with relationship
        optional_match = OptionalMatchClause(patterns=[[rel, dst_node]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="b"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, optional_match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should handle gracefully
        assert len(operators) >= 1

    def test_optional_match_relationship_not_relationship_pattern(self):
        """Plan OPTIONAL MATCH where relationship element is not RelationshipPattern."""
        src_node = NodePattern(variable="a")
        # Second element is not RelationshipPattern
        dst_node = NodePattern(variable="b")

        match = MatchClause(patterns=[[src_node]])
        # Pattern with two nodes but no relationship between
        optional_match = OptionalMatchClause(patterns=[[src_node, dst_node]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="b"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, optional_match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should handle missing relationship pattern
        from graphforge.planner.operators import OptionalExpandEdges

        # No expansion since there's no relationship
        assert not any(isinstance(op, OptionalExpandEdges) for op in operators)
