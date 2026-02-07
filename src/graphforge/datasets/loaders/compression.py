"""Compression utilities for dataset files.

Handles various compression formats used by graph datasets:
- .tar.zst (Zstandard tar archives, used by LDBC)
- .tar.gz (Gzip tar archives)
- .tar (Uncompressed tar archives)
- .zip (Zip archives, used by NetworkRepository)

Supported formats are detected by extract_archive() and is_compressed_archive().
"""

import os
from pathlib import Path, PurePosixPath
import re
import sys
import tarfile
import zipfile

try:
    import zstandard as zstd

    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False


# Regex patterns for Windows path detection
_WINDOWS_DRIVE_RE = re.compile(r"^[a-zA-Z]:[\\/]")
_UNC_RE = re.compile(r"^[\\/]{2}[^\\/]+[\\/]+[^\\/]+")  # \\server\share or //server/share


def _validate_archive_member(name: str) -> None:
    """Validate an archive member name for security (absolute or traversal).

    Args:
        name: Archive member name to validate

    Raises:
        ValueError: If the name is unsafe (absolute path or contains parent traversal)
    """
    # TAR member names are POSIX-ish, but can contain backslashes.
    # Convert backslashes to forward slashes for consistent checks.
    normalized = name.replace("\\", "/")

    # Reject Windows absolute path variants + Unix absolute paths
    if normalized.startswith("/"):
        raise ValueError(f"Absolute path not allowed: '{name}'")
    if name.startswith("\\"):  # Critical for Windows backslash-absolute paths
        raise ValueError(f"Absolute path not allowed: '{name}'")
    if _WINDOWS_DRIVE_RE.match(name):
        raise ValueError(f"Absolute path not allowed: '{name}'")
    if _UNC_RE.match(name):
        raise ValueError(f"Absolute path not allowed: '{name}'")

    # Reject parent traversal
    parts = PurePosixPath(normalized).parts
    if ".." in parts:
        raise ValueError(f"Parent directory reference not allowed: '{name}'")


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
        # Validate member name for security (absolute paths, traversal, etc.)
        _validate_archive_member(member.name)

        # Normalize to forward slashes for extraction
        normalized = member.name.replace("\\", "/")
        target_path = extract_to / normalized

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

        # Extract this validated member
        # Python 3.12+ supports filter="data" to strip metadata (avoids deprecation warning)
        if sys.version_info >= (3, 12):
            # Use filter parameter on Python 3.12+ to avoid deprecation warning
            tar.extract(member, extract_to, filter="data")  # type: ignore[call-arg]
        else:
            # Python 3.10-3.11 don't support filter parameter
            tar.extract(member, extract_to)


def safe_extract_zip(zip_file: zipfile.ZipFile, extract_to: Path) -> None:
    """Safely extract zip archive members with path traversal validation.

    Validates each member to prevent path traversal attacks by ensuring
    extracted files remain within the target directory.

    Args:
        zip_file: Open ZipFile object to extract from
        extract_to: Directory to extract files into

    Raises:
        ValueError: If a member path would escape the extraction directory
    """
    # Resolve the extraction directory to absolute path
    extract_to_resolved = extract_to.resolve()

    for member in zip_file.namelist():
        # Validate member name for security (absolute paths, traversal, etc.)
        _validate_archive_member(member)

        # Normalize to forward slashes for extraction
        normalized = member.replace("\\", "/")
        target_path = extract_to / normalized

        # Resolve to absolute path and check if it's within extraction directory
        try:
            target_path_resolved = target_path.resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid member path '{member}': cannot resolve path") from e

        # Ensure the resolved path is within the extraction directory
        if not str(target_path_resolved).startswith(str(extract_to_resolved) + os.sep):
            # Also check exact match (for files directly in extract_to)
            if target_path_resolved != extract_to_resolved:
                raise ValueError(
                    f"Path traversal attempt detected: '{member}' "
                    f"would extract to '{target_path_resolved}' "
                    f"outside of '{extract_to_resolved}'"
                )

        # Extract this validated member
        zip_file.extract(member, extract_to)


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

    # Open zstd-compressed file and decompress to temporary tar
    import tempfile

    # Use delete=False for Windows compatibility (avoids exclusive lock issues)
    temp_tar_file = tempfile.NamedTemporaryFile(suffix=".tar", delete=False)  # noqa: SIM115
    temp_path = Path(temp_tar_file.name)

    try:
        with archive_path.open("rb") as compressed_file:
            # Create zstd decompressor
            dctx = zstd.ZstdDecompressor()

            # Decompress to temporary file
            with dctx.stream_reader(compressed_file) as reader:
                temp_tar_file.write(reader.read())
                temp_tar_file.flush()

        # Close temp file before re-opening (required on Windows)
        temp_tar_file.close()

        # Extract tar with path validation
        with tarfile.open(temp_path, "r") as tar:
            safe_extract_tar(tar, extract_to)
    finally:
        # Always clean up the temporary file
        if temp_path.exists():
            temp_path.unlink()


def extract_archive(archive_path: Path, extract_to: Path) -> Path:
    """Extract an archive file to a directory.

    Automatically detects compression format based on file extension.
    Supported formats: .tar.zst, .tar.gz, .tar, .zip

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
    if archive_path.suffix == ".zip":
        # .zip
        with zipfile.ZipFile(archive_path, "r") as zip_file:
            safe_extract_zip(zip_file, extract_to)
    elif archive_path.suffixes[-2:] == [".tar", ".zst"]:
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

    Checks for formats supported by extract_archive(): .tar.zst, .tar.gz, .tar, .zip

    Args:
        path: Path to check

    Returns:
        True if file is a supported archive format
    """
    # Check for .zip
    if path.suffix == ".zip":
        return True

    # Check for .tar.zst or .tar.gz
    if path.suffixes[-2:] in [[".tar", ".zst"], [".tar", ".gz"]]:
        return True

    # Check for plain .tar
    if path.suffix == ".tar":
        return True

    return False
