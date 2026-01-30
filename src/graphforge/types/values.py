"""Runtime value types for openCypher.

This module implements the openCypher type system including:
- Scalar types: NULL, BOOLEAN, INTEGER, FLOAT, STRING
- Collection types: LIST, MAP

Values follow openCypher semantics including:
- NULL propagation in comparisons and operations
- Type-aware equality and comparison
- Conversion to/from Python types
"""

from enum import Enum
from typing import Any


class CypherType(Enum):
    """openCypher value types."""

    NULL = "NULL"
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    LIST = "LIST"
    MAP = "MAP"


class CypherValue:
    """Base class for all openCypher values.

    All comparison operations follow openCypher semantics:
    - NULL in any operation propagates NULL
    - Type-aware comparisons
    """

    def __init__(self, value: Any, cypher_type: CypherType):
        self.value = value
        self.type = cypher_type

    def equals(self, other: "CypherValue") -> "CypherValue":
        """Check equality following openCypher semantics.

        Returns:
            CypherBool(True) if equal
            CypherBool(False) if not equal
            CypherNull if either operand is NULL
        """
        # NULL propagation
        if isinstance(self, CypherNull) or isinstance(other, CypherNull):
            return CypherNull()

        # Numeric types can be compared across int/float
        if self._is_numeric() and other._is_numeric():
            return CypherBool(self.value == other.value)

        # Same type comparison
        if self.type == other.type:
            if self.type in (CypherType.LIST, CypherType.MAP):
                return self._deep_equals(other)
            return CypherBool(self.value == other.value)

        # Different types are not equal
        return CypherBool(False)

    def less_than(self, other: "CypherValue") -> "CypherValue":
        """Check if this value is less than another.

        Returns:
            CypherBool(True/False) for comparable types
            CypherNull if either operand is NULL
        """
        # NULL propagation
        if isinstance(self, CypherNull) or isinstance(other, CypherNull):
            return CypherNull()

        # Numeric comparison
        if self._is_numeric() and other._is_numeric():
            return CypherBool(self.value < other.value)

        # String comparison
        if self.type == CypherType.STRING and other.type == CypherType.STRING:
            return CypherBool(self.value < other.value)

        # Other comparisons are not supported in this simplified model
        return CypherBool(False)

    def _is_numeric(self) -> bool:
        """Check if this value is a numeric type."""
        return self.type in (CypherType.INTEGER, CypherType.FLOAT)

    def _deep_equals(self, other: "CypherValue") -> "CypherValue":
        """Deep equality check for collections."""
        if self.type == CypherType.LIST:
            if len(self.value) != len(other.value):
                return CypherBool(False)
            for a, b in zip(self.value, other.value):
                result = a.equals(b)
                if isinstance(result, CypherNull):
                    return CypherNull()
                if not result.value:
                    return CypherBool(False)
            return CypherBool(True)

        if self.type == CypherType.MAP:
            if set(self.value.keys()) != set(other.value.keys()):
                return CypherBool(False)
            for key in self.value:
                result = self.value[key].equals(other.value[key])
                if isinstance(result, CypherNull):
                    return CypherNull()
                if not result.value:
                    return CypherBool(False)
            return CypherBool(True)

        return CypherBool(False)

    def to_python(self) -> Any:
        """Convert this Cypher value to a Python value."""
        if self.type == CypherType.NULL:
            return None
        if self.type == CypherType.LIST:
            return [item.to_python() for item in self.value]
        if self.type == CypherType.MAP:
            return {key: val.to_python() for key, val in self.value.items()}
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"


class CypherNull(CypherValue):
    """Represents NULL in openCypher."""

    def __init__(self):
        super().__init__(None, CypherType.NULL)


class CypherBool(CypherValue):
    """Represents a boolean value in openCypher."""

    def __init__(self, value: bool):
        super().__init__(value, CypherType.BOOLEAN)


class CypherInt(CypherValue):
    """Represents an integer value in openCypher."""

    def __init__(self, value: int):
        super().__init__(value, CypherType.INTEGER)


class CypherFloat(CypherValue):
    """Represents a floating-point value in openCypher."""

    def __init__(self, value: float):
        super().__init__(value, CypherType.FLOAT)


class CypherString(CypherValue):
    """Represents a string value in openCypher."""

    def __init__(self, value: str):
        super().__init__(value, CypherType.STRING)


class CypherList(CypherValue):
    """Represents a list value in openCypher."""

    def __init__(self, value: list["CypherValue"]):
        super().__init__(value, CypherType.LIST)


class CypherMap(CypherValue):
    """Represents a map (dictionary) value in openCypher."""

    def __init__(self, value: dict[str, "CypherValue"]):
        super().__init__(value, CypherType.MAP)


def from_python(value: Any) -> CypherValue:
    """Convert a Python value to a CypherValue.

    Args:
        value: Python value to convert

    Returns:
        Appropriate CypherValue subclass

    Raises:
        TypeError: If the value type is not supported
    """
    if value is None:
        return CypherNull()
    if isinstance(value, bool):
        return CypherBool(value)
    if isinstance(value, int):
        return CypherInt(value)
    if isinstance(value, float):
        return CypherFloat(value)
    if isinstance(value, str):
        return CypherString(value)
    if isinstance(value, list):
        return CypherList([from_python(item) for item in value])
    if isinstance(value, dict):
        return CypherMap({key: from_python(val) for key, val in value.items()})

    raise TypeError(f"Cannot convert Python type {type(value).__name__} to CypherValue")
