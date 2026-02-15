"""Unit tests for dataset registry functionality."""

import gzip
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
    _download_dataset,
    _get_cache_path,
    _is_cache_valid,
    _validate_gzip_file,
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
            url="https://example.com/test.csv",
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
            url="https://example.com/test.csv",
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
                url="https://example.com/snap-small.csv",
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
                url="https://example.com/snap-large.csv",
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
                url="https://example.com/movies.cypher",
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

    def test_clear_cache_single_dataset_with_extension(self):
        """Test clearing cache for dataset with URL extension."""
        # Register dataset with URL that has extension
        info = DatasetInfo(
            name="test-dataset-ext",
            description="Test",
            source="test",
            url="https://example.com/data.txt.gz",
            nodes=100,
            edges=200,
            labels=["Node"],
            relationship_types=["EDGE"],
            size_mb=1.0,
            license="MIT",
            category="test",
            loader_class="csv",
        )
        register_dataset(info)

        with patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)):
            # Create cache file with extension matching URL
            cache_file = Path(self.temp_cache) / "test-dataset-ext.txt.gz"
            cache_file.touch()

            assert cache_file.exists()

            clear_cache("test-dataset-ext")

            assert not cache_file.exists()

    def test_clear_cache_directory(self):
        """Test clearing cache when it's a directory."""
        with patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)):
            # Create a directory instead of a file
            cache_dir = Path(self.temp_cache) / "test-dataset-dir"
            cache_dir.mkdir()
            (cache_dir / "file1.txt").touch()
            (cache_dir / "file2.txt").touch()

            assert cache_dir.exists()
            assert cache_dir.is_dir()

            clear_cache("test-dataset-dir")

            assert not cache_dir.exists()

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

    def test_clear_cache_when_cache_dir_does_not_exist(self):
        """Test clearing all cache when cache directory doesn't exist."""
        with patch(
            "graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache) / "nonexistent"
        ):
            # Should not raise an error
            clear_cache()


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
            url="https://example.com/test.csv",
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
            url="https://example.com/bad.csv",
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
            url="https://example.com/test.csv",
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


class TestGetCachePath:
    """Test _get_cache_path helper function."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_cache = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_cache, ignore_errors=True)

    def test_cache_path_no_url(self):
        """Test cache path without URL (no extension)."""
        with patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)):
            path = _get_cache_path("test-dataset")
            assert path == Path(self.temp_cache) / "test-dataset"

    def test_cache_path_with_txt_gz_extension(self):
        """Test cache path preserves .txt.gz extension."""
        with patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)):
            path = _get_cache_path("test-dataset", "https://example.com/data.txt.gz")
            assert path == Path(self.temp_cache) / "test-dataset.txt.gz"

    def test_cache_path_with_csv_gz_extension(self):
        """Test cache path preserves .csv.gz extension."""
        with patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)):
            path = _get_cache_path("test-dataset", "https://example.com/data.csv.gz")
            assert path == Path(self.temp_cache) / "test-dataset.csv.gz"

    def test_cache_path_with_tar_gz_extension(self):
        """Test cache path preserves .tar.gz extension."""
        with patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)):
            path = _get_cache_path("test-dataset", "https://example.com/data.tar.gz")
            assert path == Path(self.temp_cache) / "test-dataset.tar.gz"

    def test_cache_path_with_single_extension(self):
        """Test cache path preserves single extension."""
        with patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)):
            path = _get_cache_path("test-dataset", "https://example.com/data.csv")
            assert path == Path(self.temp_cache) / "test-dataset.csv"

    def test_cache_path_with_no_extension(self):
        """Test cache path with URL without extension."""
        with patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)):
            path = _get_cache_path("test-dataset", "https://example.com/data")
            assert path == Path(self.temp_cache) / "test-dataset"

    def test_cache_path_sanitizes_slashes(self):
        """Test cache path sanitizes forward and back slashes in name."""
        with patch("graphforge.datasets.registry._CACHE_DIR", Path(self.temp_cache)):
            path = _get_cache_path("test/dataset\\name", "https://example.com/data.csv")
            assert path == Path(self.temp_cache) / "test_dataset_name.csv"


class TestValidateGzipFile:
    """Test _validate_gzip_file helper function."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_non_gzip_file(self):
        """Test validation passes for non-gzip files."""
        # Create a non-gzip file
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("Hello, world!")

        assert _validate_gzip_file(test_file) is True

    def test_validate_valid_gzip_file(self):
        """Test validation passes for valid gzip files."""
        # Create a valid gzip file
        test_file = Path(self.temp_dir) / "test.txt.gz"
        with gzip.open(test_file, "wt") as f:
            f.write("Hello, world!\n" * 1000)

        assert _validate_gzip_file(test_file) is True

    def test_validate_corrupt_gzip_file(self):
        """Test validation fails for corrupt gzip files."""
        # Create a gzip file with invalid magic bytes (corrupt header)
        test_file = Path(self.temp_dir) / "test.txt.gz"
        # Write invalid gzip header (correct format starts with 0x1f 0x8b)
        test_file.write_bytes(b"\x1f\x8c\x08\x00\x00\x00\x00\x00\x00\x00")

        assert _validate_gzip_file(test_file) is False

    def test_validate_fake_gzip_file(self):
        """Test validation fails for file with .gz extension but not gzip format."""
        test_file = Path(self.temp_dir) / "fake.gz"
        test_file.write_text("This is not a gzip file")

        assert _validate_gzip_file(test_file) is False


class TestIsCacheValid:
    """Test _is_cache_valid helper function."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_nonexistent_cache_invalid(self):
        """Test that nonexistent cache is invalid."""
        test_file = Path(self.temp_dir) / "nonexistent.txt"
        assert _is_cache_valid(test_file) is False

    def test_fresh_cache_valid(self):
        """Test that fresh cache is valid."""
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("Hello, world!")

        assert _is_cache_valid(test_file) is True

    def test_expired_cache_invalid(self):
        """Test that expired cache is invalid."""
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("Hello, world!")

        # Mock time to make cache appear expired
        with patch("graphforge.datasets.registry.time.time") as mock_time:
            # Set current time to 31 days after file creation
            mock_time.return_value = test_file.stat().st_mtime + (31 * 24 * 60 * 60)
            assert _is_cache_valid(test_file) is False

    def test_corrupt_gzip_removed_and_invalid(self):
        """Test that corrupt gzip files are removed and marked invalid."""
        # Create a corrupt gzip file
        test_file = Path(self.temp_dir) / "test.txt.gz"
        test_file.write_text("This is not a valid gzip file")

        assert test_file.exists()
        assert _is_cache_valid(test_file) is False
        # File should be removed after validation failure
        assert not test_file.exists()

    def test_valid_gzip_cache_valid(self):
        """Test that valid gzip cache is marked valid."""
        # Create a valid gzip file
        test_file = Path(self.temp_dir) / "test.txt.gz"
        with gzip.open(test_file, "wt") as f:
            f.write("Hello, world!\n" * 100)

        assert _is_cache_valid(test_file) is True


class TestDownloadDataset:
    """Test _download_dataset helper function."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_download_rejects_file_url(self):
        """Test that file:// URLs are rejected."""
        dest_path = Path(self.temp_dir) / "output.txt"

        with pytest.raises(ValueError, match="Unsupported URL scheme"):
            _download_dataset("file:///etc/passwd", dest_path)

    def test_download_rejects_ftp_url(self):
        """Test that ftp:// URLs are rejected."""
        dest_path = Path(self.temp_dir) / "output.txt"

        with pytest.raises(ValueError, match="Unsupported URL scheme"):
            _download_dataset("ftp://example.com/data.txt", dest_path)

    def test_download_creates_parent_directory(self):
        """Test that download creates parent directory if needed."""
        dest_path = Path(self.temp_dir) / "subdir" / "output.txt"

        with patch("graphforge.datasets.registry.urlretrieve") as mock_download:
            # Mock successful download
            def side_effect(url, path):
                Path(path).touch()

            mock_download.side_effect = side_effect

            _download_dataset("https://example.com/data.txt", dest_path)

            assert dest_path.parent.exists()

    def test_download_retries_on_failure(self):
        """Test that download retries on failure."""
        dest_path = Path(self.temp_dir) / "output.txt"

        with patch("graphforge.datasets.registry.urlretrieve") as mock_download:
            # Fail twice, succeed on third attempt
            call_count = [0]

            def side_effect(url, path):
                call_count[0] += 1
                if call_count[0] < 3:
                    raise RuntimeError("Download failed")
                Path(path).touch()

            mock_download.side_effect = side_effect

            # Should succeed after retries
            _download_dataset("https://example.com/data.txt", dest_path, max_retries=2)

            # Should have been called 3 times (initial + 2 retries)
            assert call_count[0] == 3
            assert dest_path.exists()

    def test_download_fails_after_max_retries(self):
        """Test that download fails after exhausting retries."""
        dest_path = Path(self.temp_dir) / "output.txt"

        with patch("graphforge.datasets.registry.urlretrieve") as mock_download:
            # Always fail
            mock_download.side_effect = RuntimeError("Download failed")

            with pytest.raises(RuntimeError, match="Failed to download dataset after 3 attempts"):
                _download_dataset("https://example.com/data.txt", dest_path, max_retries=2)

    def test_download_validates_gzip_files(self):
        """Test that gzip files are validated after download."""
        dest_path = Path(self.temp_dir) / "output.txt.gz"

        with patch("graphforge.datasets.registry.urlretrieve") as mock_download:
            # Create a corrupt gzip file
            def side_effect(url, path):
                Path(path).write_text("Not a valid gzip file")

            mock_download.side_effect = side_effect

            # Should fail validation and retry
            with pytest.raises(RuntimeError, match="Failed to download dataset"):
                _download_dataset("https://example.com/data.txt.gz", dest_path, max_retries=1)

    def test_download_cleans_up_temp_files_on_failure(self):
        """Test that temporary files are cleaned up on failure."""
        dest_path = Path(self.temp_dir) / "output.txt"
        temp_path = Path(self.temp_dir) / "output.txt.tmp"

        with patch("graphforge.datasets.registry.urlretrieve") as mock_download:
            # Create temp file then fail
            def side_effect(url, path):
                Path(path).touch()
                raise RuntimeError("Download failed")

            mock_download.side_effect = side_effect

            with pytest.raises(RuntimeError, match="Failed to download dataset"):
                _download_dataset("https://example.com/data.txt", dest_path, max_retries=0)

            # Temp file should be cleaned up
            assert not temp_path.exists()
            assert not dest_path.exists()

    def test_download_removes_corrupt_destination_on_retry(self):
        """Test that corrupt destination files are removed before retry."""
        dest_path = Path(self.temp_dir) / "output.txt"

        with patch("graphforge.datasets.registry.urlretrieve") as mock_download:
            call_count = [0]

            def side_effect(url, path):
                call_count[0] += 1
                if call_count[0] == 1:
                    # First attempt: create file then fail
                    Path(path).touch()
                    raise RuntimeError("Download failed")
                # Second attempt: succeed
                Path(path).touch()

            mock_download.side_effect = side_effect

            _download_dataset("https://example.com/data.txt", dest_path, max_retries=1)

            assert dest_path.exists()
            assert call_count[0] == 2
