"""Unit tests for optimizer instance reuse and update_statistics method."""

import pytest

from graphforge.api import GraphForge
from graphforge.optimizer.optimizer import QueryOptimizer
from graphforge.optimizer.statistics import GraphStatistics


@pytest.mark.unit
class TestUpdateStatistics:
    """Tests for QueryOptimizer.update_statistics() method."""

    def test_update_statistics_sets_statistics(self):
        """update_statistics replaces the internal statistics."""
        optimizer = QueryOptimizer()
        assert optimizer._statistics is None

        stats = GraphStatistics(total_nodes=10, total_edges=5)
        optimizer.update_statistics(stats)
        assert optimizer._statistics is stats
        assert optimizer._statistics.total_nodes == 10
        assert optimizer._statistics.total_edges == 5

    def test_update_statistics_replaces_previous(self):
        """Calling update_statistics again replaces old statistics."""
        stats1 = GraphStatistics(total_nodes=10, total_edges=5)
        stats2 = GraphStatistics(total_nodes=20, total_edges=15)

        optimizer = QueryOptimizer(statistics=stats1)
        assert optimizer._statistics.total_nodes == 10

        optimizer.update_statistics(stats2)
        assert optimizer._statistics is stats2
        assert optimizer._statistics.total_nodes == 20

    def test_update_statistics_with_none(self):
        """update_statistics accepts None to clear statistics."""
        stats = GraphStatistics(total_nodes=10, total_edges=5)
        optimizer = QueryOptimizer(statistics=stats)

        optimizer.update_statistics(None)
        assert optimizer._statistics is None

    def test_update_statistics_preserves_optimizer_settings(self):
        """update_statistics does not alter other optimizer configuration."""
        optimizer = QueryOptimizer(
            enable_filter_pushdown=False,
            enable_join_reorder=False,
            enable_predicate_reorder=False,
            enable_redundant_elimination=False,
            enable_aggregate_pushdown=False,
        )
        stats = GraphStatistics(total_nodes=100, total_edges=50)
        optimizer.update_statistics(stats)

        assert optimizer.enable_filter_pushdown is False
        assert optimizer.enable_join_reorder is False
        assert optimizer.enable_predicate_reorder is False
        assert optimizer.enable_redundant_elimination is False
        assert optimizer.enable_aggregate_pushdown is False
        assert optimizer._statistics.total_nodes == 100


@pytest.mark.unit
class TestOptimizerReuse:
    """Tests that GraphForge reuses the optimizer instance across queries."""

    def test_optimizer_same_instance_across_queries(self):
        """The same optimizer instance is used for multiple queries."""
        gf = GraphForge()
        optimizer_id = id(gf.optimizer)

        gf.execute("CREATE (:Person {name: 'Alice'})")
        assert id(gf.optimizer) == optimizer_id

        gf.execute("MATCH (n) RETURN n")
        assert id(gf.optimizer) == optimizer_id

    def test_optimizer_statistics_updated_on_execute(self):
        """Optimizer statistics are refreshed each query execution."""
        gf = GraphForge()
        assert gf.optimizer._statistics is None

        gf.execute("CREATE (:Person {name: 'Alice'})")
        # After a CREATE, the next query should update statistics
        gf.execute("MATCH (n) RETURN n")
        assert gf.optimizer._statistics is not None
        assert gf.optimizer._statistics.total_nodes >= 1

    def test_optimizer_statistics_reflect_graph_changes(self):
        """Statistics track graph mutations between queries."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("MATCH (n) RETURN n")
        stats_after_one = gf.optimizer._statistics
        node_count_1 = stats_after_one.total_nodes

        gf.execute("CREATE (:Person {name: 'Bob'})")
        gf.execute("MATCH (n) RETURN n")
        stats_after_two = gf.optimizer._statistics
        node_count_2 = stats_after_two.total_nodes

        assert node_count_2 > node_count_1

    def test_optimizer_disabled_no_error(self):
        """Queries work correctly with optimizer disabled."""
        gf = GraphForge(enable_optimizer=False)
        assert gf.optimizer is None

        gf.execute("CREATE (:Person {name: 'Alice'})")
        results = gf.execute("MATCH (n:Person) RETURN n.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_optimizer_reused_for_union_queries(self):
        """Same optimizer instance is reused for UNION queries."""
        gf = GraphForge()
        optimizer_id = id(gf.optimizer)

        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")
        gf.execute(
            "MATCH (n:Person) WHERE n.name = 'Alice' RETURN n.name AS name "
            "UNION "
            "MATCH (n:Person) WHERE n.name = 'Bob' RETURN n.name AS name"
        )
        assert id(gf.optimizer) == optimizer_id
