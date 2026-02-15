"""Unit tests for filter pushdown optimization pass."""

from graphforge.ast.clause import ReturnItem
from graphforge.ast.expression import BinaryOp, Literal, PropertyAccess, Variable
from graphforge.optimizer.optimizer import QueryOptimizer
from graphforge.planner.operators import (
    ExpandEdges,
    Filter,
    OptionalScanNodes,
    Project,
    ScanNodes,
    With,
)


class TestFilterPushdownBasic:
    """Basic filter pushdown scenarios."""

    def test_push_into_scan_nodes(self):
        """Filter on node property is pushed into ScanNodes."""
        ops = [
            ScanNodes(variable="n", labels=[["Person"]]),
            Filter(
                predicate=BinaryOp(
                    op="=",
                    left=PropertyAccess(variable="n", property="name"),
                    right=Literal(value="Alice"),
                )
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Filter should be pushed into ScanNodes
        assert len(result) == 1
        assert isinstance(result[0], ScanNodes)
        assert result[0].predicate is not None
        assert isinstance(result[0].predicate, BinaryOp)
        assert result[0].predicate.op == "="

    def test_push_into_expand_edges(self):
        """Filter on edge property is pushed into ExpandEdges."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
            Filter(
                predicate=BinaryOp(
                    op=">",
                    left=PropertyAccess(variable="r", property="since"),
                    right=Literal(value=2020),
                )
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Filter should be pushed into ExpandEdges
        assert len(result) == 2
        assert isinstance(result[0], ScanNodes)
        assert isinstance(result[1], ExpandEdges)
        assert result[1].predicate is not None
        assert isinstance(result[1].predicate, BinaryOp)
        assert result[1].predicate.op == ">"

    def test_dont_push_with_unbound_variables(self):
        """Filter with unbound variables is not pushed."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            Filter(
                predicate=BinaryOp(
                    op=">",
                    left=PropertyAccess(variable="a", property="age"),
                    right=PropertyAccess(variable="b", property="age"),  # b is unbound!
                )
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Filter should remain unpushed
        assert len(result) == 2
        assert isinstance(result[0], ScanNodes)
        assert result[0].predicate is None  # Not pushed
        assert isinstance(result[1], Filter)

    def test_filter_with_no_operators_remains(self):
        """Filter with no preceding operators remains."""
        ops = [
            Filter(
                predicate=BinaryOp(
                    op="=",
                    left=Variable(name="x"),
                    right=Literal(value=5),
                )
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Filter should remain
        assert len(result) == 1
        assert isinstance(result[0], Filter)


class TestFilterPushdownConjuncts:
    """Test pushing AND-combined predicates."""

    def test_push_and_conjuncts_separately(self):
        """AND predicates are split and pushed separately."""
        ops = [
            ScanNodes(variable="n", labels=[["Person"]]),
            Filter(
                predicate=BinaryOp(
                    op="AND",
                    left=BinaryOp(
                        op="=",
                        left=PropertyAccess(variable="n", property="name"),
                        right=Literal(value="Alice"),
                    ),
                    right=BinaryOp(
                        op=">",
                        left=PropertyAccess(variable="n", property="age"),
                        right=Literal(value=25),
                    ),
                )
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Both predicates pushed into ScanNodes
        assert len(result) == 1
        assert isinstance(result[0], ScanNodes)
        assert result[0].predicate is not None
        # Predicate should be AND-combined
        assert isinstance(result[0].predicate, BinaryOp)
        assert result[0].predicate.op == "AND"

    def test_push_some_conjuncts_keep_others(self):
        """Push compatible conjuncts, keep incompatible in Filter."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
            Filter(
                predicate=BinaryOp(
                    op="AND",
                    left=BinaryOp(
                        op="=",
                        left=PropertyAccess(variable="a", property="name"),
                        right=Literal(value="Alice"),
                    ),
                    right=BinaryOp(
                        op=">",
                        left=PropertyAccess(variable="b", property="age"),
                        right=Literal(value=25),
                    ),
                )
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # First predicate pushed into ScanNodes, second into ExpandEdges
        assert len(result) == 2
        assert isinstance(result[0], ScanNodes)
        assert result[0].predicate is not None  # a.name = "Alice" pushed here
        assert isinstance(result[1], ExpandEdges)
        assert result[1].predicate is not None  # b.age > 25 pushed here


class TestFilterPushdownBoundaries:
    """Test pipeline boundaries prevent pushdown."""

    def test_dont_push_across_with(self):
        """Filter cannot be pushed across WITH clause."""
        ops = [
            ScanNodes(variable="n", labels=[["Person"]]),
            With(items=[ReturnItem(expression=Variable(name="n"), alias="n")]),
            Filter(
                predicate=BinaryOp(
                    op="=",
                    left=PropertyAccess(variable="n", property="name"),
                    right=Literal(value="Alice"),
                )
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Filter should remain after WITH
        assert len(result) == 3
        assert isinstance(result[0], ScanNodes)
        assert result[0].predicate is None  # Not pushed
        assert isinstance(result[1], With)
        assert isinstance(result[2], Filter)

    def test_push_before_with_boundary(self):
        """Filter before WITH can be pushed."""
        ops = [
            ScanNodes(variable="n", labels=[["Person"]]),
            Filter(
                predicate=BinaryOp(
                    op="=",
                    left=PropertyAccess(variable="n", property="name"),
                    right=Literal(value="Alice"),
                )
            ),
            With(items=[ReturnItem(expression=Variable(name="n"), alias="n")]),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Filter should be pushed into ScanNodes
        assert len(result) == 2
        assert isinstance(result[0], ScanNodes)
        assert result[0].predicate is not None
        assert isinstance(result[1], With)


class TestFilterPushdownOptional:
    """Test Optional operators prevent pushdown."""

    def test_dont_push_into_optional_scan(self):
        """Filter cannot be pushed into OptionalScanNodes (breaks NULL semantics)."""
        ops = [
            OptionalScanNodes(variable="n", labels=[["Person"]]),
            Filter(
                predicate=BinaryOp(
                    op="=",
                    left=PropertyAccess(variable="n", property="name"),
                    right=Literal(value="Alice"),
                )
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Filter should NOT be pushed into OptionalScanNodes
        assert len(result) == 2
        assert isinstance(result[0], OptionalScanNodes)
        # OptionalScanNodes doesn't have predicate field (and shouldn't)
        assert isinstance(result[1], Filter)  # Filter remains separate


class TestFilterPushdownCombine:
    """Test combining with existing predicates."""

    def test_combine_with_existing_scan_predicate(self):
        """Pushed predicate combines with existing ScanNodes predicate."""
        ops = [
            ScanNodes(
                variable="n",
                labels=[["Person"]],
                predicate=BinaryOp(
                    op=">",
                    left=PropertyAccess(variable="n", property="age"),
                    right=Literal(value=18),
                ),
            ),
            Filter(
                predicate=BinaryOp(
                    op="=",
                    left=PropertyAccess(variable="n", property="name"),
                    right=Literal(value="Alice"),
                )
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Filter pushed and combined with existing predicate
        assert len(result) == 1
        assert isinstance(result[0], ScanNodes)
        assert result[0].predicate is not None
        # Should be AND-combined
        assert isinstance(result[0].predicate, BinaryOp)
        assert result[0].predicate.op == "AND"

    def test_combine_with_existing_expand_predicate(self):
        """Pushed predicate combines with existing ExpandEdges predicate."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
                predicate=BinaryOp(
                    op=">",
                    left=PropertyAccess(variable="r", property="since"),
                    right=Literal(value=2020),
                ),
            ),
            Filter(
                predicate=BinaryOp(
                    op="=",
                    left=PropertyAccess(variable="b", property="active"),
                    right=Literal(value=True),
                )
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Filter pushed and combined with existing predicate
        assert len(result) == 2
        assert isinstance(result[1], ExpandEdges)
        assert result[1].predicate is not None
        # Should be AND-combined
        assert isinstance(result[1].predicate, BinaryOp)
        assert result[1].predicate.op == "AND"


class TestFilterPushdownDisabled:
    """Test disabling filter pushdown."""

    def test_filter_pushdown_disabled(self):
        """When disabled, filters are not pushed."""
        ops = [
            ScanNodes(variable="n", labels=[["Person"]]),
            Filter(
                predicate=BinaryOp(
                    op="=",
                    left=PropertyAccess(variable="n", property="name"),
                    right=Literal(value="Alice"),
                )
            ),
        ]

        optimizer = QueryOptimizer(enable_filter_pushdown=False)
        result = optimizer.optimize(ops)

        # Filter should remain unpushed
        assert len(result) == 2
        assert isinstance(result[0], ScanNodes)
        assert result[0].predicate is None
        assert isinstance(result[1], Filter)


class TestFilterPushdownEdgeCases:
    """Edge cases for filter pushdown."""

    def test_multiple_filters(self):
        """Multiple Filter operators are handled correctly."""
        ops = [
            ScanNodes(variable="n", labels=[["Person"]]),
            Filter(
                predicate=BinaryOp(
                    op="=",
                    left=PropertyAccess(variable="n", property="name"),
                    right=Literal(value="Alice"),
                )
            ),
            Filter(
                predicate=BinaryOp(
                    op=">",
                    left=PropertyAccess(variable="n", property="age"),
                    right=Literal(value=25),
                )
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Both filters should be pushed into ScanNodes
        assert len(result) == 1
        assert isinstance(result[0], ScanNodes)
        assert result[0].predicate is not None

    def test_filter_between_other_operators(self):
        """Filter in middle of pipeline is handled correctly."""
        ops = [
            ScanNodes(variable="n", labels=[["Person"]]),
            Filter(
                predicate=BinaryOp(
                    op="=",
                    left=PropertyAccess(variable="n", property="name"),
                    right=Literal(value="Alice"),
                )
            ),
            Project(items=[ReturnItem(expression=Variable(name="n"), alias="person")]),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Filter pushed, Project remains
        assert len(result) == 2
        assert isinstance(result[0], ScanNodes)
        assert result[0].predicate is not None
        assert isinstance(result[1], Project)
