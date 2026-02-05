"""Dataset source modules.

Each source module registers datasets from a specific public repository:
- snap: Stanford Network Analysis Project
- ldbc: Linked Data Benchmark Council
- networkrepository: NetworkRepository.com (planned)
"""

from graphforge.datasets.sources.ldbc import register_ldbc_datasets
from graphforge.datasets.sources.snap import register_snap_datasets

# Register all dataset sources when this module is imported
register_snap_datasets()
register_ldbc_datasets()

__all__ = []
