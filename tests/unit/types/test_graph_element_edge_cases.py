"""Unit tests for NodeRef and EdgeRef edge cases.

Tests for equality, hashing, and repr edge cases.
"""

from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import CypherInt, CypherString


class TestNodeRefEdgeCases:
    """Tests for NodeRef edge cases."""

    def test_node_equality_with_different_type(self):
        """NodeRef equality with non-NodeRef returns NotImplemented."""
        node = NodeRef(id=1, labels=frozenset(["Person"]), properties={})

        # Comparing with non-NodeRef should return False (via NotImplemented)
        assert node != "not a node"
        assert node != 1
        assert node is not None
        assert node != "not a node"

    def test_node_hash_collision_different_labels(self):
        """Nodes with same ID hash the same despite different labels."""
        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node2 = NodeRef(id=1, labels=frozenset(["Employee"]), properties={})

        assert hash(node1) == hash(node2)
        assert node1 == node2  # Equal because same ID

    def test_node_repr_with_labels(self):
        """NodeRef repr includes labels when present."""
        node = NodeRef(
            id=1,
            labels=frozenset(["Person", "Employee"]),
            properties={"name": CypherString("Alice")},
        )

        repr_str = repr(node)
        assert "NodeRef(id=1" in repr_str
        assert "labels=" in repr_str

    def test_node_repr_without_labels(self):
        """NodeRef repr excludes labels when empty."""
        node = NodeRef(id=1, labels=frozenset(), properties={})

        repr_str = repr(node)
        assert repr_str == "NodeRef(id=1)"
        assert "labels=" not in repr_str


class TestEdgeRefEdgeCases:
    """Tests for EdgeRef edge cases."""

    def test_edge_equality_with_different_type(self):
        """EdgeRef equality with non-EdgeRef returns NotImplemented."""
        node1 = NodeRef(id=1, labels=frozenset(), properties={})
        node2 = NodeRef(id=2, labels=frozenset(), properties={})
        edge = EdgeRef(id=10, type="KNOWS", src=node1, dst=node2, properties={})

        # Comparing with non-EdgeRef should return False (via NotImplemented)
        assert edge != "not an edge"
        assert edge != 10
        assert edge is not None
        assert edge != "not an edge"

    def test_edge_hash_collision_different_endpoints(self):
        """Edges with same ID hash the same despite different endpoints."""
        node1 = NodeRef(id=1, labels=frozenset(), properties={})
        node2 = NodeRef(id=2, labels=frozenset(), properties={})
        node3 = NodeRef(id=3, labels=frozenset(), properties={})

        edge1 = EdgeRef(id=10, type="KNOWS", src=node1, dst=node2, properties={})
        edge2 = EdgeRef(id=10, type="LIKES", src=node1, dst=node3, properties={})

        assert hash(edge1) == hash(edge2)
        assert edge1 == edge2  # Equal because same ID

    def test_edge_repr_format(self):
        """EdgeRef repr includes id, type, and node IDs."""
        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node2 = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        edge = EdgeRef(
            id=10,
            type="KNOWS",
            src=node1,
            dst=node2,
            properties={"since": CypherInt(2020)},
        )

        repr_str = repr(edge)
        assert "EdgeRef(id=10" in repr_str
        assert "type='KNOWS'" in repr_str
        assert "src=1" in repr_str
        assert "dst=2" in repr_str
