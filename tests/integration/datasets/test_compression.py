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


class TestTarSecurityValidation:
    """Security tests for TAR archive extraction."""

    def test_reject_absolute_path_tar(self, tmp_path):
        """Test that absolute paths in TAR are rejected."""
        archive_path = tmp_path / "malicious.tar.gz"
        extract_to = tmp_path / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        # Create TAR and manually modify member to have absolute path
        with tarfile.open(archive_path, "w:gz") as tar:
            tarinfo = tar.gettarinfo(test_file, arcname="passwd")
            # Force absolute path (not normalized by tarfile)
            tarinfo.name = "/etc/passwd"
            with test_file.open("rb") as f:
                tar.addfile(tarinfo, f)

        # Extract should raise ValueError
        # (Can be caught by either absolute path check or path traversal check)
        with pytest.raises(
            ValueError, match="(Absolute path not allowed|Path traversal attempt detected)"
        ):
            extract_archive(archive_path, extract_to)

    def test_reject_parent_directory_reference_tar(self, tmp_path):
        """Test that parent directory references in TAR are rejected."""
        archive_path = tmp_path / "malicious.tar.gz"
        extract_to = tmp_path / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        # Create TAR with parent directory reference
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(test_file, arcname="../../etc/passwd")

        # Extract should raise ValueError
        # (Can be caught by either path traversal check or parent directory check)
        with pytest.raises(
            ValueError,
            match="(Parent directory reference not allowed|Path traversal attempt detected)",
        ):
            extract_archive(archive_path, extract_to)

    def test_tarfile_windows_path_normalization(self, tmp_path):
        """Document how tarfile handles Windows paths on different platforms.

        This diagnostic test helps understand platform-specific behavior.
        """
        import sys

        archive_path = tmp_path / "diagnostic.tar.gz"
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        # Create TAR with Windows-style path
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(test_file, arcname="\\Windows\\System32\\evil.dll")

        # Read back and document what tarfile stores
        with tarfile.open(archive_path, "r:gz") as tar:
            members = tar.getmembers()
            assert len(members) == 1
            member_name = members[0].name

            # Print for CI visibility
            print(f"\nPlatform: {sys.platform}")
            print(f"Stored member.name: {member_name!r}")
            print(f"Starts with backslash: {member_name.startswith(chr(92))}")

            # Document expected behavior
            # Note: This may differ between platforms

    def test_reject_backslash_absolute_path_tar(self, tmp_path):
        """Test that Windows-style absolute paths in TAR are rejected."""
        import logging

        # Enable logging for test diagnostics
        logging.basicConfig(level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s")

        archive_path = tmp_path / "malicious.tar.gz"
        extract_to = tmp_path / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        # Create TAR with Windows-style absolute path using TarInfo
        # This bypasses platform-specific path normalization
        with tarfile.open(archive_path, "w:gz") as tar:
            # Manually create TarInfo to force the exact name we want
            tarinfo = tar.gettarinfo(str(test_file))
            tarinfo.name = "\\Windows\\System32\\evil.dll"  # Force this exact name
            with open(test_file, "rb") as f:
                tar.addfile(tarinfo, f)

        # Verify what was stored
        with tarfile.open(archive_path, "r:gz") as tar:
            members = tar.getmembers()
            stored_name = members[0].name
            # Should be the exact name we set, regardless of platform
            assert stored_name == "\\Windows\\System32\\evil.dll", (
                f"Expected TAR to store exact name, got {stored_name!r}"
            )

        # Extract should raise ValueError
        with pytest.raises(ValueError, match="Absolute path not allowed"):
            extract_archive(archive_path, extract_to)

    def test_safe_tar_extracts_normally(self, tmp_path):
        """Test that safe TAR files extract without issues."""
        archive_path = tmp_path / "safe.tar.gz"
        extract_to = tmp_path / "extracted"

        # Create safe TAR
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        (test_dir / "safe_file.txt").write_text("safe content")
        (test_dir / "subdir").mkdir()
        (test_dir / "subdir" / "nested.txt").write_text("nested safe content")

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(test_dir / "safe_file.txt", arcname="safe_file.txt")
            tar.add(test_dir / "subdir" / "nested.txt", arcname="subdir/nested.txt")

        # Should extract without issues
        extract_archive(archive_path, extract_to)

        assert (extract_to / "safe_file.txt").exists()
        assert (extract_to / "subdir" / "nested.txt").exists()
        assert (extract_to / "safe_file.txt").read_text() == "safe content"


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


class TestTarZstExtraction:
    """Tests for .tar.zst archive extraction."""

    def test_extract_tar_zst_requires_zstandard(self, tmp_path):
        """Test that extracting .tar.zst without zstandard raises ImportError."""
        from graphforge.datasets.loaders import compression

        # Save original state
        original_available = compression.ZSTD_AVAILABLE

        try:
            # Simulate zstandard not available
            compression.ZSTD_AVAILABLE = False

            archive_path = tmp_path / "test.tar.zst"
            extract_to = tmp_path / "extracted"

            # Create a dummy file (doesn't matter, will fail before reading)
            archive_path.write_bytes(b"dummy")

            # Should raise ImportError
            with pytest.raises(ImportError, match="zstandard package required"):
                compression.extract_tar_zst(archive_path, extract_to)

        finally:
            # Restore original state
            compression.ZSTD_AVAILABLE = original_available

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("zstandard"),
        reason="zstandard not available",
    )
    def test_extract_tar_zst_nonexistent(self, tmp_path):
        """Test that extracting nonexistent .tar.zst raises FileNotFoundError."""
        from graphforge.datasets.loaders.compression import extract_tar_zst

        archive_path = tmp_path / "nonexistent.tar.zst"
        extract_to = tmp_path / "extracted"

        with pytest.raises(FileNotFoundError, match="Archive not found"):
            extract_tar_zst(archive_path, extract_to)

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("zstandard"),
        reason="zstandard not available",
    )
    def test_extract_tar_zst_with_zstandard(self, tmp_path):
        """Test extracting .tar.zst archive when zstandard is available."""
        import io

        import zstandard as zstd

        # Create a test .tar.zst archive
        archive_path = tmp_path / "test.tar.zst"
        extract_to = tmp_path / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("zst content")

        # Create tar archive in memory
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            tar.add(test_file, arcname="test.txt")

        # Compress with zstd
        tar_buffer.seek(0)
        cctx = zstd.ZstdCompressor()
        compressed = cctx.compress(tar_buffer.read())

        # Write compressed data to file
        archive_path.write_bytes(compressed)

        # Extract using extract_archive (which will call extract_tar_zst)
        from graphforge.datasets.loaders.compression import extract_archive

        result = extract_archive(archive_path, extract_to)

        assert result == extract_to
        assert (extract_to / "test.txt").exists()
        assert (extract_to / "test.txt").read_text() == "zst content"

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("zstandard"),
        reason="zstandard not available",
    )
    def test_extract_tar_zst_security(self, tmp_path):
        """Test that .tar.zst extraction validates paths."""
        import io

        import zstandard as zstd

        archive_path = tmp_path / "malicious.tar.zst"
        extract_to = tmp_path / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        # Create tar with absolute path (force absolute path in tarinfo)
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            tarinfo = tar.gettarinfo(str(test_file), arcname="passwd")
            # Force absolute path (not normalized by tarfile)
            tarinfo.name = "/etc/passwd"
            with test_file.open("rb") as f:
                tar.addfile(tarinfo, f)

        # Compress with zstd
        tar_buffer.seek(0)
        cctx = zstd.ZstdCompressor()
        compressed = cctx.compress(tar_buffer.read())
        archive_path.write_bytes(compressed)

        # Should reject absolute path
        from graphforge.datasets.loaders.compression import extract_archive

        with pytest.raises(
            ValueError, match="(Absolute path not allowed|Path traversal attempt detected)"
        ):
            extract_archive(archive_path, extract_to)


class TestDriveLetterAbsolutePaths:
    r"""Tests for Windows drive-letter absolute paths (C:\, D:/, etc.)."""

    def test_reject_drive_letter_colon_backslash_tar(self, tmp_path):
        """Test that C:\\ style paths are rejected in TAR."""
        archive_path = tmp_path / "drive_letter.tar.gz"
        extract_to = tmp_path / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        # Create TAR with drive letter absolute path
        with tarfile.open(archive_path, "w:gz") as tar:
            tarinfo = tar.gettarinfo(str(test_file))
            tarinfo.name = "C:\\Windows\\System32\\evil.dll"
            with open(test_file, "rb") as f:
                tar.addfile(tarinfo, f)

        # Should reject drive letter path
        from graphforge.datasets.loaders.compression import extract_archive

        with pytest.raises(ValueError, match="Absolute path not allowed"):
            extract_archive(archive_path, extract_to)

    def test_reject_drive_letter_colon_forward_slash_tar(self, tmp_path):
        """Test that C:/ style paths are rejected in TAR."""
        archive_path = tmp_path / "drive_fwd.tar.gz"
        extract_to = tmp_path / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        # Create TAR with drive letter (forward slash variant)
        with tarfile.open(archive_path, "w:gz") as tar:
            tarinfo = tar.gettarinfo(str(test_file))
            tarinfo.name = "D:/Program Files/malware.exe"
            with open(test_file, "rb") as f:
                tar.addfile(tarinfo, f)

        # Should reject drive letter path
        from graphforge.datasets.loaders.compression import extract_archive

        with pytest.raises(ValueError, match="Absolute path not allowed"):
            extract_archive(archive_path, extract_to)

    def test_reject_drive_letter_zip(self, tmp_path):
        """Test that drive letter paths are rejected in ZIP."""
        archive_path = tmp_path / "drive.zip"
        extract_to = tmp_path / "extracted"

        # Create ZIP with drive letter path
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("E:\\System\\config.sys", "malicious")

        # Should reject drive letter path
        from graphforge.datasets.loaders.compression import extract_archive

        with pytest.raises(ValueError, match="Absolute path not allowed"):
            extract_archive(archive_path, extract_to)


class TestPathValidationEdgeCases:
    """Edge case tests for path validation during extraction."""

    def test_path_exactly_at_extraction_root_tar(self, tmp_path):
        """Test that files at extraction root are allowed (edge case for path check)."""
        archive_path = tmp_path / "root_file.tar.gz"
        extract_to = tmp_path / "extracted"
        extract_to.mkdir()

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        # Create TAR with file at root level
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(test_file, arcname="root_file.txt")

        # Should extract without issues
        from graphforge.datasets.loaders.compression import extract_archive

        extract_archive(archive_path, extract_to)
        assert (extract_to / "root_file.txt").exists()

    def test_path_exactly_at_extraction_root_zip(self, tmp_path):
        """Test that files at extraction root are allowed in ZIP (edge case for path check)."""
        archive_path = tmp_path / "root_file.zip"
        extract_to = tmp_path / "extracted"
        extract_to.mkdir()

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        # Create ZIP with file at root level
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.write(test_file, arcname="root_file.txt")

        # Should extract without issues
        from graphforge.datasets.loaders.compression import extract_archive

        extract_archive(archive_path, extract_to)
        assert (extract_to / "root_file.txt").exists()

    def test_deeply_nested_path_tar(self, tmp_path):
        """Test extraction of deeply nested paths in TAR."""
        archive_path = tmp_path / "nested.tar.gz"
        extract_to = tmp_path / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("nested content")

        # Create TAR with deeply nested path
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(test_file, arcname="a/b/c/d/e/f/nested.txt")

        # Should extract without issues
        from graphforge.datasets.loaders.compression import extract_archive

        extract_archive(archive_path, extract_to)
        assert (extract_to / "a/b/c/d/e/f/nested.txt").exists()
        assert (extract_to / "a/b/c/d/e/f/nested.txt").read_text() == "nested content"

    def test_mixed_safe_and_parent_refs_rejected_zip(self, tmp_path):
        """Test that even one parent ref in a path causes rejection in ZIP."""
        archive_path = tmp_path / "mixed.zip"
        extract_to = tmp_path / "extracted"

        # Create ZIP with path containing parent reference
        with zipfile.ZipFile(archive_path, "w") as zf:
            # Mix of safe dirs and parent ref
            zf.writestr("safe/subdir/../../../etc/passwd", "malicious")

        # Should reject due to parent reference
        from graphforge.datasets.loaders.compression import extract_archive

        with pytest.raises(
            ValueError,
            match="(Parent directory reference not allowed|Path traversal attempt detected)",
        ):
            extract_archive(archive_path, extract_to)

    def test_tar_with_many_parent_refs(self, tmp_path):
        """Test rejection of path with multiple parent refs in TAR."""
        archive_path = tmp_path / "many_parents.tar.gz"
        extract_to = tmp_path / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        # Create TAR with multiple parent refs
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(test_file, arcname="../../../../../../etc/passwd")

        # Should reject due to parent directory reference
        from graphforge.datasets.loaders.compression import extract_archive

        with pytest.raises(
            ValueError,
            match="(Parent directory reference not allowed|Path traversal attempt detected)",
        ):
            extract_archive(archive_path, extract_to)

    def test_zip_with_many_parent_refs(self, tmp_path):
        """Test rejection of path with multiple parent refs in ZIP."""
        archive_path = tmp_path / "many_parents.zip"
        extract_to = tmp_path / "extracted"

        # Create ZIP with multiple parent refs
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("../../../../../../etc/passwd", "malicious")

        # Should reject due to parent directory reference
        from graphforge.datasets.loaders.compression import extract_archive

        with pytest.raises(
            ValueError,
            match="(Parent directory reference not allowed|Path traversal attempt detected)",
        ):
            extract_archive(archive_path, extract_to)


class TestPostNormalizationAbsolutePath:
    """Tests for post-normalization absolute path detection."""

    def test_reject_absolute_after_normalization_tar(self, tmp_path):
        """Test that paths becoming absolute after normalization are rejected."""
        archive_path = tmp_path / "normalized_abs.tar.gz"
        extract_to = tmp_path / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        # Create TAR with backslash at start that normalizes to forward slash
        with tarfile.open(archive_path, "w:gz") as tar:
            tarinfo = tar.gettarinfo(str(test_file))
            # After normalization (\\ -> /), this becomes /etc/passwd
            tarinfo.name = "\\etc\\passwd"  # Will normalize to /etc/passwd
            with open(test_file, "rb") as f:
                tar.addfile(tarinfo, f)

        # Should reject after normalization
        from graphforge.datasets.loaders.compression import extract_archive

        with pytest.raises(ValueError, match="Absolute path not allowed"):
            extract_archive(archive_path, extract_to)


class TestTarBz2Extraction:
    """Tests for .tar.bz2 archive support (should fail as unsupported)."""

    def test_tar_bz2_format_not_supported(self, tmp_path):
        """Test that .tar.bz2 is rejected as unsupported format."""
        import bz2

        archive_path = tmp_path / "test.tar.bz2"
        extract_to = tmp_path / "extracted"

        # Create a valid .tar.bz2 file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("bz2 content")

        # Create tar in memory, then compress with bz2
        import io

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            tar.add(test_file, arcname="test.txt")

        tar_buffer.seek(0)
        compressed = bz2.compress(tar_buffer.read())
        archive_path.write_bytes(compressed)

        # Should raise ValueError for unsupported format
        from graphforge.datasets.loaders.compression import extract_archive

        with pytest.raises(ValueError, match="Unsupported archive format"):
            extract_archive(archive_path, extract_to)

    def test_tar_xz_format_not_supported(self, tmp_path):
        """Test that .tar.xz is rejected as unsupported format."""
        archive_path = tmp_path / "test.tar.xz"
        extract_to = tmp_path / "extracted"

        # Create a dummy file (doesn't need to be valid tar.xz)
        archive_path.write_bytes(b"dummy xz content")

        # Should raise ValueError for unsupported format
        from graphforge.datasets.loaders.compression import extract_archive

        with pytest.raises(ValueError, match="Unsupported archive format"):
            extract_archive(archive_path, extract_to)


class TestComplexTarZstScenarios:
    """Additional tests for .tar.zst when zstandard is available."""

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("zstandard"),
        reason="zstandard not available",
    )
    def test_extract_tar_zst_with_nested_directories(self, tmp_path):
        """Test extracting .tar.zst with nested directory structure."""
        import io

        import zstandard as zstd

        archive_path = tmp_path / "nested.tar.zst"
        extract_to = tmp_path / "extracted"

        # Create test files with nested structure
        test_dir = tmp_path / "test_data"
        (test_dir / "a" / "b" / "c").mkdir(parents=True)
        (test_dir / "a" / "file1.txt").write_text("content1")
        (test_dir / "a" / "b" / "file2.txt").write_text("content2")
        (test_dir / "a" / "b" / "c" / "file3.txt").write_text("content3")

        # Create tar with nested structure
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            tar.add(test_dir / "a" / "file1.txt", arcname="a/file1.txt")
            tar.add(test_dir / "a" / "b" / "file2.txt", arcname="a/b/file2.txt")
            tar.add(test_dir / "a" / "b" / "c" / "file3.txt", arcname="a/b/c/file3.txt")

        # Compress with zstd
        tar_buffer.seek(0)
        cctx = zstd.ZstdCompressor()
        compressed = cctx.compress(tar_buffer.read())
        archive_path.write_bytes(compressed)

        # Extract
        from graphforge.datasets.loaders.compression import extract_archive

        result = extract_archive(archive_path, extract_to)

        # Verify nested structure
        assert result == extract_to
        assert (extract_to / "a" / "file1.txt").exists()
        assert (extract_to / "a" / "b" / "file2.txt").exists()
        assert (extract_to / "a" / "b" / "c" / "file3.txt").exists()
        assert (extract_to / "a" / "file1.txt").read_text() == "content1"
        assert (extract_to / "a" / "b" / "file2.txt").read_text() == "content2"
        assert (extract_to / "a" / "b" / "c" / "file3.txt").read_text() == "content3"

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("zstandard"),
        reason="zstandard not available",
    )
    def test_extract_tar_zst_creates_directory(self, tmp_path):
        """Test that .tar.zst extraction creates output directory."""
        import io

        import zstandard as zstd

        archive_path = tmp_path / "test.tar.zst"
        extract_to = tmp_path / "new_dir" / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        # Create tar.zst
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            tar.add(test_file, arcname="test.txt")

        tar_buffer.seek(0)
        cctx = zstd.ZstdCompressor()
        compressed = cctx.compress(tar_buffer.read())
        archive_path.write_bytes(compressed)

        # Extract (should create new_dir/extracted)
        from graphforge.datasets.loaders.compression import extract_tar_zst

        extract_tar_zst(archive_path, extract_to)

        assert extract_to.exists()
        assert (extract_to / "test.txt").exists()
        assert (extract_to / "test.txt").read_text() == "content"

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("zstandard"),
        reason="zstandard not available",
    )
    def test_extract_tar_zst_multiple_files(self, tmp_path):
        """Test extracting .tar.zst with multiple files."""
        import io

        import zstandard as zstd

        archive_path = tmp_path / "multi.tar.zst"
        extract_to = tmp_path / "extracted"

        # Create multiple test files
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        for i in range(10):
            (test_dir / f"file{i}.txt").write_text(f"content{i}")

        # Create tar with multiple files
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            for i in range(10):
                tar.add(test_dir / f"file{i}.txt", arcname=f"file{i}.txt")

        # Compress with zstd
        tar_buffer.seek(0)
        cctx = zstd.ZstdCompressor()
        compressed = cctx.compress(tar_buffer.read())
        archive_path.write_bytes(compressed)

        # Extract
        from graphforge.datasets.loaders.compression import extract_archive

        extract_archive(archive_path, extract_to)

        # Verify all files
        for i in range(10):
            assert (extract_to / f"file{i}.txt").exists()
            assert (extract_to / f"file{i}.txt").read_text() == f"content{i}"

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("zstandard"),
        reason="zstandard not available",
    )
    def test_extract_tar_zst_with_parent_refs_rejected(self, tmp_path):
        """Test that .tar.zst with parent refs is rejected."""
        import io

        import zstandard as zstd

        archive_path = tmp_path / "malicious.tar.zst"
        extract_to = tmp_path / "extracted"

        # Create test file
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        test_file = test_dir / "test.txt"
        test_file.write_text("content")

        # Create tar with parent reference
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            tar.add(test_file, arcname="../../../etc/passwd")

        # Compress with zstd
        tar_buffer.seek(0)
        cctx = zstd.ZstdCompressor()
        compressed = cctx.compress(tar_buffer.read())
        archive_path.write_bytes(compressed)

        # Should reject parent reference
        from graphforge.datasets.loaders.compression import extract_archive

        with pytest.raises(
            ValueError,
            match="(Parent directory reference not allowed|Path traversal attempt detected)",
        ):
            extract_archive(archive_path, extract_to)
