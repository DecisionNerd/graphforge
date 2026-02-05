"""Unit tests for id() function in evaluator.

Tests the id() function which returns internal IDs for nodes and relationships.
"""

import pytest

from graphforge.ast.expression import FunctionCall, Variable
from graphforge.executor.evaluator import ExecutionContext, evaluate_expression
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import CypherFloat, CypherInt, CypherNull, CypherString

pytestmark = pytest.mark.unit


class TestIdFunction:
    """Tests for id() function."""

    def test_id_of_node(self):
        """Test id() returns node ID."""
        node = NodeRef(id=42, labels=frozenset(["Person"]), properties={})
        ctx = ExecutionContext()
        ctx.bind("n", node)

        func = FunctionCall(name="id", args=[Variable(name="n")])
        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 42

    def test_id_of_relationship(self):
        """Test id() returns relationship ID."""
        node1 = NodeRef(id=1, labels=frozenset(), properties={})
        node2 = NodeRef(id=2, labels=frozenset(), properties={})
        edge = EdgeRef(id=100, type="KNOWS", src=node1, dst=node2, properties={})

        ctx = ExecutionContext()
        ctx.bind("r", edge)

        func = FunctionCall(name="id", args=[Variable(name="r")])
        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 100

    def test_id_with_string_id(self):
        """Test id() converts string IDs to integers."""
        node = NodeRef(id="123", labels=frozenset(), properties={})
        ctx = ExecutionContext()
        ctx.bind("n", node)

        func = FunctionCall(name="id", args=[Variable(name="n")])
        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherInt)
        assert result.value == 123

    def test_id_with_non_numeric_string_id(self):
        """Test id() hashes non-numeric string IDs."""
        node = NodeRef(id="node-abc-123", labels=frozenset(), properties={})
        ctx = ExecutionContext()
        ctx.bind("n", node)

        func = FunctionCall(name="id", args=[Variable(name="n")])
        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherInt)
        # Should be a hash of the string ID
        assert result.value == hash("node-abc-123")

    def test_id_with_null(self):
        """Test id() returns NULL for NULL input."""
        ctx = ExecutionContext()
        ctx.bind("n", CypherNull())

        func = FunctionCall(name="id", args=[Variable(name="n")])
        result = evaluate_expression(func, ctx)

        assert isinstance(result, CypherNull)

    def test_id_wrong_arg_count_no_args(self):
        """Test id() with no arguments raises error."""
        func = FunctionCall(name="id", args=[])
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="ID expects 1 argument, got 0"):
            evaluate_expression(func, ctx)

    def test_id_wrong_arg_count_multiple_args(self):
        """Test id() with multiple arguments raises error."""
        node1 = NodeRef(id=1, labels=frozenset(), properties={})
        node2 = NodeRef(id=2, labels=frozenset(), properties={})

        ctx = ExecutionContext()
        ctx.bind("n1", node1)
        ctx.bind("n2", node2)

        func = FunctionCall(name="id", args=[Variable(name="n1"), Variable(name="n2")])

        with pytest.raises(TypeError, match="ID expects 1 argument, got 2"):
            evaluate_expression(func, ctx)

    def test_id_with_non_graph_element(self):
        """Test id() with non-node/relationship argument raises error."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherString("not a node"))

        func = FunctionCall(name="id", args=[Variable(name="x")])

        with pytest.raises(
            TypeError, match="ID expects node or relationship argument, got CypherString"
        ):
            evaluate_expression(func, ctx)

    def test_id_with_integer(self):
        """Test id() with integer argument raises error."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherInt(42))

        func = FunctionCall(name="id", args=[Variable(name="x")])

        with pytest.raises(
            TypeError, match="ID expects node or relationship argument, got CypherInt"
        ):
            evaluate_expression(func, ctx)

    def test_id_with_float(self):
        """Test id() with float argument raises error."""
        ctx = ExecutionContext()
        ctx.bind("x", CypherFloat(3.14))

        func = FunctionCall(name="id", args=[Variable(name="x")])

        with pytest.raises(
            TypeError, match="ID expects node or relationship argument, got CypherFloat"
        ):
            evaluate_expression(func, ctx)
