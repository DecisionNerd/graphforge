"""GraphML loader for NetworkRepository and other GraphML-format datasets."""

import gzip
from pathlib import Path
from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element  # nosec B405 - Only used for type hints, not parsing

import defusedxml.ElementTree as ET  # noqa: N817

from graphforge.datasets.base import DatasetLoader

if TYPE_CHECKING:
    from graphforge import GraphForge


class GraphMLLoader(DatasetLoader):
    """Loader for GraphML-format graph datasets.

    GraphML is an XML-based format for graphs. It supports:
    - Typed properties (boolean, int, float, string)
    - Node and edge attributes
    - Default values
    - Directed and undirected graphs

    Features:
    - Type-aware property parsing
    - Configurable label extraction
    - Multi-label support (comma-separated)
    - Compressed file support (.graphml.gz)
    - Comprehensive error handling

    Example GraphML:
        <graphml>
          <key id="d0" for="node" attr.name="label" attr.type="string"/>
          <key id="d1" for="node" attr.name="age" attr.type="int"/>
          <graph edgedefault="directed">
            <node id="n0">
              <data key="d0">Person</data>
              <data key="d1">30</data>
            </node>
            <edge source="n0" target="n1"/>
          </graph>
        </graphml>
    """

    def __init__(self, label_key: str = "label", default_label: str = "Node"):
        """Initialize GraphML loader.

        Args:
            label_key: Property key to extract labels from (default: "label")
            default_label: Default label if none found (default: "Node")
        """
        self.label_key = label_key
        self.default_label = default_label

    def load(self, gf: "GraphForge", path: Path) -> None:
        """Load GraphML file into GraphForge.

        Args:
            gf: GraphForge instance to load data into
            path: Path to GraphML file (may be gzipped)

        Raises:
            ValueError: If GraphML format is invalid
            FileNotFoundError: If file doesn't exist
        """
        if not path.exists():
            raise FileNotFoundError(f"GraphML file not found: {path}")

        # Parse XML (handles .gz automatically)
        try:
            if path.suffix == ".gz":
                with gzip.open(path, "rt", encoding="utf-8") as f:
                    tree = ET.parse(f)
            else:
                tree = ET.parse(path)
        except ET.ParseError as e:
            raise ValueError(f"Invalid GraphML XML: {e}") from e

        root = tree.getroot()
        if root is None:
            raise ValueError("Empty GraphML document")

        # Extract namespace if present
        namespace = self._extract_namespace(root.tag)
        ns = {"graphml": namespace} if namespace else {}

        # Parse key declarations (schema)
        keys = self._parse_keys(root, ns)

        # Find the graph element
        graph = root.find("graphml:graph" if namespace else "graph", ns)
        if graph is None:
            raise ValueError("No <graph> element found in GraphML")

        # Check for unsupported nested graphs
        nested_graphs = graph.findall("graphml:graph" if namespace else "graph", ns)
        if nested_graphs:
            raise ValueError("Nested graphs are not supported")

        # Determine if graph is directed (default: directed)
        edgedefault = graph.get("edgedefault", "directed")
        is_directed = edgedefault == "directed"

        # Parse nodes
        node_map = self._parse_nodes(gf, graph, keys, ns)

        # Parse edges
        self._parse_edges(gf, graph, keys, node_map, ns, is_directed)

    def get_format(self) -> str:
        """Return format identifier.

        Returns:
            Format name: "graphml"
        """
        return "graphml"

    def _extract_namespace(self, tag: str) -> str:
        """Extract XML namespace from tag.

        Args:
            tag: XML tag (may include namespace)

        Returns:
            Namespace URL or empty string
        """
        if tag.startswith("{"):
            return tag[1 : tag.index("}")]
        return ""

    def _parse_keys(self, root: Element, ns: dict[str, str]) -> dict[str, dict[str, Any]]:
        """Parse key declarations (schema) from GraphML.

        Args:
            root: Root XML element
            ns: Namespace dict

        Returns:
            Dict mapping key IDs to their metadata:
            {
                "d0": {
                    "for": "node",
                    "name": "label",
                    "type": "string",
                    "default": "Person"
                }
            }
        """
        keys = {}
        for key in root.findall("graphml:key" if ns else "key", ns):
            key_id = key.get("id")
            if not key_id:
                continue

            key_info = {
                "for": key.get("for", "all"),
                "name": key.get("attr.name", key_id),
                "type": key.get("attr.type", "string"),
            }

            # Check for default value (preserve empty strings)
            # If <default> element exists, use its text (even if empty/None)
            default_elem = key.find("graphml:default" if ns else "default", ns)
            if default_elem is not None:
                # Treat None as empty string (for <default/> or <default></default>)
                key_info["default"] = default_elem.text if default_elem.text is not None else ""

            keys[key_id] = key_info

        return keys

    def _parse_nodes(
        self,
        gf: "GraphForge",
        graph: Element,
        keys: dict[str, dict[str, Any]],
        ns: dict[str, str],
    ) -> dict[str, Any]:
        """Parse nodes from GraphML.

        Args:
            gf: GraphForge instance
            graph: Graph XML element
            keys: Key declarations
            ns: Namespace dict

        Returns:
            Dict mapping node IDs to NodeRef instances

        Raises:
            ValueError: If duplicate node IDs found
        """
        node_map = {}

        for node_elem in graph.findall("graphml:node" if ns else "node", ns):
            node_id = node_elem.get("id")
            if not node_id:
                continue

            if node_id in node_map:
                raise ValueError(f"Duplicate node ID: {node_id}")

            # Parse properties
            properties = self._parse_data_elements(node_elem, keys, "node", ns)

            # Extract labels
            labels = self._extract_labels(properties)

            # Remove label property after extraction
            if self.label_key in properties:
                del properties[self.label_key]

            # Create node
            node_ref = gf.create_node(labels, **properties)
            node_map[node_id] = node_ref

        return node_map

    def _parse_edges(
        self,
        gf: "GraphForge",
        graph: Element,
        keys: dict[str, dict[str, Any]],
        node_map: dict[str, Any],
        ns: dict[str, str],
        is_directed: bool = True,
    ) -> None:
        """Parse edges from GraphML.

        Args:
            gf: GraphForge instance
            graph: Graph XML element
            keys: Key declarations
            node_map: Mapping of node IDs to NodeRef
            ns: Namespace dict
            is_directed: Whether the graph is directed (default: True)

        Raises:
            ValueError: If edge references invalid node
        """
        for edge_elem in graph.findall("graphml:edge" if ns else "edge", ns):
            source_id = edge_elem.get("source")
            target_id = edge_elem.get("target")

            if not source_id or not target_id:
                continue

            if source_id not in node_map:
                raise ValueError(f"Edge references non-existent source node: {source_id}")
            if target_id not in node_map:
                raise ValueError(f"Edge references non-existent target node: {target_id}")

            # Parse properties
            properties = self._parse_data_elements(edge_elem, keys, "edge", ns)

            # Create edge(s) based on directedness
            if is_directed:
                # Directed: create single relationship
                gf.create_relationship(
                    node_map[source_id], node_map[target_id], "RELATED_TO", **properties
                )
            else:
                # Undirected: create reciprocal relationships
                gf.create_relationship(
                    node_map[source_id], node_map[target_id], "RELATED_TO", **properties
                )
                gf.create_relationship(
                    node_map[target_id], node_map[source_id], "RELATED_TO", **properties
                )

    def _parse_data_elements(
        self,
        elem: Element,
        keys: dict[str, dict[str, Any]],
        context: str,
        ns: dict[str, str],
    ) -> dict[str, Any]:
        """Parse <data> elements into properties.

        Args:
            elem: Node or edge XML element
            keys: Key declarations
            context: "node" or "edge"
            ns: Namespace dict

        Returns:
            Dict of property name → Python value

        Raises:
            ValueError: If data references undefined key
        """
        properties = {}

        # Apply defaults from key declarations
        for key_id, key_info in keys.items():
            if key_info["for"] in (context, "all") and "default" in key_info:
                prop_name = key_info["name"]
                prop_type = key_info["type"]
                properties[prop_name] = self._convert_value(
                    key_info["default"], prop_type, key_id=key_id, prop_name=prop_name
                )

        # Parse <data> elements
        for data_elem in elem.findall("graphml:data" if ns else "data", ns):
            data_key_id = data_elem.get("key")
            if not data_key_id:
                continue

            if data_key_id not in keys:
                raise ValueError(f"Data references undefined key: {data_key_id}")

            key_info = keys[data_key_id]

            # Skip if wrong context
            if key_info["for"] not in (context, "all"):
                continue

            # Get value
            value = data_elem.text
            if value is None:
                continue

            prop_name = key_info["name"]
            prop_type = key_info["type"]

            properties[prop_name] = self._convert_value(
                value, prop_type, key_id=data_key_id, prop_name=prop_name
            )

        return properties

    def _convert_value(
        self, value: str, value_type: str, key_id: str | None = None, prop_name: str | None = None
    ) -> Any:
        """Convert GraphML value to Python type with error handling.

        Args:
            value: String value from GraphML
            value_type: GraphML type (boolean, int, long, float, double, string)
            key_id: Optional key ID for error context
            prop_name: Optional property name for error context

        Returns:
            Python value (bool, int, float, str)

        Raises:
            ValueError: If conversion fails with context information
        """
        context = f" for key '{key_id}' (property '{prop_name}')" if key_id else ""

        try:
            if value_type == "boolean":
                # GraphML boolean can be "true"/"false" or "1"/"0"
                return value.lower() in ("true", "1")
            elif value_type in ("int", "long"):
                return int(value)
            elif value_type in ("float", "double"):
                return float(value)
            else:  # string or unknown types default to string
                return value
        except (ValueError, TypeError, AttributeError) as e:
            raise ValueError(
                f"Failed to convert value '{value}' to type '{value_type}'{context}"
            ) from e

    def _extract_labels(self, properties: dict[str, Any]) -> list[str]:
        """Extract labels from properties.

        Supports comma-separated multi-labels: "Person,Customer" → ["Person", "Customer"]

        Args:
            properties: Property dict

        Returns:
            List of label strings
        """
        if self.label_key not in properties:
            return [self.default_label]

        label_value = properties[self.label_key]

        # Handle string labels (may be comma-separated)
        if isinstance(label_value, str):
            labels = [label.strip() for label in label_value.split(",") if label.strip()]
            return labels if labels else [self.default_label]

        # Non-string label values use default
        return [self.default_label]
