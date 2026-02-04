"""Unit tests for SNAP dataset registrations."""

import pytest

from graphforge.datasets import get_dataset_info, list_datasets
from graphforge.datasets.registry import _LOADER_REGISTRY


class TestSNAPDatasetRegistrations:
    """Test that SNAP datasets are registered correctly."""

    @pytest.fixture(autouse=True)
    def _ensure_snap_datasets_registered(self):
        """Ensure SNAP datasets are registered before each test."""
        from graphforge.datasets.sources.snap import register_snap_datasets

        # Re-register SNAP datasets (idempotent - safe to call multiple times)
        register_snap_datasets()

    def test_snap_datasets_registered(self):
        """Test that SNAP datasets are registered on module import."""
        # Should have 5 SNAP datasets
        snap_datasets = [d for d in list_datasets() if d.source == "snap"]
        assert len(snap_datasets) == 5

    def test_csv_loader_registered(self):
        """Test that CSV loader is registered."""
        assert "csv" in _LOADER_REGISTRY

    def test_snap_ego_facebook_metadata(self):
        """Test snap-ego-facebook dataset metadata."""
        info = get_dataset_info("snap-ego-facebook")

        assert info.name == "snap-ego-facebook"
        assert info.source == "snap"
        assert info.category == "social"
        assert info.nodes == 4039
        assert info.edges == 88234
        assert info.loader_class == "csv"
        assert "facebook" in info.description.lower()

    def test_snap_email_enron_metadata(self):
        """Test snap-email-enron dataset metadata."""
        info = get_dataset_info("snap-email-enron")

        assert info.name == "snap-email-enron"
        assert info.source == "snap"
        assert info.category == "communication"
        assert info.nodes == 36692
        assert info.edges == 183831
        assert info.loader_class == "csv"

    def test_snap_ca_astroph_metadata(self):
        """Test snap-ca-astroph dataset metadata."""
        info = get_dataset_info("snap-ca-astroph")

        assert info.name == "snap-ca-astroph"
        assert info.source == "snap"
        assert info.category == "collaboration"
        assert info.nodes == 18772
        assert info.edges == 198110
        assert info.loader_class == "csv"

    def test_snap_web_google_metadata(self):
        """Test snap-web-google dataset metadata."""
        info = get_dataset_info("snap-web-google")

        assert info.name == "snap-web-google"
        assert info.source == "snap"
        assert info.category == "web"
        assert info.nodes == 875713
        assert info.edges == 5105039
        assert info.loader_class == "csv"

    def test_snap_twitter_combined_metadata(self):
        """Test snap-twitter-combined dataset metadata."""
        info = get_dataset_info("snap-twitter-combined")

        assert info.name == "snap-twitter-combined"
        assert info.source == "snap"
        assert info.category == "social"
        assert info.nodes == 81306
        assert info.edges == 1768149
        assert info.loader_class == "csv"

    def test_all_snap_datasets_have_urls(self):
        """Test that all SNAP datasets have download URLs."""
        snap_datasets = list_datasets(source="snap")

        for dataset in snap_datasets:
            assert dataset.url.startswith("https://snap.stanford.edu")
            assert dataset.url.endswith(".txt.gz")

    def test_all_snap_datasets_use_csv_loader(self):
        """Test that all SNAP datasets use CSV loader."""
        snap_datasets = list_datasets(source="snap")

        for dataset in snap_datasets:
            assert dataset.loader_class == "csv"

    def test_filter_by_category_social(self):
        """Test filtering SNAP datasets by social category."""
        social = list_datasets(source="snap", category="social")

        assert len(social) == 2  # ego-facebook and twitter-combined
        names = {d.name for d in social}
        assert "snap-ego-facebook" in names
        assert "snap-twitter-combined" in names

    def test_filter_by_size(self):
        """Test filtering SNAP datasets by size."""
        small = list_datasets(source="snap", max_size_mb=10.0)

        # Should include: ego-facebook (0.5MB), email-enron (2.5MB), ca-astroph (1.8MB)
        assert len(small) >= 3
        assert all(d.size_mb <= 10.0 for d in small)

    def test_snap_datasets_have_correct_labels(self):
        """Test that SNAP datasets have Node label."""
        snap_datasets = list_datasets(source="snap")

        for dataset in snap_datasets:
            assert "Node" in dataset.labels

    def test_snap_datasets_have_correct_relationship_types(self):
        """Test that SNAP datasets have CONNECTED_TO relationship."""
        snap_datasets = list_datasets(source="snap")

        for dataset in snap_datasets:
            assert "CONNECTED_TO" in dataset.relationship_types
