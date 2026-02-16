"""Unit tests for cardinality estimation and cost modeling."""

from graphforge.ast.expression import BinaryOp, Literal
from graphforge.optimizer.cost_model import CardinalityEstimator
from graphforge.optimizer.statistics import GraphStatistics
from graphforge.planner.operators import ExpandEdges, Filter, ScanNodes


class TestCardinalityEstimatorInit:
    """Test CardinalityEstimator initialization."""

    def test_init_with_statistics(self):
        """Estimator should initialize with statistics."""
        stats = GraphStatistics(total_nodes=100, total_edges=200)
        estimator = CardinalityEstimator(stats)

        assert estimator.statistics == stats


class TestScanNodesEstimation:
    """Test cardinality estimation for ScanNodes operator."""

    def test_full_scan_no_labels(self):
        """Full scan should return total_nodes."""
        stats = GraphStatistics(total_nodes=1000, total_edges=2000)
        estimator = CardinalityEstimator(stats)

        op = ScanNodes(variable="n", labels=None)
        estimate = estimator.estimate_scan_nodes(op)

        assert estimate == 1000

    def test_full_scan_empty_labels(self):
        """Empty labels list should return total_nodes."""
        stats = GraphStatistics(total_nodes=1000, total_edges=2000)
        estimator = CardinalityEstimator(stats)

        op = ScanNodes(variable="n", labels=[])
        estimate = estimator.estimate_scan_nodes(op)

        assert estimate == 1000

    def test_single_label_scan(self):
        """Single label scan should use label count."""
        stats = GraphStatistics(
            total_nodes=1000,
            total_edges=2000,
            node_counts_by_label={"Person": 500, "Company": 500},
        )
        estimator = CardinalityEstimator(stats)

        op = ScanNodes(variable="n", labels=[["Person"]])
        estimate = estimator.estimate_scan_nodes(op)

        assert estimate == 500

    def test_label_conjunction(self):
        """Label conjunction should use minimum count."""
        stats = GraphStatistics(
            total_nodes=1000,
            total_edges=2000,
            node_counts_by_label={"Person": 500, "Employee": 300},
        )
        estimator = CardinalityEstimator(stats)

        # Must have both Person AND Employee labels
        op = ScanNodes(variable="n", labels=[["Person", "Employee"]])
        estimate = estimator.estimate_scan_nodes(op)

        # Should use minimum (most selective)
        assert estimate == 300

    def test_label_disjunction(self):
        """Label disjunction should sum counts."""
        stats = GraphStatistics(
            total_nodes=1000,
            total_edges=2000,
            node_counts_by_label={"Person": 500, "Company": 300},
        )
        estimator = CardinalityEstimator(stats)

        # Must have Person OR Company label
        op = ScanNodes(variable="n", labels=[["Person"], ["Company"]])
        estimate = estimator.estimate_scan_nodes(op)

        assert estimate == 800

    def test_missing_label_returns_zero(self):
        """Scan for non-existent label should return 0."""
        stats = GraphStatistics(
            total_nodes=1000, total_edges=2000, node_counts_by_label={"Person": 500}
        )
        estimator = CardinalityEstimator(stats)

        op = ScanNodes(variable="n", labels=[["NonExistent"]])
        estimate = estimator.estimate_scan_nodes(op)

        assert estimate == 0

    def test_scan_with_predicate(self):
        """Scan with predicate should apply selectivity."""
        stats = GraphStatistics(total_nodes=1000, total_edges=2000)
        estimator = CardinalityEstimator(stats)

        # Predicate with 0.1 selectivity (equality)
        predicate = BinaryOp(op="=", left=Literal(value=5), right=Literal(value=5))
        op = ScanNodes(variable="n", labels=None, predicate=predicate)
        estimate = estimator.estimate_scan_nodes(op)

        # 1000 * 0.1 = 100
        assert estimate == 100


class TestExpandEdgesEstimation:
    """Test cardinality estimation for ExpandEdges operator."""

    def test_expand_with_zero_input(self):
        """Expand with 0 input should return 0."""
        stats = GraphStatistics(total_nodes=1000, total_edges=2000)
        estimator = CardinalityEstimator(stats)

        op = ExpandEdges(src_var="a", dst_var="b", edge_types=["KNOWS"], direction="OUT")
        estimate = estimator.estimate_expand_edges(op, input_cardinality=0)

        assert estimate == 0

    def test_expand_all_edge_types(self):
        """Expand with no specific types should use total avg degree."""
        stats = GraphStatistics(
            total_nodes=100,
            total_edges=200,
            avg_degree_by_type={},  # Empty but shouldn't matter
        )
        estimator = CardinalityEstimator(stats)

        op = ExpandEdges(src_var="a", dst_var="b", edge_types=[], direction="OUT")
        estimate = estimator.estimate_expand_edges(op, input_cardinality=10)

        # 10 input * (200 / 100 = 2.0 avg degree) = 20
        assert estimate == 20

    def test_expand_single_edge_type(self):
        """Expand with specific type should use type avg degree."""
        stats = GraphStatistics(
            total_nodes=100,
            total_edges=200,
            avg_degree_by_type={"KNOWS": 3.0, "WORKS_FOR": 1.0},
        )
        estimator = CardinalityEstimator(stats)

        op = ExpandEdges(src_var="a", dst_var="b", edge_types=["KNOWS"], direction="OUT")
        estimate = estimator.estimate_expand_edges(op, input_cardinality=10)

        # 10 input * 3.0 avg degree = 30
        assert estimate == 30

    def test_expand_multiple_edge_types(self):
        """Expand with multiple types should sum their degrees (OR semantics)."""
        stats = GraphStatistics(
            total_nodes=100,
            total_edges=200,
            avg_degree_by_type={"KNOWS": 4.0, "WORKS_FOR": 2.0},
        )
        estimator = CardinalityEstimator(stats)

        op = ExpandEdges(
            src_var="a", dst_var="b", edge_types=["KNOWS", "WORKS_FOR"], direction="OUT"
        )
        estimate = estimator.estimate_expand_edges(op, input_cardinality=10)

        # 10 input * (4.0 + 2.0 = 6.0) = 60
        assert estimate == 60

    def test_expand_unknown_edge_type_defaults_to_one(self):
        """Expand with unknown type should default to degree 1.0."""
        stats = GraphStatistics(total_nodes=100, total_edges=200, avg_degree_by_type={"KNOWS": 3.0})
        estimator = CardinalityEstimator(stats)

        op = ExpandEdges(src_var="a", dst_var="b", edge_types=["UNKNOWN"], direction="OUT")
        estimate = estimator.estimate_expand_edges(op, input_cardinality=10)

        # 10 input * 1.0 default = 10
        assert estimate == 10

    def test_expand_with_predicate(self):
        """Expand with predicate should apply selectivity."""
        stats = GraphStatistics(total_nodes=100, total_edges=200, avg_degree_by_type={"KNOWS": 4.0})
        estimator = CardinalityEstimator(stats)

        # Predicate with 0.5 selectivity (inequality)
        predicate = BinaryOp(op="<", left=Literal(value=5), right=Literal(value=10))
        op = ExpandEdges(
            src_var="a",
            dst_var="b",
            edge_types=["KNOWS"],
            direction="OUT",
            predicate=predicate,
        )
        estimate = estimator.estimate_expand_edges(op, input_cardinality=10)

        # 10 * 4.0 * 0.5 = 20
        assert estimate == 20


class TestFilterEstimation:
    """Test cardinality estimation for Filter operator."""

    def test_filter_equality(self):
        """Filter with equality should apply 0.1 selectivity."""
        stats = GraphStatistics(total_nodes=1000, total_edges=2000)
        estimator = CardinalityEstimator(stats)

        predicate = BinaryOp(op="=", left=Literal(value=5), right=Literal(value=5))
        op = Filter(predicate=predicate)
        estimate = estimator.estimate_filter(op, input_cardinality=1000)

        # 1000 * 0.1 = 100
        assert estimate == 100

    def test_filter_inequality(self):
        """Filter with inequality should apply 0.5 selectivity."""
        stats = GraphStatistics(total_nodes=1000, total_edges=2000)
        estimator = CardinalityEstimator(stats)

        predicate = BinaryOp(op="<", left=Literal(value=5), right=Literal(value=10))
        op = Filter(predicate=predicate)
        estimate = estimator.estimate_filter(op, input_cardinality=1000)

        # 1000 * 0.5 = 500
        assert estimate == 500

    def test_filter_not_equals(self):
        """Filter with <> should apply 0.9 selectivity."""
        stats = GraphStatistics(total_nodes=1000, total_edges=2000)
        estimator = CardinalityEstimator(stats)

        predicate = BinaryOp(op="<>", left=Literal(value=5), right=Literal(value=10))
        op = Filter(predicate=predicate)
        estimate = estimator.estimate_filter(op, input_cardinality=1000)

        # 1000 * 0.9 = 900
        assert estimate == 900


class TestCostEstimation:
    """Test cost estimation for operator sequences."""

    def test_single_scan_cost(self):
        """Single scan should have cost equal to cardinality."""
        stats = GraphStatistics(total_nodes=100, total_edges=200)
        estimator = CardinalityEstimator(stats)

        ops = [ScanNodes(variable="n", labels=None)]
        cost = estimator.estimate_cost(ops)

        # 100 nodes
        assert cost == 100.0

    def test_scan_and_expand_cost(self):
        """Scan + expand should accumulate cardinalities."""
        stats = GraphStatistics(total_nodes=100, total_edges=200, avg_degree_by_type={"KNOWS": 2.0})
        estimator = CardinalityEstimator(stats)

        ops = [
            ScanNodes(variable="a", labels=None),
            ExpandEdges(src_var="a", dst_var="b", edge_types=["KNOWS"], direction="OUT"),
        ]
        cost = estimator.estimate_cost(ops)

        # Scan: 100, Expand: 100 * 2.0 = 200
        # Total cost: 100 + 200 = 300
        assert cost == 300.0

    def test_cartesian_product_detection(self):
        """Multiple scans should create Cartesian product."""
        stats = GraphStatistics(
            total_nodes=1000,
            total_edges=2000,
            node_counts_by_label={"Person": 100, "Company": 10},
        )
        estimator = CardinalityEstimator(stats)

        # Bad query: MATCH (a:Person) MATCH (b:Company)
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="b", labels=[["Company"]]),
        ]
        cost = estimator.estimate_cost(ops)

        # Scan Person: 100
        # Scan Company (Cartesian): 100 * 10 = 1000
        # Total cost: 100 + 1000 = 1100
        assert cost == 1100.0

    def test_good_ordering_lower_cost(self):
        """Scan + expand should have lower cost than Cartesian."""
        stats = GraphStatistics(
            total_nodes=1000,
            total_edges=2000,
            node_counts_by_label={"Person": 100, "Company": 10},
            avg_degree_by_type={"WORKS_FOR": 1.0},
        )
        estimator = CardinalityEstimator(stats)

        # Bad ordering: Cartesian product
        bad_ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="b", labels=[["Company"]]),
        ]
        bad_cost = estimator.estimate_cost(bad_ops)

        # Good ordering: Scan + expand
        good_ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(src_var="a", dst_var="b", edge_types=["WORKS_FOR"], direction="OUT"),
        ]
        good_cost = estimator.estimate_cost(good_ops)

        # Good cost should be significantly lower
        assert good_cost < bad_cost
        # Good: 100 + (100 * 1.0) = 200
        # Bad: 100 + (100 * 10) = 1100
        assert good_cost == 200.0
        assert bad_cost == 1100.0

    def test_filter_reduces_cost(self):
        """Filter should reduce subsequent operator costs."""
        stats = GraphStatistics(
            total_nodes=1000, total_edges=2000, avg_degree_by_type={"KNOWS": 5.0}
        )
        estimator = CardinalityEstimator(stats)

        # Without filter
        ops_without_filter = [
            ScanNodes(variable="a", labels=None),
            ExpandEdges(src_var="a", dst_var="b", edge_types=["KNOWS"], direction="OUT"),
        ]
        cost_without = estimator.estimate_cost(ops_without_filter)

        # With filter (0.1 selectivity)
        predicate = BinaryOp(op="=", left=Literal(value=5), right=Literal(value=5))
        ops_with_filter = [
            ScanNodes(variable="a", labels=None),
            Filter(predicate=predicate),
            ExpandEdges(src_var="a", dst_var="b", edge_types=["KNOWS"], direction="OUT"),
        ]
        cost_with = estimator.estimate_cost(ops_with_filter)

        # Without: 1000 + 5000 = 6000
        # With: 1000 + 100 + 500 = 1600
        assert cost_with < cost_without
        assert cost_with == 1600.0
        assert cost_without == 6000.0
