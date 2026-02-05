"""LDBC dataset loader for multi-file CSV format.

Loads LDBC Social Network Benchmark (SNB) datasets from .tar.zst archives
containing multiple CSV files with nodes and relationships.
"""

import csv
from pathlib import Path
from typing import TYPE_CHECKING, Any

from graphforge.datasets.base import DatasetLoader
from graphforge.datasets.loaders.compression import extract_archive, is_compressed_archive
from graphforge.datasets.loaders.ldbc_schema import (
    NODE_SCHEMAS,
    RELATIONSHIP_SCHEMAS,
    PropertyMapping,
)

if TYPE_CHECKING:
    from graphforge import GraphForge


class LDBCLoader(DatasetLoader):
    """Loader for LDBC SNB datasets in multi-file CSV format.

    LDBC datasets come as .tar.zst archives containing multiple CSV files:
    - Node files: person_0_0.csv, post_0_0.csv, etc.
    - Relationship files: person_knows_person_0_0.csv, etc.

    Each CSV file has a header row with column names and uses pipe (|) as delimiter.

    Example:
        >>> loader = LDBCLoader()
        >>> gf = GraphForge()
        >>> loader.load(gf, Path("ldbc-snb-sf0.1.tar.zst"))
    """

    def __init__(self, delimiter: str = "|") -> None:
        """Initialize LDBC loader.

        Args:
            delimiter: CSV delimiter character (default: pipe '|')
        """
        self.delimiter = delimiter

    def load(self, gf: "GraphForge", path: Path) -> None:
        """Load LDBC dataset from archive or directory.

        Args:
            gf: GraphForge instance to load data into
            path: Path to .tar.zst archive or extracted directory

        Raises:
            ValueError: If dataset format is invalid
            FileNotFoundError: If dataset file doesn't exist
        """
        if not path.exists():
            raise FileNotFoundError(f"Dataset path not found: {path}")

        # Extract archive if needed
        if is_compressed_archive(path):
            # Extract to temporary directory
            extract_dir = path.parent / f".{path.stem}_extracted"
            extract_archive(path, extract_dir)
            data_dir = extract_dir
        elif path.is_dir():
            data_dir = path
        else:
            raise ValueError(f"Expected .tar.zst archive or directory, got: {path.suffix}")

        # Load nodes first (so relationships can reference them)
        node_cache = self._load_nodes(gf, data_dir)

        # Then load relationships
        self._load_relationships(gf, data_dir, node_cache)

    def _load_nodes(self, gf: "GraphForge", data_dir: Path) -> dict[tuple[str, str], Any]:
        """Load all node types from CSV files.

        Args:
            gf: GraphForge instance
            data_dir: Directory containing CSV files

        Returns:
            Dictionary mapping (label, id) -> NodeRef for relationship loading
        """
        node_cache: dict[tuple[str, str], Any] = {}

        for schema in NODE_SCHEMAS:
            csv_path = self._find_csv_file(data_dir, schema.csv_file)
            if csv_path is None:
                # Skip missing node types (some scale factors may omit certain types)
                continue

            with csv_path.open(encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)

                for row in reader:
                    # Extract node ID
                    node_id = row[schema.id_column]

                    # Parse properties
                    properties = self._parse_properties(row, schema.properties)

                    # Create node
                    node = gf.create_node([schema.label], **properties)

                    # Cache for relationship loading
                    node_cache[(schema.label, node_id)] = node

        return node_cache

    def _load_relationships(
        self,
        gf: "GraphForge",
        data_dir: Path,
        node_cache: dict[tuple[str, str], Any],
    ) -> None:
        """Load all relationship types from CSV files.

        Args:
            gf: GraphForge instance
            data_dir: Directory containing CSV files
            node_cache: Dictionary mapping (label, id) -> NodeRef
        """
        for schema in RELATIONSHIP_SCHEMAS:
            csv_path = self._find_csv_file(data_dir, schema.csv_file)
            if csv_path is None:
                # Skip missing relationship types
                continue

            with csv_path.open(encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)

                for row in reader:
                    # Get source and target node IDs
                    source_id = row[schema.source_id_column]
                    target_id = row[schema.target_id_column]

                    # Look up nodes in cache
                    source_key = (schema.source_label, source_id)
                    target_key = (schema.target_label, target_id)

                    if source_key not in node_cache or target_key not in node_cache:
                        # Skip relationships with missing nodes
                        continue

                    source_node = node_cache[source_key]
                    target_node = node_cache[target_key]

                    # Parse properties
                    properties = self._parse_properties(row, schema.properties)

                    # Create relationship
                    gf.create_relationship(
                        source_node,
                        target_node,
                        schema.type,
                        **properties,
                    )

    def _parse_properties(
        self,
        row: dict[str, str],
        mappings: list[PropertyMapping],
    ) -> dict[str, Any]:
        """Parse properties from CSV row according to schema.

        Args:
            row: CSV row as dictionary
            mappings: List of property mappings

        Returns:
            Dictionary of parsed properties
        """
        properties = {}

        for mapping in mappings:
            # Get raw value from CSV
            raw_value = row.get(mapping.csv_column, "")

            # Check for missing required properties
            if mapping.required and not raw_value:
                raise ValueError(
                    f"Required property '{mapping.property_name}' is missing "
                    f"from column '{mapping.csv_column}'"
                )

            # Skip empty values for optional properties
            if not mapping.required and not raw_value:
                continue

            # Convert to proper type
            try:
                converted_value = mapping.type_converter(raw_value)
                properties[mapping.property_name] = converted_value
            except (ValueError, TypeError) as e:
                if mapping.required:
                    raise ValueError(
                        f"Failed to parse required property '{mapping.property_name}' "
                        f"from column '{mapping.csv_column}': {e}"
                    ) from e
                # Skip optional properties that fail parsing
                continue

        return properties

    def _find_csv_file(self, data_dir: Path, filename: str) -> Path | None:
        """Find CSV file in data directory or subdirectories.

        LDBC datasets may have flat or nested directory structures.

        Args:
            data_dir: Root directory to search
            filename: CSV filename to find

        Returns:
            Path to CSV file, or None if not found
        """
        # Try direct path
        direct_path = data_dir / filename
        if direct_path.exists():
            return direct_path

        # Search subdirectories (one level deep)
        for subdir in data_dir.iterdir():
            if subdir.is_dir():
                csv_path = subdir / filename
                if csv_path.exists():
                    return csv_path

        return None

    def get_format(self) -> str:
        """Return the format name this loader handles.

        Returns:
            Format identifier
        """
        return "ldbc"
