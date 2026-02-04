"""Dataset loaders for various formats.

Implemented loaders:
- CSVLoader: Handles edge-list CSV/TSV files (SNAP datasets)
- CypherLoader: Handles .cypher script files (Neo4j examples)

Planned loaders:
- GraphMLLoader: Handles GraphML XML files (NetworkRepository)
- LDBCLoader: Handles LDBC multi-file CSV format
"""

from graphforge.datasets.loaders.csv import CSVLoader
from graphforge.datasets.loaders.cypher import CypherLoader

__all__ = ["CSVLoader", "CypherLoader"]
