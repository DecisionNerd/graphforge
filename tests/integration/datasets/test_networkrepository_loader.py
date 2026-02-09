"""Integration tests for NetworkRepository dataset integration.

Tests end-to-end loading of NetworkRepository datasets, metadata validation,
and querying capabilities.
"""

import pytest

from graphforge.datasets.base import DatasetInfo
from graphforge.datasets.registry import get_dataset_info, list_datasets
from graphforge.datasets.sources.networkrepository import (
    _load_networkrepository_metadata,
    register_networkrepository_datasets,
)


@pytest.mark.integration
class TestNetworkRepositoryMetadata:
    """Tests for NetworkRepository metadata loading and validation."""

    def test_load_metadata_from_json(self):
        """Test that NetworkRepository metadata loads from JSON file."""
        datasets = _load_networkrepository_metadata()

        # Should load all 10 datasets
        assert len(datasets) == 10

        # All should be DatasetInfo instances
        assert all(isinstance(ds, DatasetInfo) for ds in datasets)

        # All should have networkrepository as source
        assert all(ds.source == "networkrepository" for ds in datasets)

        # All should use graphml loader
        assert all(ds.loader_class == "graphml" for ds in datasets)

    def test_metadata_fields_are_valid(self):
        """Test that all metadata fields meet validation requirements."""
        datasets = _load_networkrepository_metadata()

        for ds in datasets:
            # Name should start with netrepo- prefix
            assert ds.name.startswith("netrepo-")

            # URL should point to networkrepository.com
            assert "networkrepository.com" in ds.url

            # Nodes and edges should be positive
            assert ds.nodes > 0
            assert ds.edges > 0

            # Size should be reasonable for small datasets (<1MB mostly)
            assert 0 < ds.size_mb < 10

            # Category should be one of expected types
            assert ds.category in [
                "social",
                "biological",
                "collaboration",
                "infrastructure",
                "communication",
            ]

    def test_specific_datasets_exist(self):
        """Test that key NetworkRepository datasets are present."""
        datasets = _load_networkrepository_metadata()
        dataset_names = {ds.name for ds in datasets}

        # Check for classic network datasets
        expected_datasets = {
            "netrepo-karate",  # Zachary's karate club
            "netrepo-dolphins",  # Dolphin social network
            "netrepo-polbooks",  # Political books
            "netrepo-football",  # College football
            "netrepo-lesmis",  # Les Miserables
            "netrepo-celegans",  # C. elegans neural network
            "netrepo-netscience",  # Collaboration network
            "netrepo-jazz",  # Jazz musicians
            "netrepo-power",  # Power grid
            "netrepo-email-eu",  # Email network
        }

        assert expected_datasets.issubset(dataset_names)

    def test_karate_dataset_metadata(self):
        """Test specific metadata for Zachary's karate club dataset."""
        datasets = _load_networkrepository_metadata()
        karate = next(ds for ds in datasets if ds.name == "netrepo-karate")

        assert karate.description
        assert "karate" in karate.description.lower()
        assert karate.nodes == 34
        assert karate.edges == 78
        assert karate.category == "social"
        assert karate.size_mb < 0.1  # Very small dataset

    def test_celegans_dataset_metadata(self):
        """Test specific metadata for C. elegans neural network dataset."""
        datasets = _load_networkrepository_metadata()
        celegans = next(ds for ds in datasets if ds.name == "netrepo-celegans")

        assert (
            "celegans" in celegans.description.lower() or "elegans" in celegans.description.lower()
        )
        assert celegans.nodes == 297
        assert celegans.edges == 2148
        assert celegans.category == "biological"


@pytest.mark.integration
class TestNetworkRepositoryRegistration:
    """Tests for NetworkRepository dataset registration in global registry."""

    def test_datasets_registered_in_global_registry(self):
        """Test that NetworkRepository datasets are registered globally."""
        # Registration happens automatically on import, but call explicitly to ensure
        register_networkrepository_datasets()

        # List all datasets
        all_datasets = list_datasets()

        # Filter NetworkRepository datasets
        netrepo_datasets = [ds for ds in all_datasets if ds.name.startswith("netrepo-")]

        # Should have 10 NetworkRepository datasets
        assert len(netrepo_datasets) == 10

    def test_get_karate_dataset_info(self):
        """Test retrieving karate dataset info from registry."""
        register_networkrepository_datasets()

        info = get_dataset_info("netrepo-karate")

        assert info is not None
        assert info.name == "netrepo-karate"
        assert info.source == "networkrepository"
        assert info.nodes == 34
        assert info.edges == 78
        assert info.loader_class == "graphml"

    def test_get_dolphins_dataset_info(self):
        """Test retrieving dolphins dataset info from registry."""
        register_networkrepository_datasets()

        info = get_dataset_info("netrepo-dolphins")

        assert info is not None
        assert info.name == "netrepo-dolphins"
        assert info.source == "networkrepository"
        assert info.nodes == 62
        assert info.edges == 159
        assert info.category == "biological"

    def test_filter_datasets_by_source(self):
        """Test filtering datasets by NetworkRepository source."""
        register_networkrepository_datasets()

        all_datasets = list_datasets()
        netrepo_datasets = [ds for ds in all_datasets if ds.name.startswith("netrepo-")]

        # Should have all 10 NetworkRepository datasets
        assert len(netrepo_datasets) == 10

        # Verify they all start with netrepo- prefix
        assert all(ds.name.startswith("netrepo-") for ds in netrepo_datasets)

    def test_no_duplicate_registrations(self):
        """Test that calling register multiple times doesn't create duplicates."""
        # Register twice
        register_networkrepository_datasets()
        register_networkrepository_datasets()

        # Count NetworkRepository datasets
        all_datasets = list_datasets()
        netrepo_datasets = [ds for ds in all_datasets if ds.name.startswith("netrepo-")]

        # Should still have exactly 10 datasets, not 20
        assert len(netrepo_datasets) == 10


@pytest.mark.integration
class TestNetworkRepositoryDatasetCategories:
    """Tests for NetworkRepository dataset categorization."""

    def test_datasets_by_category(self):
        """Test that datasets are properly categorized."""
        datasets = _load_networkrepository_metadata()

        # Group by category
        categories = {}
        for ds in datasets:
            if ds.category not in categories:
                categories[ds.category] = []
            categories[ds.category].append(ds.name)

        # Should have multiple categories
        assert len(categories) >= 4

        # Social category should have multiple datasets
        assert "social" in categories
        assert len(categories["social"]) >= 3

        # Should have biological datasets
        assert "biological" in categories
        assert "netrepo-dolphins" in categories["biological"]
        assert "netrepo-celegans" in categories["biological"]

        # Should have collaboration datasets
        assert "collaboration" in categories
        assert "netrepo-netscience" in categories["collaboration"]
        assert "netrepo-jazz" in categories["collaboration"]

    def test_dataset_size_distribution(self):
        """Test that datasets are appropriately sized for quick loading."""
        datasets = _load_networkrepository_metadata()

        # All datasets should be < 1 MB (small, quick to load)
        small_datasets = [ds for ds in datasets if ds.size_mb < 1.0]
        assert len(small_datasets) >= 8  # Most should be very small

        # No dataset should be > 10 MB
        assert all(ds.size_mb < 10 for ds in datasets)

        # Average size should be small
        avg_size = sum(ds.size_mb for ds in datasets) / len(datasets)
        assert avg_size < 1.0  # Average under 1 MB


@pytest.mark.integration
class TestNetworkRepositoryDatasetLoading:
    """Tests for loading NetworkRepository datasets (unit tests, no actual downloads)."""

    def test_dataset_info_has_correct_loader_class(self):
        """Test that all NetworkRepository datasets use GraphML loader."""
        datasets = _load_networkrepository_metadata()

        # All should use GraphML loader
        assert all(ds.loader_class == "graphml" for ds in datasets)

    def test_urls_are_well_formed(self):
        """Test that all dataset URLs are valid."""
        datasets = _load_networkrepository_metadata()

        for ds in datasets:
            # URLs should be HTTPS
            assert ds.url.startswith("https://")

            # URLs should point to networkrepository.com
            assert "networkrepository.com" in ds.url

            # URLs should have graphml.php endpoint
            assert "graphml.php" in ds.url

    def test_node_edge_ratios_are_reasonable(self):
        """Test that node/edge ratios are reasonable for network datasets."""
        datasets = _load_networkrepository_metadata()

        for ds in datasets:
            # Edge/node ratio should be reasonable (not 0, not millions)
            ratio = ds.edges / ds.nodes if ds.nodes > 0 else 0

            # Most networks have 1-100 edges per node on average
            assert 0.1 < ratio < 100, f"{ds.name} has unusual edge/node ratio: {ratio}"

    def test_labels_and_relationship_types_defined(self):
        """Test that all datasets have labels and relationship types."""
        datasets = _load_networkrepository_metadata()

        for ds in datasets:
            # Should have at least one label
            assert len(ds.labels) >= 1

            # Should have at least one relationship type
            assert len(ds.relationship_types) >= 1

            # For NetworkRepository, most use generic "Node" label
            assert "Node" in ds.labels

            # Most use generic "CONNECTED_TO" relationship
            assert "CONNECTED_TO" in ds.relationship_types
