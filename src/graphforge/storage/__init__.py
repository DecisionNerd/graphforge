"""Storage backends for GraphForge.

This module contains storage implementations:
- In-memory graph store
- (Future) Persistent storage backends
"""

from graphforge.storage.memory import Graph

__all__ = ["Graph"]
