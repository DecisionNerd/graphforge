"""Dataset loaders for various formats.

Implemented loaders:
- CSVLoader: Handles edge-list CSV/TSV files (SNAP datasets)
- CypherLoader: Handles .cypher script files (Neo4j examples)
- LDBCLoader: Handles LDBC multi-file CSV format
- JSONGraphLoader: Handles JSON Graph format with typed properties

Planned loaders:
- GraphMLLoader: Handles GraphML XML files (NetworkRepository)
"""

from graphforge.datasets.loaders.csv import CSVLoader
from graphforge.datasets.loaders.cypher import CypherLoader
from graphforge.datasets.loaders.json_graph import JSONGraphLoader
from graphforge.datasets.loaders.ldbc import LDBCLoader

__all__ = ["CSVLoader", "CypherLoader", "JSONGraphLoader", "LDBCLoader"]
