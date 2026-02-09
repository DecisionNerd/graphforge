"""NetworkRepository dataset registrations.

NetworkRepository (http://networkrepository.com/) provides a comprehensive
collection of network datasets covering social, biological, infrastructure,
communication, and other domains. Datasets are provided in GraphML format
with rich metadata and typed properties.

Source: https://networkrepository.com/
"""

import json
from pathlib import Path

from graphforge.datasets.base import DatasetInfo
from graphforge.datasets.registry import _DATASET_REGISTRY, register_dataset, register_loader


def _load_networkrepository_metadata() -> list[DatasetInfo]:
    """Load NetworkRepository dataset metadata from JSON file.

    Returns:
        List of DatasetInfo objects for all NetworkRepository datasets

    Raises:
        FileNotFoundError: If networkrepository.json is not found
        ValueError: If JSON is malformed
    """
    # Get path to networkrepository.json (relative to this file)
    data_dir = Path(__file__).parent.parent / "data"
    netrepo_json_path = data_dir / "networkrepository.json"

    if not netrepo_json_path.exists():
        raise FileNotFoundError(f"NetworkRepository metadata file not found: {netrepo_json_path}")

    with netrepo_json_path.open(encoding="utf-8") as f:
        data = json.load(f)

    # Extract source metadata
    source = data.get("source", "networkrepository")

    # Parse dataset entries
    datasets = []
    for entry in data.get("datasets", []):
        try:
            dataset = DatasetInfo(
                name=entry["name"],
                description=entry["description"],
                source=source,
                url=entry["url"],
                nodes=entry["nodes"],
                edges=entry["edges"],
                labels=entry["labels"],
                relationship_types=entry["relationship_types"],
                size_mb=entry["size_mb"],
                license=entry["license"],
                category=entry["category"],
                loader_class=entry["loader_class"],
            )
            datasets.append(dataset)
        except KeyError as e:  # noqa: PERF203
            raise ValueError(
                f"Missing required key {e} in dataset entry: {entry.get('name', '<unknown>')}"
            ) from e

    return datasets


def register_networkrepository_datasets() -> None:
    """Register all NetworkRepository datasets in the global registry."""
    # Register the CSV loader (idempotent - ignore if already registered)
    from graphforge.datasets.loaders.csv import CSVLoader

    try:
        register_loader("csv", CSVLoader)
    except ValueError as e:
        # Loader already registered - this is fine, continue with dataset registration
        if "already registered" not in str(e):
            # Re-raise if it's a different ValueError
            raise

    # Load NetworkRepository datasets from JSON
    datasets = _load_networkrepository_metadata()

    # Register all datasets, skipping duplicates
    for dataset in datasets:
        if dataset.name not in _DATASET_REGISTRY:
            register_dataset(dataset)
