"""Unit tests for Neo4j example dataset registrations."""

from unittest.mock import patch

import pytest

from graphforge.datasets import get_dataset_info, list_datasets
from graphforge.datasets.base import DatasetInfo
from graphforge.datasets.registry import _DATASET_REGISTRY
from graphforge.datasets.sources.neo4j_examples import register_neo4j_datasets


class TestNeo4jDatasetRegistration:
    """Tests for Neo4j dataset registration."""

    def test_neo4j_datasets_registered(self):
        """Test that Neo4j datasets are registered."""
        neo4j_datasets = list_datasets(source="neo4j")

        # Should have at least 12 datasets (from JSON file)
        assert len(neo4j_datasets) >= 12

        # All should be from neo4j source
        assert all(ds.source == "neo4j" for ds in neo4j_datasets)

    def test_neo4j_movie_graph_metadata(self):
        """Test neo4j-movie-graph metadata."""
        info = get_dataset_info("neo4j-movie-graph")

        assert isinstance(info, DatasetInfo)
        assert info.name == "neo4j-movie-graph"
        assert info.source == "neo4j"
        assert info.description == "Movie and actor data with ratings and reviews"
        assert info.nodes == 171
        assert info.edges == 253
        assert "Movie" in info.labels
        assert "Person" in info.labels
        assert "ACTED_IN" in info.relationship_types
        assert "DIRECTED" in info.relationship_types
        assert info.license == "Apache 2.0"
        assert info.category == "entertainment"
        assert info.loader_class == "cypher"
        assert info.url.startswith("https://raw.githubusercontent.com/neo4j-graph-examples")
        assert info.url.endswith("import.cypher")

    def test_neo4j_northwind_metadata(self):
        """Test neo4j-northwind metadata."""
        info = get_dataset_info("neo4j-northwind")

        assert info.name == "neo4j-northwind"
        assert info.source == "neo4j"
        assert "Northwind" in info.description or "products" in info.description
        assert info.nodes == 1044
        assert info.edges == 3146
        assert "Product" in info.labels
        assert "Customer" in info.labels
        assert "Order" in info.labels
        assert info.category == "business"
        assert info.loader_class == "cypher"

    def test_neo4j_recommendations_metadata(self):
        """Test neo4j-recommendations metadata."""
        info = get_dataset_info("neo4j-recommendations")

        assert info.name == "neo4j-recommendations"
        assert info.source == "neo4j"
        assert "recommendation" in info.description.lower() or "user" in info.description.lower()
        assert info.nodes == 400
        assert info.edges == 1200
        assert "User" in info.labels or "Product" in info.labels
        assert info.category == "recommendation"
        assert info.loader_class == "cypher"

    def test_neo4j_network_management_metadata(self):
        """Test neo4j-network-management metadata."""
        info = get_dataset_info("neo4j-network-management")

        assert info.name == "neo4j-network-management"
        assert info.source == "neo4j"
        assert "network" in info.description.lower() or "infrastructure" in info.description.lower()
        assert info.nodes == 250
        assert info.edges == 800
        assert "Device" in info.labels or "Network" in info.labels
        assert info.category == "infrastructure"
        assert info.loader_class == "cypher"

    def test_neo4j_fraud_detection_metadata(self):
        """Test neo4j-fraud-detection metadata."""
        info = get_dataset_info("neo4j-fraud-detection")

        assert info.name == "neo4j-fraud-detection"
        assert info.source == "neo4j"
        assert "fraud" in info.description.lower() or "transaction" in info.description.lower()
        assert info.nodes == 500
        assert info.edges == 1500
        assert "Customer" in info.labels or "Transaction" in info.labels
        assert info.category == "security"
        assert info.loader_class == "cypher"

    def test_neo4j_datasets_use_cypher_loader(self):
        """Test that all Neo4j datasets use the cypher loader."""
        neo4j_datasets = list_datasets(source="neo4j")

        for dataset in neo4j_datasets:
            assert dataset.loader_class == "cypher", (
                f"Dataset {dataset.name} should use cypher loader"
            )

    def test_neo4j_datasets_have_valid_urls(self):
        """Test that all Neo4j datasets have valid GitHub URLs."""
        neo4j_datasets = list_datasets(source="neo4j")

        for dataset in neo4j_datasets:
            assert dataset.url.startswith(
                "https://raw.githubusercontent.com/neo4j-graph-examples/"
            ), f"Dataset {dataset.name} should have a valid GitHub raw URL"
            assert dataset.url.endswith(".cypher"), (
                f"Dataset {dataset.name} should point to a .cypher file"
            )

    def test_neo4j_datasets_have_apache_license(self):
        """Test that all Neo4j datasets have Apache 2.0 license."""
        neo4j_datasets = list_datasets(source="neo4j")

        for dataset in neo4j_datasets:
            assert dataset.license == "Apache 2.0", (
                f"Dataset {dataset.name} should have Apache 2.0 license"
            )

    def test_neo4j_datasets_are_small(self):
        """Test that Neo4j example datasets are reasonably small."""
        neo4j_datasets = list_datasets(source="neo4j")

        for dataset in neo4j_datasets:
            # Neo4j examples should be small (< 1 MB typically)
            assert dataset.size_mb < 1.0, (
                f"Dataset {dataset.name} should be < 1 MB (got {dataset.size_mb} MB)"
            )
            assert dataset.nodes < 10000, (
                f"Dataset {dataset.name} should have < 10K nodes (got {dataset.nodes})"
            )


class TestNeo4jDatasetFiltering:
    """Tests for filtering Neo4j datasets."""

    def test_filter_by_neo4j_source(self):
        """Test filtering datasets by neo4j source."""
        neo4j_datasets = list_datasets(source="neo4j")

        assert len(neo4j_datasets) >= 5
        assert all(ds.source == "neo4j" for ds in neo4j_datasets)

    def test_filter_by_category(self):
        """Test filtering Neo4j datasets by category."""
        business_datasets = list_datasets(source="neo4j", category="business")

        # Should include at least northwind
        assert any(ds.name == "neo4j-northwind" for ds in business_datasets)
        assert all(ds.category == "business" for ds in business_datasets)

    def test_filter_by_max_size(self):
        """Test filtering Neo4j datasets by size."""
        small_datasets = list_datasets(source="neo4j", max_size_mb=0.1)

        # Should have some small datasets
        assert len(small_datasets) >= 2
        assert all(ds.size_mb <= 0.1 for ds in small_datasets)

    def test_filter_combined_criteria(self):
        """Test filtering with multiple criteria."""
        datasets = list_datasets(source="neo4j", category="entertainment", max_size_mb=0.5)

        # Should include movie graph
        movie_datasets = [ds for ds in datasets if "movie" in ds.name.lower()]
        assert len(movie_datasets) >= 1


class TestNeo4jDatasetComparison:
    """Tests comparing Neo4j datasets with other sources."""

    def test_neo4j_vs_snap_datasets(self):
        """Test that Neo4j and SNAP datasets are distinct."""
        neo4j_datasets = {ds.name for ds in list_datasets(source="neo4j")}
        snap_datasets = {ds.name for ds in list_datasets(source="snap")}

        # No overlap in dataset names
        assert neo4j_datasets.isdisjoint(snap_datasets)

    def test_neo4j_datasets_smaller_than_snap(self):
        """Test that Neo4j examples are generally smaller than SNAP datasets."""
        neo4j_datasets = list_datasets(source="neo4j")
        snap_datasets = list_datasets(source="snap")

        neo4j_avg_nodes = sum(ds.nodes for ds in neo4j_datasets) / len(neo4j_datasets)
        snap_avg_nodes = sum(ds.nodes for ds in snap_datasets) / len(snap_datasets)

        # Neo4j examples should be much smaller on average
        assert neo4j_avg_nodes < snap_avg_nodes

    def test_neo4j_datasets_different_categories(self):
        """Test that Neo4j datasets cover different categories than SNAP."""
        neo4j_categories = {ds.category for ds in list_datasets(source="neo4j")}
        snap_categories = {ds.category for ds in list_datasets(source="snap")}

        # Neo4j should have some unique categories
        neo4j_only = neo4j_categories - snap_categories
        assert len(neo4j_only) >= 1  # e.g., "business", "entertainment", "recommendation"


class TestRegistrationFunction:
    """Tests for the register_neo4j_datasets function."""

    def test_register_neo4j_datasets_idempotent(self):
        """Test that calling register_neo4j_datasets multiple times is safe."""
        # Get count before
        before_count = len(list(list_datasets(source="neo4j")))

        # Call registration again
        register_neo4j_datasets()

        # Count should be the same (no duplicates)
        after_count = len(list(list_datasets(source="neo4j")))
        assert after_count == before_count

    def test_register_neo4j_datasets_registers_all(self):
        """Test that register_neo4j_datasets registers all expected datasets."""
        # Ensure registration has been called
        register_neo4j_datasets()

        expected_datasets = {
            "neo4j-movie-graph",
            "neo4j-northwind",
            "neo4j-recommendations",
            "neo4j-network-management",
            "neo4j-fraud-detection",
            "neo4j-game-of-thrones",
            "neo4j-stackoverflow",
            "neo4j-twitter",
            "neo4j-fincen-files",
            "neo4j-pole",
            "neo4j-knowledge-graph",
            "neo4j-football-transfers",
        }

        registered_neo4j = {ds.name for ds in list_datasets(source="neo4j")}

        # All expected datasets should be registered
        assert expected_datasets.issubset(registered_neo4j)

    def test_register_loader_already_exists(self):
        """Test that re-registering the cypher loader is handled gracefully."""
        # This should not raise an exception even if loader already exists
        # The function should catch ValueError with "already registered" and continue
        try:
            register_neo4j_datasets()
        except ValueError as e:
            if "already registered" in str(e):
                pytest.fail("Should not raise ValueError for already registered loader")
            raise

    @patch("graphforge.datasets.sources.neo4j_examples.register_loader")
    def test_register_loader_other_error_propagates(self, mock_register_loader):
        """Test that other ValueError exceptions are propagated."""
        # Clear registry to test fresh registration
        original_registry = _DATASET_REGISTRY.copy()
        _DATASET_REGISTRY.clear()

        try:
            # Mock register_loader to raise a different ValueError
            mock_register_loader.side_effect = ValueError("Some other error")

            # This should raise the ValueError
            with pytest.raises(ValueError, match="Some other error"):
                register_neo4j_datasets()
        finally:
            # Restore registry
            _DATASET_REGISTRY.clear()
            _DATASET_REGISTRY.update(original_registry)

    def test_datasets_not_duplicated_in_registry(self):
        """Test that datasets are only registered once even after multiple calls."""
        # Call multiple times
        register_neo4j_datasets()
        register_neo4j_datasets()
        register_neo4j_datasets()

        # Count occurrences of each dataset
        all_datasets = list_datasets()
        neo4j_names = [ds.name for ds in all_datasets if ds.source == "neo4j"]

        # Each dataset should appear exactly once
        for name in ["neo4j-movie-graph", "neo4j-northwind", "neo4j-recommendations"]:
            count = neo4j_names.count(name)
            assert count == 1, f"Dataset {name} appears {count} times, expected 1"
