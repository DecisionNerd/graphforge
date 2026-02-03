"""Dataset loaders for various formats.

Each loader knows how to parse and load datasets in a specific format:
- CSVLoader: Handles edge-list CSV/TSV files (SNAP datasets)
- CypherLoader: Handles .cypher script files (Neo4j examples)
- GraphMLLoader: Handles GraphML XML files (NetworkRepository)
- LDBCLoader: Handles LDBC multi-file CSV format
"""

__all__ = []
