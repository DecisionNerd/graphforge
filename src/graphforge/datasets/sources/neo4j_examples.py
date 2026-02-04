"""Neo4j Graph Examples dataset registrations.

Neo4j provides curated example datasets with realistic data models and queries,
commonly used for learning Cypher and demonstrating graph database concepts.

Source: https://github.com/neo4j-graph-examples
"""

import json
from pathlib import Path

from graphforge.datasets.base import DatasetInfo
from graphforge.datasets.registry import _DATASET_REGISTRY, register_dataset, register_loader


def register_neo4j_datasets() -> None:
    """Register Neo4j example datasets from JSON configuration file."""
    # Register the Cypher loader (idempotent - ignore if already registered)
    from graphforge.datasets.loaders.cypher import CypherLoader

    try:
        register_loader("cypher", CypherLoader)
    except ValueError as e:
        # Loader already registered - this is fine, continue with dataset registration
        if "already registered" not in str(e):
            # Re-raise if it's a different ValueError
            raise

    # Load datasets from JSON file
    json_path = Path(__file__).parent / "neo4j_datasets.json"
    with json_path.open(encoding="utf-8") as f:
        datasets_data = json.load(f)

    # Convert JSON data to DatasetInfo objects and register
    for dataset_dict in datasets_data:
        dataset = DatasetInfo(**dataset_dict)
        if dataset.name not in _DATASET_REGISTRY:
            register_dataset(dataset)
