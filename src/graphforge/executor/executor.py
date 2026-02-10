"""Query executor that executes logical plans.

This module implements the execution engine that runs logical plan operators
against a graph store.
"""

from typing import Any

from graphforge.ast.expression import FunctionCall, PropertyAccess, Variable
from graphforge.executor.evaluator import ExecutionContext, evaluate_expression
from graphforge.planner.operators import (
    Aggregate,
    Create,
    Delete,
    Distinct,
    ExpandEdges,
    ExpandVariableLength,
    Filter,
    Limit,
    Merge,
    OptionalExpandEdges,
    OptionalScanNodes,
    Project,
    Remove,
    ScanNodes,
    Set,
    Skip,
    Sort,
    Subquery,
    Union,
    Unwind,
    With,
)
from graphforge.storage.memory import Graph
from graphforge.types.values import (
    CypherBool,
    CypherFloat,
    CypherInt,
    CypherList,
    CypherMap,
    CypherNull,
    CypherValue,
)


def _cypher_to_python(cypher_val: CypherValue) -> Any:
    """Convert CypherValue to Python value for storage.

    Recursively converts CypherList and CypherMap to Python list and dict.

    Args:
        cypher_val: CypherValue to convert

    Returns:
        Python value (None, bool, int, float, str, list, dict)
    """
    if isinstance(cypher_val, CypherNull):
        return None
    elif isinstance(cypher_val, (CypherBool, CypherInt, CypherFloat)):
        return cypher_val.value
    elif isinstance(cypher_val, CypherList):
        return [_cypher_to_python(item) for item in cypher_val.value]
    elif isinstance(cypher_val, CypherMap):
        return {k: _cypher_to_python(v) for k, v in cypher_val.value.items()}
    else:
        # CypherString or any other type
        return cypher_val.value


class QueryExecutor:
    """Executes logical query plans against a graph.

    The executor processes a pipeline of operators, streaming rows through
    each stage of the query.
    """

    def __init__(self, graph: Graph, graphforge=None, planner=None):
        """Initialize executor with a graph.

        Args:
            graph: The graph to query
            graphforge: Optional GraphForge instance for CREATE operations
            planner: Optional QueryPlanner instance for subquery execution
        """
        self.graph = graph
        self.graphforge = graphforge
        self.planner = planner

    def execute(self, operators: list) -> list[dict]:
        """Execute a pipeline of operators.

        Args:
            operators: List of logical plan operators

        Returns:
            List of result rows (dicts mapping column names to values)
        """
        # Start with empty context
        rows: list[Any] = [ExecutionContext()]

        # Execute each operator in sequence
        for i, op in enumerate(operators):
            rows = self._execute_operator(op, rows, i, len(operators))

        # If there's no Project or Aggregate operator in the pipeline (no RETURN clause),
        # return empty results (Cypher semantics: queries without RETURN produce no output)
        # Exception: Union operators contain their own RETURN clauses in branches
        if operators and not any(isinstance(op, (Project, Aggregate, Union)) for op in operators):
            return []

        # At this point, rows has been converted to list[dict] by Project/Aggregate operator
        # (or Union operator which also returns list[dict])
        return rows

    def _execute_operator(
        self,
        op,
        input_rows: list[Any],
        op_index: int,
        total_ops: int,
    ) -> list[Any]:
        """Execute a single operator.

        Args:
            op: Logical plan operator
            input_rows: Input execution contexts
            op_index: Index of current operator in pipeline
            total_ops: Total number of operators in pipeline

        Returns:
            Output execution contexts or dicts (for final Project/Aggregate)
        """
        if isinstance(op, ScanNodes):
            return self._execute_scan(op, input_rows)

        if isinstance(op, OptionalScanNodes):
            return self._execute_optional_scan(op, input_rows)

        if isinstance(op, ExpandEdges):
            return self._execute_expand(op, input_rows)

        from graphforge.planner.operators import ExpandVariableLength

        if isinstance(op, ExpandVariableLength):
            return self._execute_variable_expand(op, input_rows)

        if isinstance(op, OptionalExpandEdges):
            return self._execute_optional_expand(op, input_rows)

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
            # Determine if we're in WITH context (more operators follow)
            # In WITH, return ExecutionContexts; in RETURN, return dicts
            for_with = op_index < total_ops - 1
            return self._execute_aggregate(op, input_rows, for_with=for_with)

        if isinstance(op, Create):
            return self._execute_create(op, input_rows)

        if isinstance(op, Set):
            return self._execute_set(op, input_rows)

        if isinstance(op, Remove):
            return self._execute_remove(op, input_rows)

        if isinstance(op, Delete):
            return self._execute_delete(op, input_rows)

        if isinstance(op, Merge):
            return self._execute_merge(op, input_rows)

        if isinstance(op, Unwind):
            return self._execute_unwind(op, input_rows)

        if isinstance(op, With):
            return self._execute_with(op, input_rows)

        if isinstance(op, Distinct):
            return self._execute_distinct(op, input_rows)

        if isinstance(op, Union):
            return self._execute_union(op, input_rows)

        if isinstance(op, Subquery):
            return self._execute_subquery(op, input_rows)

        raise TypeError(f"Unknown operator type: {type(op).__name__}")

    def _execute_scan(
        self, op: ScanNodes, input_rows: list[ExecutionContext]
    ) -> list[ExecutionContext]:
        """Execute ScanNodes operator.

        If the variable is already bound in the input context (e.g., from WITH),
        validate that the bound node matches the pattern instead of doing a full scan.
        """
        result = []

        # For each input row
        for ctx in input_rows:
            # Check if variable is already bound (e.g., from WITH clause)
            if op.variable in ctx.bindings:
                # Variable already bound - validate it matches the pattern
                bound_node = ctx.get(op.variable)

                # Check if bound node has required labels
                if op.labels:
                    if all(label in bound_node.labels for label in op.labels):
                        # Node matches pattern - keep the context
                        result.append(ctx)
                else:
                    # No label requirements - keep the context
                    result.append(ctx)
            else:
                # Variable not bound - do normal scan
                if op.labels:
                    # Scan by first label for efficiency
                    nodes = self.graph.get_nodes_by_label(op.labels[0])

                    # Filter to only nodes with ALL required labels
                    if len(op.labels) > 1:
                        nodes = [
                            node
                            for node in nodes
                            if all(label in node.labels for label in op.labels)
                        ]
                else:
                    # Scan all nodes
                    nodes = self.graph.get_all_nodes()

                # Bind each node
                for node in nodes:
                    new_ctx = ExecutionContext()
                    # Copy existing bindings
                    new_ctx.bindings = dict(ctx.bindings)
                    # Bind new node
                    new_ctx.bind(op.variable, node)
                    result.append(new_ctx)

        return result

    def _execute_optional_scan(
        self, op: OptionalScanNodes, input_rows: list[ExecutionContext]
    ) -> list[ExecutionContext]:
        """Execute OptionalScanNodes operator with LEFT JOIN semantics.

        Like ScanNodes but preserves input rows with NULL binding when no match found.
        """
        result = []

        # For each input row
        for ctx in input_rows:
            # Check if variable is already bound (e.g., from WITH clause)
            if op.variable in ctx.bindings:
                # Variable already bound - validate it matches the pattern
                bound_node = ctx.get(op.variable)

                # Check if bound node has required labels
                if op.labels:
                    if all(label in bound_node.labels for label in op.labels):
                        # Node matches pattern - keep the context
                        result.append(ctx)
                    else:
                        # Node doesn't match - OPTIONAL preserves row with NULL
                        new_ctx = ExecutionContext()
                        new_ctx.bindings = dict(ctx.bindings)
                        new_ctx.bind(op.variable, CypherNull())
                        result.append(new_ctx)
                else:
                    # No label requirements - keep the context
                    result.append(ctx)
            else:
                # Variable not bound - do normal scan
                if op.labels:
                    # Scan by first label for efficiency
                    nodes = self.graph.get_nodes_by_label(op.labels[0])

                    # Filter to only nodes with ALL required labels
                    if len(op.labels) > 1:
                        nodes = [
                            node
                            for node in nodes
                            if all(label in node.labels for label in op.labels)
                        ]
                else:
                    # Scan all nodes
                    nodes = self.graph.get_all_nodes()

                if nodes:
                    # Bind each node
                    for node in nodes:
                        new_ctx = ExecutionContext()
                        new_ctx.bindings = dict(ctx.bindings)
                        new_ctx.bind(op.variable, node)
                        result.append(new_ctx)
                else:
                    # OPTIONAL semantics: No nodes found - preserve row with NULL
                    new_ctx = ExecutionContext()
                    new_ctx.bindings = dict(ctx.bindings)
                    new_ctx.bind(op.variable, CypherNull())
                    result.append(new_ctx)

        return result

    def _execute_expand(
        self, op: ExpandEdges, input_rows: list[ExecutionContext]
    ) -> list[ExecutionContext]:
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
                edges = self.graph.get_outgoing_edges(src_node.id) + self.graph.get_incoming_edges(
                    src_node.id
                )

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

    def _execute_variable_expand(
        self, op: ExpandVariableLength, input_rows: list[ExecutionContext]
    ) -> list[ExecutionContext]:
        """Execute ExpandVariableLength operator with recursive traversal and cycle detection."""
        result = []

        for ctx in input_rows:
            src_node = ctx.get(op.src_var)

            # Perform depth-first search with cycle detection
            from graphforge.types.graph import EdgeRef, NodeRef

            stack: list[tuple[NodeRef, list[EdgeRef], int, set[str | int]]] = [
                (src_node, [], 0, {src_node.id})
            ]

            while stack:
                current_node, edge_path, depth, visited_in_path = stack.pop()

                # Check if we've reached valid depth range
                if op.min_hops <= depth <= (op.max_hops if op.max_hops else float("inf")):
                    # Yield this path
                    new_ctx = ExecutionContext()
                    new_ctx.bindings = dict(ctx.bindings)

                    new_ctx.bind(op.dst_var, current_node)

                    # Bind edge list if variable provided
                    # Note: Binding raw list of EdgeRef objects (not wrapped in CypherList)
                    # since EdgeRef is not a CypherValue and individual edges are bound directly
                    if op.edge_var:
                        new_ctx.bind(op.edge_var, edge_path)

                    result.append(new_ctx)

                # Continue exploration if we haven't exceeded max depth
                if op.max_hops is None or depth < op.max_hops:
                    # Get edges based on direction
                    if op.direction == "OUT":
                        edges = self.graph.get_outgoing_edges(current_node.id)
                    elif op.direction == "IN":
                        edges = self.graph.get_incoming_edges(current_node.id)
                    else:  # UNDIRECTED
                        edges = self.graph.get_outgoing_edges(
                            current_node.id
                        ) + self.graph.get_incoming_edges(current_node.id)

                    # Filter by type if specified
                    if op.edge_types:
                        edges = [e for e in edges if e.type in op.edge_types]

                    # Add edges to stack for exploration
                    for edge in edges:
                        # Determine next node
                        if op.direction == "OUT":
                            next_node = edge.dst
                        elif op.direction == "IN":
                            next_node = edge.src
                        else:  # UNDIRECTED
                            next_node = edge.dst if edge.src.id == current_node.id else edge.src

                        # Cycle detection - don't revisit nodes in current path
                        if next_node.id not in visited_in_path:
                            new_visited = visited_in_path | {next_node.id}
                            stack.append((next_node, [*edge_path, edge], depth + 1, new_visited))

        return result

    def _execute_filter(
        self, op: Filter, input_rows: list[ExecutionContext]
    ) -> list[ExecutionContext]:
        """Execute Filter operator."""
        result = []

        for ctx in input_rows:
            # Evaluate predicate
            value = evaluate_expression(op.predicate, ctx, self)

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
                value = evaluate_expression(return_item.expression, ctx, self)

                # Determine column name
                if return_item.alias:
                    # Explicit alias provided - use it
                    key = return_item.alias
                elif isinstance(return_item.expression, Variable):
                    # Simple variable reference - use variable name as column name
                    # This preserves names from WITH clauses
                    key = return_item.expression.name
                elif isinstance(return_item.expression, PropertyAccess):
                    # Property access - use dotted notation (e.g., "p.name")
                    key = f"{return_item.expression.variable}.{return_item.expression.property}"
                else:
                    # Complex expression without alias - use default column naming
                    key = f"col_{i}"

                row[key] = value
            result.append(row)

        return result

    def _execute_with(self, op: With, input_rows: list[ExecutionContext]) -> list[ExecutionContext]:
        """Execute WITH operator.

        WITH acts as a pipeline boundary, projecting specified columns and
        optionally filtering, sorting, and paginating.

        Unlike Project, WITH returns ExecutionContexts (not final dicts) so the
        query can continue with more clauses.

        Args:
            op: WITH operator with items, predicate, sort_items, skip_count, limit_count
            input_rows: Input execution contexts

        Returns:
            List of ExecutionContexts with only the projected variables
        """
        from graphforge.ast.expression import Variable

        # Step 1: Project items into new contexts
        result = []

        for ctx in input_rows:
            new_ctx = ExecutionContext()

            for return_item in op.items:
                # Evaluate expression
                value = evaluate_expression(return_item.expression, ctx, self)

                # Determine variable name to bind
                if return_item.alias:
                    # Explicit alias provided
                    var_name = return_item.alias
                elif isinstance(return_item.expression, Variable):
                    # No alias, but expression is a variable - use variable name
                    var_name = return_item.expression.name
                else:
                    # Complex expression without alias - skip binding
                    # (This is technically invalid Cypher, but we'll allow it)
                    continue

                # Bind the value in the new context
                new_ctx.bind(var_name, value)

            result.append(new_ctx)

        # Step 2: Apply optional WHERE filter
        if op.predicate:
            filtered = []
            for ctx in result:
                value = evaluate_expression(op.predicate, ctx, self)
                if isinstance(value, CypherBool) and value.value:
                    filtered.append(ctx)
            result = filtered

        # Step 3: Apply optional ORDER BY sort
        if op.sort_items:
            # Similar to _execute_sort but simpler since WITH items are already projected
            from functools import cmp_to_key

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

                # Compare non-NULL values
                comp_result = val1.less_than(val2)
                if isinstance(comp_result, CypherBool):
                    if comp_result.value:
                        return -1 if ascending else 1
                    comp_result2 = val2.less_than(val1)
                    if isinstance(comp_result2, CypherBool) and comp_result2.value:
                        return 1 if ascending else -1
                    return 0
                return 0

            def compare_rows(ctx1, ctx2):
                """Compare two contexts by evaluating sort expressions."""
                for sort_item in op.sort_items:  # type: ignore[union-attr]
                    val1 = evaluate_expression(sort_item.expression, ctx1, self)
                    val2 = evaluate_expression(sort_item.expression, ctx2, self)
                    cmp = compare_values(val1, val2, sort_item.ascending)
                    if cmp != 0:
                        return cmp
                return 0

            result = sorted(result, key=cmp_to_key(compare_rows))

        # Step 4: Apply optional SKIP
        if op.skip_count is not None:
            result = result[op.skip_count :]

        # Step 5: Apply optional LIMIT
        if op.limit_count is not None:
            result = result[: op.limit_count]

        return result

    def _execute_limit(self, op: Limit, input_rows: list) -> list:
        """Execute Limit operator."""
        return input_rows[: op.count]

    def _execute_skip(self, op: Skip, input_rows: list) -> list:
        """Execute Skip operator."""
        return input_rows[op.count :]

    def _execute_distinct(self, op: Distinct, input_rows: list) -> list:
        """Execute DISTINCT operator.

        Removes duplicate rows by comparing all bound variables.
        Handles both ExecutionContext objects (before projection) and
        dict objects (after projection).
        """
        if not input_rows:
            return input_rows

        seen = set()
        result = []

        for ctx in input_rows:
            # Create hashable key from all bindings
            # Handle both ExecutionContext and dict types
            if isinstance(ctx, dict):
                # After projection - ctx is a dict
                keys = sorted(ctx.keys())
                key_items = []
                for var_name in keys:
                    value = ctx[var_name]
                    hashable = self._value_to_hashable(value)
                    key_items.append((var_name, hashable))
            else:
                # Before projection - ctx is ExecutionContext
                key_items = []
                for var_name in sorted(ctx.bindings.keys()):
                    value = ctx.bindings[var_name]
                    hashable = self._value_to_hashable(value)
                    key_items.append((var_name, hashable))

            key = tuple(key_items)
            if key not in seen:
                seen.add(key)
                result.append(ctx)

        return result

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

        # Check if ORDER BY expressions can already be evaluated from input context
        # This happens after aggregation where aliases are already bound
        skip_return_items_eval = False
        if input_rows and op.items:
            try:
                # Try to evaluate all ORDER BY expressions from first context
                for order_item in op.items:
                    evaluate_expression(order_item.expression, input_rows[0], self)
                # If we got here, all ORDER BY expressions are available - skip return_items eval
                skip_return_items_eval = True
            except (KeyError, AttributeError):
                # ORDER BY references something not in context - need return_items eval
                skip_return_items_eval = False

        extended_rows = []
        context_mapping = {}  # Maps id(extended_ctx) -> original_ctx

        for ctx in input_rows:
            extended_ctx = ExecutionContext()
            extended_ctx.bindings = dict(ctx.bindings)

            # Add RETURN aliases to context (only if not after aggregation)
            if op.return_items and not skip_return_items_eval:
                for return_item in op.return_items:
                    if return_item.alias:
                        # Skip aggregate functions (COUNT, SUM, AVG, etc.)
                        # They must be evaluated by the Aggregate operator
                        if not isinstance(return_item.expression, FunctionCall):
                            # Evaluate the expression and bind it with the alias name
                            value = evaluate_expression(return_item.expression, ctx, self)
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
                val1 = evaluate_expression(order_item.expression, ctx1, self)
                val2 = evaluate_expression(order_item.expression, ctx2, self)
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

    def _expressions_match(self, expr1, expr2) -> bool:
        """Check if two expressions are semantically equivalent.

        Args:
            expr1: First expression
            expr2: Second expression

        Returns:
            True if expressions are semantically equivalent
        """
        from graphforge.ast.expression import Literal, PropertyAccess, Variable

        # Same object
        if expr1 is expr2:
            return True

        # Different types
        if not isinstance(expr1, type(expr2)):
            return False

        # Variable: compare by name
        if isinstance(expr1, Variable) and isinstance(expr2, Variable):
            return expr1.name == expr2.name

        # PropertyAccess: compare variable and property
        if isinstance(expr1, PropertyAccess) and isinstance(expr2, PropertyAccess):
            return (
                self._expressions_match(expr1.variable, expr2.variable)
                and expr1.property == expr2.property
            )

        # Literal: compare values
        if isinstance(expr1, Literal) and isinstance(expr2, Literal):
            return bool(expr1.value == expr2.value)

        # FunctionCall: compare function name and arguments
        if isinstance(expr1, FunctionCall) and isinstance(expr2, FunctionCall):
            if expr1.name.lower() != expr2.name.lower():
                return False
            if len(expr1.args) != len(expr2.args):
                return False
            return all(self._expressions_match(a1, a2) for a1, a2 in zip(expr1.args, expr2.args))

        # For other types, fall back to object identity
        return False

    def _execute_aggregate(
        self, op: Aggregate, input_rows: list[ExecutionContext], for_with: bool = False
    ) -> list[dict] | list[ExecutionContext]:
        """Execute Aggregate operator.

        Groups rows by grouping expressions and computes aggregation functions.

        Args:
            op: Aggregate operator
            input_rows: Input execution contexts
            for_with: If True, return ExecutionContexts for WITH; if False, return dicts for RETURN

        Returns:
            List of dicts (for RETURN) or ExecutionContexts (for WITH)
        """
        from collections import defaultdict

        # Handle empty input
        if not input_rows:
            # If no grouping (only aggregates), return one row with NULL/0 aggregates
            if not op.grouping_exprs:
                if for_with:
                    # Return ExecutionContext for WITH
                    ctx = ExecutionContext()
                    for agg_expr in op.agg_exprs:
                        for item in op.return_items:
                            if item.expression == agg_expr:
                                var_name = item.alias if item.alias else "col_0"
                                result_value = self._compute_aggregation(agg_expr, [])
                                ctx.bind(var_name, result_value)
                                break
                    return [ctx]
                else:
                    return [self._compute_aggregates_for_group(op, [])]
            return []

        # Group rows by grouping expressions
        if op.grouping_exprs:
            # Multiple groups
            groups = defaultdict(list)
            for ctx in input_rows:
                # Compute grouping key
                key_values = tuple(
                    self._value_to_hashable(evaluate_expression(expr, ctx, self))
                    for expr in op.grouping_exprs
                )
                groups[key_values].append(ctx)
        else:
            # No grouping - single group with all rows
            groups = {(): input_rows}  # type: ignore[assignment]

        # Compute aggregates for each group
        result: list[Any] = []
        for group_key, group_rows in groups.items():
            if for_with:
                # Return ExecutionContext for WITH clauses
                ctx = ExecutionContext()

                # Bind grouping values
                for i, (expr, val) in enumerate(zip(op.grouping_exprs, group_key)):
                    # Find alias from return_items
                    for item in op.return_items:
                        if self._expressions_match(item.expression, expr):
                            # Determine variable name
                            if item.alias:
                                var_name = item.alias
                            elif isinstance(expr, Variable):
                                # No alias, but expression is a variable - use variable name
                                var_name = expr.name
                            else:
                                # Complex expression without alias - use column index
                                var_name = f"col_{i}"
                            ctx.bind(var_name, self._hashable_to_cypher_value(val))
                            break

                # Compute and bind aggregates
                for agg_expr in op.agg_exprs:
                    # Find alias from return_items
                    for item in op.return_items:
                        if self._expressions_match(item.expression, agg_expr):
                            var_name = item.alias if item.alias else "col_0"
                            result_value = self._compute_aggregation(agg_expr, group_rows)
                            ctx.bind(var_name, result_value)
                            break

                result.append(ctx)
            else:
                # Return dict for RETURN clauses (existing behavior)
                row = self._compute_aggregates_for_group(op, group_rows, group_key)
                result.append(row)

        return result

    def _value_to_hashable(self, value):
        """Convert CypherValue to hashable key for grouping.

        Recursively handles CypherList and CypherMap to produce stable,
        hashable representations for use with COLLECT DISTINCT and grouping.
        """
        from graphforge.types.values import CypherList, CypherMap

        if isinstance(value, CypherNull):
            return None
        if isinstance(value, (CypherInt, CypherFloat, CypherBool)):
            return (type(value).__name__, value.value)
        if isinstance(value, CypherList):
            # Recursively convert list elements to hashable tuple
            return (type(value).__name__, tuple(self._value_to_hashable(v) for v in value.value))
        if isinstance(value, CypherMap):
            # Convert map to tuple of sorted (key, hashable-value) pairs
            return (
                type(value).__name__,
                tuple(sorted((k, self._value_to_hashable(v)) for k, v in value.value.items())),
            )
        if hasattr(value, "value"):
            # CypherString, etc.
            return (type(value).__name__, value.value)
        # NodeRef, EdgeRef have their own hash
        return value

    def _hashable_to_cypher_value(self, hashable_val):
        """Convert hashable representation back to CypherValue.

        Recursively reconstructs CypherList and CypherMap from their
        hashable tuple representations.
        """
        from graphforge.types.values import CypherList, CypherMap, CypherString

        if hashable_val is None:
            return CypherNull()
        elif isinstance(hashable_val, tuple) and len(hashable_val) == 2:
            type_name, val = hashable_val
            if type_name == "CypherInt":
                return CypherInt(val)
            elif type_name == "CypherFloat":
                return CypherFloat(val)
            elif type_name == "CypherBool":
                return CypherBool(val)
            elif type_name == "CypherString":
                return CypherString(val)
            elif type_name == "CypherList":
                # Recursively reconstruct list from tuple of hashable items
                reconstructed_items = [self._hashable_to_cypher_value(item) for item in val]
                return CypherList(reconstructed_items)
            elif type_name == "CypherMap":
                # Recursively reconstruct map from tuple of (key, hashable-value) pairs
                reconstructed_map = {k: self._hashable_to_cypher_value(v) for k, v in val}
                return CypherMap(reconstructed_map)

        # NodeRef, EdgeRef, or already a CypherValue
        return hashable_val

    def _compute_aggregates_for_group(
        self, op: Aggregate, group_rows: list[ExecutionContext], group_key=None
    ) -> dict:
        """Compute aggregates for a single group.

        Args:
            op: Aggregate operator
            group_rows: Rows in this group
            group_key: Tuple of grouping values (or None)

        Returns:
            Dict with both grouping values and aggregate results
        """
        row: dict[str, Any] = {}

        # Add grouping values to result
        if group_key:
            for i, expr in enumerate(op.grouping_exprs):
                # Find the corresponding ReturnItem to get the alias
                for j, return_item in enumerate(op.return_items):
                    if return_item.expression == expr:
                        key = return_item.alias if return_item.alias else f"col_{j}"
                        # Convert back from hashable to CypherValue
                        hashable_val = group_key[i]
                        row[key] = self._hashable_to_cypher_value(hashable_val)
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
            seen: set[Any] | None = set() if func_call.distinct else None

            for ctx in group_rows:
                value = evaluate_expression(func_call.args[0], ctx, self)
                if not isinstance(value, CypherNull):
                    if func_call.distinct and seen is not None:
                        hashable = self._value_to_hashable(value)
                        if hashable not in seen:
                            seen.add(hashable)
                            count += 1
                    else:
                        count += 1

            return CypherInt(count)

        # COLLECT - always return a list (even if empty, unlike other aggregations)
        if func_name == "COLLECT":
            from graphforge.types.values import CypherList

            collected_values: list[CypherValue] = []
            seen_hashes: set[Any] = set()

            for ctx in group_rows:
                value = evaluate_expression(func_call.args[0], ctx, self)
                # Skip NULL values
                if not isinstance(value, CypherNull):
                    if func_call.distinct:
                        hashable = self._value_to_hashable(value)
                        if hashable not in seen_hashes:
                            seen_hashes.add(hashable)
                            collected_values.append(value)
                    else:
                        collected_values.append(value)

            return CypherList(collected_values)

        # SUM, AVG, MIN, MAX require evaluating the expression
        values: list[Any] = []
        for ctx in group_rows:
            value = evaluate_expression(func_call.args[0], ctx, self)
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
            total: int | float = 0
            is_float = False
            for val in values:
                if isinstance(val, CypherFloat):
                    is_float = True
                    total += val.value
                elif isinstance(val, CypherInt):
                    total += val.value
            return CypherFloat(total) if is_float else CypherInt(int(total))

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

    def _execute_create(
        self, op: Create, input_rows: list[ExecutionContext]
    ) -> list[ExecutionContext]:
        """Execute CREATE operator.

        Creates nodes and relationships from patterns.

        Args:
            op: Create operator with patterns
            input_rows: Input execution contexts

        Returns:
            Execution contexts with created elements bound to variables
        """
        if not self.graphforge:
            raise RuntimeError("CREATE requires GraphForge instance")

        from graphforge.ast.pattern import NodePattern, RelationshipPattern

        result = []

        # Process each input row (usually just one for CREATE)
        for ctx in input_rows:
            new_ctx = ExecutionContext()
            new_ctx.bindings = ctx.bindings.copy()

            # Process each pattern
            for pattern in op.patterns:
                if not pattern:
                    continue

                # Extract pattern parts from new format (dict with path_variable and parts)
                # or use pattern directly if it's old format (list)
                if isinstance(pattern, dict) and "parts" in pattern:
                    path_var = pattern.get("path_variable")
                    pattern_parts = pattern["parts"]
                    # TODO: Phase 3 will use path_var to bind CypherPath objects
                else:
                    # Old format: pattern is already a list
                    pattern_parts = pattern
                    path_var = None

                # Handle simple node pattern: CREATE (n:Person {name: 'Alice'})
                if len(pattern_parts) == 1 and isinstance(pattern_parts[0], NodePattern):
                    node_pattern = pattern_parts[0]
                    node = self._create_node_from_pattern(node_pattern, new_ctx)
                    if node_pattern.variable:
                        new_ctx.bindings[node_pattern.variable] = node

                # Handle node-relationship-node pattern: CREATE (a)-[r:KNOWS]->(b)
                elif len(pattern_parts) >= 3:
                    # First node
                    if isinstance(pattern_parts[0], NodePattern):
                        src_pattern = pattern_parts[0]
                        # Check if variable already bound (for connecting existing nodes)
                        if src_pattern.variable and src_pattern.variable in new_ctx.bindings:
                            src_node = new_ctx.bindings[src_pattern.variable]
                        else:
                            src_node = self._create_node_from_pattern(src_pattern, new_ctx)
                            if src_pattern.variable:
                                new_ctx.bindings[src_pattern.variable] = src_node

                    # Relationship and destination node
                    if len(pattern_parts) >= 3 and isinstance(pattern_parts[1], RelationshipPattern):
                        rel_pattern = pattern_parts[1]
                        dst_pattern = pattern_parts[2]

                        # Check if destination variable already bound
                        if dst_pattern.variable and dst_pattern.variable in new_ctx.bindings:
                            dst_node = new_ctx.bindings[dst_pattern.variable]
                        else:
                            dst_node = self._create_node_from_pattern(dst_pattern, new_ctx)
                            if dst_pattern.variable:
                                new_ctx.bindings[dst_pattern.variable] = dst_node

                        # Create relationship
                        rel_type = rel_pattern.types[0] if rel_pattern.types else "RELATED_TO"
                        edge = self._create_relationship_from_pattern(
                            src_node, dst_node, rel_type, rel_pattern, new_ctx
                        )
                        if rel_pattern.variable:
                            new_ctx.bindings[rel_pattern.variable] = edge

            result.append(new_ctx)

        return result

    def _create_node_from_pattern(self, node_pattern, ctx: ExecutionContext):
        """Create a node from a NodePattern.

        Args:
            node_pattern: NodePattern from AST
            ctx: Execution context for evaluating property expressions

        Returns:
            Created NodeRef
        """
        # Extract labels
        labels = list(node_pattern.labels) if node_pattern.labels else []

        # Extract and evaluate properties
        properties = {}
        if node_pattern.properties:
            for key, value_expr in node_pattern.properties.items():
                # Evaluate the expression to get the value
                cypher_value = evaluate_expression(value_expr, ctx, self)
                # Convert CypherValue to Python value (handles nested lists/maps)
                properties[key] = _cypher_to_python(cypher_value)

        # Create node using GraphForge API
        node = self.graphforge.create_node(labels, **properties)
        return node

    def _create_relationship_from_pattern(
        self, src_node, dst_node, rel_type, rel_pattern, ctx: ExecutionContext
    ):
        """Create a relationship from a RelationshipPattern.

        Args:
            src_node: Source NodeRef
            dst_node: Destination NodeRef
            rel_type: Relationship type string
            rel_pattern: RelationshipPattern from AST
            ctx: Execution context for evaluating property expressions

        Returns:
            Created EdgeRef
        """
        # Extract and evaluate properties
        properties = {}
        if hasattr(rel_pattern, "properties") and rel_pattern.properties:
            for key, value_expr in rel_pattern.properties.items():
                # Evaluate the expression to get the value
                cypher_value = evaluate_expression(value_expr, ctx, self)
                # Convert CypherValue to Python value (handles nested lists/maps)
                properties[key] = _cypher_to_python(cypher_value)

        # Create relationship using GraphForge API
        edge = self.graphforge.create_relationship(src_node, dst_node, rel_type, **properties)
        return edge

    def _execute_set(self, op: Set, input_rows: list[ExecutionContext]) -> list[ExecutionContext]:
        """Execute SET operator.

        Updates properties on nodes and relationships.

        Args:
            op: Set operator with property assignments
            input_rows: Input execution contexts

        Returns:
            Updated execution contexts
        """
        result = []

        for ctx in input_rows:
            self._execute_set_items(op.items, ctx)
            result.append(ctx)

        return result

    def _execute_remove(
        self, op: Remove, input_rows: list[ExecutionContext]
    ) -> list[ExecutionContext]:
        """Execute REMOVE operator.

        Removes properties from nodes/relationships or labels from nodes.

        Args:
            op: Remove operator with items to remove
            input_rows: Input execution contexts

        Returns:
            Updated execution contexts
        """
        from graphforge.types.graph import NodeRef

        result = []

        for ctx in input_rows:
            # Process each REMOVE item
            for item in op.items:
                var_name = item.variable
                name = item.name

                # Get the element from context
                if var_name in ctx.bindings:
                    element = ctx.bindings[var_name]

                    if item.item_type == "property":
                        # Remove property if it exists
                        if hasattr(element, "properties") and name in element.properties:
                            del element.properties[name]
                    elif item.item_type == "label":
                        # Remove label if it exists
                        # NodeRef is immutable, so we need to create a new one with updated labels
                        if hasattr(element, "labels") and name in element.labels:
                            # Create new labels set without the removed label
                            new_labels = set(element.labels)
                            new_labels.discard(name)

                            # Create new NodeRef with updated labels
                            new_node = NodeRef(
                                id=element.id,
                                labels=frozenset(new_labels),
                                properties=element.properties,
                            )

                            # Update the node in the graph
                            self.graph.add_node(new_node)

                            # Update the binding to reference the new node
                            ctx.bindings[var_name] = new_node

            result.append(ctx)

        return result

    def _execute_delete(
        self, op: Delete, input_rows: list[ExecutionContext]
    ) -> list[ExecutionContext]:
        """Execute DELETE operator.

        Removes nodes and relationships from the graph.

        Args:
            op: Delete operator with variables to delete
            input_rows: Input execution contexts

        Returns:
            Empty list (DELETE produces no output rows)

        Raises:
            ValueError: If trying to delete a node with relationships without DETACH
        """
        from graphforge.types.graph import EdgeRef, NodeRef

        for ctx in input_rows:
            for var_name in op.variables:
                if var_name in ctx.bindings:
                    element = ctx.bindings[var_name]

                    # Delete from graph
                    if isinstance(element, NodeRef):
                        # Get all edges connected to this node
                        outgoing = self.graph.get_outgoing_edges(element.id)
                        incoming = self.graph.get_incoming_edges(element.id)
                        all_edges = outgoing + incoming

                        # Check if node has relationships
                        if all_edges and not op.detach:
                            raise ValueError(
                                "Cannot delete node with relationships. "
                                "Use DETACH DELETE to delete relationships first."
                            )

                        # Remove all connected edges first (if DETACH)
                        if op.detach:
                            for edge in all_edges:
                                self.graph._edges.pop(edge.id, None)
                                # Remove from adjacency lists
                                if edge.src.id in self.graph._outgoing:
                                    self.graph._outgoing[edge.src.id] = [
                                        e
                                        for e in self.graph._outgoing[edge.src.id]
                                        if e.id != edge.id
                                    ]
                                if edge.dst.id in self.graph._incoming:
                                    self.graph._incoming[edge.dst.id] = [
                                        e
                                        for e in self.graph._incoming[edge.dst.id]
                                        if e.id != edge.id
                                    ]
                                # Remove from type index
                                if edge.type in self.graph._type_index:
                                    self.graph._type_index[edge.type].discard(edge.id)

                        # Remove node
                        self.graph._nodes.pop(element.id, None)
                        # Remove from label index
                        for label in element.labels:
                            if label in self.graph._label_index:
                                self.graph._label_index[label].discard(element.id)
                        # Remove adjacency lists
                        self.graph._outgoing.pop(element.id, None)
                        self.graph._incoming.pop(element.id, None)

                    elif isinstance(element, EdgeRef):
                        # Remove edge
                        self.graph._edges.pop(element.id, None)
                        # Remove from adjacency lists
                        if element.src.id in self.graph._outgoing:
                            self.graph._outgoing[element.src.id] = [
                                e
                                for e in self.graph._outgoing[element.src.id]
                                if e.id != element.id
                            ]
                        if element.dst.id in self.graph._incoming:
                            self.graph._incoming[element.dst.id] = [
                                e
                                for e in self.graph._incoming[element.dst.id]
                                if e.id != element.id
                            ]
                        # Remove from type index
                        if element.type in self.graph._type_index:
                            self.graph._type_index[element.type].discard(element.id)

        # DELETE produces no output rows
        return []

    def _execute_merge(
        self, op: Merge, input_rows: list[ExecutionContext]
    ) -> list[ExecutionContext]:
        """Execute MERGE operator with ON CREATE SET and ON MATCH SET support.

        Creates patterns if they don't exist, or matches them if they do.
        Conditionally executes SET operations based on whether elements were created or matched.

        Args:
            op: Merge operator with patterns, on_create, and on_match clauses
            input_rows: Input execution contexts

        Returns:
            Execution contexts with matched or created elements
        """
        if not self.graphforge:
            raise RuntimeError("MERGE requires GraphForge instance")

        from graphforge.ast.pattern import NodePattern

        result = []

        # Process each input row
        for ctx in input_rows:
            new_ctx = ExecutionContext()
            new_ctx.bindings = ctx.bindings.copy()

            # Track whether we created anything (for ON CREATE SET)
            was_created = False

            # Process each pattern
            for pattern in op.patterns:
                if not pattern:
                    continue

                # Extract pattern parts from new format (dict with path_variable and parts)
                # or use pattern directly if it's old format (list)
                if isinstance(pattern, dict) and "parts" in pattern:
                    path_var = pattern.get("path_variable")
                    pattern_parts = pattern["parts"]
                    # TODO: Phase 3 will use path_var to bind CypherPath objects
                else:
                    # Old format: pattern is already a list
                    pattern_parts = pattern
                    path_var = None

                # Handle simple node pattern: MERGE (n:Person {name: 'Alice'})
                if len(pattern_parts) == 1 and isinstance(pattern_parts[0], NodePattern):
                    node_pattern = pattern_parts[0]

                    # Try to find existing node
                    found_node = None

                    if node_pattern.labels:
                        # Get candidate nodes by first label
                        first_label = node_pattern.labels[0]
                        candidates = self.graph.get_nodes_by_label(first_label)

                        for node in candidates:
                            # Check if all required labels are present
                            if not all(label in node.labels for label in node_pattern.labels):
                                continue

                            # Check if properties match
                            if node_pattern.properties:
                                match = True
                                for key, value_expr in node_pattern.properties.items():
                                    expected_value = evaluate_expression(value_expr, new_ctx, self)
                                    if key not in node.properties:
                                        match = False
                                        break
                                    # Compare CypherValue objects using equality
                                    node_value = node.properties[key]
                                    comparison_result = node_value.equals(expected_value)
                                    if (
                                        isinstance(comparison_result, CypherBool)
                                        and not comparison_result.value
                                    ):
                                        match = False
                                        break

                                if match:
                                    # Found matching node
                                    found_node = node
                                    break
                            else:
                                # No properties specified, just match on labels
                                found_node = node
                                break

                    # Bind found node or create new one
                    if found_node:
                        was_created = False
                        if node_pattern.variable:
                            new_ctx.bindings[node_pattern.variable] = found_node
                    else:
                        was_created = True
                        node = self._create_node_from_pattern(node_pattern, new_ctx)
                        if node_pattern.variable:
                            new_ctx.bindings[node_pattern.variable] = node

            # Execute conditional SET operations
            if was_created and op.on_create:
                # Execute ON CREATE SET
                self._execute_set_items(op.on_create.items, new_ctx)
            elif not was_created and op.on_match:
                # Execute ON MATCH SET
                self._execute_set_items(op.on_match.items, new_ctx)

            result.append(new_ctx)

        return result

    def _execute_set_items(self, items: list, ctx: ExecutionContext) -> None:
        """Execute SET items on a context (helper for conditional SET).

        Args:
            items: List of (property_access, expression) tuples
            ctx: Execution context to update
        """
        for property_access, value_expr in items:
            # Evaluate the target (should be a PropertyAccess node)
            if hasattr(property_access, "variable") and hasattr(property_access, "property"):
                var_name = (
                    property_access.variable.name
                    if hasattr(property_access.variable, "name")
                    else property_access.variable
                )
                prop_name = property_access.property

                # Get the node or edge from context
                if var_name in ctx.bindings:
                    element = ctx.bindings[var_name]

                    # Evaluate the new value
                    new_value = evaluate_expression(value_expr, ctx, self)

                    # Update the property on the element
                    element.properties[prop_name] = new_value

    def _execute_unwind(
        self, op: Unwind, input_rows: list[ExecutionContext]
    ) -> list[ExecutionContext]:
        """Execute UNWIND operator.

        Expands a list into multiple rows, binding each element to a variable.

        Args:
            op: Unwind operator with expression and variable
            input_rows: Input execution contexts

        Returns:
            Expanded execution contexts (one per list element per input row)
        """
        result = []

        # If no input rows, start with one empty context
        if not input_rows:
            input_rows = [ExecutionContext()]

        for ctx in input_rows:
            # Evaluate the list expression
            value = evaluate_expression(op.expression, ctx, self)

            # Handle NULL - treated as empty list (produces no rows)
            if isinstance(value, CypherNull):
                continue

            # Handle CypherList
            if isinstance(value, CypherList):
                # Expand each list item into a new row
                for item in value.value:
                    new_ctx = ExecutionContext()
                    new_ctx.bindings = dict(ctx.bindings)
                    new_ctx.bind(op.variable, item)
                    result.append(new_ctx)
            else:
                # If not a list or NULL, wrap in a list
                new_ctx = ExecutionContext()
                new_ctx.bindings = dict(ctx.bindings)
                new_ctx.bind(op.variable, value)
                result.append(new_ctx)

        return result

    def _execute_optional_expand(
        self, op: OptionalExpandEdges, input_rows: list[ExecutionContext]
    ) -> list[ExecutionContext]:
        """Execute OptionalExpandEdges operator (left outer join).

        Like ExpandEdges, but preserves rows with NULL bindings when no matches found.
        This implements OPTIONAL MATCH semantics.

        Args:
            op: OptionalExpandEdges operator
            input_rows: Input execution contexts

        Returns:
            Execution contexts with expanded relationships or NULL bindings
        """
        from graphforge.types.graph import NodeRef

        result = []

        for ctx in input_rows:
            # Get source node
            if op.src_var not in ctx.bindings:
                # OPTIONAL MATCH: Source variable not bound - preserve row with NULL bindings
                new_ctx = ExecutionContext()
                new_ctx.bindings = dict(ctx.bindings)
                new_ctx.bind(op.dst_var, CypherNull())
                if op.edge_var:
                    new_ctx.bind(op.edge_var, CypherNull())
                result.append(new_ctx)
                continue

            src_node = ctx.get(op.src_var)
            if not isinstance(src_node, NodeRef):
                # OPTIONAL MATCH: Source is not a node - preserve row with NULL bindings
                new_ctx = ExecutionContext()
                new_ctx.bindings = dict(ctx.bindings)
                new_ctx.bind(op.dst_var, CypherNull())
                if op.edge_var:
                    new_ctx.bind(op.edge_var, CypherNull())
                result.append(new_ctx)
                continue

            # Get edges based on direction
            if op.direction == "OUT":
                edges = self.graph.get_outgoing_edges(src_node.id)
            elif op.direction == "IN":
                edges = self.graph.get_incoming_edges(src_node.id)
            else:  # UNDIRECTED
                edges = self.graph.get_outgoing_edges(src_node.id) + self.graph.get_incoming_edges(
                    src_node.id
                )

            # Filter by edge types if specified
            if op.edge_types:
                edges = [e for e in edges if e.type in op.edge_types]

            # LEFT JOIN behavior
            if not edges:
                # No edges found - preserve row with NULL bindings
                new_ctx = ExecutionContext()
                new_ctx.bindings = dict(ctx.bindings)
                new_ctx.bind(op.dst_var, CypherNull())
                if op.edge_var:
                    new_ctx.bind(op.edge_var, CypherNull())
                result.append(new_ctx)
            else:
                # INNER JOIN behavior - bind actual values
                for edge in edges:
                    new_ctx = ExecutionContext()
                    new_ctx.bindings = dict(ctx.bindings)

                    # Bind edge if variable specified
                    if op.edge_var:
                        new_ctx.bind(op.edge_var, edge)

                    # Determine destination node based on direction
                    if op.direction == "OUT":
                        dst_node = edge.dst
                    elif op.direction == "IN":
                        dst_node = edge.src
                    else:  # UNDIRECTED - check which end is the source
                        dst_node = edge.dst if edge.src.id == src_node.id else edge.src

                    new_ctx.bind(op.dst_var, dst_node)
                    result.append(new_ctx)

        return result

    def _execute_union(self, op: Union, input_rows: list[ExecutionContext]) -> list[Any]:
        """Execute Union operator.

        Combines results from multiple query branches. Each branch is executed
        independently and results are merged.

        Args:
            op: Union operator with branches
            input_rows: Input execution contexts (typically empty for UNION at query level)

        Returns:
            Combined results from all branches (list of dicts or ExecutionContexts)
        """
        all_results: list[Any] = []

        # Execute each branch independently
        for branch in op.branches:
            # Execute this branch's pipeline
            branch_results: list[Any] = input_rows if input_rows else [ExecutionContext()]
            for op_index, branch_op in enumerate(branch):
                branch_results = self._execute_operator(
                    branch_op, branch_results, op_index, len(branch)
                )
            all_results.extend(branch_results)

        # UNION (not UNION ALL) requires deduplication
        if not op.all:
            # Convert to hashable representations for deduplication
            seen: set[tuple[Any, ...]] = set()
            deduplicated: list[Any] = []
            for row in all_results:
                key: tuple[Any, ...]
                if isinstance(row, ExecutionContext):
                    # Hash based on bindings
                    key = tuple(
                        sorted((k, self._value_to_hashable(v)) for k, v in row.bindings.items())
                    )
                else:
                    # Dict result (from RETURN)
                    key = tuple(sorted((k, self._value_to_hashable(v)) for k, v in row.items()))

                if key not in seen:
                    seen.add(key)
                    deduplicated.append(row)
            return deduplicated

        return all_results

    def _execute_subquery(
        self, op: Subquery, input_rows: list[ExecutionContext]
    ) -> list[ExecutionContext]:
        """Execute Subquery operator.

        Executes a nested query pipeline for each input row, typically for
        EXISTS or COUNT subquery expressions.

        Args:
            op: Subquery operator with nested pipeline
            input_rows: Input execution contexts (outer query context)

        Returns:
            Input contexts unchanged (subquery results are evaluated in expression context)
        """
        # NOTE: This is a placeholder implementation.
        # In practice, subqueries are typically evaluated as part of expressions
        # (e.g., WHERE EXISTS {...}) rather than as standalone operators.
        # The actual evaluation logic should be in evaluator.py when processing
        # subquery expressions.

        # For now, just pass through input rows
        # Real implementation will be in evaluator.py when we add subquery expression support
        return input_rows
