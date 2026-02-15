"""Unit tests for predicate reordering optimization pass."""

from graphforge.ast.expression import BinaryOp, Literal, PropertyAccess, UnaryOp, Variable
from graphforge.optimizer.optimizer import QueryOptimizer
from graphforge.optimizer.predicate_utils import PredicateAnalysis
from graphforge.planner.operators import ExpandEdges, Filter, ScanNodes


class TestPredicateReorderBasic:
    """Basic predicate reordering scenarios."""

    def test_reorder_filter_predicates(self):
        """Filter predicates are reordered by selectivity."""
        # Create filter with: (a <> 1) AND (b = 2) AND (c > 3)
        # Expected order after reordering: (b = 2) AND (c > 3) AND (a <> 1)
        # Selectivity: = (0.1), > (0.5), <> (0.9)
        ops = [
            Filter(
                predicate=BinaryOp(
                    op="AND",
                    left=BinaryOp(op="<>", left=Variable(name="a"), right=Literal(value=1)),
                    right=BinaryOp(
                        op="AND",
                        left=BinaryOp(op="=", left=Variable(name="b"), right=Literal(value=2)),
                        right=BinaryOp(op=">", left=Variable(name="c"), right=Literal(value=3)),
                    ),
                )
            )
        ]

        optimizer = QueryOptimizer(enable_filter_pushdown=False)
        result = optimizer.optimize(ops)

        # Extract reordered conjuncts
        assert len(result) == 1
        assert isinstance(result[0], Filter)
        conjuncts = PredicateAnalysis.extract_conjuncts(result[0].predicate)

        # Check order: equality first, then inequality, then not-equals
        assert conjuncts[0].op == "="  # Most selective
        assert conjuncts[1].op == ">"  # Moderate
        assert conjuncts[2].op == "<>"  # Least selective

    def test_reorder_scan_nodes_predicates(self):
        """ScanNodes predicates are reordered by selectivity."""
        ops = [
            ScanNodes(
                variable="n",
                labels=[["Person"]],
                predicate=BinaryOp(
                    op="AND",
                    left=BinaryOp(
                        op=">",
                        left=PropertyAccess(variable="n", property="age"),
                        right=Literal(value=25),
                    ),
                    right=BinaryOp(
                        op="=",
                        left=PropertyAccess(variable="n", property="name"),
                        right=Literal(value="Alice"),
                    ),
                ),
            )
        ]

        optimizer = QueryOptimizer(enable_filter_pushdown=False)
        result = optimizer.optimize(ops)

        # Extract reordered conjuncts
        assert len(result) == 1
        assert isinstance(result[0], ScanNodes)
        conjuncts = PredicateAnalysis.extract_conjuncts(result[0].predicate)

        # Equality should come first (more selective than >)
        assert conjuncts[0].op == "="
        assert conjuncts[1].op == ">"

    def test_reorder_expand_edges_predicates(self):
        """ExpandEdges predicates are reordered by selectivity."""
        ops = [
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=["KNOWS"],
                direction="OUT",
                predicate=BinaryOp(
                    op="AND",
                    left=BinaryOp(
                        op="<>",
                        left=PropertyAccess(variable="r", property="type"),
                        right=Literal(value="BLOCKED"),
                    ),
                    right=BinaryOp(
                        op="=",
                        left=PropertyAccess(variable="r", property="active"),
                        right=Literal(value=True),
                    ),
                ),
            )
        ]

        optimizer = QueryOptimizer(enable_filter_pushdown=False)
        result = optimizer.optimize(ops)

        # Extract reordered conjuncts
        assert len(result) == 1
        assert isinstance(result[0], ExpandEdges)
        conjuncts = PredicateAnalysis.extract_conjuncts(result[0].predicate)

        # Equality should come first
        assert conjuncts[0].op == "="
        assert conjuncts[1].op == "<>"


class TestPredicateReorderSelectivity:
    """Test selectivity-based reordering."""

    def test_is_null_before_inequality(self):
        """IS NULL (0.1) should be evaluated before inequality (0.5)."""
        ops = [
            Filter(
                predicate=BinaryOp(
                    op="AND",
                    left=BinaryOp(
                        op=">",
                        left=PropertyAccess(variable="a", property="age"),
                        right=Literal(value=25),
                    ),
                    right=UnaryOp(
                        op="IS NULL",
                        operand=PropertyAccess(variable="a", property="email"),
                    ),
                )
            )
        ]

        optimizer = QueryOptimizer(enable_filter_pushdown=False)
        result = optimizer.optimize(ops)

        conjuncts = PredicateAnalysis.extract_conjuncts(result[0].predicate)

        # IS NULL should come first
        assert isinstance(conjuncts[0], UnaryOp)
        assert conjuncts[0].op == "IS NULL"
        assert isinstance(conjuncts[1], BinaryOp)
        assert conjuncts[1].op == ">"

    def test_equality_before_is_not_null(self):
        """Equality (0.1) should be evaluated before IS NOT NULL (0.9)."""
        ops = [
            Filter(
                predicate=BinaryOp(
                    op="AND",
                    left=UnaryOp(
                        op="IS NOT NULL",
                        operand=PropertyAccess(variable="a", property="name"),
                    ),
                    right=BinaryOp(
                        op="=",
                        left=PropertyAccess(variable="a", property="city"),
                        right=Literal(value="NYC"),
                    ),
                )
            )
        ]

        optimizer = QueryOptimizer(enable_filter_pushdown=False)
        result = optimizer.optimize(ops)

        conjuncts = PredicateAnalysis.extract_conjuncts(result[0].predicate)

        # Equality should come first
        assert isinstance(conjuncts[0], BinaryOp)
        assert conjuncts[0].op == "="
        assert isinstance(conjuncts[1], UnaryOp)
        assert conjuncts[1].op == "IS NOT NULL"

    def test_three_level_ordering(self):
        """Three predicates with different selectivities are ordered correctly."""
        # Create: IS NOT NULL (0.9) AND = (0.1) AND > (0.5)
        # Expected: = (0.1) AND > (0.5) AND IS NOT NULL (0.9)
        ops = [
            Filter(
                predicate=BinaryOp(
                    op="AND",
                    left=UnaryOp(
                        op="IS NOT NULL",
                        operand=PropertyAccess(variable="a", property="name"),
                    ),
                    right=BinaryOp(
                        op="AND",
                        left=BinaryOp(
                            op="=",
                            left=PropertyAccess(variable="a", property="city"),
                            right=Literal(value="NYC"),
                        ),
                        right=BinaryOp(
                            op=">",
                            left=PropertyAccess(variable="a", property="age"),
                            right=Literal(value=25),
                        ),
                    ),
                )
            )
        ]

        optimizer = QueryOptimizer(enable_filter_pushdown=False)
        result = optimizer.optimize(ops)

        conjuncts = PredicateAnalysis.extract_conjuncts(result[0].predicate)

        # Check ordering
        assert conjuncts[0].op == "="  # 0.1
        assert conjuncts[1].op == ">"  # 0.5
        assert conjuncts[2].op == "IS NOT NULL"  # 0.9


class TestPredicateReorderOrPreserved:
    """Test that OR predicates are NOT reordered."""

    def test_or_predicate_not_split(self):
        """OR predicates should not be split during reordering."""
        ops = [
            Filter(
                predicate=BinaryOp(
                    op="OR",
                    left=BinaryOp(
                        op="=",
                        left=PropertyAccess(variable="a", property="city"),
                        right=Literal(value="NYC"),
                    ),
                    right=BinaryOp(
                        op="=",
                        left=PropertyAccess(variable="a", property="city"),
                        right=Literal(value="LA"),
                    ),
                )
            )
        ]

        optimizer = QueryOptimizer(enable_filter_pushdown=False)
        result = optimizer.optimize(ops)

        # OR predicate should remain unchanged
        assert len(result) == 1
        assert isinstance(result[0], Filter)
        assert result[0].predicate.op == "OR"

    def test_and_with_or_branches_preserves_or(self):
        """AND with OR branches: reorder AND, preserve OR."""
        # (a OR b) AND c → should become c AND (a OR b) if c is more selective
        ops = [
            Filter(
                predicate=BinaryOp(
                    op="AND",
                    left=BinaryOp(
                        op="OR",
                        left=BinaryOp(
                            op="<>",  # 0.9 selectivity
                            left=PropertyAccess(variable="a", property="status"),
                            right=Literal(value="blocked"),
                        ),
                        right=BinaryOp(
                            op="<>",  # 0.9 selectivity
                            left=PropertyAccess(variable="b", property="status"),
                            right=Literal(value="deleted"),
                        ),
                    ),
                    right=BinaryOp(
                        op="=",  # 0.1 selectivity
                        left=PropertyAccess(variable="c", property="active"),
                        right=Literal(value=True),
                    ),
                )
            )
        ]

        optimizer = QueryOptimizer(enable_filter_pushdown=False)
        result = optimizer.optimize(ops)

        conjuncts = PredicateAnalysis.extract_conjuncts(result[0].predicate)

        # Equality should come first, OR predicate second
        assert conjuncts[0].op == "="  # Most selective
        assert conjuncts[1].op == "OR"  # Least selective (max of two 0.9s)


class TestPredicateReorderDisabled:
    """Test disabling predicate reordering."""

    def test_predicate_reorder_disabled(self):
        """When disabled, predicates are not reordered."""
        original_ops = [
            Filter(
                predicate=BinaryOp(
                    op="AND",
                    left=BinaryOp(op=">", left=Variable(name="a"), right=Literal(value=1)),
                    right=BinaryOp(op="=", left=Variable(name="b"), right=Literal(value=2)),
                )
            )
        ]

        optimizer = QueryOptimizer(enable_predicate_reorder=False)
        result = optimizer.optimize(original_ops)

        # Predicate structure should be unchanged
        assert len(result) == 1
        assert isinstance(result[0], Filter)
        # Left side should still be > (not reordered to put = first)
        assert result[0].predicate.left.op == ">"
        assert result[0].predicate.right.op == "="


class TestPredicateReorderNoChange:
    """Test cases where reordering doesn't change anything."""

    def test_single_predicate_unchanged(self):
        """Single predicate (no AND) is unchanged."""
        ops = [
            Filter(
                predicate=BinaryOp(
                    op="=",
                    left=PropertyAccess(variable="a", property="name"),
                    right=Literal(value="Alice"),
                )
            )
        ]

        optimizer = QueryOptimizer(enable_filter_pushdown=False)
        result = optimizer.optimize(ops)

        # Should be unchanged
        assert len(result) == 1
        assert isinstance(result[0], Filter)
        assert result[0].predicate.op == "="

    def test_already_optimal_order(self):
        """Already optimally ordered predicates remain unchanged."""
        # Equality (0.1) AND Inequality (0.5) - already optimal
        ops = [
            Filter(
                predicate=BinaryOp(
                    op="AND",
                    left=BinaryOp(op="=", left=Variable(name="a"), right=Literal(value=1)),
                    right=BinaryOp(op=">", left=Variable(name="b"), right=Literal(value=2)),
                )
            )
        ]

        optimizer = QueryOptimizer(enable_filter_pushdown=False)
        result = optimizer.optimize(ops)

        # Order should be preserved (already optimal)
        conjuncts = PredicateAnalysis.extract_conjuncts(result[0].predicate)
        assert conjuncts[0].op == "="
        assert conjuncts[1].op == ">"


class TestPredicateReorderCombined:
    """Test filter pushdown and predicate reordering together."""

    def test_pushdown_then_reorder(self):
        """Filter pushed down, then predicates reordered."""
        ops = [
            ScanNodes(variable="n", labels=[["Person"]]),
            Filter(
                predicate=BinaryOp(
                    op="AND",
                    left=BinaryOp(
                        op=">",
                        left=PropertyAccess(variable="n", property="age"),
                        right=Literal(value=25),
                    ),
                    right=BinaryOp(
                        op="=",
                        left=PropertyAccess(variable="n", property="name"),
                        right=Literal(value="Alice"),
                    ),
                )
            ),
        ]

        optimizer = QueryOptimizer(enable_filter_pushdown=True, enable_predicate_reorder=True)
        result = optimizer.optimize(ops)

        # Filter should be pushed into ScanNodes
        assert len(result) == 1
        assert isinstance(result[0], ScanNodes)
        assert result[0].predicate is not None

        # Predicates should be reordered (= before >)
        conjuncts = PredicateAnalysis.extract_conjuncts(result[0].predicate)
        assert conjuncts[0].op == "="  # More selective
        assert conjuncts[1].op == ">"  # Less selective
