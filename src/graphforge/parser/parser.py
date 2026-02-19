"""openCypher parser for GraphForge.

This module provides the main parser interface that converts openCypher query
strings into AST representations using Lark and custom transformers.
"""

from pathlib import Path

from lark import Lark, Token, Transformer

from graphforge.ast.clause import (
    CreateClause,
    DeleteClause,
    LimitClause,
    MatchClause,
    MergeClause,
    OptionalMatchClause,
    OrderByClause,
    OrderByItem,
    RemoveClause,
    RemoveItem,
    ReturnClause,
    ReturnItem,
    SetClause,
    SkipClause,
    UnwindClause,
    WhereClause,
    WithClause,
)
from graphforge.ast.expression import (
    BinaryOp,
    CaseExpression,
    FunctionCall,
    Literal,
    PropertyAccess,
    Subscript,
    UnaryOp,
    Variable,
    Wildcard,
)
from graphforge.ast.pattern import Direction, NodePattern, RelationshipPattern
from graphforge.ast.query import CypherQuery


class ASTTransformer(Transformer):
    """Transforms Lark parse tree into GraphForge AST."""

    def _get_token_value(self, item):
        """Extract string value from Token or string."""
        if isinstance(item, Token):
            return str(item.value)
        return str(item)

    # Query
    def query(self, items):
        """Transform query rule."""
        # Items can be single_part_query, multi_part_query, or union_query
        return items[0]

    def union_query(self, items):
        """Transform UNION query.

        Returns a UnionQuery AST node with branches and union type.
        Validates that all UNION clauses are consistent (all UNION or all UNION ALL).
        """
        from graphforge.ast.query import UnionQuery

        # items structure: [query1, union_clause, query2, union_clause, query3, ...]
        # union_clause is either "UNION" or "UNION ALL"
        branches = []
        union_types = []

        i = 0
        while i < len(items):
            if isinstance(items[i], str):
                # This is a union clause indicator
                union_types.append(items[i])
                i += 1
            else:
                # This is a query (CypherQuery object)
                branches.append(items[i])
                i += 1

        # Validate consistency: all UNION or all UNION ALL
        if union_types:
            first_type = union_types[0]
            if not all(ut == first_type for ut in union_types):
                raise ValueError(
                    "Mixed UNION and UNION ALL in same query. "
                    "Use either UNION or UNION ALL consistently."
                )
            union_all = first_type == "UNION ALL"
        else:
            union_all = False

        return UnionQuery(branches=branches, all=union_all)

    def union_distinct(self, items):
        """Transform UNION (without ALL)."""
        return "UNION"

    def union_all(self, items):
        """Transform UNION ALL."""
        return "UNION ALL"

    def single_part_query(self, items):
        """Transform single-part query (without WITH)."""
        # Items already contain a CypherQuery from read_query, write_query, or update_query
        return items[0]

    def multi_part_query(self, items):
        """Transform multi-part query (with WITH clauses).

        Structure: reading_or_writing_clauses+ with_clause+ final_query_part
        Each reading_or_writing_clauses is a list of clauses (MATCH, WHERE, CREATE, MERGE)
        Each with_clause is a WithClause
        final_query_part is a CypherQuery
        """
        # Flatten all clauses from reading/writing clauses, with clauses, and final query
        all_clauses = []

        for item in items:
            if isinstance(item, list):
                # reading_or_writing_clauses returns a list of clauses
                all_clauses.extend(item)
            elif isinstance(item, WithClause):
                # with_clause returns a single WithClause
                all_clauses.append(item)
            elif isinstance(item, CypherQuery):
                # final_query_part returns a CypherQuery
                all_clauses.extend(item.clauses)

        return CypherQuery(clauses=all_clauses)

    def with_query(self, items):
        """Transform query starting with WITH clause (Issue #172).

        Structure: with_clause+ final_query_part
        Each with_clause is a WithClause
        final_query_part is a CypherQuery
        """
        # Flatten all WITH clauses and final query
        all_clauses = []

        for item in items:
            if isinstance(item, WithClause):
                # with_clause returns a single WithClause
                all_clauses.append(item)
            elif isinstance(item, CypherQuery):
                # final_query_part returns a CypherQuery
                all_clauses.extend(item.clauses)

        return CypherQuery(clauses=all_clauses)

    def reading_clause(self, items):
        """Transform reading clause (MATCH/UNWIND with optional WHERE).

        Returns a list of clauses for easier flattening in multi_part_query.
        """
        return list(items)

    def writing_clause(self, items):
        """Transform writing clause (CREATE/MERGE).

        Returns the clause directly (single clause, no WHERE allowed).
        """
        return items[0]

    def reading_or_writing_clauses(self, items):
        """Transform reading or writing clauses for multi_part_query.

        Returns a list of clauses for flattening.
        """
        # reading_clause returns a list, writing_clause returns a single clause
        if isinstance(items[0], list):
            return items[0]
        else:
            return [items[0]]

    def final_query_part(self, items):
        """Transform final part of multi-part query.

        Can be a read_query, return_only_query, write_query, or update_query.
        """
        return items[0]

    def return_only_query(self, items):
        """Transform return-only query (RETURN without MATCH).

        This is allowed after WITH clauses.
        """
        return CypherQuery(clauses=list(items))

    def read_query(self, items):
        """Transform read query (MATCH with optional clauses)."""
        return CypherQuery(clauses=list(items))

    def write_query(self, items):
        """Transform write query (CREATE/MERGE with optional RETURN)."""
        return CypherQuery(clauses=list(items))

    def update_query(self, items):
        """Transform update query (MATCH with SET/DELETE)."""
        return CypherQuery(clauses=list(items))

    def unwind_query(self, items):
        """Transform unwind query (UNWIND with optional clauses)."""
        return CypherQuery(clauses=list(items))

    def call_query(self, items):
        """Transform call query (CALL with optional clauses)."""
        return CypherQuery(clauses=list(items))

    def reading_only_query(self, items):
        """Transform reading-only query (multiple reading clauses + RETURN)."""
        # Flatten reading_clause lists
        flat_clauses = []
        for item in items:
            if isinstance(item, list):
                flat_clauses.extend(item)
            else:
                flat_clauses.append(item)
        return CypherQuery(clauses=flat_clauses)

    # Clauses
    def match_clause(self, items):
        """Transform MATCH clause."""
        patterns = [item for item in items if not isinstance(item, str)]
        return MatchClause(patterns=patterns)

    def optional_match_clause(self, items):
        """Transform OPTIONAL MATCH clause."""
        patterns = [item for item in items if not isinstance(item, str)]
        return OptionalMatchClause(patterns=patterns)

    def create_clause(self, items):
        """Transform CREATE clause."""
        patterns = [item for item in items if not isinstance(item, str)]
        return CreateClause(patterns=patterns)

    def set_clause(self, items):
        """Transform SET clause."""
        return SetClause(items=list(items))

    def set_item(self, items):
        """Transform SET item (property = expression)."""
        property_access = items[0]
        expression = items[1]
        return (property_access, expression)

    def remove_clause(self, items):
        """Transform REMOVE clause."""
        return RemoveClause(items=list(items))

    def remove_property(self, items):
        """Transform REMOVE property item (e.g., n.age)."""
        property_access = items[0]
        return RemoveItem(
            item_type="property",
            variable=property_access.variable,
            name=property_access.property,
        )

    def remove_label(self, items):
        """Transform REMOVE label item (e.g., n:Person)."""
        variable = items[0]
        label = items[1]
        return RemoveItem(
            item_type="label",
            variable=variable.name,
            name=label,
        )

    def detach_delete(self, items):
        """Transform DETACH DELETE clause."""
        # Items are Variable nodes from the grammar
        variables = [item.name for item in items if isinstance(item, Variable)]
        return DeleteClause(variables=variables, detach=True)

    def regular_delete(self, items):
        """Transform regular DELETE clause (without DETACH)."""
        # Items are Variable nodes from the grammar
        variables = [item.name for item in items if isinstance(item, Variable)]
        return DeleteClause(variables=variables, detach=False)

    def merge_clause(self, items):
        """Transform MERGE clause with optional ON CREATE/ON MATCH actions."""
        patterns = []
        on_create = None
        on_match = None

        for item in items:
            if isinstance(item, str):
                continue
            if isinstance(item, tuple) and len(item) == 2:
                # merge_action returns (action_type, SetClause)
                action_type, set_clause = item
                if action_type == "on_create":
                    on_create = set_clause
                elif action_type == "on_match":
                    on_match = set_clause
            else:
                patterns.append(item)

        return MergeClause(patterns=patterns, on_create=on_create, on_match=on_match)

    def merge_action(self, items):
        """Transform merge action."""
        return items[0]

    def on_create_clause(self, items):
        """Transform ON CREATE SET clause."""
        return ("on_create", items[0])

    def on_match_clause(self, items):
        """Transform ON MATCH SET clause."""
        return ("on_match", items[0])

    def unwind_clause(self, items):
        """Transform UNWIND clause."""
        # items: [expression, variable]
        expression = items[0]
        variable = items[1]
        return UnwindClause(expression=expression, variable=variable.name)

    def call_clause(self, items):
        """Transform CALL clause."""
        # items: [query]
        from graphforge.ast.clause import CallClause

        return CallClause(query=items[0])

    def where_clause(self, items):
        """Transform WHERE clause."""
        return WhereClause(predicate=items[0])

    def return_clause(self, items):
        """Transform RETURN clause."""
        return_items = []
        distinct = False

        for item in items:
            if isinstance(item, ReturnItem):
                return_items.append(item)
            elif isinstance(item, Token) and item.value.upper() == "DISTINCT":
                distinct = True

        return ReturnClause(items=return_items, distinct=distinct)

    def with_clause(self, items):
        """Transform WITH clause.

        Structure: return_item+ where_clause? order_by_clause? skip_clause? limit_clause?
        """
        # First collect all return items (before any optional clauses)
        return_items = []
        distinct = False
        where = None
        order_by = None
        skip = None
        limit = None

        for item in items:
            if isinstance(item, ReturnItem):
                return_items.append(item)
            elif isinstance(item, Token) and item.value.upper() == "DISTINCT":
                distinct = True
            elif isinstance(item, WhereClause):
                where = item
            elif isinstance(item, OrderByClause):
                order_by = item
            elif isinstance(item, SkipClause):
                skip = item
            elif isinstance(item, LimitClause):
                limit = item

        return WithClause(
            items=return_items,
            distinct=distinct,
            where=where,
            order_by=order_by,
            skip=skip,
            limit=limit,
        )

    def limit_clause(self, items):
        """Transform LIMIT clause."""
        return LimitClause(count=int(items[0]))

    def skip_clause(self, items):
        """Transform SKIP clause."""
        return SkipClause(count=int(items[0]))

    def order_by_clause(self, items):
        """Transform ORDER BY clause."""
        return OrderByClause(items=list(items))

    def order_by_item(self, items):
        """Transform ORDER BY item with optional direction."""
        expression = items[0]
        ascending = True  # Default is ASC
        if len(items) > 1:
            # Second item is the DIRECTION token
            direction = self._get_token_value(items[1]).upper()
            ascending = direction == "ASC"
        return OrderByItem(expression=expression, ascending=ascending)

    # Patterns
    def pattern_with_binding(self, items):
        """Transform pattern with path variable binding: p = (a)-[:R]->(b)."""
        # items: [Variable, pattern_parts_list]
        path_var = items[0]
        pattern_parts = items[1]

        # Return dict with path variable and pattern parts
        return {"path_variable": path_var.name, "parts": pattern_parts}

    def pattern_without_binding(self, items):
        """Transform pattern without path binding."""
        # items: [pattern_parts_list]
        return {"path_variable": None, "parts": items[0]}

    def pattern_parts(self, items):
        """Transform pattern parts (node-rel-node-rel-node...)."""
        return items

    def node_pattern(self, items):
        """Transform node pattern."""
        variable = None
        labels = []
        properties = {}

        for item in items:
            if isinstance(item, Variable):
                variable = item.name
            elif isinstance(item, list):
                # Check if it's the new nested list format (label groups)
                if item and isinstance(item[0], list):
                    # It's a list of label groups (disjunction of conjunctions)
                    labels = item
                elif all(isinstance(x, str) for x in item):
                    # It's a flat list of strings (old format, shouldn't happen anymore)
                    labels = [item]  # Wrap in a list to make it consistent
            elif isinstance(item, dict):
                properties = item

        return NodePattern(variable=variable, labels=labels, properties=properties)

    def relationship_pattern(self, items):
        """Transform relationship pattern."""
        return items[0] if items else None

    def right_arrow_rel(self, items):
        """Transform outgoing relationship."""
        variable, types, properties, min_hops, max_hops, predicate = self._parse_rel_parts(items)
        return RelationshipPattern(
            variable=variable,
            types=types,
            direction=Direction.OUT,
            properties=properties,
            min_hops=min_hops,
            max_hops=max_hops,
            predicate=predicate,
        )

    def left_arrow_rel(self, items):
        """Transform incoming relationship."""
        variable, types, properties, min_hops, max_hops, predicate = self._parse_rel_parts(items)
        return RelationshipPattern(
            variable=variable,
            types=types,
            direction=Direction.IN,
            properties=properties,
            min_hops=min_hops,
            max_hops=max_hops,
            predicate=predicate,
        )

    def undirected_rel(self, items):
        """Transform undirected relationship."""
        variable, types, properties, min_hops, max_hops, predicate = self._parse_rel_parts(items)
        return RelationshipPattern(
            variable=variable,
            types=types,
            direction=Direction.UNDIRECTED,
            properties=properties,
            min_hops=min_hops,
            max_hops=max_hops,
            predicate=predicate,
        )

    def pattern_where(self, items):
        """Transform pattern WHERE clause."""
        # items[0] is the expression
        return items[0] if items else None

    def _parse_rel_parts(self, items):
        """Parse relationship variable, types, properties, variable-length range, and predicate."""
        variable = None
        types = []
        properties = {}
        min_hops = None
        max_hops = None
        predicate = None

        for item in items:
            if isinstance(item, Variable):
                variable = item.name
            elif isinstance(item, list) and all(isinstance(x, str) for x in item):
                types = item
            elif isinstance(item, dict):
                properties = item
            elif isinstance(item, tuple) and len(item) == 2:
                # Variable-length range: (min_hops, max_hops)
                min_hops, max_hops = item
            elif hasattr(item, "__class__") and item.__class__.__name__ in [
                "BinaryOp",
                "UnaryOp",
                "FunctionCall",
                "PropertyAccess",
                "Literal",
            ]:
                # This is a WHERE predicate expression
                predicate = item

        return variable, types, properties, min_hops, max_hops, predicate

    def var_length_unbounded(self, items):
        """Transform unbounded variable-length: *"""
        # * means 1 or more hops (unbounded)
        return (1, None)

    def var_length_min_max(self, items):
        """Transform variable-length with min and max: *1..3"""
        min_val = int(items[0])
        max_val = int(items[1])
        return (min_val, max_val)

    def var_length_min_only(self, items):
        """Transform variable-length with only min: *2.."""
        min_val = int(items[0])
        return (min_val, None)

    def var_length_max_only(self, items):
        """Transform variable-length with only max: *..3"""
        max_val = int(items[0])
        return (1, max_val)

    # Labels and types
    def labels(self, items):
        """Transform labels rule.

        Returns a list of label groups (disjunction of conjunctions).
        Example: :Person → [['Person']]
        Example: :Person:Employee → [['Person', 'Employee']]
        Example: :Person|Company → [['Person'], ['Company']]
        Example: :Person:Employee|Company:Startup → [['Person', 'Employee'], ['Company', 'Startup']]
        """
        # items[0] is the label_disjunction
        return items[0]

    def label_disjunction(self, items):
        """Transform label disjunction (list of label_conjunction groups)."""
        return list(items)

    def label_conjunction(self, items):
        """Transform a conjunction group of labels (list of IDENTIFIER tokens)."""
        return [self._get_token_value(item) for item in items]

    def label(self, items):
        """Transform single label (for REMOVE clause)."""
        return self._get_token_value(items[0])

    def rel_types(self, items):
        """Transform relationship types."""
        return list(items)

    def rel_type(self, items):
        """Transform single relationship type."""
        return self._get_token_value(items[0])

    # Properties
    def properties(self, items):
        """Transform property map."""
        props = {}
        for item in items:
            if isinstance(item, tuple) and len(item) == 2:
                props[item[0]] = item[1]
        return props

    def property(self, items):
        """Transform single property."""
        return (self._get_token_value(items[0]), items[1])

    # Expressions
    def return_all(self, items):
        """Transform RETURN * item."""
        # "*" means return all variables in scope
        # Use Wildcard expression to represent this
        return ReturnItem(expression=Wildcard(), alias=None)

    def return_expression(self, items):
        """Transform return item with optional alias."""
        expression = items[0]
        alias = None
        if len(items) > 1:
            # Second item is the alias (IDENTIFIER token)
            alias = self._get_token_value(items[1])
        return ReturnItem(expression=expression, alias=alias)

    def or_expr(self, items):
        """Transform OR expression."""
        if len(items) == 1:
            return items[0]
        # Build left-associative OR chain
        result = items[0]
        for item in items[1:]:
            result = BinaryOp(op="OR", left=result, right=item)
        return result

    def xor_expr(self, items):
        """Transform XOR expression."""
        if len(items) == 1:
            return items[0]
        # Build left-associative XOR chain
        result = items[0]
        for item in items[1:]:
            result = BinaryOp(op="XOR", left=result, right=item)
        return result

    def and_expr(self, items):
        """Transform AND expression."""
        if len(items) == 1:
            return items[0]
        # Build left-associative AND chain
        result = items[0]
        for item in items[1:]:
            result = BinaryOp(op="AND", left=result, right=item)
        return result

    def not_operation(self, items):
        """Transform NOT operation (when NOT keyword is present)."""
        # items[0] is the operand (result of transforming the inner not_expr)
        return UnaryOp(op="NOT", operand=items[0])

    def not_passthrough(self, items):
        """Transform not_expr when there's no NOT (just passes through comparison_expr)."""
        return items[0]

    def comparison_expr(self, items):
        """Transform comparison expression."""
        if len(items) == 1:
            return items[0]
        # Check if it's a NULL check (IS NULL or IS NOT NULL)
        if len(items) == 2 and isinstance(items[1], str) and items[1] in ("IS NULL", "IS NOT NULL"):
            # Items: [left, "IS NULL" or "IS NOT NULL"]
            # Represent as unary operation to distinguish from = NULL
            return UnaryOp(op=items[1], operand=items[0])
        # Items: [left, op, right]
        # op can be either a Token (COMP_OP) or a string from string_match_op
        op = items[1] if isinstance(items[1], str) else self._get_token_value(items[1])
        return BinaryOp(op=op, left=items[0], right=items[2])

    def starts_with(self, items):
        """Transform STARTS WITH operator."""
        return "STARTS WITH"

    def ends_with(self, items):
        """Transform ENDS WITH operator."""
        return "ENDS WITH"

    def contains(self, items):
        """Transform CONTAINS operator."""
        return "CONTAINS"

    def in_operator(self, items):
        """Transform IN operator."""
        return "IN"

    def is_null(self, items):
        """Transform IS NULL operator."""
        return "IS NULL"

    def is_not_null(self, items):
        """Transform IS NOT NULL operator."""
        return "IS NOT NULL"

    def add_expr(self, items):
        """Transform addition/subtraction expression."""
        if len(items) == 1:
            return items[0]
        # Build left-associative chain: mult_expr (("+"|"-") mult_expr)*
        result = items[0]
        i = 1
        while i < len(items):
            op = self._get_token_value(items[i])
            result = BinaryOp(op=op, left=result, right=items[i + 1])
            i += 2
        return result

    def mult_expr(self, items):
        """Transform multiplication/division/modulo expression."""
        if len(items) == 1:
            return items[0]
        # Build left-associative chain: power_expr (("*"|"/"|"%") power_expr)*
        result = items[0]
        i = 1
        while i < len(items):
            op = self._get_token_value(items[i])
            result = BinaryOp(op=op, left=result, right=items[i + 1])
            i += 2
        return result

    def power_expr(self, items):
        """Transform power/exponentiation expression.

        Right-associative: 2^3^2 = 2^(3^2) = 512, NOT (2^3)^2 = 64.
        """
        if len(items) == 1:
            return items[0]
        # Build right-associative chain: unary_expr ("^" unary_expr)*
        # Collect operands (every other item, starting at 0)
        operands = items[::2]
        # Build from right to left
        result = operands[-1]
        for i in range(len(operands) - 2, -1, -1):
            result = BinaryOp(op="^", left=operands[i], right=result)
        return result

    def unary_minus(self, items):
        """Transform unary minus expression (e.g., -5, -x)."""
        return UnaryOp(op="-", operand=items[0])

    def unary_passthrough(self, items):
        """Transform unary_expr when there's no unary minus (just passes through primary_expr)."""
        return items[0]

    def property_access(self, items):
        """Transform property access.

        Supports:
        - variable.property (e.g., n.name)
        - map_literal.property (e.g., {key: 'value'}.key)
        - list_literal.property (e.g., [1, 2, 3][0].prop)
        """
        base_expr = items[0]
        prop_name = self._get_token_value(items[1])

        # If base is a Variable, use variable field for backward compatibility
        if isinstance(base_expr, Variable):
            return PropertyAccess(variable=base_expr.name, property=prop_name)

        # Otherwise, use base field for expression-based property access
        return PropertyAccess(base=base_expr, property=prop_name)

    def subscript(self, items):
        """Transform subscript/slice expression.

        Supports:
        - list[index] - single index access
        - list[start..end] - slice with start and end
        - list[..end] - slice from beginning to end
        - list[start..] - slice from start to end of list
        """
        base_expr = items[0]
        index_info = items[1]  # This is the result from subscript_index

        # index_info is a Subscript object with index OR start/end set
        # Update it with the correct base
        return Subscript(
            base=base_expr,
            index=index_info.index,
            start=index_info.start,
            end=index_info.end,
        )

    def index_access(self, items):
        """Transform single index access: list[0]"""
        # items[0] is the index expression
        return Subscript(base=None, index=items[0], start=None, end=None)

    def slice_range(self, items):
        """Transform slice with start and end: list[1..3]"""
        # items[0] is start, items[1] is end
        return Subscript(base=None, index=None, start=items[0], end=items[1])

    def slice_from(self, items):
        """Transform slice from start to end: list[2..]"""
        # items[0] is start, end is None (implicit)
        return Subscript(base=None, index=None, start=items[0], end=None)

    def slice_to(self, items):
        """Transform slice from beginning to end: list[..3]"""
        # start is None (implicit), items[0] is end
        return Subscript(base=None, index=None, start=None, end=items[0])

    def slice_all(self, items):
        """Transform full slice: list[..]"""
        # Both start and end are None (implicit)
        return Subscript(base=None, index=None, start=None, end=None)

    def function_call(self, items):
        """Transform function call."""
        # First item is function name token
        func_name = self._get_token_value(items[0]).upper()
        # Second item (if present) is the args
        args = []
        distinct = False
        if len(items) > 1:
            args_item = items[1]
            if isinstance(args_item, tuple):
                # (args_list, distinct_flag)
                args, distinct = args_item
            else:
                args = args_item
        return FunctionCall(name=func_name, args=args, distinct=distinct)

    def count_star(self, items):
        """Transform COUNT(*) - no arguments."""
        return []  # Empty args list

    def distinct_arg(self, items):
        """Transform DISTINCT argument."""
        return ([items[0]], True)  # (args_list, distinct=True)

    def regular_args(self, items):
        """Transform regular function arguments."""
        return (list(items), False)  # (args_list, distinct=False)

    def case_expr(self, items):
        """Transform CASE expression.

        Structure: when_clause+ [else_expr]?
        """
        when_clauses = []
        else_expr = None

        for item in items:
            if isinstance(item, tuple):
                # when_clause returns (condition, result)
                when_clauses.append(item)
            else:
                # ELSE expression
                else_expr = item

        return CaseExpression(when_clauses=when_clauses, else_expr=else_expr)

    def when_clause(self, items):
        """Transform WHEN clause.

        Structure: WHEN condition THEN result
        Returns: (condition_expr, result_expr)
        """
        condition = items[0]
        result = items[1]
        return (condition, result)

    def exists_expr(self, items):
        """Transform EXISTS subquery expression.

        Syntax: EXISTS { MATCH ... }
        """
        from graphforge.ast.expression import SubqueryExpression

        # items[0] is the nested query
        return SubqueryExpression(type="EXISTS", query=items[0])

    def count_expr(self, items):
        """Transform COUNT subquery expression.

        Syntax: COUNT { MATCH ... }
        """
        from graphforge.ast.expression import SubqueryExpression

        # items[0] is the nested query
        return SubqueryExpression(type="COUNT", query=items[0])

    def all_quantifier(self, items):
        """Transform ALL quantifier expression.

        Syntax: ALL(x IN list WHERE predicate)
        """
        from graphforge.ast.expression import QuantifierExpression

        # items[0] = variable, items[1] = list_expr, items[2] = predicate
        variable = items[0].name if hasattr(items[0], "name") else str(items[0])
        return QuantifierExpression(
            quantifier="ALL", variable=variable, list_expr=items[1], predicate=items[2]
        )

    def any_quantifier(self, items):
        """Transform ANY quantifier expression.

        Syntax: ANY(x IN list WHERE predicate)
        """
        from graphforge.ast.expression import QuantifierExpression

        variable = items[0].name if hasattr(items[0], "name") else str(items[0])
        return QuantifierExpression(
            quantifier="ANY", variable=variable, list_expr=items[1], predicate=items[2]
        )

    def none_quantifier(self, items):
        """Transform NONE quantifier expression.

        Syntax: NONE(x IN list WHERE predicate)
        """
        from graphforge.ast.expression import QuantifierExpression

        variable = items[0].name if hasattr(items[0], "name") else str(items[0])
        return QuantifierExpression(
            quantifier="NONE", variable=variable, list_expr=items[1], predicate=items[2]
        )

    def single_quantifier(self, items):
        """Transform SINGLE quantifier expression.

        Syntax: SINGLE(x IN list WHERE predicate)
        """
        from graphforge.ast.expression import QuantifierExpression

        variable = items[0].name if hasattr(items[0], "name") else str(items[0])
        return QuantifierExpression(
            quantifier="SINGLE", variable=variable, list_expr=items[1], predicate=items[2]
        )

    def filter_expr(self, items):
        """Transform FILTER expression.

        Syntax: FILTER(x IN list WHERE predicate)
        """
        from graphforge.ast.expression import FilterExpression

        # items[0] = variable, items[1] = list_expr, items[2] = predicate
        variable = items[0].name if hasattr(items[0], "name") else str(items[0])
        return FilterExpression(variable=variable, list_expr=items[1], predicate=items[2])

    def extract_expr(self, items):
        """Transform EXTRACT expression.

        Syntax: EXTRACT(x IN list | expression)
        """
        from graphforge.ast.expression import ExtractExpression

        # items[0] = variable, items[1] = list_expr, items[2] = map_expr
        variable = items[0].name if hasattr(items[0], "name") else str(items[0])
        return ExtractExpression(variable=variable, list_expr=items[1], map_expr=items[2])

    def reduce_expr(self, items):
        """Transform REDUCE expression.

        Syntax: REDUCE(accumulator = initial, x IN list | expression)
        """
        from graphforge.ast.expression import ReduceExpression

        # items[0] = accumulator, items[1] = initial_expr,
        # items[2] = variable, items[3] = list_expr, items[4] = map_expr
        accumulator = items[0].name if hasattr(items[0], "name") else str(items[0])
        variable = items[2].name if hasattr(items[2], "name") else str(items[2])
        return ReduceExpression(
            accumulator=accumulator,
            initial_expr=items[1],
            variable=variable,
            list_expr=items[3],
            map_expr=items[4],
        )

    def variable(self, items):
        """Transform variable reference."""
        return Variable(name=self._get_token_value(items[0]))

    # Literals
    def int_literal(self, items):
        """Transform integer literal."""
        return Literal(value=int(items[0]))

    def float_literal(self, items):
        """Transform float literal."""
        return Literal(value=float(items[0]))

    def string_literal(self, items):
        """Transform string literal."""
        # Strip quotes
        value = self._get_token_value(items[0])
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        return Literal(value=value)

    def true_literal(self, items):
        """Transform true literal."""
        # items[0] is now a TRUE terminal token
        return Literal(value=True)

    def false_literal(self, items):
        """Transform false literal."""
        # items[0] is now a FALSE terminal token
        return Literal(value=False)

    def null_literal(self, items):
        """Transform null literal."""
        # items[0] is now a NULL terminal token
        return Literal(value=None)

    def list_literal(self, items):
        """Transform list literal.

        items can be empty (for []) or contain expressions.
        Returns a Literal containing a Python list, or a ListComprehension/PatternComprehension
        if that's what was parsed.
        """
        from graphforge.ast.expression import ListComprehension, PatternComprehension

        # Check if this is actually a comprehension (alternative rule)
        if len(items) == 1 and isinstance(items[0], (ListComprehension, PatternComprehension)):
            return items[0]

        # Filter out None values from optional expressions
        # Empty list [] comes through as [None] from Lark
        filtered_items = [item for item in items if item is not None]

        # items contains the expressions in the list
        # We return a Literal with a list of expressions
        # The executor will evaluate these expressions later
        return Literal(value=filtered_items)

    def comp_where_clause(self, items):
        """Transform WHERE clause in list comprehension.

        Returns the filter expression.
        """
        return ("WHERE", items[0])

    def comp_map_clause(self, items):
        """Transform map clause (|) in list comprehension.

        Returns the map expression.
        """
        return ("MAP", items[0])

    def list_comprehension(self, items):
        """Transform list comprehension.

        Syntax: [x IN list WHERE x > 5 | x * 2]
        items: [variable, list_expr, optional_where_clause, optional_map_clause]
        """
        from graphforge.ast.expression import ListComprehension

        # items[0] is a Variable object, extract the name
        variable = (
            items[0].name if isinstance(items[0], Variable) else self._get_token_value(items[0])
        )
        list_expr = items[1]
        filter_expr = None
        map_expr = None

        # Process optional WHERE and MAP clauses (tagged tuples from sub-rules)
        for item in items[2:]:
            if isinstance(item, tuple):
                tag, expr = item
                if tag == "WHERE":
                    filter_expr = expr
                elif tag == "MAP":
                    map_expr = expr

        return ListComprehension(
            variable=variable, list_expr=list_expr, filter_expr=filter_expr, map_expr=map_expr
        )

    def pattern_comprehension(self, items):
        """Transform pattern comprehension.

        Syntax: [(pattern) WHERE predicate | expression]
        items: [pattern, optional_comp_where_clause, map_expression]
        """
        from graphforge.ast.expression import PatternComprehension

        pattern = items[0]
        filter_expr = None
        map_expr = items[-1]  # Last item is always the map expression

        # Check for optional WHERE clause (tagged tuple from comp_where_clause)
        for item in items[1:-1]:
            if isinstance(item, tuple):
                tag, expr = item
                if tag == "WHERE":
                    filter_expr = expr

        return PatternComprehension(pattern=pattern, filter_expr=filter_expr, map_expr=map_expr)

    def map_literal(self, items):
        """Transform map literal.

        items contains map_pair tuples (key, value_expression).
        Returns a Literal containing a Python dict.
        """
        # items contains (key, value_expr) tuples from map_pair
        # We return a Literal with a dict
        return Literal(value=dict(items))

    def map_pair(self, items):
        """Transform map key-value pair.

        Returns tuple of (key_string, value_expression).
        """
        # First item is the key (IDENTIFIER or STRING token)
        key = self._get_token_value(items[0])
        # Strip quotes from STRING keys
        if (key.startswith('"') and key.endswith('"')) or (
            key.startswith("'") and key.endswith("'")
        ):
            key = key[1:-1]
        # Second item is the value expression
        value_expr = items[1]
        return (key, value_expr)


class CypherParser:
    """Main parser for openCypher queries.

    Examples:
        >>> parser = CypherParser()
        >>> ast = parser.parse("MATCH (n:Person) RETURN n")
        >>> isinstance(ast, CypherQuery)
        True
    """

    def __init__(self):
        """Initialize parser with grammar and transformer."""
        grammar_path = Path(__file__).parent / "cypher.lark"
        with grammar_path.open() as f:
            self._lark = Lark(f.read(), start="query", parser="earley")
        self._transformer = ASTTransformer()

    def parse(self, query: str) -> CypherQuery:
        """Parse a Cypher query string into an AST.

        Args:
            query: The Cypher query string to parse

        Returns:
            CypherQuery AST node

        Raises:
            lark.exceptions.LarkError: If the query is syntactically invalid
        """
        tree = self._lark.parse(query)
        ast = self._transformer.transform(tree)
        return ast  # type: ignore[no-any-return]


def parse_cypher(query: str) -> CypherQuery:
    """Convenience function to parse a Cypher query.

    Args:
        query: The Cypher query string to parse

    Returns:
        CypherQuery AST node
    """
    parser = CypherParser()
    return parser.parse(query)
