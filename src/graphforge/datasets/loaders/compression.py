"""Compression utilities for dataset files.

Handles various compression formats used by graph datasets:
- .tar.zst (Zstandard tar archives, used by LDBC)
- .tar.gz (Gzip tar archives)
- .gz (Gzip files)
- .zip (Zip archives)
"""

from pathlib import Path
import tarfile

try:
    import zstandard as zstd  # type: ignore[import-not-found]

    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False


def extract_tar_zst(archive_path: Path, extract_to: Path) -> None:
    """Extract a .tar.zst archive using zstandard.

    Args:
        archive_path: Path to .tar.zst file
        extract_to: Directory to extract files into

    Raises:
        ImportError: If zstandard package is not installed
        FileNotFoundError: If archive doesn't exist
        ValueError: If extraction fails
    """
    if not ZSTD_AVAILABLE:
        raise ImportError(
            "zstandard package required for .tar.zst files. Install with: pip install zstandard"
        )

    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    extract_to.mkdir(parents=True, exist_ok=True)

    # Open zstd-compressed file
    with archive_path.open("rb") as compressed_file:
        # Create zstd decompressor
        dctx = zstd.ZstdDecompressor()

        # Decompress and extract tar
        with (
            dctx.stream_reader(compressed_file) as reader,
            tarfile.open(fileobj=reader, mode="r|") as tar,
        ):
            # Extract all files safely (filter='data' prevents path traversal attacks)
            tar.extractall(extract_to, filter="data")


def extract_archive(archive_path: Path, extract_to: Path) -> Path:
    """Extract an archive file to a directory.

    Automatically detects compression format based on file extension.

    Args:
        archive_path: Path to archive file
        extract_to: Directory to extract files into

    Returns:
        Path to extracted directory

    Raises:
        ValueError: If archive format is unsupported
        FileNotFoundError: If archive doesn't exist
    """
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    extract_to.mkdir(parents=True, exist_ok=True)

    # Determine compression format
    if archive_path.suffixes[-2:] == [".tar", ".zst"]:
        # .tar.zst
        extract_tar_zst(archive_path, extract_to)
    elif archive_path.suffixes[-2:] == [".tar", ".gz"]:
        # .tar.gz
        with tarfile.open(archive_path, "r:gz") as tar:
            # Extract safely (filter='data' prevents path traversal attacks)
            tar.extractall(extract_to, filter="data")
    elif archive_path.suffix == ".tar":
        # .tar (uncompressed)
        with tarfile.open(archive_path, "r") as tar:
            # Extract safely (filter='data' prevents path traversal attacks)
            tar.extractall(extract_to, filter="data")
    else:
        raise ValueError(f"Unsupported archive format: {archive_path.suffixes}")

    return extract_to


def is_compressed_archive(path: Path) -> bool:
    """Check if a file is a supported compressed archive.

    Args:
        path: Path to check

    Returns:
        True if file is a supported archive format
    """
    # Check for .tar.zst or .tar.gz
    if path.suffixes[-2:] in [[".tar", ".zst"], [".tar", ".gz"]]:
        return True

    # Check for plain .tar
    if path.suffix == ".tar":
        return True

    return False
