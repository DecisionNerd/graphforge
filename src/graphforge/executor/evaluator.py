"""Expression evaluator for query execution.

This module evaluates AST expressions in an execution context to produce
CypherValue results.
"""

from typing import Any

from graphforge.ast.expression import BinaryOp, FunctionCall, Literal, PropertyAccess, Variable
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import (
    CypherBool,
    CypherInt,
    CypherNull,
    CypherString,
    CypherValue,
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

    def get(self, name: str) -> Any:
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


def evaluate_expression(expr: Any, ctx: ExecutionContext) -> CypherValue:
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
        return ctx.get(expr.name)  # type: ignore[no-any-return]

    # Property access
    if isinstance(expr, PropertyAccess):
        obj = ctx.get(expr.variable)

        # Handle NodeRef/EdgeRef
        if isinstance(obj, (NodeRef, EdgeRef)):
            if expr.property in obj.properties:
                return obj.properties[expr.property]  # type: ignore[no-any-return]
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

    # Function calls
    if isinstance(expr, FunctionCall):
        return _evaluate_function(expr, ctx)

    raise TypeError(f"Cannot evaluate expression type: {type(expr).__name__}")


# Function categories
STRING_FUNCTIONS = {"LENGTH", "SUBSTRING", "UPPER", "LOWER", "TRIM"}
TYPE_FUNCTIONS = {"TOINTEGER", "TOFLOAT", "TOSTRING", "TYPE"}


def _evaluate_function(func_call: FunctionCall, ctx: ExecutionContext) -> CypherValue:
    """Evaluate scalar function calls.

    Args:
        func_call: Function call AST node
        ctx: Execution context with variable bindings

    Returns:
        CypherValue result of the function

    Raises:
        ValueError: If function is unknown
        TypeError: If function arguments have invalid types
    """
    func_name = func_call.name.upper()

    # COALESCE is special - it doesn't propagate NULL, returns first non-NULL value
    if func_name == "COALESCE":
        args = [evaluate_expression(arg, ctx) for arg in func_call.args]
        for arg in args:
            if not isinstance(arg, CypherNull):
                return arg
        return CypherNull()

    # Evaluate arguments
    args = [evaluate_expression(arg, ctx) for arg in func_call.args]

    # NULL propagation: if any arg is NULL, return NULL (for most functions)
    if any(isinstance(arg, CypherNull) for arg in args):
        return CypherNull()

    # Dispatch to specific function handlers
    if func_name in STRING_FUNCTIONS:
        return _evaluate_string_function(func_name, args)
    elif func_name in TYPE_FUNCTIONS:
        return _evaluate_type_function(func_name, args)
    else:
        raise ValueError(f"Unknown function: {func_name}")


def _evaluate_string_function(func_name: str, args: list[CypherValue]) -> CypherValue:
    """Evaluate string functions.

    Args:
        func_name: Name of the string function (uppercase)
        args: List of evaluated arguments (non-NULL)

    Returns:
        CypherValue result of the string function

    Raises:
        ValueError: If function is unknown
        TypeError: If arguments have invalid types
    """
    if func_name == "LENGTH":
        # LENGTH(string) -> int
        if not isinstance(args[0], CypherString):
            raise TypeError(f"LENGTH expects string, got {type(args[0]).__name__}")
        return CypherInt(len(args[0].value))

    elif func_name == "SUBSTRING":
        # SUBSTRING(string, start) or SUBSTRING(string, start, length)
        if not isinstance(args[0], CypherString):
            raise TypeError(f"SUBSTRING expects string, got {type(args[0]).__name__}")
        if not isinstance(args[1], CypherInt):
            raise TypeError("SUBSTRING start must be integer")

        string = args[0].value
        start = args[1].value

        if len(args) == 3:
            if not isinstance(args[2], CypherInt):
                raise TypeError("SUBSTRING length must be integer")
            length = args[2].value
            return CypherString(string[start : start + length])
        else:
            return CypherString(string[start:])

    elif func_name == "UPPER":
        if not isinstance(args[0], CypherString):
            raise TypeError(f"UPPER expects string, got {type(args[0]).__name__}")
        return CypherString(args[0].value.upper())

    elif func_name == "LOWER":
        if not isinstance(args[0], CypherString):
            raise TypeError(f"LOWER expects string, got {type(args[0]).__name__}")
        return CypherString(args[0].value.lower())

    elif func_name == "TRIM":
        if not isinstance(args[0], CypherString):
            raise TypeError(f"TRIM expects string, got {type(args[0]).__name__}")
        return CypherString(args[0].value.strip())

    raise ValueError(f"Unknown string function: {func_name}")


def _evaluate_type_function(func_name: str, _args: list[CypherValue]) -> CypherValue:
    """Evaluate type conversion and introspection functions.

    Args:
        func_name: Name of the type function
        _args: List of evaluated arguments (non-NULL) - unused in placeholder

    Returns:
        CypherValue result of the type function

    Raises:
        ValueError: If function is unknown
        TypeError: If arguments have invalid types
    """
    # Placeholder - will be implemented in Feature 3
    raise ValueError(f"Type function not yet implemented: {func_name}")
