"""Dataset loading and management for GraphForge.

This module provides utilities for loading sample graph datasets from various
public repositories including SNAP, Neo4j Examples, LDBC, and NetworkRepository.

Examples:
    >>> from graphforge import GraphForge
    >>> from graphforge.datasets import load_dataset, list_datasets
    >>>
    >>> # List available datasets
    >>> datasets = list_datasets()
    >>> for ds in datasets:
    ...     print(f"{ds.name}: {ds.nodes} nodes, {ds.edges} edges")
    >>>
    >>> # Load a dataset
    >>> gf = GraphForge.from_dataset("snap-ego-facebook")
    >>>
    >>> # Or load into existing instance
    >>> gf = GraphForge()
    >>> load_dataset(gf, "snap-ego-facebook")
"""

from graphforge.datasets.base import Dataset, DatasetInfo, DatasetLoader
from graphforge.datasets.registry import (
    clear_cache,
    get_dataset_info,
    list_datasets,
    load_dataset,
    register_dataset,
)

__all__ = [
    # Base classes
    "Dataset",
    "DatasetInfo",
    "DatasetLoader",
    # Registry functions
    "clear_cache",
    "get_dataset_info",
    "list_datasets",
    "load_dataset",
    "register_dataset",
]
