"""Unit tests for SQLiteBackend adjacency loading methods.

Tests for load_adjacency_out and load_adjacency_in methods.
"""

from pathlib import Path
import tempfile

from graphforge.storage.sqlite_backend import SQLiteBackend
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import CypherString


class TestSQLiteBackendAdjacency:
    """Tests for SQLite backend adjacency loading."""

    def test_load_adjacency_out_empty(self):
        """Loading outgoing adjacency from empty database returns empty dict."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            backend = SQLiteBackend(db_path)
            adjacency = backend.load_adjacency_out()
            assert adjacency == {}
            backend.close()
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_load_adjacency_in_empty(self):
        """Loading incoming adjacency from empty database returns empty dict."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            backend = SQLiteBackend(db_path)
            adjacency = backend.load_adjacency_in()
            assert adjacency == {}
            backend.close()
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_load_adjacency_out_with_edges(self):
        """Loading outgoing adjacency with edges returns correct mapping."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            backend = SQLiteBackend(db_path)

            # Create nodes and edges
            node1 = NodeRef(
                id=1, labels=frozenset(["Person"]), properties={"name": CypherString("Alice")}
            )
            node2 = NodeRef(
                id=2, labels=frozenset(["Person"]), properties={"name": CypherString("Bob")}
            )
            node3 = NodeRef(
                id=3, labels=frozenset(["Person"]), properties={"name": CypherString("Charlie")}
            )

            backend.save_node(node1)
            backend.save_node(node2)
            backend.save_node(node3)

            edge1 = EdgeRef(id=10, type="KNOWS", src=node1, dst=node2, properties={})
            edge2 = EdgeRef(id=11, type="KNOWS", src=node1, dst=node3, properties={})

            backend.save_edge(edge1)
            backend.save_edge(edge2)
            backend.commit()

            # Load outgoing adjacency
            adjacency = backend.load_adjacency_out()

            # Node 1 should have two outgoing edges
            assert 1 in adjacency
            assert set(adjacency[1]) == {10, 11}

            # Nodes 2 and 3 have no outgoing edges
            assert 2 not in adjacency or adjacency[2] == []
            assert 3 not in adjacency or adjacency[3] == []

            backend.close()
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_load_adjacency_in_with_edges(self):
        """Loading incoming adjacency with edges returns correct mapping."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            backend = SQLiteBackend(db_path)

            # Create nodes and edges
            node1 = NodeRef(
                id=1, labels=frozenset(["Person"]), properties={"name": CypherString("Alice")}
            )
            node2 = NodeRef(
                id=2, labels=frozenset(["Person"]), properties={"name": CypherString("Bob")}
            )
            node3 = NodeRef(
                id=3, labels=frozenset(["Person"]), properties={"name": CypherString("Charlie")}
            )

            backend.save_node(node1)
            backend.save_node(node2)
            backend.save_node(node3)

            edge1 = EdgeRef(id=10, type="KNOWS", src=node1, dst=node2, properties={})
            edge2 = EdgeRef(id=20, type="KNOWS", src=node3, dst=node2, properties={})

            backend.save_edge(edge1)
            backend.save_edge(edge2)
            backend.commit()

            # Load incoming adjacency
            adjacency = backend.load_adjacency_in()

            # Node 2 should have two incoming edges
            assert 2 in adjacency
            assert set(adjacency[2]) == {10, 20}

            # Nodes 1 and 3 have no incoming edges
            assert 1 not in adjacency or adjacency[1] == []
            assert 3 not in adjacency or adjacency[3] == []

            backend.close()
        finally:
            if db_path.exists():
                db_path.unlink()

    def test_load_adjacency_multiple_edges_per_node(self):
        """Loading adjacency with multiple edges per node."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            backend = SQLiteBackend(db_path)

            # Create nodes
            node1 = NodeRef(id=1, labels=frozenset(), properties={})
            node2 = NodeRef(id=2, labels=frozenset(), properties={})

            backend.save_node(node1)
            backend.save_node(node2)

            # Create multiple edges from node1 to node2
            for i in range(5):
                edge = EdgeRef(id=10 + i, type="REL", src=node1, dst=node2, properties={})
                backend.save_edge(edge)

            backend.commit()

            # Load outgoing adjacency
            adj_out = backend.load_adjacency_out()
            assert len(adj_out[1]) == 5
            assert set(adj_out[1]) == {10, 11, 12, 13, 14}

            # Load incoming adjacency
            adj_in = backend.load_adjacency_in()
            assert len(adj_in[2]) == 5
            assert set(adj_in[2]) == {10, 11, 12, 13, 14}

            backend.close()
        finally:
            if db_path.exists():
                db_path.unlink()
