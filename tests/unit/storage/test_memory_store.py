"""Tests for in-memory graph store.

Tests cover:
- Adding and retrieving nodes
- Adding and retrieving edges
- Adjacency list navigation
- Querying by labels
- Graph statistics
"""

import pytest

from graphforge.storage.memory import Graph
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import CypherInt, CypherString


@pytest.mark.unit
class TestGraphBasics:
    """Basic graph operations."""

    def test_empty_graph(self):
        """Empty graph can be created."""
        graph = Graph()
        assert graph.node_count() == 0
        assert graph.edge_count() == 0

    def test_add_node(self):
        """Node can be added to graph."""
        graph = Graph()
        node = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        graph.add_node(node)
        assert graph.node_count() == 1

    def test_get_node_by_id(self):
        """Node can be retrieved by ID."""
        graph = Graph()
        node = NodeRef(
            id=1,
            labels=frozenset(["Person"]),
            properties={"name": CypherString("Alice")},
        )
        graph.add_node(node)
        retrieved = graph.get_node(1)
        assert retrieved == node
        assert retrieved.properties["name"].value == "Alice"

    def test_get_nonexistent_node(self):
        """Getting nonexistent node returns None."""
        graph = Graph()
        assert graph.get_node(999) is None

    def test_add_multiple_nodes(self):
        """Multiple nodes can be added."""
        graph = Graph()
        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node2 = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        graph.add_node(node1)
        graph.add_node(node2)
        assert graph.node_count() == 2


@pytest.mark.unit
class TestEdgeOperations:
    """Edge operations."""

    def test_add_edge(self):
        """Edge can be added to graph."""
        graph = Graph()
        src = NodeRef(id=1, labels=frozenset(), properties={})
        dst = NodeRef(id=2, labels=frozenset(), properties={})
        edge = EdgeRef(id=10, type="KNOWS", src=src, dst=dst, properties={})

        graph.add_node(src)
        graph.add_node(dst)
        graph.add_edge(edge)

        assert graph.edge_count() == 1

    def test_get_edge_by_id(self):
        """Edge can be retrieved by ID."""
        graph = Graph()
        src = NodeRef(id=1, labels=frozenset(), properties={})
        dst = NodeRef(id=2, labels=frozenset(), properties={})
        edge = EdgeRef(
            id=10,
            type="KNOWS",
            src=src,
            dst=dst,
            properties={"since": CypherInt(2020)},
        )

        graph.add_node(src)
        graph.add_node(dst)
        graph.add_edge(edge)

        retrieved = graph.get_edge(10)
        assert retrieved == edge
        assert retrieved.properties["since"].value == 2020

    def test_get_nonexistent_edge(self):
        """Getting nonexistent edge returns None."""
        graph = Graph()
        assert graph.get_edge(999) is None

    def test_add_edge_requires_nodes(self):
        """Adding edge requires source and destination nodes to exist."""
        graph = Graph()
        src = NodeRef(id=1, labels=frozenset(), properties={})
        dst = NodeRef(id=2, labels=frozenset(), properties={})
        edge = EdgeRef(id=10, type="KNOWS", src=src, dst=dst, properties={})

        with pytest.raises(ValueError, match="Source node.*not found"):
            graph.add_edge(edge)

    def test_replace_edge(self):
        """Replacing edge with same ID updates the edge."""
        graph = Graph()
        alice = NodeRef(id=1, labels=frozenset(), properties={})
        bob = NodeRef(id=2, labels=frozenset(), properties={})
        charlie = NodeRef(id=3, labels=frozenset(), properties={})

        graph.add_node(alice)
        graph.add_node(bob)
        graph.add_node(charlie)

        # Add initial edge
        edge1 = EdgeRef(id=10, type="KNOWS", src=alice, dst=bob, properties={})
        graph.add_edge(edge1)

        # Replace with different edge but same ID
        edge2 = EdgeRef(id=10, type="LIKES", src=alice, dst=charlie, properties={})
        graph.add_edge(edge2)

        # Should have replaced
        assert graph.edge_count() == 1
        retrieved = graph.get_edge(10)
        assert retrieved.type == "LIKES"
        assert retrieved.dst.id == 3

    def test_replace_node(self):
        """Replacing node with same ID updates the node."""
        graph = Graph()
        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        graph.add_node(node1)

        node2 = NodeRef(id=1, labels=frozenset(["Employee"]), properties={})
        graph.add_node(node2)

        # Should have replaced
        assert graph.node_count() == 1
        retrieved = graph.get_node(1)
        assert "Employee" in retrieved.labels
        assert "Person" not in retrieved.labels


@pytest.mark.unit
class TestAdjacencyNavigation:
    """Adjacency list navigation."""

    def test_get_outgoing_edges(self):
        """Get edges going out from a node."""
        graph = Graph()
        alice = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        bob = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        charlie = NodeRef(id=3, labels=frozenset(["Person"]), properties={})

        edge1 = EdgeRef(id=10, type="KNOWS", src=alice, dst=bob, properties={})
        edge2 = EdgeRef(id=11, type="KNOWS", src=alice, dst=charlie, properties={})

        graph.add_node(alice)
        graph.add_node(bob)
        graph.add_node(charlie)
        graph.add_edge(edge1)
        graph.add_edge(edge2)

        outgoing = graph.get_outgoing_edges(1)
        assert len(outgoing) == 2
        assert edge1 in outgoing
        assert edge2 in outgoing

    def test_get_incoming_edges(self):
        """Get edges coming into a node."""
        graph = Graph()
        alice = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        bob = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        charlie = NodeRef(id=3, labels=frozenset(["Person"]), properties={})

        edge1 = EdgeRef(id=10, type="KNOWS", src=alice, dst=bob, properties={})
        edge2 = EdgeRef(id=11, type="KNOWS", src=charlie, dst=bob, properties={})

        graph.add_node(alice)
        graph.add_node(bob)
        graph.add_node(charlie)
        graph.add_edge(edge1)
        graph.add_edge(edge2)

        incoming = graph.get_incoming_edges(2)
        assert len(incoming) == 2
        assert edge1 in incoming
        assert edge2 in incoming

    def test_get_edges_empty(self):
        """Getting edges for node with no edges returns empty list."""
        graph = Graph()
        node = NodeRef(id=1, labels=frozenset(), properties={})
        graph.add_node(node)

        assert graph.get_outgoing_edges(1) == []
        assert graph.get_incoming_edges(1) == []

    def test_self_loop(self):
        """Self-loop edge appears in both incoming and outgoing."""
        graph = Graph()
        node = NodeRef(id=1, labels=frozenset(), properties={})
        edge = EdgeRef(id=10, type="LIKES", src=node, dst=node, properties={})

        graph.add_node(node)
        graph.add_edge(edge)

        assert edge in graph.get_outgoing_edges(1)
        assert edge in graph.get_incoming_edges(1)


@pytest.mark.unit
class TestLabelQueries:
    """Label-based queries."""

    def test_get_nodes_by_label(self):
        """Get all nodes with a specific label."""
        graph = Graph()
        alice = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        bob = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        company = NodeRef(id=3, labels=frozenset(["Company"]), properties={})

        graph.add_node(alice)
        graph.add_node(bob)
        graph.add_node(company)

        persons = graph.get_nodes_by_label("Person")
        assert len(persons) == 2
        assert alice in persons
        assert bob in persons

    def test_get_nodes_by_nonexistent_label(self):
        """Getting nodes by nonexistent label returns empty list."""
        graph = Graph()
        node = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        graph.add_node(node)

        assert graph.get_nodes_by_label("NonExistent") == []

    def test_node_multiple_labels(self):
        """Node with multiple labels appears in queries for each label."""
        graph = Graph()
        node = NodeRef(id=1, labels=frozenset(["Person", "Employee"]), properties={})
        graph.add_node(node)

        assert node in graph.get_nodes_by_label("Person")
        assert node in graph.get_nodes_by_label("Employee")

    def test_get_all_nodes(self):
        """Get all nodes in the graph."""
        graph = Graph()
        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node2 = NodeRef(id=2, labels=frozenset(["Company"]), properties={})
        graph.add_node(node1)
        graph.add_node(node2)

        all_nodes = graph.get_all_nodes()
        assert len(all_nodes) == 2
        assert node1 in all_nodes
        assert node2 in all_nodes


@pytest.mark.unit
class TestEdgeTypeQueries:
    """Edge type queries."""

    def test_get_edges_by_type(self):
        """Get all edges of a specific type."""
        graph = Graph()
        alice = NodeRef(id=1, labels=frozenset(), properties={})
        bob = NodeRef(id=2, labels=frozenset(), properties={})
        charlie = NodeRef(id=3, labels=frozenset(), properties={})

        knows1 = EdgeRef(id=10, type="KNOWS", src=alice, dst=bob, properties={})
        knows2 = EdgeRef(id=11, type="KNOWS", src=bob, dst=charlie, properties={})
        likes = EdgeRef(id=12, type="LIKES", src=alice, dst=charlie, properties={})

        graph.add_node(alice)
        graph.add_node(bob)
        graph.add_node(charlie)
        graph.add_edge(knows1)
        graph.add_edge(knows2)
        graph.add_edge(likes)

        knows_edges = graph.get_edges_by_type("KNOWS")
        assert len(knows_edges) == 2
        assert knows1 in knows_edges
        assert knows2 in knows_edges

    def test_get_all_edges(self):
        """Get all edges in the graph."""
        graph = Graph()
        src = NodeRef(id=1, labels=frozenset(), properties={})
        dst = NodeRef(id=2, labels=frozenset(), properties={})
        edge1 = EdgeRef(id=10, type="KNOWS", src=src, dst=dst, properties={})
        edge2 = EdgeRef(id=11, type="LIKES", src=src, dst=dst, properties={})

        graph.add_node(src)
        graph.add_node(dst)
        graph.add_edge(edge1)
        graph.add_edge(edge2)

        all_edges = graph.get_all_edges()
        assert len(all_edges) == 2
        assert edge1 in all_edges
        assert edge2 in all_edges


@pytest.mark.unit
class TestGraphStatistics:
    """Graph statistics and utility methods."""

    def test_node_count(self):
        """Node count is accurate."""
        graph = Graph()
        assert graph.node_count() == 0

        graph.add_node(NodeRef(id=1, labels=frozenset(), properties={}))
        assert graph.node_count() == 1

        graph.add_node(NodeRef(id=2, labels=frozenset(), properties={}))
        assert graph.node_count() == 2

    def test_edge_count(self):
        """Edge count is accurate."""
        graph = Graph()
        src = NodeRef(id=1, labels=frozenset(), properties={})
        dst = NodeRef(id=2, labels=frozenset(), properties={})

        graph.add_node(src)
        graph.add_node(dst)

        assert graph.edge_count() == 0

        graph.add_edge(EdgeRef(id=10, type="KNOWS", src=src, dst=dst, properties={}))
        assert graph.edge_count() == 1

    def test_has_node(self):
        """Check if node exists in graph."""
        graph = Graph()
        node = NodeRef(id=1, labels=frozenset(), properties={})
        assert not graph.has_node(1)

        graph.add_node(node)
        assert graph.has_node(1)

    def test_has_edge(self):
        """Check if edge exists in graph."""
        graph = Graph()
        src = NodeRef(id=1, labels=frozenset(), properties={})
        dst = NodeRef(id=2, labels=frozenset(), properties={})
        edge = EdgeRef(id=10, type="KNOWS", src=src, dst=dst, properties={})

        graph.add_node(src)
        graph.add_node(dst)

        assert not graph.has_edge(10)

        graph.add_edge(edge)
        assert graph.has_edge(10)


@pytest.mark.unit
class TestComplexGraph:
    """Tests with more complex graph structures."""

    def test_social_network(self):
        """Build and query a small social network."""
        graph = Graph()

        # Create nodes
        alice = NodeRef(
            id=1,
            labels=frozenset(["Person"]),
            properties={"name": CypherString("Alice")},
        )
        bob = NodeRef(id=2, labels=frozenset(["Person"]), properties={"name": CypherString("Bob")})
        charlie = NodeRef(
            id=3,
            labels=frozenset(["Person"]),
            properties={"name": CypherString("Charlie")},
        )

        graph.add_node(alice)
        graph.add_node(bob)
        graph.add_node(charlie)

        # Create edges
        graph.add_edge(EdgeRef(id=10, type="KNOWS", src=alice, dst=bob, properties={}))
        graph.add_edge(EdgeRef(id=11, type="KNOWS", src=alice, dst=charlie, properties={}))
        graph.add_edge(EdgeRef(id=12, type="KNOWS", src=bob, dst=charlie, properties={}))

        # Query
        assert graph.node_count() == 3
        assert graph.edge_count() == 3

        # Alice knows 2 people
        alice_knows = graph.get_outgoing_edges(1)
        assert len(alice_knows) == 2

        # Charlie is known by 2 people
        charlie_known_by = graph.get_incoming_edges(3)
        assert len(charlie_known_by) == 2

        # All are persons
        persons = graph.get_nodes_by_label("Person")
        assert len(persons) == 3
