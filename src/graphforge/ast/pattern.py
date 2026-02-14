"""Pattern matching AST nodes for openCypher.

This module defines AST nodes for graph pattern matching:
- NodePattern: Match nodes by labels and properties
- RelationshipPattern: Match relationships by type and direction
- Direction: Relationship direction enum
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Direction(Enum):
    """Relationship direction in pattern matching."""

    OUT = "OUT"  # -[:R]->
    IN = "IN"  # <-[:R]-
    UNDIRECTED = "UNDIRECTED"  # -[:R]-


class NodePattern(BaseModel):
    """AST node for matching graph nodes.

    Represents a node pattern like: (n:Person {name: "Alice"})

    Attributes:
        variable: Variable name to bind the node (None for anonymous)
        labels: List of label groups (disjunction of conjunctions)
               Example: [['Person']] - must have 'Person'
               Example: [['Person', 'Employee']] - must have both
               Example: [['Person'], ['Company']] - must have Person OR Company
        properties: Dict of property constraints (property_name -> Expression)
    """

    variable: str | None = Field(default=None, description="Variable name (None for anonymous)")
    labels: list[list[str]] = Field(
        default_factory=list, description="Label groups (disjunction of conjunctions)"
    )
    properties: dict[str, Any] = Field(default_factory=dict, description="Property constraints")

    @field_validator("variable")
    @classmethod
    def validate_variable(cls, v: str | None) -> str | None:
        """Validate variable name format if provided."""
        if v is not None:
            if len(v) == 0:
                raise ValueError("Variable name cannot be empty string")
            if not v[0].isalpha() and v[0] != "_":
                raise ValueError(f"Variable name must start with letter or underscore: {v}")
            if not v.replace("_", "").isalnum():
                raise ValueError(
                    f"Variable name must contain only alphanumeric and underscore: {v}"
                )
        return v

    @field_validator("labels")
    @classmethod
    def validate_labels(cls, v: list[str]) -> list[str]:
        """Validate label names."""
        for label in v:
            if not label or not label[0].isalpha():
                raise ValueError(f"Label must start with a letter: {label}")
        return v

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class RelationshipPattern(BaseModel):
    """AST node for matching relationships.

    Represents a relationship pattern like: -[r:KNOWS {since: 2020}]->
    Or variable-length: -[r:KNOWS*1..3]->
    Or with predicate: -[r:KNOWS WHERE r.since > 2020]->

    Attributes:
        variable: Variable name to bind the relationship (None for anonymous)
        types: List of relationship types to match
        direction: Direction of the relationship
        properties: Dict of property constraints (property_name -> Expression)
        min_hops: Minimum hops for variable-length (None for single-hop)
        max_hops: Maximum hops for variable-length (None for unbounded)
        predicate: WHERE predicate expression inside pattern (None if not specified)
    """

    variable: str | None = Field(default=None, description="Variable name (None for anonymous)")
    types: list[str] = Field(default_factory=list, description="Relationship types")
    direction: Direction = Field(..., description="Relationship direction")
    properties: dict[str, Any] = Field(default_factory=dict, description="Property constraints")
    min_hops: int | None = Field(
        default=None, description="Minimum hops for variable-length (None = single-hop)"
    )
    max_hops: int | None = Field(
        default=None, description="Maximum hops for variable-length (None = unbounded)"
    )
    predicate: Any | None = Field(
        default=None, description="WHERE predicate expression inside pattern"
    )

    @field_validator("variable")
    @classmethod
    def validate_variable(cls, v: str | None) -> str | None:
        """Validate variable name format if provided."""
        if v is not None:
            if len(v) == 0:
                raise ValueError("Variable name cannot be empty string")
            if not v[0].isalpha() and v[0] != "_":
                raise ValueError(f"Variable name must start with letter or underscore: {v}")
            if not v.replace("_", "").isalnum():
                raise ValueError(
                    f"Variable name must contain only alphanumeric and underscore: {v}"
                )
        return v

    @field_validator("types")
    @classmethod
    def validate_types(cls, v: list[str]) -> list[str]:
        """Validate relationship type names."""
        for typ in v:
            if not typ or not typ[0].isalpha():
                raise ValueError(f"Relationship type must start with a letter: {typ}")
        return v

    @field_validator("min_hops")
    @classmethod
    def validate_min_hops(cls, v: int | None) -> int | None:
        """Validate minimum hops."""
        if v is not None and v < 0:
            raise ValueError(f"Minimum hops must be non-negative, got {v}")
        return v

    @field_validator("max_hops")
    @classmethod
    def validate_max_hops(cls, v: int | None) -> int | None:
        """Validate maximum hops."""
        if v is not None and v < 1:
            raise ValueError(f"Maximum hops must be positive, got {v}")
        return v

    model_config = {"frozen": True, "arbitrary_types_allowed": True}
