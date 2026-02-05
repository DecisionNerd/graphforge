"""Base classes and data structures for dataset loading."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from graphforge import GraphForge


class DatasetInfo(BaseModel):
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

    name: str = Field(..., min_length=1, description="Unique dataset identifier")
    description: str = Field(..., min_length=1, description="Dataset description")
    source: str = Field(..., min_length=1, description="Source repository")
    url: str = Field(..., description="Download URL")
    nodes: int = Field(..., ge=0, description="Expected number of nodes")
    edges: int = Field(..., ge=0, description="Expected number of edges")
    labels: list[str] = Field(default_factory=list, description="Node labels")
    relationship_types: list[str] = Field(default_factory=list, description="Relationship types")
    size_mb: float = Field(..., gt=0, description="Download size in MB")
    license: str = Field(..., min_length=1, description="Dataset license")
    category: str = Field(..., min_length=1, description="Dataset category")
    loader_class: str = Field(..., min_length=1, description="Loader class name")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://", "ftp://")):
            raise ValueError(f"Invalid URL scheme: {v}")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate dataset name format."""
        if not v.replace("-", "").replace("_", "").replace(".", "").isalnum():
            raise ValueError(
                f"Dataset name must contain only alphanumeric, dash, underscore, "
                f"and dot characters: {v}"
            )
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        """Validate source is a non-empty lowercase string."""
        if not v.islower():
            raise ValueError(f"Source must be lowercase: {v}")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category is a non-empty lowercase string."""
        if not v.islower():
            raise ValueError(f"Category must be lowercase: {v}")
        return v

    model_config = {"frozen": True}  # Make instances immutable like dataclass(frozen=True)


class Dataset(BaseModel):
    """A loaded graph dataset with its metadata.

    Attributes:
        info: Metadata about the dataset
        path: Local path to the downloaded dataset file(s)
    """

    info: DatasetInfo
    path: Path

    @field_validator("path", mode="before")
    @classmethod
    def validate_path(cls, v: Any) -> Path:
        """Validate and convert path to Path object."""
        if not isinstance(v, Path):
            return Path(v)
        return v

    model_config = {"arbitrary_types_allowed": True}  # Allow Path type


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
