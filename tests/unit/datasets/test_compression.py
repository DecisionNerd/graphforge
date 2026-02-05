"""Unit tests for compression utilities."""

from pathlib import Path
import tarfile

import pytest

from graphforge.datasets.loaders.compression import (
    extract_archive,
    is_compressed_archive,
)

pytestmark = pytest.mark.unit


class TestIsCompressedArchive:
    """Tests for archive format detection."""

    def test_tar_zst_detected(self):
        """Test .tar.zst files are detected."""
        path = Path("dataset.tar.zst")
        assert is_compressed_archive(path) is True

    def test_tar_gz_detected(self):
        """Test .tar.gz files are detected."""
        path = Path("dataset.tar.gz")
        assert is_compressed_archive(path) is True

    def test_tar_detected(self):
        """Test .tar files are detected."""
        path = Path("dataset.tar")
        assert is_compressed_archive(path) is True

    def test_gz_not_detected(self):
        """Test standalone .gz files are not detected."""
        path = Path("file.gz")
        assert is_compressed_archive(path) is False

    def test_zip_not_detected(self):
        """Test .zip files are not detected."""
        path = Path("file.zip")
        assert is_compressed_archive(path) is False

    def test_csv_not_detected(self):
        """Test .csv files are not detected."""
        path = Path("file.csv")
        assert is_compressed_archive(path) is False


class TestExtractArchive:
    """Tests for archive extraction."""

    def test_extract_tar_gz(self, tmp_path):
        """Test extracting .tar.gz archive."""
        # Create a test .tar.gz archive
        archive_path = tmp_path / "test.tar.gz"
        extract_to = tmp_path / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("test content")

        # Create tar.gz
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(test_file, arcname="test.txt")

        # Extract
        result = extract_archive(archive_path, extract_to)

        assert result == extract_to
        assert (extract_to / "test.txt").exists()
        assert (extract_to / "test.txt").read_text() == "test content"

    def test_extract_plain_tar(self, tmp_path):
        """Test extracting plain .tar archive."""
        # Create a test .tar archive
        archive_path = tmp_path / "test.tar"
        extract_to = tmp_path / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("plain tar content")

        # Create tar
        with tarfile.open(archive_path, "w") as tar:
            tar.add(test_file, arcname="test.txt")

        # Extract
        result = extract_archive(archive_path, extract_to)

        assert result == extract_to
        assert (extract_to / "test.txt").exists()
        assert (extract_to / "test.txt").read_text() == "plain tar content"

    def test_extract_nonexistent_archive(self, tmp_path):
        """Test extracting nonexistent archive raises error."""
        archive_path = tmp_path / "nonexistent.tar.gz"
        extract_to = tmp_path / "extracted"

        with pytest.raises(FileNotFoundError, match="Archive not found"):
            extract_archive(archive_path, extract_to)

    def test_extract_unsupported_format(self, tmp_path):
        """Test extracting unsupported format raises error."""
        # Create a plain file with .zip extension
        archive_path = tmp_path / "test.zip"
        archive_path.write_text("not a real zip")
        extract_to = tmp_path / "extracted"

        with pytest.raises(ValueError, match="Unsupported archive format"):
            extract_archive(archive_path, extract_to)

    def test_extract_creates_directory(self, tmp_path):
        """Test extraction creates output directory if it doesn't exist."""
        archive_path = tmp_path / "test.tar.gz"
        extract_to = tmp_path / "new_dir" / "extracted"

        # Create test archive
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(test_file, arcname="test.txt")

        # Extract to non-existent directory
        result = extract_archive(archive_path, extract_to)

        assert result == extract_to
        assert extract_to.exists()
        assert (extract_to / "test.txt").exists()
