"""Unit tests for graph statistics collection."""

from pathlib import Path
import tempfile

import pytest

from graphforge.optimizer.statistics import GraphStatistics
from graphforge.storage.memory import Graph
from graphforge.storage.sqlite_backend import SQLiteBackend
from graphforge.types.graph import EdgeRef, NodeRef


class TestGraphStatisticsModel:
    """Test the GraphStatistics Pydantic model."""

    def test_empty_statistics(self):
        """Empty statistics should have zero counts."""
        stats = GraphStatistics.empty()

        assert stats.total_nodes == 0
        assert stats.total_edges == 0
        assert stats.node_counts_by_label == {}
        assert stats.edge_counts_by_type == {}
        assert stats.avg_degree_by_type == {}
        assert stats.last_updated > 0

    def test_statistics_immutable(self):
        """GraphStatistics should be immutable."""
        from pydantic import ValidationError

        stats = GraphStatistics.empty()

        with pytest.raises(ValidationError):  # Pydantic raises ValidationError for frozen models
            stats.total_nodes = 10  # type: ignore

    def test_model_copy_creates_new_instance(self):
        """model_copy should create a new instance with updated fields."""
        stats = GraphStatistics.empty()
        new_stats = stats.model_copy(update={"total_nodes": 5, "total_edges": 10})

        assert stats.total_nodes == 0
        assert new_stats.total_nodes == 5
        assert new_stats.total_edges == 10


class TestGraphStatisticsTracking:
    """Test statistics tracking in Graph class."""

    def test_new_graph_has_empty_statistics(self):
        """A new graph should have empty statistics."""
        graph = Graph()
        stats = graph.get_statistics()

        assert stats.total_nodes == 0
        assert stats.total_edges == 0
        assert stats.node_counts_by_label == {}
        assert stats.edge_counts_by_type == {}

    def test_add_node_updates_statistics(self):
        """Adding a node should update total_nodes and node_counts_by_label."""
        graph = Graph()

        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        graph.add_node(node1)

        stats = graph.get_statistics()
        assert stats.total_nodes == 1
        assert stats.node_counts_by_label == {"Person": 1}

    def test_add_multiple_nodes_updates_counts(self):
        """Adding multiple nodes should accumulate counts."""
        graph = Graph()

        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node2 = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        node3 = NodeRef(id=3, labels=frozenset(["Company"]), properties={})

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        stats = graph.get_statistics()
        assert stats.total_nodes == 3
        assert stats.node_counts_by_label == {"Person": 2, "Company": 1}

    def test_add_node_with_multiple_labels(self):
        """A node with multiple labels should update all label counts."""
        graph = Graph()

        node = NodeRef(id=1, labels=frozenset(["Person", "Employee"]), properties={})
        graph.add_node(node)

        stats = graph.get_statistics()
        assert stats.total_nodes == 1
        assert stats.node_counts_by_label == {"Person": 1, "Employee": 1}

    def test_replace_node_updates_statistics(self):
        """Replacing a node should update statistics correctly."""
        graph = Graph()

        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        graph.add_node(node1)

        # Replace with different labels
        node2 = NodeRef(id=1, labels=frozenset(["Company"]), properties={})
        graph.add_node(node2)

        stats = graph.get_statistics()
        assert stats.total_nodes == 1
        assert stats.node_counts_by_label == {"Company": 1}
        assert "Person" not in stats.node_counts_by_label

    def test_add_edge_updates_statistics(self):
        """Adding an edge should update total_edges and edge_counts_by_type."""
        graph = Graph()

        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node2 = NodeRef(id=2, labels=frozenset(["Company"]), properties={})
        graph.add_node(node1)
        graph.add_node(node2)

        edge = EdgeRef(id=1, type="WORKS_FOR", src=node1, dst=node2, properties={})
        graph.add_edge(edge)

        stats = graph.get_statistics()
        assert stats.total_edges == 1
        assert stats.edge_counts_by_type == {"WORKS_FOR": 1}
        assert stats.avg_degree_by_type == {"WORKS_FOR": 1.0}

    def test_add_multiple_edges_updates_avg_degree(self):
        """Adding multiple edges should update average degree."""
        graph = Graph()

        # Create nodes
        person1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        person2 = NodeRef(id=2, labels=frozenset(["Person"]), properties={})
        company = NodeRef(id=3, labels=frozenset(["Company"]), properties={})

        graph.add_node(person1)
        graph.add_node(person2)
        graph.add_node(company)

        # Two edges from same source (person1) -> avg degree = 2
        edge1 = EdgeRef(id=1, type="WORKS_FOR", src=person1, dst=company, properties={})
        edge2 = EdgeRef(id=2, type="WORKS_FOR", src=person1, dst=company, properties={})
        graph.add_edge(edge1)
        graph.add_edge(edge2)

        stats = graph.get_statistics()
        assert stats.total_edges == 2
        assert stats.edge_counts_by_type == {"WORKS_FOR": 2}
        assert stats.avg_degree_by_type["WORKS_FOR"] == 2.0

        # Add edge from different source (person2) -> avg degree = 3/2 = 1.5
        edge3 = EdgeRef(id=3, type="WORKS_FOR", src=person2, dst=company, properties={})
        graph.add_edge(edge3)

        stats = graph.get_statistics()
        assert stats.total_edges == 3
        assert stats.edge_counts_by_type == {"WORKS_FOR": 3}
        assert stats.avg_degree_by_type["WORKS_FOR"] == 1.5

    def test_replace_edge_updates_statistics(self):
        """Replacing an edge should update statistics correctly."""
        graph = Graph()

        node1 = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        node2 = NodeRef(id=2, labels=frozenset(["Company"]), properties={})
        graph.add_node(node1)
        graph.add_node(node2)

        edge1 = EdgeRef(id=1, type="WORKS_FOR", src=node1, dst=node2, properties={})
        graph.add_edge(edge1)

        # Replace with different type
        edge2 = EdgeRef(id=1, type="EMPLOYED_BY", src=node1, dst=node2, properties={})
        graph.add_edge(edge2)

        stats = graph.get_statistics()
        assert stats.total_edges == 1
        assert stats.edge_counts_by_type == {"EMPLOYED_BY": 1}
        assert "WORKS_FOR" not in stats.edge_counts_by_type

    def test_snapshot_includes_statistics(self):
        """Graph snapshot should include statistics."""
        graph = Graph()

        node = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        graph.add_node(node)

        snapshot = graph.snapshot()
        assert "statistics" in snapshot
        assert snapshot["statistics"].total_nodes == 1

    def test_restore_restores_statistics(self):
        """Graph restore should restore statistics."""
        graph = Graph()

        node = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        graph.add_node(node)

        snapshot = graph.snapshot()

        # Create new graph and restore
        graph2 = Graph()
        graph2.restore(snapshot)

        stats = graph2.get_statistics()
        assert stats.total_nodes == 1
        assert stats.node_counts_by_label == {"Person": 1}


class TestSQLiteStatisticsPersistence:
    """Test statistics persistence in SQLite backend."""

    def test_save_and_load_statistics(self):
        """Statistics should persist across sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create backend and save statistics
            backend = SQLiteBackend(db_path)
            stats = GraphStatistics(
                total_nodes=100,
                total_edges=200,
                node_counts_by_label={"Person": 50, "Company": 50},
                edge_counts_by_type={"WORKS_FOR": 200},
                avg_degree_by_type={"WORKS_FOR": 2.0},
            )
            backend.save_statistics(stats)
            backend.commit()
            backend.close()

            # Load in new session
            backend2 = SQLiteBackend(db_path)
            loaded_stats = backend2.load_statistics()
            backend2.close()

            assert loaded_stats is not None
            assert loaded_stats.total_nodes == 100
            assert loaded_stats.total_edges == 200
            assert loaded_stats.node_counts_by_label == {"Person": 50, "Company": 50}
            assert loaded_stats.edge_counts_by_type == {"WORKS_FOR": 200}
            assert loaded_stats.avg_degree_by_type == {"WORKS_FOR": 2.0}

    def test_load_statistics_returns_none_when_empty(self):
        """Loading statistics from empty database should return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            backend = SQLiteBackend(db_path)

            loaded_stats = backend.load_statistics()

            assert loaded_stats is None
            backend.close()

    def test_save_statistics_overwrites_previous(self):
        """Saving statistics should overwrite previous values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            backend = SQLiteBackend(db_path)

            # Save first version
            stats1 = GraphStatistics(total_nodes=50, total_edges=100)
            backend.save_statistics(stats1)
            backend.commit()

            # Save second version
            stats2 = GraphStatistics(total_nodes=75, total_edges=150)
            backend.save_statistics(stats2)
            backend.commit()

            # Load should return latest
            loaded_stats = backend.load_statistics()
            assert loaded_stats is not None
            assert loaded_stats.total_nodes == 75
            assert loaded_stats.total_edges == 150

            backend.close()
