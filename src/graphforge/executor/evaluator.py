"""Expression evaluator for query execution.

This module evaluates AST expressions in an execution context to produce
CypherValue results.
"""

from collections.abc import Sequence
from typing import Any

from graphforge.ast.expression import (
    BinaryOp,
    CaseExpression,
    FunctionCall,
    ListComprehension,
    Literal,
    PropertyAccess,
    QuantifierExpression,
    SubqueryExpression,
    UnaryOp,
    Variable,
)
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import (
    CypherBool,
    CypherDate,
    CypherDateTime,
    CypherDistance,
    CypherDuration,
    CypherFloat,
    CypherInt,
    CypherList,
    CypherMap,
    CypherNull,
    CypherPoint,
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


def evaluate_expression(expr: Any, ctx: ExecutionContext, executor: Any = None) -> CypherValue:
    """Evaluate an AST expression in a context.

    Args:
        expr: AST expression node
        ctx: Execution context with variable bindings
        executor: Optional QueryExecutor instance for subquery evaluation

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
                evaluate_expression(item, ctx, executor)
                if isinstance(
                    item,
                    (
                        Literal,
                        Variable,
                        PropertyAccess,
                        BinaryOp,
                        FunctionCall,
                        CaseExpression,
                        ListComprehension,
                        SubqueryExpression,
                    ),
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
                    val,
                    (
                        Literal,
                        Variable,
                        PropertyAccess,
                        BinaryOp,
                        FunctionCall,
                        CaseExpression,
                        ListComprehension,
                        SubqueryExpression,
                    ),
                ):
                    evaluated_dict[key] = evaluate_expression(val, ctx, executor)
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

        # Handle NULL: accessing property on NULL returns NULL
        if isinstance(obj, CypherNull):
            return CypherNull()

        # Handle NodeRef/EdgeRef
        if isinstance(obj, (NodeRef, EdgeRef)):
            if expr.property in obj.properties:
                return obj.properties[expr.property]  # type: ignore[no-any-return]
            return CypherNull()

        raise TypeError(f"Cannot access property on {type(obj).__name__}")

    # Unary operations
    if isinstance(expr, UnaryOp):
        operand_val = evaluate_expression(expr.operand, ctx, executor)

        # IS NULL operator
        if expr.op == "IS NULL":
            return CypherBool(isinstance(operand_val, CypherNull))

        # IS NOT NULL operator
        if expr.op == "IS NOT NULL":
            return CypherBool(not isinstance(operand_val, CypherNull))

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
        left_val = evaluate_expression(expr.left, ctx, executor)
        right_val = evaluate_expression(expr.right, ctx, executor)

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
            condition_val = evaluate_expression(condition_expr, ctx, executor)

            # NULL is treated as false, not propagated
            if isinstance(condition_val, CypherBool) and condition_val.value:
                return evaluate_expression(result_expr, ctx, executor)

        # No WHEN matched - return ELSE or NULL
        if expr.else_expr is not None:
            return evaluate_expression(expr.else_expr, ctx, executor)

        return CypherNull()

    # List comprehensions
    if isinstance(expr, ListComprehension):
        # Evaluate the list expression
        list_val = evaluate_expression(expr.list_expr, ctx, executor)

        # Must be a list
        if not isinstance(list_val, CypherList):
            raise TypeError(f"IN requires a list, got {type(list_val).__name__}")

        items: list[CypherValue] = []
        for item in list_val.value:
            # Create new context with loop variable bound
            new_ctx = ExecutionContext()
            new_ctx.bindings = dict(ctx.bindings)
            new_ctx.bind(expr.variable, item)

            # Apply filter if present
            if expr.filter_expr is not None:
                filter_val = evaluate_expression(expr.filter_expr, new_ctx, executor)
                # Skip if filter is false or NULL
                if not (isinstance(filter_val, CypherBool) and filter_val.value):
                    continue

            # Apply map transformation if present, otherwise use item as-is
            if expr.map_expr is not None:
                result_val = evaluate_expression(expr.map_expr, new_ctx, executor)
            else:
                result_val = item

            items.append(result_val)

        return CypherList(items)

    # Quantifier expressions (ALL, ANY, NONE, SINGLE)
    if isinstance(expr, QuantifierExpression):
        # Evaluate the list expression
        list_val = evaluate_expression(expr.list_expr, ctx, executor)

        # Must be a list
        if not isinstance(list_val, CypherList):
            raise TypeError(f"Quantifier requires a list, got {type(list_val).__name__}")

        # Count satisfied items and track NULL predicates (three-valued logic)
        satisfied_count = 0
        false_count = 0
        null_count = 0

        for item in list_val.value:
            # Create new context with loop variable bound
            new_ctx = ExecutionContext()
            new_ctx.bindings = dict(ctx.bindings)
            new_ctx.bind(expr.variable, item)

            # Evaluate predicate
            predicate_val = evaluate_expression(expr.predicate, new_ctx, executor)

            # Track predicate results with three-valued logic
            if isinstance(predicate_val, CypherBool):
                if predicate_val.value:
                    satisfied_count += 1
                else:
                    false_count += 1
            elif isinstance(predicate_val, CypherNull):
                null_count += 1
            else:
                # Non-boolean, non-null result counts as NULL (unknown)
                null_count += 1

        # Apply quantifier logic with openCypher three-valued semantics
        list_length = len(list_val.value)

        if expr.quantifier == "ALL":
            # ALL: False if any False, True if empty or all True, else NULL
            if false_count > 0:
                return CypherBool(False)
            elif list_length == 0 or (satisfied_count == list_length):  # noqa: PLR1714
                return CypherBool(True)
            else:  # No False, but at least one NULL
                return CypherNull()

        elif expr.quantifier == "ANY":
            # ANY: True if any True, NULL if any NULL but no True, else False
            if satisfied_count > 0:
                return CypherBool(True)
            elif null_count > 0:
                return CypherNull()
            else:
                return CypherBool(False)

        elif expr.quantifier == "NONE":
            # NONE: False if any True, NULL if any NULL but no True, else True
            if satisfied_count > 0:
                return CypherBool(False)
            elif null_count > 0:
                return CypherNull()
            else:
                return CypherBool(True)

        elif expr.quantifier == "SINGLE":
            # SINGLE: True if exactly one True and no NULLs,
            # False if more than one True,
            # NULL if zero True and any NULL,
            # else False
            if satisfied_count == 1 and null_count == 0:
                return CypherBool(True)
            elif satisfied_count > 1:
                return CypherBool(False)
            elif satisfied_count == 0 and null_count > 0:
                return CypherNull()
            else:
                return CypherBool(False)

        else:
            raise ValueError(f"Unknown quantifier: {expr.quantifier}")

    # Subquery expressions (EXISTS, COUNT)
    if isinstance(expr, SubqueryExpression):
        if executor is None:
            raise TypeError("Subquery expressions require executor parameter")

        if executor.planner is None:
            raise TypeError("Subquery expressions require executor with planner configured")

        # Plan the nested query
        operators = executor.planner.plan(expr.query)

        # Create a new execution context with current bindings (correlated subquery)
        subquery_ctx = ExecutionContext()
        subquery_ctx.bindings = dict(ctx.bindings)

        # Execute the subquery
        subquery_rows = [subquery_ctx]
        for i, op in enumerate(operators):
            subquery_rows = executor._execute_operator(op, subquery_rows, i, len(operators))

        # Return result based on subquery type
        if expr.type == "EXISTS":
            return CypherBool(len(subquery_rows) > 0)
        elif expr.type == "COUNT":
            return CypherInt(len(subquery_rows))
        else:
            raise ValueError(f"Unknown subquery type: {expr.type}")

    # Function calls
    if isinstance(expr, FunctionCall):
        return _evaluate_function(expr, ctx, executor)

    raise TypeError(f"Cannot evaluate expression type: {type(expr).__name__}")


# Function categories
STRING_FUNCTIONS = {"LENGTH", "SUBSTRING", "UPPER", "LOWER", "TRIM"}
TYPE_FUNCTIONS = {"TOBOOLEAN", "TOINTEGER", "TOFLOAT", "TOSTRING", "TYPE"}
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
SPATIAL_FUNCTIONS = {"POINT", "DISTANCE"}
GRAPH_FUNCTIONS = {"ID", "LABELS"}


def _evaluate_function(
    func_call: FunctionCall, ctx: ExecutionContext, executor: Any = None
) -> CypherValue:
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
        args = [evaluate_expression(arg, ctx, executor) for arg in func_call.args]
        for arg in args:
            if not isinstance(arg, CypherNull):
                return arg
        return CypherNull()

    # Graph functions need special handling for NodeRef/EdgeRef arguments
    if func_name in GRAPH_FUNCTIONS:
        args = [evaluate_expression(arg, ctx, executor) for arg in func_call.args]
        return _evaluate_graph_function(func_name, args)

    # Evaluate arguments
    args = [evaluate_expression(arg, ctx, executor) for arg in func_call.args]

    # NULL propagation: if any arg is NULL, return NULL (for most functions)
    if any(isinstance(arg, CypherNull) for arg in args):
        return CypherNull()

    # SIZE function for lists and strings
    if func_name == "SIZE":
        arg = args[0]
        if isinstance(arg, CypherList):
            return CypherInt(len(arg.value))
        elif isinstance(arg, CypherString):
            return CypherInt(len(arg.value))
        else:
            raise TypeError(f"SIZE expects list or string, got {type(arg).__name__}")

    # Dispatch to specific function handlers
    if func_name in STRING_FUNCTIONS:
        return _evaluate_string_function(func_name, args)
    elif func_name in TYPE_FUNCTIONS:
        return _evaluate_type_function(func_name, args)
    elif func_name in TEMPORAL_FUNCTIONS:
        return _evaluate_temporal_function(func_name, args)
    elif func_name in SPATIAL_FUNCTIONS:
        return _evaluate_spatial_function(func_name, args)
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

    if func_name == "TOBOOLEAN":
        try:
            if isinstance(args[0], CypherBool):
                return args[0]
            elif isinstance(args[0], CypherString):
                # Only "true" and "false" (case-insensitive) convert to boolean
                value_lower = args[0].value.lower()
                if value_lower == "true":
                    return CypherBool(True)
                elif value_lower == "false":
                    return CypherBool(False)
                else:
                    return CypherNull()  # Invalid string
            else:
                return CypherNull()  # Cannot convert other types
        except (ValueError, TypeError):
            return CypherNull()

    elif func_name == "TOINTEGER":
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
        # TYPE function - dual purpose:
        # 1. For relationships: returns relationship type string
        # 2. For values: returns the CypherValue type name

        arg = args[0]

        # Handle EdgeRef (relationship) by checking if it has both 'type' and 'src' attributes
        # EdgeRef is not a CypherValue subclass, it's a separate runtime reference type
        if hasattr(arg, "src") and hasattr(arg, "type"):
            # This is an EdgeRef - return its relationship type
            edge_ref: EdgeRef = arg  # type: ignore[assignment]
            return CypherString(edge_ref.type)

        # Handle CypherValue type introspection
        type_name = type(arg).__name__
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


def _evaluate_spatial_function(func_name: str, args: list[CypherValue]) -> CypherValue:
    """Evaluate spatial functions.

    Args:
        func_name: Name of the spatial function (uppercase)
        args: List of evaluated arguments (non-NULL)

    Returns:
        CypherValue result of the spatial function

    Raises:
        ValueError: If function is unknown
        TypeError: If arguments have invalid types
    """
    if func_name == "POINT":
        # point({x: 1.0, y: 2.0}) or point({latitude: 51.5, longitude: -0.1})
        if len(args) != 1:
            raise TypeError(f"POINT expects 1 argument, got {len(args)}")
        if not isinstance(args[0], CypherMap):
            raise TypeError(f"POINT expects map argument, got {type(args[0]).__name__}")

        # Convert CypherMap to dict of Python floats
        coordinates = {}
        for key, val in args[0].value.items():
            if isinstance(val, (CypherInt, CypherFloat)):
                coordinates[key] = float(val.value)
            else:
                raise TypeError(
                    f"POINT coordinate '{key}' must be numeric, got {type(val).__name__}"
                )

        return CypherPoint(coordinates)

    elif func_name == "DISTANCE":
        # distance(point1, point2)
        if len(args) != 2:
            raise TypeError(f"DISTANCE expects 2 arguments, got {len(args)}")
        if not isinstance(args[0], CypherPoint):
            raise TypeError(f"DISTANCE first argument must be point, got {type(args[0]).__name__}")
        if not isinstance(args[1], CypherPoint):
            raise TypeError(f"DISTANCE second argument must be point, got {type(args[1]).__name__}")

        p1 = args[0].value
        p2 = args[1].value

        # Check if both points use the same coordinate reference system
        if p1["crs"] != p2["crs"]:
            raise ValueError(
                f"Cannot calculate distance between points with different CRS: "
                f"{p1['crs']} and {p2['crs']}"
            )

        if p1["crs"] == "wgs-84":
            # Use Haversine formula for geographic coordinates
            distance = _haversine_distance(
                p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"]
            )
        elif p1["crs"] == "cartesian":
            # 2D Euclidean distance
            dx = p2["x"] - p1["x"]
            dy = p2["y"] - p1["y"]
            distance = (dx**2 + dy**2) ** 0.5
        elif p1["crs"] == "cartesian-3d":
            # 3D Euclidean distance
            dx = p2["x"] - p1["x"]
            dy = p2["y"] - p1["y"]
            dz = p2["z"] - p1["z"]
            distance = (dx**2 + dy**2 + dz**2) ** 0.5
        else:
            raise ValueError(f"Unknown coordinate reference system: {p1['crs']}")

        return CypherDistance(distance)

    raise ValueError(f"Unknown spatial function: {func_name}")


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two WGS-84 points using Haversine formula.

    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees

    Returns:
        Distance in meters
    """
    import math

    # Earth radius in meters
    earth_radius = 6371000

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c


def _evaluate_graph_function(
    func_name: str, args: Sequence[NodeRef | EdgeRef | CypherValue]
) -> CypherValue:
    """Evaluate graph element functions.

    These functions work with graph elements (nodes, relationships) rather than
    just CypherValues. They handle NodeRef and EdgeRef objects directly.

    Args:
        func_name: Name of the graph function (uppercase)
        args: List of evaluated arguments (may include NodeRef/EdgeRef)

    Returns:
        CypherValue result of the graph function

    Raises:
        ValueError: If function is unknown
        TypeError: If arguments have invalid types
    """
    if func_name == "ID":
        # id(node) or id(relationship)
        if len(args) != 1:
            raise TypeError(f"ID expects 1 argument, got {len(args)}")

        arg = args[0]

        # Handle NULL
        if isinstance(arg, CypherNull):
            return CypherNull()

        # Check if argument is a node or relationship
        if isinstance(arg, (NodeRef, EdgeRef)):
            # Return the internal ID as an integer
            id_value = arg.id
            # ID might be int or str, convert to int if string
            if isinstance(id_value, str):
                try:
                    id_value = int(id_value)
                except ValueError:
                    # If ID is a non-numeric string, hash it to get an int
                    id_value = hash(id_value)
            return CypherInt(id_value)

        raise TypeError(f"ID expects node or relationship argument, got {type(arg).__name__}")

    if func_name == "LABELS":
        # labels(node) - returns list of label strings for a node
        if len(args) != 1:
            raise TypeError(f"LABELS expects 1 argument, got {len(args)}")

        arg = args[0]

        # Handle NULL
        if isinstance(arg, CypherNull):
            return CypherNull()

        # Check if argument is a node
        if isinstance(arg, NodeRef):
            # Return labels as a sorted list of CypherStrings
            labels_list: list[CypherValue] = [CypherString(label) for label in sorted(arg.labels)]
            return CypherList(labels_list)

        raise TypeError(f"LABELS expects node argument, got {type(arg).__name__}")

    raise ValueError(f"Unknown graph function: {func_name}")
