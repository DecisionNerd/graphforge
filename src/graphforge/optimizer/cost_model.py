"""Cost-based query optimization using cardinality estimation.

This module provides cardinality estimation for logical plan operators,
enabling cost-based query optimization such as join reordering.
"""

from typing import Any

from graphforge.optimizer.predicate_utils import PredicateAnalysis
from graphforge.optimizer.statistics import GraphStatistics
from graphforge.planner.operators import ExpandEdges, Filter, ScanNodes


class CardinalityEstimator:
    """Estimates cardinality and cost of operator sequences.

    Uses graph statistics to estimate intermediate result sizes and
    total execution cost for operator pipelines.
    """

    def __init__(self, statistics: GraphStatistics):
        """Initialize estimator with graph statistics.

        Args:
            statistics: GraphStatistics instance with current graph stats
        """
        self.statistics = statistics

    def estimate_scan_nodes(self, op: ScanNodes) -> int:
        """Estimate cardinality of ScanNodes operator.

        Args:
            op: ScanNodes operator to estimate

        Returns:
            Estimated number of output rows
        """
        # No labels = full table scan
        if op.labels is None or len(op.labels) == 0:
            base_estimate = self.statistics.total_nodes
        else:
            # Labels is list[list[str]] (disjunction of conjunctions)
            total_estimate = 0
            for label_group in op.labels:
                if len(label_group) == 0:
                    continue
                # Conjunction: estimate as minimum (most selective label)
                # This is a conservative estimate assuming label overlap
                group_estimate = min(
                    self.statistics.node_counts_by_label.get(label, 0) for label in label_group
                )
                total_estimate += group_estimate

            base_estimate = total_estimate

        # Apply predicate selectivity if present
        if op.predicate is not None:
            selectivity = PredicateAnalysis.estimate_selectivity(op.predicate)
            base_estimate = int(base_estimate * selectivity)

        return max(base_estimate, 0)

    def estimate_expand_edges(self, op: ExpandEdges, input_cardinality: int) -> int:
        """Estimate cardinality of ExpandEdges operator.

        Args:
            op: ExpandEdges operator to estimate
            input_cardinality: Number of input rows (source nodes)

        Returns:
            Estimated number of output rows
        """
        if input_cardinality == 0:
            return 0

        # Get average outgoing degree for the edge types
        if len(op.edge_types) == 0:
            # All edge types
            if self.statistics.total_nodes > 0:
                avg_degree = self.statistics.total_edges / self.statistics.total_nodes
            else:
                avg_degree = 1.0
        else:
            # Specific edge types - average their degrees
            type_degrees = [
                self.statistics.avg_degree_by_type.get(edge_type, 1.0)
                for edge_type in op.edge_types
            ]
            avg_degree = sum(type_degrees) / max(len(type_degrees), 1)

        # Output cardinality = input * avg degree
        estimate = int(input_cardinality * avg_degree)

        # Apply predicate selectivity if present
        if op.predicate is not None:
            selectivity = PredicateAnalysis.estimate_selectivity(op.predicate)
            estimate = int(estimate * selectivity)

        return max(estimate, 0)

    def estimate_filter(self, op: Filter, input_cardinality: int) -> int:
        """Estimate cardinality of Filter operator.

        Args:
            op: Filter operator to estimate
            input_cardinality: Number of input rows

        Returns:
            Estimated number of output rows
        """
        selectivity = PredicateAnalysis.estimate_selectivity(op.predicate)
        return int(input_cardinality * selectivity)

    def estimate_cost(self, operators: list[Any]) -> float:
        """Estimate total execution cost of an operator sequence.

        Cost is defined as the sum of intermediate cardinalities (total work done).
        This metric captures Cartesian product explosions and helps compare orderings.

        Args:
            operators: List of operators in execution order

        Returns:
            Estimated cost (sum of intermediate cardinalities)
        """
        cardinality = 1  # Start with 1 row (empty context)
        total_cost = 0.0

        for op in operators:
            if isinstance(op, ScanNodes):
                # ScanNodes creates Cartesian product with existing rows
                scan_card = self.estimate_scan_nodes(op)
                cardinality = cardinality * scan_card
            elif isinstance(op, ExpandEdges):
                # ExpandEdges multiplies by average degree
                cardinality = self.estimate_expand_edges(op, cardinality)
            elif isinstance(op, Filter):
                # Filter reduces cardinality
                cardinality = self.estimate_filter(op, cardinality)
            # Other operators: assume cardinality unchanged

            # Accumulate cost
            total_cost += cardinality

        return total_cost
