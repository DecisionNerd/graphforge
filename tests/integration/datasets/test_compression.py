"""Integration tests for compression utilities.

These tests perform actual file I/O operations and are therefore
classified as integration tests rather than unit tests.
"""

from pathlib import Path
import tarfile
import zipfile

import pytest

from graphforge.datasets.loaders.compression import (
    extract_archive,
    is_compressed_archive,
)

pytestmark = pytest.mark.integration


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

    def test_zip_detected(self):
        """Test .zip files are detected."""
        path = Path("file.zip")
        assert is_compressed_archive(path) is True

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
        # Create a plain file with unsupported extension
        archive_path = tmp_path / "test.rar"
        archive_path.write_text("not a supported archive")
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


class TestExtractZipArchive:
    """Tests for ZIP archive extraction."""

    def test_extract_zip(self, tmp_path):
        """Test extracting .zip archive."""
        # Create a test .zip archive
        archive_path = tmp_path / "test.zip"
        extract_to = tmp_path / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("zip content")

        # Create zip
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.write(test_file, arcname="test.txt")

        # Extract
        result = extract_archive(archive_path, extract_to)

        assert result == extract_to
        assert (extract_to / "test.txt").exists()
        assert (extract_to / "test.txt").read_text() == "zip content"

    def test_extract_zip_with_directory_structure(self, tmp_path):
        """Test extracting .zip archive with nested directories."""
        archive_path = tmp_path / "test.zip"
        extract_to = tmp_path / "extracted"

        # Create test files with directory structure
        test_dir = tmp_path / "test_data"
        (test_dir / "subdir").mkdir(parents=True)
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "subdir" / "file2.txt").write_text("content2")

        # Create zip
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.write(test_dir / "file1.txt", arcname="file1.txt")
            zf.write(test_dir / "subdir" / "file2.txt", arcname="subdir/file2.txt")

        # Extract
        result = extract_archive(archive_path, extract_to)

        assert result == extract_to
        assert (extract_to / "file1.txt").exists()
        assert (extract_to / "subdir" / "file2.txt").exists()
        assert (extract_to / "file1.txt").read_text() == "content1"
        assert (extract_to / "subdir" / "file2.txt").read_text() == "content2"

    def test_extract_zip_creates_directory(self, tmp_path):
        """Test ZIP extraction creates output directory if it doesn't exist."""
        archive_path = tmp_path / "test.zip"
        extract_to = tmp_path / "new_dir" / "extracted"

        # Create test archive
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.write(test_file, arcname="test.txt")

        # Extract to non-existent directory
        result = extract_archive(archive_path, extract_to)

        assert result == extract_to
        assert extract_to.exists()
        assert (extract_to / "test.txt").exists()

    def test_extract_zip_multiple_files(self, tmp_path):
        """Test extracting ZIP with multiple files."""
        archive_path = tmp_path / "test.zip"
        extract_to = tmp_path / "extracted"

        # Create multiple test files
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        for i in range(5):
            (test_dir / f"file{i}.txt").write_text(f"content{i}")

        # Create zip with multiple files
        with zipfile.ZipFile(archive_path, "w") as zf:
            for i in range(5):
                zf.write(test_dir / f"file{i}.txt", arcname=f"file{i}.txt")

        # Extract
        extract_archive(archive_path, extract_to)

        # Verify all files extracted
        for i in range(5):
            assert (extract_to / f"file{i}.txt").exists()
            assert (extract_to / f"file{i}.txt").read_text() == f"content{i}"


class TestZipSecurityValidation:
    """Security tests for ZIP archive extraction."""

    def test_reject_absolute_path(self, tmp_path):
        """Test that absolute paths in ZIP are rejected."""
        archive_path = tmp_path / "malicious.zip"
        extract_to = tmp_path / "extracted"

        # Create ZIP with absolute path
        with zipfile.ZipFile(archive_path, "w") as zf:
            # Add a file with absolute path
            zf.writestr("/etc/passwd", "malicious content")

        # Extract should raise ValueError (caught as path traversal or absolute path)
        with pytest.raises(
            ValueError, match="(Absolute path not allowed|Path traversal attempt detected)"
        ):
            extract_archive(archive_path, extract_to)

    def test_reject_parent_directory_reference(self, tmp_path):
        """Test that parent directory references in ZIP are rejected."""
        archive_path = tmp_path / "malicious.zip"
        extract_to = tmp_path / "extracted"

        # Create ZIP with parent directory reference
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("../../etc/passwd", "malicious content")

        # Extract should raise ValueError (caught as path traversal or parent reference)
        with pytest.raises(
            ValueError,
            match="(Parent directory reference not allowed|Path traversal attempt detected)",
        ):
            extract_archive(archive_path, extract_to)

    def test_reject_path_traversal(self, tmp_path):
        """Test that path traversal attempts in ZIP are rejected."""
        archive_path = tmp_path / "malicious.zip"
        extract_to = tmp_path / "safe_dir" / "extracted"
        extract_to.mkdir(parents=True)

        # Create a file outside the extraction directory
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("should not be created")

        # Create ZIP with path that would escape
        with zipfile.ZipFile(archive_path, "w") as zf:
            # This would try to write to tmp_path/outside.txt
            zf.writestr("../outside.txt", "malicious")

        # Extract should raise ValueError (caught as path traversal or parent reference)
        with pytest.raises(
            ValueError,
            match="(Parent directory reference not allowed|Path traversal attempt detected)",
        ):
            extract_archive(archive_path, extract_to)

    def test_backslash_path_safely_handled(self, tmp_path):
        """Test that paths with backslashes are safely handled.

        On Windows, paths like C:\\Windows\\... would be absolute and rejected.
        On Unix, they're treated as filenames with backslashes, which is safe.
        """
        archive_path = tmp_path / "safe_backslash.zip"
        extract_to = tmp_path / "extracted"

        # Create ZIP with backslash in name (Unix treats this as a regular character)
        with zipfile.ZipFile(archive_path, "w") as zf:
            # On Unix, this is just a filename with backslash characters
            zf.writestr("file\\with\\backslashes.txt", "content")

        # Should extract without issues on Unix (backslash is just a character)
        # Would need OS-specific handling if Windows support is critical
        extract_archive(archive_path, extract_to)

        # Verify extraction worked (file exists with backslashes in name on Unix)
        extracted_files = list(extract_to.rglob("*"))
        assert len(extracted_files) > 0

    def test_safe_zip_extracts_normally(self, tmp_path):
        """Test that safe ZIP files extract without issues."""
        archive_path = tmp_path / "safe.zip"
        extract_to = tmp_path / "extracted"

        # Create safe ZIP
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        (test_dir / "safe_file.txt").write_text("safe content")
        (test_dir / "subdir").mkdir()
        (test_dir / "subdir" / "nested.txt").write_text("nested safe content")

        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.write(test_dir / "safe_file.txt", arcname="safe_file.txt")
            zf.write(test_dir / "subdir" / "nested.txt", arcname="subdir/nested.txt")

        # Should extract without issues
        extract_archive(archive_path, extract_to)

        assert (extract_to / "safe_file.txt").exists()
        assert (extract_to / "subdir" / "nested.txt").exists()
        assert (extract_to / "safe_file.txt").read_text() == "safe content"
