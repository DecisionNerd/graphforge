"""openCypher parser for GraphForge.

This module provides the main parser interface that converts openCypher query
strings into AST representations using Lark and custom transformers.
"""

from pathlib import Path

from lark import Lark, Token, Transformer

from graphforge.ast.clause import (
    CreateClause,
    LimitClause,
    MatchClause,
    OrderByClause,
    OrderByItem,
    ReturnClause,
    ReturnItem,
    SkipClause,
    WhereClause,
)
from graphforge.ast.expression import BinaryOp, FunctionCall, Literal, PropertyAccess, Variable
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
        # Items already contain clauses from read_query or write_query
        return items[0] if len(items) == 1 else CypherQuery(clauses=list(items))

    def read_query(self, items):
        """Transform read query (MATCH with optional clauses)."""
        return CypherQuery(clauses=list(items))

    def write_query(self, items):
        """Transform write query (CREATE with optional RETURN)."""
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

    def where_clause(self, items):
        """Transform WHERE clause."""
        return WhereClause(predicate=items[0])

    def return_clause(self, items):
        """Transform RETURN clause."""
        return ReturnClause(items=list(items))

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
        return [item for item in items]

    def label(self, items):
        """Transform single label."""
        return self._get_token_value(items[0])

    def rel_types(self, items):
        """Transform relationship types."""
        return [item for item in items]

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

    def comparison_expr(self, items):
        """Transform comparison expression."""
        if len(items) == 1:
            return items[0]
        # Items: [left, Token(COMP_OP), right]
        op = self._get_token_value(items[1])
        return BinaryOp(op=op, left=items[0], right=items[2])

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
        return Literal(value=True)

    def false_literal(self, items):
        """Transform false literal."""
        return Literal(value=False)

    def null_literal(self, items):
        """Transform null literal."""
        return Literal(value=None)


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
        with open(grammar_path) as f:
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
        return ast


def parse_cypher(query: str) -> CypherQuery:
    """Convenience function to parse a Cypher query.

    Args:
        query: The Cypher query string to parse

    Returns:
        CypherQuery AST node
    """
    parser = CypherParser()
    return parser.parse(query)
