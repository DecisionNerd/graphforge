"""JSON Graph interchange format with typed properties.

This module defines the JSON Graph format for lossless interchange of graph data
with typed property values. The format preserves CypherValue type information
through explicit type tags.

Format specification:
- Nodes have IDs, labels (list of strings), and typed properties
- Edges have IDs, source/target references, type string, and typed properties
- Properties use typed-value wrappers: {"t": "type", "v": value}
- Supports all CypherValue types: primitives, temporal, spatial, collections

Example JSON Graph:
    {
      "nodes": [
        {
          "id": "n0",
          "labels": ["Person"],
          "properties": {
            "name": {"t": "string", "v": "Alice"},
            "age": {"t": "int", "v": 30},
            "birthday": {"t": "date", "v": "1990-01-01"}
          }
        }
      ],
      "edges": [
        {
          "id": "e0",
          "source": "n0",
          "target": "n1",
          "type": "KNOWS",
          "properties": {
            "weight": {"t": "float", "v": 0.8}
          }
        }
      ],
      "directed": true,
      "metadata": {}
    }
"""

from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


class PropertyValue(BaseModel):
    """Typed property value in JSON Graph format.

    Uses explicit type tags to preserve CypherValue type information:
    - Primitive types: null, bool, int, float, string
    - Temporal types: date, datetime, time, duration
    - Spatial types: point, distance
    - Collection types: list, map

    Examples:
        {"t": "string", "v": "Alice"}
        {"t": "int", "v": 30}
        {"t": "date", "v": "1990-01-01"}
        {"t": "point", "v": {"x": 1.0, "y": 2.0, "crs": "cartesian"}}
    """

    t: str = Field(
        ...,
        description=(
            "Type tag: null, bool, int, float, string, "
            "date, datetime, time, duration, point, distance, list, map"
        ),
    )
    v: Any = Field(..., description="Value in appropriate format for the type")

    @field_validator("t")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate type tag is supported."""
        valid_types = {
            # Primitive types
            "null",
            "bool",
            "int",
            "float",
            "string",
            # Temporal types
            "date",
            "datetime",
            "time",
            "duration",
            # Spatial types
            "point",
            "distance",
            # Collection types
            "list",
            "map",
        }
        if v not in valid_types:
            raise ValueError(f"Invalid type tag: {v!r}. Must be one of: {sorted(valid_types)}")
        return v

    @model_validator(mode="after")
    def validate_value_for_type(self) -> "PropertyValue":
        """Validate value matches the declared type."""
        t = self.t
        v = self.v

        # null: value must be None
        if t == "null":
            if v is not None:
                raise ValueError(f"Type 'null' requires value None, got {v!r}")

        # bool: value must be boolean
        elif t == "bool":
            if not isinstance(v, bool):
                raise ValueError(f"Type 'bool' requires boolean value, got {type(v).__name__}")

        # int: value must be integer
        elif t == "int":
            if not isinstance(v, int) or isinstance(v, bool):
                raise ValueError(f"Type 'int' requires integer value, got {type(v).__name__}")

        # float: value must be number
        elif t == "float":
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                raise ValueError(f"Type 'float' requires numeric value, got {type(v).__name__}")

        # string: value must be string
        elif t == "string":
            if not isinstance(v, str):
                raise ValueError(f"Type 'string' requires string value, got {type(v).__name__}")

        # date: value must be ISO 8601 date string (YYYY-MM-DD)
        elif t == "date":
            if not isinstance(v, str):
                raise ValueError(
                    f"Type 'date' requires ISO 8601 date string, got {type(v).__name__}"
                )
            # Basic validation (full validation happens during conversion)
            if len(v) < 8 or "-" not in v:
                raise ValueError(f"Type 'date' requires ISO 8601 format (YYYY-MM-DD), got {v!r}")

        # datetime: value must be ISO 8601 datetime string
        elif t == "datetime":
            if not isinstance(v, str):
                raise ValueError(
                    f"Type 'datetime' requires ISO 8601 datetime string, got {type(v).__name__}"
                )
            if "T" not in v:
                raise ValueError(
                    f"Type 'datetime' requires ISO 8601 format (YYYY-MM-DDTHH:MM:SS), got {v!r}"
                )

        # time: value must be ISO 8601 time string
        elif t == "time":
            if not isinstance(v, str):
                raise ValueError(
                    f"Type 'time' requires ISO 8601 time string, got {type(v).__name__}"
                )
            if ":" not in v:
                raise ValueError(f"Type 'time' requires ISO 8601 format (HH:MM:SS), got {v!r}")

        # duration: value must be ISO 8601 duration string (PnYnMnDTnHnMnS)
        elif t == "duration":
            if not isinstance(v, str):
                raise ValueError(
                    f"Type 'duration' requires ISO 8601 duration string, got {type(v).__name__}"
                )
            if not v.startswith("P"):
                raise ValueError(f"Type 'duration' requires ISO 8601 format (P...), got {v!r}")

        # point: value must be coordinate object
        elif t == "point":
            if not isinstance(v, dict):
                raise ValueError(f"Type 'point' requires coordinate object, got {type(v).__name__}")
            # Must have either (x, y) or (latitude, longitude)
            has_cartesian = "x" in v and "y" in v
            has_geographic = "latitude" in v and "longitude" in v
            if not (has_cartesian or has_geographic):
                keys_list = list(v.keys())
                raise ValueError(
                    f"Type 'point' requires (x, y) or (latitude, longitude), got keys: {keys_list}"
                )

        # distance: value must be non-negative number
        elif t == "distance":
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                raise ValueError(f"Type 'distance' requires numeric value, got {type(v).__name__}")
            if v < 0:
                raise ValueError(f"Type 'distance' requires non-negative value, got {v}")

        # list: value must be array of PropertyValue objects
        elif t == "list":
            if not isinstance(v, list):
                raise ValueError(f"Type 'list' requires array value, got {type(v).__name__}")
            # Recursively validate each item
            for idx, item in enumerate(v):
                if not isinstance(item, dict):
                    raise ValueError(
                        f"Type 'list' item at index {idx} must be PropertyValue object, "
                        f"got {type(item).__name__}"
                    )
                if "t" not in item or "v" not in item:
                    raise ValueError(
                        f"Type 'list' item at index {idx} must have 't' and 'v' keys, "
                        f"got keys: {list(item.keys())}"
                    )
                # Recursively validate nested PropertyValue
                try:
                    PropertyValue(t=item["t"], v=item["v"])
                except (ValueError, ValidationError) as e:
                    raise ValueError(
                        f"Type 'list' item at index {idx} validation failed: {e}"
                    ) from e

        # map: value must be object with PropertyValue values
        elif t == "map":
            if not isinstance(v, dict):
                raise ValueError(f"Type 'map' requires object value, got {type(v).__name__}")
            # Recursively validate each value
            for key, val in v.items():
                if not isinstance(val, dict):
                    raise ValueError(
                        f"Type 'map' value at key {key!r} must be PropertyValue object, "
                        f"got {type(val).__name__}"
                    )
                if "t" not in val or "v" not in val:
                    raise ValueError(
                        f"Type 'map' value at key {key!r} must have 't' and 'v' keys, "
                        f"got keys: {list(val.keys())}"
                    )
                # Recursively validate nested PropertyValue
                try:
                    PropertyValue(t=val["t"], v=val["v"])
                except (ValueError, ValidationError) as e:
                    raise ValueError(
                        f"Type 'map' value at key {key!r} validation failed: {e}"
                    ) from e

        return self

    model_config = {"frozen": True}


class JSONGraphNode(BaseModel):
    """Node in JSON Graph format.

    A node has a unique ID, optional labels (list of strings), and typed properties.

    Example:
        {
          "id": "n0",
          "labels": ["Person", "Customer"],
          "properties": {
            "name": {"t": "string", "v": "Alice"},
            "age": {"t": "int", "v": 30}
          }
        }
    """

    id: str = Field(..., description="Unique node identifier", min_length=1)
    labels: list[str] = Field(
        default_factory=list, description="Node labels (empty list if unlabeled)"
    )
    properties: dict[str, PropertyValue] = Field(
        default_factory=dict, description="Node properties with type information"
    )

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate node ID is non-empty."""
        if not v.strip():
            raise ValueError("Node ID cannot be empty or whitespace")
        return v

    @field_validator("labels")
    @classmethod
    def validate_labels(cls, v: list[str]) -> list[str]:
        """Validate labels are non-empty strings."""
        for label in v:
            if not label.strip():
                raise ValueError("Node labels cannot be empty or whitespace")
        return v

    model_config = {"frozen": True}


class JSONGraphEdge(BaseModel):
    """Edge in JSON Graph format.

    An edge has a unique ID, source/target node IDs, a type string, and typed properties.

    Example:
        {
          "id": "e0",
          "source": "n0",
          "target": "n1",
          "type": "KNOWS",
          "properties": {
            "weight": {"t": "float", "v": 0.8}
          }
        }
    """

    id: str = Field(..., description="Unique edge identifier", min_length=1)
    source: str = Field(..., description="Source node ID", min_length=1)
    target: str = Field(..., description="Target node ID", min_length=1)
    type: str = Field(default="RELATED_TO", description="Edge type (relationship type)")
    properties: dict[str, PropertyValue] = Field(
        default_factory=dict, description="Edge properties with type information"
    )

    @field_validator("id", "source", "target")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate IDs are non-empty."""
        if not v.strip():
            raise ValueError("Edge ID, source, and target cannot be empty or whitespace")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate edge type is non-empty."""
        if not v.strip():
            raise ValueError("Edge type cannot be empty or whitespace")
        return v

    model_config = {"frozen": True}


class JSONGraph(BaseModel):
    """Complete JSON Graph with nodes, edges, and metadata.

    The top-level format for graph interchange. Contains nodes, edges, directionality
    flag, and optional metadata.

    Example:
        {
          "nodes": [...],
          "edges": [...],
          "directed": true,
          "metadata": {"name": "Example Graph", "version": "1.0"}
        }
    """

    nodes: list[JSONGraphNode] = Field(
        default_factory=list, description="List of nodes in the graph"
    )
    edges: list[JSONGraphEdge] = Field(
        default_factory=list, description="List of edges in the graph"
    )
    directed: bool = Field(default=True, description="Whether edges are directed")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Optional metadata about the graph"
    )

    @model_validator(mode="after")
    def validate_edge_references(self) -> "JSONGraph":
        """Validate edge source/target references point to existing nodes."""
        node_ids = {node.id for node in self.nodes}

        for edge in self.edges:
            if edge.source not in node_ids:
                raise ValueError(
                    f"Edge {edge.id!r} references non-existent source node {edge.source!r}"
                )
            if edge.target not in node_ids:
                raise ValueError(
                    f"Edge {edge.id!r} references non-existent target node {edge.target!r}"
                )

        return self

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "JSONGraph":
        """Validate node and edge IDs are unique."""
        # Check node ID uniqueness
        node_ids = [node.id for node in self.nodes]
        duplicate_nodes = {nid for nid in node_ids if node_ids.count(nid) > 1}
        if duplicate_nodes:
            raise ValueError(f"Duplicate node IDs found: {sorted(duplicate_nodes)}")

        # Check edge ID uniqueness
        edge_ids = [edge.id for edge in self.edges]
        duplicate_edges = {eid for eid in edge_ids if edge_ids.count(eid) > 1}
        if duplicate_edges:
            raise ValueError(f"Duplicate edge IDs found: {sorted(duplicate_edges)}")

        return self

    model_config = {"frozen": True}
