"""Pydantic model serialization for GraphForge (Pydantic + JSON).

This module provides serialization/deserialization for Pydantic models
including AST nodes, operators, and dataset metadata.

IMPORTANT: This is System 2 - Metadata & Schema Storage
========================================================

Purpose: Serialize metadata, schemas, and definitions
Format: JSON (human-readable, validatable)
Storage: JSON files (*.json)

Use this for:
- Dataset metadata (DatasetInfo models)
- Schema definitions (ontology classes, constraints)
- Configuration files
- AST node caching (future)
- User-defined class schemas (future)

Do NOT use this for:
- Graph data (nodes, edges, properties - use serialization.py instead)
- Runtime graph operations (use serialization.py instead)
- Performance-critical paths (use serialization.py instead)

Key Features:
- Human-readable JSON format (can edit files)
- Pydantic validation (catches errors at load time)
- Git-friendly (versionable, diffable)
- Self-documenting (field names and descriptions)

Example - Dataset Metadata:
    >>> from graphforge.datasets.base import DatasetInfo
    >>> info = DatasetInfo(name="test", description="Test dataset", ...)
    >>> save_model_to_file(info, "datasets/test.json")
    >>> loaded = load_model_from_file(DatasetInfo, "datasets/test.json")

Example - Future Ontology Support:
    >>> # Define Person class schema (future)
    >>> schema = ClassSchema(name="Person", properties=[...])
    >>> save_model_to_file(schema, "ontologies/person.json")

See: src/graphforge/storage/serialization.py for System 1 (graph data)
See: CLAUDE.md "Two Serialization Systems" for detailed explanation
"""

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def serialize_model(model: BaseModel) -> dict[str, Any]:
    """Serialize a Pydantic model to a dictionary.

    Uses Pydantic's model_dump() method with mode='python' to ensure
    all types are JSON-serializable.

    Args:
        model: Pydantic BaseModel instance

    Returns:
        Dictionary representation of the model

    Examples:
        >>> from graphforge.datasets.base import DatasetInfo
        >>> info = DatasetInfo(
        ...     name="test-dataset",
        ...     description="Test dataset",
        ...     source="test",
        ...     url="https://example.com/data.csv",
        ...     nodes=100,
        ...     edges=200,
        ...     size_mb=1.5,
        ...     license="MIT",
        ...     category="test",
        ...     loader_class="csv"
        ... )
        >>> data = serialize_model(info)
        >>> data['name']
        'test-dataset'
    """
    return model.model_dump(mode="python")


def deserialize_model(model_class: type[T], data: dict[str, Any]) -> T:
    """Deserialize a dictionary to a Pydantic model.

    Uses Pydantic's model_validate() method which runs all validators
    and ensures the data matches the model schema.

    Args:
        model_class: Pydantic BaseModel class to deserialize to
        data: Dictionary representation of the model

    Returns:
        Model instance

    Raises:
        ValidationError: If data doesn't match model schema

    Examples:
        >>> from graphforge.datasets.base import DatasetInfo
        >>> data = {
        ...     "name": "test-dataset",
        ...     "description": "Test dataset",
        ...     "source": "test",
        ...     "url": "https://example.com/data.csv",
        ...     "nodes": 100,
        ...     "edges": 200,
        ...     "size_mb": 1.5,
        ...     "license": "MIT",
        ...     "category": "test",
        ...     "loader_class": "csv"
        ... }
        >>> info = deserialize_model(DatasetInfo, data)
        >>> info.name
        'test-dataset'
    """
    return model_class.model_validate(data)


def serialize_model_to_json(model: BaseModel, indent: int | None = 2) -> str:
    """Serialize a Pydantic model to JSON string.

    Args:
        model: Pydantic BaseModel instance
        indent: JSON indentation (None for compact, 2 for pretty)

    Returns:
        JSON string representation

    Examples:
        >>> from graphforge.datasets.base import DatasetInfo
        >>> info = DatasetInfo(
        ...     name="test",
        ...     description="Test",
        ...     source="test",
        ...     url="https://example.com/data.csv",
        ...     nodes=100,
        ...     edges=200,
        ...     size_mb=1.5,
        ...     license="MIT",
        ...     category="test",
        ...     loader_class="csv"
        ... )
        >>> json_str = serialize_model_to_json(info)
        >>> '"name": "test"' in json_str
        True
    """
    return model.model_dump_json(indent=indent)


def deserialize_model_from_json(model_class: type[T], json_str: str) -> T:
    """Deserialize a JSON string to a Pydantic model.

    Args:
        model_class: Pydantic BaseModel class to deserialize to
        json_str: JSON string representation

    Returns:
        Model instance

    Raises:
        ValidationError: If JSON doesn't match model schema

    Examples:
        >>> from graphforge.datasets.base import DatasetInfo
        >>> json_str = '''
        ... {
        ...     "name": "test",
        ...     "description": "Test",
        ...     "source": "test",
        ...     "url": "https://example.com/data.csv",
        ...     "nodes": 100,
        ...     "edges": 200,
        ...     "size_mb": 1.5,
        ...     "license": "MIT",
        ...     "category": "test",
        ...     "loader_class": "csv"
        ... }
        ... '''
        >>> info = deserialize_model_from_json(DatasetInfo, json_str)
        >>> info.name
        'test'
    """
    return model_class.model_validate_json(json_str)


def save_model_to_file(model: BaseModel, path: Path | str, indent: int | None = 2) -> None:
    """Save a Pydantic model to a JSON file.

    Args:
        model: Pydantic BaseModel instance
        path: File path to save to
        indent: JSON indentation (None for compact, 2 for pretty)

    Examples:
        >>> from graphforge.datasets.base import DatasetInfo
        >>> info = DatasetInfo(
        ...     name="test",
        ...     description="Test",
        ...     source="test",
        ...     url="https://example.com/data.csv",
        ...     nodes=100,
        ...     edges=200,
        ...     size_mb=1.5,
        ...     license="MIT",
        ...     category="test",
        ...     loader_class="csv"
        ... )
        >>> save_model_to_file(info, "/tmp/dataset.json")
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    json_str = serialize_model_to_json(model, indent=indent)
    path.write_text(json_str, encoding="utf-8")


def load_model_from_file(model_class: type[T], path: Path | str) -> T:
    """Load a Pydantic model from a JSON file.

    Args:
        model_class: Pydantic BaseModel class to deserialize to
        path: File path to load from

    Returns:
        Model instance

    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If file content doesn't match model schema

    Examples:
        >>> from graphforge.datasets.base import DatasetInfo
        >>> # Assuming dataset.json exists
        >>> info = load_model_from_file(DatasetInfo, "/tmp/dataset.json")
    """
    path = Path(path)
    json_str = path.read_text(encoding="utf-8")
    return deserialize_model_from_json(model_class, json_str)


def serialize_models_batch(models: list[BaseModel]) -> list[dict[str, Any]]:
    """Serialize a batch of Pydantic models to dictionaries.

    Useful for serializing lists of dataset metadata, AST nodes, etc.

    Args:
        models: List of Pydantic BaseModel instances

    Returns:
        List of dictionary representations

    Examples:
        >>> from graphforge.datasets.base import DatasetInfo
        >>> datasets = [
        ...     DatasetInfo(name="test1", description="Test 1", source="test",
        ...                 url="https://example.com/1.csv", nodes=100, edges=200,
        ...                 size_mb=1.5, license="MIT", category="test",
        ...                 loader_class="csv"),
        ...     DatasetInfo(name="test2", description="Test 2", source="test",
        ...                 url="https://example.com/2.csv", nodes=200, edges=400,
        ...                 size_mb=2.5, license="MIT", category="test",
        ...                 loader_class="csv")
        ... ]
        >>> data = serialize_models_batch(datasets)
        >>> len(data)
        2
    """
    return [serialize_model(model) for model in models]


def deserialize_models_batch(model_class: type[T], data_list: list[dict[str, Any]]) -> list[T]:
    """Deserialize a batch of dictionaries to Pydantic models.

    Args:
        model_class: Pydantic BaseModel class to deserialize to
        data_list: List of dictionary representations

    Returns:
        List of model instances

    Raises:
        ValidationError: If any dictionary doesn't match model schema

    Examples:
        >>> from graphforge.datasets.base import DatasetInfo
        >>> data_list = [
        ...     {"name": "test1", "description": "Test 1", "source": "test",
        ...      "url": "https://example.com/1.csv", "nodes": 100, "edges": 200,
        ...      "size_mb": 1.5, "license": "MIT", "category": "test",
        ...      "loader_class": "csv"},
        ...     {"name": "test2", "description": "Test 2", "source": "test",
        ...      "url": "https://example.com/2.csv", "nodes": 200, "edges": 400,
        ...      "size_mb": 2.5, "license": "MIT", "category": "test",
        ...      "loader_class": "csv"}
        ... ]
        >>> datasets = deserialize_models_batch(DatasetInfo, data_list)
        >>> len(datasets)
        2
    """
    return [deserialize_model(model_class, data) for data in data_list]


def save_models_batch_to_file(
    models: list[BaseModel], path: Path | str, indent: int | None = 2
) -> None:
    """Save a batch of Pydantic models to a JSON file.

    Args:
        models: List of Pydantic BaseModel instances
        path: File path to save to
        indent: JSON indentation (None for compact, 2 for pretty)

    Examples:
        >>> from graphforge.datasets.base import DatasetInfo
        >>> datasets = [
        ...     DatasetInfo(name="test1", description="Test 1", source="test",
        ...                 url="https://example.com/1.csv", nodes=100, edges=200,
        ...                 size_mb=1.5, license="MIT", category="test",
        ...                 loader_class="csv")
        ... ]
        >>> save_models_batch_to_file(datasets, "/tmp/datasets.json")
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = serialize_models_batch(models)
    json_str = json.dumps(data, indent=indent)
    path.write_text(json_str, encoding="utf-8")


def load_models_batch_from_file(model_class: type[T], path: Path | str) -> list[T]:
    """Load a batch of Pydantic models from a JSON file.

    Args:
        model_class: Pydantic BaseModel class to deserialize to
        path: File path to load from

    Returns:
        List of model instances

    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If file content doesn't match model schema

    Examples:
        >>> from graphforge.datasets.base import DatasetInfo
        >>> # Assuming datasets.json exists
        >>> datasets = load_models_batch_from_file(DatasetInfo, "/tmp/datasets.json")
    """
    path = Path(path)
    json_str = path.read_text(encoding="utf-8")
    data_list = json.loads(json_str)
    return deserialize_models_batch(model_class, data_list)
