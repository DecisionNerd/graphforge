"""Unit tests for executor error paths and edge cases to improve coverage.

These tests target error handling and edge cases in the executor that are
often missed by integration tests.
"""

import pytest

from graphforge import GraphForge
from graphforge.executor.evaluator import ExecutionContext
from graphforge.executor.executor import QueryExecutor
from graphforge.planner.operators import Create, Delete, Merge, Set


@pytest.mark.unit
class TestExecutorErrorPaths:
    """Test error paths in executor operations."""

    @pytest.mark.parametrize(
        "op_type,error_match",
        [
            ("CREATE", "CREATE requires GraphForge instance"),
            ("MERGE", "MERGE requires GraphForge instance"),
        ],
        ids=["create", "merge"],
    )
    def test_operation_without_graphforge_instance(self, op_type, error_match):
        """Test operations raise error when GraphForge instance not provided."""
        from graphforge.ast.pattern import NodePattern

        gf = GraphForge()

        # Create executor WITHOUT graphforge reference
        executor = QueryExecutor(gf.graph, graphforge=None)

        pattern = [NodePattern(variable="n", labels=["Person"], properties={})]

        if op_type == "CREATE":
            op = Create(patterns=[pattern])
            execute_fn = executor._execute_create
        else:  # MERGE
            op = Merge(patterns=[pattern], on_create=None, on_match=None)
            execute_fn = executor._execute_merge

        ctx = ExecutionContext()

        with pytest.raises(RuntimeError, match=error_match):
            execute_fn(op, [ctx])

    def test_delete_node_with_relationships_no_detach(self):
        """Test DELETE raises error when deleting node with relationships without DETACH."""
        gf = GraphForge()

        # Create nodes with relationship
        alice = gf.execute("CREATE (a:Person {name: 'Alice'}) RETURN a")[0]["a"]
        _bob = gf.execute("CREATE (b:Person {name: 'Bob'}) RETURN b")[0]["b"]
        gf.execute(
            """
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            CREATE (a)-[:KNOWS]->(b)
        """
        )

        executor = QueryExecutor(gf.graph, gf)

        # Try to DELETE node without DETACH
        ctx = ExecutionContext()
        ctx.bind("a", alice)

        op = Delete(variables=["a"], detach=False)

        with pytest.raises(
            ValueError,
            match="Cannot delete node with relationships. Use DETACH DELETE",
        ):
            executor._execute_delete(op, [ctx])

    def test_delete_node_with_detach(self):
        """Test DETACH DELETE successfully removes node and relationships."""
        gf = GraphForge()

        # Create nodes with relationship
        gf.execute("CREATE (a:Person {name: 'Alice'})")
        gf.execute("CREATE (b:Person {name: 'Bob'})")
        gf.execute(
            """
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            CREATE (a)-[:KNOWS]->(b)
        """
        )

        # Get Alice node
        alice = gf.execute("MATCH (a:Person {name: 'Alice'}) RETURN a")[0]["a"]

        executor = QueryExecutor(gf.graph, gf)

        # DETACH DELETE
        ctx = ExecutionContext()
        ctx.bind("a", alice)

        op = Delete(variables=["a"], detach=True)
        result = executor._execute_delete(op, [ctx])

        # Should return empty list (DELETE produces no output)
        assert result == []

        # Verify node and relationship removed
        remaining = gf.execute("MATCH (n) RETURN n")
        assert len(remaining) == 1  # Only Bob remains
        assert remaining[0]["n"].properties["name"].value == "Bob"

        # Verify relationship removed
        rels = gf.execute("MATCH ()-[r]->() RETURN r")
        assert len(rels) == 0

    def test_delete_relationship(self):
        """Test DELETE removes relationship."""
        gf = GraphForge()

        # Create relationship
        gf.execute("CREATE (a:Person {name: 'Alice'})")
        gf.execute("CREATE (b:Person {name: 'Bob'})")
        gf.execute(
            """
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            CREATE (a)-[:KNOWS]->(b)
        """
        )

        # Get relationship
        rel = gf.execute("MATCH ()-[r:KNOWS]->() RETURN r")[0]["r"]

        executor = QueryExecutor(gf.graph, gf)

        # DELETE relationship
        ctx = ExecutionContext()
        ctx.bind("r", rel)

        op = Delete(variables=["r"], detach=False)
        result = executor._execute_delete(op, [ctx])

        # Should return empty list
        assert result == []

        # Verify relationship removed but nodes remain
        nodes = gf.execute("MATCH (n) RETURN n")
        assert len(nodes) == 2  # Both nodes still exist

        rels = gf.execute("MATCH ()-[r]->() RETURN r")
        assert len(rels) == 0  # Relationship removed


@pytest.mark.unit
class TestExecutorEdgeCases:
    """Test edge cases in executor operations."""

    def test_unknown_operator_type(self):
        """Test _execute_operator raises TypeError for unknown operator."""
        gf = GraphForge()

        executor = QueryExecutor(gf.graph, gf)

        # Create a fake operator class
        class UnknownOperator:
            pass

        unknown_op = UnknownOperator()
        ctx = ExecutionContext()

        with pytest.raises(TypeError, match="Unknown operator type"):
            executor._execute_operator(unknown_op, [ctx], 0, 1)

    @pytest.mark.parametrize(
        "op_type,expected_result",
        [
            ("SET", "non_empty"),  # Returns input rows
            ("REMOVE", "non_empty"),  # Returns input rows
            ("DELETE", "empty"),  # Returns empty list
        ],
        ids=["set", "remove", "delete"],
    )
    def test_operation_on_unbound_variable(self, op_type, expected_result):
        """Test operations handle unbound variables gracefully."""
        gf = GraphForge()
        executor = QueryExecutor(gf.graph, gf)
        ctx = ExecutionContext()
        # Variable is not bound in context

        if op_type == "SET":
            from graphforge.ast.expression import Literal, PropertyAccess

            prop_access = PropertyAccess(variable="n", property="name")
            op = Set(items=[(prop_access, Literal(value="Alice"))])
            result = executor._execute_set(op, [ctx])
        elif op_type == "REMOVE":
            from graphforge.planner.operators import Remove

            class RemoveItemStruct:
                def __init__(self, variable, name, item_type):
                    self.variable = variable
                    self.name = name
                    self.item_type = item_type

            remove_item = RemoveItemStruct(variable="n", name="age", item_type="property")
            op = Remove(items=[remove_item])
            result = executor._execute_remove(op, [ctx])
        else:  # DELETE
            op = Delete(variables=["nonexistent"], detach=False)
            result = executor._execute_delete(op, [ctx])

        # Should not crash, operations handle unbound variables gracefully
        if expected_result == "non_empty":
            assert len(result) == 1
        else:  # empty
            assert result == []
