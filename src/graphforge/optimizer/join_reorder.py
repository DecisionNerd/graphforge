"""Join reordering optimization for reducing Cartesian products.

This module implements cost-based join reordering to avoid Cartesian products
by analyzing operator dependencies and choosing optimal execution orders.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from graphforge.optimizer.cost_model import CardinalityEstimator
from graphforge.optimizer.predicate_utils import PredicateAnalysis
from graphforge.optimizer.statistics import GraphStatistics
from graphforge.planner.operators import (
    Create,
    Delete,
    ExpandEdges,
    Filter,
    Merge,
    Remove,
    ScanNodes,
    Set,
    Subquery,
    Union,
    With,
)


@dataclass
class OperatorNode:
    """Node in the dependency graph.

    Represents an operator and its variable dependencies.
    """

    index: int
    operator: Any
    binds: set[str]  # Variables bound by this operator
    requires: set[str]  # Variables required (must be bound first)


class DependencyAnalyzer:
    """Analyzes operator dependencies for safe reordering."""

    def build_dependency_graph(
        self, operators: list[Any]
    ) -> tuple[list[OperatorNode], dict[int, set[int]]]:
        """Build dependency graph from operators.

        Args:
            operators: List of operators to analyze

        Returns:
            Tuple of (nodes, dependencies) where:
            - nodes: List of OperatorNode objects
            - dependencies: Dict mapping operator index to set of dependency indices
        """
        nodes = []

        for idx, op in enumerate(operators):
            binds = self._get_bound_variables(op)
            requires = self._get_required_variables(op)

            nodes.append(OperatorNode(index=idx, operator=op, binds=binds, requires=requires))

        # Build dependency edges
        dependencies: dict[int, set[int]] = defaultdict(set)
        for node in nodes:
            # Find which earlier operators bind our required variables
            for req_var in node.requires:
                for earlier_node in nodes[: node.index]:
                    if req_var in earlier_node.binds:
                        dependencies[node.index].add(earlier_node.index)

        return nodes, dependencies

    def _get_bound_variables(self, op: Any) -> set[str]:
        """Get variables bound by an operator.

        Args:
            op: Operator to analyze

        Returns:
            Set of variable names bound by this operator
        """
        if isinstance(op, ScanNodes):
            bound = {op.variable}
            if op.path_var:
                bound.add(op.path_var)
            return bound
        elif isinstance(op, ExpandEdges):
            bound = {op.dst_var}
            if op.edge_var:
                bound.add(op.edge_var)
            if op.path_var:
                bound.add(op.path_var)
            return bound
        return set()

    def _get_required_variables(self, op: Any) -> set[str]:
        """Get variables required by an operator.

        Args:
            op: Operator to analyze

        Returns:
            Set of variable names required by this operator
        """
        required = set()

        if isinstance(op, ExpandEdges):
            # ExpandEdges requires source variable
            required.add(op.src_var)
            # Plus any variables in predicate (excluding bound variables)
            if op.predicate:
                pred_vars = PredicateAnalysis.get_referenced_variables(op.predicate)
                required.update(pred_vars - self._get_bound_variables(op))

        elif isinstance(op, Filter):
            # Filter requires all variables in predicate
            pred_vars = PredicateAnalysis.get_referenced_variables(op.predicate)
            required.update(pred_vars)

        return required

    def find_valid_orderings(
        self,
        nodes: list[OperatorNode],
        dependencies: dict[int, set[int]],
        max_orderings: int = 1000,
    ) -> list[list[OperatorNode]]:
        """Find valid topological orderings with a configurable limit.

        Args:
            nodes: List of OperatorNode objects
            dependencies: Dict mapping node index to dependency indices
            max_orderings: Maximum number of orderings to enumerate (default 1000)

        Returns:
            List of valid orderings (each is a list of OperatorNode)
        """
        # Use greedy approach if max_orderings is 1 or nodes are too many
        if max_orderings == 1 or len(nodes) > 10:
            return [self._greedy_ordering(nodes, dependencies)]

        valid_orderings: list[list[OperatorNode]] = []

        def backtrack(remaining: set[int], current_ordering: list[OperatorNode], placed: set[int]):
            """Recursive backtracking to find all valid orderings."""
            # Stop if we've found enough orderings
            if len(valid_orderings) >= max_orderings:
                return

            if not remaining:
                valid_orderings.append(current_ordering.copy())
                return

            # Try each remaining node that has all dependencies satisfied
            for node_idx in list(remaining):
                if len(valid_orderings) >= max_orderings:
                    return

                deps = dependencies.get(node_idx, set())
                # Check if all dependencies are already placed (O(1) with set)
                if deps.issubset(placed):
                    remaining.remove(node_idx)
                    placed.add(node_idx)
                    current_ordering.append(nodes[node_idx])
                    backtrack(remaining, current_ordering, placed)
                    current_ordering.pop()
                    placed.discard(node_idx)
                    remaining.add(node_idx)

        backtrack(set(range(len(nodes))), [], set())

        # If enumeration was cut short, add greedy fallback
        if len(valid_orderings) >= max_orderings:
            greedy = self._greedy_ordering(nodes, dependencies)
            if greedy not in valid_orderings:
                valid_orderings.append(greedy)

        return valid_orderings if valid_orderings else [self._greedy_ordering(nodes, dependencies)]

    def _greedy_ordering(
        self, nodes: list[OperatorNode], dependencies: dict[int, set[int]]
    ) -> list[OperatorNode]:
        """Build a greedy ordering by repeatedly choosing the next node with minimal dependencies.

        Args:
            nodes: List of OperatorNode objects
            dependencies: Dict mapping node index to dependency indices

        Returns:
            A single valid ordering
        """
        remaining = set(range(len(nodes)))
        ordering = []
        bound_indices = set()

        while remaining:
            # Find nodes with all dependencies satisfied
            available = [
                idx
                for idx in remaining
                if all(dep in bound_indices for dep in dependencies.get(idx, set()))
            ]

            if not available:
                # Should not happen in valid dependency graph
                # Just pick first remaining
                available = [next(iter(remaining))]

            # Pick the one with smallest index (deterministic)
            chosen = min(available)
            remaining.remove(chosen)
            bound_indices.add(chosen)
            ordering.append(nodes[chosen])

        return ordering


class JoinReorderOptimizer:
    """Performs join reordering optimization."""

    def __init__(self, statistics: GraphStatistics, max_orderings: int = 1000):
        """Initialize optimizer with graph statistics.

        Args:
            statistics: GraphStatistics instance for cost estimation
            max_orderings: Maximum number of orderings to enumerate (default 1000)
        """
        self.statistics = statistics
        self.estimator = CardinalityEstimator(statistics)
        self.analyzer = DependencyAnalyzer()
        self.max_orderings = max_orderings

    def can_reorder(self, operators: list[Any]) -> bool:
        """Check if operators are eligible for reordering.

        Args:
            operators: List of operators to check

        Returns:
            True if reordering is safe, False otherwise
        """
        # Need at least 2 pattern operators to reorder
        pattern_ops = [op for op in operators if isinstance(op, (ScanNodes, ExpandEdges))]
        if len(pattern_ops) < 2:
            return False

        return True

    def _segment_has_side_effects(self, operators: list[Any]) -> bool:
        """Check if a segment has side effects that prevent reordering.

        Args:
            operators: List of operators in segment

        Returns:
            True if segment has side effects, False otherwise
        """
        return any(isinstance(op, (Create, Set, Delete, Remove, Merge)) for op in operators)

    def reorder_joins(self, operators: list[Any]) -> list[Any]:
        """Reorder operators to minimize cost.

        Args:
            operators: List of operators in source order

        Returns:
            List of operators in optimized order
        """
        if not self.can_reorder(operators):
            return operators

        # Split at pipeline boundaries (With, Union, Subquery)
        segments = self._split_at_boundaries(operators)

        # Reorder each segment independently
        reordered_segments = []
        for segment in segments:
            if isinstance(segment, list):
                reordered_segments.append(self._reorder_segment(segment))
            else:
                reordered_segments.append([segment])

        # Flatten back into operator list
        return [op for segment in reordered_segments for op in segment]

    def _reorder_segment(self, operators: list[Any]) -> list[Any]:
        """Reorder a single segment without boundaries.

        Reorders pattern operators while ensuring all operator dependencies
        (including non-pattern operators like Filter) remain satisfied.

        Args:
            operators: List of operators in segment

        Returns:
            Reordered list of operators
        """
        # Can't reorder if segment has side effects
        if self._segment_has_side_effects(operators):
            return operators

        # Need at least 2 pattern operators to reorder
        pattern_op_count = sum(
            1 for op in operators if isinstance(op, (ScanNodes, ExpandEdges))
        )
        if pattern_op_count < 2:
            return operators

        # Build dependency graph for ALL operators (not just pattern ops)
        # This ensures non-pattern operators like Filter maintain valid bindings
        nodes, dependencies = self.analyzer.build_dependency_graph(operators)

        # Find all valid orderings that respect ALL dependencies
        valid_orderings = self.analyzer.find_valid_orderings(
            nodes, dependencies, max_orderings=self.max_orderings
        )

        if len(valid_orderings) <= 1:
            # Only one valid ordering, return original
            return operators

        # Estimate cost for each ordering and choose the best
        costs = []
        for ordering in valid_orderings:
            ops = [node.operator for node in ordering]
            cost = self.estimator.estimate_cost(ops)
            costs.append((cost, ops))

        # Get best ordering
        _min_cost, best_ops = min(costs, key=lambda x: x[0])

        return best_ops

    def _split_at_boundaries(self, operators: list[Any]) -> list[Any]:
        """Split operator list at pipeline boundaries.

        Args:
            operators: List of operators

        Returns:
            List where each element is either:
            - A single boundary operator (With, Union, Subquery)
            - A list of operators (segment to be reordered)
        """
        segments: list[Any] = []
        current_segment: list[Any] = []

        for op in operators:
            if isinstance(op, (With, Union, Subquery)):
                # Flush current segment
                if current_segment:
                    segments.append(current_segment)
                    current_segment = []
                # Add boundary as standalone
                segments.append(op)
            else:
                current_segment.append(op)

        # Flush final segment
        if current_segment:
            segments.append(current_segment)

        return segments
