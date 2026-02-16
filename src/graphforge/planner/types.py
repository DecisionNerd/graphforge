"""Type tracking for variables in query plans.

This module provides variable type tracking to detect type conflicts at compile time.
For example, a variable bound to a scalar value in WITH cannot be used as a node
in a subsequent MATCH clause.
"""

from enum import Enum


class VariableType(Enum):
    """Types for variables in query plans."""

    NODE = "node"
    RELATIONSHIP = "relationship"
    PATH = "path"
    SCALAR = "scalar"  # int, str, bool, list, map, etc.
    UNKNOWN = "unknown"  # For variables we haven't analyzed yet


class TypeContext:
    """Tracks variable types across query clauses."""

    def __init__(self):
        """Initialize an empty type context."""
        self._types: dict[str, VariableType] = {}

    def bind_variable(self, name: str, var_type: VariableType) -> None:
        """Register a variable with its type.

        Args:
            name: Variable name
            var_type: Type of the variable
        """
        self._types[name] = var_type

    def get_type(self, name: str) -> VariableType:
        """Get the type of a variable.

        Args:
            name: Variable name

        Returns:
            VariableType for the variable, or UNKNOWN if not found
        """
        return self._types.get(name, VariableType.UNKNOWN)

    def has_variable(self, name: str) -> bool:
        """Check if a variable has been bound.

        Args:
            name: Variable name

        Returns:
            True if variable is bound, False otherwise
        """
        return name in self._types

    def validate_compatible(self, name: str, expected_type: VariableType) -> None:
        """Validate that a variable can be used in a context requiring expected_type.

        Args:
            name: Variable name
            expected_type: Expected type for the variable

        Raises:
            SyntaxError: If variable type conflicts with expected type
        """
        actual_type = self.get_type(name)

        if actual_type == VariableType.UNKNOWN:
            # Variable not yet bound, will be bound by this usage
            return

        if actual_type != expected_type:
            raise SyntaxError(
                f"VariableTypeConflict: Variable `{name}` already bound to type "
                f"{actual_type.value}, cannot be used as {expected_type.value}"
            )

    def copy(self) -> "TypeContext":
        """Create a copy of this context for new query segments.

        Returns:
            New TypeContext with copied variable types
        """
        new_context = TypeContext()
        new_context._types = self._types.copy()
        return new_context
