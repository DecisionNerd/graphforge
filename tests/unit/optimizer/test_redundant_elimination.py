"""Unit tests for redundant traversal elimination optimization pass."""

from graphforge.ast.clause import ReturnItem
from graphforge.ast.expression import BinaryOp, Literal, PropertyAccess, Variable
from graphforge.optimizer.optimizer import QueryOptimizer
from graphforge.planner.operators import (
    ExpandEdges,
    ExpandVariableLength,
    Filter,
    Project,
    ScanNodes,
    Subquery,
    Union,
    With,
)


class TestRedundantEliminationBasic:
    """Basic redundant elimination scenarios."""

    def test_eliminate_duplicate_scan_nodes(self):
        """Duplicate ScanNodes operators are eliminated."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="a", labels=[["Person"]]),  # Duplicate
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Second ScanNodes should be removed
        assert len(result) == 1
        assert isinstance(result[0], ScanNodes)
        assert result[0].variable == "a"

    def test_eliminate_duplicate_expand_edges(self):
        """Duplicate ExpandEdges operators are eliminated."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),  # Duplicate
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Second ExpandEdges should be removed
        assert len(result) == 2
        assert isinstance(result[0], ScanNodes)
        assert isinstance(result[1], ExpandEdges)

    def test_eliminate_duplicate_expand_variable_length(self):
        """Duplicate ExpandVariableLength operators are eliminated."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandVariableLength(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
                min_hops=1,
                max_hops=3,
            ),
            ExpandVariableLength(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
                min_hops=1,
                max_hops=3,
            ),  # Duplicate
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Second ExpandVariableLength should be removed
        assert len(result) == 2
        assert isinstance(result[0], ScanNodes)
        assert isinstance(result[1], ExpandVariableLength)

    def test_eliminate_multiple_duplicates(self):
        """Multiple duplicates are all eliminated."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="a", labels=[["Person"]]),  # Duplicate 1
            ScanNodes(variable="a", labels=[["Person"]]),  # Duplicate 2
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Only first should remain
        assert len(result) == 1
        assert isinstance(result[0], ScanNodes)


class TestRedundantEliminationNonDuplicates:
    """Test cases for operators that should NOT be eliminated."""

    def test_dont_eliminate_different_variables(self):
        """Operators with different variables are not eliminated."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="b", labels=[["Person"]]),  # Different variable
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Both should remain
        assert len(result) == 2
        assert result[0].variable == "a"
        assert result[1].variable == "b"

    def test_dont_eliminate_different_labels(self):
        """Operators with different labels are not eliminated."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="a", labels=[["Company"]]),  # Different labels
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Both should remain
        assert len(result) == 2
        assert result[0].labels == [["Person"]]
        assert result[1].labels == [["Company"]]

    def test_dont_eliminate_different_predicates(self):
        """Operators with different predicates are not eliminated."""
        ops = [
            ScanNodes(
                variable="a",
                labels=[["Person"]],
                predicate=BinaryOp(
                    op="=",
                    left=PropertyAccess(variable="a", property="age"),
                    right=Literal(value=30),
                ),
            ),
            ScanNodes(
                variable="a",
                labels=[["Person"]],
                predicate=BinaryOp(
                    op=">",
                    left=PropertyAccess(variable="a", property="age"),
                    right=Literal(value=25),
                ),
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Both should remain (different predicates)
        assert len(result) == 2

    def test_dont_eliminate_different_edge_types(self):
        """ExpandEdges with different edge types are not eliminated."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r1",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
            ExpandEdges(
                src_var="a",
                edge_var="r2",
                dst_var="c",
                edge_types=["LIKES"],
                direction="OUT",
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Both ExpandEdges should remain
        assert len(result) == 3
        assert isinstance(result[0], ScanNodes)
        assert isinstance(result[1], ExpandEdges)
        assert isinstance(result[2], ExpandEdges)
        assert result[1].edge_types == ["KNOWS"]
        assert result[2].edge_types == ["LIKES"]

    def test_dont_eliminate_different_directions(self):
        """ExpandEdges with different directions are not eliminated."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r1",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
            ExpandEdges(
                src_var="a",
                edge_var="r2",
                dst_var="c",
                edge_types=["KNOWS"],
                direction="IN",
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Both ExpandEdges should remain (different directions)
        assert len(result) == 3
        assert result[1].direction == "OUT"
        assert result[2].direction == "IN"

    def test_dont_eliminate_different_hop_ranges(self):
        """ExpandVariableLength with different hop ranges are not eliminated."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandVariableLength(
                src_var="a",
                edge_var="r1",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
                min_hops=1,
                max_hops=3,
            ),
            ExpandVariableLength(
                src_var="a",
                edge_var="r2",
                dst_var="c",
                edge_types=["KNOWS"],
                direction="OUT",
                min_hops=2,
                max_hops=5,
            ),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Both should remain (different hop ranges)
        assert len(result) == 3
        assert result[1].min_hops == 1
        assert result[1].max_hops == 3
        assert result[2].min_hops == 2
        assert result[2].max_hops == 5


class TestRedundantEliminationBoundaries:
    """Test cases for pipeline boundaries."""

    def test_dont_eliminate_across_with_boundary(self):
        """Duplicates separated by WITH are not eliminated."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            With(items=[ReturnItem(expression=Variable(name="a"), alias="a")]),
            ScanNodes(variable="a", labels=[["Person"]]),  # After WITH
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Both ScanNodes should remain (WITH is a boundary)
        assert len(result) == 3
        assert isinstance(result[0], ScanNodes)
        assert isinstance(result[1], With)
        assert isinstance(result[2], ScanNodes)

    def test_dont_eliminate_across_union_boundary(self):
        """Duplicates separated by UNION are not eliminated."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            Union(branches=[[], []], all=False),
            ScanNodes(variable="a", labels=[["Person"]]),  # After UNION
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Both ScanNodes should remain (UNION is a boundary)
        assert len(result) == 3
        assert isinstance(result[0], ScanNodes)
        assert isinstance(result[1], Union)
        assert isinstance(result[2], ScanNodes)

    def test_dont_eliminate_across_subquery_boundary(self):
        """Duplicates separated by Subquery are not eliminated."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            Subquery(
                operators=[ScanNodes(variable="n", labels=[["Person"]])],
                expression_type="EXISTS",
            ),
            ScanNodes(variable="a", labels=[["Person"]]),  # After Subquery
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Both ScanNodes should remain (Subquery is a boundary)
        assert len(result) == 3
        assert isinstance(result[0], ScanNodes)
        assert isinstance(result[1], Subquery)
        assert isinstance(result[2], ScanNodes)

    def test_eliminate_before_boundary_and_after_separately(self):
        """Duplicates before and after boundary are eliminated independently."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="a", labels=[["Person"]]),  # Duplicate (before WITH)
            With(items=[ReturnItem(expression=Variable(name="a"), alias="a")]),
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="a", labels=[["Person"]]),  # Duplicate (after WITH)
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Should have: ScanNodes, WITH, ScanNodes (duplicates eliminated in each section)
        assert len(result) == 3
        assert isinstance(result[0], ScanNodes)
        assert isinstance(result[1], With)
        assert isinstance(result[2], ScanNodes)


class TestRedundantEliminationComplex:
    """Complex scenarios with mixed operators."""

    def test_eliminate_keeps_non_duplicates(self):
        """Mixed duplicates and non-duplicates are handled correctly."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="b", labels=[["Company"]]),
            ScanNodes(variable="a", labels=[["Person"]]),  # Duplicate
            ScanNodes(variable="b", labels=[["Company"]]),  # Duplicate
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # First occurrence of each should remain
        assert len(result) == 2
        assert isinstance(result[0], ScanNodes)
        assert result[0].variable == "a"
        assert isinstance(result[1], ScanNodes)
        assert result[1].variable == "b"

    def test_eliminate_with_interleaved_non_scan_operators(self):
        """Duplicates with non-scan operators in between are eliminated."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            Filter(
                predicate=BinaryOp(
                    op=">",
                    left=PropertyAccess(variable="a", property="age"),
                    right=Literal(value=18),
                )
            ),
            ScanNodes(variable="a", labels=[["Person"]]),  # Duplicate
            Project(items=[ReturnItem(expression=Variable(name="a"), alias="a")]),
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Duplicate ScanNodes should be removed, but Filter and Project remain
        assert len(result) == 3
        assert isinstance(result[0], ScanNodes)
        # Note: Filter might be pushed down into ScanNodes due to filter pushdown pass
        # So we check that we have fewer operators than the input
        assert any(isinstance(op, Project) for op in result)

    def test_eliminate_with_same_predicate(self):
        """Operators with identical predicates are considered duplicates."""
        predicate = BinaryOp(
            op="=",
            left=PropertyAccess(variable="a", property="age"),
            right=Literal(value=30),
        )
        ops = [
            ScanNodes(variable="a", labels=[["Person"]], predicate=predicate),
            ScanNodes(variable="a", labels=[["Person"]], predicate=predicate),  # Duplicate
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Second ScanNodes should be removed
        assert len(result) == 1
        assert isinstance(result[0], ScanNodes)

    def test_eliminate_with_none_predicate(self):
        """Operators with None predicates are considered duplicates."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]], predicate=None),
            ScanNodes(variable="a", labels=[["Person"]], predicate=None),  # Duplicate
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Second ScanNodes should be removed
        assert len(result) == 1
        assert isinstance(result[0], ScanNodes)

    def test_eliminate_complex_pattern(self):
        """Complex query pattern with multiple duplicates."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),
            ScanNodes(variable="a", labels=[["Person"]]),  # Duplicate scan
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
            ),  # Duplicate expand (same signature)
        ]

        optimizer = QueryOptimizer()
        result = optimizer.optimize(ops)

        # Both duplicates should be removed
        assert len(result) == 2
        assert isinstance(result[0], ScanNodes)
        assert isinstance(result[1], ExpandEdges)


class TestRedundantEliminationDisabled:
    """Test that pass can be disabled."""

    def test_disable_redundant_elimination(self):
        """Redundant elimination can be disabled."""
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="a", labels=[["Person"]]),  # Would be duplicate
        ]

        optimizer = QueryOptimizer(enable_redundant_elimination=False)
        result = optimizer.optimize(ops)

        # Both should remain when pass is disabled
        assert len(result) == 2
        assert isinstance(result[0], ScanNodes)
        assert isinstance(result[1], ScanNodes)
