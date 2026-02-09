"""CSV loader for edge-list datasets (e.g., SNAP datasets)."""

import gzip
from pathlib import Path
from typing import TYPE_CHECKING
import zipfile

from graphforge.datasets.base import DatasetLoader

if TYPE_CHECKING:
    from graphforge import GraphForge


class CSVLoader(DatasetLoader):
    """Loader for CSV/TSV edge-list format datasets.

    Supports:
    - Tab-separated values (TSV)
    - Comma-separated values (CSV)
    - Space-delimited files
    - Gzip-compressed files (.gz)
    - Zip-compressed files (.zip)
    - Comment lines (starting with #)
    - Weighted and unweighted edges
    - Auto-delimiter detection

    Expected format:
        # Comment lines (optional)
        source_id target_id [weight]

    Examples:
        # SNAP ego-Facebook network
        0 1
        0 2
        0 3

        # Weighted network
        0 1 0.5
        1 2 0.8
    """

    def load(self, gf: "GraphForge", path: Path) -> None:
        """Load CSV edge list into GraphForge.

        Args:
            gf: GraphForge instance to load data into
            path: Path to CSV file (may be gzipped or zipped)

        Raises:
            ValueError: If file format is invalid
            FileNotFoundError: If file doesn't exist
        """
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        # Open file (handle compression if needed)
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as f:
                self._load_edges(gf, f)
        elif path.suffix == ".zip":
            # Extract and load first CSV/TXT file from zip
            with zipfile.ZipFile(path) as zf:
                # Find first CSV, TXT, or MTX file in the archive
                csv_files = [
                    name
                    for name in zf.namelist()
                    if name.endswith((".csv", ".txt", ".tsv", ".mtx")) and not name.startswith("__")
                ]
                if not csv_files:
                    raise ValueError(f"No CSV/TXT/MTX files found in zip archive: {path}")

                # Load the first CSV file found
                with zf.open(csv_files[0], "r") as raw_f:
                    # Wrap in TextIOWrapper for text mode
                    import io

                    with io.TextIOWrapper(raw_f, encoding="utf-8") as f:
                        self._load_edges(gf, f)
        else:
            with path.open(encoding="utf-8") as f:
                self._load_edges(gf, f)

    def _load_edges(self, gf: "GraphForge", file) -> None:
        """Load edges from file handle.

        Args:
            gf: GraphForge instance
            file: File handle to read from
        """
        node_cache = {}  # Cache node IDs to avoid duplicate creates
        delimiter = None  # Auto-detect delimiter
        skip_next_line = False  # Flag to skip MTX dimension line

        for line_num, line in enumerate(file, start=1):
            stripped_line = line.strip()

            # Skip empty lines and comments (# for CSV/TXT, % for MTX format)
            if not stripped_line or stripped_line.startswith(("#", "%")):
                # If this is the last comment line in MTX, skip the next line (dimensions)
                if stripped_line.startswith("%"):
                    # Peek at next line to see if it's dimensions
                    skip_next_line = True
                continue

            # Skip MTX dimension line (comes right after comments)
            if skip_next_line:
                parts = stripped_line.split()
                # MTX dimension line has exactly 3 integers: rows cols entries
                if len(parts) == 3 and all(p.isdigit() for p in parts):
                    skip_next_line = False
                    continue
                skip_next_line = False

            # Auto-detect delimiter from first data line
            if delimiter is None:
                delimiter = self._detect_delimiter(stripped_line)

            # Parse line (handle consecutive spaces by using split() without argument)
            if delimiter == " ":
                parts = stripped_line.split()  # Collapses consecutive whitespace
            else:
                parts = stripped_line.split(delimiter)

            if len(parts) < 2:
                raise ValueError(
                    f"Invalid edge format at line {line_num}: "
                    f"expected at least 2 columns, got {len(parts)}"
                )

            # Extract source and target IDs
            try:
                source_id = parts[0].strip()
                target_id = parts[1].strip()
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid node ID at line {line_num}: {e}") from e

            # Extract optional weight
            weight = None
            if len(parts) >= 3:
                try:
                    weight = float(parts[2].strip())
                except ValueError as e:
                    raise ValueError(f"Invalid weight at line {line_num}: {e}") from e

            # Create or get source node
            if source_id not in node_cache:
                node_cache[source_id] = gf.create_node(["Node"], id=source_id)

            # Create or get target node
            if target_id not in node_cache:
                node_cache[target_id] = gf.create_node(["Node"], id=target_id)

            # Create edge
            edge_props = {}
            if weight is not None:
                edge_props["weight"] = weight

            gf.create_relationship(
                node_cache[source_id], node_cache[target_id], "CONNECTED_TO", **edge_props
            )

    def _detect_delimiter(self, line: str) -> str:
        """Detect the delimiter used in the CSV file.

        Args:
            line: First non-comment line of data

        Returns:
            Detected delimiter character

        Examples:
            >>> _detect_delimiter("0\t1\t2")
            '\t'
            >>> _detect_delimiter("0,1,2")
            ','
            >>> _detect_delimiter("0 1 2")
            ' '
        """
        # Check for tab (most common in SNAP datasets)
        if "\t" in line:
            return "\t"
        # Check for comma
        if "," in line:
            return ","
        # Default to space
        return " "

    def get_format(self) -> str:
        """Return the format name this loader handles.

        Returns:
            Format identifier
        """
        return "csv"
