"""High-level API for GraphForge.

This module provides the main public interface for GraphForge.
"""

from pathlib import Path

from graphforge.executor.executor import QueryExecutor
from graphforge.parser.parser import CypherParser
from graphforge.planner.planner import QueryPlanner
from graphforge.storage.memory import Graph
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import (
    CypherBool,
    CypherFloat,
    CypherInt,
    CypherList,
    CypherMap,
    CypherNull,
    CypherString,
)


class GraphForge:
    """Main GraphForge interface for graph operations.

    GraphForge provides an embedded graph database with openCypher query support.

    Examples:
        >>> gf = GraphForge()
        >>> # Create nodes with Python API
        >>> alice = gf.create_node(['Person'], name='Alice', age=30)
        >>> bob = gf.create_node(['Person'], name='Bob', age=25)
        >>> # Create relationships
        >>> knows = gf.create_relationship(alice, bob, 'KNOWS', since=2020)
        >>> # Query with openCypher
        >>> results = gf.execute("MATCH (p:Person) WHERE p.age > 25 RETURN p.name")
    """

    def __init__(self, path: str | Path | None = None):
        """Initialize GraphForge.

        Args:
            path: Optional path to persistent storage (not yet implemented)
                  If None, uses in-memory storage.
        """
        # For now, always use in-memory storage
        self.graph = Graph()
        self.parser = CypherParser()
        self.planner = QueryPlanner()
        self.executor = QueryExecutor(self.graph)

        # ID generation for nodes and edges
        self._next_node_id = 1
        self._next_edge_id = 1

    def execute(self, query: str) -> list[dict]:
        """Execute an openCypher query.

        Args:
            query: openCypher query string

        Returns:
            List of result rows as dictionaries

        Examples:
            >>> gf = GraphForge()
            >>> results = gf.execute("MATCH (n) RETURN n LIMIT 10")
        """
        # Parse query
        ast = self.parser.parse(query)

        # Plan execution
        operators = self.planner.plan(ast)

        # Execute
        results = self.executor.execute(operators)

        return results

    def create_node(self, labels: list[str] | None = None, **properties) -> NodeRef:
        """Create a node with labels and properties.

        Automatically assigns a unique node ID and converts Python values
        to CypherValue types.

        Args:
            labels: List of label strings (e.g., ['Person', 'Employee'])
            **properties: Property key-value pairs as Python types
                         (str, int, float, bool, None, list, dict)

        Returns:
            NodeRef for the created node

        Examples:
            >>> gf = GraphForge()
            >>> alice = gf.create_node(['Person'], name='Alice', age=30)
            >>> bob = gf.create_node(['Person', 'Employee'], name='Bob', salary=50000)
            >>> # Query the created nodes
            >>> results = gf.execute("MATCH (p:Person) RETURN p.name")
        """
        # Convert properties to CypherValues
        cypher_properties = {key: self._to_cypher_value(value) for key, value in properties.items()}

        # Create node with auto-generated ID
        node = NodeRef(
            id=self._next_node_id,
            labels=frozenset(labels or []),
            properties=cypher_properties,
        )

        # Add to graph
        self.graph.add_node(node)

        # Increment ID for next node
        self._next_node_id += 1

        return node

    def create_relationship(
        self, src: NodeRef, dst: NodeRef, rel_type: str, **properties
    ) -> EdgeRef:
        """Create a relationship between two nodes.

        Automatically assigns a unique edge ID and converts Python values
        to CypherValue types.

        Args:
            src: Source node (NodeRef)
            dst: Destination node (NodeRef)
            rel_type: Relationship type (e.g., 'KNOWS', 'WORKS_AT')
            **properties: Property key-value pairs as Python types

        Returns:
            EdgeRef for the created relationship

        Examples:
            >>> gf = GraphForge()
            >>> alice = gf.create_node(['Person'], name='Alice')
            >>> bob = gf.create_node(['Person'], name='Bob')
            >>> knows = gf.create_relationship(alice, bob, 'KNOWS', since=2020)
            >>> # Query relationships
            >>> results = gf.execute("MATCH (a)-[r:KNOWS]->(b) RETURN a.name, b.name")
        """
        # Convert properties to CypherValues
        cypher_properties = {key: self._to_cypher_value(value) for key, value in properties.items()}

        # Create edge with auto-generated ID
        edge = EdgeRef(
            id=self._next_edge_id,
            type=rel_type,
            src=src,
            dst=dst,
            properties=cypher_properties,
        )

        # Add to graph
        self.graph.add_edge(edge)

        # Increment ID for next edge
        self._next_edge_id += 1

        return edge

    def _to_cypher_value(self, value):
        """Convert Python value to CypherValue type.

        Args:
            value: Python value (str, int, float, bool, None, list, dict)

        Returns:
            Corresponding CypherValue instance

        Raises:
            TypeError: If value type is not supported
        """
        # Handle None
        if value is None:
            return CypherNull()

        # Handle bool (must check before int since bool is subclass of int)
        if isinstance(value, bool):
            return CypherBool(value)

        # Handle int
        if isinstance(value, int):
            return CypherInt(value)

        # Handle float
        if isinstance(value, float):
            return CypherFloat(value)

        # Handle str
        if isinstance(value, str):
            return CypherString(value)

        # Handle list (recursively convert elements)
        if isinstance(value, list):
            return CypherList([self._to_cypher_value(item) for item in value])

        # Handle dict (recursively convert values)
        if isinstance(value, dict):
            return CypherMap({key: self._to_cypher_value(val) for key, val in value.items()})

        # Unsupported type
        raise TypeError(
            f"Unsupported property value type: {type(value).__name__}. "
            f"Supported types: str, int, float, bool, None, list, dict"
        )
