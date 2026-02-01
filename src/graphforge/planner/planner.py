"""Query planner that converts AST to logical plans.

This module converts parsed AST into executable logical plans.
"""

from graphforge.ast.clause import (
    CreateClause,
    DeleteClause,
    LimitClause,
    MatchClause,
    MergeClause,
    OrderByClause,
    ReturnClause,
    SetClause,
    SkipClause,
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
    Project,
    ScanNodes,
    Set,
    Skip,
    Sort,
    With,
)


class QueryPlanner:
    """Plans query execution from AST."""

    def plan(self, ast: CypherQuery) -> list:
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
        create_clauses = []
        merge_clauses = []
        set_clause = None
        delete_clause = None
        where_clause = None
        return_clause = None
        order_by_clause = None
        skip_clause = None
        limit_clause = None

        for clause in clauses:
            if isinstance(clause, MatchClause):
                match_clauses.append(clause)
            elif isinstance(clause, CreateClause):
                create_clauses.append(clause)
            elif isinstance(clause, MergeClause):
                merge_clauses.append(clause)
            elif isinstance(clause, SetClause):
                set_clause = clause
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

        # 1. MATCH
        for match in match_clauses:
            operators.extend(self._plan_match(match))

        # 2. CREATE
        for create in create_clauses:
            operators.append(Create(patterns=create.patterns))

        # 3. MERGE
        for merge in merge_clauses:
            operators.append(Merge(patterns=merge.patterns))

        # 4. WHERE
        if where_clause:
            operators.append(Filter(predicate=where_clause.predicate))

        # 5. SET
        if set_clause:
            operators.append(Set(items=set_clause.items))

        # 6. DELETE
        if delete_clause:
            operators.append(Delete(variables=delete_clause.variables))

        # 7. ORDER BY (before projection!)
        if order_by_clause:
            # Pass return_items to Sort so it can resolve RETURN aliases
            return_items = return_clause.items if return_clause else None
            operators.append(Sort(items=order_by_clause.items, return_items=return_items))

        # 8. RETURN
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

        # 9. SKIP/LIMIT
        if skip_clause:
            operators.append(Skip(count=skip_clause.count))
        if limit_clause:
            operators.append(Limit(count=limit_clause.count))

        return operators

    def _plan_with_query(self, ast: CypherQuery) -> list:
        """Plan a query with WITH clauses.

        WITH acts as a pipeline boundary, so we plan each segment separately
        and connect them with WITH operators.

        Args:
            ast: Query AST with WITH clauses

        Returns:
            List of logical plan operators
        """
        operators = []

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
                # Convert WITH clause to With operator
                with_op = With(
                    items=segment.items,
                    predicate=segment.where.predicate if segment.where else None,
                    sort_items=segment.order_by.items if segment.order_by else None,
                    skip_count=segment.skip.count if segment.skip else None,
                    limit_count=segment.limit.count if segment.limit else None,
                )
                operators.append(with_op)
            elif isinstance(segment, list):
                # Plan the segment as a simple query
                operators.extend(self._plan_simple_query(segment))

        return operators

    def _plan_match(self, clause: MatchClause) -> list:
        """Plan MATCH clause into operators.

        Args:
            clause: MATCH clause from AST

        Returns:
            List of operators for the MATCH pattern
        """
        operators = []

        for pattern in clause.patterns:
            if not pattern:
                continue

            # Handle simple node pattern
            if len(pattern) == 1 and isinstance(pattern[0], NodePattern):
                node_pattern = pattern[0]
                operators.append(
                    ScanNodes(
                        variable=node_pattern.variable,  # type: ignore[arg-type]
                        labels=node_pattern.labels if node_pattern.labels else None,
                    )
                )

                # Add Filter for inline property predicates
                if node_pattern.properties:
                    predicate = self._properties_to_predicate(
                        node_pattern.variable,  # type: ignore[arg-type]
                        node_pattern.properties,
                    )
                    operators.append(Filter(predicate=predicate))  # type: ignore[arg-type]

            # Handle node-relationship-node pattern
            elif len(pattern) >= 3:
                # First node
                if isinstance(pattern[0], NodePattern):
                    src_pattern = pattern[0]
                    operators.append(
                        ScanNodes(
                            variable=src_pattern.variable,  # type: ignore[arg-type]
                            labels=src_pattern.labels if src_pattern.labels else None,
                        )
                    )

                    # Add Filter for inline property predicates on src node
                    if src_pattern.properties:
                        predicate = self._properties_to_predicate(
                            src_pattern.variable,  # type: ignore[arg-type]
                            src_pattern.properties,
                        )
                        operators.append(Filter(predicate=predicate))  # type: ignore[arg-type]

                # Relationship
                if isinstance(pattern[1], RelationshipPattern):
                    rel_pattern = pattern[1]
                    dst_pattern = pattern[2]

                    direction_map = {
                        Direction.OUT: "OUT",
                        Direction.IN: "IN",
                        Direction.UNDIRECTED: "UNDIRECTED",
                    }

                    operators.append(
                        ExpandEdges(
                            src_var=src_pattern.variable,  # type: ignore[arg-type]
                            edge_var=rel_pattern.variable,
                            dst_var=dst_pattern.variable,
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
            True if expression is or contains a FunctionCall
        """
        if isinstance(expr, FunctionCall):
            return True
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
