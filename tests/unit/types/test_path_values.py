"""Unit tests for CypherPath value type."""

import pytest

from graphforge.types import CypherPath, CypherBool, CypherInt, CypherNull, CypherString
from graphforge.types.graph import NodeRef, EdgeRef


class TestCypherPathConstruction:
    """Test CypherPath construction and validation."""

    def test_single_node_path(self):
        """Test path with single node (no relationships)."""
        node = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        path = CypherPath(nodes=[node], relationships=[])

        assert len(path.nodes) == 1
        assert len(path.relationships) == 0
        assert path.length() == 0
        assert path.nodes[0] == node

    def test_two_node_path(self):
        """Test path with two nodes and one relationship."""
        node_a = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node_b = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        edge = EdgeRef(id=10, type="KNOWS", src=node_a, dst=node_b, properties={})

        path = CypherPath(nodes=[node_a, node_b], relationships=[edge])

        assert len(path.nodes) == 2
        assert len(path.relationships) == 1
        assert path.length() == 1
        assert path.nodes[0] == node_a
        assert path.nodes[1] == node_b
        assert path.relationships[0] == edge

    def test_three_node_path(self):
        """Test path with three nodes and two relationships."""
        node_a = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node_b = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        node_c = NodeRef(id=3, labels=frozenset(["Person"]), properties={})

        edge_ab = EdgeRef(id=10, type="KNOWS", src=node_a, dst=node_b, properties={})
        edge_bc = EdgeRef(id=11, type="KNOWS", src=node_b, dst=node_c, properties={})

        path = CypherPath(nodes=[node_a, node_b, node_c], relationships=[edge_ab, edge_bc])

        assert len(path.nodes) == 3
        assert len(path.relationships) == 2
        assert path.length() == 2

    def test_empty_nodes_raises_error(self):
        """Test that empty node list raises ValueError."""
        with pytest.raises(ValueError, match="Path must contain at least one node"):
            CypherPath(nodes=[], relationships=[])

    def test_wrong_relationship_count_raises_error(self):
        """Test that wrong number of relationships raises ValueError."""
        node_a = NodeRef(id=1, labels=frozenset(), properties={})
        node_b = NodeRef(id=2, labels=frozenset(), properties={})
        edge = EdgeRef(id=10, type="KNOWS", src=node_a, dst=node_b, properties={})

        # Too many relationships
        with pytest.raises(ValueError, match="must have exactly len\\(nodes\\)-1 relationships"):
            CypherPath(nodes=[node_a], relationships=[edge])

        # Too few relationships
        with pytest.raises(ValueError, match="must have exactly len\\(nodes\\)-1 relationships"):
            CypherPath(nodes=[node_a, node_b], relationships=[])

    def test_disconnected_path_raises_error(self):
        """Test that disconnected nodes/edges raise ValueError."""
        node_a = NodeRef(id=1, labels=frozenset(), properties={})
        node_b = NodeRef(id=2, labels=frozenset(), properties={})
        node_c = NodeRef(id=3, labels=frozenset(), properties={})

        # Edge connects wrong nodes
        edge_ac = EdgeRef(id=10, type="KNOWS", src=node_a, dst=node_c, properties={})

        with pytest.raises(ValueError, match="does not connect nodes"):
            CypherPath(nodes=[node_a, node_b], relationships=[edge_ac])

    def test_invalid_node_type_raises_error(self):
        """Test that non-NodeRef in nodes raises TypeError."""
        with pytest.raises(TypeError, match="All nodes must be NodeRef instances"):
            CypherPath(nodes=["not a node"], relationships=[])

    def test_invalid_relationship_type_raises_error(self):
        """Test that non-EdgeRef in relationships raises TypeError."""
        node_a = NodeRef(id=1, labels=frozenset(), properties={})
        node_b = NodeRef(id=2, labels=frozenset(), properties={})

        with pytest.raises(TypeError, match="All relationships must be EdgeRef instances"):
            CypherPath(nodes=[node_a, node_b], relationships=["not an edge"])


class TestCypherPathEquality:
    """Test CypherPath equality semantics."""

    def test_identical_paths_equal(self):
        """Test that identical paths are equal."""
        node_a = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node_b = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        edge = EdgeRef(id=10, type="KNOWS", src=node_a, dst=node_b, properties={})

        path1 = CypherPath(nodes=[node_a, node_b], relationships=[edge])
        path2 = CypherPath(nodes=[node_a, node_b], relationships=[edge])

        result = path1.equals(path2)
        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_different_nodes_not_equal(self):
        """Test that paths with different nodes are not equal."""
        node_a = NodeRef(id=1, labels=frozenset(), properties={})
        node_b = NodeRef(id=2, labels=frozenset(), properties={})
        node_c = NodeRef(id=3, labels=frozenset(), properties={})

        edge_ab = EdgeRef(id=10, type="KNOWS", src=node_a, dst=node_b, properties={})
        edge_ac = EdgeRef(id=11, type="KNOWS", src=node_a, dst=node_c, properties={})

        path1 = CypherPath(nodes=[node_a, node_b], relationships=[edge_ab])
        path2 = CypherPath(nodes=[node_a, node_c], relationships=[edge_ac])

        result = path1.equals(path2)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_different_relationships_not_equal(self):
        """Test that paths with different relationships are not equal."""
        node_a = NodeRef(id=1, labels=frozenset(), properties={})
        node_b = NodeRef(id=2, labels=frozenset(), properties={})

        edge1 = EdgeRef(id=10, type="KNOWS", src=node_a, dst=node_b, properties={})
        edge2 = EdgeRef(id=11, type="LIKES", src=node_a, dst=node_b, properties={})

        path1 = CypherPath(nodes=[node_a, node_b], relationships=[edge1])
        path2 = CypherPath(nodes=[node_a, node_b], relationships=[edge2])

        result = path1.equals(path2)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_different_lengths_not_equal(self):
        """Test that paths with different lengths are not equal."""
        node_a = NodeRef(id=1, labels=frozenset(), properties={})
        node_b = NodeRef(id=2, labels=frozenset(), properties={})
        node_c = NodeRef(id=3, labels=frozenset(), properties={})

        edge_ab = EdgeRef(id=10, type="KNOWS", src=node_a, dst=node_b, properties={})
        edge_bc = EdgeRef(id=11, type="KNOWS", src=node_b, dst=node_c, properties={})

        path1 = CypherPath(nodes=[node_a, node_b], relationships=[edge_ab])
        path2 = CypherPath(nodes=[node_a, node_b, node_c], relationships=[edge_ab, edge_bc])

        result = path1.equals(path2)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_path_equals_null_returns_null(self):
        """Test that path.equals(NULL) returns NULL."""
        node = NodeRef(id=1, labels=frozenset(), properties={})
        path = CypherPath(nodes=[node], relationships=[])

        result = path.equals(CypherNull())
        assert isinstance(result, CypherNull)

    def test_path_not_equal_to_other_types(self):
        """Test that path is not equal to non-path values."""
        node = NodeRef(id=1, labels=frozenset(), properties={})
        path = CypherPath(nodes=[node], relationships=[])

        # Not equal to int
        result = path.equals(CypherInt(1))
        assert isinstance(result, CypherBool)
        assert result.value is False

        # Not equal to string
        result = path.equals(CypherString("path"))
        assert isinstance(result, CypherBool)
        assert result.value is False


class TestCypherPathLength:
    """Test CypherPath.length() method."""

    def test_single_node_length_zero(self):
        """Test that single node path has length 0."""
        node = NodeRef(id=1, labels=frozenset(), properties={})
        path = CypherPath(nodes=[node], relationships=[])

        assert path.length() == 0

    def test_two_node_length_one(self):
        """Test that two node path has length 1."""
        node_a = NodeRef(id=1, labels=frozenset(), properties={})
        node_b = NodeRef(id=2, labels=frozenset(), properties={})
        edge = EdgeRef(id=10, type="KNOWS", src=node_a, dst=node_b, properties={})

        path = CypherPath(nodes=[node_a, node_b], relationships=[edge])

        assert path.length() == 1

    def test_long_path_length(self):
        """Test length of longer path."""
        nodes = [NodeRef(id=i, labels=frozenset(), properties={}) for i in range(10)]
        edges = [
            EdgeRef(id=i + 100, type="KNOWS", src=nodes[i], dst=nodes[i + 1], properties={})
            for i in range(9)
        ]

        path = CypherPath(nodes=nodes, relationships=edges)

        assert path.length() == 9


class TestCypherPathRepr:
    """Test CypherPath string representation."""

    def test_repr_shows_node_ids_and_length(self):
        """Test that repr shows node IDs and path length."""
        node_a = NodeRef(id=1, labels=frozenset(), properties={})
        node_b = NodeRef(id=2, labels=frozenset(), properties={})
        node_c = NodeRef(id=3, labels=frozenset(), properties={})

        edge_ab = EdgeRef(id=10, type="KNOWS", src=node_a, dst=node_b, properties={})
        edge_bc = EdgeRef(id=11, type="KNOWS", src=node_b, dst=node_c, properties={})

        path = CypherPath(nodes=[node_a, node_b, node_c], relationships=[edge_ab, edge_bc])

        repr_str = repr(path)
        assert "1 -> 2 -> 3" in repr_str
        assert "length=2" in repr_str


class TestCypherPathToPython:
    """Test CypherPath.to_python() conversion."""

    def test_to_python_returns_dict(self):
        """Test that to_python returns dict with nodes and relationships."""
        node_a = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node_b = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        edge = EdgeRef(id=10, type="KNOWS", src=node_a, dst=node_b, properties={})

        path = CypherPath(nodes=[node_a, node_b], relationships=[edge])

        result = path.to_python()

        assert isinstance(result, dict)
        assert "nodes" in result
        assert "relationships" in result
        assert result["nodes"] == [node_a, node_b]
        assert result["relationships"] == [edge]
