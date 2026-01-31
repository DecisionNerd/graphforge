"""Pattern matching AST nodes for openCypher.

This module defines AST nodes for graph pattern matching:
- NodePattern: Match nodes by labels and properties
- RelationshipPattern: Match relationships by type and direction
- Direction: Relationship direction enum
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Direction(Enum):
    """Relationship direction in pattern matching."""

    OUT = "OUT"  # -[:R]->
    IN = "IN"  # <-[:R]-
    UNDIRECTED = "UNDIRECTED"  # -[:R]-


@dataclass
class NodePattern:
    """AST node for matching graph nodes.

    Represents a node pattern like: (n:Person {name: "Alice"})

    Attributes:
        variable: Variable name to bind the node (None for anonymous)
        labels: List of labels the node must have
        properties: Dict of property constraints (property_name -> Expression)
    """

    variable: str | None
    labels: list[str]
    properties: dict[str, Any]  # Maps property name to Expression


@dataclass
class RelationshipPattern:
    """AST node for matching relationships.

    Represents a relationship pattern like: -[r:KNOWS {since: 2020}]->

    Attributes:
        variable: Variable name to bind the relationship (None for anonymous)
        types: List of relationship types to match
        direction: Direction of the relationship
        properties: Dict of property constraints (property_name -> Expression)
    """

    variable: str | None
    types: list[str]
    direction: Direction
    properties: dict[str, Any]  # Maps property name to Expression
