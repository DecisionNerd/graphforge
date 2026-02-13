"""Edge case tests for query planner.

Tests for rare or edge case scenarios in query planning.
"""

import pytest

from graphforge.ast.clause import (
    MatchClause,
    OptionalMatchClause,
    ReturnClause,
    ReturnItem,
    SkipClause,
)
from graphforge.ast.expression import Variable
from graphforge.ast.pattern import Direction, NodePattern, RelationshipPattern
from graphforge.ast.query import CypherQuery
from graphforge.planner.planner import QueryPlanner


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases in query planning."""

    def test_match_with_empty_pattern_list(self):
        """Plan MATCH with empty pattern (should skip)."""
        # Pattern list contains None or empty elements
        match = MatchClause(patterns=[None])  # type: ignore[list-item]

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should skip the None pattern and only have Project operator
        assert len([op for op in operators if hasattr(op, "variable")]) == 0

    def test_match_with_pattern_dict_and_parts(self):
        """Plan MATCH with pattern dict format (new style)."""
        # Pattern dict with parts key (new format)
        node = NodePattern(variable="n")
        match = MatchClause(patterns=[{"path_variable": None, "parts": [node]}])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should handle new format correctly
        from graphforge.planner.operators import ScanNodes

        scan_ops = [op for op in operators if isinstance(op, ScanNodes)]
        assert len(scan_ops) == 1
        assert scan_ops[0].path_var is None

    def test_optional_match_with_empty_pattern(self):
        """Plan OPTIONAL MATCH with empty pattern."""
        # Empty pattern
        optional_match = OptionalMatchClause(patterns=[None])  # type: ignore[list-item]

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[optional_match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should skip the None pattern
        assert len([op for op in operators if hasattr(op, "variable")]) == 0

    def test_properties_to_predicate_with_empty_properties(self):
        """Test _properties_to_predicate with empty dict."""
        planner = QueryPlanner()
        result = planner._properties_to_predicate("n", {})
        assert result is None

    def test_match_with_src_node_properties_in_relationship_pattern(self):
        """Plan MATCH where src node has inline properties."""
        # Source node with properties
        src_node = NodePattern(variable="a", properties={"age": Variable(name="x")})
        rel = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
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

        # Should have Filter for source node properties
        from graphforge.planner.operators import Filter

        filters = [op for op in operators if isinstance(op, Filter)]
        assert len(filters) >= 1

    def test_optional_match_src_node_with_properties(self):
        """Plan OPTIONAL MATCH where src node has properties."""
        src_node = NodePattern(variable="a", properties={"name": Variable(name="x")})
        rel = RelationshipPattern(
            variable="r",
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        dst_node = NodePattern(variable="b")

        match = MatchClause(patterns=[[src_node]])
        optional_match = OptionalMatchClause(patterns=[[src_node, rel, dst_node]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="b"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, optional_match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have Filter for source node properties
        from graphforge.planner.operators import Filter

        filters = [op for op in operators if isinstance(op, Filter)]
        assert len(filters) >= 1

    def test_match_complex_inline_properties(self):
        """Plan MATCH with multiple inline properties on same node."""
        properties = {
            "name": Variable(name="x"),
            "age": Variable(name="y"),
            "city": Variable(name="z"),
        }
        node_pattern = NodePattern(variable="n", labels=["Person"], properties=properties)
        match = MatchClause(patterns=[[node_pattern]])

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have Filter with nested AND operators
        from graphforge.planner.operators import Filter

        filter_ops = [op for op in operators if isinstance(op, Filter)]
        assert len(filter_ops) == 1
        # The predicate should combine all properties with AND
        predicate = filter_ops[0].predicate
        assert predicate.op == "AND"

    def test_anonymous_variable_generation_increments(self):
        """Test that anonymous variable counter increments correctly."""
        planner = QueryPlanner()

        var1 = planner._generate_anonymous_variable()
        var2 = planner._generate_anonymous_variable()
        var3 = planner._generate_anonymous_variable()

        # Each should be unique and incrementing
        assert var1 == "__anon_0"
        assert var2 == "__anon_1"
        assert var3 == "__anon_2"

    def test_match_multi_hop_with_partial_anonymous_relationships(self):
        """Plan multi-hop MATCH with some anonymous, some named relationships."""
        src_node = NodePattern(variable="a")
        rel1 = RelationshipPattern(
            variable="r1",  # Named
            types=["KNOWS"],
            direction=Direction.OUT,
            min_hops=None,
            max_hops=None,
            predicate=None,
        )
        mid_node = NodePattern(variable="b")
        rel2 = RelationshipPattern(
            variable=None,  # Anonymous
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

        # Should use individual ExpandEdges (no path variable)
        from graphforge.planner.operators import ExpandEdges

        expand_ops = [op for op in operators if isinstance(op, ExpandEdges)]
        assert len(expand_ops) == 2
        # First relationship should have named variable
        assert expand_ops[0].edge_var == "r1"
        # Second relationship should have None (anonymous in multi-hop without path)
        assert expand_ops[1].edge_var is None

    def test_aggregation_function_case_insensitive(self):
        """Test that aggregation function detection is case-insensitive."""
        from graphforge.ast.expression import FunctionCall

        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        # Use lowercase function name
        count_expr = FunctionCall(
            name="count",  # lowercase
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

        # Should still detect as aggregation
        from graphforge.planner.operators import Aggregate

        assert any(isinstance(op, Aggregate) for op in operators)

    def test_with_skip_without_limit(self):
        """Plan WITH with only SKIP (no LIMIT)."""
        from graphforge.ast.clause import WithClause

        node_pattern = NodePattern(variable="n")
        match = MatchClause(patterns=[[node_pattern]])

        with_clause = WithClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
            where=None,
            order_by=None,
            skip=SkipClause(count=5),
            limit=None,  # No LIMIT
        )

        return_clause = ReturnClause(
            items=[ReturnItem(expression=Variable(name="n"), alias=None)],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, with_clause, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have With with skip_count but no limit_count
        from graphforge.planner.operators import With

        with_op = next(op for op in operators if isinstance(op, With))
        assert with_op.skip_count == 5
        assert with_op.limit_count is None

    def test_all_aggregation_function_types(self):
        """Test detection of all aggregation function types."""
        from graphforge.ast.expression import FunctionCall

        planner = QueryPlanner()

        agg_functions = [
            "COUNT",
            "SUM",
            "AVG",
            "MIN",
            "MAX",
            "COLLECT",
            "PERCENTILEDISC",
            "PERCENTILECONT",
            "STDEV",
            "STDEVP",
        ]

        for func_name in agg_functions:
            expr = FunctionCall(name=func_name, args=[Variable(name="n")], distinct=False)
            assert planner._contains_aggregate(expr) is True

    def test_non_aggregation_functions(self):
        """Test that non-aggregation functions are not detected as aggregates."""
        from graphforge.ast.expression import FunctionCall

        planner = QueryPlanner()

        non_agg_functions = ["toInteger", "toString", "size", "length", "type", "labels"]

        for func_name in non_agg_functions:
            expr = FunctionCall(name=func_name, args=[Variable(name="n")], distinct=False)
            assert planner._contains_aggregate(expr) is False

    def test_match_with_both_old_and_new_format_patterns(self):
        """Plan MATCH with mixed old (list) and new (dict) format patterns."""
        # Old format: plain list
        old_pattern = [NodePattern(variable="n")]

        # New format: dict with parts
        new_pattern = {
            "path_variable": None,
            "parts": [NodePattern(variable="m")],
        }

        match = MatchClause(patterns=[old_pattern, new_pattern])

        return_clause = ReturnClause(
            items=[
                ReturnItem(expression=Variable(name="n"), alias=None),
                ReturnItem(expression=Variable(name="m"), alias=None),
            ],
            distinct=False,
        )

        query = CypherQuery(clauses=[match, return_clause])
        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should handle both formats
        from graphforge.planner.operators import ScanNodes

        scan_ops = [op for op in operators if isinstance(op, ScanNodes)]
        assert len(scan_ops) == 2
