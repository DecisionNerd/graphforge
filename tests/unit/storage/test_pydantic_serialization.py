"""Unit tests for Pydantic model serialization."""

import json

from pydantic import ValidationError
import pytest

from graphforge.datasets.base import DatasetInfo
from graphforge.storage.pydantic_serialization import (
    deserialize_model,
    deserialize_model_from_json,
    deserialize_models_batch,
    load_model_from_file,
    load_models_batch_from_file,
    save_model_to_file,
    save_models_batch_to_file,
    serialize_model,
    serialize_model_to_json,
    serialize_models_batch,
)


@pytest.fixture
def sample_dataset_info():
    """Sample DatasetInfo for testing."""
    return DatasetInfo(
        name="test-dataset",
        description="Test dataset for serialization",
        source="test",
        url="https://example.com/data.csv",
        nodes=1000,
        edges=2000,
        size_mb=5.5,
        license="MIT",
        category="test",
        loader_class="csv",
    )


@pytest.fixture
def sample_dataset_info_2():
    """Second sample DatasetInfo for batch testing."""
    return DatasetInfo(
        name="test-dataset-2",
        description="Second test dataset",
        source="test",
        url="https://example.com/data2.csv",
        nodes=500,
        edges=1000,
        size_mb=2.5,
        license="Apache-2.0",
        category="test",
        loader_class="csv",
    )


class TestSerializeModel:
    """Tests for serialize_model function."""

    def test_serialize_dataset_info(self, sample_dataset_info):
        """Serialize DatasetInfo to dict."""
        data = serialize_model(sample_dataset_info)

        assert isinstance(data, dict)
        assert data["name"] == "test-dataset"
        assert data["description"] == "Test dataset for serialization"
        assert data["source"] == "test"
        assert data["url"] == "https://example.com/data.csv"
        assert data["nodes"] == 1000
        assert data["edges"] == 2000
        assert data["size_mb"] == 5.5
        assert data["license"] == "MIT"
        assert data["category"] == "test"
        assert data["loader_class"] == "csv"

    def test_serialize_preserves_all_fields(self, sample_dataset_info):
        """All model fields are preserved in serialization."""
        data = serialize_model(sample_dataset_info)

        # Should have exactly the fields defined in DatasetInfo
        expected_fields = {
            "name",
            "description",
            "source",
            "url",
            "nodes",
            "edges",
            "labels",
            "relationship_types",
            "size_mb",
            "license",
            "category",
            "loader_class",
        }
        assert set(data.keys()) == expected_fields


class TestDeserializeModel:
    """Tests for deserialize_model function."""

    def test_deserialize_dataset_info(self, sample_dataset_info):
        """Deserialize dict to DatasetInfo."""
        data = serialize_model(sample_dataset_info)
        restored = deserialize_model(DatasetInfo, data)

        assert restored.name == sample_dataset_info.name
        assert restored.description == sample_dataset_info.description
        assert restored.source == sample_dataset_info.source
        assert restored.url == sample_dataset_info.url
        assert restored.nodes == sample_dataset_info.nodes
        assert restored.edges == sample_dataset_info.edges
        assert restored.size_mb == sample_dataset_info.size_mb
        assert restored.license == sample_dataset_info.license
        assert restored.category == sample_dataset_info.category
        assert restored.loader_class == sample_dataset_info.loader_class

    def test_deserialize_validates_data(self):
        """Deserialization validates data against model schema."""
        invalid_data = {
            "name": "test",
            "description": "Test",
            "source": "test",
            "url": "invalid-url",  # Invalid URL scheme
            "nodes": 100,
            "edges": 200,
            "size_mb": 1.5,
            "license": "MIT",
            "category": "test",
            "loader_class": "csv",
        }

        with pytest.raises(ValidationError, match="Invalid URL scheme"):
            deserialize_model(DatasetInfo, invalid_data)

    def test_deserialize_missing_required_field(self):
        """Deserialization fails if required field is missing."""
        incomplete_data = {
            "name": "test",
            "description": "Test",
            # Missing 'source'
            "url": "https://example.com/data.csv",
            "nodes": 100,
            "edges": 200,
            "size_mb": 1.5,
            "license": "MIT",
            "category": "test",
            "loader_class": "csv",
        }

        with pytest.raises(ValidationError, match="Field required"):
            deserialize_model(DatasetInfo, incomplete_data)


class TestSerializeModelToJson:
    """Tests for serialize_model_to_json function."""

    def test_serialize_to_json_string(self, sample_dataset_info):
        """Serialize model to JSON string."""
        json_str = serialize_model_to_json(sample_dataset_info)

        assert isinstance(json_str, str)
        assert '"name": "test-dataset"' in json_str
        assert '"nodes": 1000' in json_str

    def test_serialize_to_json_pretty(self, sample_dataset_info):
        """Serialize with indentation for readability."""
        json_str = serialize_model_to_json(sample_dataset_info, indent=2)

        # Should have newlines (pretty-printed)
        assert "\n" in json_str

    def test_serialize_to_json_compact(self, sample_dataset_info):
        """Serialize without indentation for compactness."""
        json_str = serialize_model_to_json(sample_dataset_info, indent=None)

        # Should not have unnecessary whitespace
        assert "\n" not in json_str


class TestDeserializeModelFromJson:
    """Tests for deserialize_model_from_json function."""

    def test_deserialize_from_json_string(self, sample_dataset_info):
        """Deserialize model from JSON string."""
        json_str = serialize_model_to_json(sample_dataset_info)
        restored = deserialize_model_from_json(DatasetInfo, json_str)

        assert restored.name == sample_dataset_info.name
        assert restored.nodes == sample_dataset_info.nodes

    def test_deserialize_from_json_validates(self):
        """JSON deserialization validates data."""
        invalid_json = """
        {
            "name": "test",
            "description": "Test",
            "source": "UPPERCASE",
            "url": "https://example.com/data.csv",
            "nodes": 100,
            "edges": 200,
            "size_mb": 1.5,
            "license": "MIT",
            "category": "test",
            "loader_class": "csv"
        }
        """

        # Source must be lowercase
        with pytest.raises(ValidationError, match="Source must be lowercase"):
            deserialize_model_from_json(DatasetInfo, invalid_json)


class TestSaveLoadModelFile:
    """Tests for save_model_to_file and load_model_from_file functions."""

    def test_save_and_load_model(self, tmp_path, sample_dataset_info):
        """Save model to file and load it back."""
        file_path = tmp_path / "dataset.json"

        # Save
        save_model_to_file(sample_dataset_info, file_path)
        assert file_path.exists()

        # Load
        restored = load_model_from_file(DatasetInfo, file_path)
        assert restored.name == sample_dataset_info.name
        assert restored.nodes == sample_dataset_info.nodes

    def test_save_creates_parent_directories(self, tmp_path, sample_dataset_info):
        """Save creates parent directories if they don't exist."""
        file_path = tmp_path / "subdir" / "nested" / "dataset.json"

        save_model_to_file(sample_dataset_info, file_path)
        assert file_path.exists()

    def test_load_nonexistent_file_raises_error(self, tmp_path):
        """Loading nonexistent file raises FileNotFoundError."""
        file_path = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            load_model_from_file(DatasetInfo, file_path)

    def test_saved_file_is_valid_json(self, tmp_path, sample_dataset_info):
        """Saved file is valid JSON."""
        file_path = tmp_path / "dataset.json"

        save_model_to_file(sample_dataset_info, file_path)

        # Can parse as standard JSON
        with open(file_path) as f:
            data = json.load(f)

        assert data["name"] == "test-dataset"


class TestSerializeModelsBatch:
    """Tests for serialize_models_batch function."""

    def test_serialize_multiple_models(self, sample_dataset_info, sample_dataset_info_2):
        """Serialize list of models to list of dicts."""
        models = [sample_dataset_info, sample_dataset_info_2]
        data_list = serialize_models_batch(models)

        assert isinstance(data_list, list)
        assert len(data_list) == 2
        assert data_list[0]["name"] == "test-dataset"
        assert data_list[1]["name"] == "test-dataset-2"

    def test_serialize_empty_list(self):
        """Serialize empty list returns empty list."""
        data_list = serialize_models_batch([])
        assert data_list == []


class TestDeserializeModelsBatch:
    """Tests for deserialize_models_batch function."""

    def test_deserialize_multiple_models(self, sample_dataset_info, sample_dataset_info_2):
        """Deserialize list of dicts to list of models."""
        models = [sample_dataset_info, sample_dataset_info_2]
        data_list = serialize_models_batch(models)
        restored = deserialize_models_batch(DatasetInfo, data_list)

        assert len(restored) == 2
        assert restored[0].name == "test-dataset"
        assert restored[1].name == "test-dataset-2"

    def test_deserialize_empty_list(self):
        """Deserialize empty list returns empty list."""
        restored = deserialize_models_batch(DatasetInfo, [])
        assert restored == []

    def test_deserialize_validates_all_items(self):
        """Batch deserialization validates all items."""
        data_list = [
            {
                "name": "valid",
                "description": "Valid",
                "source": "test",
                "url": "https://example.com/valid.csv",
                "nodes": 100,
                "edges": 200,
                "size_mb": 1.5,
                "license": "MIT",
                "category": "test",
                "loader_class": "csv",
            },
            {
                "name": "invalid",
                "description": "Invalid",
                "source": "test",
                "url": "file:///etc/passwd",  # Invalid URL scheme
                "nodes": 100,
                "edges": 200,
                "size_mb": 1.5,
                "license": "MIT",
                "category": "test",
                "loader_class": "csv",
            },
        ]

        with pytest.raises(ValidationError, match="Invalid URL scheme"):
            deserialize_models_batch(DatasetInfo, data_list)


class TestSaveLoadModelsBatchFile:
    """Tests for batch file save/load functions."""

    def test_save_and_load_batch(self, tmp_path, sample_dataset_info, sample_dataset_info_2):
        """Save batch of models and load them back."""
        file_path = tmp_path / "datasets.json"
        models = [sample_dataset_info, sample_dataset_info_2]

        # Save
        save_models_batch_to_file(models, file_path)
        assert file_path.exists()

        # Load
        restored = load_models_batch_from_file(DatasetInfo, file_path)
        assert len(restored) == 2
        assert restored[0].name == "test-dataset"
        assert restored[1].name == "test-dataset-2"

    def test_saved_batch_is_valid_json(self, tmp_path, sample_dataset_info, sample_dataset_info_2):
        """Saved batch file is valid JSON array."""
        file_path = tmp_path / "datasets.json"
        models = [sample_dataset_info, sample_dataset_info_2]

        save_models_batch_to_file(models, file_path)

        # Can parse as standard JSON
        with open(file_path) as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 2

    def test_load_batch_nonexistent_file(self, tmp_path):
        """Loading nonexistent batch file raises FileNotFoundError."""
        file_path = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            load_models_batch_from_file(DatasetInfo, file_path)


class TestRoundTripSerialization:
    """Tests for round-trip serialization/deserialization."""

    def test_roundtrip_dict(self, sample_dataset_info):
        """Model -> dict -> model preserves data."""
        data = serialize_model(sample_dataset_info)
        restored = deserialize_model(DatasetInfo, data)

        # Compare all fields
        assert restored.model_dump() == sample_dataset_info.model_dump()

    def test_roundtrip_json(self, sample_dataset_info):
        """Model -> JSON -> model preserves data."""
        json_str = serialize_model_to_json(sample_dataset_info)
        restored = deserialize_model_from_json(DatasetInfo, json_str)

        assert restored.model_dump() == sample_dataset_info.model_dump()

    def test_roundtrip_file(self, tmp_path, sample_dataset_info):
        """Model -> file -> model preserves data."""
        file_path = tmp_path / "dataset.json"

        save_model_to_file(sample_dataset_info, file_path)
        restored = load_model_from_file(DatasetInfo, file_path)

        assert restored.model_dump() == sample_dataset_info.model_dump()

    def test_roundtrip_batch_file(self, tmp_path, sample_dataset_info, sample_dataset_info_2):
        """Batch -> file -> batch preserves data."""
        file_path = tmp_path / "datasets.json"
        models = [sample_dataset_info, sample_dataset_info_2]

        save_models_batch_to_file(models, file_path)
        restored = load_models_batch_from_file(DatasetInfo, file_path)

        assert len(restored) == len(models)
        for original, restored_model in zip(models, restored):
            assert restored_model.model_dump() == original.model_dump()


class TestWithLabelsAndRelationshipTypes:
    """Test serialization with optional list fields."""

    def test_serialize_with_labels(self):
        """Serialize DatasetInfo with labels."""
        info = DatasetInfo(
            name="test",
            description="Test",
            source="test",
            url="https://example.com/data.csv",
            nodes=100,
            edges=200,
            labels=["Person", "Post", "Comment"],
            relationship_types=["KNOWS", "LIKES"],
            size_mb=1.5,
            license="MIT",
            category="test",
            loader_class="csv",
        )

        data = serialize_model(info)
        assert data["labels"] == ["Person", "Post", "Comment"]
        assert data["relationship_types"] == ["KNOWS", "LIKES"]

    def test_roundtrip_with_labels(self):
        """Round-trip preserves labels and relationship types."""
        info = DatasetInfo(
            name="test",
            description="Test",
            source="test",
            url="https://example.com/data.csv",
            nodes=100,
            edges=200,
            labels=["Node"],
            relationship_types=["REL"],
            size_mb=1.5,
            license="MIT",
            category="test",
            loader_class="csv",
        )

        json_str = serialize_model_to_json(info)
        restored = deserialize_model_from_json(DatasetInfo, json_str)

        assert restored.labels == ["Node"]
        assert restored.relationship_types == ["REL"]
