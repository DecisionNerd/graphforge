"""Query planner that converts AST to logical plans.

This module converts parsed AST into executable logical plans.
"""

from typing import Any

from graphforge.ast.clause import (
    CreateClause,
    DeleteClause,
    LimitClause,
    MatchClause,
    MergeClause,
    OptionalMatchClause,
    OrderByClause,
    RemoveClause,
    ReturnClause,
    SetClause,
    SkipClause,
    UnwindClause,
    WhereClause,
    WithClause,
)
from graphforge.ast.expression import FunctionCall
from graphforge.ast.pattern import Direction, NodePattern, RelationshipPattern
from graphforge.ast.query import CypherQuery
from graphforge.planner.operators import (
    Aggregate,
    Create,
    Delete,
    ExpandEdges,
    Filter,
    Limit,
    Merge,
    OptionalExpandEdges,
    Project,
    Remove,
    ScanNodes,
    Set,
    Skip,
    Sort,
    Unwind,
    With,
)
from graphforge.planner.types import VariableType


class QueryPlanner:
    """Plans query execution from AST."""

    def __init__(self):
        """Initialize the query planner."""
        from graphforge.planner.types import TypeContext

        self._anon_counter = 0
        self._type_context = TypeContext()

    def _generate_anonymous_variable(self) -> str:
        """Generate a unique variable name for anonymous patterns."""
        var = f"__anon_{self._anon_counter}"
        self._anon_counter += 1
        return var

    def plan(self, ast: CypherQuery) -> list[Any]:
        """Convert AST to logical plan operators.

        Operators are ordered for correct execution:
        1. MATCH (scan/expand)
        2. WHERE (filter)
        3. WITH (pipeline boundary) - optional
        4. ORDER BY (sort) - before projection to access all variables
        5. RETURN (project)
        6. SKIP/LIMIT

        Args:
            ast: Parsed query AST

        Returns:
            List of logical plan operators
        """
        from graphforge.planner.types import TypeContext

        # Reset type context for new query
        self._type_context = TypeContext()

        # Check if query contains WITH clauses
        has_with = any(isinstance(c, WithClause) for c in ast.clauses)

        if has_with:
            # Split query at WITH boundaries and plan each segment
            return self._plan_with_query(ast)
        # Use traditional single-pass planning
        return self._plan_simple_query(ast.clauses)

    def _plan_simple_query(self, clauses: list) -> list:
        """Plan a simple query without WITH clauses.

        Args:
            clauses: List of clause AST nodes

        Returns:
            List of logical plan operators
        """
        # Collect clauses by type
        match_clauses = []
        optional_match_clauses = []
        unwind_clauses = []
        create_clauses = []
        merge_clauses = []
        set_clause = None
        remove_clause = None
        delete_clause = None
        where_clause = None
        return_clause = None
        order_by_clause = None
        skip_clause = None
        limit_clause = None

        for clause in clauses:
            if isinstance(clause, MatchClause):
                match_clauses.append(clause)
            elif isinstance(clause, OptionalMatchClause):
                optional_match_clauses.append(clause)
            elif isinstance(clause, UnwindClause):
                unwind_clauses.append(clause)
            elif isinstance(clause, CreateClause):
                create_clauses.append(clause)
            elif isinstance(clause, MergeClause):
                merge_clauses.append(clause)
            elif isinstance(clause, SetClause):
                set_clause = clause
            elif isinstance(clause, RemoveClause):
                remove_clause = clause
            elif isinstance(clause, DeleteClause):
                delete_clause = clause
            elif isinstance(clause, WhereClause):
                where_clause = clause
            elif isinstance(clause, ReturnClause):
                return_clause = clause
            elif isinstance(clause, OrderByClause):
                order_by_clause = clause
            elif isinstance(clause, SkipClause):
                skip_clause = clause
            elif isinstance(clause, LimitClause):
                limit_clause = clause

        # Build operators in execution order
        operators = []

        # 1. Process reading clauses (MATCH, OPTIONAL MATCH, UNWIND) in order
        # This is important because UNWIND may depend on variables from MATCH, or vice versa
        for clause in clauses:
            if isinstance(clause, MatchClause):
                operators.extend(self._plan_match(clause))
            elif isinstance(clause, OptionalMatchClause):
                operators.extend(self._plan_optional_match(clause))
            elif isinstance(clause, UnwindClause):
                operators.append(Unwind(expression=clause.expression, variable=clause.variable))

        # 3. CREATE
        for create in create_clauses:
            # Validate and bind variable types from CREATE patterns
            self._validate_pattern_types(create.patterns)
            operators.append(Create(patterns=create.patterns))

        # 4. MERGE
        for merge in merge_clauses:
            # Validate and bind variable types from MERGE patterns
            self._validate_pattern_types(merge.patterns)
            operators.append(
                Merge(patterns=merge.patterns, on_create=merge.on_create, on_match=merge.on_match)
            )

        # 5. WHERE
        if where_clause:
            operators.append(Filter(predicate=where_clause.predicate))

        # 6. SET
        if set_clause:
            operators.append(Set(items=set_clause.items))

        # 7. REMOVE
        if remove_clause:
            operators.append(Remove(items=remove_clause.items))

        # 8. DELETE
        if delete_clause:
            operators.append(Delete(variables=delete_clause.variables, detach=delete_clause.detach))

        # 9. ORDER BY (before projection!)
        if order_by_clause:
            # Pass return_items to Sort so it can resolve RETURN aliases
            return_items = return_clause.items if return_clause else None
            operators.append(Sort(items=order_by_clause.items, return_items=return_items))

        # 10. RETURN
        if return_clause:
            # Check if RETURN contains aggregations
            has_aggregates = self._has_aggregations(return_clause)
            if has_aggregates:
                # Use Aggregate operator for grouping and aggregation
                grouping_exprs, agg_exprs = self._split_aggregates(return_clause)
                operators.append(
                    Aggregate(
                        grouping_exprs=grouping_exprs,
                        agg_exprs=agg_exprs,
                        return_items=return_clause.items,
                    )
                )
            else:
                # Use simple Project operator
                operators.append(Project(items=return_clause.items))

            # Add DISTINCT operator if needed
            if return_clause.distinct:
                from graphforge.planner.operators import Distinct

                operators.append(Distinct())

        # 11. SKIP/LIMIT
        if skip_clause:
            operators.append(Skip(count=skip_clause.count))
        if limit_clause:
            operators.append(Limit(count=limit_clause.count))

        return operators

    def _plan_with_query(self, ast: CypherQuery) -> list[Any]:
        """Plan a query with WITH clauses.

        WITH acts as a pipeline boundary, so we plan each segment separately
        and connect them with WITH operators.

        Args:
            ast: Query AST with WITH clauses

        Returns:
            List of logical plan operators
        """
        operators: list[Any] = []

        # Split clauses at WITH boundaries
        segments: list[list | WithClause] = []
        current_segment: list = []

        for clause in ast.clauses:
            if isinstance(clause, WithClause):
                # End current segment and start new one
                if current_segment:
                    segments.append(current_segment)
                    current_segment = []
                # Add WITH as its own segment marker
                segments.append(clause)
            else:
                current_segment.append(clause)

        # Add final segment
        if current_segment:
            segments.append(current_segment)

        # Plan each segment
        for segment in segments:
            if isinstance(segment, WithClause):
                # Validate WITH clause (Issue #172)
                self._validate_with_clause(segment)

                # Infer and register variable types from WITH expressions
                self._infer_with_types(segment)

                # Check if WITH contains aggregations
                has_aggregates = any(
                    self._contains_aggregate(item.expression) for item in segment.items
                )

                if has_aggregates:
                    # Split items into grouping and aggregation expressions
                    grouping_exprs = []
                    agg_exprs = []
                    for item in segment.items:
                        if self._contains_aggregate(item.expression):
                            agg_exprs.append(item.expression)
                        else:
                            grouping_exprs.append(item.expression)

                    # Create Aggregate operator
                    operators.append(
                        Aggregate(
                            grouping_exprs=grouping_exprs,
                            agg_exprs=agg_exprs,
                            return_items=segment.items,
                        )
                    )

                    # Add optional WHERE, ORDER BY, DISTINCT, SKIP, LIMIT after aggregation
                    # Order matters: DISTINCT before SKIP/LIMIT
                    if segment.where:
                        operators.append(Filter(predicate=segment.where.predicate))
                    if segment.order_by:
                        operators.append(
                            Sort(items=segment.order_by.items, return_items=segment.items)
                        )
                    # Add DISTINCT operator before SKIP/LIMIT (after ORDER BY)
                    if segment.distinct:
                        from graphforge.planner.operators import Distinct

                        operators.append(Distinct())
                    if segment.skip:
                        operators.append(Skip(count=segment.skip.count))
                    if segment.limit:
                        operators.append(Limit(count=segment.limit.count))
                else:
                    # No aggregations - use simple With operator
                    # When DISTINCT is used, SKIP/LIMIT must be applied after the
                    # separate Distinct operator, not in the With operator itself
                    pred = segment.where.predicate if segment.where else None
                    sort_items = segment.order_by.items if segment.order_by else None
                    skip_count = (
                        segment.skip.count if (segment.skip and not segment.distinct) else None
                    )
                    limit_count = (
                        segment.limit.count if (segment.limit and not segment.distinct) else None
                    )

                    with_op = With(
                        items=segment.items,
                        distinct=segment.distinct,
                        predicate=pred,
                        sort_items=sort_items,
                        skip_count=skip_count,
                        limit_count=limit_count,
                    )
                    operators.append(with_op)

                    # Add DISTINCT operator if needed (before SKIP/LIMIT)
                    if segment.distinct:
                        from graphforge.planner.operators import Distinct

                        operators.append(Distinct())
                        # Add SKIP/LIMIT after DISTINCT
                        if segment.skip:
                            operators.append(Skip(count=segment.skip.count))
                        if segment.limit:
                            operators.append(Limit(count=segment.limit.count))
            elif isinstance(segment, list):
                # Plan the segment as a simple query
                operators.extend(self._plan_simple_query(segment))

        return operators

    def _plan_match(self, clause: MatchClause) -> list[Any]:
        """Plan MATCH clause into operators.

        Args:
            clause: MATCH clause from AST

        Returns:
            List of operators for the MATCH pattern
        """
        operators: list[Any] = []

        for pattern in clause.patterns:
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

            # Handle simple node pattern
            if len(pattern_parts) == 1 and isinstance(pattern_parts[0], NodePattern):
                node_pattern = pattern_parts[0]
                var_name = node_pattern.variable or self._generate_anonymous_variable()

                # VALIDATE: Check if variable already bound to incompatible type
                self._type_context.validate_compatible(var_name, VariableType.NODE)

                # BIND: Register as node type
                self._type_context.bind_variable(var_name, VariableType.NODE)

                # Handle path variable if present
                if path_var:
                    self._type_context.validate_compatible(path_var, VariableType.PATH)
                    self._type_context.bind_variable(path_var, VariableType.PATH)

                operators.append(
                    ScanNodes(
                        variable=var_name,
                        labels=node_pattern.labels if node_pattern.labels else None,
                        path_var=path_var,
                    )
                )

                # Add Filter for inline property predicates
                if node_pattern.properties:
                    predicate = self._properties_to_predicate(
                        node_pattern.variable,  # type: ignore[arg-type]
                        node_pattern.properties,
                    )
                    operators.append(Filter(predicate=predicate))

            # Handle node-relationship-node pattern (single or multi-hop)
            elif len(pattern_parts) >= 3:
                # First node
                if isinstance(pattern_parts[0], NodePattern):
                    src_pattern = pattern_parts[0]
                    # Generate variable name for anonymous patterns
                    src_var = (
                        src_pattern.variable
                        if src_pattern.variable
                        else self._generate_anonymous_variable()
                    )

                    # VALIDATE: Check if variable already bound to incompatible type
                    self._type_context.validate_compatible(src_var, VariableType.NODE)

                    # BIND: Register as node type
                    self._type_context.bind_variable(src_var, VariableType.NODE)

                    operators.append(
                        ScanNodes(
                            variable=src_var,
                            labels=src_pattern.labels if src_pattern.labels else None,
                        )
                    )

                    # Add Filter for inline property predicates on src node
                    if src_pattern.properties:
                        predicate = self._properties_to_predicate(
                            src_var,
                            src_pattern.properties,
                        )
                        operators.append(Filter(predicate=predicate))

                # Determine number of hops
                # Pattern: node, rel, node, rel, node, ... (alternating)
                num_hops = (len(pattern_parts) - 1) // 2

                direction_map = {
                    Direction.OUT: "OUT",
                    Direction.IN: "IN",
                    Direction.UNDIRECTED: "UNDIRECTED",
                }

                # Check if any relationship is variable-length
                has_variable_length = any(
                    isinstance(pattern_parts[1 + (i * 2)], RelationshipPattern)
                    and (
                        pattern_parts[1 + (i * 2)].min_hops is not None
                        or pattern_parts[1 + (i * 2)].max_hops is not None
                    )
                    for i in range(num_hops)
                )

                # For multi-hop patterns with path binding and no variable-length:
                # Use ExpandMultiHop operator
                if num_hops > 1 and path_var and not has_variable_length:
                    from graphforge.planner.operators import ExpandMultiHop

                    # Collect all hops and filters
                    hops = []
                    filters = []
                    for hop_idx in range(num_hops):
                        rel_idx = 1 + (hop_idx * 2)
                        node_idx = rel_idx + 1

                        if rel_idx >= len(pattern_parts) or node_idx >= len(pattern_parts):
                            break

                        if not isinstance(pattern_parts[rel_idx], RelationshipPattern):
                            continue

                        rel_pattern = pattern_parts[rel_idx]
                        dst_pattern = pattern_parts[node_idx]

                        # Generate variable names
                        rel_var = (
                            rel_pattern.variable
                            if rel_pattern.variable
                            else None  # Anonymous relationship
                        )
                        dst_var = (
                            dst_pattern.variable
                            if dst_pattern.variable
                            else self._generate_anonymous_variable()
                        )

                        # VALIDATE and BIND types
                        if rel_var:
                            self._type_context.validate_compatible(
                                rel_var, VariableType.RELATIONSHIP
                            )
                            self._type_context.bind_variable(rel_var, VariableType.RELATIONSHIP)

                        self._type_context.validate_compatible(dst_var, VariableType.NODE)
                        self._type_context.bind_variable(dst_var, VariableType.NODE)

                        hops.append(
                            (
                                rel_var,
                                rel_pattern.types if rel_pattern.types else [],
                                direction_map[rel_pattern.direction],
                                dst_var,
                            )
                        )

                        # Collect Filter for inline property predicates on dst node
                        # (to be added AFTER ExpandMultiHop binds the variables)
                        if dst_pattern.properties:
                            predicate = self._properties_to_predicate(
                                dst_var,
                                dst_pattern.properties,
                            )
                            filters.append(Filter(predicate=predicate))

                    # Handle path variable if present
                    if path_var:
                        self._type_context.validate_compatible(path_var, VariableType.PATH)
                        self._type_context.bind_variable(path_var, VariableType.PATH)

                    # Add ExpandMultiHop operator first
                    operators.append(
                        ExpandMultiHop(
                            src_var=src_var,
                            hops=hops,
                            path_var=path_var,
                        )
                    )

                    # Then add filters (now that variables are bound)
                    operators.extend(filters)
                else:
                    # Single hop OR multi-hop without path binding OR has variable-length:
                    # Use individual ExpandEdges/ExpandVariableLength operators
                    prev_dst_var = src_var  # Initialize for multi-hop chaining
                    for hop_idx in range(num_hops):
                        rel_idx = 1 + (hop_idx * 2)
                        node_idx = rel_idx + 1

                        if rel_idx >= len(pattern_parts) or node_idx >= len(pattern_parts):
                            break

                        if not isinstance(pattern_parts[rel_idx], RelationshipPattern):
                            continue

                        rel_pattern = pattern_parts[rel_idx]
                        dst_pattern = pattern_parts[node_idx]

                        # Source is previous destination (or first src_var for first hop)
                        if hop_idx == 0:
                            current_src_var = src_var
                        else:
                            current_src_var = prev_dst_var

                        # Generate variable names for anonymous patterns
                        rel_var = (
                            rel_pattern.variable
                            if rel_pattern.variable
                            else None
                            if num_hops > 1
                            else self._generate_anonymous_variable()
                        )
                        dst_var = (
                            dst_pattern.variable
                            if dst_pattern.variable
                            else self._generate_anonymous_variable()
                        )

                        # VALIDATE and BIND types
                        if rel_var:
                            self._type_context.validate_compatible(
                                rel_var, VariableType.RELATIONSHIP
                            )
                            self._type_context.bind_variable(rel_var, VariableType.RELATIONSHIP)

                        self._type_context.validate_compatible(dst_var, VariableType.NODE)
                        self._type_context.bind_variable(dst_var, VariableType.NODE)

                        # For single-hop patterns with path binding:
                        # Set path_var on the (only) hop
                        is_single_hop = num_hops == 1
                        hop_path_var = path_var if is_single_hop else None

                        # Handle path variable if present on this hop
                        if hop_path_var:
                            self._type_context.validate_compatible(hop_path_var, VariableType.PATH)
                            self._type_context.bind_variable(hop_path_var, VariableType.PATH)

                        # Check if this is a variable-length pattern
                        if rel_pattern.min_hops is not None or rel_pattern.max_hops is not None:
                            # Variable-length expansion
                            from graphforge.planner.operators import ExpandVariableLength

                            operators.append(
                                ExpandVariableLength(
                                    src_var=current_src_var,
                                    edge_var=rel_var,
                                    dst_var=dst_var,
                                    path_var=hop_path_var,
                                    edge_types=rel_pattern.types if rel_pattern.types else [],
                                    direction=direction_map[rel_pattern.direction],
                                    min_hops=rel_pattern.min_hops
                                    if rel_pattern.min_hops is not None
                                    else 1,
                                    max_hops=rel_pattern.max_hops,
                                    predicate=rel_pattern.predicate,
                                )
                            )
                        else:
                            # Single-hop expansion
                            operators.append(
                                ExpandEdges(
                                    src_var=current_src_var,
                                    edge_var=rel_var,
                                    dst_var=dst_var,
                                    path_var=hop_path_var,
                                    edge_types=rel_pattern.types if rel_pattern.types else [],
                                    direction=direction_map[rel_pattern.direction],
                                    predicate=rel_pattern.predicate,
                                )
                            )

                        # Add Filter for inline property predicates on dst node
                        if dst_pattern.properties:
                            predicate = self._properties_to_predicate(
                                dst_var,
                                dst_pattern.properties,
                            )
                            operators.append(Filter(predicate=predicate))

                        # Track destination for next hop
                        prev_dst_var = dst_var

        return operators

    def _plan_optional_match(self, clause: OptionalMatchClause) -> list[Any]:
        """Plan OPTIONAL MATCH clause into operators.

        Similar to _plan_match, but uses OptionalExpandEdges for left outer join semantics.

        Args:
            clause: OPTIONAL MATCH clause from AST

        Returns:
            List of operators for the OPTIONAL MATCH pattern
        """
        operators: list[Any] = []

        for pattern in clause.patterns:
            if not pattern:
                continue

            # Extract pattern parts from new format (dict with path_variable and parts)
            # or use pattern directly if it's old format (list)
            if isinstance(pattern, dict) and "parts" in pattern:
                path_var = pattern.get("path_variable")
                pattern_parts = pattern["parts"]
            else:
                # Old format: pattern is already a list
                path_var = None
                pattern_parts = pattern

            # Handle simple node pattern
            if len(pattern_parts) == 1 and isinstance(pattern_parts[0], NodePattern):
                # OPTIONAL MATCH on a single node uses OptionalScanNodes
                # to preserve rows with NULL bindings when no match found
                from graphforge.planner.operators import OptionalScanNodes

                node_pattern = pattern_parts[0]
                operators.append(
                    OptionalScanNodes(
                        variable=node_pattern.variable,  # type: ignore[arg-type]
                        labels=node_pattern.labels if node_pattern.labels else None,
                        path_var=path_var,
                    )
                )

                # Add Filter for inline property predicates
                if node_pattern.properties:
                    predicate = self._properties_to_predicate(
                        node_pattern.variable,  # type: ignore[arg-type]
                        node_pattern.properties,
                    )
                    operators.append(Filter(predicate=predicate))

            # Handle node-relationship-node pattern
            elif len(pattern_parts) >= 3:
                # First node
                if isinstance(pattern_parts[0], NodePattern):
                    src_pattern = pattern_parts[0]
                    # Generate variable name for anonymous patterns
                    src_var = (
                        src_pattern.variable
                        if src_pattern.variable
                        else self._generate_anonymous_variable()
                    )
                    operators.append(
                        ScanNodes(
                            variable=src_var,
                            labels=src_pattern.labels if src_pattern.labels else None,
                        )
                    )

                    # Add Filter for inline property predicates on src node
                    if src_pattern.properties:
                        predicate = self._properties_to_predicate(
                            src_var,
                            src_pattern.properties,
                        )
                        operators.append(Filter(predicate=predicate))

                # Relationship - use OptionalExpandEdges instead of ExpandEdges
                if isinstance(pattern_parts[1], RelationshipPattern):
                    rel_pattern = pattern_parts[1]
                    dst_pattern = pattern_parts[2]

                    # Generate variable names for anonymous patterns
                    rel_var = (
                        rel_pattern.variable
                        if rel_pattern.variable
                        else None  # Anonymous relationship variable
                    )
                    dst_var = (
                        dst_pattern.variable
                        if dst_pattern.variable
                        else self._generate_anonymous_variable()
                    )

                    direction_map = {
                        Direction.OUT: "OUT",
                        Direction.IN: "IN",
                        Direction.UNDIRECTED: "UNDIRECTED",
                    }

                    operators.append(
                        OptionalExpandEdges(
                            src_var=src_var,
                            edge_var=rel_var,
                            dst_var=dst_var,
                            edge_types=rel_pattern.types if rel_pattern.types else [],
                            direction=direction_map[rel_pattern.direction],
                        )
                    )

        return operators

    def _properties_to_predicate(self, variable: str, properties: dict):
        """Convert inline property predicates to a WHERE predicate.

        Args:
            variable: Variable name to check properties on
            properties: Dict of property_name -> Expression

        Returns:
            BinaryOp predicate combining all property checks with AND
        """
        from graphforge.ast.expression import BinaryOp, PropertyAccess

        if not properties:
            return None

        predicates = []
        for prop_name, prop_value in properties.items():
            # Create: variable.property = value
            left = PropertyAccess(variable=variable, property=prop_name)
            predicate = BinaryOp(op="=", left=left, right=prop_value)
            predicates.append(predicate)

        # Combine with AND if multiple properties
        if len(predicates) == 1:
            return predicates[0]

        result = predicates[0]
        for pred in predicates[1:]:
            result = BinaryOp(op="AND", left=result, right=pred)

        return result

    def _validate_with_clause(self, with_clause: WithClause) -> None:
        """Validate WITH clause for compile-time errors (Issue #172).

        Checks for:
        1. Duplicate aliases (ColumnNameConflict)
        2. Unaliased expressions that aren't simple variables (NoExpressionAlias)

        Args:
            with_clause: WITH clause to validate

        Raises:
            SyntaxError: If validation fails
        """
        from graphforge.ast.expression import Variable, Wildcard

        # Check for duplicate aliases
        seen_aliases = set()
        for item in with_clause.items:
            # Get the alias (explicit or implicit)
            alias = (
                item.alias
                if item.alias
                else (item.expression.name if isinstance(item.expression, Variable) else None)
            )

            if alias:
                if alias in seen_aliases:
                    raise SyntaxError(
                        f"ColumnNameConflict: Multiple result columns with the same "
                        f"name '{alias}' are not supported"
                    )
                seen_aliases.add(alias)

        # Check for unaliased expressions (only Variables and Wildcard can be unaliased)
        for item in with_clause.items:
            if not item.alias and not isinstance(item.expression, (Variable, Wildcard)):
                raise SyntaxError(
                    "NoExpressionAlias: All non-variable expressions in WITH must be aliased"
                )

    def _infer_with_types(self, with_clause: WithClause) -> None:
        """Infer and register variable types from WITH clause expressions.

        Args:
            with_clause: WITH clause to analyze
        """
        from graphforge.ast.expression import Variable

        for item in with_clause.items:
            # Get the alias (explicit or implicit from Variable)
            alias = (
                item.alias
                if item.alias
                else (item.expression.name if isinstance(item.expression, Variable) else None)
            )

            if not alias:
                continue

            # Infer type from expression
            expr_type = self._infer_expression_type(item.expression)

            # Register the variable type
            self._type_context.bind_variable(alias, expr_type)

    def _infer_expression_type(self, expr: Any) -> "VariableType":
        """Infer the type of an expression.

        Args:
            expr: Expression to analyze

        Returns:
            VariableType for the expression
        """
        from graphforge.ast.expression import FunctionCall, Literal, PropertyAccess, Variable

        if isinstance(expr, Literal):
            # All literal values are scalar types
            return VariableType.SCALAR

        elif isinstance(expr, Variable):
            # Look up the variable's type
            return self._type_context.get_type(expr.name)

        elif isinstance(expr, PropertyAccess):
            # Property access on any type returns scalar
            return VariableType.SCALAR

        elif isinstance(expr, FunctionCall):
            # Function calls return scalars
            # (Special cases like nodes() or relationships() are rare)
            return VariableType.SCALAR

        else:
            # Default to SCALAR for other expression types
            return VariableType.SCALAR

    def _validate_pattern_types(self, patterns: list[Any]) -> None:
        """Validate and bind variable types from CREATE/MERGE patterns.

        Args:
            patterns: List of patterns to validate
        """
        from graphforge.ast.pattern import NodePattern, RelationshipPattern

        for pattern in patterns:
            # Get pattern parts - patterns can be dicts or objects with parts/elements
            parts = None
            path_var = None

            if isinstance(pattern, dict):
                parts = pattern.get("parts", pattern.get("elements", []))
                path_var = pattern.get("path_variable")
            elif hasattr(pattern, "parts"):
                parts = pattern.parts
                path_var = getattr(pattern, "path_variable", None)
            elif hasattr(pattern, "elements"):
                parts = pattern.elements
                path_var = getattr(pattern, "path_variable", None)

            # Validate each part (node or relationship)
            if parts:
                for part in parts:
                    if isinstance(part, NodePattern):
                        if part.variable:
                            # VALIDATE: Check if variable already bound to incompatible type
                            self._type_context.validate_compatible(part.variable, VariableType.NODE)
                            # BIND: Register as node type
                            self._type_context.bind_variable(part.variable, VariableType.NODE)

                    elif isinstance(part, RelationshipPattern):
                        if part.variable:
                            # VALIDATE: Check if variable already bound to incompatible type
                            self._type_context.validate_compatible(
                                part.variable, VariableType.RELATIONSHIP
                            )
                            # BIND: Register as relationship type
                            self._type_context.bind_variable(
                                part.variable, VariableType.RELATIONSHIP
                            )

            # Handle path variable if present
            if path_var:
                # VALIDATE: Check if variable already bound to incompatible type
                self._type_context.validate_compatible(path_var, VariableType.PATH)
                # BIND: Register as path type
                self._type_context.bind_variable(path_var, VariableType.PATH)

    def _has_aggregations(self, return_clause: ReturnClause) -> bool:
        """Check if RETURN clause contains any aggregation functions.

        Args:
            return_clause: RETURN clause to check

        Returns:
            True if any ReturnItem contains a FunctionCall
        """
        for item in return_clause.items:
            if self._contains_aggregate(item.expression):
                return True
        return False

    def _contains_aggregate(self, expr) -> bool:
        """Recursively check if an expression contains aggregation functions.

        Args:
            expr: Expression to check

        Returns:
            True if expression is or contains an aggregation FunctionCall
        """
        # Define aggregation functions
        aggregation_functions = {
            "COUNT",
            "SUM",
            "AVG",
            "MIN",
            "MAX",
            "COLLECT",
            "PERCENTILEDISC",
            "PERCENTILECONT",
            "STDEV",
            "STDEVP",
        }

        if isinstance(expr, FunctionCall):
            # Only return True if it's an aggregation function
            return expr.name.upper() in aggregation_functions
        # Could add recursive checking for complex expressions in the future
        return False

    def _split_aggregates(self, return_clause: ReturnClause) -> tuple[list, list]:
        """Split RETURN items into grouping expressions and aggregates.

        Args:
            return_clause: RETURN clause to split

        Returns:
            Tuple of (grouping_expressions, aggregate_expressions)
        """
        grouping_exprs = []
        agg_exprs = []

        for item in return_clause.items:
            if self._contains_aggregate(item.expression):
                agg_exprs.append(item.expression)
            else:
                grouping_exprs.append(item.expression)

        return grouping_exprs, agg_exprs
