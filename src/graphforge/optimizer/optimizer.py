"""Query optimizer for transforming logical operator plans."""

from typing import Any

from graphforge.ast.expression import FunctionCall, Variable
from graphforge.optimizer.predicate_utils import PredicateAnalysis
from graphforge.optimizer.statistics import GraphStatistics
from graphforge.planner.operators import (
    Aggregate,
    AggregationHint,
    ExpandEdges,
    ExpandVariableLength,
    Filter,
    OptionalExpandEdges,
    OptionalScanNodes,
    ScanNodes,
    Subquery,
    Union,
    With,
)


class QueryOptimizer:
    """Optimizes logical query plans for better performance.

    Applies a series of optimization passes to transform the operator pipeline
    emitted by the planner. Optimizations preserve query semantics while
    improving execution efficiency.

    Optimization passes:
        1. Filter pushdown - Move WHERE predicates into ScanNodes/ExpandEdges
        2. Join reordering - Reorder MATCH patterns to avoid Cartesian products
        3. Predicate reordering - Evaluate more selective predicates first
        4. Redundant traversal elimination - Remove duplicate pattern scans
        5. Aggregate pushdown - Move aggregations into traversal operators

    Attributes:
        enable_filter_pushdown: Enable filter pushdown optimization
        enable_join_reorder: Enable join reordering optimization
        enable_predicate_reorder: Enable predicate reordering optimization
        enable_redundant_elimination: Enable redundant traversal elimination
        enable_aggregate_pushdown: Enable aggregate pushdown optimization
        statistics: Graph statistics for cost-based optimization (optional)
    """

    def __init__(
        self,
        enable_filter_pushdown: bool = True,
        enable_join_reorder: bool = True,
        enable_predicate_reorder: bool = True,
        enable_redundant_elimination: bool = True,
        enable_aggregate_pushdown: bool = True,
        statistics: GraphStatistics | None = None,
        max_orderings: int = 1000,
    ):
        """Initialize query optimizer.

        Args:
            enable_filter_pushdown: Enable filter pushdown pass
            enable_join_reorder: Enable join reordering pass
            enable_predicate_reorder: Enable predicate reordering pass
            enable_redundant_elimination: Enable redundant traversal elimination
            enable_aggregate_pushdown: Enable aggregate pushdown pass
            statistics: Graph statistics for cost-based optimization (optional)
            max_orderings: Maximum orderings to enumerate in join reordering (default 1000)
        """
        self.enable_filter_pushdown = enable_filter_pushdown
        self.enable_join_reorder = enable_join_reorder
        self.enable_predicate_reorder = enable_predicate_reorder
        self.enable_redundant_elimination = enable_redundant_elimination
        self.enable_aggregate_pushdown = enable_aggregate_pushdown
        self._statistics = statistics
        self._max_orderings = max_orderings
        self._predicate_analysis = PredicateAnalysis()

    def optimize(self, operators: list[Any]) -> list[Any]:
        """Apply optimization passes to operator pipeline.

        Args:
            operators: List of logical operators from planner

        Returns:
            Optimized list of operators
        """
        # Apply filter pushdown first (reduces cardinality early)
        if self.enable_filter_pushdown:
            operators = self._filter_pushdown_pass(operators)

        # Join reordering (must run while patterns are recognizable)
        if self.enable_join_reorder and self._statistics:
            operators = self._join_reorder_pass(operators)

        # Then reorder predicates within operators
        if self.enable_predicate_reorder:
            operators = self._predicate_reorder_pass(operators)

        # Eliminate redundant traversals
        if self.enable_redundant_elimination:
            operators = self._redundant_traversal_elimination_pass(operators)

        # Finally push aggregations into traversals (work with simplified operator list)
        if self.enable_aggregate_pushdown:
            operators = self._aggregate_pushdown_pass(operators)

        return operators

    def _filter_pushdown_pass(self, operators: list[Any]) -> list[Any]:
        """Push Filter predicates into ScanNodes/ExpandEdges operators.

        This optimization reduces the number of rows flowing through the pipeline
        by filtering as early as possible.

        Algorithm:
            1. Track bound variables as we scan operators forward
            2. When encountering Filter, extract AND conjuncts
            3. Try to push each conjunct backward into preceding operators
            4. Only push if predicate references only operator's bound variables
            5. Remove Filter if all predicates successfully pushed

        Safety checks:
            - Don't push predicates with unbound variables
            - Don't push across pipeline boundaries (With, Union, Subquery)
            - Don't push into Optional operators (breaks NULL semantics)

        Args:
            operators: Input operator list

        Returns:
            Transformed operator list with filters pushed down
        """
        result: list[Any] = []
        bound_vars: set[str] = set()

        for op in operators:
            # Check for pipeline boundaries
            if isinstance(op, (With, Union, Subquery)):
                # Reset tracking at pipeline boundaries
                result.append(op)
                bound_vars = self._get_bound_variables_after_op(op, bound_vars)
                continue

            # Try to push Filter predicates backward
            if isinstance(op, Filter):
                conjuncts = PredicateAnalysis.extract_conjuncts(op.predicate)
                unpushed_predicates = []

                # Try to push each conjunct backward
                for conjunct in conjuncts:
                    if not self._try_push_predicate(conjunct, result, bound_vars):
                        # Couldn't push this predicate
                        unpushed_predicates.append(conjunct)

                # Only keep Filter if some predicates couldn't be pushed
                if unpushed_predicates:
                    combined = PredicateAnalysis.combine_with_and(unpushed_predicates)
                    result.append(Filter(predicate=combined))
                # Otherwise Filter is completely pushed down and removed

                continue

            # Track variables bound by this operator
            bound_vars = self._get_bound_variables_after_op(op, bound_vars)
            result.append(op)

        return result

    def _try_push_predicate(
        self, predicate: Any, operators: list[Any], bound_vars: set[str]
    ) -> bool:
        """Try to push a predicate into a preceding operator.

        Args:
            predicate: Predicate expression to push
            operators: List of operators processed so far (may be modified)
            bound_vars: Set of variables bound so far

        Returns:
            True if predicate was successfully pushed, False otherwise
        """
        # Get variables referenced by predicate
        pred_vars = PredicateAnalysis.get_referenced_variables(predicate)

        # Don't push if predicate references unbound variables
        if not pred_vars.issubset(bound_vars):
            return False

        # Scan backwards to find a compatible operator
        for i in range(len(operators) - 1, -1, -1):
            op = operators[i]

            # Don't push across pipeline boundaries
            if isinstance(op, (With, Union, Subquery)):
                return False

            # Don't push into Optional operators (breaks NULL semantics)
            if isinstance(op, (OptionalScanNodes, OptionalExpandEdges)):
                continue

            # Try to push into ScanNodes
            if isinstance(op, ScanNodes):
                # Check if predicate only references the node variable
                if pred_vars == {op.variable}:
                    # Combine with existing predicate if present
                    if op.predicate is not None:
                        new_predicate = PredicateAnalysis.combine_with_and(
                            [op.predicate, predicate]
                        )
                    else:
                        new_predicate = predicate

                    # Replace operator with updated version
                    operators[i] = op.model_copy(update={"predicate": new_predicate})
                    return True

            # Try to push into ExpandEdges
            if isinstance(op, ExpandEdges):
                # Check if predicate references only variables bound by this operator
                op_vars = {op.dst_var}
                if op.edge_var:
                    op_vars.add(op.edge_var)

                if pred_vars.issubset(op_vars):
                    # Combine with existing predicate if present
                    if op.predicate is not None:
                        new_predicate = PredicateAnalysis.combine_with_and(
                            [op.predicate, predicate]
                        )
                    else:
                        new_predicate = predicate

                    # Replace operator with updated version
                    operators[i] = op.model_copy(update={"predicate": new_predicate})
                    return True

        return False

    def _get_bound_variables_after_op(self, op: Any, current_bound: set[str]) -> set[str]:
        """Get set of bound variables after executing an operator.

        Args:
            op: Operator to analyze
            current_bound: Variables already bound

        Returns:
            Updated set of bound variables
        """
        new_bound = current_bound.copy()

        # ScanNodes binds the node variable
        if isinstance(op, (ScanNodes, OptionalScanNodes)):
            new_bound.add(op.variable)

        # ExpandEdges binds edge and destination variables
        elif isinstance(op, (ExpandEdges, OptionalExpandEdges)):
            new_bound.add(op.dst_var)
            if op.edge_var:
                new_bound.add(op.edge_var)

        # With redefines the variable scope
        elif isinstance(op, With):
            # After WITH, only projected variables are bound
            new_bound = {item.alias for item in op.items}

        return new_bound

    def _predicate_reorder_pass(self, operators: list[Any]) -> list[Any]:
        """Reorder predicates within operators by selectivity.

        Evaluates more selective predicates first to enable early short-circuiting
        of AND chains.

        Algorithm:
            1. For each operator with a predicate (Filter, ScanNodes, ExpandEdges)
            2. Extract AND conjuncts
            3. Estimate selectivity for each conjunct
            4. Sort by selectivity (lower = more selective = evaluate first)
            5. Recombine with AND

        Args:
            operators: Input operator list

        Returns:
            Transformed operator list with reordered predicates
        """
        result = []

        for op in operators:
            # Reorder predicates in operators that support them
            if isinstance(op, (Filter, ScanNodes, ExpandEdges)):
                if hasattr(op, "predicate") and op.predicate is not None:
                    reordered_predicate = self._reorder_predicate(op.predicate)
                    result.append(op.model_copy(update={"predicate": reordered_predicate}))
                else:
                    result.append(op)
            else:
                result.append(op)

        return result

    def _reorder_predicate(self, predicate: Any) -> Any:
        """Reorder AND conjuncts by selectivity (most selective first).

        Args:
            predicate: Predicate expression to reorder

        Returns:
            Reordered predicate expression
        """
        # Extract AND conjuncts
        conjuncts = PredicateAnalysis.extract_conjuncts(predicate)

        # If only one conjunct, no reordering needed
        if len(conjuncts) == 1:
            return predicate

        # Sort by selectivity (lower = more selective = evaluate first)
        sorted_conjuncts = sorted(conjuncts, key=PredicateAnalysis.estimate_selectivity)

        # Recombine with AND
        return PredicateAnalysis.combine_with_and(sorted_conjuncts)

    def _redundant_traversal_elimination_pass(self, operators: list[Any]) -> list[Any]:
        """Eliminate redundant pattern scan operators.

        Detects duplicate ScanNodes/ExpandEdges operators and removes them,
        reusing results from the first occurrence.

        Algorithm:
            1. Track operator signatures as we scan forward
            2. For each operator, check if signature already seen
            3. If duplicate: mark for removal
            4. If first occurrence: record in signature map
            5. Return operator list with duplicates removed

        Safety checks:
            - Don't merge across pipeline boundaries (With, Union, Subquery)
            - Don't merge operators with side effects (Create, Set, Delete, Merge)
            - Don't merge Optional operators (breaks NULL semantics)
            - Variables must have same binding (same variable name)

        Args:
            operators: Input operator list

        Returns:
            Transformed operator list with duplicates removed
        """
        result: list[Any] = []
        seen_signatures: dict[tuple, int] = {}  # signature -> index in result

        for op in operators:
            # Reset tracking at pipeline boundaries
            if isinstance(op, (With, Union, Subquery)):
                result.append(op)
                seen_signatures.clear()  # Variables rescoped
                continue

            # Compute signature for pattern scan operators
            signature = self._compute_operator_signature(op)

            if signature is None:
                # Not a pattern scan operator, keep as-is
                result.append(op)
                continue

            # Check if we've seen this exact operator before
            if signature in seen_signatures:
                # Duplicate found - skip it (first occurrence handles the work)
                continue

            # First occurrence - record and keep
            seen_signatures[signature] = len(result)
            result.append(op)

        return result

    def _compute_operator_signature(self, op: Any) -> tuple | None:
        """Compute a unique signature for an operator.

        Returns a hashable tuple representing the operator's semantics,
        or None if operator should not be considered for elimination.

        Signature includes:
            - Operator type (class name)
            - Variable bindings
            - Labels/types
            - Direction
            - Predicate (if present)

        Args:
            op: Operator to compute signature for

        Returns:
            Signature tuple, or None if not applicable
        """
        # ScanNodes signature
        if isinstance(op, ScanNodes):
            labels_tuple = tuple(tuple(g) for g in op.labels) if op.labels else None
            predicate_repr = self._predicate_signature(op.predicate) if op.predicate else None
            return ("ScanNodes", op.variable, labels_tuple, op.path_var, predicate_repr)

        # ExpandEdges signature
        elif isinstance(op, ExpandEdges):
            predicate_repr = self._predicate_signature(op.predicate) if op.predicate else None
            return (
                "ExpandEdges",
                op.src_var,
                op.edge_var,
                op.dst_var,
                tuple(op.edge_types),
                op.direction,
                op.path_var,
                predicate_repr,
            )

        # ExpandVariableLength signature
        elif isinstance(op, ExpandVariableLength):
            predicate_repr = self._predicate_signature(op.predicate) if op.predicate else None
            return (
                "ExpandVariableLength",
                op.src_var,
                op.edge_var,
                op.dst_var,
                tuple(op.edge_types),
                op.direction,
                op.min_hops,
                op.max_hops,
                op.path_var,
                predicate_repr,
            )

        # Not a pattern scan operator
        return None

    def _predicate_signature(self, predicate: Any) -> str:
        """Convert predicate to hashable signature.

        Args:
            predicate: Predicate AST node

        Returns:
            String representation of predicate structure
        """
        # For Pydantic models, repr() gives structural representation
        return repr(predicate)

    def _aggregate_pushdown_pass(self, operators: list[Any]) -> list[Any]:
        """Push aggregations into traversal operators when safe.

        This optimization computes aggregations incrementally during traversal
        instead of materializing all rows first. Only applies to COUNT, SUM,
        MIN, MAX with simple GROUP BY patterns.

        Algorithm:
            1. Scan for ExpandEdges followed by Aggregate
            2. Check if pushdown is safe (safety checks detailed below)
            3. If safe:
               - Add agg_hint to ExpandEdges
               - Remove Aggregate operator
               - Update downstream operators to use new variable bindings

        Safety checks:
            - Must have exactly one aggregation function
            - Function must be COUNT, SUM, MIN, or MAX (not COLLECT, AVG, etc.)
            - No DISTINCT modifier on aggregation
            - GROUP BY must include source variable
            - Can't push across pipeline boundaries (With, Union, Subquery)
            - Can't push into Optional operators (breaks NULL semantics)

        Args:
            operators: Input operator list

        Returns:
            Transformed operator list with aggregations pushed down
        """
        result: list[Any] = []
        i = 0

        while i < len(operators):
            op = operators[i]

            # Look for pattern: ExpandEdges + Aggregate
            if isinstance(op, ExpandEdges) and i + 1 < len(operators):
                next_op = operators[i + 1]

                if isinstance(next_op, Aggregate):
                    # Check if pushdown is safe
                    agg_hint = self._try_create_aggregation_hint(op, next_op)

                    if agg_hint is not None:
                        # Push aggregation into ExpandEdges
                        enhanced_op = op.model_copy(update={"agg_hint": agg_hint})
                        result.append(enhanced_op)

                        # Skip the Aggregate operator
                        i += 2
                        continue

            # Pipeline boundaries reset optimization potential
            if isinstance(op, (With, Union, Subquery)):
                result.append(op)
                i += 1
                continue

            result.append(op)
            i += 1

        return result

    def _try_create_aggregation_hint(
        self, expand_op: ExpandEdges, agg_op: Aggregate
    ) -> AggregationHint | None:
        """Try to create an aggregation hint for pushdown.

        Args:
            expand_op: ExpandEdges operator
            agg_op: Aggregate operator

        Returns:
            AggregationHint if pushdown is safe, None otherwise
        """
        # Must have exactly one aggregation function
        if len(agg_op.agg_exprs) != 1:
            return None

        agg_expr = agg_op.agg_exprs[0]
        if not isinstance(agg_expr, FunctionCall):
            return None

        func_name = agg_expr.name.upper()

        # Only support COUNT, SUM, MIN, MAX
        if func_name not in ("COUNT", "SUM", "MIN", "MAX"):
            return None

        # Don't push down DISTINCT aggregations
        if getattr(agg_expr, "distinct", False):
            return None

        # Must have grouping expressions
        if not agg_op.grouping_exprs:
            return None

        # GROUP BY must include source variable
        source_var_in_group = any(
            isinstance(expr, Variable) and expr.name == expand_op.src_var
            for expr in agg_op.grouping_exprs
        )

        if not source_var_in_group:
            return None

        # For SUM/MIN/MAX, must have argument expression
        if func_name in ("SUM", "MIN", "MAX"):
            if not agg_expr.args or len(agg_expr.args) == 0:
                return None
            # Use first argument as expression to aggregate
            expr = agg_expr.args[0]
        else:
            # COUNT can have no args (COUNT(*)) or args (COUNT(expr))
            expr = agg_expr.args[0] if agg_expr.args else None

        # Extract group by variable names, mapping to their output aliases
        group_by_vars = []
        for group_expr in agg_op.grouping_exprs:
            if isinstance(group_expr, Variable):
                # Check if this variable has an alias in return_items
                alias = None
                for item in agg_op.return_items:
                    if (
                        hasattr(item, "expression")
                        and isinstance(item.expression, Variable)
                        and item.expression.name == group_expr.name
                    ):
                        # Use the alias if present
                        if hasattr(item, "alias") and item.alias:
                            alias = item.alias
                            break

                # If no alias found, use the original variable name
                # This handles cases where the variable is used but not aliased
                if alias is None:
                    alias = group_expr.name

                group_by_vars.append(alias)
            else:
                # Complex grouping expressions not supported yet
                return None

        # Find result variable from return items
        # The aggregation result should be bound to an alias
        result_var = None
        for item in agg_op.return_items:
            # Check if this return item is the aggregation
            if hasattr(item, "expression") and item.expression == agg_expr:
                # Use alias if present, otherwise generate from function name
                if hasattr(item, "alias") and item.alias:
                    result_var = item.alias
                    break

        if result_var is None:
            # Can't determine result variable, can't push down
            return None

        # Create aggregation hint
        return AggregationHint(
            func=func_name, expr=expr, group_by=group_by_vars, result_var=result_var
        )

    def _join_reorder_pass(self, operators: list[Any]) -> list[Any]:
        """Reorder join patterns to avoid Cartesian products.

        Uses cost-based optimization to find the best execution order for
        MATCH patterns based on graph statistics.

        This pass must run early (after filter pushdown but before other passes)
        while pattern operators are still recognizable.

        Algorithm:
            1. Check if reordering is applicable (2+ pattern ops, no side effects)
            2. Split operator list at pipeline boundaries (With, Union, Subquery)
            3. For each segment:
               - Build dependency graph based on variable bindings
               - Enumerate all valid topological orderings
               - Estimate cost for each ordering
               - Select minimum-cost ordering
            4. Reconstruct operator list with optimized segments

        Safety constraints:
            - Only reorders ScanNodes and ExpandEdges operators
            - Preserves variable binding dependencies
            - Doesn't cross pipeline boundaries (With, Union, Subquery)
            - Doesn't reorder if side effects present (CREATE, SET, DELETE, MERGE)

        Args:
            operators: Input operator list

        Returns:
            Operator list with join patterns reordered for minimum cost
        """
        # Can't reorder without statistics
        if self._statistics is None:
            return operators

        from graphforge.optimizer.join_reorder import JoinReorderOptimizer

        optimizer = JoinReorderOptimizer(
            self._statistics,
            max_orderings=self._max_orderings,
        )
        return optimizer.reorder_joins(operators)
