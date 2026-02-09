"""Validation tests for NetworkRepository datasets with actual downloads.

These tests download actual datasets from NetworkRepository to verify:
- URLs are correct and accessible
- Node/edge counts match metadata
- Datasets load successfully
- Basic queries work
- Caching functions correctly

NOTE: These tests require network access and download real data.
Mark as slow tests to skip in CI if needed.
"""

import pytest

from graphforge import GraphForge
from graphforge.datasets import load_dataset


@pytest.mark.integration
@pytest.mark.slow
class TestNetworkRepositoryValidation:
    """Validation tests with actual NetworkRepository downloads."""

    def test_karate_dataset_loads_and_validates(self, tmp_path):
        """Test karate dataset downloads and validates correctly."""
        gf = GraphForge()
        load_dataset(gf, "netrepo-karate")

        # Verify node count
        result = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert result[0]["count"].value == 34

        # Verify edge count
        result = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert result[0]["count"].value == 78

        # Test basic query - verify nodes exist
        result = gf.execute("MATCH (n) RETURN n LIMIT 1")
        assert len(result) == 1

    def test_dolphins_dataset_loads_and_validates(self, tmp_path):
        """Test dolphins dataset downloads and validates correctly."""
        gf = GraphForge()
        load_dataset(gf, "netrepo-dolphins")

        # Verify node count
        result = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert result[0]["count"].value == 62

        # Verify edge count
        result = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert result[0]["count"].value == 159

    def test_polbooks_dataset_loads_and_validates(self, tmp_path):
        """Test polbooks dataset downloads and validates correctly."""
        gf = GraphForge()
        load_dataset(gf, "netrepo-polbooks")

        # Verify node count
        result = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert result[0]["count"].value == 105

        # Verify edge count
        result = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert result[0]["count"].value == 441

    def test_football_dataset_loads_and_validates(self, tmp_path):
        """Test football dataset downloads and validates correctly."""
        gf = GraphForge()
        load_dataset(gf, "netrepo-football")

        # Verify node count
        result = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert result[0]["count"].value == 115

        # Verify edge count
        result = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert result[0]["count"].value == 613

    def test_lesmis_dataset_loads_and_validates(self, tmp_path):
        """Test lesmis dataset downloads and validates correctly."""
        gf = GraphForge()
        load_dataset(gf, "netrepo-lesmis")

        # Verify node count
        result = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert result[0]["count"].value == 77

        # Verify edge count
        result = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert result[0]["count"].value == 254

    def test_celegans_dataset_loads_and_validates(self, tmp_path):
        """Test celegans dataset downloads and validates correctly."""
        gf = GraphForge()
        load_dataset(gf, "netrepo-celegans")

        # Verify node count
        result = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert result[0]["count"].value == 297

        # Verify edge count
        result = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert result[0]["count"].value == 2148

    def test_netscience_dataset_loads_and_validates(self, tmp_path):
        """Test netscience dataset downloads and validates correctly."""
        gf = GraphForge()
        load_dataset(gf, "netrepo-netscience")

        # Verify node count
        result = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert result[0]["count"].value == 1589

        # Verify edge count
        result = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert result[0]["count"].value == 2742

    def test_jazz_dataset_loads_and_validates(self, tmp_path):
        """Test jazz dataset downloads and validates correctly."""
        gf = GraphForge()
        load_dataset(gf, "netrepo-jazz")

        # Verify node count
        result = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert result[0]["count"].value == 198

        # Verify edge count
        result = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert result[0]["count"].value == 2742

    def test_power_dataset_loads_and_validates(self, tmp_path):
        """Test power grid dataset downloads and validates correctly."""
        gf = GraphForge()
        load_dataset(gf, "netrepo-power")

        # Verify node count
        result = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert result[0]["count"].value == 4941

        # Verify edge count
        result = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert result[0]["count"].value == 6594

    def test_email_eu_dataset_loads_and_validates(self, tmp_path):
        """Test email-EU dataset downloads and validates correctly."""
        gf = GraphForge()
        load_dataset(gf, "netrepo-email-eu")

        # Verify node count
        result = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert result[0]["count"].value == 1005

        # Verify edge count
        result = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")
        assert result[0]["count"].value == 25571


@pytest.mark.integration
@pytest.mark.slow
class TestNetworkRepositoryCaching:
    """Test caching functionality for NetworkRepository datasets."""

    def test_dataset_caches_after_first_load(self, tmp_path):
        """Test that datasets are cached after first download."""
        import time

        # First load - downloads from network
        gf1 = GraphForge()
        start1 = time.time()
        load_dataset(gf1, "netrepo-karate")
        time1 = time.time() - start1

        # Second load - uses cache (should be much faster)
        gf2 = GraphForge()
        start2 = time.time()
        load_dataset(gf2, "netrepo-karate")
        time2 = time.time() - start2

        # Verify both have correct data
        result1 = gf1.execute("MATCH (n) RETURN count(n) AS count")
        result2 = gf2.execute("MATCH (n) RETURN count(n) AS count")
        assert result1[0]["count"].value == 34
        assert result2[0]["count"].value == 34

        # Second load should be faster (cached)
        # Allow some variance, but cached should be significantly faster
        assert time2 < time1 * 0.5 or time2 < 0.5, (
            f"Cached load ({time2:.2f}s) should be faster than first load ({time1:.2f}s)"
        )


@pytest.mark.integration
@pytest.mark.slow
class TestNetworkRepositoryQueries:
    """Test example queries on NetworkRepository datasets."""

    def test_karate_degree_centrality(self):
        """Test degree centrality query on karate club network."""
        gf = GraphForge()
        load_dataset(gf, "netrepo-karate")

        result = gf.execute("""
            MATCH (n)-[r]-()
            WITH n, count(r) AS degree
            RETURN degree, count(n) AS frequency
            ORDER BY degree DESC
            LIMIT 5
        """)

        # Should have results
        assert len(result) > 0

        # Degrees should be in descending order
        degrees = [row["degree"].value for row in result]
        assert degrees == sorted(degrees, reverse=True)

    def test_dolphins_community_structure(self):
        """Test community detection query on dolphin network."""
        gf = GraphForge()
        load_dataset(gf, "netrepo-dolphins")

        # Find nodes with many connections (potential community hubs)
        result = gf.execute("""
            MATCH (n)-[r]-()
            RETURN n, count(r) AS connections
            ORDER BY connections DESC
            LIMIT 10
        """)

        assert len(result) == 10

        # All should have at least 1 connection
        for row in result:
            assert row["connections"].value >= 1

    def test_netscience_collaboration_patterns(self):
        """Test collaboration patterns on netscience network."""
        gf = GraphForge()
        load_dataset(gf, "netrepo-netscience")

        # Find most collaborative authors
        result = gf.execute("""
            MATCH (author)-[:CONNECTED_TO]-(coauthor)
            WITH author, count(DISTINCT coauthor) AS collaborators
            RETURN collaborators, count(author) AS author_count
            ORDER BY collaborators DESC
            LIMIT 5
        """)

        assert len(result) > 0

        # Collaboration counts should be positive
        for row in result:
            assert row["collaborators"].value > 0
            assert row["author_count"].value > 0

    def test_power_grid_topology(self):
        """Test topology analysis on power grid network."""
        gf = GraphForge()
        load_dataset(gf, "netrepo-power")

        # Analyze degree distribution
        result = gf.execute("""
            MATCH (n)-[r]-()
            WITH n, count(r) AS degree
            WITH degree, count(n) AS frequency
            RETURN sum(frequency) AS total_nodes
        """)

        assert result[0]["total_nodes"].value == 4941


@pytest.mark.integration
@pytest.mark.slow
class TestNetworkRepositoryPerformance:
    """Performance benchmarks for NetworkRepository datasets."""

    def test_small_datasets_load_quickly(self):
        """Test that small datasets (< 100 KB) load in < 1 second."""
        import time

        small_datasets = [
            "netrepo-karate",
            "netrepo-dolphins",
            "netrepo-lesmis",
        ]

        for dataset_name in small_datasets:
            gf = GraphForge()
            start = time.time()
            load_dataset(gf, dataset_name)
            elapsed = time.time() - start

            assert elapsed < 1.0, f"{dataset_name} took {elapsed:.2f}s, expected < 1.0s"

    def test_medium_datasets_load_reasonably(self):
        """Test that medium datasets (100-500 KB) load in < 2 seconds."""
        import time

        medium_datasets = [
            "netrepo-netscience",
            "netrepo-power",
        ]

        for dataset_name in medium_datasets:
            gf = GraphForge()
            start = time.time()
            load_dataset(gf, dataset_name)
            elapsed = time.time() - start

            assert elapsed < 2.0, f"{dataset_name} took {elapsed:.2f}s, expected < 2.0s"
