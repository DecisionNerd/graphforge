"""Runtime value types for openCypher.

This module implements the openCypher type system including:
- Scalar types: NULL, BOOLEAN, INTEGER, FLOAT, STRING
- Temporal types: DATE, DATETIME, TIME, DURATION
- Collection types: LIST, MAP, PATH

Values follow openCypher semantics including:
- NULL propagation in comparisons and operations
- Type-aware equality and comparison
- Conversion to/from Python types
"""

import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from dateutil import parser as dateutil_parser
import isodate  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from graphforge.types.graph import EdgeRef, NodeRef


class CypherType(Enum):
    """openCypher value types."""

    NULL = "NULL"
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    STRING = "STRING"
    DATE = "DATE"
    DATETIME = "DATETIME"
    TIME = "TIME"
    DURATION = "DURATION"
    POINT = "POINT"
    DISTANCE = "DISTANCE"
    LIST = "LIST"
    MAP = "MAP"
    PATH = "PATH"


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
            if self.type in (CypherType.LIST, CypherType.MAP, CypherType.PATH):
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

        # Boolean comparison (False < True)
        if self.type == CypherType.BOOLEAN and other.type == CypherType.BOOLEAN:
            return CypherBool(self.value < other.value)

        # List comparison (lexicographic)
        if self.type == CypherType.LIST and other.type == CypherType.LIST:
            for a, b in zip(self.value, other.value):
                a_lt_b = a.less_than(b)
                if isinstance(a_lt_b, CypherNull):
                    return CypherNull()
                if a_lt_b.value:
                    return CypherBool(True)
                b_lt_a = b.less_than(a)
                if isinstance(b_lt_a, CypherNull):
                    return CypherNull()
                if b_lt_a.value:
                    return CypherBool(False)
            # All elements equal so far, shorter list is less
            return CypherBool(len(self.value) < len(other.value))

        # Temporal comparison (DATE, DATETIME, TIME, DURATION)
        if self._is_temporal() and other._is_temporal():
            # Only allow comparison of same temporal types
            if self.type == other.type:
                return CypherBool(self.value < other.value)
            return CypherBool(False)

        # Other comparisons are not supported in this simplified model
        return CypherBool(False)

    def _is_numeric(self) -> bool:
        """Check if this value is a numeric type."""
        return self.type in (CypherType.INTEGER, CypherType.FLOAT)

    def _is_temporal(self) -> bool:
        """Check if this value is a temporal type."""
        return self.type in (
            CypherType.DATE,
            CypherType.DATETIME,
            CypherType.TIME,
            CypherType.DURATION,
        )

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

        if self.type == CypherType.PATH:
            # Path equality: same nodes and relationships in same order
            # Cast to CypherPath for type safety
            if not isinstance(other, CypherPath):
                return CypherBool(False)
            self_path = self if isinstance(self, CypherPath) else None
            other_path = other if isinstance(other, CypherPath) else None
            if self_path is None or other_path is None:
                return CypherBool(False)

            # Compare lengths first
            if len(self_path.nodes) != len(other_path.nodes):
                return CypherBool(False)

            # Compare node IDs (identity-based)
            for n1, n2 in zip(self_path.nodes, other_path.nodes):
                if n1.id != n2.id:
                    return CypherBool(False)

            # Compare relationship IDs (identity-based)
            for r1, r2 in zip(self_path.relationships, other_path.relationships):
                if r1.id != r2.id:
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
        if self.type == CypherType.PATH:
            # Return dict with nodes and relationships
            if isinstance(self, CypherPath):
                return {"nodes": self.nodes, "relationships": self.relationships}
            return self.value
        # Temporal types already store Python datetime/timedelta objects
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


class CypherDate(CypherValue):
    """Represents a date value in openCypher.

    Stores a Python datetime.date object. Supports ISO 8601 date strings.
    """

    def __init__(self, value: datetime.date | str):
        if isinstance(value, str):
            # Parse ISO 8601 date string
            parsed = dateutil_parser.parse(value)
            value = parsed.date()
        elif isinstance(value, datetime.datetime):
            # Extract date component if datetime passed
            value = value.date()
        super().__init__(value, CypherType.DATE)

    def __repr__(self) -> str:
        return f"CypherDate({self.value.isoformat()!r})"


class CypherDateTime(CypherValue):
    """Represents a datetime value in openCypher.

    Stores a Python datetime.datetime object with timezone support.
    Supports ISO 8601 datetime strings.
    """

    def __init__(self, value: datetime.datetime | str):
        if isinstance(value, str):
            # Parse ISO 8601 datetime string
            value = dateutil_parser.parse(value)
        super().__init__(value, CypherType.DATETIME)

    def __repr__(self) -> str:
        return f"CypherDateTime({self.value.isoformat()!r})"


class CypherTime(CypherValue):
    """Represents a time value in openCypher.

    Stores a Python datetime.time object with timezone support.
    Supports ISO 8601 time strings.
    """

    def __init__(self, value: datetime.time | datetime.datetime | str):
        if isinstance(value, str):
            # Parse ISO 8601 time string
            parsed = dateutil_parser.parse(value)
            # Use timetz() to preserve timezone information
            value = parsed.timetz()
        elif isinstance(value, datetime.datetime):
            # Extract time component with timezone if datetime passed
            value = value.timetz()
        super().__init__(value, CypherType.TIME)

    def __repr__(self) -> str:
        return f"CypherTime({self.value.isoformat()!r})"


class CypherDuration(CypherValue):
    """Represents a duration value in openCypher.

    Stores a Python datetime.timedelta or isodate.Duration object.
    Supports ISO 8601 duration strings. When parsing ISO 8601 strings with
    years/months (e.g., "P1Y2M"), stores an isodate.Duration; otherwise stores
    a datetime.timedelta.
    """

    def __init__(self, value: datetime.timedelta | isodate.Duration | str):
        if isinstance(value, str):
            # Parse ISO 8601 duration string (e.g., "P1Y2M10DT2H30M")
            # Returns timedelta for simple durations, isodate.Duration for year/month
            value = isodate.parse_duration(value)
        super().__init__(value, CypherType.DURATION)

    def __repr__(self) -> str:
        return f"CypherDuration({isodate.duration_isoformat(self.value)!r})"


class CypherPoint(CypherValue):
    """Represents a point value in openCypher.

    Stores a dictionary with coordinate information. Supports:
    - 2D Cartesian: {"x": float, "y": float, "crs": "cartesian"}
    - 3D Cartesian: {"x": float, "y": float, "z": float, "crs": "cartesian-3d"}
    - WGS84 Geographic: {"latitude": float, "longitude": float, "crs": "wgs-84"}

    The coordinate reference system (crs) is optional and inferred from keys.
    """

    def __init__(self, coordinates: dict[str, float]):
        """Initialize a point from coordinate dictionary.

        Args:
            coordinates: Dict with coordinate keys (x/y or latitude/longitude)

        Raises:
            ValueError: If coordinates are invalid or incomplete
        """
        # Validate and normalize coordinates
        if "x" in coordinates and "y" in coordinates:
            # Cartesian coordinates
            x = float(coordinates["x"])
            y = float(coordinates["y"])
            if "z" in coordinates:
                # 3D Cartesian
                z = float(coordinates["z"])
                value = {"x": x, "y": y, "z": z, "crs": "cartesian-3d"}
            else:
                # 2D Cartesian
                value = {"x": x, "y": y, "crs": "cartesian"}
        elif "latitude" in coordinates and "longitude" in coordinates:
            # Geographic coordinates (WGS-84)
            lat = float(coordinates["latitude"])
            lon = float(coordinates["longitude"])
            # Validate latitude/longitude ranges
            if not -90 <= lat <= 90:
                raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
            if not -180 <= lon <= 180:
                raise ValueError(f"Longitude must be between -180 and 180, got {lon}")
            value = {"latitude": lat, "longitude": lon, "crs": "wgs-84"}
        else:
            raise ValueError(
                "Point requires either (x, y) or (latitude, longitude) coordinates, "
                f"got: {list(coordinates.keys())}"
            )

        super().__init__(value, CypherType.POINT)

    def __repr__(self) -> str:
        return f"CypherPoint({self.value!r})"


class CypherDistance(CypherValue):
    """Represents a distance value in openCypher.

    Stores a float representing the Euclidean distance between two points.
    For WGS-84 points, uses the Haversine formula to compute great-circle distance.
    """

    def __init__(self, value: float):
        """Initialize a distance value.

        Args:
            value: Distance as a float (must be non-negative)

        Raises:
            ValueError: If distance is negative
        """
        if value < 0:
            raise ValueError(f"Distance must be non-negative, got {value}")
        super().__init__(float(value), CypherType.DISTANCE)

    def __repr__(self) -> str:
        return f"CypherDistance({self.value})"


class CypherList(CypherValue):
    """Represents a list value in openCypher."""

    def __init__(self, value: list["CypherValue"]):
        super().__init__(value, CypherType.LIST)


class CypherMap(CypherValue):
    """Represents a map (dictionary) value in openCypher."""

    def __init__(self, value: dict[str, "CypherValue"]):
        super().__init__(value, CypherType.MAP)


class CypherPath(CypherValue):
    """Represents a path through the graph.

    A path consists of an alternating sequence of nodes and relationships:
    node -> edge -> node -> edge -> node

    Attributes:
        nodes: List of NodeRef objects in the path (N nodes)
        relationships: List of EdgeRef objects connecting the nodes (N-1 relationships)

    The path structure ensures that:
    - len(relationships) == len(nodes) - 1
    - relationships[i] connects nodes[i] to nodes[i+1]

    Examples:
        >>> # Path with 3 nodes: A -> B -> C
        >>> path = CypherPath(
        ...     nodes=[node_a, node_b, node_c],
        ...     relationships=[edge_ab, edge_bc]
        ... )
        >>> path.length()  # Number of relationships
        2
        >>> len(path.nodes)
        3
    """

    def __init__(self, nodes: list["NodeRef"], relationships: list["EdgeRef"]):
        """Initialize a path from nodes and relationships.

        Args:
            nodes: List of NodeRef objects in the path
            relationships: List of EdgeRef objects connecting the nodes

        Raises:
            ValueError: If path structure is invalid
        """
        from graphforge.types.graph import EdgeRef, NodeRef

        # Validate types
        if not all(isinstance(n, NodeRef) for n in nodes):
            raise TypeError("All nodes must be NodeRef instances")
        if not all(isinstance(r, EdgeRef) for r in relationships):
            raise TypeError("All relationships must be EdgeRef instances")

        # Validate path structure
        if len(nodes) == 0:
            raise ValueError("Path must contain at least one node")
        if len(relationships) != len(nodes) - 1:
            raise ValueError(
                f"Path must have exactly len(nodes)-1 relationships: "
                f"got {len(nodes)} nodes and {len(relationships)} relationships"
            )

        # Validate connectivity
        for i, rel in enumerate(relationships):
            node_a = nodes[i]
            node_b = nodes[i + 1]
            # Check that relationship connects consecutive nodes
            # Allow traversal in either direction (for undirected or reversed patterns)
            forward_match = rel.src.id == node_a.id and rel.dst.id == node_b.id
            reverse_match = rel.src.id == node_b.id and rel.dst.id == node_a.id

            if not (forward_match or reverse_match):
                raise ValueError(
                    f"Relationship at index {i} does not connect nodes {i} and {i + 1}: "
                    f"relationship goes from {rel.src.id} to {rel.dst.id}, "
                    f"but path expects connection between {node_a.id} and {node_b.id}"
                )

        # Store as tuple for immutability
        self.nodes = nodes
        self.relationships = relationships

        # Store tuple of (nodes, relationships) as value for compatibility
        super().__init__((tuple(nodes), tuple(relationships)), CypherType.PATH)

    def length(self) -> int:
        """Return the length of the path (number of relationships)."""
        return len(self.relationships)

    def __repr__(self) -> str:
        """Readable string representation."""
        node_ids = " -> ".join(str(n.id) for n in self.nodes)
        return f"CypherPath([{node_ids}], length={self.length()})"


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
    # Temporal types (check datetime before date since datetime is subclass of date)
    if isinstance(value, datetime.datetime):
        return CypherDateTime(value)
    if isinstance(value, datetime.date):
        return CypherDate(value)
    if isinstance(value, datetime.time):
        return CypherTime(value)
    if isinstance(value, datetime.timedelta):
        return CypherDuration(value)
    # Collections
    if isinstance(value, list):
        return CypherList([from_python(item) for item in value])
    if isinstance(value, dict):
        return CypherMap({key: from_python(val) for key, val in value.items()})

    raise TypeError(f"Cannot convert Python type {type(value).__name__} to CypherValue")
