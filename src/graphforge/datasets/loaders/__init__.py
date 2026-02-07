"""Dataset loaders for various formats.

Implemented loaders:
- CSVLoader: Handles edge-list CSV/TSV files (SNAP datasets)
- CypherLoader: Handles .cypher script files (Neo4j examples)
- GraphMLLoader: Handles GraphML XML files (NetworkRepository)
- JSONGraphLoader: Handles JSON Graph format with typed properties
- LDBCLoader: Handles LDBC multi-file CSV format
"""

from graphforge.datasets.loaders.csv import CSVLoader
from graphforge.datasets.loaders.cypher import CypherLoader
from graphforge.datasets.loaders.graphml import GraphMLLoader
from graphforge.datasets.loaders.json_graph import JSONGraphLoader
from graphforge.datasets.loaders.ldbc import LDBCLoader

__all__ = ["CSVLoader", "CypherLoader", "GraphMLLoader", "JSONGraphLoader", "LDBCLoader"]
