"""Dataset source modules.

Each source module registers datasets from a specific public repository:
- snap: Stanford Network Analysis Project
- neo4j: Neo4j Graph Examples
- ldbc: Linked Data Benchmark Council
- networkrepository: NetworkRepository.com
"""

from graphforge.datasets.sources.neo4j_examples import register_neo4j_datasets
from graphforge.datasets.sources.snap import register_snap_datasets

# Register all dataset sources when this module is imported
register_snap_datasets()
register_neo4j_datasets()

__all__ = []
