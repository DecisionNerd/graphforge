"""Base classes and data structures for dataset loading."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from graphforge import GraphForge


@dataclass
class DatasetInfo:
    """Metadata about a graph dataset.

    Attributes:
        name: Unique identifier for the dataset (e.g., "snap-ego-facebook")
        description: Human-readable description of the dataset
        source: Source repository (e.g., "snap", "neo4j", "ldbc", "networkrepository")
        url: URL to download the dataset
        nodes: Expected number of nodes
        edges: Expected number of edges
        labels: List of node labels in the dataset
        relationship_types: List of relationship types in the dataset
        size_mb: Download size in megabytes
        license: Dataset license (e.g., "CC BY 4.0", "Public Domain")
        category: Dataset category (e.g., "social", "citation", "infrastructure")
        loader_class: Name of the DatasetLoader class to use
    """

    name: str
    description: str
    source: str
    url: str
    nodes: int
    edges: int
    labels: list[str]
    relationship_types: list[str]
    size_mb: float
    license: str
    category: str
    loader_class: str


@dataclass
class Dataset:
    """A loaded graph dataset with its metadata.

    Attributes:
        info: Metadata about the dataset
        path: Local path to the downloaded dataset file(s)
    """

    info: DatasetInfo
    path: Path


class DatasetLoader(ABC):
    """Abstract base class for dataset loaders.

    Each data source (SNAP, Neo4j, LDBC, etc.) implements its own loader
    that knows how to parse and load datasets in that source's specific format.
    """

    @abstractmethod
    def load(self, gf: "GraphForge", path: Path) -> None:
        """Load a dataset from a local file path into a GraphForge instance.

        Args:
            gf: The GraphForge instance to load data into
            path: Local path to the dataset file or directory

        Raises:
            ValueError: If the dataset format is invalid
            FileNotFoundError: If the dataset file doesn't exist
        """
        pass

    @abstractmethod
    def get_format(self) -> str:
        """Return the format name this loader handles.

        Returns:
            Format identifier (e.g., "csv", "cypher", "graphml", "ldbc")
        """
        pass
