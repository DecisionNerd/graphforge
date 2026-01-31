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
class FunctionCall:
    """Function call expression.

    Examples:
        COUNT(n), SUM(n.age), AVG(n.salary)
        COUNT(*) for counting all rows
    """

    name: str  # Function name (COUNT, SUM, AVG, MIN, MAX)
    args: list[Any]  # List of argument expressions (empty for COUNT(*))
    distinct: bool = False  # True for COUNT(DISTINCT n)
