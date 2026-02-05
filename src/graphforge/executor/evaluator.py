"""Expression evaluator for query execution.

This module evaluates AST expressions in an execution context to produce
CypherValue results.
"""

from typing import Any

from graphforge.ast.expression import (
    BinaryOp,
    CaseExpression,
    FunctionCall,
    Literal,
    PropertyAccess,
    UnaryOp,
    Variable,
)
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import (
    CypherBool,
    CypherDate,
    CypherDateTime,
    CypherDuration,
    CypherFloat,
    CypherInt,
    CypherList,
    CypherMap,
    CypherNull,
    CypherString,
    CypherTime,
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
        value = expr.value
        # Handle nested structures (lists and maps)
        if isinstance(value, list):
            # Evaluate each item in the list
            evaluated_items = [
                evaluate_expression(item, ctx)
                if isinstance(
                    item,
                    (Literal, Variable, PropertyAccess, BinaryOp, FunctionCall, CaseExpression),
                )
                else from_python(item)
                for item in value
            ]
            return CypherList(evaluated_items)
        elif isinstance(value, dict):
            # Evaluate each value in the dict
            evaluated_dict = {}
            for key, val in value.items():
                if isinstance(
                    val, (Literal, Variable, PropertyAccess, BinaryOp, FunctionCall, CaseExpression)
                ):
                    evaluated_dict[key] = evaluate_expression(val, ctx)
                else:
                    evaluated_dict[key] = from_python(val)
            return CypherMap(evaluated_dict)
        else:
            # Simple scalar value
            return from_python(value)

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

    # Unary operations
    if isinstance(expr, UnaryOp):
        operand_val = evaluate_expression(expr.operand, ctx)

        # NOT operator
        if expr.op == "NOT":
            # Handle NULL: NOT NULL → NULL
            if isinstance(operand_val, CypherNull):
                return CypherNull()
            # Must be boolean
            if isinstance(operand_val, CypherBool):
                return CypherBool(not operand_val.value)
            raise TypeError("NOT requires boolean operand")

        # Unary minus operator
        if expr.op == "-":
            # Handle NULL: -NULL → NULL
            if isinstance(operand_val, CypherNull):
                return CypherNull()
            # Must be numeric
            if isinstance(operand_val, CypherInt):
                return CypherInt(-operand_val.value)
            if isinstance(operand_val, CypherFloat):
                return CypherFloat(-operand_val.value)
            raise TypeError(
                f"Unary minus requires numeric operand, got {type(operand_val).__name__}"
            )

        raise ValueError(f"Unknown unary operator: {expr.op}")

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

        # Arithmetic operators
        if expr.op in ("+", "-", "*", "/", "%"):
            # NULL propagation: any NULL operand returns NULL
            if isinstance(left_val, CypherNull) or isinstance(right_val, CypherNull):
                return CypherNull()

            # Special case: string concatenation with +
            if expr.op == "+":
                from graphforge.types.values import CypherString, CypherValue

                if isinstance(left_val, CypherString) or isinstance(right_val, CypherString):
                    # Ensure both operands are CypherValue instances before accessing .value
                    if not isinstance(left_val, CypherValue) or not isinstance(
                        right_val, CypherValue
                    ):
                        raise TypeError(
                            f"String concatenation requires CypherValue operands, "
                            f"got {type(left_val).__name__} and {type(right_val).__name__}"
                        )

                    # Convert both to strings and concatenate
                    left_str = (
                        left_val.value
                        if isinstance(left_val, CypherString)
                        else str(left_val.value)
                    )
                    right_str = (
                        right_val.value
                        if isinstance(right_val, CypherString)
                        else str(right_val.value)
                    )
                    return CypherString(left_str + right_str)

            # Type checking: both operands must be numeric
            if not isinstance(left_val, (CypherInt, CypherFloat)) or not isinstance(
                right_val, (CypherInt, CypherFloat)
            ):
                raise TypeError(
                    f"Arithmetic operator {expr.op} requires numeric operands, "
                    f"got {type(left_val).__name__} and {type(right_val).__name__}"
                )

            # Type coercion: if either operand is float, result is float
            result_type = (
                CypherFloat
                if isinstance(left_val, CypherFloat) or isinstance(right_val, CypherFloat)
                else CypherInt
            )

            # Convert to Python numeric types
            left_num = (
                float(left_val.value) if isinstance(left_val, CypherFloat) else int(left_val.value)
            )
            right_num = (
                float(right_val.value)
                if isinstance(right_val, CypherFloat)
                else int(right_val.value)
            )

            # Perform arithmetic operation
            arith_result: float | int
            if expr.op == "+":
                arith_result = left_num + right_num
            elif expr.op == "-":
                arith_result = left_num - right_num
            elif expr.op == "*":
                arith_result = left_num * right_num
            elif expr.op == "/":
                # Division by zero returns NULL
                if right_num == 0:
                    return CypherNull()
                # Division always returns float in Cypher
                return CypherFloat(left_num / right_num)
            elif expr.op == "%":
                # Modulo by zero returns NULL
                if right_num == 0:
                    return CypherNull()
                arith_result = left_num % right_num
            else:
                raise ValueError(f"Unknown arithmetic operator: {expr.op}")

            # Return with appropriate type (except division which always returns float)
            if result_type is CypherFloat:
                return CypherFloat(float(arith_result))
            else:
                return CypherInt(int(arith_result))

        # String matching operators
        if expr.op in ("STARTS WITH", "ENDS WITH", "CONTAINS"):
            # NULL handling: any NULL operand returns NULL
            if isinstance(left_val, CypherNull) or isinstance(right_val, CypherNull):
                return CypherNull()

            # Type checking: both operands must be strings
            from graphforge.types.values import CypherString

            if not isinstance(left_val, CypherString) or not isinstance(right_val, CypherString):
                raise TypeError(
                    f"{expr.op} requires string operands, "
                    f"got {type(left_val).__name__} and {type(right_val).__name__}"
                )

            # Perform string matching
            if expr.op == "STARTS WITH":
                return CypherBool(left_val.value.startswith(right_val.value))
            elif expr.op == "ENDS WITH":
                return CypherBool(left_val.value.endswith(right_val.value))
            elif expr.op == "CONTAINS":
                return CypherBool(right_val.value in left_val.value)

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

    # CASE expressions
    if isinstance(expr, CaseExpression):
        # Evaluate WHEN clauses in order until one matches
        for condition_expr, result_expr in expr.when_clauses:
            condition_val = evaluate_expression(condition_expr, ctx)

            # NULL is treated as false, not propagated
            if isinstance(condition_val, CypherBool) and condition_val.value:
                return evaluate_expression(result_expr, ctx)

        # No WHEN matched - return ELSE or NULL
        if expr.else_expr is not None:
            return evaluate_expression(expr.else_expr, ctx)

        return CypherNull()

    # Function calls
    if isinstance(expr, FunctionCall):
        return _evaluate_function(expr, ctx)

    raise TypeError(f"Cannot evaluate expression type: {type(expr).__name__}")


# Function categories
STRING_FUNCTIONS = {"LENGTH", "SUBSTRING", "UPPER", "LOWER", "TRIM"}
TYPE_FUNCTIONS = {"TOINTEGER", "TOFLOAT", "TOSTRING", "TYPE"}
TEMPORAL_FUNCTIONS = {
    "DATE",
    "DATETIME",
    "TIME",
    "DURATION",
    "YEAR",
    "MONTH",
    "DAY",
    "HOUR",
    "MINUTE",
    "SECOND",
}


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
    elif func_name in TEMPORAL_FUNCTIONS:
        return _evaluate_temporal_function(func_name, args)
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

        # Validate start is non-negative (openCypher requirement)
        if start < 0:
            raise TypeError("SUBSTRING start must be non-negative")

        if len(args) == 3:
            if not isinstance(args[2], CypherInt):
                raise TypeError("SUBSTRING length must be integer")
            length = args[2].value
            # Validate length is non-negative (openCypher requirement)
            if length < 0:
                raise TypeError("SUBSTRING length must be non-negative")
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


def _evaluate_type_function(func_name: str, args: list[CypherValue]) -> CypherValue:
    """Evaluate type conversion and introspection functions.

    Args:
        func_name: Name of the type function
        args: List of evaluated arguments (non-NULL)

    Returns:
        CypherValue result of the type function

    Raises:
        ValueError: If function is unknown
        TypeError: If arguments have invalid types
    """
    # Special handling for NULL in type conversions
    if isinstance(args[0], CypherNull):
        return CypherNull()

    if func_name == "TOINTEGER":
        try:
            if isinstance(args[0], CypherInt):
                return args[0]
            elif isinstance(args[0], (CypherFloat, CypherString)):
                return CypherInt(int(args[0].value))
            elif isinstance(args[0], CypherBool):
                # Booleans convert to 1 (true) or 0 (false)
                return CypherInt(1 if args[0].value else 0)
            else:
                return CypherNull()  # Cannot convert
        except (ValueError, TypeError):
            return CypherNull()

    elif func_name == "TOFLOAT":
        try:
            if isinstance(args[0], CypherFloat):
                return args[0]
            elif isinstance(args[0], (CypherInt, CypherString)):
                return CypherFloat(float(args[0].value))
            elif isinstance(args[0], CypherBool):
                # Booleans convert to 1.0 (true) or 0.0 (false)
                return CypherFloat(1.0 if args[0].value else 0.0)
            else:
                return CypherNull()
        except (ValueError, TypeError):
            return CypherNull()

    elif func_name == "TOSTRING":
        if isinstance(args[0], CypherString):
            return args[0]
        elif isinstance(args[0], (CypherInt, CypherFloat)):
            return CypherString(str(args[0].value))
        elif isinstance(args[0], CypherBool):
            # Booleans convert to "true" or "false"
            return CypherString("true" if args[0].value else "false")
        else:
            return CypherNull()

    elif func_name == "TYPE":
        # TYPE function returns the type name as a string
        # Return the CypherValue type name
        type_name = type(args[0]).__name__
        # Strip "Cypher" prefix for cleaner output
        if type_name.startswith("Cypher"):
            type_name = type_name[6:]  # Remove "Cypher" prefix
        return CypherString(type_name)

    raise ValueError(f"Unknown type function: {func_name}")


def _evaluate_temporal_function(func_name: str, args: list[CypherValue]) -> CypherValue:
    """Evaluate temporal functions.

    Args:
        func_name: Name of the temporal function (uppercase)
        args: List of evaluated arguments (non-NULL)

    Returns:
        CypherValue result of the temporal function

    Raises:
        ValueError: If function is unknown
        TypeError: If arguments have invalid types
    """
    if func_name == "DATE":
        # date() or date(string)
        if len(args) == 0:
            # date() returns current date
            import datetime

            return CypherDate(datetime.date.today())
        elif len(args) == 1:
            # date(string) parses ISO 8601 date
            if not isinstance(args[0], CypherString):
                raise TypeError(f"DATE expects string, got {type(args[0]).__name__}")
            return CypherDate(args[0].value)
        else:
            raise TypeError(f"DATE expects 0 or 1 argument, got {len(args)}")

    elif func_name == "DATETIME":
        # datetime() or datetime(string)
        if len(args) == 0:
            # datetime() returns current datetime
            import datetime

            return CypherDateTime(datetime.datetime.now())
        elif len(args) == 1:
            # datetime(string) parses ISO 8601 datetime
            if not isinstance(args[0], CypherString):
                raise TypeError(f"DATETIME expects string, got {type(args[0]).__name__}")
            return CypherDateTime(args[0].value)
        else:
            raise TypeError(f"DATETIME expects 0 or 1 argument, got {len(args)}")

    elif func_name == "TIME":
        # time() or time(string)
        if len(args) == 0:
            # time() returns current time
            import datetime

            return CypherTime(datetime.datetime.now().time())
        elif len(args) == 1:
            # time(string) parses ISO 8601 time
            if not isinstance(args[0], CypherString):
                raise TypeError(f"TIME expects string, got {type(args[0]).__name__}")
            return CypherTime(args[0].value)
        else:
            raise TypeError(f"TIME expects 0 or 1 argument, got {len(args)}")

    elif func_name == "DURATION":
        # duration(string)
        if len(args) != 1:
            raise TypeError(f"DURATION expects 1 argument, got {len(args)}")
        if not isinstance(args[0], CypherString):
            raise TypeError(f"DURATION expects string, got {type(args[0]).__name__}")
        return CypherDuration(args[0].value)

    # Temporal component extraction functions
    elif func_name == "YEAR":
        if len(args) != 1:
            raise TypeError(f"YEAR expects 1 argument, got {len(args)}")
        if not isinstance(args[0], (CypherDate, CypherDateTime)):
            raise TypeError(f"YEAR expects date or datetime, got {type(args[0]).__name__}")
        return CypherInt(args[0].value.year)

    elif func_name == "MONTH":
        if len(args) != 1:
            raise TypeError(f"MONTH expects 1 argument, got {len(args)}")
        if not isinstance(args[0], (CypherDate, CypherDateTime)):
            raise TypeError(f"MONTH expects date or datetime, got {type(args[0]).__name__}")
        return CypherInt(args[0].value.month)

    elif func_name == "DAY":
        if len(args) != 1:
            raise TypeError(f"DAY expects 1 argument, got {len(args)}")
        if not isinstance(args[0], (CypherDate, CypherDateTime)):
            raise TypeError(f"DAY expects date or datetime, got {type(args[0]).__name__}")
        return CypherInt(args[0].value.day)

    elif func_name == "HOUR":
        if len(args) != 1:
            raise TypeError(f"HOUR expects 1 argument, got {len(args)}")
        if isinstance(args[0], (CypherDateTime, CypherTime)):
            return CypherInt(args[0].value.hour)
        else:
            raise TypeError(f"HOUR expects datetime or time, got {type(args[0]).__name__}")

    elif func_name == "MINUTE":
        if len(args) != 1:
            raise TypeError(f"MINUTE expects 1 argument, got {len(args)}")
        if isinstance(args[0], (CypherDateTime, CypherTime)):
            return CypherInt(args[0].value.minute)
        else:
            raise TypeError(f"MINUTE expects datetime or time, got {type(args[0]).__name__}")

    elif func_name == "SECOND":
        if len(args) != 1:
            raise TypeError(f"SECOND expects 1 argument, got {len(args)}")
        if isinstance(args[0], (CypherDateTime, CypherTime)):
            return CypherInt(args[0].value.second)
        else:
            raise TypeError(f"SECOND expects datetime or time, got {type(args[0]).__name__}")

    raise ValueError(f"Unknown temporal function: {func_name}")
