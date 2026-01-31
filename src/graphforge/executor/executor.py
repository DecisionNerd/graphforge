"""Query executor that executes logical plans.

This module implements the execution engine that runs logical plan operators
against a graph store.
"""

from graphforge.ast.expression import FunctionCall
from graphforge.executor.evaluator import ExecutionContext, evaluate_expression
from graphforge.planner.operators import (
    Aggregate,
    ExpandEdges,
    Filter,
    Limit,
    Project,
    ScanNodes,
    Skip,
    Sort,
)
from graphforge.storage.memory import Graph
from graphforge.types.values import CypherBool, CypherFloat, CypherInt, CypherNull


class QueryExecutor:
    """Executes logical query plans against a graph.

    The executor processes a pipeline of operators, streaming rows through
    each stage of the query.
    """

    def __init__(self, graph: Graph):
        """Initialize executor with a graph.

        Args:
            graph: The graph to query
        """
        self.graph = graph

    def execute(self, operators: list) -> list[dict]:
        """Execute a pipeline of operators.

        Args:
            operators: List of logical plan operators

        Returns:
            List of result rows (dicts mapping column names to values)
        """
        # Start with empty context
        rows = [ExecutionContext()]

        # Execute each operator in sequence
        for op in operators:
            rows = self._execute_operator(op, rows)

        return rows

    def _execute_operator(self, op, input_rows: list[ExecutionContext]) -> list[ExecutionContext]:
        """Execute a single operator.

        Args:
            op: Logical plan operator
            input_rows: Input execution contexts

        Returns:
            Output execution contexts
        """
        if isinstance(op, ScanNodes):
            return self._execute_scan(op, input_rows)

        if isinstance(op, ExpandEdges):
            return self._execute_expand(op, input_rows)

        if isinstance(op, Filter):
            return self._execute_filter(op, input_rows)

        if isinstance(op, Project):
            return self._execute_project(op, input_rows)

        if isinstance(op, Limit):
            return self._execute_limit(op, input_rows)

        if isinstance(op, Skip):
            return self._execute_skip(op, input_rows)

        if isinstance(op, Sort):
            return self._execute_sort(op, input_rows)

        if isinstance(op, Aggregate):
            return self._execute_aggregate(op, input_rows)

        raise TypeError(f"Unknown operator type: {type(op).__name__}")

    def _execute_scan(self, op: ScanNodes, input_rows: list[ExecutionContext]) -> list[ExecutionContext]:
        """Execute ScanNodes operator."""
        result = []

        # Get nodes from graph
        if op.labels:
            # Scan by label (TODO: handle multiple labels)
            nodes = self.graph.get_nodes_by_label(op.labels[0])
        else:
            # Scan all nodes
            nodes = self.graph.get_all_nodes()

        # For each input row, bind each node
        for ctx in input_rows:
            for node in nodes:
                new_ctx = ExecutionContext()
                # Copy existing bindings
                new_ctx.bindings = dict(ctx.bindings)
                # Bind new node
                new_ctx.bind(op.variable, node)
                result.append(new_ctx)

        return result

    def _execute_expand(self, op: ExpandEdges, input_rows: list[ExecutionContext]) -> list[ExecutionContext]:
        """Execute ExpandEdges operator."""
        result = []

        for ctx in input_rows:
            src_node = ctx.get(op.src_var)

            # Get edges based on direction
            if op.direction == "OUT":
                edges = self.graph.get_outgoing_edges(src_node.id)
            elif op.direction == "IN":
                edges = self.graph.get_incoming_edges(src_node.id)
            else:  # UNDIRECTED
                edges = self.graph.get_outgoing_edges(src_node.id) + self.graph.get_incoming_edges(src_node.id)

            # Filter by type if specified
            if op.edge_types:
                edges = [e for e in edges if e.type in op.edge_types]

            # Bind edge and dst node
            for edge in edges:
                new_ctx = ExecutionContext()
                new_ctx.bindings = dict(ctx.bindings)

                if op.edge_var:
                    new_ctx.bind(op.edge_var, edge)

                # Determine dst node based on direction
                if op.direction == "OUT":
                    dst_node = edge.dst
                elif op.direction == "IN":
                    dst_node = edge.src
                else:  # UNDIRECTED - use whichever is not src
                    dst_node = edge.dst if edge.src.id == src_node.id else edge.src

                new_ctx.bind(op.dst_var, dst_node)
                result.append(new_ctx)

        return result

    def _execute_filter(self, op: Filter, input_rows: list[ExecutionContext]) -> list[ExecutionContext]:
        """Execute Filter operator."""
        result = []

        for ctx in input_rows:
            # Evaluate predicate
            value = evaluate_expression(op.predicate, ctx)

            # Keep row if predicate is true
            if isinstance(value, CypherBool) and value.value:
                result.append(ctx)

        return result

    def _execute_project(self, op: Project, input_rows: list[ExecutionContext]) -> list[dict]:
        """Execute Project operator."""
        result = []

        for ctx in input_rows:
            row = {}
            for i, return_item in enumerate(op.items):
                # Extract expression and alias from ReturnItem
                value = evaluate_expression(return_item.expression, ctx)
                # Use alias if provided, otherwise generate default column name
                key = return_item.alias if return_item.alias else f"col_{i}"
                row[key] = value
            result.append(row)

        return result

    def _execute_limit(self, op: Limit, input_rows: list) -> list:
        """Execute Limit operator."""
        return input_rows[:op.count]

    def _execute_skip(self, op: Skip, input_rows: list) -> list:
        """Execute Skip operator."""
        return input_rows[op.count:]

    def _execute_sort(self, op: Sort, input_rows: list[ExecutionContext]) -> list[ExecutionContext]:
        """Execute Sort operator.

        Sorts rows by evaluating sort expressions and applying directions.
        NULL values are handled according to Cypher semantics:
        - ASC: NULLs last
        - DESC: NULLs first

        Supports referencing RETURN aliases by pre-evaluating RETURN expressions.
        """
        if not input_rows:
            return input_rows

        # Pre-evaluate RETURN expressions with aliases and extend contexts
        # This allows ORDER BY to reference aliases defined in RETURN
        # Keep mapping from extended context to original context
        # Note: Skip aggregate functions - they can't be evaluated until after Aggregate operator
        extended_rows = []
        context_mapping = {}  # Maps id(extended_ctx) -> original_ctx

        for ctx in input_rows:
            extended_ctx = ExecutionContext()
            extended_ctx.bindings = dict(ctx.bindings)

            # Add RETURN aliases to context
            if op.return_items:
                for return_item in op.return_items:
                    if return_item.alias:
                        # Skip aggregate functions (COUNT, SUM, AVG, etc.)
                        # They must be evaluated by the Aggregate operator
                        if not isinstance(return_item.expression, FunctionCall):
                            # Evaluate the expression and bind it with the alias name
                            value = evaluate_expression(return_item.expression, ctx)
                            extended_ctx.bind(return_item.alias, value)

            extended_rows.append(extended_ctx)
            context_mapping[id(extended_ctx)] = ctx

        def compare_values(val1, val2, ascending):
            """Compare two CypherValues."""
            # Handle NULLs
            is_null1 = isinstance(val1, CypherNull)
            is_null2 = isinstance(val2, CypherNull)

            if is_null1 and is_null2:
                return 0
            if is_null1:
                return 1 if ascending else -1  # NULLs last in ASC, first in DESC
            if is_null2:
                return -1 if ascending else 1

            # Compare non-NULL values using less_than
            result = val1.less_than(val2)
            if isinstance(result, CypherBool):
                if result.value:
                    return -1 if ascending else 1
                # Check if val2 < val1
                result2 = val2.less_than(val1)
                if isinstance(result2, CypherBool) and result2.value:
                    return 1 if ascending else -1
                return 0  # Equal
            return 0  # NULL comparison result, treat as equal

        from functools import cmp_to_key

        def multi_key_compare(ctx1, ctx2):
            """Compare two contexts by all sort keys."""
            for order_item in op.items:
                val1 = evaluate_expression(order_item.expression, ctx1)
                val2 = evaluate_expression(order_item.expression, ctx2)
                cmp_result = compare_values(val1, val2, order_item.ascending)
                if cmp_result != 0:
                    return cmp_result
            return 0  # All keys equal

        sorted_extended_rows = sorted(extended_rows, key=cmp_to_key(multi_key_compare))

        # Map back to original contexts maintaining the sorted order
        result_rows = []
        for sorted_ctx in sorted_extended_rows:
            original_ctx = context_mapping[id(sorted_ctx)]
            result_rows.append(original_ctx)

        return result_rows

    def _execute_aggregate(self, op: Aggregate, input_rows: list[ExecutionContext]) -> list[dict]:
        """Execute Aggregate operator.

        Groups rows by grouping expressions and computes aggregation functions.
        Returns one row per group with grouping values and aggregate results.
        """
        from collections import defaultdict

        # Handle empty input
        if not input_rows:
            # If no grouping (only aggregates), return one row with NULL/0 aggregates
            if not op.grouping_exprs:
                return [self._compute_aggregates_for_group(op, [])]
            return []

        # Group rows by grouping expressions
        if op.grouping_exprs:
            # Multiple groups
            groups = defaultdict(list)
            for ctx in input_rows:
                # Compute grouping key
                key_values = tuple(
                    self._value_to_hashable(evaluate_expression(expr, ctx))
                    for expr in op.grouping_exprs
                )
                groups[key_values].append(ctx)
        else:
            # No grouping - single group with all rows
            groups = {(): input_rows}

        # Compute aggregates for each group
        result = []
        for group_key, group_rows in groups.items():
            row = self._compute_aggregates_for_group(op, group_rows, group_key)
            result.append(row)

        return result

    def _value_to_hashable(self, value):
        """Convert CypherValue to hashable key for grouping."""
        if isinstance(value, CypherNull):
            return None
        if isinstance(value, (CypherInt, CypherFloat, CypherBool)):
            return (type(value).__name__, value.value)
        if hasattr(value, 'value'):
            # CypherString, etc.
            return (type(value).__name__, value.value)
        # NodeRef, EdgeRef have their own hash
        return value

    def _compute_aggregates_for_group(self, op: Aggregate, group_rows: list[ExecutionContext], group_key=None) -> dict:
        """Compute aggregates for a single group.

        Args:
            op: Aggregate operator
            group_rows: Rows in this group
            group_key: Tuple of grouping values (or None)

        Returns:
            Dict with both grouping values and aggregate results
        """
        row = {}

        # Add grouping values to result
        if group_key:
            for i, expr in enumerate(op.grouping_exprs):
                # Find the corresponding ReturnItem to get the alias
                for j, return_item in enumerate(op.return_items):
                    if return_item.expression == expr:
                        key = return_item.alias if return_item.alias else f"col_{j}"
                        # Convert back from hashable to CypherValue
                        hashable_val = group_key[i]
                        if hashable_val is None:
                            row[key] = CypherNull()
                        elif isinstance(hashable_val, tuple) and len(hashable_val) == 2:
                            type_name, val = hashable_val
                            if type_name == 'CypherInt':
                                row[key] = CypherInt(val)
                            elif type_name == 'CypherFloat':
                                row[key] = CypherFloat(val)
                            elif type_name == 'CypherBool':
                                from graphforge.types.values import CypherBool as CB
                                row[key] = CB(val)
                            else:
                                from graphforge.types.values import CypherString
                                row[key] = CypherString(val)
                        else:
                            # NodeRef, EdgeRef, etc.
                            row[key] = hashable_val
                        break

        # Compute aggregates
        for agg_expr in op.agg_exprs:
            assert isinstance(agg_expr, FunctionCall)

            # Find the corresponding ReturnItem to get the alias
            for j, return_item in enumerate(op.return_items):
                if return_item.expression == agg_expr:
                    key = return_item.alias if return_item.alias else f"col_{j}"

                    # Compute the aggregation
                    result_value = self._compute_aggregation(agg_expr, group_rows)
                    row[key] = result_value
                    break

        return row

    def _compute_aggregation(self, func_call: FunctionCall, group_rows: list[ExecutionContext]):
        """Compute a single aggregation function over a group.

        Args:
            func_call: FunctionCall node with aggregation function
            group_rows: Rows in the group

        Returns:
            CypherValue result of the aggregation
        """
        func_name = func_call.name.upper()

        # COUNT(*) or COUNT(expr)
        if func_name == "COUNT":
            if not func_call.args:  # COUNT(*)
                return CypherInt(len(group_rows))

            # COUNT(expr) - count non-NULL values
            count = 0
            seen = set() if func_call.distinct else None

            for ctx in group_rows:
                value = evaluate_expression(func_call.args[0], ctx)
                if not isinstance(value, CypherNull):
                    if func_call.distinct:
                        hashable = self._value_to_hashable(value)
                        if hashable not in seen:
                            seen.add(hashable)
                            count += 1
                    else:
                        count += 1

            return CypherInt(count)

        # SUM, AVG, MIN, MAX require evaluating the expression
        values = []
        for ctx in group_rows:
            value = evaluate_expression(func_call.args[0], ctx)
            if not isinstance(value, CypherNull):
                if func_call.distinct:
                    hashable = self._value_to_hashable(value)
                    if hashable not in (self._value_to_hashable(v) for v in values):
                        values.append(value)
                else:
                    values.append(value)

        # If no non-NULL values, return NULL for most functions
        if not values:
            return CypherNull()

        # SUM
        if func_name == "SUM":
            total = 0
            is_float = False
            for val in values:
                if isinstance(val, CypherFloat):
                    is_float = True
                    total += val.value
                elif isinstance(val, CypherInt):
                    total += val.value
            return CypherFloat(total) if is_float else CypherInt(total)

        # AVG
        if func_name == "AVG":
            total = 0.0
            for val in values:
                if isinstance(val, (CypherInt, CypherFloat)):
                    total += val.value
            return CypherFloat(total / len(values))

        # MIN
        if func_name == "MIN":
            min_val = values[0]
            for val in values[1:]:
                result = val.less_than(min_val)
                if isinstance(result, CypherBool) and result.value:
                    min_val = val
            return min_val

        # MAX
        if func_name == "MAX":
            max_val = values[0]
            for val in values[1:]:
                result = max_val.less_than(val)
                if isinstance(result, CypherBool) and result.value:
                    max_val = val
            return max_val

        raise ValueError(f"Unknown aggregation function: {func_name}")
