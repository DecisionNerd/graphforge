"""Unit tests for Graph storage edge cases.

Tests for node/edge replacement and other edge cases.
"""

import pytest

from graphforge.storage.memory import Graph
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import CypherInt, CypherString


class TestGraphNodeEdgeCases:
    """Tests for node storage edge cases."""

    def test_replace_node_with_same_id(self):
        """Replacing a node with same ID updates label index."""
        graph = Graph()

        # Add node with Person label
        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        graph.add_node(node1)

        # Replace with node having different labels
        node2 = NodeRef(id=1, labels=frozenset(["Employee"]), properties={})
        graph.add_node(node2)

        # Old label should be removed from index
        assert graph.get_nodes_by_label("Person") == []
        # New label should be in index
        assert len(graph.get_nodes_by_label("Employee")) == 1

    def test_add_node_initializes_adjacency_lists(self):
        """Adding a node initializes empty adjacency lists."""
        graph = Graph()
        node = NodeRef(id=1, labels=frozenset(), properties={})
        graph.add_node(node)

        # Adjacency lists should be empty but initialized
        assert graph.get_outgoing_edges(1) == []
        assert graph.get_incoming_edges(1) == []


class TestGraphEdgeEdgeCases:
    """Tests for edge storage edge cases."""

    def test_replace_edge_with_same_id(self):
        """Replacing an edge with same ID updates indexes."""
        graph = Graph()

        # Add nodes
        node1 = NodeRef(id=1, labels=frozenset(), properties={})
        node2 = NodeRef(id=2, labels=frozenset(), properties={})
        node3 = NodeRef(id=3, labels=frozenset(), properties={})
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        # Add edge
        edge1 = EdgeRef(id=10, type="KNOWS", src=node1, dst=node2, properties={})
        graph.add_edge(edge1)

        # Replace with different edge (same ID, different nodes and type)
        edge2 = EdgeRef(id=10, type="LIKES", src=node1, dst=node3, properties={})
        graph.add_edge(edge2)

        # Old edge should be removed from adjacency lists and type index
        assert len(graph.get_outgoing_edges(1)) == 1
        assert graph.get_outgoing_edges(1)[0].dst.id == 3
        assert graph.get_edges_by_type("KNOWS") == []
        assert len(graph.get_edges_by_type("LIKES")) == 1

    def test_add_edge_with_missing_source_node(self):
        """Adding edge with missing source node raises ValueError."""
        graph = Graph()
        node = NodeRef(id=2, labels=frozenset(), properties={})
        graph.add_node(node)

        # Try to add edge with non-existent source
        fake_src = NodeRef(id=999, labels=frozenset(), properties={})
        edge = EdgeRef(id=1, type="KNOWS", src=fake_src, dst=node, properties={})

        with pytest.raises(ValueError, match="Source node 999 not found"):
            graph.add_edge(edge)

    def test_add_edge_with_missing_destination_node(self):
        """Adding edge with missing destination node raises ValueError."""
        graph = Graph()
        node = NodeRef(id=1, labels=frozenset(), properties={})
        graph.add_node(node)

        # Try to add edge with non-existent destination
        fake_dst = NodeRef(id=999, labels=frozenset(), properties={})
        edge = EdgeRef(id=1, type="KNOWS", src=node, dst=fake_dst, properties={})

        with pytest.raises(ValueError, match="Destination node 999 not found"):
            graph.add_edge(edge)


class TestGraphSnapshotRestore:
    """Tests for graph snapshot and restore functionality."""

    def test_snapshot_and_restore(self):
        """Snapshot captures full graph state and restore recovers it."""
        graph = Graph()

        # Create graph with nodes and edges
        node1 = NodeRef(
            id=1, labels=frozenset(["Person"]), properties={"name": CypherString("Alice")}
        )
        node2 = NodeRef(
            id=2, labels=frozenset(["Person"]), properties={"name": CypherString("Bob")}
        )
        graph.add_node(node1)
        graph.add_node(node2)

        edge = EdgeRef(
            id=10, type="KNOWS", src=node1, dst=node2, properties={"since": CypherInt(2020)}
        )
        graph.add_edge(edge)

        # Take snapshot
        snapshot = graph.snapshot()

        # Modify graph
        node3 = NodeRef(
            id=3, labels=frozenset(["Person"]), properties={"name": CypherString("Charlie")}
        )
        graph.add_node(node3)

        # Restore from snapshot
        graph.restore(snapshot)

        # Graph should be back to original state
        assert graph.node_count() == 2
        assert graph.edge_count() == 1
        assert graph.get_node(3) is None
        assert len(graph.get_nodes_by_label("Person")) == 2

    def test_snapshot_is_deep_copy(self):
        """Snapshot creates independent copy of graph data."""
        graph = Graph()
        node = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        graph.add_node(node)

        snapshot = graph.snapshot()

        # Modify graph after snapshot
        node2 = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        graph.add_node(node2)

        # Snapshot should not be affected
        assert len(snapshot["nodes"]) == 1
        assert graph.node_count() == 2
