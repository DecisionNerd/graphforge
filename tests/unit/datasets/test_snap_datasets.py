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
        # Should have 95 SNAP datasets (comprehensive coverage)
        snap_datasets = [d for d in list_datasets() if d.source == "snap"]
        assert len(snap_datasets) == 95

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
            # URLs can end with various extensions: .txt.gz, .csv.gz, .tsv, .tar.gz, .zip
            assert any(
                dataset.url.endswith(ext)
                for ext in [".txt.gz", ".csv.gz", ".tsv", ".tar.gz", ".zip"]
            )

    def test_all_snap_datasets_use_csv_loader(self):
        """Test that all SNAP datasets use CSV loader."""
        snap_datasets = list_datasets(source="snap")

        for dataset in snap_datasets:
            assert dataset.loader_class == "csv"

    def test_filter_by_category_social(self):
        """Test filtering SNAP datasets by social category."""
        social = list_datasets(source="snap", category="social")

        # Should have 23 social datasets in the comprehensive collection
        assert len(social) == 23
        names = {d.name for d in social}
        assert "snap-ego-facebook" in names
        assert "snap-twitter-combined" in names
        assert "snap-soc-epinions1" in names
        assert "snap-musae-github" in names
        assert "snap-musae-twitch" in names

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

    def test_all_dataset_names_unique(self):
        """Test that all SNAP dataset names are unique."""
        snap_datasets = list_datasets(source="snap")
        names = [d.name for d in snap_datasets]

        assert len(names) == len(set(names)), "Duplicate dataset names found"

    def test_all_datasets_have_valid_metadata(self):
        """Test that all SNAP datasets have valid metadata."""
        snap_datasets = list_datasets(source="snap")

        for dataset in snap_datasets:
            # Name checks
            assert dataset.name.startswith("snap-"), f"{dataset.name} doesn't start with 'snap-'"
            assert len(dataset.name) > 5, f"{dataset.name} is too short"

            # Numeric metadata checks
            assert dataset.nodes > 0, f"{dataset.name} has invalid node count: {dataset.nodes}"
            assert dataset.edges > 0, f"{dataset.name} has invalid edge count: {dataset.edges}"
            assert dataset.size_mb > 0, f"{dataset.name} has invalid size: {dataset.size_mb}"

            # String metadata checks
            assert len(dataset.description) > 0, f"{dataset.name} has no description"
            assert dataset.source == "snap", f"{dataset.name} has wrong source"
            assert dataset.license == "Public Domain", f"{dataset.name} has unexpected license"

    def test_all_categories_represented(self):
        """Test that all major categories have datasets."""
        snap_datasets = list_datasets(source="snap")
        categories = {d.category for d in snap_datasets}

        # Expected categories in comprehensive collection
        expected_categories = {
            "social",
            "communication",
            "citation",
            "collaboration",
            "web",
            "product",
            "road",
            "infrastructure",
            "community",
            "p2p",
            "temporal",
            "signed",
            "location",
            "wikipedia",
        }

        assert expected_categories.issubset(categories), (
            f"Missing categories: {expected_categories - categories}"
        )

    def test_large_community_datasets_included(self):
        """Test that large community datasets are included."""
        snap_datasets = list_datasets(source="snap")
        names = {d.name for d in snap_datasets}

        # Check for the large community datasets
        assert "snap-com-livejournal" in names
        assert "snap-com-orkut" in names
        assert "snap-com-friendster" in names

        # Verify Friendster is the largest
        friendster = get_dataset_info("snap-com-friendster")
        assert friendster.nodes > 60_000_000
        assert friendster.size_mb > 20_000

    def test_autonomous_systems_datasets_included(self):
        """Test that autonomous systems datasets are included."""
        snap_datasets = list_datasets(source="snap")
        names = {d.name for d in snap_datasets}

        # Check for AS datasets
        assert "snap-as-skitter" in names
        assert "snap-as-733" in names
        assert "snap-as-caida" in names
        assert "snap-oregon1" in names
        assert "snap-oregon2" in names

    def test_musae_datasets_included(self):
        """Test that MUSAE (Multi-Scale Attributed Node Embedding) datasets are included."""
        snap_datasets = list_datasets(source="snap")
        names = {d.name for d in snap_datasets}

        # Check for MUSAE datasets
        assert "snap-musae-github" in names
        assert "snap-musae-facebook" in names
        assert "snap-musae-twitch" in names
        assert "snap-musae-wiki" in names

    def test_musae_and_social_features_included(self):
        """Test that MUSAE and social feature datasets are included."""
        snap_datasets = list_datasets(source="snap")
        names = {d.name for d in snap_datasets}

        # Check for MUSAE and social network feature datasets
        feature_datasets = [
            "snap-musae-github",
            "snap-musae-facebook",
            "snap-musae-twitch",
            "snap-lastfm-asia",
            "snap-deezer-europe",
        ]

        for dataset in feature_datasets:
            assert dataset in names, f"Missing social feature dataset: {dataset}"

    def test_dataset_size_distribution(self):
        """Test that datasets have reasonable size distribution."""
        snap_datasets = list_datasets(source="snap")

        # Count datasets by size
        small = [d for d in snap_datasets if d.size_mb < 10]
        medium = [d for d in snap_datasets if 10 <= d.size_mb < 100]
        large = [d for d in snap_datasets if 100 <= d.size_mb < 1000]
        very_large = [d for d in snap_datasets if d.size_mb >= 1000]

        # Should have datasets across all size ranges
        assert len(small) > 20, "Not enough small datasets"
        assert len(medium) > 20, "Not enough medium datasets"
        assert len(large) > 5, "Not enough large datasets"
        assert len(very_large) > 2, "Not enough very large datasets"

    def test_edge_density_varies(self):
        """Test that datasets have varying edge densities."""
        snap_datasets = list_datasets(source="snap")

        # Calculate edge densities (edges/nodes ratio)
        densities = [d.edges / d.nodes for d in snap_datasets]

        # Should have both sparse and dense graphs
        min_density = min(densities)
        max_density = max(densities)

        assert min_density < 2, "No sparse graphs found"
        assert max_density > 10, "No dense graphs found"

    def test_temporal_datasets_properly_labeled(self):
        """Test that temporal datasets are properly categorized."""
        temporal = list_datasets(source="snap", category="temporal")

        # Should have at least 10 temporal datasets
        assert len(temporal) >= 10

        # Check for specific temporal datasets
        names = {d.name for d in temporal}
        assert "snap-sx-stackoverflow" in names
        assert "snap-wiki-talk-temporal" in names
        assert "snap-email-eucore-temporal" in names

    def test_signed_networks_properly_labeled(self):
        """Test that signed networks are properly categorized."""
        signed = list_datasets(source="snap", category="signed")

        # Should have at least 8 signed network datasets
        assert len(signed) >= 8

        # Check for specific signed datasets
        names = {d.name for d in signed}
        assert "snap-soc-sign-epinions" in names
        assert "snap-wiki-rfa-signed" in names
