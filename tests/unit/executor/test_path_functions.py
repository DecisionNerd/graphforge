"""Unit tests for path functions."""

import pytest

from graphforge.executor.evaluator import _evaluate_path_function
from graphforge.types import CypherPath
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import CypherInt, CypherList, CypherNull


class TestPathFunctionLength:
    """Test length() function for paths."""

    def test_length_single_hop(self):
        """Test length() with single-hop path."""
        n1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        n2 = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        e1 = EdgeRef(id=1, type="KNOWS", src=n1, dst=n2, properties={})

        path = CypherPath(nodes=[n1, n2], relationships=[e1])
        result = _evaluate_path_function("LENGTH", [path])

        assert isinstance(result, CypherInt)
        assert result.value == 1

    def test_length_multi_hop(self):
        """Test length() with multi-hop path."""
        n1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        n2 = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        n3 = NodeRef(id=3, labels=frozenset(["Person"]), properties={})
        e1 = EdgeRef(id=1, type="KNOWS", src=n1, dst=n2, properties={})
        e2 = EdgeRef(id=2, type="KNOWS", src=n2, dst=n3, properties={})

        path = CypherPath(nodes=[n1, n2, n3], relationships=[e1, e2])
        result = _evaluate_path_function("LENGTH", [path])

        assert isinstance(result, CypherInt)
        assert result.value == 2

    def test_length_single_node(self):
        """Test length() with single-node path (zero relationships)."""
        n1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})

        path = CypherPath(nodes=[n1], relationships=[])
        result = _evaluate_path_function("LENGTH", [path])

        assert isinstance(result, CypherInt)
        assert result.value == 0

    def test_length_null(self):
        """Test length() with NULL argument."""
        result = _evaluate_path_function("LENGTH", [CypherNull()])
        assert isinstance(result, CypherNull)

    def test_length_wrong_type(self):
        """Test length() with non-path argument."""
        with pytest.raises(TypeError, match="LENGTH expects path argument"):
            _evaluate_path_function("LENGTH", [CypherInt(5)])

    def test_length_wrong_arg_count(self):
        """Test length() with wrong number of arguments."""
        n1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        path = CypherPath(nodes=[n1], relationships=[])

        with pytest.raises(TypeError, match="LENGTH expects 1 argument"):
            _evaluate_path_function("LENGTH", [path, path])


class TestPathFunctionNodes:
    """Test nodes() function for paths."""

    def test_nodes_single_hop(self):
        """Test nodes() with single-hop path."""
        n1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        n2 = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        e1 = EdgeRef(id=1, type="KNOWS", src=n1, dst=n2, properties={})

        path = CypherPath(nodes=[n1, n2], relationships=[e1])
        result = _evaluate_path_function("NODES", [path])

        assert isinstance(result, CypherList)
        assert len(result.value) == 2
        assert result.value[0] is n1
        assert result.value[1] is n2

    def test_nodes_multi_hop(self):
        """Test nodes() with multi-hop path."""
        n1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        n2 = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        n3 = NodeRef(id=3, labels=frozenset(["Person"]), properties={})
        e1 = EdgeRef(id=1, type="KNOWS", src=n1, dst=n2, properties={})
        e2 = EdgeRef(id=2, type="KNOWS", src=n2, dst=n3, properties={})

        path = CypherPath(nodes=[n1, n2, n3], relationships=[e1, e2])
        result = _evaluate_path_function("NODES", [path])

        assert isinstance(result, CypherList)
        assert len(result.value) == 3
        assert result.value[0] is n1
        assert result.value[1] is n2
        assert result.value[2] is n3

    def test_nodes_single_node(self):
        """Test nodes() with single-node path."""
        n1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})

        path = CypherPath(nodes=[n1], relationships=[])
        result = _evaluate_path_function("NODES", [path])

        assert isinstance(result, CypherList)
        assert len(result.value) == 1
        assert result.value[0] is n1

    def test_nodes_null(self):
        """Test nodes() with NULL argument."""
        result = _evaluate_path_function("NODES", [CypherNull()])
        assert isinstance(result, CypherNull)

    def test_nodes_wrong_type(self):
        """Test nodes() with non-path argument."""
        with pytest.raises(TypeError, match="NODES expects path argument"):
            _evaluate_path_function("NODES", [CypherInt(5)])

    def test_nodes_wrong_arg_count(self):
        """Test nodes() with wrong number of arguments."""
        n1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        path = CypherPath(nodes=[n1], relationships=[])

        with pytest.raises(TypeError, match="NODES expects 1 argument"):
            _evaluate_path_function("NODES", [path, path])


class TestPathFunctionRelationships:
    """Test relationships() function for paths."""

    def test_relationships_single_hop(self):
        """Test relationships() with single-hop path."""
        n1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        n2 = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        e1 = EdgeRef(id=1, type="KNOWS", src=n1, dst=n2, properties={})

        path = CypherPath(nodes=[n1, n2], relationships=[e1])
        result = _evaluate_path_function("RELATIONSHIPS", [path])

        assert isinstance(result, CypherList)
        assert len(result.value) == 1
        assert result.value[0] is e1

    def test_relationships_multi_hop(self):
        """Test relationships() with multi-hop path."""
        n1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        n2 = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        n3 = NodeRef(id=3, labels=frozenset(["Person"]), properties={})
        e1 = EdgeRef(id=1, type="KNOWS", src=n1, dst=n2, properties={})
        e2 = EdgeRef(id=2, type="KNOWS", src=n2, dst=n3, properties={})

        path = CypherPath(nodes=[n1, n2, n3], relationships=[e1, e2])
        result = _evaluate_path_function("RELATIONSHIPS", [path])

        assert isinstance(result, CypherList)
        assert len(result.value) == 2
        assert result.value[0] is e1
        assert result.value[1] is e2

    def test_relationships_single_node(self):
        """Test relationships() with single-node path (no relationships)."""
        n1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})

        path = CypherPath(nodes=[n1], relationships=[])
        result = _evaluate_path_function("RELATIONSHIPS", [path])

        assert isinstance(result, CypherList)
        assert len(result.value) == 0

    def test_relationships_null(self):
        """Test relationships() with NULL argument."""
        result = _evaluate_path_function("RELATIONSHIPS", [CypherNull()])
        assert isinstance(result, CypherNull)

    def test_relationships_wrong_type(self):
        """Test relationships() with non-path argument."""
        with pytest.raises(TypeError, match="RELATIONSHIPS expects path argument"):
            _evaluate_path_function("RELATIONSHIPS", [CypherInt(5)])

    def test_relationships_wrong_arg_count(self):
        """Test relationships() with wrong number of arguments."""
        n1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        path = CypherPath(nodes=[n1], relationships=[])

        with pytest.raises(TypeError, match="RELATIONSHIPS expects 1 argument"):
            _evaluate_path_function("RELATIONSHIPS", [path, path])
