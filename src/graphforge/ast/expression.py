"""Expression AST nodes for openCypher.

This module defines expression nodes for:
- Literals (integers, strings, booleans, null)
- Variable references
- Property access
- Binary operations (comparisons, logical operators)
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Literal:
    """Literal value expression.

    Examples:
        42, "hello", true, null
    """

    value: Any  # int, str, bool, None, float


@dataclass
class Variable:
    """Variable reference expression.

    Examples:
        n, person, r
    """

    name: str


@dataclass
class PropertyAccess:
    """Property access expression.

    Examples:
        n.name, person.age
    """

    variable: str
    property: str


@dataclass
class BinaryOp:
    """Binary operation expression.

    Supports:
    - Comparisons: =, <>, <, >, <=, >=
    - Logical: AND, OR
    - Arithmetic: +, -, *, / (future)
    """

    op: str
    left: Any  # Expression
    right: Any  # Expression


@dataclass
class UnaryOp:
    """Unary operation expression.

    Supports:
    - Logical: NOT
    - Arithmetic: - (negation, future)
    """

    op: str
    operand: Any  # Expression


@dataclass
class FunctionCall:
    """Function call expression.

    Examples:
        COUNT(n), SUM(n.age), AVG(n.salary)
        COUNT(*) for counting all rows
    """

    name: str  # Function name (COUNT, SUM, AVG, MIN, MAX)
    args: list[Any]  # List of argument expressions (empty for COUNT(*))
    distinct: bool = False  # True for COUNT(DISTINCT n)


@dataclass
class CaseExpression:
    """CASE expression for conditional logic.

    Examples:
        CASE WHEN n.age < 18 THEN 'minor' ELSE 'adult' END
        CASE WHEN n.status = 'active' THEN 1 WHEN n.status = 'pending' THEN 2 ELSE 0 END
    """

    when_clauses: list[tuple[Any, Any]]  # List of (condition_expr, result_expr) tuples
    else_expr: Any | None = None  # Optional ELSE expression, returns NULL if None
