"""Unit tests for NetworkRepository source module."""

import json
from pathlib import Path
import tempfile

import pytest

from graphforge.datasets.sources.networkrepository import (
    _load_networkrepository_metadata,
    register_networkrepository_datasets,
)


class TestNetworkRepositoryMetadataLoading:
    """Test NetworkRepository metadata loading functionality."""

    def test_load_metadata_missing_file_raises_error(self):
        """Test that loading from non-existent file raises FileNotFoundError."""
        # Temporarily move the JSON file to simulate missing file
        from graphforge.datasets.sources import networkrepository

        module_dir = Path(networkrepository.__file__).parent.parent
        json_path = module_dir / "data" / "networkrepository.json"
        temp_path = module_dir / "data" / "networkrepository.json.backup"

        if json_path.exists():
            json_path.rename(temp_path)

        try:
            with pytest.raises(
                FileNotFoundError, match="NetworkRepository metadata file not found"
            ):
                _load_networkrepository_metadata()
        finally:
            # Restore the file
            if temp_path.exists():
                temp_path.rename(json_path)

    def test_load_metadata_missing_required_key_raises_error(self):
        """Test that missing required keys in dataset entries raise ValueError."""
        # Create temporary JSON file with missing 'url' field
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump(
                {
                    "source": "test",
                    "datasets": [
                        {
                            "name": "test-dataset",
                            "description": "Test",
                            # Missing 'url' field
                            "nodes": 10,
                            "edges": 20,
                            "labels": ["Node"],
                            "relationship_types": ["CONNECTED"],
                            "size_mb": 0.1,
                            "license": "MIT",
                            "category": "test",
                            "loader_class": "csv",
                        }
                    ],
                },
                f,
            )
            temp_path = Path(f.name)

        try:
            # Monkey-patch the path to use our temp file
            from graphforge.datasets.sources import networkrepository

            original_file = networkrepository.__file__
            module_dir = Path(original_file).parent.parent
            json_path = module_dir / "data" / "networkrepository.json"

            # Back up original
            import shutil

            backup_path = module_dir / "data" / "networkrepository.json.test_backup"
            if json_path.exists():
                shutil.copy(json_path, backup_path)

            try:
                # Replace with our test file
                shutil.copy(temp_path, json_path)

                with pytest.raises(ValueError, match="Missing required key.*url"):
                    _load_networkrepository_metadata()
            finally:
                # Restore original
                if backup_path.exists():
                    shutil.copy(backup_path, json_path)
                    backup_path.unlink()
        finally:
            temp_path.unlink()


class TestNetworkRepositoryRegistration:
    """Test NetworkRepository dataset registration."""

    def test_register_datasets_idempotent(self):
        """Test that registering multiple times doesn't cause errors."""
        # This should not raise any errors
        register_networkrepository_datasets()
        register_networkrepository_datasets()
        register_networkrepository_datasets()

        # Verify datasets are still registered correctly
        from graphforge.datasets.registry import get_dataset_info

        info = get_dataset_info("netrepo-karate")
        assert info is not None
        assert info.name == "netrepo-karate"
