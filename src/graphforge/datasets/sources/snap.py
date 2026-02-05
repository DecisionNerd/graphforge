"""SNAP (Stanford Network Analysis Project) dataset registrations.

SNAP provides a collection of large network datasets from real-world sources
including social networks, web graphs, collaboration networks, and more.

Source: https://snap.stanford.edu/data/
"""

import json
from pathlib import Path

from graphforge.datasets.base import DatasetInfo
from graphforge.datasets.registry import _DATASET_REGISTRY, register_dataset, register_loader


def _load_snap_metadata() -> list[DatasetInfo]:
    """Load SNAP dataset metadata from JSON file.

    Returns:
        List of DatasetInfo objects for all SNAP datasets

    Raises:
        FileNotFoundError: If snap.json is not found
        ValueError: If JSON is malformed
    """
    # Get path to snap.json (relative to this file)
    data_dir = Path(__file__).parent.parent / "data"
    snap_json_path = data_dir / "snap.json"

    if not snap_json_path.exists():
        raise FileNotFoundError(f"SNAP metadata file not found: {snap_json_path}")

    with snap_json_path.open(encoding="utf-8") as f:
        data = json.load(f)

    # Extract source metadata
    source = data.get("source", "snap")

    # Parse dataset entries
    datasets = []
    for entry in data.get("datasets", []):
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

    return datasets


def register_snap_datasets() -> None:
    """Register all SNAP datasets in the global registry."""
    # Register the CSV loader (idempotent - ignore if already registered)
    from graphforge.datasets.loaders.csv import CSVLoader

    try:
        register_loader("csv", CSVLoader)
    except ValueError as e:
        # Loader already registered - this is fine, continue with dataset registration
        if "already registered" not in str(e):
            # Re-raise if it's a different ValueError
            raise

    # Load SNAP datasets from JSON
    datasets = _load_snap_metadata()

    # Register all datasets, skipping duplicates
    for dataset in datasets:
        if dataset.name not in _DATASET_REGISTRY:
            register_dataset(dataset)
