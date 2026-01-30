"""Graph element types for GraphForge.

This module implements the runtime graph element model:
- NodeRef: Runtime reference to a node with id, labels, and properties
- EdgeRef: Runtime reference to a relationship with type, directionality, and properties

Element identity is defined by ID, and elements are hashable for use in
sets and dictionaries.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NodeRef:
    """Runtime reference to a node in the graph.

    Nodes have:
    - A unique stable ID
    - Zero or more labels (frozenset of strings)
    - Zero or more properties (dict mapping string to CypherValue)

    Identity is defined by ID - two NodeRefs with the same ID are considered
    the same node, even if they have different labels or properties.

    Nodes are immutable and hashable, allowing them to be used in sets and
    as dictionary keys.

    Examples:
        >>> node = NodeRef(
        ...     id=1,
        ...     labels=frozenset(["Person", "Employee"]),
        ...     properties={"name": CypherString("Alice"), "age": CypherInt(30)}
        ... )
        >>> node.id
        1
        >>> "Person" in node.labels
        True
        >>> node.properties["name"].value
        'Alice'
    """

    id: int | str
    labels: frozenset[str]
    properties: dict[str, Any]  # Maps str -> CypherValue

    def __hash__(self) -> int:
        """Hash based on ID only."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Equality based on ID only."""
        if not isinstance(other, NodeRef):
            return NotImplemented
        return self.id == other.id

    def __repr__(self) -> str:
        """Readable string representation."""
        labels_str = ":".join(sorted(self.labels)) if self.labels else ""
        if labels_str:
            return f"NodeRef(id={self.id!r}, labels={labels_str})"
        return f"NodeRef(id={self.id!r})"


@dataclass(frozen=True)
class EdgeRef:
    """Runtime reference to a relationship (edge) in the graph.

    Edges have:
    - A unique stable ID
    - A relationship type (string)
    - A source node (NodeRef)
    - A destination node (NodeRef)
    - Intrinsic directionality (src -> dst)
    - Zero or more properties (dict mapping string to CypherValue)

    Identity is defined by ID - two EdgeRefs with the same ID are considered
    the same relationship, even if they have different types or endpoints.

    Edges are immutable and hashable, allowing them to be used in sets and
    as dictionary keys.

    Examples:
        >>> alice = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        >>> bob = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        >>> edge = EdgeRef(
        ...     id=10,
        ...     type="KNOWS",
        ...     src=alice,
        ...     dst=bob,
        ...     properties={"since": CypherInt(2020)}
        ... )
        >>> edge.type
        'KNOWS'
        >>> edge.src.id
        1
        >>> edge.dst.id
        2
    """

    id: int | str
    type: str
    src: NodeRef
    dst: NodeRef
    properties: dict[str, Any]  # Maps str -> CypherValue

    def __hash__(self) -> int:
        """Hash based on ID only."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Equality based on ID only."""
        if not isinstance(other, EdgeRef):
            return NotImplemented
        return self.id == other.id

    def __repr__(self) -> str:
        """Readable string representation."""
        return (
            f"EdgeRef(id={self.id!r}, type={self.type!r}, src={self.src.id!r}, dst={self.dst.id!r})"
        )
