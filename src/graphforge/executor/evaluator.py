"""Expression evaluator for query execution.

This module evaluates AST expressions in an execution context to produce
CypherValue results.
"""

from typing import Any

from graphforge.ast.expression import BinaryOp, Literal, PropertyAccess, Variable
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import (
    CypherBool,
    CypherNull,
    from_python,
)


class ExecutionContext:
    """Context for query execution.

    Maintains variable bindings during query execution.

    Attributes:
        bindings: Dictionary mapping variable names to values
    """

    def __init__(self):
        """Initialize empty execution context."""
        self.bindings: dict[str, Any] = {}

    def bind(self, name: str, value: Any) -> None:
        """Bind a variable to a value.

        Args:
            name: Variable name
            value: Value to bind (NodeRef, EdgeRef, CypherValue)
        """
        self.bindings[name] = value

    def get(self, name: str):
        """Get a variable's value.

        Args:
            name: Variable name

        Returns:
            The bound value

        Raises:
            KeyError: If variable is not bound
        """
        return self.bindings[name]

    def has(self, name: str) -> bool:
        """Check if a variable is bound.

        Args:
            name: Variable name

        Returns:
            True if variable is bound
        """
        return name in self.bindings


def evaluate_expression(expr, ctx: ExecutionContext):
    """Evaluate an AST expression in a context.

    Args:
        expr: AST expression node
        ctx: Execution context with variable bindings

    Returns:
        CypherValue result

    Raises:
        KeyError: If a referenced variable is not bound
        TypeError: If expression type is not supported
    """
    # Literal
    if isinstance(expr, Literal):
        return from_python(expr.value)

    # Variable reference
    if isinstance(expr, Variable):
        return ctx.get(expr.name)

    # Property access
    if isinstance(expr, PropertyAccess):
        obj = ctx.get(expr.variable)

        # Handle NodeRef/EdgeRef
        if isinstance(obj, (NodeRef, EdgeRef)):
            if expr.property in obj.properties:
                return obj.properties[expr.property]
            return CypherNull()

        raise TypeError(f"Cannot access property on {type(obj).__name__}")

    # Binary operations
    if isinstance(expr, BinaryOp):
        left_val = evaluate_expression(expr.left, ctx)
        right_val = evaluate_expression(expr.right, ctx)

        # Comparison operators
        if expr.op == ">":
            result = left_val.less_than(right_val)
            # Swap because we want left > right
            if isinstance(result, CypherBool):
                result = CypherBool(not result.value)
                # But actually we want right < left
                result = right_val.less_than(left_val)
            return result

        if expr.op == "<":
            return left_val.less_than(right_val)

        if expr.op == ">=":
            # left >= right  is  NOT (left < right)
            result = left_val.less_than(right_val)
            if isinstance(result, CypherNull):
                return result
            return CypherBool(not result.value)

        if expr.op == "<=":
            # left <= right  is  NOT (right < left)
            result = right_val.less_than(left_val)
            if isinstance(result, CypherNull):
                return result
            return CypherBool(not result.value)

        if expr.op == "=":
            return left_val.equals(right_val)

        if expr.op == "<>":
            result = left_val.equals(right_val)
            if isinstance(result, CypherNull):
                return result
            return CypherBool(not result.value)

        # Logical operators
        if expr.op == "AND":
            # Handle NULL propagation
            if isinstance(left_val, CypherNull) or isinstance(right_val, CypherNull):
                return CypherNull()
            # Both must be booleans
            if isinstance(left_val, CypherBool) and isinstance(right_val, CypherBool):
                return CypherBool(left_val.value and right_val.value)
            raise TypeError("AND requires boolean operands")

        if expr.op == "OR":
            # Handle NULL propagation
            if isinstance(left_val, CypherNull) or isinstance(right_val, CypherNull):
                return CypherNull()
            # Both must be booleans
            if isinstance(left_val, CypherBool) and isinstance(right_val, CypherBool):
                return CypherBool(left_val.value or right_val.value)
            raise TypeError("OR requires boolean operands")

        raise ValueError(f"Unknown binary operator: {expr.op}")

    raise TypeError(f"Cannot evaluate expression type: {type(expr).__name__}")
