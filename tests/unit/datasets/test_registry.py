"""Unit tests for dataset registry functionality."""

from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch

import pytest

from graphforge import GraphForge
from graphforge.datasets.base import DatasetInfo, DatasetLoader
from graphforge.datasets.registry import (
    _CACHE_DIR,
    _DATASET_REGISTRY,
    _LOADER_REGISTRY,
    clear_cache,
    get_dataset_info,
    list_datasets,
    load_dataset,
    register_dataset,
    register_loader,
)


class MockLoader(DatasetLoader):
    """Mock loader for testing."""

    def load(self, gf: GraphForge, path: Path) -> None:
        """Mock load that creates a simple node."""
        gf.create_node(["TestNode"], name="test")

    def get_format(self) -> str:
        """Return mock format."""
        return "mock"


class TestDatasetRegistration:
    """Test dataset registration."""

    def setup_method(self):
        """Clear registry before each test."""
        _DATASET_REGISTRY.clear()
        _LOADER_REGISTRY.clear()

    def test_register_dataset(self):
        """Test registering a dataset."""
        info = DatasetInfo(
            name="test-dataset",
            description="Test dataset",
            source="test",
            url="http://example.com/test.csv",
            nodes=100,
            edges=200,
            labels=["Person"],
            relationship_types=["KNOWS"],
            size_mb=1.5,
            license="MIT",
            category="social",
            loader_class="mock",
        )

        register_dataset(info)

        assert "test-dataset" in _DATASET_REGISTRY
        assert _DATASET_REGISTRY["test-dataset"] == info

    def test_register_duplicate_dataset_fails(self):
        """Test that registering a duplicate dataset raises an error."""
        info = DatasetInfo(
            name="test-dataset",
            description="Test dataset",
            source="test",
            url="http://example.com/test.csv",
            nodes=100,
            edges=200,
            labels=["Person"],
            relationship_types=["KNOWS"],
            size_mb=1.5,
            license="MIT",
            category="social",
            loader_class="mock",
        )

        register_dataset(info)

        with pytest.raises(ValueError, match="already registered"):
            register_dataset(info)

    def test_register_loader(self):
        """Test registering a loader."""
        register_loader("mock", MockLoader)

        assert "mock" in _LOADER_REGISTRY
        assert _LOADER_REGISTRY["mock"] == MockLoader

    def test_register_duplicate_loader_fails(self):
        """Test that registering a duplicate loader raises an error."""
        register_loader("mock", MockLoader)

        with pytest.raises(ValueError, match="already registered"):
            register_loader("mock", MockLoader)


class TestDatasetListing:
    """Test dataset listing and filtering."""

    def setup_method(self):
        """Set up test datasets."""
        _DATASET_REGISTRY.clear()

        # Register test datasets
        datasets = [
            DatasetInfo(
                name="snap-small",
                description="Small SNAP dataset",
                source="snap",
                url="http://example.com/snap-small.csv",
                nodes=100,
                edges=200,
                labels=["Node"],
                relationship_types=["EDGE"],
                size_mb=1.0,
                license="Public Domain",
                category="social",
                loader_class="csv",
            ),
            DatasetInfo(
                name="snap-large",
                description="Large SNAP dataset",
                source="snap",
                url="http://example.com/snap-large.csv",
                nodes=10000,
                edges=50000,
                labels=["Node"],
                relationship_types=["EDGE"],
                size_mb=50.0,
                license="Public Domain",
                category="social",
                loader_class="csv",
            ),
            DatasetInfo(
                name="neo4j-movies",
                description="Neo4j movies dataset",
                source="neo4j",
                url="http://example.com/movies.cypher",
                nodes=500,
                edges=1000,
                labels=["Person", "Movie"],
                relationship_types=["ACTED_IN", "DIRECTED"],
                size_mb=5.0,
                license="Apache 2.0",
                category="entertainment",
                loader_class="cypher",
            ),
        ]

        for ds in datasets:
            register_dataset(ds)

    def test_list_all_datasets(self):
        """Test listing all datasets."""
        datasets = list_datasets()

        assert len(datasets) == 3
        # Should be sorted by name
        assert datasets[0].name == "neo4j-movies"
        assert datasets[1].name == "snap-large"
        assert datasets[2].name == "snap-small"

    def test_filter_by_source(self):
        """Test filtering datasets by source."""
        datasets = list_datasets(source="snap")

        assert len(datasets) == 2
        assert all(d.source == "snap" for d in datasets)

    def test_filter_by_category(self):
        """Test filtering datasets by category."""
        datasets = list_datasets(category="social")

        assert len(datasets) == 2
        assert all(d.category == "social" for d in datasets)

    def test_filter_by_max_size(self):
        """Test filtering datasets by maximum size."""
        datasets = list_datasets(max_size_mb=10.0)

        assert len(datasets) == 2
        assert all(d.size_mb <= 10.0 for d in datasets)

    def test_filter_multiple_criteria(self):
        """Test filtering with multiple criteria."""
        datasets = list_datasets(source="snap", max_size_mb=10.0)

        assert len(datasets) == 1
        assert datasets[0].name == "snap-small"

    def test_get_dataset_info(self):
        """Test retrieving specific dataset info."""
        info = get_dataset_info("neo4j-movies")

        assert info.name == "neo4j-movies"
        assert info.source == "neo4j"
        assert info.category == "entertainment"

    def test_get_nonexistent_dataset_info_fails(self):
        """Test that getting info for nonexistent dataset raises error."""
        with pytest.raises(ValueError, match="not found"):
            get_dataset_info("nonexistent")


class TestDatasetCaching:
    """Test dataset caching functionality."""

    def setup_method(self):
        """Set up test environment."""
        _DATASET_REGISTRY.clear()
        _LOADER_REGISTRY.clear()

        # Use a temporary directory for cache
        self.temp_cache = tempfile.mkdtemp()
        self.original_cache = _CACHE_DIR

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_cache, ignore_errors=True)

    def test_clear_cache_single_dataset(self):
        """Test clearing cache for a single dataset."""
        with patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)):
            # Create a fake cached file
            cache_file = Path(self.temp_cache) / "test-dataset"
            cache_file.touch()

            assert cache_file.exists()

            clear_cache("test-dataset")

            assert not cache_file.exists()

    def test_clear_cache_all_datasets(self):
        """Test clearing entire cache."""
        with patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)):
            # Create fake cached files
            (Path(self.temp_cache) / "dataset1").touch()
            (Path(self.temp_cache) / "dataset2").touch()

            clear_cache()

            assert not Path(self.temp_cache).exists()

    def test_clear_cache_nonexistent_dataset(self):
        """Test clearing cache for nonexistent dataset doesn't error."""
        with patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)):
            # Should not raise an error
            clear_cache("nonexistent-dataset")


class TestDatasetLoading:
    """Test dataset loading functionality."""

    def setup_method(self):
        """Set up test environment."""
        _DATASET_REGISTRY.clear()
        _LOADER_REGISTRY.clear()

        # Register mock loader
        register_loader("mock", MockLoader)

        # Register test dataset
        self.test_info = DatasetInfo(
            name="test-dataset",
            description="Test dataset",
            source="test",
            url="http://example.com/test.csv",
            nodes=100,
            edges=200,
            labels=["Person"],
            relationship_types=["KNOWS"],
            size_mb=1.5,
            license="MIT",
            category="social",
            loader_class="mock",
        )
        register_dataset(self.test_info)

        # Use temporary directory for cache
        self.temp_cache = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_cache, ignore_errors=True)

    def test_load_dataset_downloads_and_loads(self):
        """Test that load_dataset downloads and loads the dataset."""
        with (
            patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)),
            patch("graphforge.datasets.registry.urlretrieve") as mock_download,
        ):
            # Mock successful download
            def side_effect(url, path):
                Path(path).touch()

            mock_download.side_effect = side_effect

            gf = GraphForge()
            dataset = load_dataset(gf, "test-dataset")

            # Verify download was called
            mock_download.assert_called_once()

            # Verify dataset was loaded
            assert dataset.info == self.test_info
            assert dataset.path.exists()

            # Verify mock loader created a node
            results = gf.execute("MATCH (n:TestNode) RETURN n.name as name")
            assert len(results) == 1
            assert results[0]["name"].value == "test"

    def test_load_dataset_uses_cache_if_valid(self):
        """Test that load_dataset uses cached file if available."""
        with patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)):
            # Create a cached file (with extension matching the URL)
            cache_path = Path(self.temp_cache) / "test-dataset.csv"
            cache_path.touch()

            with patch("graphforge.datasets.registry.urlretrieve") as mock_download:
                gf = GraphForge()
                load_dataset(gf, "test-dataset")

                # Should not download if cache is valid
                mock_download.assert_not_called()

    def test_load_dataset_force_download(self):
        """Test that force_download bypasses cache."""
        with patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)):
            # Create a cached file (with extension matching the URL)
            cache_path = Path(self.temp_cache) / "test-dataset.csv"
            cache_path.touch()

            with patch("graphforge.datasets.registry.urlretrieve") as mock_download:
                # Mock successful download
                def side_effect(url, path):
                    Path(path).touch()

                mock_download.side_effect = side_effect

                gf = GraphForge()
                load_dataset(gf, "test-dataset", force_download=True)

                # Should download even with valid cache
                mock_download.assert_called_once()

    def test_load_nonexistent_dataset_fails(self):
        """Test that loading a nonexistent dataset raises an error."""
        gf = GraphForge()

        with pytest.raises(ValueError, match="not found"):
            load_dataset(gf, "nonexistent-dataset")

    def test_load_dataset_with_unregistered_loader_fails(self):
        """Test that loading with unregistered loader raises an error."""
        # Register dataset with non-existent loader
        info = DatasetInfo(
            name="bad-dataset",
            description="Dataset with bad loader",
            source="test",
            url="http://example.com/bad.csv",
            nodes=10,
            edges=20,
            labels=["Node"],
            relationship_types=["EDGE"],
            size_mb=1.0,
            license="MIT",
            category="test",
            loader_class="nonexistent",
        )
        register_dataset(info)

        with (
            patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)),
            patch("graphforge.datasets.registry.urlretrieve") as mock_download,
        ):
            # Mock successful download
            def side_effect(url, path):
                Path(path).touch()

            mock_download.side_effect = side_effect

            gf = GraphForge()

            with pytest.raises(ValueError, match="not registered"):
                load_dataset(gf, "bad-dataset")

    def test_load_dataset_rejects_unsafe_url_schemes(self):
        """Test that unsafe URL schemes are rejected by Pydantic validation."""
        from pydantic import ValidationError

        # Pydantic now validates URL schemes at DatasetInfo construction time
        with pytest.raises(ValidationError, match="Invalid URL scheme"):
            DatasetInfo(
                name="unsafe-dataset",
                description="Dataset with unsafe URL",
                source="test",
                url="file:///etc/passwd",
                nodes=10,
                edges=20,
                labels=["Node"],
                relationship_types=["EDGE"],
                size_mb=1.0,
                license="MIT",
                category="test",
                loader_class="mock",
            )


class TestGraphForgeFromDataset:
    """Test GraphForge.from_dataset() classmethod."""

    def setup_method(self):
        """Set up test environment."""
        _DATASET_REGISTRY.clear()
        _LOADER_REGISTRY.clear()

        # Register mock loader
        register_loader("mock", MockLoader)

        # Register test dataset
        info = DatasetInfo(
            name="test-dataset",
            description="Test dataset",
            source="test",
            url="http://example.com/test.csv",
            nodes=100,
            edges=200,
            labels=["Person"],
            relationship_types=["KNOWS"],
            size_mb=1.5,
            license="MIT",
            category="social",
            loader_class="mock",
        )
        register_dataset(info)

        self.temp_cache = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_cache, ignore_errors=True)

    def test_from_dataset_creates_and_loads(self):
        """Test that from_dataset creates instance and loads dataset."""
        with (
            patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)),
            patch("graphforge.datasets.registry.urlretrieve") as mock_download,
        ):
            # Mock successful download
            def side_effect(url, path):
                Path(path).touch()

            mock_download.side_effect = side_effect

            gf = GraphForge.from_dataset("test-dataset")

            # Verify instance was created and dataset loaded
            assert isinstance(gf, GraphForge)

            # Verify mock loader created a node
            results = gf.execute("MATCH (n:TestNode) RETURN n.name as name")
            assert len(results) == 1
            assert results[0]["name"].value == "test"
