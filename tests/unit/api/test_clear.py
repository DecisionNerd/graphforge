"""Unit tests for GraphForge.clear() method.

Tests that clear() properly resets graph state, ID counters, transaction state,
and custom functions while preserving parser/planner/executor instances.
"""

import pytest

from graphforge import GraphForge
from graphforge.types.values import CypherInt


@pytest.mark.unit
class TestClearBasicBehavior:
    """Test that clear() resets graph data."""

    def test_clear_removes_all_nodes(self):
        """After clear(), the graph should contain no nodes."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")

        gf.clear()

        results = gf.execute("MATCH (n) RETURN count(n) AS c")
        assert results[0]["c"].value == 0

    def test_clear_removes_all_edges(self):
        """After clear(), the graph should contain no edges."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})-[:KNOWS]->(:Person {name: 'Bob'})")

        gf.clear()

        results = gf.execute("MATCH ()-[r]->() RETURN count(r) AS c")
        assert results[0]["c"].value == 0

    def test_clear_allows_new_data(self):
        """After clear(), new nodes and edges can be created."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.clear()
        gf.execute("CREATE (:Animal {name: 'Rex'})")

        results = gf.execute("MATCH (n:Animal) RETURN n.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Rex"

    def test_clear_empty_graph_is_noop(self):
        """Clearing an already empty graph should succeed without error."""
        gf = GraphForge()
        gf.clear()

        results = gf.execute("MATCH (n) RETURN count(n) AS c")
        assert results[0]["c"].value == 0


@pytest.mark.unit
class TestClearIdCounterReset:
    """Test that clear() resets internal ID counters."""

    def test_node_ids_restart_from_one(self):
        """After clear(), node IDs should restart from 1."""
        gf = GraphForge()
        gf.execute("CREATE (:A)")
        gf.execute("CREATE (:B)")
        # At this point _next_node_id should be 3

        gf.clear()

        node = gf.create_node(["C"])
        assert node.id == 1

    def test_edge_ids_restart_from_one(self):
        """After clear(), edge IDs should restart from 1."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(alice, bob, "KNOWS")
        # At this point _next_edge_id should be 2

        gf.clear()

        n1 = gf.create_node(["X"])
        n2 = gf.create_node(["Y"])
        edge = gf.create_relationship(n1, n2, "LINKED")
        assert edge.id == 1


@pytest.mark.unit
class TestClearTransactionState:
    """Test that clear() resets transaction state."""

    def test_clear_resets_active_transaction(self):
        """clear() should reset transaction state even if in a transaction."""
        gf = GraphForge()
        gf.begin()
        gf.execute("CREATE (:Person {name: 'Alice'})")

        gf.clear()

        # Should not be in a transaction anymore
        assert gf._in_transaction is False
        assert gf._transaction_snapshot is None

    def test_can_begin_transaction_after_clear(self):
        """After clear(), a new transaction can be started."""
        gf = GraphForge()
        gf.begin()
        gf.execute("CREATE (:Person)")

        gf.clear()

        # Should be able to begin a fresh transaction
        gf.begin()
        gf.execute("CREATE (:Animal)")
        gf.commit()

        results = gf.execute("MATCH (n) RETURN count(n) AS c")
        assert results[0]["c"].value == 1


@pytest.mark.unit
class TestClearCustomFunctions:
    """Test that clear() resets custom functions."""

    def test_clear_removes_custom_functions(self):
        """Custom functions should be cleared after clear()."""
        gf = GraphForge()
        gf.register_function("MY_FUNC", lambda args, ctx, executor: CypherInt(42))

        gf.clear()

        assert len(gf.executor.custom_functions) == 0


@pytest.mark.unit
class TestClearPreservesInfrastructure:
    """Test that clear() preserves parser/planner/executor instances."""

    def test_parser_preserved(self):
        """Parser instance should be the same after clear()."""
        gf = GraphForge()
        parser_before = gf.parser

        gf.clear()

        assert gf.parser is parser_before

    def test_planner_preserved(self):
        """Planner instance should be the same after clear()."""
        gf = GraphForge()
        planner_before = gf.planner

        gf.clear()

        assert gf.planner is planner_before

    def test_executor_preserved(self):
        """Executor instance should be the same after clear()."""
        gf = GraphForge()
        executor_before = gf.executor

        gf.clear()

        assert gf.executor is executor_before

    def test_optimizer_preserved(self):
        """Optimizer instance should be the same after clear()."""
        gf = GraphForge()
        optimizer_before = gf.optimizer

        gf.clear()

        assert gf.optimizer is optimizer_before

    def test_graph_object_preserved(self):
        """The Graph object itself should be the same after clear()."""
        gf = GraphForge()
        graph_before = gf.graph

        gf.clear()

        assert gf.graph is graph_before


@pytest.mark.unit
class TestClearClosedInstance:
    """Test that clear() raises on closed instances."""

    def test_clear_raises_on_closed_instance(self, tmp_path):
        """clear() should raise RuntimeError if the instance has been closed."""
        db_path = tmp_path / "test.db"
        gf = GraphForge(str(db_path))
        gf.close()

        with pytest.raises(RuntimeError, match="closed"):
            gf.clear()


@pytest.mark.unit
class TestClearIsolation:
    """Test that clear() provides complete isolation between uses."""

    def test_data_from_before_clear_is_gone(self):
        """Data created before clear() should not appear in queries after."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) "
            "CREATE (a)-[:KNOWS]->(b)"
        )

        gf.clear()

        # No nodes
        results = gf.execute("MATCH (n) RETURN n")
        assert len(results) == 0

        # No edges
        results = gf.execute("MATCH ()-[r]->() RETURN r")
        assert len(results) == 0

        # No label index entries
        results = gf.execute("MATCH (p:Person) RETURN p")
        assert len(results) == 0

    def test_multiple_clear_cycles(self):
        """Repeated clear-and-reuse cycles should work correctly."""
        gf = GraphForge()

        for i in range(5):
            gf.execute(f"CREATE (:Item {{idx: {i}}})")
            results = gf.execute("MATCH (n:Item) RETURN count(n) AS c")
            assert results[0]["c"].value == 1
            gf.clear()

        # Final state should be empty
        results = gf.execute("MATCH (n) RETURN count(n) AS c")
        assert results[0]["c"].value == 0

    def test_statistics_reset_after_clear(self):
        """Graph statistics should be reset after clear()."""
        gf = GraphForge()
        gf.execute("CREATE (:Person)-[:KNOWS]->(:Person)")

        stats_before = gf.graph.get_statistics()
        assert stats_before.total_nodes > 0

        gf.clear()

        stats_after = gf.graph.get_statistics()
        assert stats_after.total_nodes == 0
        assert stats_after.total_edges == 0
