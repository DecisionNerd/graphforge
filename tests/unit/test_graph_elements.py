"""Tests for graph element types (NodeRef and EdgeRef).

Tests cover the runtime graph element model including:
- Node references with IDs, labels, and properties
- Edge references with source, destination, and type
- Identity semantics (equality by ID)
- Hashability for use in sets and dicts
"""

import pytest

from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import CypherInt, CypherString


@pytest.mark.unit
class TestNodeRef:
    """Tests for NodeRef."""

    def test_node_creation(self):
        """Node can be created with id, labels, and properties."""
        node = NodeRef(
            id=1, labels=frozenset(["Person"]), properties={"name": CypherString("Alice")}
        )
        assert node.id == 1
        assert "Person" in node.labels
        assert node.properties["name"].value == "Alice"

    def test_node_no_labels(self):
        """Node can be created without labels."""
        node = NodeRef(id=1, labels=frozenset(), properties={})
        assert len(node.labels) == 0

    def test_node_no_properties(self):
        """Node can be created without properties."""
        node = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        assert len(node.properties) == 0

    def test_node_multiple_labels(self):
        """Node can have multiple labels."""
        node = NodeRef(id=1, labels=frozenset(["Person", "Employee"]), properties={})
        assert len(node.labels) == 2
        assert "Person" in node.labels
        assert "Employee" in node.labels

    def test_node_equality_by_id(self):
        """Nodes with same ID are equal."""
        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node2 = NodeRef(id=1, labels=frozenset(["Employee"]), properties={"x": CypherInt(1)})
        assert node1 == node2

    def test_node_inequality_by_id(self):
        """Nodes with different IDs are not equal."""
        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node2 = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        assert node1 != node2

    def test_node_hashable(self):
        """Nodes can be used in sets and as dict keys."""
        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node2 = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        node_set = {node1, node2}
        assert len(node_set) == 2
        assert node1 in node_set

    def test_node_hash_by_id(self):
        """Nodes with same ID have same hash."""
        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node2 = NodeRef(id=1, labels=frozenset(["Employee"]), properties={})
        assert hash(node1) == hash(node2)

    def test_node_string_id(self):
        """Node can use string ID."""
        node = NodeRef(id="node-123", labels=frozenset(["Person"]), properties={})
        assert node.id == "node-123"

    def test_node_repr(self):
        """Node has readable string representation."""
        node = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        repr_str = repr(node)
        assert "NodeRef" in repr_str
        assert "1" in repr_str


@pytest.mark.unit
class TestEdgeRef:
    """Tests for EdgeRef."""

    def test_edge_creation(self):
        """Edge can be created with id, type, src, dst, and properties."""
        src = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        dst = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        edge = EdgeRef(
            id=10,
            type="KNOWS",
            src=src,
            dst=dst,
            properties={"since": CypherInt(2020)},
        )
        assert edge.id == 10
        assert edge.type == "KNOWS"
        assert edge.src == src
        assert edge.dst == dst
        assert edge.properties["since"].value == 2020

    def test_edge_directionality(self):
        """Edge has intrinsic directionality (src -> dst)."""
        src = NodeRef(id=1, labels=frozenset(), properties={})
        dst = NodeRef(id=2, labels=frozenset(), properties={})
        edge = EdgeRef(id=10, type="KNOWS", src=src, dst=dst, properties={})
        assert edge.src.id == 1
        assert edge.dst.id == 2

    def test_edge_no_properties(self):
        """Edge can be created without properties."""
        src = NodeRef(id=1, labels=frozenset(), properties={})
        dst = NodeRef(id=2, labels=frozenset(), properties={})
        edge = EdgeRef(id=10, type="KNOWS", src=src, dst=dst, properties={})
        assert len(edge.properties) == 0

    def test_edge_equality_by_id(self):
        """Edges with same ID are equal."""
        src = NodeRef(id=1, labels=frozenset(), properties={})
        dst = NodeRef(id=2, labels=frozenset(), properties={})
        edge1 = EdgeRef(id=10, type="KNOWS", src=src, dst=dst, properties={})
        edge2 = EdgeRef(id=10, type="LIKES", src=dst, dst=src, properties={})
        assert edge1 == edge2

    def test_edge_inequality_by_id(self):
        """Edges with different IDs are not equal."""
        src = NodeRef(id=1, labels=frozenset(), properties={})
        dst = NodeRef(id=2, labels=frozenset(), properties={})
        edge1 = EdgeRef(id=10, type="KNOWS", src=src, dst=dst, properties={})
        edge2 = EdgeRef(id=11, type="KNOWS", src=src, dst=dst, properties={})
        assert edge1 != edge2

    def test_edge_hashable(self):
        """Edges can be used in sets and as dict keys."""
        src = NodeRef(id=1, labels=frozenset(), properties={})
        dst = NodeRef(id=2, labels=frozenset(), properties={})
        edge1 = EdgeRef(id=10, type="KNOWS", src=src, dst=dst, properties={})
        edge2 = EdgeRef(id=11, type="KNOWS", src=src, dst=dst, properties={})
        edge_set = {edge1, edge2}
        assert len(edge_set) == 2
        assert edge1 in edge_set

    def test_edge_self_loop(self):
        """Edge can be a self-loop (src == dst)."""
        node = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        edge = EdgeRef(id=10, type="LIKES", src=node, dst=node, properties={})
        assert edge.src == edge.dst

    def test_edge_string_id(self):
        """Edge can use string ID."""
        src = NodeRef(id=1, labels=frozenset(), properties={})
        dst = NodeRef(id=2, labels=frozenset(), properties={})
        edge = EdgeRef(id="edge-abc", type="KNOWS", src=src, dst=dst, properties={})
        assert edge.id == "edge-abc"

    def test_edge_repr(self):
        """Edge has readable string representation."""
        src = NodeRef(id=1, labels=frozenset(), properties={})
        dst = NodeRef(id=2, labels=frozenset(), properties={})
        edge = EdgeRef(id=10, type="KNOWS", src=src, dst=dst, properties={})
        repr_str = repr(edge)
        assert "EdgeRef" in repr_str
        assert "KNOWS" in repr_str


@pytest.mark.unit
class TestGraphElementInteraction:
    """Tests for interactions between nodes and edges."""

    def test_edge_references_nodes(self):
        """Edge correctly references its source and destination nodes."""
        alice = NodeRef(
            id=1,
            labels=frozenset(["Person"]),
            properties={"name": CypherString("Alice")},
        )
        bob = NodeRef(id=2, labels=frozenset(["Person"]), properties={"name": CypherString("Bob")})
        knows = EdgeRef(id=10, type="KNOWS", src=alice, dst=bob, properties={})

        assert knows.src == alice
        assert knows.dst == bob
        assert knows.src.properties["name"].value == "Alice"
        assert knows.dst.properties["name"].value == "Bob"

    def test_nodes_in_dict_as_keys(self):
        """Nodes can be used as dictionary keys."""
        node1 = NodeRef(id=1, labels=frozenset(), properties={})
        node2 = NodeRef(id=2, labels=frozenset(), properties={})
        node_dict = {node1: "first", node2: "second"}
        assert node_dict[node1] == "first"
        assert node_dict[node2] == "second"

    def test_edges_in_dict_as_keys(self):
        """Edges can be used as dictionary keys."""
        src = NodeRef(id=1, labels=frozenset(), properties={})
        dst = NodeRef(id=2, labels=frozenset(), properties={})
        edge1 = EdgeRef(id=10, type="KNOWS", src=src, dst=dst, properties={})
        edge2 = EdgeRef(id=11, type="LIKES", src=src, dst=dst, properties={})
        edge_dict = {edge1: "first", edge2: "second"}
        assert edge_dict[edge1] == "first"
        assert edge_dict[edge2] == "second"
