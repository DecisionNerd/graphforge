"""SQLite storage backend for GraphForge.

This module implements durable graph storage using SQLite with WAL mode.
"""

from pathlib import Path
import sqlite3

from graphforge.storage.serialization import (
    deserialize_labels,
    deserialize_properties,
    serialize_labels,
    serialize_properties,
)
from graphforge.types.graph import EdgeRef, NodeRef


class SQLiteBackend:
    """SQLite storage backend with WAL mode for durability.

    Provides ACID guarantees and concurrent readers through SQLite's
    WAL (Write-Ahead Logging) mode.

    Schema:
        - nodes: (id, labels, properties)
        - edges: (id, type, src_id, dst_id, properties)
        - adjacency_out: (node_id, edge_id) for outgoing edges
        - adjacency_in: (node_id, edge_id) for incoming edges
    """

    def __init__(self, db_path: Path):
        """Initialize SQLite backend.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self._closed = False

        # Configure SQLite for durability and concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")  # Single writer, multiple readers
        self.conn.execute("PRAGMA synchronous=FULL")  # Durability guarantee
        self.conn.execute("PRAGMA foreign_keys=ON")  # Referential integrity

        # Create schema if needed
        self._init_schema()

    def _init_schema(self):
        """Create database schema if it doesn't exist."""
        cursor = self.conn.cursor()

        # Nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY,
                labels BLOB NOT NULL,
                properties BLOB NOT NULL
            )
        """)

        # Edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY,
                type TEXT NOT NULL,
                src_id INTEGER NOT NULL,
                dst_id INTEGER NOT NULL,
                properties BLOB NOT NULL,
                FOREIGN KEY (src_id) REFERENCES nodes(id),
                FOREIGN KEY (dst_id) REFERENCES nodes(id)
            )
        """)

        # Adjacency lists for graph-native traversal
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adjacency_out (
                node_id INTEGER NOT NULL,
                edge_id INTEGER NOT NULL,
                PRIMARY KEY (node_id, edge_id),
                FOREIGN KEY (node_id) REFERENCES nodes(id),
                FOREIGN KEY (edge_id) REFERENCES edges(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adjacency_in (
                node_id INTEGER NOT NULL,
                edge_id INTEGER NOT NULL,
                PRIMARY KEY (node_id, edge_id),
                FOREIGN KEY (node_id) REFERENCES nodes(id),
                FOREIGN KEY (edge_id) REFERENCES edges(id)
            )
        """)

        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_nodes_labels ON nodes(labels)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst_id)
        """)

        self.conn.commit()

    def save_node(self, node: NodeRef):
        """Save a node to the database.

        Args:
            node: NodeRef to save
        """
        labels_blob = serialize_labels(node.labels)
        properties_blob = serialize_properties(node.properties)

        self.conn.execute(
            "INSERT OR REPLACE INTO nodes (id, labels, properties) VALUES (?, ?, ?)",
            (node.id, labels_blob, properties_blob),
        )

    def save_edge(self, edge: EdgeRef):
        """Save an edge to the database.

        Args:
            edge: EdgeRef to save
        """
        properties_blob = serialize_properties(edge.properties)

        # Save edge
        self.conn.execute(
            """INSERT OR REPLACE INTO edges (id, type, src_id, dst_id, properties)
               VALUES (?, ?, ?, ?, ?)""",
            (edge.id, edge.type, edge.src.id, edge.dst.id, properties_blob),
        )

        # Update adjacency lists
        self.conn.execute(
            "INSERT OR IGNORE INTO adjacency_out (node_id, edge_id) VALUES (?, ?)",
            (edge.src.id, edge.id),
        )

        self.conn.execute(
            "INSERT OR IGNORE INTO adjacency_in (node_id, edge_id) VALUES (?, ?)",
            (edge.dst.id, edge.id),
        )

    def load_all_nodes(self) -> list[NodeRef]:
        """Load all nodes from the database.

        Returns:
            List of NodeRef instances
        """
        cursor = self.conn.execute("SELECT id, labels, properties FROM nodes")
        nodes = []

        for row in cursor.fetchall():
            node_id, labels_blob, properties_blob = row
            labels = deserialize_labels(labels_blob)
            properties = deserialize_properties(properties_blob)

            nodes.append(NodeRef(id=node_id, labels=labels, properties=properties))

        return nodes

    def load_all_edges(self) -> dict[int, tuple]:
        """Load all edges from the database.

        Returns edge data as a dict mapping edge_id to (type, src_id, dst_id, properties).
        Caller must reconstruct EdgeRef with actual NodeRef instances.

        Returns:
            Dict mapping edge_id to (type, src_id, dst_id, properties)
        """
        cursor = self.conn.execute("SELECT id, type, src_id, dst_id, properties FROM edges")

        edges = {}
        for row in cursor.fetchall():
            edge_id, edge_type, src_id, dst_id, properties_blob = row
            properties = deserialize_properties(properties_blob)
            edges[edge_id] = (edge_type, src_id, dst_id, properties)

        return edges

    def load_adjacency_out(self) -> dict[int, list[int]]:
        """Load outgoing adjacency lists.

        Returns:
            Dict mapping node_id to list of outgoing edge_ids
        """
        cursor = self.conn.execute("SELECT node_id, edge_id FROM adjacency_out")

        adjacency: dict[int, list[int]] = {}
        for node_id, edge_id in cursor.fetchall():
            if node_id not in adjacency:
                adjacency[node_id] = []
            adjacency[node_id].append(edge_id)

        return adjacency

    def load_adjacency_in(self) -> dict[int, list[int]]:
        """Load incoming adjacency lists.

        Returns:
            Dict mapping node_id to list of incoming edge_ids
        """
        cursor = self.conn.execute("SELECT node_id, edge_id FROM adjacency_in")

        adjacency: dict[int, list[int]] = {}
        for node_id, edge_id in cursor.fetchall():
            if node_id not in adjacency:
                adjacency[node_id] = []
            adjacency[node_id].append(edge_id)

        return adjacency

    def get_next_node_id(self) -> int:
        """Get the next available node ID.

        Returns:
            Next node ID (max + 1, or 1 if no nodes exist)
        """
        cursor = self.conn.execute("SELECT MAX(id) FROM nodes")
        max_id = cursor.fetchone()[0]
        return (max_id or 0) + 1

    def get_next_edge_id(self) -> int:
        """Get the next available edge ID.

        Returns:
            Next edge ID (max + 1, or 1 if no edges exist)
        """
        cursor = self.conn.execute("SELECT MAX(id) FROM edges")
        max_id = cursor.fetchone()[0]
        return (max_id or 0) + 1

    def commit(self):
        """Commit the current transaction."""
        self.conn.commit()

    def rollback(self):
        """Roll back the current transaction."""
        self.conn.rollback()

    def close(self):
        """Close the database connection. Safe to call multiple times."""
        if not self._closed:
            self.conn.close()
            self._closed = True
