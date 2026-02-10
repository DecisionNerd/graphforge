"""Dataset registry and loading functionality."""

import contextlib
from pathlib import Path
import shutil
import time
from typing import TYPE_CHECKING
from urllib.request import urlretrieve

from graphforge.datasets.base import Dataset, DatasetInfo, DatasetLoader

if TYPE_CHECKING:
    from graphforge import GraphForge

# Global registry of available datasets
_DATASET_REGISTRY: dict[str, DatasetInfo] = {}

# Global registry of dataset loaders
_LOADER_REGISTRY: dict[str, type[DatasetLoader]] = {}

# Cache directory for downloaded datasets
_CACHE_DIR = Path.home() / ".graphforge" / "datasets"

# Cache TTL (time to live) in seconds (default: 30 days)
_CACHE_TTL = 30 * 24 * 60 * 60


def register_dataset(info: DatasetInfo) -> None:
    """Register a dataset in the global registry.

    Args:
        info: Dataset metadata

    Raises:
        ValueError: If a dataset with the same name is already registered
    """
    if info.name in _DATASET_REGISTRY:
        raise ValueError(f"Dataset '{info.name}' is already registered")
    _DATASET_REGISTRY[info.name] = info


def register_loader(format_name: str, loader_class: type[DatasetLoader]) -> None:
    """Register a dataset loader for a specific format.

    Args:
        format_name: Format identifier (e.g., "csv", "cypher", "graphml")
        loader_class: The DatasetLoader class to use for this format

    Raises:
        ValueError: If a loader for this format is already registered
    """
    if format_name in _LOADER_REGISTRY:
        raise ValueError(f"Loader for format '{format_name}' is already registered")
    _LOADER_REGISTRY[format_name] = loader_class


def list_datasets(
    source: str | None = None,
    category: str | None = None,
    max_size_mb: float | None = None,
) -> list[DatasetInfo]:
    """List all available datasets, optionally filtered.

    Args:
        source: Filter by source (e.g., "snap", "neo4j")
        category: Filter by category (e.g., "social", "citation")
        max_size_mb: Only include datasets smaller than this size

    Returns:
        List of dataset metadata, sorted by name

    Examples:
        >>> # List all datasets
        >>> datasets = list_datasets()
        >>>
        >>> # List only SNAP datasets
        >>> snap_datasets = list_datasets(source="snap")
        >>>
        >>> # List small social networks
        >>> small_social = list_datasets(category="social", max_size_mb=10)
    """
    datasets = list(_DATASET_REGISTRY.values())

    if source:
        datasets = [d for d in datasets if d.source == source]

    if category:
        datasets = [d for d in datasets if d.category == category]

    if max_size_mb is not None:
        datasets = [d for d in datasets if d.size_mb <= max_size_mb]

    return sorted(datasets, key=lambda d: d.name)


def get_dataset_info(name: str) -> DatasetInfo:
    """Get metadata for a specific dataset.

    Args:
        name: Dataset name

    Returns:
        Dataset metadata

    Raises:
        ValueError: If dataset not found
    """
    if name not in _DATASET_REGISTRY:
        raise ValueError(
            f"Dataset '{name}' not found. Use list_datasets() to see available datasets."
        )
    return _DATASET_REGISTRY[name]


def _get_cache_path(name: str, url: str | None = None) -> Path:
    """Get the cache file path for a dataset.

    Args:
        name: Dataset name
        url: Dataset URL (used to preserve file extension)

    Returns:
        Path to cached dataset file with appropriate extension
    """
    # Create a filesystem-safe filename from dataset name
    safe_name = name.replace("/", "_").replace("\\", "_")

    # Preserve file extension from URL if provided
    if url:
        # Extract extension from URL (handles .txt.gz, .tar.gz, etc.)
        from urllib.parse import urlparse

        parsed_url = urlparse(url)
        url_path = parsed_url.path

        # Handle compound extensions like .txt.gz, .tar.gz
        if url_path.endswith(".txt.gz"):
            extension = ".txt.gz"
        elif url_path.endswith(".csv.gz"):
            extension = ".csv.gz"
        elif url_path.endswith(".tar.gz"):
            extension = ".tar.gz"
        elif "." in url_path:
            # Single extension
            extension = url_path[url_path.rfind(".") :]
        else:
            extension = ""

        if extension:
            safe_name = f"{safe_name}{extension}"

    return _CACHE_DIR / safe_name


def _validate_gzip_file(path: Path) -> bool:
    """Validate a gzip file by checking its CRC integrity.

    Args:
        path: Path to gzip file

    Returns:
        True if file is valid, False if corrupt or not a gzip file
    """
    import gzip

    if path.suffix != ".gz":
        return True  # Not a gzip file, skip validation

    try:
        # Try to open and read the file to verify CRC
        with gzip.open(path, "rb") as f:
            # Read in chunks to avoid loading entire file into memory
            while f.read(8192):
                pass  # Just verify we can decompress without CRC errors
        return True
    except (OSError, gzip.BadGzipFile):
        return False


def _is_cache_valid(cache_path: Path) -> bool:
    """Check if cached dataset is still valid (not expired and not corrupt).

    Args:
        cache_path: Path to cached dataset

    Returns:
        True if cache exists, is not expired, and passes integrity checks
    """
    if not cache_path.exists():
        return False

    # Check if cache has expired
    cache_age = time.time() - cache_path.stat().st_mtime
    if cache_age >= _CACHE_TTL:
        return False

    # For gzip files, validate integrity
    if cache_path.suffix == ".gz" or cache_path.name.endswith(".gz"):
        if not _validate_gzip_file(cache_path):
            # Corrupt file, remove it so it will be re-downloaded
            with contextlib.suppress(OSError):
                cache_path.unlink()
            return False

    return True


def _download_dataset(url: str, dest_path: Path, max_retries: int = 2) -> None:
    """Download a dataset from a URL with integrity validation and retry.

    Args:
        url: URL to download from (must be HTTP or HTTPS)
        dest_path: Destination file path
        max_retries: Number of times to retry download on failure (default: 2)

    Raises:
        ValueError: If URL scheme is not HTTP or HTTPS
        RuntimeError: If download fails after all retries
    """
    # Validate URL scheme for security (only allow HTTP/HTTPS)
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"Unsupported URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are allowed."
        )

    # Ensure cache directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Download to temporary file first (append .tmp to preserve extension)
    temp_path = dest_path.parent / f"{dest_path.name}.tmp"

    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            # Clean up any existing temp or corrupt destination files
            if temp_path.exists():
                temp_path.unlink()
            if dest_path.exists() and not _is_cache_valid(dest_path):
                dest_path.unlink()

            # Download the file
            urlretrieve(url, temp_path)  # nosec B310 - URL scheme validated above

            # Validate gzip files before finalizing
            if dest_path.suffix == ".gz" or dest_path.name.endswith(".gz"):
                # For gzip files, validate integrity before finalizing
                # Temporarily rename temp to final name for validation
                temp_path.rename(dest_path)

                if not _validate_gzip_file(dest_path):
                    dest_path.unlink()
                    raise RuntimeError("Downloaded file failed CRC check (corrupt or incomplete)")

                # Validation passed, file already in final location
            else:
                # Not a gzip file, move directly to destination
                temp_path.replace(dest_path)

            # Success!
            return

        except Exception as e:  # noqa: PERF203 - try-except in loop is intentional for retry logic
            last_error = e
            # Clean up any partial files
            if temp_path.exists():
                temp_path.unlink()
            if dest_path.exists():
                # Remove potentially corrupt destination file
                dest_path.unlink()

            if attempt < max_retries:
                # Wait a bit before retrying
                time.sleep(1)
                continue

    # All retries exhausted
    raise RuntimeError(
        f"Failed to download dataset after {max_retries + 1} attempts: {last_error}"
    ) from last_error


def load_dataset(gf: "GraphForge", name: str, force_download: bool = False) -> Dataset:
    """Load a dataset into a GraphForge instance.

    This function handles:
    1. Looking up dataset metadata
    2. Downloading the dataset (if not cached)
    3. Loading the dataset using the appropriate loader

    Args:
        gf: GraphForge instance to load data into
        name: Dataset name
        force_download: If True, re-download even if cached

    Returns:
        Dataset object with metadata and path

    Raises:
        ValueError: If dataset not found or invalid
        RuntimeError: If download or loading fails

    Examples:
        >>> gf = GraphForge()
        >>> dataset = load_dataset(gf, "snap-ego-facebook")
        >>> print(f"Loaded {dataset.info.nodes} nodes")
    """
    # Get dataset metadata
    info = get_dataset_info(name)

    # Get cache path (preserve file extension from URL)
    cache_path = _get_cache_path(name, info.url)

    # Download if needed
    if force_download or not _is_cache_valid(cache_path):
        _download_dataset(info.url, cache_path)

    # Get the appropriate loader
    if info.loader_class not in _LOADER_REGISTRY:
        raise ValueError(f"Loader '{info.loader_class}' not registered for dataset '{name}'")

    loader_class = _LOADER_REGISTRY[info.loader_class]
    loader = loader_class()

    # Load the dataset
    loader.load(gf, cache_path)

    return Dataset(info=info, path=cache_path)


def clear_cache(name: str | None = None) -> None:
    """Clear cached datasets.

    Args:
        name: If provided, clear only this dataset's cache.
              If None, clear all cached datasets.

    Examples:
        >>> # Clear a specific dataset
        >>> clear_cache("snap-ego-facebook")
        >>>
        >>> # Clear all cached datasets
        >>> clear_cache()
    """
    if name:
        # Get dataset info to construct correct cache path with extension
        try:
            info = get_dataset_info(name)
            cache_path = _get_cache_path(name, info.url)
        except ValueError:
            # If dataset not found, try without URL (for backward compatibility)
            cache_path = _get_cache_path(name)

        if cache_path.exists():
            if cache_path.is_dir():
                shutil.rmtree(cache_path)
            else:
                cache_path.unlink()
    elif _CACHE_DIR.exists():
        shutil.rmtree(_CACHE_DIR)
