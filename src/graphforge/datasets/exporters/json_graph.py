"""JSON Graph format exporter.

Exports GraphForge graphs to JSON Graph format with typed properties.
Converts CypherValue objects to PropertyValue format while preserving type information.
"""

import json
from pathlib import Path
from typing import Any

import isodate  # type: ignore[import-untyped]

from graphforge.api import GraphForge
from graphforge.datasets.formats.json_graph import (
    JSONGraph,
    JSONGraphEdge,
    JSONGraphNode,
    PropertyValue,
)
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


def cypher_value_to_property_value(cypher_val: CypherValue) -> PropertyValue:
    """Convert a CypherValue to a PropertyValue.

    Args:
        cypher_val: CypherValue instance

    Returns:
        PropertyValue with type tag and value

    Raises:
        ValueError: If CypherValue type is not supported
    """
    # Primitive types
    if isinstance(cypher_val, CypherNull):
        return PropertyValue(t="null", v=None)
    if isinstance(cypher_val, CypherBool):
        return PropertyValue(t="bool", v=cypher_val.value)
    if isinstance(cypher_val, CypherInt):
        return PropertyValue(t="int", v=cypher_val.value)
    if isinstance(cypher_val, CypherFloat):
        return PropertyValue(t="float", v=cypher_val.value)
    if isinstance(cypher_val, CypherString):
        return PropertyValue(t="string", v=cypher_val.value)

    # Temporal types
    if isinstance(cypher_val, CypherDate):
        # Convert date to ISO 8601 string
        return PropertyValue(t="date", v=cypher_val.value.isoformat())
    if isinstance(cypher_val, CypherDateTime):
        # Convert datetime to ISO 8601 string
        return PropertyValue(t="datetime", v=cypher_val.value.isoformat())
    if isinstance(cypher_val, CypherTime):
        # Convert time to ISO 8601 string
        return PropertyValue(t="time", v=cypher_val.value.isoformat())
    if isinstance(cypher_val, CypherDuration):
        # Convert duration to ISO 8601 duration string
        duration_str = isodate.duration_isoformat(cypher_val.value)
        return PropertyValue(t="duration", v=duration_str)

    # Spatial types
    if isinstance(cypher_val, CypherPoint):
        # Point is already a dict with coordinates
        return PropertyValue(t="point", v=cypher_val.value)
    if isinstance(cypher_val, CypherDistance):
        return PropertyValue(t="distance", v=cypher_val.value)

    # Collection types
    if isinstance(cypher_val, CypherList):
        # Recursively convert list items to PropertyValue dicts
        list_items: list[dict[str, Any]] = []
        for item in cypher_val.value:
            prop_val = cypher_value_to_property_value(item)
            list_items.append({"t": prop_val.t, "v": prop_val.v})
        return PropertyValue(t="list", v=list_items)

    if isinstance(cypher_val, CypherMap):
        # Recursively convert map values to PropertyValue dicts
        map_items: dict[str, dict[str, Any]] = {}
        for key, val in cypher_val.value.items():
            prop_val = cypher_value_to_property_value(val)
            map_items[key] = {"t": prop_val.t, "v": prop_val.v}
        return PropertyValue(t="map", v=map_items)

    raise ValueError(f"Unsupported CypherValue type: {type(cypher_val).__name__}")


class JSONGraphExporter:
    """Exporter for JSON Graph format.

    Exports GraphForge graphs to JSON files using the typed JSON Graph format.
    Queries all nodes and edges from the graph and converts CypherValue properties
    to PropertyValue format.

    Example usage:
        exporter = JSONGraphExporter()
        exporter.export(gf, Path("output.json"), metadata={"name": "My Graph"})
    """

    def export(
        self, gf: GraphForge, output_path: Path, metadata: dict[str, Any] | None = None
    ) -> None:
        """Export GraphForge graph to JSON Graph format.

        Args:
            gf: GraphForge instance to export
            output_path: Path to write JSON file
            metadata: Optional metadata to include in the graph

        Raises:
            ValueError: If graph data is invalid
        """
        # Query all nodes
        node_results = gf.execute("MATCH (n) RETURN id(n) AS id, labels(n) AS labels, n AS node")

        # Build nodes list
        nodes = []
        node_id_map = {}  # Map NodeRef -> JSON ID

        for i, row in enumerate(node_results):
            node_id = f"n{i}"
            node_ref = row["node"]

            # Get labels from result (CypherList of CypherString)
            labels_val = row["labels"]
            if hasattr(labels_val, "value"):
                # Extract string values from CypherString objects
                labels = [label.value for label in labels_val.value]
            else:
                labels = []

            # Get properties from the NodeRef
            properties = {}
            if hasattr(node_ref, "properties") and node_ref.properties:
                for key, val in node_ref.properties.items():
                    if not key.startswith("_"):  # Skip internal properties
                        properties[key] = cypher_value_to_property_value(val)

            nodes.append(JSONGraphNode(id=node_id, labels=labels, properties=properties))

            # Store mapping from internal ID to JSON ID
            internal_id = row["id"].value if hasattr(row["id"], "value") else row["id"]
            node_id_map[internal_id] = node_id

        # Query all edges
        edge_results = gf.execute(
            "MATCH (a)-[r]->(b) RETURN id(a) AS source_id, id(b) AS target_id, "
            "type(r) AS rel_type, r AS relationship"
        )

        # Build edges list
        edges = []
        for i, row in enumerate(edge_results):
            edge_id = f"e{i}"

            # Get source and target IDs
            source_internal = (
                row["source_id"].value if hasattr(row["source_id"], "value") else row["source_id"]
            )
            target_internal = (
                row["target_id"].value if hasattr(row["target_id"], "value") else row["target_id"]
            )

            source_id = node_id_map[source_internal]
            target_id = node_id_map[target_internal]

            # Get relationship type
            rel_type_val = row["rel_type"]
            rel_type = rel_type_val.value if hasattr(rel_type_val, "value") else str(rel_type_val)

            # Get properties from the EdgeRef
            relationship = row["relationship"]
            properties = {}
            if hasattr(relationship, "properties") and relationship.properties:
                for key, val in relationship.properties.items():
                    if not key.startswith("_"):  # Skip internal properties
                        properties[key] = cypher_value_to_property_value(val)

            edges.append(
                JSONGraphEdge(
                    id=edge_id,
                    source=source_id,
                    target=target_id,
                    type=rel_type,
                    properties=properties,
                )
            )

        # Create JSONGraph
        graph = JSONGraph(
            nodes=nodes,
            edges=edges,
            directed=True,  # GraphForge uses directed graphs
            metadata=metadata or {},
        )

        # Convert to dict and write JSON
        graph_dict = {
            "nodes": [
                {
                    "id": node.id,
                    "labels": node.labels,
                    "properties": {
                        key: {"t": val.t, "v": val.v} for key, val in node.properties.items()
                    },
                }
                for node in graph.nodes
            ],
            "edges": [
                {
                    "id": edge.id,
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.type,
                    "properties": {
                        key: {"t": val.t, "v": val.v} for key, val in edge.properties.items()
                    },
                }
                for edge in graph.edges
            ],
            "directed": graph.directed,
            "metadata": graph.metadata,
        }

        # Write to file
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(graph_dict, f, indent=2, ensure_ascii=False)
