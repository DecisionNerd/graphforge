"""High-level API for GraphForge.

This module provides the main public interface for GraphForge.
"""

import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from graphforge.executor.executor import QueryExecutor
from graphforge.parser.parser import CypherParser
from graphforge.planner.planner import QueryPlanner
from graphforge.storage.memory import Graph
from graphforge.storage.sqlite_backend import SQLiteBackend
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import (
    CypherBool,
    CypherDate,
    CypherDateTime,
    CypherDuration,
    CypherFloat,
    CypherInt,
    CypherList,
    CypherMap,
    CypherNull,
    CypherPoint,
    CypherString,
    CypherTime,
)

# Pydantic models for API validation


class QueryInput(BaseModel):
    """Validates openCypher query input."""

    query: str = Field(..., min_length=1, description="openCypher query string")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query is not just whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v

    model_config = {"frozen": True}


class NodeInput(BaseModel):
    """Validates node creation input."""

    labels: list[str] = Field(default_factory=list, description="Node labels")

    @field_validator("labels")
    @classmethod
    def validate_labels(cls, v: list[str]) -> list[str]:
        """Validate label names."""
        for label in v:
            if not label:
                raise ValueError("Label cannot be empty string")
            if not label[0].isalpha():
                raise ValueError(f"Label must start with a letter: {label}")
            if not label.replace("_", "").isalnum():
                raise ValueError(f"Label must contain only alphanumeric and underscore: {label}")
        return v

    model_config = {"frozen": True}


class RelationshipInput(BaseModel):
    """Validates relationship creation input."""

    rel_type: str = Field(..., min_length=1, description="Relationship type")

    @field_validator("rel_type")
    @classmethod
    def validate_rel_type(cls, v: str) -> str:
        """Validate relationship type name."""
        if not v[0].isalpha() and v[0] != "_":
            raise ValueError(f"Relationship type must start with letter or underscore: {v}")
        if not v.replace("_", "").isalnum():
            raise ValueError(
                f"Relationship type must contain only alphanumeric and underscore: {v}"
            )
        return v

    model_config = {"frozen": True}


class DatasetNameInput(BaseModel):
    """Validates dataset name input."""

    name: str = Field(..., min_length=1, description="Dataset name")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate dataset name is not just whitespace."""
        if not v.strip():
            raise ValueError("Dataset name cannot be empty or whitespace only")
        return v

    model_config = {"frozen": True}


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

        Raises:
            ValueError: If path is empty string or whitespace only

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
        # Validate path if provided
        if path is not None:
            if isinstance(path, str) and not path.strip():
                raise ValueError("Path cannot be empty or whitespace only")

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
        self.executor = QueryExecutor(self.graph, graphforge=self, planner=self.planner)

    @classmethod
    def from_dataset(cls, name: str, path: str | Path | None = None) -> "GraphForge":
        """Create a new GraphForge instance and load a dataset into it.

        This is a convenience method that combines instance creation with dataset loading.

        Args:
            name: Dataset name (e.g., "snap-ego-facebook", "neo4j-movie-graph")
            path: Optional path for persistent storage

        Returns:
            GraphForge instance with dataset loaded

        Raises:
            ValueError: If dataset name is empty or whitespace only
            pydantic.ValidationError: If dataset name fails validation

        Examples:
            >>> # Load dataset into in-memory graph
            >>> gf = GraphForge.from_dataset("snap-ego-facebook")
            >>>
            >>> # Load dataset into persistent storage
            >>> gf = GraphForge.from_dataset("neo4j-movie-graph", "movies.db")
        """
        from graphforge.datasets import load_dataset

        # Validate dataset name
        DatasetNameInput(name=name)

        instance = cls(path)
        load_dataset(instance, name)  # nosec B615 - Not Hugging Face, our own dataset loader
        return instance

    def execute(self, query: str) -> list[dict]:
        """Execute an openCypher query.

        Args:
            query: openCypher query string

        Returns:
            List of result rows as dictionaries

        Raises:
            ValueError: If query is empty or whitespace only
            pydantic.ValidationError: If query fails validation

        Examples:
            >>> gf = GraphForge()
            >>> results = gf.execute("MATCH (n) RETURN n LIMIT 10")
        """
        # Validate query input
        QueryInput(query=query)

        # Parse query
        ast = self.parser.parse(query)

        # Check if this is a UNION query
        if isinstance(ast, dict) and ast.get("type") == "union":
            # Handle UNION query: plan each branch separately
            branch_operators = []
            for branch_ast in ast["branches"]:
                branch_ops = self.planner.plan(branch_ast)
                branch_operators.append(branch_ops)

            # Create Union operator
            from graphforge.planner.operators import Union

            union_op = Union(branches=branch_operators, all=ast["all"])
            operators = [union_op]
        else:
            # Regular query
            operators = self.planner.plan(ast)

        # Execute
        results = self.executor.execute(operators)

        return results

    def create_node(self, labels: list[str] | None = None, **properties: Any) -> NodeRef:
        """Create a node with labels and properties.

        Automatically assigns a unique node ID and converts Python values
        to CypherValue types.

        Args:
            labels: List of label strings (e.g., ['Person', 'Employee'])
            **properties: Property key-value pairs as Python types.
                Values are converted to CypherValue types:
                - int → CypherInt
                - float → CypherFloat
                - str → CypherString
                - bool → CypherBool
                - None → CypherNull
                - dict with {x, y} or {latitude, longitude} → CypherPoint
                - dict (other) → CypherMap
                - list → CypherList
                - date → CypherDate
                - datetime → CypherDateTime
                - time → CypherTime
                - timedelta → CypherDuration

        Returns:
            NodeRef for the created node

        Raises:
            ValueError: If labels are invalid (empty, don't start with letter, etc.)
            pydantic.ValidationError: If labels fail validation
            TypeError: If property values are unsupported types

        Examples:
            >>> gf = GraphForge()
            >>> alice = gf.create_node(['Person'], name='Alice', age=30)
            >>> bob = gf.create_node(['Person', 'Employee'], name='Bob', salary=50000)
            >>> # Create node with spatial property (Cartesian coordinates)
            >>> office = gf.create_node(['Place'], name='Office', location={"x": 1.0, "y": 2.0})
            >>> # Create node with geographic coordinates
            >>> sf = gf.create_node(
            ...     ['City'], name='SF', location={"latitude": 37.7749, "longitude": -122.4194}
            ... )
            >>> # Query the created nodes
            >>> results = gf.execute("MATCH (p:Person) RETURN p.name")
        """
        # Validate labels
        NodeInput(labels=labels or [])

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
        self, src: NodeRef, dst: NodeRef, rel_type: str, **properties: Any
    ) -> EdgeRef:
        """Create a relationship between two nodes.

        Automatically assigns a unique edge ID and converts Python values
        to CypherValue types.

        Args:
            src: Source node (NodeRef)
            dst: Destination node (NodeRef)
            rel_type: Relationship type (e.g., 'KNOWS', 'WORKS_AT')
            **properties: Property key-value pairs as Python types.
                Values are converted to CypherValue types (same as create_node).
                Supports Point coordinates: {"x": 1.0, "y": 2.0} or
                {"latitude": 37.7, "longitude": -122.4}

        Returns:
            EdgeRef for the created relationship

        Raises:
            ValueError: If rel_type is invalid (empty, doesn't start with letter/underscore, etc.)
            TypeError: If src or dst are not NodeRef instances
            pydantic.ValidationError: If rel_type fails validation

        Examples:
            >>> gf = GraphForge()
            >>> alice = gf.create_node(['Person'], name='Alice')
            >>> bob = gf.create_node(['Person'], name='Bob')
            >>> knows = gf.create_relationship(alice, bob, 'KNOWS', since=2020)
            >>> # Relationship with spatial property
            >>> travels = gf.create_relationship(
            ...     alice, bob, 'TRAVELS_TO', distance_from={"x": 0.0, "y": 0.0}
            ... )
            >>> # Query relationships
            >>> results = gf.execute("MATCH (a)-[r:KNOWS]->(b) RETURN a.name, b.name")
        """
        # Validate inputs
        if not isinstance(src, NodeRef):
            raise TypeError(f"src must be a NodeRef, got {type(src).__name__}")
        if not isinstance(dst, NodeRef):
            raise TypeError(f"dst must be a NodeRef, got {type(dst).__name__}")

        RelationshipInput(rel_type=rel_type)

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
            value: Python value (str, int, float, bool, None, list, dict,
                   date, datetime, time, timedelta)

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

        # Handle temporal types (check datetime before date since datetime is subclass of date)
        if isinstance(value, datetime.datetime):
            return CypherDateTime(value)
        if isinstance(value, datetime.date):
            return CypherDate(value)
        if isinstance(value, datetime.time):
            return CypherTime(value)
        if isinstance(value, datetime.timedelta):
            return CypherDuration(value)

        # Handle isodate.Duration (used for ISO 8601 durations with years/months)
        try:
            import isodate  # type: ignore[import-untyped]

            if isinstance(value, isodate.Duration):
                return CypherDuration(value)
        except ImportError:
            pass

        # Handle list (recursively convert elements)
        if isinstance(value, list):
            return CypherList([self._to_cypher_value(item) for item in value])

        # Handle dict - check for Point coordinates before CypherMap
        if isinstance(value, dict):
            keys = set(value.keys())

            # Detect Cartesian coordinates: {x, y} or {x, y, z}, optionally with crs
            # Valid: {"x", "y"}, {"x", "y", "crs"}, {"x", "y", "z"}, {"x", "y", "z", "crs"}
            cartesian_2d = {"x", "y"}
            cartesian_2d_crs = {"x", "y", "crs"}
            cartesian_3d = {"x", "y", "z"}
            cartesian_3d_crs = {"x", "y", "z", "crs"}

            if keys in (cartesian_2d, cartesian_2d_crs, cartesian_3d, cartesian_3d_crs):
                try:
                    return CypherPoint(value)
                except (ValueError, TypeError):
                    # Invalid coordinates (out of range or non-numeric), fall through to CypherMap
                    pass

            # Detect Geographic coordinates: {latitude, longitude}, optionally with crs
            # Valid: {"latitude", "longitude"}, {"latitude", "longitude", "crs"}
            geographic = {"latitude", "longitude"}
            geographic_crs = {"latitude", "longitude", "crs"}

            if keys in (geographic, geographic_crs):
                try:
                    return CypherPoint(value)
                except (ValueError, TypeError):
                    # Invalid coordinates (out of range or non-numeric), fall through to CypherMap
                    pass

            # Default to CypherMap (recursively convert values)
            return CypherMap({key: self._to_cypher_value(val) for key, val in value.items()})

        # Unsupported type
        raise TypeError(
            f"Unsupported property value type: {type(value).__name__}. "
            "Supported types: str, int, float, bool, None, list, dict, "
            "date, datetime, time, timedelta"
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
