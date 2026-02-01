"""Query executor that executes logical plans.

This module implements the execution engine that runs logical plan operators
against a graph store.
"""

from typing import Any

from graphforge.ast.expression import FunctionCall
from graphforge.executor.evaluator import ExecutionContext, evaluate_expression
from graphforge.planner.operators import (
    Aggregate,
    Create,
    Delete,
    ExpandEdges,
    Filter,
    Limit,
    Merge,
    Project,
    ScanNodes,
    Set,
    Skip,
    Sort,
    With,
)
from graphforge.storage.memory import Graph
from graphforge.types.values import CypherBool, CypherFloat, CypherInt, CypherNull


class QueryExecutor:
    """Executes logical query plans against a graph.

    The executor processes a pipeline of operators, streaming rows through
    each stage of the query.
    """

    def __init__(self, graph: Graph, graphforge=None):
        """Initialize executor with a graph.

        Args:
            graph: The graph to query
            graphforge: Optional GraphForge instance for CREATE operations
        """
        self.graph = graph
        self.graphforge = graphforge

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

        # If there's no Project or Aggregate operator in the pipeline (no RETURN clause),
        # return empty results (Cypher semantics: queries without RETURN produce no output)
        if operators and not any(isinstance(op, (Project, Aggregate)) for op in operators):
            return []

        # At this point, rows has been converted to list[dict] by Project/Aggregate operator
        return rows  # type: ignore[return-value]

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
            return self._execute_project(op, input_rows)  # type: ignore[return-value]

        if isinstance(op, Limit):
            return self._execute_limit(op, input_rows)

        if isinstance(op, Skip):
            return self._execute_skip(op, input_rows)

        if isinstance(op, Sort):
            return self._execute_sort(op, input_rows)

        if isinstance(op, Aggregate):
            return self._execute_aggregate(op, input_rows)  # type: ignore[return-value]

        if isinstance(op, Create):
            return self._execute_create(op, input_rows)

        if isinstance(op, Set):
            return self._execute_set(op, input_rows)

        if isinstance(op, Delete):
            return self._execute_delete(op, input_rows)

        if isinstance(op, Merge):
            return self._execute_merge(op, input_rows)

        if isinstance(op, With):
            return self._execute_with(op, input_rows)

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

    def _execute_filter(
        self, op: Filter, input_rows: list[ExecutionContext]
    ) -> list[ExecutionContext]:
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

                # Determine column name
                if return_item.alias:
                    # Explicit alias provided - use it
                    key = return_item.alias
                else:
                    # No alias - use default column naming (col_0, col_1, etc.)
                    # This applies to all expressions, including simple variables
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
                value = evaluate_expression(return_item.expression, ctx)

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
                value = evaluate_expression(op.predicate, ctx)
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
                    val1 = evaluate_expression(sort_item.expression, ctx1)
                    val2 = evaluate_expression(sort_item.expression, ctx2)
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
            groups = {(): input_rows}  # type: ignore[assignment]

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
        if hasattr(value, "value"):
            # CypherString, etc.
            return (type(value).__name__, value.value)
        # NodeRef, EdgeRef have their own hash
        return value

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
                        if hashable_val is None:
                            row[key] = CypherNull()
                        elif isinstance(hashable_val, tuple) and len(hashable_val) == 2:
                            type_name, val = hashable_val
                            if type_name == "CypherInt":
                                row[key] = CypherInt(val)
                            elif type_name == "CypherFloat":
                                row[key] = CypherFloat(val)
                            elif type_name == "CypherBool":
                                from graphforge.types.values import CypherBool

                                row[key] = CypherBool(val)
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
            seen: set[Any] | None = set() if func_call.distinct else None

            for ctx in group_rows:
                value = evaluate_expression(func_call.args[0], ctx)
                if not isinstance(value, CypherNull):
                    if func_call.distinct and seen is not None:
                        hashable = self._value_to_hashable(value)
                        if hashable not in seen:
                            seen.add(hashable)
                            count += 1
                    else:
                        count += 1

            return CypherInt(count)

        # SUM, AVG, MIN, MAX require evaluating the expression
        values: list[Any] = []
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

                # Handle simple node pattern: CREATE (n:Person {name: 'Alice'})
                if len(pattern) == 1 and isinstance(pattern[0], NodePattern):
                    node_pattern = pattern[0]
                    node = self._create_node_from_pattern(node_pattern, new_ctx)
                    if node_pattern.variable:
                        new_ctx.bindings[node_pattern.variable] = node

                # Handle node-relationship-node pattern: CREATE (a)-[r:KNOWS]->(b)
                elif len(pattern) >= 3:
                    # First node
                    if isinstance(pattern[0], NodePattern):
                        src_pattern = pattern[0]
                        # Check if variable already bound (for connecting existing nodes)
                        if src_pattern.variable and src_pattern.variable in new_ctx.bindings:
                            src_node = new_ctx.bindings[src_pattern.variable]
                        else:
                            src_node = self._create_node_from_pattern(src_pattern, new_ctx)
                            if src_pattern.variable:
                                new_ctx.bindings[src_pattern.variable] = src_node

                    # Relationship and destination node
                    if len(pattern) >= 3 and isinstance(pattern[1], RelationshipPattern):
                        rel_pattern = pattern[1]
                        dst_pattern = pattern[2]

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
                cypher_value = evaluate_expression(value_expr, ctx)
                properties[key] = cypher_value.value

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
                cypher_value = evaluate_expression(value_expr, ctx)
                properties[key] = cypher_value.value

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
            # Process each SET item
            for property_access, value_expr in op.items:
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
                        new_value = evaluate_expression(value_expr, ctx)

                        # Update the property on the element
                        # Note: This modifies the element in place in the graph
                        element.properties[prop_name] = new_value

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
        """
        from graphforge.types.graph import EdgeRef, NodeRef

        for ctx in input_rows:
            for var_name in op.variables:
                if var_name in ctx.bindings:
                    element = ctx.bindings[var_name]

                    # Delete from graph
                    if isinstance(element, NodeRef):
                        # Remove node (need to remove edges first)
                        # Get all edges connected to this node
                        outgoing = self.graph.get_outgoing_edges(element.id)
                        incoming = self.graph.get_incoming_edges(element.id)

                        # Remove all connected edges first
                        for edge in outgoing + incoming:
                            self.graph._edges.pop(edge.id, None)
                            # Remove from adjacency lists
                            if edge.src.id in self.graph._outgoing:
                                self.graph._outgoing[edge.src.id] = [
                                    e for e in self.graph._outgoing[edge.src.id] if e.id != edge.id
                                ]
                            if edge.dst.id in self.graph._incoming:
                                self.graph._incoming[edge.dst.id] = [
                                    e for e in self.graph._incoming[edge.dst.id] if e.id != edge.id
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
        """Execute MERGE operator.

        Creates patterns if they don't exist, or matches them if they do.

        Args:
            op: Merge operator with patterns
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

            # Process each pattern
            for pattern in op.patterns:
                if not pattern:
                    continue

                # Handle simple node pattern: MERGE (n:Person {name: 'Alice'})
                if len(pattern) == 1 and isinstance(pattern[0], NodePattern):
                    node_pattern = pattern[0]

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
                                    expected_value = evaluate_expression(value_expr, new_ctx)
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
                        if node_pattern.variable:
                            new_ctx.bindings[node_pattern.variable] = found_node
                    else:
                        node = self._create_node_from_pattern(node_pattern, new_ctx)
                        if node_pattern.variable:
                            new_ctx.bindings[node_pattern.variable] = node

            result.append(new_ctx)

        return result
