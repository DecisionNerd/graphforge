"""Statistics collection for cost-based query optimization.

This module provides the GraphStatistics model for tracking graph-wide statistics
used in cardinality estimation and join reordering optimization.
"""

import time

from pydantic import BaseModel, Field


class GraphStatistics(BaseModel):
    """Graph-wide statistics for cost estimation.

    Tracks node counts, edge counts, and relationship cardinalities to enable
    cost-based query optimization. Statistics are maintained eagerly during
    graph mutations and persisted with the database.

    Attributes:
        total_nodes: Total number of nodes in the graph
        total_edges: Total number of edges in the graph
        node_counts_by_label: Count of nodes for each label
        edge_counts_by_type: Count of edges for each relationship type
        avg_degree_by_type: Average outgoing degree per relationship type
        last_updated: Timestamp of last statistics update
    """

    total_nodes: int = Field(default=0, ge=0, description="Total number of nodes")
    total_edges: int = Field(default=0, ge=0, description="Total number of edges")
    node_counts_by_label: dict[str, int] = Field(
        default_factory=dict, description="Node count per label"
    )
    edge_counts_by_type: dict[str, int] = Field(
        default_factory=dict, description="Edge count per type"
    )
    avg_degree_by_type: dict[str, float] = Field(
        default_factory=dict, description="Average outgoing degree per edge type"
    )
    last_updated: float = Field(default_factory=time.time, description="Timestamp of last update")

    model_config = {"frozen": True}

    @classmethod
    def empty(cls) -> "GraphStatistics":
        """Create empty statistics for a new graph.

        Returns:
            GraphStatistics instance with all counts at zero
        """
        return cls(total_nodes=0, total_edges=0)
