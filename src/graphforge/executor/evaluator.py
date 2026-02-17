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
    Subscript,
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
    CypherPath,
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
                        Subscript,
                        BinaryOp,
                        UnaryOp,
                        FunctionCall,
                        CaseExpression,
                        ListComprehension,
                        QuantifierExpression,
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
                        Subscript,
                        BinaryOp,
                        UnaryOp,
                        FunctionCall,
                        CaseExpression,
                        ListComprehension,
                        QuantifierExpression,
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
        # Get the base object: either from variable or evaluate base expression
        if expr.variable:
            obj = ctx.get(expr.variable)
        elif expr.base:
            obj = evaluate_expression(expr.base, ctx, executor)
        else:
            raise ValueError("PropertyAccess must have either variable or base")

        # Handle NULL: accessing property on NULL returns NULL
        if isinstance(obj, CypherNull):
            return CypherNull()

        # Handle NodeRef/EdgeRef
        if isinstance(obj, (NodeRef, EdgeRef)):
            if expr.property in obj.properties:
                return obj.properties[expr.property]  # type: ignore[no-any-return]
            return CypherNull()

        # Handle CypherMap property access (Issue #173)
        if isinstance(obj, CypherMap):
            if expr.property in obj.value:
                return obj.value[expr.property]  # type: ignore[no-any-return]
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
        # For AND/OR, implement short-circuit evaluation
        # Other operators need both operands evaluated
        if expr.op in ("AND", "OR"):
            left_val = evaluate_expression(expr.left, ctx, executor)

            # Three-valued short-circuit semantics for AND
            if expr.op == "AND":
                # false AND anything = false (short-circuit)
                if isinstance(left_val, CypherBool) and not left_val.value:
                    return CypherBool(False)

                # Evaluate right operand
                right_val = evaluate_expression(expr.right, ctx, executor)

                # true AND x = x (return right as-is, could be true/false/NULL)
                if isinstance(left_val, CypherBool) and left_val.value:
                    if isinstance(right_val, (CypherBool, CypherNull)):
                        return right_val
                    raise TypeError("AND requires boolean operands")

                # NULL AND false = false
                if isinstance(left_val, CypherNull):
                    if isinstance(right_val, CypherBool) and not right_val.value:
                        return CypherBool(False)
                    # NULL AND true = NULL, NULL AND NULL = NULL
                    if isinstance(right_val, (CypherBool, CypherNull)):
                        return CypherNull()
                    raise TypeError("AND requires boolean operands")

                raise TypeError("AND requires boolean operands")

            # Three-valued short-circuit semantics for OR
            if expr.op == "OR":
                # true OR anything = true (short-circuit)
                if isinstance(left_val, CypherBool) and left_val.value:
                    return CypherBool(True)

                # Evaluate right operand
                right_val = evaluate_expression(expr.right, ctx, executor)

                # false OR x = x (return right as-is, could be true/false/NULL)
                if isinstance(left_val, CypherBool) and not left_val.value:
                    if isinstance(right_val, (CypherBool, CypherNull)):
                        return right_val
                    raise TypeError("OR requires boolean operands")

                # NULL OR true = true
                if isinstance(left_val, CypherNull):
                    if isinstance(right_val, CypherBool) and right_val.value:
                        return CypherBool(True)
                    # NULL OR false = NULL, NULL OR NULL = NULL
                    if isinstance(right_val, (CypherBool, CypherNull)):
                        return CypherNull()
                    raise TypeError("OR requires boolean operands")

                raise TypeError("OR requires boolean operands")

        # For all other operators, evaluate both operands
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

        # IN operator: value IN list
        if expr.op == "IN":
            # anything IN NULL → NULL
            if isinstance(right_val, CypherNull):
                return CypherNull()

            # Right operand must be a list
            if not isinstance(right_val, CypherList):
                raise TypeError(
                    f"IN operator requires a list on the right side, got {type(right_val).__name__}"
                )

            # Empty list: value IN [] → false (even for NULL IN [])
            # This must come before NULL check on left operand
            if not right_val.value:
                return CypherBool(False)

            # NULL IN non-empty-list → NULL
            if isinstance(left_val, CypherNull):
                return CypherNull()

            # Check if left_val is in the list
            # Use three-valued logic: if any comparison is NULL and no match found, return NULL
            has_null = False
            for item in right_val.value:
                result = left_val.equals(item)
                if isinstance(result, CypherBool):
                    if result.value:
                        return CypherBool(True)  # Found a match
                elif isinstance(result, CypherNull):
                    has_null = True  # Track that we saw a NULL comparison

            # No match found: return NULL if we saw any NULL comparisons, else false
            return CypherNull() if has_null else CypherBool(False)

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

            # Temporal arithmetic: datetime + duration, datetime - duration, datetime - datetime
            if expr.op in ("+", "-"):
                # Addition: temporal + duration or duration + temporal
                if expr.op == "+":
                    if isinstance(
                        left_val, (CypherDateTime, CypherDate, CypherTime)
                    ) and isinstance(right_val, CypherDuration):
                        return _add_duration(left_val, right_val)
                    elif isinstance(left_val, CypherDuration) and isinstance(
                        right_val, (CypherDateTime, CypherDate, CypherTime)
                    ):
                        return _add_duration(right_val, left_val)

                # Subtraction: temporal - duration or temporal - temporal
                if expr.op == "-":
                    if isinstance(
                        left_val, (CypherDateTime, CypherDate, CypherTime)
                    ) and isinstance(right_val, CypherDuration):
                        return _subtract_duration(left_val, right_val)
                    elif isinstance(left_val, (CypherDateTime, CypherDate)) and isinstance(
                        right_val, (CypherDateTime, CypherDate)
                    ):
                        return _duration_between(left_val, right_val)

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

        # NULL list returns NULL (three-valued logic)
        if isinstance(list_val, CypherNull):
            return CypherNull()

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
            # NULL if any NULL exists (can't determine uniqueness)
            if satisfied_count == 1 and null_count == 0:
                return CypherBool(True)
            elif satisfied_count > 1:
                return CypherBool(False)
            elif null_count > 0:
                # Can't determine uniqueness when NULLs exist
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

    # Subscript operations (list indexing and slicing)
    if isinstance(expr, Subscript):
        return _evaluate_subscript(expr, ctx, executor)

    # Function calls
    if isinstance(expr, FunctionCall):
        return _evaluate_function(expr, ctx, executor)

    raise TypeError(f"Cannot evaluate expression type: {type(expr).__name__}")


# Function categories
STRING_FUNCTIONS = {
    "LENGTH",
    "SUBSTRING",
    "UPPER",
    "LOWER",
    "TRIM",
    "REVERSE",
    "SPLIT",
    "REPLACE",
    "LEFT",
    "RIGHT",
    "LTRIM",
    "RTRIM",
}
LIST_FUNCTIONS = {"TAIL", "HEAD", "LAST", "REVERSE", "RANGE", "SIZE"}
TYPE_FUNCTIONS = {"TOBOOLEAN", "TOINTEGER", "TOFLOAT", "TOSTRING", "TYPE"}
TEMPORAL_FUNCTIONS = {
    "DATE",
    "DATETIME",
    "LOCALDATETIME",
    "TIME",
    "LOCALTIME",
    "DURATION",
    "YEAR",
    "MONTH",
    "DAY",
    "HOUR",
    "MINUTE",
    "SECOND",
    "TRUNCATE",
}
SPATIAL_FUNCTIONS = {"POINT", "DISTANCE"}
MATH_FUNCTIONS = {"ABS", "CEIL", "FLOOR", "ROUND", "SIGN"}
GRAPH_FUNCTIONS = {"ID", "LABELS"}
PATH_FUNCTIONS = {"LENGTH", "NODES", "RELATIONSHIPS", "HEAD", "LAST"}
AGGREGATE_FUNCTIONS = {
    "COUNT",
    "SUM",
    "AVG",
    "MAX",
    "MIN",
    "COLLECT",
    "PERCENTILEDISC",
    "PERCENTILECONT",
    "STDEV",
    "STDEVP",
}


def is_aggregate_function(expr: Any) -> bool:
    """Check if an expression is an aggregate function call.

    Args:
        expr: AST expression node

    Returns:
        True if expr is an aggregate function call, False otherwise
    """
    if not isinstance(expr, FunctionCall):
        return False
    return expr.name.upper() in AGGREGATE_FUNCTIONS


def _add_duration(temporal: CypherValue, duration: CypherDuration) -> CypherValue:
    """Add duration to temporal value.

    Args:
        temporal: CypherDateTime, CypherDate, or CypherTime
        duration: CypherDuration to add

    Returns:
        New temporal value with duration added
    """
    import datetime

    import isodate  # type: ignore[import-untyped]

    duration_val = duration.value

    if isinstance(temporal, CypherDateTime):
        # Add duration to datetime, preserving timezone
        dt = temporal.value
        if isinstance(duration_val, isodate.Duration):
            # isodate.Duration with years/months - needs calendar arithmetic
            result = duration_val + dt
        else:
            # timedelta - simple addition
            result = dt + duration_val
        return CypherDateTime(result)

    elif isinstance(temporal, CypherDate):
        # Add duration to date
        date_val = temporal.value
        if isinstance(duration_val, isodate.Duration):
            # Convert date to datetime for isodate arithmetic, then back to date
            dt = datetime.datetime.combine(date_val, datetime.time.min)
            result_dt = duration_val + dt
            return CypherDate(result_dt.date())
        else:
            # timedelta - simple addition
            result = date_val + duration_val
            return CypherDate(result)

    elif isinstance(temporal, CypherTime):
        # Add duration to time (ignores date components of duration)
        time_val = temporal.value
        if isinstance(duration_val, isodate.Duration):
            # Extract timedelta component from isodate.Duration
            td = duration_val.tdelta if hasattr(duration_val, "tdelta") else datetime.timedelta()
        else:
            td = duration_val

        # Combine time with fixed sentinel date, add timedelta, extract time with timezone
        # Use fixed date (2000-01-01) for deterministic computation
        dt = datetime.datetime.combine(datetime.date(2000, 1, 1), time_val)
        result_dt = dt + td
        # Preserve timezone with timetz()
        return CypherTime(result_dt.timetz())

    else:
        raise TypeError(
            f"Cannot add duration to {type(temporal).__name__}, "
            "expected CypherDateTime, CypherDate, or CypherTime"
        )


def _subtract_duration(temporal: CypherValue, duration: CypherDuration) -> CypherValue:
    """Subtract duration from temporal value.

    Args:
        temporal: CypherDateTime, CypherDate, or CypherTime
        duration: CypherDuration to subtract

    Returns:
        New temporal value with duration subtracted
    """
    import datetime

    import isodate

    duration_val = duration.value

    if isinstance(temporal, CypherDateTime):
        # Subtract duration from datetime, preserving timezone
        dt = temporal.value
        if isinstance(duration_val, isodate.Duration):
            # isodate.Duration with years/months - needs calendar arithmetic
            # Negate the duration components
            negated = isodate.Duration(
                years=-duration_val.years if hasattr(duration_val, "years") else 0,
                months=-duration_val.months if hasattr(duration_val, "months") else 0,
            )
            if hasattr(duration_val, "tdelta"):
                result = dt + negated - duration_val.tdelta
            else:
                result = dt + negated
        else:
            # timedelta - simple subtraction
            result = dt - duration_val
        return CypherDateTime(result)

    elif isinstance(temporal, CypherDate):
        # Subtract duration from date
        date_val = temporal.value
        if isinstance(duration_val, isodate.Duration):
            # Convert date to datetime for isodate arithmetic, then back to date
            dt = datetime.datetime.combine(date_val, datetime.time.min)
            negated = isodate.Duration(
                years=-duration_val.years if hasattr(duration_val, "years") else 0,
                months=-duration_val.months if hasattr(duration_val, "months") else 0,
            )
            if hasattr(duration_val, "tdelta"):
                result_dt = dt + negated - duration_val.tdelta
            else:
                result_dt = dt + negated
            return CypherDate(result_dt.date())
        else:
            # timedelta - simple subtraction
            result = date_val - duration_val
            return CypherDate(result)

    elif isinstance(temporal, CypherTime):
        # Subtract duration from time (ignores date components of duration)
        time_val = temporal.value
        if isinstance(duration_val, isodate.Duration):
            # Extract timedelta component from isodate.Duration
            td = duration_val.tdelta if hasattr(duration_val, "tdelta") else datetime.timedelta()
        else:
            td = duration_val

        # Combine time with fixed sentinel date, subtract timedelta, extract time with timezone
        # Use fixed date (2000-01-01) for deterministic computation
        dt = datetime.datetime.combine(datetime.date(2000, 1, 1), time_val)
        result_dt = dt - td
        # Preserve timezone with timetz()
        return CypherTime(result_dt.timetz())

    else:
        raise TypeError(
            f"Cannot subtract duration from {type(temporal).__name__}, "
            "expected CypherDateTime, CypherDate, or CypherTime"
        )


def _duration_between(left: CypherValue, right: CypherValue) -> CypherDuration:
    """Calculate duration between two temporal values (left - right).

    Args:
        left: CypherDateTime or CypherDate (minuend)
        right: CypherDateTime or CypherDate (subtrahend)

    Returns:
        CypherDuration representing the time difference (left - right)
    """
    import datetime

    # Convert to comparable datetime objects
    if isinstance(left, CypherDate):
        left_dt = datetime.datetime.combine(left.value, datetime.time.min)
    elif isinstance(left, CypherDateTime):
        left_dt = left.value
    else:
        raise TypeError(f"Cannot calculate duration from {type(left).__name__}")

    if isinstance(right, CypherDate):
        right_dt = datetime.datetime.combine(right.value, datetime.time.min)
    elif isinstance(right, CypherDateTime):
        right_dt = right.value
    else:
        raise TypeError(f"Cannot calculate duration to {type(right).__name__}")

    # Normalize timezone awareness: if one is tz-aware and the other is naive,
    # make both aware using the same timezone
    if left_dt.tzinfo is not None and right_dt.tzinfo is None:
        # Left is aware, right is naive - attach left's timezone to right
        right_dt = right_dt.replace(tzinfo=left_dt.tzinfo)
    elif left_dt.tzinfo is None and right_dt.tzinfo is not None:
        # Left is naive, right is aware - attach right's timezone to left
        left_dt = left_dt.replace(tzinfo=right_dt.tzinfo)

    # Calculate timedelta: left - right
    duration = left_dt - right_dt
    return CypherDuration(duration)


def _truncate_temporal(temporal: CypherValue, unit: str) -> CypherValue:
    """Truncate temporal value to specified unit.

    Args:
        temporal: CypherDateTime, CypherDate, or CypherTime
        unit: Truncation unit ('year', 'month', 'day', 'hour', 'minute', 'second',
              'millisecond', 'microsecond')

    Returns:
        Truncated temporal value

    Raises:
        ValueError: If unit is invalid
        TypeError: If temporal type doesn't support the unit
    """
    import datetime

    valid_units = {
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "second",
        "millisecond",
        "microsecond",
    }
    if unit not in valid_units:
        raise ValueError(
            f"Invalid truncation unit: {unit}. Valid units: {', '.join(sorted(valid_units))}"
        )

    if isinstance(temporal, CypherDateTime):
        dt = temporal.value
        tz = dt.tzinfo

        dt_result: datetime.datetime
        if unit == "year":
            dt_result = datetime.datetime(dt.year, 1, 1, 0, 0, 0, 0, tz)
        elif unit == "month":
            dt_result = datetime.datetime(dt.year, dt.month, 1, 0, 0, 0, 0, tz)
        elif unit == "day":
            dt_result = datetime.datetime(dt.year, dt.month, dt.day, 0, 0, 0, 0, tz)
        elif unit == "hour":
            dt_result = datetime.datetime(dt.year, dt.month, dt.day, dt.hour, 0, 0, 0, tz)
        elif unit == "minute":
            dt_result = datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, 0, 0, tz)
        elif unit == "second":
            dt_result = datetime.datetime(
                dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, 0, tz
            )
        elif unit == "millisecond":
            # Truncate microseconds to millisecond boundary
            ms = dt.microsecond // 1000 * 1000
            dt_result = datetime.datetime(
                dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, ms, tz
            )
        elif unit == "microsecond":
            # Keep existing datetime as-is (already at microsecond precision)
            dt_result = dt
        else:
            raise ValueError(f"Invalid unit for datetime truncation: {unit}")

        return CypherDateTime(dt_result)

    elif isinstance(temporal, CypherDate):
        date_val = temporal.value

        date_result: datetime.date
        if unit == "year":
            date_result = datetime.date(date_val.year, 1, 1)
        elif unit == "month":
            date_result = datetime.date(date_val.year, date_val.month, 1)
        elif unit == "day":
            date_result = date_val  # Already at day precision
        else:
            raise TypeError(
                f"Cannot truncate date to {unit}. "
                "Date only supports truncation to: year, month, day"
            )

        return CypherDate(date_result)

    elif isinstance(temporal, CypherTime):
        time_val = temporal.value
        tz = time_val.tzinfo

        time_result: datetime.time
        if unit == "hour":
            time_result = datetime.time(time_val.hour, 0, 0, 0, tz)
        elif unit == "minute":
            time_result = datetime.time(time_val.hour, time_val.minute, 0, 0, tz)
        elif unit == "second":
            time_result = datetime.time(time_val.hour, time_val.minute, time_val.second, 0, tz)
        elif unit == "millisecond":
            # Truncate microseconds to millisecond boundary
            ms = time_val.microsecond // 1000 * 1000
            time_result = datetime.time(time_val.hour, time_val.minute, time_val.second, ms, tz)
        elif unit == "microsecond":
            # Keep existing time as-is (already at microsecond precision)
            time_result = time_val
        else:
            raise TypeError(
                f"Cannot truncate time to {unit}. "
                "Time only supports truncation to: hour, minute, second, millisecond, microsecond"
            )

        return CypherTime(time_result)

    else:
        raise TypeError(
            f"Cannot truncate {type(temporal).__name__}, "
            "expected CypherDateTime, CypherDate, or CypherTime"
        )


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

    # Check for custom registered functions first
    if (
        executor
        and hasattr(executor, "custom_functions")
        and func_name in executor.custom_functions
    ):
        from typing import cast

        custom_func = executor.custom_functions[func_name]
        # Evaluate arguments
        args = [evaluate_expression(arg, ctx, executor) for arg in func_call.args]
        # Call the custom function
        result = custom_func(args, ctx, executor)
        return cast(CypherValue, result)

    # COALESCE is special - it doesn't propagate NULL, returns first non-NULL value
    if func_name == "COALESCE":
        args = [evaluate_expression(arg, ctx, executor) for arg in func_call.args]
        for arg in args:
            if not isinstance(arg, CypherNull):
                return arg
        return CypherNull()

    # LENGTH is overloaded - works for both strings and paths
    if func_name == "LENGTH":
        args = [evaluate_expression(arg, ctx, executor) for arg in func_call.args]
        arg = args[0]
        if isinstance(arg, CypherNull):
            return CypherNull()
        if isinstance(arg, CypherPath):
            return _evaluate_path_function(func_name, args)
        if isinstance(arg, CypherString):
            return _evaluate_string_function(func_name, args)
        raise TypeError(f"LENGTH expects string or path argument, got {type(arg).__name__}")

    # HEAD is overloaded - works for both lists and paths
    if func_name == "HEAD":
        args = [evaluate_expression(arg, ctx, executor) for arg in func_call.args]
        arg = args[0]
        if isinstance(arg, CypherNull):
            return CypherNull()
        if isinstance(arg, CypherPath):
            return _evaluate_path_function(func_name, args)
        if isinstance(arg, CypherList):
            return _evaluate_list_function(func_name, args)
        raise TypeError(f"HEAD expects list or path argument, got {type(arg).__name__}")

    # LAST is overloaded - works for both lists and paths
    if func_name == "LAST":
        args = [evaluate_expression(arg, ctx, executor) for arg in func_call.args]
        arg = args[0]
        if isinstance(arg, CypherNull):
            return CypherNull()
        if isinstance(arg, CypherPath):
            return _evaluate_path_function(func_name, args)
        if isinstance(arg, CypherList):
            return _evaluate_list_function(func_name, args)
        raise TypeError(f"LAST expects list or path argument, got {type(arg).__name__}")

    # REVERSE is overloaded - works for both lists and strings
    if func_name == "REVERSE":
        args = [evaluate_expression(arg, ctx, executor) for arg in func_call.args]
        arg = args[0]
        if isinstance(arg, CypherNull):
            return CypherNull()
        if isinstance(arg, CypherList):
            return _evaluate_list_function(func_name, args)
        if isinstance(arg, CypherString):
            return _evaluate_string_function(func_name, args)
        raise TypeError(f"REVERSE expects list or string argument, got {type(arg).__name__}")

    # Graph functions need special handling for NodeRef/EdgeRef arguments
    if func_name in GRAPH_FUNCTIONS:
        args = [evaluate_expression(arg, ctx, executor) for arg in func_call.args]
        return _evaluate_graph_function(func_name, args)

    # Path functions need special handling for CypherPath arguments
    if func_name in PATH_FUNCTIONS:
        args = [evaluate_expression(arg, ctx, executor) for arg in func_call.args]
        return _evaluate_path_function(func_name, args)

    # EXISTS function for property existence checking
    # Must be evaluated BEFORE NULL propagation to handle property access correctly
    if func_name == "EXISTS":
        # exists() checks if a property exists on a node/relationship
        # For property access expressions, check if property is NULL
        if len(func_call.args) != 1:
            raise ValueError("EXISTS expects exactly one argument")

        arg_expr = func_call.args[0]

        # If the argument is a property access, evaluate and check for NULL
        if isinstance(arg_expr, PropertyAccess):
            result = evaluate_expression(arg_expr, ctx, executor)
            # exists() returns false if property is NULL, true otherwise
            return CypherBool(not isinstance(result, CypherNull))

        # For other expressions, evaluate and check if NULL
        result = evaluate_expression(arg_expr, ctx, executor)
        return CypherBool(not isinstance(result, CypherNull))

    # Evaluate arguments
    args = [evaluate_expression(arg, ctx, executor) for arg in func_call.args]

    # NULL propagation: if any arg is NULL, return NULL (for most functions)
    if any(isinstance(arg, CypherNull) for arg in args):
        return CypherNull()

    # SIZE function for lists and strings
    if func_name == "SIZE":
        arg = args[0]
        if isinstance(arg, (CypherList, CypherString)):
            return CypherInt(len(arg.value))
        raise TypeError(f"SIZE expects list or string, got {type(arg).__name__}")

    # ISEMPTY function for lists, strings, and maps
    if func_name == "ISEMPTY":
        arg = args[0]
        if isinstance(arg, (CypherList, CypherString)):
            return CypherBool(len(arg.value) == 0)
        if isinstance(arg, CypherMap):
            return CypherBool(len(arg.value) == 0)
        raise TypeError(f"ISEMPTY expects list, string, or map, got {type(arg).__name__}")

    # Dispatch to specific function handlers
    if func_name in STRING_FUNCTIONS:
        return _evaluate_string_function(func_name, args)
    elif func_name in LIST_FUNCTIONS:
        return _evaluate_list_function(func_name, args)
    elif func_name in MATH_FUNCTIONS:
        return _evaluate_math_function(func_name, args)
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

    elif func_name == "REVERSE":
        if not isinstance(args[0], CypherString):
            raise TypeError(f"REVERSE expects string, got {type(args[0]).__name__}")
        return CypherString(args[0].value[::-1])

    elif func_name == "SPLIT":
        # SPLIT(string, delimiter) -> list of strings
        if len(args) != 2:
            raise TypeError(f"SPLIT expects 2 arguments, got {len(args)}")
        if not isinstance(args[0], CypherString):
            raise TypeError(f"SPLIT expects string as first argument, got {type(args[0]).__name__}")
        if not isinstance(args[1], CypherString):
            raise TypeError(f"SPLIT expects string as delimiter, got {type(args[1]).__name__}")

        string = args[0].value
        delimiter = args[1].value

        # Split the string
        parts = string.split(delimiter)
        return CypherList([CypherString(part) for part in parts])

    elif func_name == "REPLACE":
        # REPLACE(string, search, replacement) -> string
        if len(args) != 3:
            raise TypeError(f"REPLACE expects 3 arguments, got {len(args)}")
        if not isinstance(args[0], CypherString):
            arg_type = type(args[0]).__name__
            raise TypeError(f"REPLACE expects string as first argument, got {arg_type}")
        if not isinstance(args[1], CypherString):
            arg_type = type(args[1]).__name__
            raise TypeError(f"REPLACE expects string as search argument, got {arg_type}")
        if not isinstance(args[2], CypherString):
            arg_type = type(args[2]).__name__
            raise TypeError(f"REPLACE expects string as replacement argument, got {arg_type}")

        string = args[0].value
        search = args[1].value
        replacement = args[2].value

        # Replace all occurrences
        result = string.replace(search, replacement)
        return CypherString(result)

    elif func_name == "LEFT":
        # LEFT(string, length) -> string
        if len(args) != 2:
            raise TypeError(f"LEFT expects 2 arguments, got {len(args)}")
        if not isinstance(args[0], CypherString):
            raise TypeError(f"LEFT expects string as first argument, got {type(args[0]).__name__}")
        if not isinstance(args[1], CypherInt):
            raise TypeError(f"LEFT expects integer as length, got {type(args[1]).__name__}")

        string = args[0].value
        length = args[1].value

        # Negative length returns empty string (openCypher behavior)
        if length < 0:
            return CypherString("")

        return CypherString(string[:length])

    elif func_name == "RIGHT":
        # RIGHT(string, length) -> string
        if len(args) != 2:
            raise TypeError(f"RIGHT expects 2 arguments, got {len(args)}")
        if not isinstance(args[0], CypherString):
            raise TypeError(f"RIGHT expects string as first argument, got {type(args[0]).__name__}")
        if not isinstance(args[1], CypherInt):
            raise TypeError(f"RIGHT expects integer as length, got {type(args[1]).__name__}")

        string = args[0].value
        length = args[1].value

        # Negative or zero length returns empty string (openCypher behavior)
        if length <= 0:
            return CypherString("")

        # If length exceeds string length, return entire string
        if length >= len(string):
            return CypherString(string)

        return CypherString(string[-length:])

    elif func_name == "LTRIM":
        # LTRIM(string) -> string (remove leading whitespace)
        if len(args) != 1:
            raise TypeError(f"LTRIM expects 1 argument, got {len(args)}")
        if not isinstance(args[0], CypherString):
            raise TypeError(f"LTRIM expects string, got {type(args[0]).__name__}")
        return CypherString(args[0].value.lstrip())

    elif func_name == "RTRIM":
        # RTRIM(string) -> string (remove trailing whitespace)
        if len(args) != 1:
            raise TypeError(f"RTRIM expects 1 argument, got {len(args)}")
        if not isinstance(args[0], CypherString):
            raise TypeError(f"RTRIM expects string, got {type(args[0]).__name__}")
        return CypherString(args[0].value.rstrip())

    raise ValueError(f"Unknown string function: {func_name}")


def _evaluate_math_function(func_name: str, args: list[CypherValue]) -> CypherValue:
    """Evaluate math functions.

    Args:
        func_name: Name of the math function (uppercase)
        args: List of evaluated arguments (non-NULL)

    Returns:
        CypherValue result of the math function

    Raises:
        ValueError: If function is unknown
        TypeError: If arguments have invalid types
    """
    import math

    if func_name == "ABS":
        # ABS(number) -> number
        if len(args) != 1:
            raise TypeError(f"ABS expects 1 argument, got {len(args)}")
        arg = args[0]
        if isinstance(arg, CypherInt):
            return CypherInt(abs(arg.value))
        elif isinstance(arg, CypherFloat):
            return CypherFloat(abs(arg.value))
        else:
            raise TypeError(f"ABS expects numeric argument, got {type(arg).__name__}")

    elif func_name == "CEIL":
        # CEIL(number) -> int (returns smallest integer >= number)
        if len(args) != 1:
            raise TypeError(f"CEIL expects 1 argument, got {len(args)}")
        arg = args[0]
        if isinstance(arg, CypherInt):
            return arg  # Integer ceiling is itself
        elif isinstance(arg, CypherFloat):
            return CypherInt(math.ceil(arg.value))
        else:
            raise TypeError(f"CEIL expects numeric argument, got {type(arg).__name__}")

    elif func_name == "FLOOR":
        # FLOOR(number) -> int (returns largest integer <= number)
        if len(args) != 1:
            raise TypeError(f"FLOOR expects 1 argument, got {len(args)}")
        arg = args[0]
        if isinstance(arg, CypherInt):
            return arg  # Integer floor is itself
        elif isinstance(arg, CypherFloat):
            return CypherInt(math.floor(arg.value))
        else:
            raise TypeError(f"FLOOR expects numeric argument, got {type(arg).__name__}")

    elif func_name == "ROUND":
        # ROUND(number, [precision]) -> number
        # With 1 arg: rounds to nearest integer
        # With 2 args: rounds to specified decimal places
        # Uses Neo4j tie-breaking: ties (x.5) round toward positive infinity
        if len(args) not in (1, 2):
            raise TypeError(f"ROUND expects 1 or 2 arguments, got {len(args)}")

        arg = args[0]
        if not isinstance(arg, (CypherInt, CypherFloat)):
            raise TypeError(f"ROUND expects numeric argument, got {type(arg).__name__}")

        # Epsilon for detecting tie cases (fractional part is ±0.5)
        eps = 1e-10
        precision = 0 if len(args) == 1 else args[1].value

        if len(args) == 2:
            precision_arg = args[1]
            if not isinstance(precision_arg, CypherInt):
                raise TypeError(
                    f"ROUND precision must be integer, got {type(precision_arg).__name__}"
                )
            precision = precision_arg.value

        if isinstance(arg, CypherInt):
            # For integers with non-negative precision, no rounding needed
            if precision >= 0:
                return arg
            # For negative precision, round to tens, hundreds, etc.
            value = arg.value
        else:
            value = arg.value

        # Scale value by 10^precision to move decimal point
        scale = 10**precision
        scaled = value * scale

        # Check if scaled value is a tie case (fractional part is ±0.5)
        frac = abs(scaled - math.floor(scaled))
        is_tie = abs(frac - 0.5) < eps

        if is_tie:
            # Tie case: round toward positive infinity (use ceil)
            rounded_scaled = math.ceil(scaled)
        else:
            # Non-tie case: standard rounding (add 0.5 and floor)
            rounded_scaled = math.floor(scaled + 0.5)

        result = rounded_scaled / scale

        # Return appropriate type
        if isinstance(arg, CypherInt) and precision >= 0:
            return CypherInt(int(result))
        elif len(args) == 1:
            # Single arg: return float
            return CypherFloat(result)
        else:
            return CypherFloat(result)

    elif func_name == "SIGN":
        # SIGN(number) -> int (-1, 0, or 1)
        if len(args) != 1:
            raise TypeError(f"SIGN expects 1 argument, got {len(args)}")
        arg = args[0]
        if isinstance(arg, (CypherInt, CypherFloat)):
            value = arg.value
        else:
            raise TypeError(f"SIGN expects numeric argument, got {type(arg).__name__}")

        if value > 0:
            return CypherInt(1)
        elif value < 0:
            return CypherInt(-1)
        else:
            return CypherInt(0)

    raise ValueError(f"Unknown math function: {func_name}")


def _evaluate_subscript(
    subscript: Subscript, ctx: ExecutionContext, executor: Any = None
) -> CypherValue:
    """Evaluate subscript/slice operations on lists.

    Args:
        subscript: Subscript AST node with base and index/start/end
        ctx: Execution context
        executor: Optional executor for nested expressions

    Returns:
        CypherValue result (element or sublist)

    Raises:
        TypeError: If base is not a list
    """
    # Evaluate the base expression
    base_val = evaluate_expression(subscript.base, ctx, executor)

    # NULL propagation: if base is NULL, return NULL
    if isinstance(base_val, CypherNull):
        return CypherNull()

    # Base must be a list
    if not isinstance(base_val, CypherList):
        raise TypeError(f"Subscript operation requires list, got {type(base_val).__name__}")

    list_value = base_val.value

    # Handle index access: list[i]
    if subscript.index is not None:
        index_val = evaluate_expression(subscript.index, ctx, executor)

        # NULL index returns NULL
        if isinstance(index_val, CypherNull):
            return CypherNull()

        if not isinstance(index_val, CypherInt):
            raise TypeError(f"List index must be integer, got {type(index_val).__name__}")

        index = index_val.value

        # Python supports negative indices naturally
        # Out of bounds returns NULL per openCypher spec
        try:
            from typing import cast

            return cast(CypherValue, list_value[index])
        except IndexError:
            return CypherNull()

    # Handle slice access: list[start..end]
    else:
        # Evaluate start and end (may be None)
        start_val = (
            None if subscript.start is None else evaluate_expression(subscript.start, ctx, executor)
        )
        end_val = (
            None if subscript.end is None else evaluate_expression(subscript.end, ctx, executor)
        )

        # NULL in slice returns NULL
        if isinstance(start_val, CypherNull) or isinstance(end_val, CypherNull):
            return CypherNull()

        # Convert to Python slice indices
        start = None if start_val is None else start_val.value
        end = None if end_val is None else end_val.value

        # Validate types
        if start is not None and not isinstance(start_val, CypherInt):
            raise TypeError(f"Slice start must be integer, got {type(start_val).__name__}")
        if end is not None and not isinstance(end_val, CypherInt):
            raise TypeError(f"Slice end must be integer, got {type(end_val).__name__}")

        # Perform slice (Python's slicing handles negative indices and bounds automatically)
        # Note: openCypher slicing is exclusive on the end, same as Python
        result = list_value[start:end]
        return CypherList(result)


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
            arg = args[0]

            # Boolean → Boolean (identity)
            if isinstance(arg, CypherBool):
                return arg

            # String → Boolean (only "true"/"false" case-insensitive)
            elif isinstance(arg, CypherString):
                value_lower = arg.value.lower()
                if value_lower == "true":
                    return CypherBool(True)
                elif value_lower == "false":
                    return CypherBool(False)
                else:
                    return CypherNull()  # Invalid string value

            # Complex types → NULL (cannot convert to boolean)
            # Lists, maps, paths, nodes, relationships are not convertible
            elif (
                isinstance(arg, (CypherList, CypherMap))
                or hasattr(arg, "id")
                or hasattr(arg, "src")
            ):
                # NodeRef has 'id', EdgeRef has 'src'/'dst'
                return CypherNull()

            # All other types → NULL
            else:
                return CypherNull()
        except (ValueError, TypeError):
            return CypherNull()

    elif func_name == "TOINTEGER":
        try:
            arg = args[0]

            # Integer → Integer (identity)
            if isinstance(arg, CypherInt):
                return arg

            # Float/String → Integer (truncate/parse)
            elif isinstance(arg, (CypherFloat, CypherString)):
                return CypherInt(int(arg.value))

            # Boolean → Integer (true=1, false=0)
            elif isinstance(arg, CypherBool):
                return CypherInt(1 if arg.value else 0)

            # Complex types → NULL (lists/maps are not numeric)
            # Graph elements → NULL (use id(node) to get ID instead)
            elif (
                isinstance(arg, (CypherList, CypherMap))
                or hasattr(arg, "id")
                or hasattr(arg, "src")
            ):
                return CypherNull()

            # All other types → NULL
            else:
                return CypherNull()
        except (ValueError, TypeError):
            return CypherNull()

    elif func_name == "TOFLOAT":
        try:
            arg = args[0]

            # Float → Float (identity)
            if isinstance(arg, CypherFloat):
                return arg

            # Integer/String → Float (convert/parse)
            elif isinstance(arg, (CypherInt, CypherString)):
                return CypherFloat(float(arg.value))

            # Boolean → Float (true=1.0, false=0.0)
            elif isinstance(arg, CypherBool):
                return CypherFloat(1.0 if arg.value else 0.0)

            # Complex types → NULL (lists/maps are not numeric)
            # Graph elements → NULL (nodes/relationships are not numeric)
            elif (
                isinstance(arg, (CypherList, CypherMap))
                or hasattr(arg, "id")
                or hasattr(arg, "src")
            ):
                return CypherNull()

            # All other types → NULL
            else:
                return CypherNull()
        except (ValueError, TypeError):
            return CypherNull()

    elif func_name == "TOSTRING":
        arg = args[0]

        # String → String (identity)
        if isinstance(arg, CypherString):
            return arg

        # Integer/Float → String (decimal representation)
        elif isinstance(arg, (CypherInt, CypherFloat)):
            return CypherString(str(arg.value))

        # Boolean → String ("true"/"false")
        elif isinstance(arg, CypherBool):
            return CypherString("true" if arg.value else "false")

        # Complex types → NULL (no standard string representation)
        # Note: We could return JSON-like representations for lists/maps,
        # but openCypher spec returns NULL for complex types
        # Graph elements → NULL (use properties() or id() instead)
        elif isinstance(arg, (CypherList, CypherMap)) or hasattr(arg, "id") or hasattr(arg, "src"):
            return CypherNull()

        # All other types → NULL
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


# Sentinel value to distinguish missing keys from explicit null
_MISSING = object()


def _extract_map_param(map_val: CypherMap, key: str, default: Any = _MISSING) -> Any:
    """Extract a parameter from a CypherMap.

    Args:
        map_val: CypherMap containing parameters
        key: Parameter key to extract
        default: Default value if key not present

    Returns:
        - int for CypherInt/CypherFloat
        - str for CypherString
        - CypherNull for present-but-null values
        - default (or _MISSING sentinel) for absent keys
    """
    cypher_val = map_val.value.get(key)
    if cypher_val is None:
        return default
    if isinstance(cypher_val, CypherNull):
        return cypher_val  # Return CypherNull itself to distinguish from missing
    if isinstance(cypher_val, (CypherInt, CypherFloat)):
        # Coerce numeric values to int for datetime constructors
        return int(cypher_val.value)
    elif isinstance(cypher_val, CypherString):
        return cypher_val.value
    else:
        raise TypeError(
            f"Temporal map parameter '{key}' must be int, float, or string, "
            f"got {type(cypher_val).__name__}: {cypher_val}"
        )


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
    import datetime

    if func_name == "DATE":
        # date(), date(string), or date(map)
        if len(args) == 0:
            # date() returns current date
            return CypherDate(datetime.date.today())
        elif len(args) == 1:
            arg = args[0]
            if isinstance(arg, CypherString):
                # date(string) parses ISO 8601 date
                return CypherDate(arg.value)
            elif isinstance(arg, CypherMap):
                # date(map) builds from components
                year = _extract_map_param(arg, "year")
                month = _extract_map_param(arg, "month")
                day = _extract_map_param(arg, "day")
                week = _extract_map_param(arg, "week")
                day_of_week = _extract_map_param(arg, "dayOfWeek")
                quarter = _extract_map_param(arg, "quarter")
                day_of_quarter = _extract_map_param(arg, "dayOfQuarter")
                ordinal_day = _extract_map_param(arg, "ordinalDay")

                # Check if any parameter is explicitly null
                all_params = [
                    year,
                    month,
                    day,
                    week,
                    day_of_week,
                    quarter,
                    day_of_quarter,
                    ordinal_day,
                ]
                if any(isinstance(p, CypherNull) for p in all_params):
                    return CypherNull()

                # Calendar date: year, month, day
                if year is not _MISSING and month is not _MISSING and day is not _MISSING:
                    return CypherDate(datetime.date(year, month, day))
                # Week date: year, week, dayOfWeek
                elif year is not _MISSING and week is not _MISSING and day_of_week is not _MISSING:
                    # Validate week and dayOfWeek ranges
                    if not (1 <= week <= 53):
                        raise ValueError(f"week must be between 1 and 53, got {week}")
                    if not (1 <= day_of_week <= 7):
                        raise ValueError(f"dayOfWeek must be between 1 and 7, got {day_of_week}")
                    # ISO week date to calendar date
                    jan4 = datetime.date(year, 1, 4)
                    week_one_monday = jan4 - datetime.timedelta(days=jan4.weekday())
                    target_date = week_one_monday + datetime.timedelta(
                        weeks=week - 1, days=day_of_week - 1
                    )
                    return CypherDate(target_date)
                # Quarter date: year, quarter, dayOfQuarter
                elif (
                    year is not _MISSING
                    and quarter is not _MISSING
                    and day_of_quarter is not _MISSING
                ):
                    # Validate quarter and dayOfQuarter ranges
                    if not (1 <= quarter <= 4):
                        raise ValueError(f"quarter must be between 1 and 4, got {quarter}")
                    # Quarter to month: Q1=Jan, Q2=Apr, Q3=Jul, Q4=Oct
                    first_month = (quarter - 1) * 3 + 1
                    # Calculate last day of quarter for validation
                    if quarter == 4:
                        last_month = 12
                    else:
                        last_month = first_month + 2
                    # Calculate days in quarter
                    import calendar

                    days_in_quarter = sum(
                        calendar.monthrange(year, m)[1] for m in range(first_month, last_month + 1)
                    )
                    if not (1 <= day_of_quarter <= days_in_quarter):
                        raise ValueError(
                            f"dayOfQuarter must be between 1 and {days_in_quarter} "
                            f"for quarter {quarter} of year {year}, got {day_of_quarter}"
                        )
                    first_day = datetime.date(year, first_month, 1)
                    target_date = first_day + datetime.timedelta(days=day_of_quarter - 1)
                    return CypherDate(target_date)
                # Ordinal date: year, ordinalDay
                elif year is not _MISSING and ordinal_day is not _MISSING:
                    # Validate ordinalDay range (366 for leap years, 365 otherwise)
                    import calendar

                    max_ordinal_day = 366 if calendar.isleap(year) else 365
                    if not (1 <= ordinal_day <= max_ordinal_day):
                        raise ValueError(
                            f"ordinalDay must be between 1 and {max_ordinal_day} "
                            f"for year {year}, got {ordinal_day}"
                        )
                    jan1 = datetime.date(year, 1, 1)
                    target_date = jan1 + datetime.timedelta(days=ordinal_day - 1)
                    return CypherDate(target_date)
                else:
                    raise TypeError(
                        "DATE map constructor requires: (year, month, day) OR "
                        "(year, week, dayOfWeek) OR (year, quarter, dayOfQuarter) OR "
                        "(year, ordinalDay)"
                    )
            else:
                raise TypeError(f"DATE expects string or map, got {type(arg).__name__}")
        else:
            raise TypeError(f"DATE expects 0 or 1 argument, got {len(args)}")

    elif func_name == "DATETIME":
        # datetime(), datetime(string), or datetime(map)
        if len(args) == 0:
            # datetime() returns current datetime
            return CypherDateTime(datetime.datetime.now())
        elif len(args) == 1:
            arg = args[0]
            if isinstance(arg, CypherString):
                # datetime(string) parses ISO 8601 datetime
                return CypherDateTime(arg.value)
            elif isinstance(arg, CypherMap):
                # datetime(map) builds from components
                year = _extract_map_param(arg, "year")
                month = _extract_map_param(arg, "month")
                day = _extract_map_param(arg, "day")
                hour = _extract_map_param(arg, "hour", 0)
                minute = _extract_map_param(arg, "minute", 0)
                second = _extract_map_param(arg, "second", 0)
                millisecond = _extract_map_param(arg, "millisecond", 0)
                microsecond = _extract_map_param(arg, "microsecond", 0)
                nanosecond = _extract_map_param(arg, "nanosecond", 0)
                timezone = _extract_map_param(arg, "timezone")

                week = _extract_map_param(arg, "week")
                day_of_week = _extract_map_param(arg, "dayOfWeek")
                quarter = _extract_map_param(arg, "quarter")
                day_of_quarter = _extract_map_param(arg, "dayOfQuarter")
                ordinal_day = _extract_map_param(arg, "ordinalDay")

                # Check if any parameter is explicitly null
                all_params = [
                    year,
                    month,
                    day,
                    hour,
                    minute,
                    second,
                    millisecond,
                    microsecond,
                    nanosecond,
                    timezone,
                    week,
                    day_of_week,
                    quarter,
                    day_of_quarter,
                    ordinal_day,
                ]
                if any(isinstance(p, CypherNull) for p in all_params):
                    return CypherNull()

                # Total microseconds from all sub-second components
                total_microsecond = microsecond + (millisecond * 1000) + (nanosecond // 1000)

                # Normalize microseconds overflow into seconds
                carry_seconds = total_microsecond // 1_000_000
                total_microsecond = total_microsecond % 1_000_000
                second += carry_seconds

                # Normalize seconds overflow into minutes
                carry_minutes = second // 60
                second = second % 60
                minute += carry_minutes

                # Normalize minutes overflow into hours
                carry_hours = minute // 60
                minute = minute % 60
                hour += carry_hours

                # Determine date part
                if year is not _MISSING and month is not _MISSING and day is not _MISSING:
                    # Calendar date
                    date_part = datetime.date(year, month, day)
                elif year is not _MISSING and week is not _MISSING and day_of_week is not _MISSING:
                    # Validate week and dayOfWeek ranges
                    if not (1 <= week <= 53):
                        raise ValueError(f"week must be between 1 and 53, got {week}")
                    if not (1 <= day_of_week <= 7):
                        raise ValueError(f"dayOfWeek must be between 1 and 7, got {day_of_week}")
                    # Week date
                    jan4 = datetime.date(year, 1, 4)
                    week_one_monday = jan4 - datetime.timedelta(days=jan4.weekday())
                    date_part = week_one_monday + datetime.timedelta(
                        weeks=week - 1, days=day_of_week - 1
                    )
                elif (
                    year is not _MISSING
                    and quarter is not _MISSING
                    and day_of_quarter is not _MISSING
                ):
                    # Validate quarter and dayOfQuarter ranges
                    if not (1 <= quarter <= 4):
                        raise ValueError(f"quarter must be between 1 and 4, got {quarter}")
                    # Quarter date
                    first_month = (quarter - 1) * 3 + 1
                    # Calculate last day of quarter for validation
                    if quarter == 4:
                        last_month = 12
                    else:
                        last_month = first_month + 2
                    # Get last day of quarter's last month
                    import calendar

                    days_in_quarter = sum(
                        calendar.monthrange(year, m)[1] for m in range(first_month, last_month + 1)
                    )
                    if not (1 <= day_of_quarter <= days_in_quarter):
                        raise ValueError(
                            f"dayOfQuarter must be between 1 and {days_in_quarter} "
                            f"for quarter {quarter} of year {year}, got {day_of_quarter}"
                        )
                    first_day = datetime.date(year, first_month, 1)
                    date_part = first_day + datetime.timedelta(days=day_of_quarter - 1)
                elif year is not _MISSING and ordinal_day is not _MISSING:
                    # Validate ordinalDay range (366 for leap years, 365 otherwise)
                    import calendar

                    max_ordinal_day = 366 if calendar.isleap(year) else 365
                    if not (1 <= ordinal_day <= max_ordinal_day):
                        raise ValueError(
                            f"ordinalDay must be between 1 and {max_ordinal_day} "
                            f"for year {year}, got {ordinal_day}"
                        )
                    # Ordinal date
                    jan1 = datetime.date(year, 1, 1)
                    date_part = jan1 + datetime.timedelta(days=ordinal_day - 1)
                else:
                    raise TypeError(
                        "DATETIME map constructor requires date components: "
                        "(year, month, day) OR (year, week, dayOfWeek) OR "
                        "(year, quarter, dayOfQuarter) OR (year, ordinalDay)"
                    )

                # Normalize hour overflow into days
                carry_days = hour // 24
                hour = hour % 24
                if carry_days > 0:
                    date_part = date_part + datetime.timedelta(days=carry_days)

                # Combine date and time
                dt = datetime.datetime.combine(
                    date_part, datetime.time(hour, minute, second, total_microsecond)
                )

                # Handle timezone if provided
                if timezone is not _MISSING:
                    from dateutil import tz

                    tzinfo = tz.gettz(timezone)
                    if tzinfo is None:
                        raise ValueError(f"Invalid timezone: {timezone}")
                    dt = dt.replace(tzinfo=tzinfo)

                return CypherDateTime(dt)
            else:
                raise TypeError(f"DATETIME expects string or map, got {type(arg).__name__}")
        else:
            raise TypeError(f"DATETIME expects 0 or 1 argument, got {len(args)}")

    elif func_name == "TIME":
        # time(), time(string), or time(map)
        if len(args) == 0:
            # time() returns current time
            return CypherTime(datetime.datetime.now().time())
        elif len(args) == 1:
            arg = args[0]
            if isinstance(arg, CypherString):
                # time(string) parses ISO 8601 time
                return CypherTime(arg.value)
            elif isinstance(arg, CypherMap):
                # time(map) builds from components
                hour = _extract_map_param(arg, "hour", 0)
                minute = _extract_map_param(arg, "minute", 0)
                second = _extract_map_param(arg, "second", 0)
                millisecond = _extract_map_param(arg, "millisecond", 0)
                microsecond = _extract_map_param(arg, "microsecond", 0)
                nanosecond = _extract_map_param(arg, "nanosecond", 0)
                timezone = _extract_map_param(arg, "timezone")

                # Check if any parameter is explicitly null
                all_params = [hour, minute, second, millisecond, microsecond, nanosecond, timezone]
                if any(isinstance(p, CypherNull) for p in all_params):
                    return CypherNull()

                # Total microseconds from all sub-second components
                total_microsecond = microsecond + (millisecond * 1000) + (nanosecond // 1000)

                # Normalize microseconds overflow into seconds
                carry_seconds = total_microsecond // 1_000_000
                total_microsecond = total_microsecond % 1_000_000
                second += carry_seconds

                # Normalize seconds overflow into minutes
                carry_minutes = second // 60
                second = second % 60
                minute += carry_minutes

                # Normalize minutes overflow into hours
                carry_hours = minute // 60
                minute = minute % 60
                hour += carry_hours

                # Validate hour range (TIME cannot have day overflow)
                if hour >= 24:
                    raise ValueError(
                        f"TIME hour overflow: hour must be 0-23 after normalization, got {hour}. "
                        f"Consider using DATETIME if day rollover is needed."
                    )

                # Create time object
                t = datetime.time(hour, minute, second, total_microsecond)

                # Handle timezone if provided
                if timezone is not _MISSING:
                    from dateutil import tz

                    tzinfo = tz.gettz(timezone)
                    if tzinfo is None:
                        raise ValueError(f"Invalid timezone: {timezone}")
                    t = t.replace(tzinfo=tzinfo)

                return CypherTime(t)
            else:
                raise TypeError(f"TIME expects string or map, got {type(arg).__name__}")
        else:
            raise TypeError(f"TIME expects 0 or 1 argument, got {len(args)}")

    elif func_name == "LOCALDATETIME":
        # localdatetime(), localdatetime(string), or localdatetime(map)
        if len(args) == 0:
            # localdatetime() returns current datetime without timezone
            return CypherDateTime(datetime.datetime.now().replace(tzinfo=None))
        elif len(args) == 1:
            arg = args[0]
            if isinstance(arg, CypherString):
                # localdatetime(string) parses ISO 8601 datetime without timezone
                cypher_dt = CypherDateTime(arg.value)
                # Strip timezone if present to ensure naive datetime
                if cypher_dt.value.tzinfo is not None:
                    cypher_dt = CypherDateTime(cypher_dt.value.replace(tzinfo=None))
                return cypher_dt
            elif isinstance(arg, CypherMap):
                # localdatetime(map) builds from components (no timezone)
                year = _extract_map_param(arg, "year")
                month = _extract_map_param(arg, "month")
                day = _extract_map_param(arg, "day")
                hour = _extract_map_param(arg, "hour", 0)
                minute = _extract_map_param(arg, "minute", 0)
                second = _extract_map_param(arg, "second", 0)
                millisecond = _extract_map_param(arg, "millisecond", 0)
                microsecond = _extract_map_param(arg, "microsecond", 0)
                nanosecond = _extract_map_param(arg, "nanosecond", 0)

                week = _extract_map_param(arg, "week")
                day_of_week = _extract_map_param(arg, "dayOfWeek")
                quarter = _extract_map_param(arg, "quarter")
                day_of_quarter = _extract_map_param(arg, "dayOfQuarter")
                ordinal_day = _extract_map_param(arg, "ordinalDay")

                # Check if any parameter is explicitly null
                all_params = [
                    year,
                    month,
                    day,
                    hour,
                    minute,
                    second,
                    millisecond,
                    microsecond,
                    nanosecond,
                    week,
                    day_of_week,
                    quarter,
                    day_of_quarter,
                    ordinal_day,
                ]
                if any(isinstance(p, CypherNull) for p in all_params):
                    return CypherNull()

                # Total microseconds from all sub-second components
                total_microsecond = microsecond + (millisecond * 1000) + (nanosecond // 1000)

                # Normalize microseconds overflow into seconds
                carry_seconds = total_microsecond // 1_000_000
                total_microsecond = total_microsecond % 1_000_000
                second += carry_seconds

                # Normalize seconds overflow into minutes
                carry_minutes = second // 60
                second = second % 60
                minute += carry_minutes

                # Normalize minutes overflow into hours
                carry_hours = minute // 60
                minute = minute % 60
                hour += carry_hours

                # Determine date part (same logic as DATETIME)
                if year is not _MISSING and month is not _MISSING and day is not _MISSING:
                    date_part = datetime.date(year, month, day)
                elif year is not _MISSING and week is not _MISSING and day_of_week is not _MISSING:
                    if not (1 <= week <= 53):
                        raise ValueError(f"week must be between 1 and 53, got {week}")
                    if not (1 <= day_of_week <= 7):
                        raise ValueError(f"dayOfWeek must be between 1 and 7, got {day_of_week}")
                    jan4 = datetime.date(year, 1, 4)
                    week_one_monday = jan4 - datetime.timedelta(days=jan4.weekday())
                    date_part = week_one_monday + datetime.timedelta(
                        weeks=week - 1, days=day_of_week - 1
                    )
                elif (
                    year is not _MISSING
                    and quarter is not _MISSING
                    and day_of_quarter is not _MISSING
                ):
                    if not (1 <= quarter <= 4):
                        raise ValueError(f"quarter must be between 1 and 4, got {quarter}")
                    first_month = (quarter - 1) * 3 + 1
                    if quarter == 4:
                        last_month = 12
                    else:
                        last_month = first_month + 2
                    import calendar

                    days_in_quarter = sum(
                        calendar.monthrange(year, m)[1] for m in range(first_month, last_month + 1)
                    )
                    if not (1 <= day_of_quarter <= days_in_quarter):
                        raise ValueError(
                            f"dayOfQuarter must be between 1 and {days_in_quarter} "
                            f"for quarter {quarter} of year {year}, got {day_of_quarter}"
                        )
                    first_day = datetime.date(year, first_month, 1)
                    date_part = first_day + datetime.timedelta(days=day_of_quarter - 1)
                elif year is not _MISSING and ordinal_day is not _MISSING:
                    import calendar

                    max_ordinal_day = 366 if calendar.isleap(year) else 365
                    if not (1 <= ordinal_day <= max_ordinal_day):
                        raise ValueError(
                            f"ordinalDay must be between 1 and {max_ordinal_day} "
                            f"for year {year}, got {ordinal_day}"
                        )
                    jan1 = datetime.date(year, 1, 1)
                    date_part = jan1 + datetime.timedelta(days=ordinal_day - 1)
                else:
                    raise TypeError(
                        "LOCALDATETIME map constructor requires date components: "
                        "(year, month, day) OR (year, week, dayOfWeek) OR "
                        "(year, quarter, dayOfQuarter) OR (year, ordinalDay)"
                    )

                # Normalize hour overflow into days
                carry_days = hour // 24
                hour = hour % 24
                if carry_days > 0:
                    date_part = date_part + datetime.timedelta(days=carry_days)

                # Combine date and time (no timezone for LOCALDATETIME)
                dt = datetime.datetime.combine(
                    date_part, datetime.time(hour, minute, second, total_microsecond)
                )

                return CypherDateTime(dt)
            else:
                raise TypeError(f"LOCALDATETIME expects string or map, got {type(arg).__name__}")
        else:
            raise TypeError(f"LOCALDATETIME expects 0 or 1 argument, got {len(args)}")

    elif func_name == "LOCALTIME":
        # localtime(), localtime(string), or localtime(map)
        if len(args) == 0:
            # localtime() returns current time without timezone
            return CypherTime(datetime.datetime.now().time().replace(tzinfo=None))
        elif len(args) == 1:
            arg = args[0]
            if isinstance(arg, CypherString):
                # localtime(string) parses ISO 8601 time without timezone
                cypher_t = CypherTime(arg.value)
                # Strip timezone if present to ensure naive time
                if cypher_t.value.tzinfo is not None:
                    cypher_t = CypherTime(cypher_t.value.replace(tzinfo=None))
                return cypher_t
            elif isinstance(arg, CypherMap):
                # localtime(map) builds from components (no timezone)
                hour = _extract_map_param(arg, "hour", 0)
                minute = _extract_map_param(arg, "minute", 0)
                second = _extract_map_param(arg, "second", 0)
                millisecond = _extract_map_param(arg, "millisecond", 0)
                microsecond = _extract_map_param(arg, "microsecond", 0)
                nanosecond = _extract_map_param(arg, "nanosecond", 0)

                # Check if any parameter is explicitly null
                all_params = [hour, minute, second, millisecond, microsecond, nanosecond]
                if any(isinstance(p, CypherNull) for p in all_params):
                    return CypherNull()

                # Total microseconds from all sub-second components
                total_microsecond = microsecond + (millisecond * 1000) + (nanosecond // 1000)

                # Normalize microseconds overflow into seconds
                carry_seconds = total_microsecond // 1_000_000
                total_microsecond = total_microsecond % 1_000_000
                second += carry_seconds

                # Normalize seconds overflow into minutes
                carry_minutes = second // 60
                second = second % 60
                minute += carry_minutes

                # Normalize minutes overflow into hours
                carry_hours = minute // 60
                minute = minute % 60
                hour += carry_hours

                # Validate hour range (LOCALTIME cannot have day overflow)
                if hour >= 24:
                    raise ValueError(
                        f"LOCALTIME hour overflow: hour must be 0-23 after normalization, "
                        f"got {hour}. Consider using LOCALDATETIME if day rollover is needed."
                    )

                # Create time object (no timezone for LOCALTIME)
                t = datetime.time(hour, minute, second, total_microsecond)

                return CypherTime(t)
            else:
                raise TypeError(f"LOCALTIME expects string or map, got {type(arg).__name__}")
        else:
            raise TypeError(f"LOCALTIME expects 0 or 1 argument, got {len(args)}")

    elif func_name == "DURATION":
        # duration(string) or duration(map)
        if len(args) != 1:
            raise TypeError(f"DURATION expects 1 argument, got {len(args)}")

        arg = args[0]
        if isinstance(arg, CypherString):
            # duration(string) parses ISO 8601 duration
            return CypherDuration(arg.value)
        elif isinstance(arg, CypherMap):
            # duration(map) builds from components
            years = _extract_map_param(arg, "years", 0)
            months = _extract_map_param(arg, "months", 0)
            weeks = _extract_map_param(arg, "weeks", 0)
            days = _extract_map_param(arg, "days", 0)
            hours = _extract_map_param(arg, "hours", 0)
            minutes = _extract_map_param(arg, "minutes", 0)
            seconds = _extract_map_param(arg, "seconds", 0)
            milliseconds = _extract_map_param(arg, "milliseconds", 0)
            microseconds = _extract_map_param(arg, "microseconds", 0)
            nanoseconds = _extract_map_param(arg, "nanoseconds", 0)

            # Check if any parameter is explicitly null
            all_params = [
                years,
                months,
                weeks,
                days,
                hours,
                minutes,
                seconds,
                milliseconds,
                microseconds,
                nanoseconds,
            ]
            if any(isinstance(p, CypherNull) for p in all_params):
                return CypherNull()

            # If years or months are present, use isodate.Duration
            if years != 0 or months != 0:
                import isodate

                # Create Duration with all components
                dur = isodate.Duration(
                    years=years,
                    months=months,
                    weeks=weeks,
                    days=days,
                    hours=hours,
                    minutes=minutes,
                    seconds=seconds,
                    milliseconds=milliseconds,
                    microseconds=microseconds + (nanoseconds // 1000),
                )
                return CypherDuration(dur)
            else:
                # Simple timedelta
                td = datetime.timedelta(
                    weeks=weeks,
                    days=days,
                    hours=hours,
                    minutes=minutes,
                    seconds=seconds,
                    milliseconds=milliseconds,
                    microseconds=microseconds + (nanoseconds // 1000),
                )
                return CypherDuration(td)
        else:
            raise TypeError(f"DURATION expects string or map, got {type(arg).__name__}")

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

    elif func_name == "TRUNCATE":
        # truncate(unit, temporal) or temporal.truncate(unit)
        if len(args) != 2:
            raise TypeError(f"TRUNCATE expects 2 arguments, got {len(args)}")

        # First argument is the unit string
        if not isinstance(args[0], CypherString):
            raise TypeError(f"TRUNCATE unit must be string, got {type(args[0]).__name__}")
        unit = args[0].value.lower()

        # Second argument is the temporal value
        temporal = args[1]
        if not isinstance(temporal, (CypherDateTime, CypherDate, CypherTime)):
            raise TypeError(
                f"TRUNCATE expects datetime, date, or time as second argument, "
                f"got {type(temporal).__name__}"
            )

        # Truncate based on unit
        return _truncate_temporal(temporal, unit)

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


def _evaluate_path_function(func_name: str, args: list[CypherValue]) -> CypherValue:
    """Evaluate path functions.

    These functions work with CypherPath values.

    Args:
        func_name: Name of the path function (uppercase)
        args: List of evaluated arguments

    Returns:
        CypherValue result of the path function

    Raises:
        ValueError: If function is unknown
        TypeError: If arguments have invalid types
    """
    from graphforge.types.values import CypherPath

    if func_name == "LENGTH":
        # length(path) - returns the number of relationships in the path
        if len(args) != 1:
            raise TypeError(f"LENGTH expects 1 argument, got {len(args)}")

        arg = args[0]

        # Handle NULL
        if isinstance(arg, CypherNull):
            return CypherNull()

        # Check if argument is a path
        if isinstance(arg, CypherPath):
            return CypherInt(arg.length())

        raise TypeError(f"LENGTH expects path argument, got {type(arg).__name__}")

    if func_name == "NODES":
        # nodes(path) - returns a list of nodes in the path
        if len(args) != 1:
            raise TypeError(f"NODES expects 1 argument, got {len(args)}")

        arg = args[0]

        # Handle NULL
        if isinstance(arg, CypherNull):
            return CypherNull()

        # Check if argument is a path
        if isinstance(arg, CypherPath):
            # Return nodes as a list (NodeRef objects are stored directly)
            # Note: We store NodeRef objects directly in the list, not wrapped in CypherValues
            # This is consistent with how graph elements are handled elsewhere
            return CypherList(arg.nodes)  # type: ignore[arg-type]

        raise TypeError(f"NODES expects path argument, got {type(arg).__name__}")

    if func_name == "RELATIONSHIPS":
        # relationships(path) - returns a list of relationships in the path
        if len(args) != 1:
            raise TypeError(f"RELATIONSHIPS expects 1 argument, got {len(args)}")

        arg = args[0]

        # Handle NULL
        if isinstance(arg, CypherNull):
            return CypherNull()

        # Check if argument is a path
        if isinstance(arg, CypherPath):
            # Return relationships as a list (EdgeRef objects are stored directly)
            # Note: We store EdgeRef objects directly in the list, not wrapped in CypherValues
            # This is consistent with how graph elements are handled elsewhere
            return CypherList(arg.relationships)  # type: ignore[arg-type]

        raise TypeError(f"RELATIONSHIPS expects path argument, got {type(arg).__name__}")

    if func_name == "HEAD":
        # head(path) - returns the first node in the path
        if len(args) != 1:
            raise TypeError(f"HEAD expects 1 argument, got {len(args)}")

        arg = args[0]

        # Handle NULL
        if isinstance(arg, CypherNull):
            return CypherNull()

        # Check if argument is a path
        if isinstance(arg, CypherPath):
            if len(arg.nodes) == 0:
                return CypherNull()
            return arg.nodes[0]  # type: ignore[return-value]

        raise TypeError(f"HEAD expects path argument, got {type(arg).__name__}")

    if func_name == "LAST":
        # last(path) - returns the last node in the path
        if len(args) != 1:
            raise TypeError(f"LAST expects 1 argument, got {len(args)}")

        arg = args[0]

        # Handle NULL
        if isinstance(arg, CypherNull):
            return CypherNull()

        # Check if argument is a path
        if isinstance(arg, CypherPath):
            if len(arg.nodes) == 0:
                return CypherNull()
            return arg.nodes[-1]  # type: ignore[return-value]

        raise TypeError(f"LAST expects path argument, got {type(arg).__name__}")

    raise ValueError(f"Unknown path function: {func_name}")


def _evaluate_list_function(func_name: str, args: list[CypherValue]) -> CypherValue:
    """Evaluate list functions.

    These functions work with CypherList values.

    Args:
        func_name: Name of the list function (uppercase)
        args: List of evaluated arguments

    Returns:
        CypherValue result of the list function

    Raises:
        ValueError: If function is unknown
        TypeError: If arguments have invalid types
    """
    if func_name == "TAIL":
        # tail(list) - returns all elements except the first
        if len(args) != 1:
            raise TypeError(f"TAIL expects 1 argument, got {len(args)}")

        arg = args[0]

        # Handle NULL
        if isinstance(arg, CypherNull):
            return CypherNull()

        # Check if argument is a list
        if isinstance(arg, CypherList):
            if len(arg.value) == 0:
                return CypherList([])
            return CypherList(arg.value[1:])

        raise TypeError(f"TAIL expects list argument, got {type(arg).__name__}")

    if func_name == "HEAD":
        # head(list) - returns the first element or NULL for empty list
        if len(args) != 1:
            raise TypeError(f"HEAD expects 1 argument, got {len(args)}")

        arg = args[0]

        # Handle NULL
        if isinstance(arg, CypherNull):
            return CypherNull()

        # Check if argument is a list
        if isinstance(arg, CypherList):
            if len(arg.value) == 0:
                return CypherNull()
            first_element: CypherValue = arg.value[0]
            return first_element

        raise TypeError(f"HEAD expects list argument, got {type(arg).__name__}")

    if func_name == "LAST":
        # last(list) - returns the last element or NULL for empty list
        if len(args) != 1:
            raise TypeError(f"LAST expects 1 argument, got {len(args)}")

        arg = args[0]

        # Handle NULL
        if isinstance(arg, CypherNull):
            return CypherNull()

        # Check if argument is a list
        if isinstance(arg, CypherList):
            if len(arg.value) == 0:
                return CypherNull()
            last_element: CypherValue = arg.value[-1]
            return last_element

        raise TypeError(f"LAST expects list argument, got {type(arg).__name__}")

    if func_name == "REVERSE":
        # reverse(list) - returns list with elements in reverse order
        if len(args) != 1:
            raise TypeError(f"REVERSE expects 1 argument, got {len(args)}")

        arg = args[0]

        # Handle NULL
        if isinstance(arg, CypherNull):
            return CypherNull()

        # Check if argument is a list
        if isinstance(arg, CypherList):
            return CypherList(list(reversed(arg.value)))

        raise TypeError(f"REVERSE expects list argument, got {type(arg).__name__}")

    if func_name == "RANGE":
        # range(start, end) or range(start, end, step)
        if len(args) < 2 or len(args) > 3:
            raise TypeError(f"RANGE expects 2 or 3 arguments, got {len(args)}")

        # Validate argument types
        if not isinstance(args[0], CypherInt):
            raise TypeError(f"RANGE start must be integer, got {type(args[0]).__name__}")
        if not isinstance(args[1], CypherInt):
            raise TypeError(f"RANGE end must be integer, got {type(args[1]).__name__}")

        start = args[0].value
        end = args[1].value
        step = 1

        if len(args) == 3:
            if not isinstance(args[2], CypherInt):
                raise TypeError(f"RANGE step must be integer, got {type(args[2]).__name__}")
            step = args[2].value

            # Validate step is not zero
            if step == 0:
                raise ValueError("RANGE step cannot be zero")

        # Generate range
        result_list: list[CypherValue] = []
        if step > 0:
            current = start
            while current <= end:
                result_list.append(CypherInt(current))
                current += step
        else:  # step < 0
            current = start
            while current >= end:
                result_list.append(CypherInt(current))
                current += step

        return CypherList(result_list)

    if func_name == "SIZE":
        # size(list) - returns the number of elements in the list
        if len(args) != 1:
            raise TypeError(f"SIZE expects 1 argument, got {len(args)}")

        arg = args[0]

        # Handle NULL
        if isinstance(arg, CypherNull):
            return CypherNull()

        # Check if argument is a list
        if isinstance(arg, CypherList):
            return CypherInt(len(arg.value))

        raise TypeError(f"SIZE expects list argument, got {type(arg).__name__}")

    raise ValueError(f"Unknown list function: {func_name}")
