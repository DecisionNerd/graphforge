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
    UnaryOp,
    Variable,
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
        # Items can be single_part_query or multi_part_query
        return items[0] if len(items) == 1 else CypherQuery(clauses=list(items))

    def single_part_query(self, items):
        """Transform single-part query (without WITH)."""
        # Items already contain a CypherQuery from read_query, write_query, or update_query
        return items[0]

    def multi_part_query(self, items):
        """Transform multi-part query (with WITH clauses).

        Structure: reading_clause+ with_clause+ single_part_query
        Each reading_clause is a list of clauses (MATCH, WHERE)
        Each with_clause is a WithClause
        single_part_query is a CypherQuery
        """
        # Flatten all clauses from reading clauses, with clauses, and final query
        all_clauses = []

        for item in items:
            if isinstance(item, list):
                # reading_clause returns a list of clauses
                all_clauses.extend(item)
            elif isinstance(item, WithClause):
                # with_clause returns a single WithClause
                all_clauses.append(item)
            elif isinstance(item, CypherQuery):
                # single_part_query returns a CypherQuery
                all_clauses.extend(item.clauses)

        return CypherQuery(clauses=all_clauses)

    def reading_clause(self, items):
        """Transform reading clause (MATCH/UNWIND with optional WHERE).

        Returns a list of clauses for easier flattening in multi_part_query.
        """
        return list(items)

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

    # Clauses
    def match_clause(self, items):
        """Transform MATCH clause."""
        patterns = [item for item in items if not isinstance(item, str)]
        return MatchClause(patterns=patterns)

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
        """Transform MERGE clause with optional ON CREATE action."""
        patterns = []
        on_create = None

        for item in items:
            if isinstance(item, str):
                continue
            if isinstance(item, tuple) and item[0] == "on_create":
                on_create = item[1]
            else:
                patterns.append(item)

        return MergeClause(patterns=patterns, on_create=on_create)

    def merge_action(self, items):
        """Transform merge action."""
        return items[0]

    def on_create_clause(self, items):
        """Transform ON CREATE SET clause."""
        return ("on_create", items[0])

    def unwind_clause(self, items):
        """Transform UNWIND clause."""
        # items: [expression, variable]
        expression = items[0]
        variable = items[1]
        return UnwindClause(expression=expression, variable=variable.name)

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
    def pattern(self, items):
        """Transform pattern (node-rel-node-rel-node...)."""
        return items

    def node_pattern(self, items):
        """Transform node pattern."""
        variable = None
        labels = []
        properties = {}

        for item in items:
            if isinstance(item, Variable):
                variable = item.name
            elif isinstance(item, list) and all(isinstance(x, str) for x in item):
                labels = item
            elif isinstance(item, dict):
                properties = item

        return NodePattern(variable=variable, labels=labels, properties=properties)

    def relationship_pattern(self, items):
        """Transform relationship pattern."""
        return items[0] if items else None

    def right_arrow_rel(self, items):
        """Transform outgoing relationship."""
        variable, types, properties = self._parse_rel_parts(items)
        return RelationshipPattern(
            variable=variable,
            types=types,
            direction=Direction.OUT,
            properties=properties,
        )

    def left_arrow_rel(self, items):
        """Transform incoming relationship."""
        variable, types, properties = self._parse_rel_parts(items)
        return RelationshipPattern(
            variable=variable,
            types=types,
            direction=Direction.IN,
            properties=properties,
        )

    def undirected_rel(self, items):
        """Transform undirected relationship."""
        variable, types, properties = self._parse_rel_parts(items)
        return RelationshipPattern(
            variable=variable,
            types=types,
            direction=Direction.UNDIRECTED,
            properties=properties,
        )

    def _parse_rel_parts(self, items):
        """Parse relationship variable, types, and properties."""
        variable = None
        types = []
        properties = {}

        for item in items:
            if isinstance(item, Variable):
                variable = item.name
            elif isinstance(item, list) and all(isinstance(x, str) for x in item):
                types = item
            elif isinstance(item, dict):
                properties = item

        return variable, types, properties

    # Labels and types
    def labels(self, items):
        """Transform labels."""
        return list(items)

    def label(self, items):
        """Transform single label."""
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
    def return_item(self, items):
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
        # Build left-associative chain: unary_expr (("*"|"/"|"%") unary_expr)*
        result = items[0]
        i = 1
        while i < len(items):
            op = self._get_token_value(items[i])
            result = BinaryOp(op=op, left=result, right=items[i + 1])
            i += 2
        return result

    def unary_minus(self, items):
        """Transform unary minus expression (e.g., -5, -x)."""
        return UnaryOp(op="-", operand=items[0])

    def unary_passthrough(self, items):
        """Transform unary_expr when there's no unary minus (just passes through primary_expr)."""
        return items[0]

    def property_access(self, items):
        """Transform property access."""
        var_name = (
            items[0].name if isinstance(items[0], Variable) else self._get_token_value(items[0])
        )
        prop_name = self._get_token_value(items[1])
        return PropertyAccess(variable=var_name, property=prop_name)

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
        Returns a Literal containing a Python list.
        """
        # items contains the expressions in the list
        # We return a Literal with a list of expressions
        # The executor will evaluate these expressions later
        return Literal(value=list(items))

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
