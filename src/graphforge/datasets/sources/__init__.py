"""Dataset source modules.

Each source module registers datasets from a specific public repository:
- snap: Stanford Network Analysis Project
- ldbc: Linked Data Benchmark Council
- json_graph: JSON Graph interchange format (loader only)
- graphml: GraphML interchange format (loader only)
- networkrepository: NetworkRepository.com (planned)
"""

from graphforge.datasets.sources.graphml import register_graphml_loader
from graphforge.datasets.sources.json_graph import register_json_graph_loader
from graphforge.datasets.sources.ldbc import register_ldbc_datasets
from graphforge.datasets.sources.snap import register_snap_datasets

# Register all dataset sources when this module is imported
register_snap_datasets()
register_ldbc_datasets()
register_json_graph_loader()
register_graphml_loader()

__all__ = []
