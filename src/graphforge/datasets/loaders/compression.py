"""Compression utilities for dataset files.

Handles various compression formats used by graph datasets:
- .tar.zst (Zstandard tar archives, used by LDBC)
- .tar.gz (Gzip tar archives)
- .tar (Uncompressed tar archives)

Supported formats are detected by extract_archive() and is_compressed_archive().
"""

import os
from pathlib import Path
import tarfile

try:
    import zstandard as zstd  # type: ignore[import-not-found]

    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False


def safe_extract_tar(tar: tarfile.TarFile, extract_to: Path) -> None:
    """Safely extract tar archive members with path traversal validation.

    Validates each member to prevent path traversal attacks by ensuring
    extracted files remain within the target directory.

    Args:
        tar: Open TarFile object to extract from
        extract_to: Directory to extract files into

    Raises:
        ValueError: If a member path would escape the extraction directory
    """
    # Resolve the extraction directory to absolute path
    extract_to_resolved = extract_to.resolve()

    for member in tar.getmembers():
        # Compute target path for this member
        target_path = extract_to / member.name

        # Resolve to absolute path and check if it's within extraction directory
        try:
            target_path_resolved = target_path.resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid member path '{member.name}': cannot resolve path") from e

        # Ensure the resolved path is within the extraction directory
        if not str(target_path_resolved).startswith(str(extract_to_resolved) + os.sep):
            # Also check exact match (for files directly in extract_to)
            if target_path_resolved != extract_to_resolved:
                raise ValueError(
                    f"Path traversal attempt detected: '{member.name}' "
                    f"would extract to '{target_path_resolved}' "
                    f"outside of '{extract_to_resolved}'"
                )

        # Refuse absolute paths
        if member.name.startswith("/") or member.name.startswith("\\"):
            raise ValueError(f"Absolute path not allowed: '{member.name}'")

        # Refuse paths with parent directory references
        if ".." in Path(member.name).parts:
            raise ValueError(f"Parent directory reference not allowed: '{member.name}'")

        # Extract this validated member
        tar.extract(member, extract_to)


def extract_tar_zst(archive_path: Path, extract_to: Path) -> None:
    """Extract a .tar.zst archive using zstandard.

    Args:
        archive_path: Path to .tar.zst file
        extract_to: Directory to extract files into

    Raises:
        ImportError: If zstandard package is not installed
        FileNotFoundError: If archive doesn't exist
        ValueError: If extraction fails or path traversal detected
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
            # Extract with path validation
            safe_extract_tar(tar, extract_to)


def extract_archive(archive_path: Path, extract_to: Path) -> Path:
    """Extract an archive file to a directory.

    Automatically detects compression format based on file extension.
    Supported formats: .tar.zst, .tar.gz, .tar

    Args:
        archive_path: Path to archive file
        extract_to: Directory to extract files into

    Returns:
        Path to extracted directory

    Raises:
        ValueError: If archive format is unsupported or path traversal detected
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
            safe_extract_tar(tar, extract_to)
    elif archive_path.suffix == ".tar":
        # .tar (uncompressed)
        with tarfile.open(archive_path, "r") as tar:
            safe_extract_tar(tar, extract_to)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path.suffixes}")

    return extract_to


def is_compressed_archive(path: Path) -> bool:
    """Check if a file is a supported compressed archive.

    Checks for formats supported by extract_archive(): .tar.zst, .tar.gz, .tar

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
