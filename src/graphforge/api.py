"""High-level API for GraphForge.

This module provides the main public interface for GraphForge.
"""

from pathlib import Path

from graphforge.executor.executor import QueryExecutor
from graphforge.parser.parser import CypherParser
from graphforge.planner.planner import QueryPlanner
from graphforge.storage.memory import Graph
from graphforge.storage.sqlite_backend import SQLiteBackend
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
            path: Optional path to persistent storage (SQLite database file)
                  If None, uses in-memory storage.
                  If provided, loads existing graph or creates new database.

        Examples:
            >>> # In-memory graph (lost on exit)
            >>> gf = GraphForge()

            >>> # Persistent graph (saved to disk)
            >>> gf = GraphForge("my-graph.db")
            >>> # ... create nodes ...
            >>> gf.close()  # Save to disk

            >>> # Later, load the graph
            >>> gf = GraphForge("my-graph.db")  # Graph is still there
        """
        # Initialize storage backend
        if path:
            # Use SQLite for persistence
            self.backend = SQLiteBackend(Path(path))
            self.graph = self._load_graph_from_backend()
            # Set next IDs based on existing data
            self._next_node_id = self.backend.get_next_node_id()
            self._next_edge_id = self.backend.get_next_edge_id()
        else:
            # Use in-memory storage
            self.backend = None  # type: ignore[assignment]
            self.graph = Graph()
            self._next_node_id = 1
            self._next_edge_id = 1

        # Track if database has been closed
        self._closed = False

        # Transaction state
        self._in_transaction = False
        self._transaction_snapshot = None

        # Initialize query execution components
        self.parser = CypherParser()
        self.planner = QueryPlanner()
        self.executor = QueryExecutor(self.graph, graphforge=self)

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

    def begin(self):
        """Begin an explicit transaction.

        Starts a new transaction by taking a snapshot of the current graph state.
        Changes made after begin() can be committed or rolled back.

        Raises:
            RuntimeError: If already in a transaction

        Examples:
            >>> gf = GraphForge("my-graph.db")
            >>> gf.begin()
            >>> alice = gf.create_node(['Person'], name='Alice')
            >>> gf.commit()  # Changes are saved

            >>> gf.begin()
            >>> bob = gf.create_node(['Person'], name='Bob')
            >>> gf.rollback()  # Bob is removed
        """
        if self._in_transaction:
            raise RuntimeError("Already in a transaction. Commit or rollback first.")

        # Take snapshot of current state
        self._transaction_snapshot = self.graph.snapshot()  # type: ignore[assignment]
        self._in_transaction = True

    def commit(self):
        """Commit the current transaction.

        Saves all changes made since begin() to the database (if using persistence).
        Clears the transaction snapshot.

        Raises:
            RuntimeError: If not in a transaction

        Examples:
            >>> gf = GraphForge("my-graph.db")
            >>> gf.begin()
            >>> gf.create_node(['Person'], name='Alice')
            >>> gf.commit()  # Changes are now permanent
        """
        if not self._in_transaction:
            raise RuntimeError("Not in a transaction. Call begin() first.")

        # Save to backend if persistence is enabled
        if self.backend:
            self._save_graph_to_backend()

        # Clear transaction state
        self._in_transaction = False
        self._transaction_snapshot = None

    def rollback(self):
        """Roll back the current transaction.

        Reverts all changes made since begin() by restoring the snapshot.
        Works for both in-memory and persistent graphs.

        Raises:
            RuntimeError: If not in a transaction

        Examples:
            >>> gf = GraphForge("my-graph.db")
            >>> gf.begin()
            >>> gf.create_node(['Person'], name='Alice')
            >>> results = gf.execute("MATCH (p:Person) RETURN count(*)")
            >>> # count is 1
            >>> gf.rollback()  # Alice is gone
            >>> results = gf.execute("MATCH (p:Person) RETURN count(*)")
            >>> # count is 0
        """
        if not self._in_transaction:
            raise RuntimeError("Not in a transaction. Call begin() first.")

        # Restore graph from snapshot
        self.graph.restore(self._transaction_snapshot)  # type: ignore[arg-type]

        # Rollback SQLite transaction if using persistence
        if self.backend:
            self.backend.rollback()

        # Clear transaction state
        self._in_transaction = False
        self._transaction_snapshot = None

    def close(self):
        """Save graph and close database.

        If using SQLite backend, saves all nodes and edges to disk and
        commits the transaction. Safe to call multiple times.

        If in an active transaction, the transaction is committed before closing.

        Examples:
            >>> gf = GraphForge("my-graph.db")
            >>> # ... create nodes and edges ...
            >>> gf.close()  # Save to disk
        """
        if self.backend and not self._closed:
            # Auto-commit any pending transaction
            if self._in_transaction:
                self.commit()
            else:
                # Save changes if not in explicit transaction
                self._save_graph_to_backend()

            self.backend.close()
            self._closed = True

    def _load_graph_from_backend(self) -> Graph:
        """Load graph from SQLite backend.

        Returns:
            Graph instance populated with nodes and edges from database
        """
        graph = Graph()

        # Load all nodes
        nodes = self.backend.load_all_nodes()
        node_map = {}  # Map node_id to NodeRef

        for node in nodes:
            graph.add_node(node)
            node_map[node.id] = node

        # Load all edges (returns dict of edge data)
        edges_data = self.backend.load_all_edges()

        # Reconstruct EdgeRef instances with actual NodeRef objects
        for edge_id, (edge_type, src_id, dst_id, properties) in edges_data.items():
            src_node = node_map[src_id]
            dst_node = node_map[dst_id]

            edge = EdgeRef(
                id=edge_id,
                type=edge_type,
                src=src_node,
                dst=dst_node,
                properties=properties,
            )

            graph.add_edge(edge)

        return graph

    def _save_graph_to_backend(self):
        """Save graph to SQLite backend."""
        # Save all nodes
        for node in self.graph.get_all_nodes():
            self.backend.save_node(node)

        # Save all edges
        for edge in self.graph.get_all_edges():
            self.backend.save_edge(edge)

        # Commit transaction
        self.backend.commit()
