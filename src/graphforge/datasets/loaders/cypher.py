"""Cypher script loader for Neo4j dataset files.

Loads .cypher and .cql script files, commonly used for Neo4j example datasets.
"""

import logging
from pathlib import Path
from typing import ClassVar

from graphforge.api import GraphForge
from graphforge.datasets.base import DatasetLoader

logger = logging.getLogger(__name__)


class CypherLoader(DatasetLoader):
    """Loader for Cypher script files (.cypher, .cql).

    Parses and executes multi-statement Cypher scripts. Automatically skips
    unsupported statements like constraints and indexes which aren't needed
    for embedded database use.

    Examples:
        >>> loader = CypherLoader()
        >>> loader.load(graph_forge, Path("movies.cypher"))

    Supported Features:
        - Multi-statement scripts
        - CREATE, MERGE, MATCH, SET, etc.
        - Automatic skipping of:
            * CREATE CONSTRAINT / DROP CONSTRAINT
            * CREATE INDEX / DROP INDEX
            * CALL procedures

    Skipped Features:
        - Schema constraints (not needed for embedded use)
        - Indexes (automatic for small datasets)
        - Stored procedures (use Python API instead)
    """

    # Statement prefixes to skip (schema operations not needed for embedded DB)
    SKIP_PREFIXES: ClassVar[list[str]] = [
        "CREATE CONSTRAINT",
        "DROP CONSTRAINT",
        "CREATE INDEX",
        "DROP INDEX",
        "CALL",  # Stored procedures - use Python API instead
    ]

    def get_format(self) -> str:
        """Return the format name this loader handles.

        Returns:
            "cypher" format identifier
        """
        return "cypher"

    def load(self, gf: GraphForge, path: Path) -> None:
        """Load Cypher script file into GraphForge instance.

        Args:
            gf: GraphForge instance to load data into
            path: Path to .cypher or .cql file

        Raises:
            FileNotFoundError: If script file doesn't exist
            ValueError: If script contains syntax errors
        """
        if not path.exists():
            raise FileNotFoundError(f"Cypher script not found: {path}")

        logger.info(f"Loading Cypher script: {path}")

        # Read entire script
        script_content = path.read_text(encoding="utf-8")

        # Split into statements (simple semicolon split)
        # Note: This doesn't handle semicolons in strings perfectly,
        # but works for typical Neo4j example datasets
        statements = self._split_statements(script_content)

        executed_count = 0
        skipped_count = 0

        for raw_stmt in statements:
            stmt = raw_stmt.strip()

            # Skip empty statements
            if not stmt:
                continue

            # Skip comments-only statements
            if stmt.startswith("//"):
                continue

            # Check if statement should be skipped
            stmt_upper = stmt.upper()
            should_skip = any(stmt_upper.startswith(prefix) for prefix in self.SKIP_PREFIXES)

            if should_skip:
                skipped_count += 1
                # Log at DEBUG level for transparency
                logger.debug(f"Skipping unsupported statement: {stmt[:50]}...")
                continue

            # Execute the statement
            try:
                gf.execute(stmt)
                executed_count += 1
            except Exception as e:
                logger.error(f"Failed to execute statement: {stmt[:100]}")
                raise ValueError(f"Cypher execution error: {e}") from e

        logger.info(
            f"Loaded {path.name}: {executed_count} statements executed, {skipped_count} skipped"
        )

    def _split_statements(self, script: str) -> list[str]:
        """Split script into individual statements.

        Args:
            script: Full script content

        Returns:
            List of individual statement strings

        Note:
            This uses a simple semicolon split which doesn't handle
            semicolons inside strings perfectly, but works for typical
            Neo4j example datasets.
        """
        # Remove single-line comments
        lines = []
        for line in script.split("\n"):
            # Remove comment portion (but preserve // in URLs, etc.)
            # Simple heuristic: // followed by space is likely a comment
            cleaned_line = line
            if "//" in line:
                comment_idx = line.find("//")
                # Check if it's likely a comment (preceded by space or at start)
                if comment_idx == 0 or line[comment_idx - 1].isspace():
                    cleaned_line = line[:comment_idx]
            lines.append(cleaned_line)

        script_no_comments = "\n".join(lines)

        # Split on semicolons
        statements = script_no_comments.split(";")

        return [s.strip() for s in statements if s.strip()]
