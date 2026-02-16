"""Unit tests for aggregate pushdown optimization."""

from graphforge.ast.clause import ReturnItem
from graphforge.ast.expression import FunctionCall, Variable
from graphforge.optimizer.optimizer import QueryOptimizer
from graphforge.planner.operators import (
    Aggregate,
    ExpandEdges,
    Filter,
    ScanNodes,
    With,
)


class TestAggregatePushdownBasic:
    """Test basic aggregate pushdown detection and transformation."""

    def test_pushdown_simple_count(self):
        """COUNT with GROUP BY source should be pushed down."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
            Aggregate(
                grouping_exprs=[Variable(name="a")],
                agg_exprs=[FunctionCall(name="count", args=[Variable(name="b")])],
                return_items=[
                    ReturnItem(
                        expression=Variable(name="a"),
                        alias="a",
                    ),
                    ReturnItem(
                        expression=FunctionCall(name="count", args=[Variable(name="b")]),
                        alias="count",
                    ),
                ],
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Should have: ScanNodes, Enhanced ExpandEdges (no Aggregate)
        assert len(result) == 2
        assert isinstance(result[0], ScanNodes)
        assert isinstance(result[1], ExpandEdges)
        assert result[1].agg_hint is not None
        assert result[1].agg_hint.func == "COUNT"
        assert result[1].agg_hint.group_by == ["a"]
        assert result[1].agg_hint.result_var == "count"

    def test_pushdown_count_star(self):
        """COUNT(*) should be pushed down."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
            Aggregate(
                grouping_exprs=[Variable(name="a")],
                agg_exprs=[FunctionCall(name="count", args=[])],  # COUNT(*)
                return_items=[
                    ReturnItem(expression=Variable(name="a"), alias="a"),
                    ReturnItem(
                        expression=FunctionCall(name="count", args=[]),
                        alias="count",
                    ),
                ],
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        assert len(result) == 2
        assert isinstance(result[1], ExpandEdges)
        assert result[1].agg_hint is not None
        assert result[1].agg_hint.func == "COUNT"
        assert result[1].agg_hint.expr is None  # COUNT(*) has no expression

    def test_pushdown_sum(self):
        """SUM aggregation should be pushed down."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["WORKS_FOR"],
                direction="OUT",
            ),
            Aggregate(
                grouping_exprs=[Variable(name="a")],
                agg_exprs=[
                    FunctionCall(
                        name="sum",
                        args=[
                            Variable(name="r")  # Simplified - real would be PropertyAccess
                        ],
                    )
                ],
                return_items=[
                    ReturnItem(expression=Variable(name="a"), alias="a"),
                    ReturnItem(
                        expression=FunctionCall(name="sum", args=[Variable(name="r")]),
                        alias="total",
                    ),
                ],
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        assert len(result) == 2
        assert isinstance(result[1], ExpandEdges)
        assert result[1].agg_hint is not None
        assert result[1].agg_hint.func == "SUM"
        assert result[1].agg_hint.result_var == "total"

    def test_pushdown_min(self):
        """MIN aggregation should be pushed down."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["RATED"],
                direction="OUT",
            ),
            Aggregate(
                grouping_exprs=[Variable(name="a")],
                agg_exprs=[FunctionCall(name="min", args=[Variable(name="r")])],
                return_items=[
                    ReturnItem(expression=Variable(name="a"), alias="a"),
                    ReturnItem(
                        expression=FunctionCall(name="min", args=[Variable(name="r")]),
                        alias="min_rating",
                    ),
                ],
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        assert len(result) == 2
        assert isinstance(result[1], ExpandEdges)
        assert result[1].agg_hint is not None
        assert result[1].agg_hint.func == "MIN"

    def test_pushdown_max(self):
        """MAX aggregation should be pushed down."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["RATED"],
                direction="OUT",
            ),
            Aggregate(
                grouping_exprs=[Variable(name="a")],
                agg_exprs=[FunctionCall(name="max", args=[Variable(name="r")])],
                return_items=[
                    ReturnItem(expression=Variable(name="a"), alias="a"),
                    ReturnItem(
                        expression=FunctionCall(name="max", args=[Variable(name="r")]),
                        alias="max_rating",
                    ),
                ],
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        assert len(result) == 2
        assert isinstance(result[1], ExpandEdges)
        assert result[1].agg_hint is not None
        assert result[1].agg_hint.func == "MAX"


class TestAggregatePushdownSafety:
    """Test safety checks that prevent incorrect pushdowns."""

    def test_dont_push_collect(self):
        """COLLECT must materialize all values, can't push down."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
            Aggregate(
                grouping_exprs=[Variable(name="a")],
                agg_exprs=[FunctionCall(name="collect", args=[Variable(name="b")])],
                return_items=[
                    ReturnItem(expression=Variable(name="a"), alias="a"),
                    ReturnItem(
                        expression=FunctionCall(name="collect", args=[Variable(name="b")]),
                        alias="friends",
                    ),
                ],
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Should NOT push down - Aggregate remains
        assert len(result) == 3
        assert isinstance(result[2], Aggregate)
        # ExpandEdges should not have agg_hint
        assert result[1].agg_hint is None

    def test_dont_push_avg(self):
        """AVG requires both sum and count, complex for incremental."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["RATED"],
                direction="OUT",
            ),
            Aggregate(
                grouping_exprs=[Variable(name="a")],
                agg_exprs=[FunctionCall(name="avg", args=[Variable(name="r")])],
                return_items=[
                    ReturnItem(expression=Variable(name="a"), alias="a"),
                    ReturnItem(
                        expression=FunctionCall(name="avg", args=[Variable(name="r")]),
                        alias="avg_rating",
                    ),
                ],
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Should NOT push down
        assert len(result) == 3
        assert isinstance(result[2], Aggregate)

    def test_dont_push_distinct_aggregation(self):
        """DISTINCT aggregations need deduplication tracking."""
        # Create FunctionCall with distinct=True (Pydantic models are frozen)
        agg_func = FunctionCall(name="count", args=[Variable(name="b")], distinct=True)

        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
            Aggregate(
                grouping_exprs=[Variable(name="a")],
                agg_exprs=[agg_func],
                return_items=[
                    ReturnItem(expression=Variable(name="a"), alias="a"),
                    ReturnItem(expression=agg_func, alias="count"),
                ],
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Should NOT push down
        assert len(result) == 3
        assert isinstance(result[2], Aggregate)

    def test_dont_push_multiple_aggregations(self):
        """Multiple aggregation functions are complex to coordinate."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["RATED"],
                direction="OUT",
            ),
            Aggregate(
                grouping_exprs=[Variable(name="a")],
                agg_exprs=[
                    FunctionCall(name="count", args=[Variable(name="b")]),
                    FunctionCall(name="sum", args=[Variable(name="r")]),
                ],
                return_items=[
                    ReturnItem(expression=Variable(name="a"), alias="a"),
                    ReturnItem(
                        expression=FunctionCall(name="count", args=[Variable(name="b")]),
                        alias="count",
                    ),
                    ReturnItem(
                        expression=FunctionCall(name="sum", args=[Variable(name="r")]),
                        alias="total",
                    ),
                ],
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Should NOT push down
        assert len(result) == 3
        assert isinstance(result[2], Aggregate)

    def test_dont_push_without_group_by_source(self):
        """GROUP BY must include source variable."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["WORKS_FOR"],
                direction="OUT",
            ),
            Aggregate(
                grouping_exprs=[Variable(name="b")],  # Grouped by dst, not src
                agg_exprs=[FunctionCall(name="count", args=[Variable(name="a")])],
                return_items=[
                    ReturnItem(expression=Variable(name="b"), alias="b"),
                    ReturnItem(
                        expression=FunctionCall(name="count", args=[Variable(name="a")]),
                        alias="count",
                    ),
                ],
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Should NOT push down
        assert len(result) == 3
        assert isinstance(result[2], Aggregate)

    def test_dont_push_without_grouping(self):
        """Aggregation without GROUP BY can't be pushed."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
            Aggregate(
                grouping_exprs=[],  # No grouping
                agg_exprs=[FunctionCall(name="count", args=[Variable(name="b")])],
                return_items=[
                    ReturnItem(
                        expression=FunctionCall(name="count", args=[Variable(name="b")]),
                        alias="total",
                    ),
                ],
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Should NOT push down
        assert len(result) == 3
        assert isinstance(result[2], Aggregate)


class TestAggregatePushdownBoundaries:
    """Test that pushdown respects pipeline boundaries."""

    def test_dont_push_across_with(self):
        """WITH clause is a pipeline boundary."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            With(
                items=[ReturnItem(expression=Variable(name="a"), alias="a")],
            ),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
            Aggregate(
                grouping_exprs=[Variable(name="a")],
                agg_exprs=[FunctionCall(name="count", args=[Variable(name="b")])],
                return_items=[
                    ReturnItem(expression=Variable(name="a"), alias="a"),
                    ReturnItem(
                        expression=FunctionCall(name="count", args=[Variable(name="b")]),
                        alias="count",
                    ),
                ],
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Pushdown should happen after WITH, but not affect operators before it
        assert len(result) == 3  # ScanNodes, With, Enhanced ExpandEdges
        assert isinstance(result[1], With)
        assert isinstance(result[2], ExpandEdges)
        assert result[2].agg_hint is not None


class TestAggregatePushdownDisabled:
    """Test that pushdown can be disabled."""

    def test_aggregate_pushdown_disabled(self):
        """Verify pushdown doesn't happen when disabled."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
            Aggregate(
                grouping_exprs=[Variable(name="a")],
                agg_exprs=[FunctionCall(name="count", args=[Variable(name="b")])],
                return_items=[
                    ReturnItem(expression=Variable(name="a"), alias="a"),
                    ReturnItem(
                        expression=FunctionCall(name="count", args=[Variable(name="b")]),
                        alias="count",
                    ),
                ],
            ),
        ]

        optimizer = QueryOptimizer(enable_aggregate_pushdown=False)
        result = optimizer.optimize(ops)

        # Should have all 3 operators, no pushdown
        assert len(result) == 3
        assert isinstance(result[2], Aggregate)
        # ExpandEdges should not have agg_hint
        assert result[1].agg_hint is None


class TestAggregatePushdownEdgeCases:
    """Test edge cases and complex scenarios."""

    def test_pushdown_with_filter_between(self):
        """Filter between ExpandEdges and Aggregate: filter pushdown enables aggregate pushdown."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
            Filter(predicate=Variable(name="b")),  # Filter in between
            Aggregate(
                grouping_exprs=[Variable(name="a")],
                agg_exprs=[FunctionCall(name="count", args=[Variable(name="b")])],
                return_items=[
                    ReturnItem(expression=Variable(name="a"), alias="a"),
                    ReturnItem(
                        expression=FunctionCall(name="count", args=[Variable(name="b")]),
                        alias="count",
                    ),
                ],
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Filter pushdown happens first (pushes filter into ExpandEdges predicate)
        # Then aggregate pushdown can happen since ExpandEdges is directly followed by Aggregate
        assert len(result) == 2  # ScanNodes, Enhanced ExpandEdges (filter + aggregation)
        assert isinstance(result[1], ExpandEdges)
        assert result[1].predicate is not None  # Filter was pushed into predicate
        assert result[1].agg_hint is not None  # Aggregate was pushed down

    def test_no_aggregate_after_expand(self):
        """No Aggregate operator means no pushdown."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Should remain unchanged
        assert len(result) == 2
        assert isinstance(result[1], ExpandEdges)
        assert result[1].agg_hint is None
