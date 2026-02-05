"""Integration tests for SNAP dataset loading and functionality.

These tests verify that SNAP datasets can be:
1. Downloaded from their URLs
2. Parsed by the CSV loader
3. Loaded into GraphForge
4. Queried with Cypher

Note: These tests require network access and may download large files.
Use pytest markers to control which tests run.
"""

from urllib.parse import urlparse

import pytest

from graphforge import GraphForge
from graphforge.datasets import get_dataset_info, list_datasets

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestSNAPDatasetLoading:
    """Integration tests for loading SNAP datasets."""

    @pytest.mark.parametrize(
        "dataset_name",
        [
            # Small datasets for quick testing (< 5 MB)
            "snap-ca-grqc",  # 1 MB, collaboration
            "snap-email-eucore",  # 1 MB, community
            "snap-p2p-gnutella04",  # 1 MB, p2p
            "snap-collegmsg",  # 1 MB, communication
        ],
    )
    def test_load_small_dataset_end_to_end(self, dataset_name):
        """Test loading small datasets end-to-end (download, parse, load, query)."""
        # Get dataset info
        info = get_dataset_info(dataset_name)
        assert info is not None, f"Dataset {dataset_name} not found"

        # Load dataset into GraphForge - uses built-in caching
        gf = GraphForge.from_dataset(dataset_name)

        # Verify graph was loaded
        result = gf.execute("MATCH (n) RETURN count(n) as node_count")
        assert len(result) == 1
        node_count = result[0]["node_count"].value

        # Verify node count is reasonable (within 20% tolerance for format variations)
        expected_nodes = info.nodes
        tolerance = 0.20  # 20% tolerance
        assert node_count > 0, f"No nodes loaded from {dataset_name}"
        assert abs(node_count - expected_nodes) / expected_nodes < tolerance, (
            f"Node count mismatch: got {node_count}, expected ~{expected_nodes} (±{tolerance * 100}%)"
        )

    def test_load_facebook_ego_network_detailed(self):
        """Test Facebook ego network with detailed validation."""
        gf = GraphForge.from_dataset("snap-ego-facebook")

        # Test 1: Verify node count
        result = gf.execute("MATCH (n) RETURN count(n) as count")
        node_count = result[0]["count"].value
        assert node_count > 3500  # Expected ~4039 nodes (allow some variance)

        # Test 2: Verify edge count
        result = gf.execute("MATCH ()-[r]->() RETURN count(r) as count")
        edge_count = result[0]["count"].value
        assert edge_count > 80000  # Expected ~88234 edges (allow some variance)

        # Test 3: Test basic graph queries work
        result = gf.execute(
            """
            MATCH (n)
            RETURN n
            LIMIT 5
        """
        )
        assert len(result) == 5

        # Test 4: Test pattern matching works
        result = gf.execute(
            """
            MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT 10
        """
        )
        assert len(result) == 10
        # Verify we got actual nodes and edges
        assert result[0]["n"] is not None
        assert result[0]["m"] is not None
        assert result[0]["r"] is not None

    def test_load_wikipedia_vote_network(self):
        """Test Wikipedia vote network with query validation."""
        gf = GraphForge.from_dataset("snap-wiki-vote")

        # Verify we can query the graph
        result = gf.execute("MATCH (n) RETURN count(n) as count")
        node_count = result[0]["count"].value
        assert node_count > 6500  # Expected ~7115 nodes (allow variance)

        # Test filtering with LIMIT (id() function not yet supported)
        result = gf.execute(
            """
            MATCH (n)
            RETURN n
            LIMIT 10
        """
        )
        assert len(result) == 10

    def test_load_collaboration_network(self):
        """Test collaboration network (ca-grqc) loading and queries."""
        gf = GraphForge.from_dataset("snap-ca-grqc")

        # Test aggregation queries
        result = gf.execute(
            """
            MATCH (n)-[r]->()
            RETURN count(DISTINCT n) as nodes_with_edges,
                   count(r) as total_edges
        """
        )
        assert result[0]["nodes_with_edges"].value > 0
        assert result[0]["total_edges"].value > 13000  # Expected ~14496 edges

    @pytest.mark.parametrize(
        "category,expected_min_datasets",
        [
            ("social", 23),
            ("communication", 4),
            ("collaboration", 5),
            ("p2p", 9),
            ("web", 4),
        ],
    )
    def test_category_has_loadable_datasets(self, category, expected_min_datasets):
        """Test that each category has datasets that can be listed."""
        datasets = list_datasets(source="snap", category=category)
        assert len(datasets) >= expected_min_datasets

        # Verify all datasets in category have valid URLs
        for dataset in datasets:
            parsed = urlparse(dataset.url)
            assert parsed.scheme == "https"
            assert parsed.hostname == "snap.stanford.edu"
            assert dataset.category == category

    def test_small_dataset_sample_from_each_category(self):
        """Test loading one small dataset from each major category."""
        # Map categories to their smallest datasets for quick testing
        test_datasets = {
            "social": "snap-wiki-vote",  # 2 MB
            "communication": "snap-collegmsg",  # 1 MB
            "collaboration": "snap-ca-grqc",  # 1 MB
            "p2p": "snap-p2p-gnutella08",  # 1 MB
        }

        for category, dataset_name in test_datasets.items():
            # Verify dataset exists and is in correct category
            info = get_dataset_info(dataset_name)
            assert info.category == category

            # Load and verify
            gf = GraphForge.from_dataset(dataset_name)
            result = gf.execute("MATCH (n) RETURN count(n) as count")
            assert result[0]["count"].value > 0, f"Failed to load {dataset_name}"

    def test_url_format_consistency(self):
        """Test that all SNAP dataset URLs are properly formatted."""
        snap_datasets = list_datasets(source="snap")

        for dataset in snap_datasets:
            # All URLs should be from snap.stanford.edu under /data/
            parsed = urlparse(dataset.url)
            assert parsed.scheme == "https"
            assert parsed.hostname == "snap.stanford.edu"
            assert parsed.path.startswith("/data/")

            # URLs should have valid extensions
            valid_extensions = [".txt.gz", ".csv.gz", ".tsv", ".tar.gz", ".zip"]
            assert any(dataset.url.endswith(ext) for ext in valid_extensions), (
                f"Invalid URL extension for {dataset.name}: {dataset.url}"
            )

    @pytest.mark.slow
    def test_load_medium_dataset(self):
        """Test loading a medium-sized dataset (~10-50 MB)."""
        # Test a medium dataset to verify loader handles larger files
        gf = GraphForge.from_dataset("snap-email-enron")

        result = gf.execute("MATCH (n) RETURN count(n) as count")
        node_count = result[0]["count"].value
        assert node_count > 35000  # Expected ~36692 nodes

        # Verify we can run complex queries
        result = gf.execute(
            """
            MATCH (n)-[r]->(m)
            RETURN count(DISTINCT n) as source_nodes,
                   count(DISTINCT m) as target_nodes,
                   count(r) as edges
        """
        )
        assert result[0]["edges"].value > 170000  # Expected ~183831 edges

    def test_csv_loader_handles_different_formats(self):
        """Test that CSV loader handles different SNAP file formats."""
        # Test .txt.gz format (most common)
        gf1 = GraphForge.from_dataset("snap-ego-facebook")
        result1 = gf1.execute("MATCH (n) RETURN count(n) as count")
        assert result1[0]["count"].value > 0

        # Test .csv.gz format (Bitcoin networks)
        gf2 = GraphForge.from_dataset("snap-soc-bitcoin-alpha")
        result2 = gf2.execute("MATCH (n) RETURN count(n) as count")
        assert result2[0]["count"].value > 0


class TestSNAPDatasetMetadataAccuracy:
    """Test that dataset metadata matches actual data."""

    @pytest.mark.parametrize(
        "dataset_name",
        [
            "snap-ego-facebook",
            "snap-ca-grqc",
            "snap-wiki-vote",
        ],
    )
    def test_metadata_node_count_accuracy(self, dataset_name):
        """Test that reported node counts are accurate (within tolerance)."""
        info = get_dataset_info(dataset_name)
        gf = GraphForge.from_dataset(dataset_name)

        result = gf.execute("MATCH (n) RETURN count(n) as count")
        actual_nodes = result[0]["count"].value

        # Allow 20% tolerance for node count variations (format differences)
        tolerance = 0.20
        expected_nodes = info.nodes

        assert abs(actual_nodes - expected_nodes) / expected_nodes < tolerance, (
            f"{dataset_name}: Node count mismatch. Expected ~{expected_nodes}, got {actual_nodes}"
        )

    @pytest.mark.parametrize(
        "dataset_name",
        [
            "snap-ego-facebook",
            "snap-ca-grqc",
        ],
    )
    def test_metadata_edge_count_accuracy(self, dataset_name):
        """Test that reported edge counts are accurate (within tolerance).

        Note: SNAP datasets are undirected but loaded as bidirectional,
        so actual edge count may be 2x the reported count.
        """
        info = get_dataset_info(dataset_name)
        gf = GraphForge.from_dataset(dataset_name)

        result = gf.execute("MATCH ()-[r]->() RETURN count(r) as count")
        actual_edges = result[0]["count"].value

        # SNAP undirected graphs are loaded as bidirectional (each edge becomes 2 directed edges)
        # So actual count can be 1x or 2x the expected count
        expected_edges = info.edges
        expected_bidirectional = expected_edges * 2

        # Check if count matches either unidirectional or bidirectional expectation
        matches_unidirectional = abs(actual_edges - expected_edges) / expected_edges < 0.20
        matches_bidirectional = (
            abs(actual_edges - expected_bidirectional) / expected_bidirectional < 0.20
        )

        assert matches_unidirectional or matches_bidirectional, (
            f"{dataset_name}: Edge count mismatch. "
            f"Expected ~{expected_edges} (undirected) or ~{expected_bidirectional} (bidirectional), "
            f"got {actual_edges}"
        )
