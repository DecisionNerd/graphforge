"""JSON Graph format loader.

Loads graphs from JSON Graph format with typed properties into GraphForge.
Converts PropertyValue objects to CypherValue types while preserving type information.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from graphforge.api import GraphForge
from graphforge.datasets.base import DatasetLoader
from graphforge.datasets.formats.json_graph import JSONGraph, PropertyValue
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
    CypherPoint,
    CypherString,
    CypherTime,
    CypherValue,
)


def property_value_to_cypher(prop_value: PropertyValue) -> CypherValue:
    """Convert a PropertyValue to a CypherValue.

    Args:
        prop_value: PropertyValue with type tag and value

    Returns:
        Corresponding CypherValue instance

    Raises:
        ValueError: If type tag is not supported or value is invalid
    """
    t = prop_value.t
    v = prop_value.v

    # Primitive types
    if t == "null":
        return CypherNull()
    if t == "bool":
        return CypherBool(v)
    if t == "int":
        return CypherInt(v)
    if t == "float":
        # Convert int to float if needed
        return CypherFloat(float(v))
    if t == "string":
        return CypherString(v)

    # Temporal types
    if t == "date":
        return CypherDate(v)  # Accepts ISO 8601 string
    if t == "datetime":
        return CypherDateTime(v)  # Accepts ISO 8601 string
    if t == "time":
        return CypherTime(v)  # Accepts ISO 8601 string
    if t == "duration":
        return CypherDuration(v)  # Accepts ISO 8601 duration string

    # Spatial types
    if t == "point":
        return CypherPoint(v)  # Accepts coordinate dict
    if t == "distance":
        return CypherDistance(float(v))

    # Collection types
    if t == "list":
        # Recursively convert list items
        list_items: list[CypherValue] = []
        for item in v:
            if isinstance(item, dict) and "t" in item and "v" in item:
                # Item is already a PropertyValue dict
                list_items.append(property_value_to_cypher(PropertyValue(**item)))
            else:
                # Item is a raw value (shouldn't happen with validation, but handle gracefully)
                raise ValueError(
                    f"List items must be PropertyValue objects, got {type(item).__name__}"
                )
        return CypherList(list_items)

    if t == "map":
        # Recursively convert map values
        map_items: dict[str, CypherValue] = {}
        for key, val in v.items():
            if isinstance(val, dict) and "t" in val and "v" in val:
                # Value is a PropertyValue dict
                map_items[key] = property_value_to_cypher(PropertyValue(**val))
            else:
                # Value is a raw value (shouldn't happen with validation, but handle gracefully)
                raise ValueError(
                    f"Map values must be PropertyValue objects, got {type(val).__name__}"
                )
        return CypherMap(map_items)

    raise ValueError(f"Unsupported type tag: {t!r}")


def convert_properties(properties: dict[str, PropertyValue]) -> dict[str, Any]:
    """Convert property dictionary from PropertyValue to Python native types.

    Args:
        properties: Dictionary mapping property names to PropertyValue objects

    Returns:
        Dictionary mapping property names to Python native types
    """
    return {key: property_value_to_cypher(val).to_python() for key, val in properties.items()}


class JSONGraphLoader(DatasetLoader):
    """Loader for JSON Graph format.

    Loads graphs from JSON files using the typed JSON Graph format.
    Validates structure with Pydantic and converts PropertyValue objects
    to CypherValue types.

    Example JSON format:
        {
          "nodes": [
            {
              "id": "n0",
              "labels": ["Person"],
              "properties": {
                "name": {"t": "string", "v": "Alice"},
                "age": {"t": "int", "v": 30}
              }
            }
          ],
          "edges": [
            {
              "id": "e0",
              "source": "n0",
              "target": "n1",
              "type": "KNOWS",
              "properties": {"weight": {"t": "float", "v": 0.8}}
            }
          ],
          "directed": true
        }
    """

    def load(self, gf: GraphForge, path: Path) -> None:
        """Load JSON Graph into GraphForge instance.

        Args:
            gf: GraphForge instance to load data into
            path: Path to JSON file

        Raises:
            FileNotFoundError: If JSON file doesn't exist
            ValidationError: If JSON doesn't match expected format
            ValueError: If JSON is malformed or contains invalid data
        """
        dataset_path = path
        if not dataset_path.exists():
            raise FileNotFoundError(f"JSON Graph file not found: {dataset_path}")

        # Load and parse JSON
        try:
            with dataset_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {dataset_path}: {e}") from e

        # Validate with Pydantic
        try:
            graph = JSONGraph(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid JSON Graph format: {e}") from e

        # Track node ID mapping (JSON ID -> GraphForge NodeRef)
        node_map = {}

        # Create nodes
        for node in graph.nodes:
            # Convert properties
            props = convert_properties(node.properties)

            # Create node with labels and properties
            node_ref = gf.create_node(labels=node.labels, **props)
            node_map[node.id] = node_ref

        # Create edges
        for edge in graph.edges:
            # Get source and target node references
            source_ref = node_map[edge.source]
            target_ref = node_map[edge.target]

            # Convert properties
            props = convert_properties(edge.properties)

            # Create relationship
            gf.create_relationship(source_ref, target_ref, edge.type, **props)

    def get_format(self) -> str:
        """Return the format name this loader handles.

        Returns:
            Format identifier "json_graph"
        """
        return "json_graph"
