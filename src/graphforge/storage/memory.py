"""In-memory graph store with adjacency lists.

This module provides an in-memory graph storage implementation using
adjacency lists for efficient traversal. This is the foundational storage
layer that will later be backed by persistent storage.

The Graph class stores:
- Nodes indexed by ID
- Edges indexed by ID
- Outgoing adjacency lists (node_id -> list of outgoing edges)
- Incoming adjacency lists (node_id -> list of incoming edges)
- Label index (label -> set of node IDs)
- Type index (edge_type -> set of edge IDs)
"""

from collections import defaultdict
import time

from graphforge.optimizer.statistics import GraphStatistics
from graphforge.types.graph import EdgeRef, NodeRef


class Graph:
    """In-memory graph store with adjacency list representation.

    The graph maintains several indexes for efficient queries:
    - Node storage: id -> NodeRef
    - Edge storage: id -> EdgeRef
    - Outgoing edges: node_id -> [EdgeRef]
    - Incoming edges: node_id -> [EdgeRef]
    - Label index: label -> {node_id}
    - Type index: edge_type -> {edge_id}

    Examples:
        >>> graph = Graph()
        >>> node = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        >>> graph.add_node(node)
        >>> graph.node_count()
        1
        >>> graph.get_node(1) == node
        True
    """

    def __init__(self):
        """Initialize an empty graph."""
        # Primary storage
        self._nodes: dict[int | str, NodeRef] = {}
        self._edges: dict[int | str, EdgeRef] = {}

        # Adjacency lists for traversal
        self._outgoing: dict[int | str, list[EdgeRef]] = defaultdict(list)
        self._incoming: dict[int | str, list[EdgeRef]] = defaultdict(list)

        # Indexes for efficient queries
        self._label_index: dict[str, set[int | str]] = defaultdict(set)
        self._type_index: dict[str, set[int | str]] = defaultdict(set)

        # Statistics for cost-based optimization
        self._statistics: GraphStatistics = GraphStatistics.empty()

    def add_node(self, node: NodeRef) -> None:
        """Add a node to the graph.

        Args:
            node: The node to add

        Note:
            If a node with this ID already exists, it will be replaced.
        """
        # Track if this is a new node (for statistics)
        is_new_node = node.id not in self._nodes

        # Remove old node from label index and statistics if it exists
        if not is_new_node:
            old_node = self._nodes[node.id]
            for label in old_node.labels:
                self._label_index[label].discard(node.id)
            # Decrement old node's label counts
            new_node_counts = dict(self._statistics.node_counts_by_label)
            for label in old_node.labels:
                count = new_node_counts.get(label, 0)
                if count > 0:
                    new_node_counts[label] = count - 1
                    if new_node_counts[label] == 0:
                        del new_node_counts[label]
            self._statistics = self._statistics.model_copy(
                update={
                    "node_counts_by_label": new_node_counts,
                    "last_updated": time.time(),
                }
            )

        # Store node
        self._nodes[node.id] = node

        # Update label index
        for label in node.labels:
            self._label_index[label].add(node.id)

        # Initialize adjacency lists if not present
        if node.id not in self._outgoing:
            self._outgoing[node.id] = []
        if node.id not in self._incoming:
            self._incoming[node.id] = []

        # Update statistics
        if is_new_node:
            self._update_statistics_after_add_node(node)
        else:
            # For replacement, just update label counts
            new_node_counts = dict(self._statistics.node_counts_by_label)
            for label in node.labels:
                new_node_counts[label] = new_node_counts.get(label, 0) + 1
            self._statistics = self._statistics.model_copy(
                update={
                    "node_counts_by_label": new_node_counts,
                    "last_updated": time.time(),
                }
            )

    def get_node(self, node_id: int | str) -> NodeRef | None:
        """Get a node by its ID.

        Args:
            node_id: The node ID to retrieve

        Returns:
            The NodeRef if found, None otherwise
        """
        return self._nodes.get(node_id)

    def has_node(self, node_id: int | str) -> bool:
        """Check if a node exists in the graph.

        Args:
            node_id: The node ID to check

        Returns:
            True if the node exists, False otherwise
        """
        return node_id in self._nodes

    def node_count(self) -> int:
        """Get the number of nodes in the graph.

        Returns:
            The number of nodes
        """
        return len(self._nodes)

    def get_all_nodes(self) -> list[NodeRef]:
        """Get all nodes in the graph.

        Returns:
            List of all nodes
        """
        return list(self._nodes.values())

    def get_nodes_by_label(self, label: str) -> list[NodeRef]:
        """Get all nodes with a specific label.

        Args:
            label: The label to filter by

        Returns:
            List of nodes with the specified label
        """
        node_ids = self._label_index.get(label, set())
        return [self._nodes[node_id] for node_id in node_ids]

    def get_statistics(self) -> GraphStatistics:
        """Get current graph statistics for cost-based optimization.

        Returns:
            GraphStatistics instance with current statistics
        """
        return self._statistics

    def _update_statistics_after_add_node(self, node: NodeRef) -> None:
        """Update statistics after adding a node.

        Args:
            node: The node that was added
        """
        # Update node counts by label
        new_node_counts = dict(self._statistics.node_counts_by_label)
        for label in node.labels:
            new_node_counts[label] = new_node_counts.get(label, 0) + 1

        # Create new statistics (immutable)
        self._statistics = self._statistics.model_copy(
            update={
                "total_nodes": self._statistics.total_nodes + 1,
                "node_counts_by_label": new_node_counts,
                "last_updated": time.time(),
            }
        )

    def _update_statistics_after_add_edge(self, edge: EdgeRef) -> None:
        """Update statistics after adding an edge.

        Args:
            edge: The edge that was added
        """
        # Update edge counts by type
        new_edge_counts = dict(self._statistics.edge_counts_by_type)
        new_edge_counts[edge.type] = new_edge_counts.get(edge.type, 0) + 1

        # Recompute average degree for this type
        # Average degree = count of edges / count of unique source nodes
        edge_ids_of_type = self._type_index.get(edge.type, set())
        unique_sources = len({self._edges[eid].src.id for eid in edge_ids_of_type})
        avg_degree = new_edge_counts[edge.type] / max(unique_sources, 1)

        new_avg_degrees = dict(self._statistics.avg_degree_by_type)
        new_avg_degrees[edge.type] = avg_degree

        # Create new statistics (immutable)
        self._statistics = self._statistics.model_copy(
            update={
                "total_edges": self._statistics.total_edges + 1,
                "edge_counts_by_type": new_edge_counts,
                "avg_degree_by_type": new_avg_degrees,
                "last_updated": time.time(),
            }
        )

    def add_edge(self, edge: EdgeRef) -> None:
        """Add an edge to the graph.

        Args:
            edge: The edge to add

        Raises:
            ValueError: If source or destination node doesn't exist

        Note:
            If an edge with this ID already exists, it will be replaced.
        """
        # Validate that nodes exist
        if edge.src.id not in self._nodes:
            raise ValueError(f"Source node {edge.src.id} not found in graph")
        if edge.dst.id not in self._nodes:
            raise ValueError(f"Destination node {edge.dst.id} not found in graph")

        # Track if this is a new edge (for statistics)
        is_new_edge = edge.id not in self._edges

        # Remove old edge from indexes and statistics if it exists
        if not is_new_edge:
            old_edge = self._edges[edge.id]
            self._outgoing[old_edge.src.id].remove(old_edge)
            self._incoming[old_edge.dst.id].remove(old_edge)
            self._type_index[old_edge.type].discard(edge.id)
            # Decrement old edge's type count
            new_edge_counts = dict(self._statistics.edge_counts_by_type)
            count = new_edge_counts.get(old_edge.type, 0)
            if count > 0:
                new_edge_counts[old_edge.type] = count - 1
                if new_edge_counts[old_edge.type] == 0:
                    del new_edge_counts[old_edge.type]
            # Recompute avg degree for old type
            edge_ids_of_old_type = self._type_index.get(old_edge.type, set()) - {edge.id}
            new_avg_degrees = dict(self._statistics.avg_degree_by_type)
            if edge_ids_of_old_type:
                unique_sources = len({self._edges[eid].src.id for eid in edge_ids_of_old_type})
                new_avg_degrees[old_edge.type] = len(edge_ids_of_old_type) / max(unique_sources, 1)
            elif old_edge.type in new_avg_degrees:
                del new_avg_degrees[old_edge.type]
            self._statistics = self._statistics.model_copy(
                update={
                    "edge_counts_by_type": new_edge_counts,
                    "avg_degree_by_type": new_avg_degrees,
                    "last_updated": time.time(),
                }
            )

        # Store edge
        self._edges[edge.id] = edge

        # Update adjacency lists
        self._outgoing[edge.src.id].append(edge)
        self._incoming[edge.dst.id].append(edge)

        # Update type index
        self._type_index[edge.type].add(edge.id)

        # Update statistics
        if is_new_edge:
            self._update_statistics_after_add_edge(edge)
        else:
            # For replacement, just update the new edge type counts (total_edges unchanged)
            new_edge_counts = dict(self._statistics.edge_counts_by_type)
            new_edge_counts[edge.type] = new_edge_counts.get(edge.type, 0) + 1

            # Recompute avg degree for new type
            edge_ids_of_type = self._type_index.get(edge.type, set())
            unique_sources = len({self._edges[eid].src.id for eid in edge_ids_of_type})
            avg_degree = new_edge_counts[edge.type] / max(unique_sources, 1)

            new_avg_degrees = dict(self._statistics.avg_degree_by_type)
            new_avg_degrees[edge.type] = avg_degree

            self._statistics = self._statistics.model_copy(
                update={
                    "edge_counts_by_type": new_edge_counts,
                    "avg_degree_by_type": new_avg_degrees,
                    "last_updated": time.time(),
                }
            )

    def get_edge(self, edge_id: int | str) -> EdgeRef | None:
        """Get an edge by its ID.

        Args:
            edge_id: The edge ID to retrieve

        Returns:
            The EdgeRef if found, None otherwise
        """
        return self._edges.get(edge_id)

    def has_edge(self, edge_id: int | str) -> bool:
        """Check if an edge exists in the graph.

        Args:
            edge_id: The edge ID to check

        Returns:
            True if the edge exists, False otherwise
        """
        return edge_id in self._edges

    def edge_count(self) -> int:
        """Get the number of edges in the graph.

        Returns:
            The number of edges
        """
        return len(self._edges)

    def get_all_edges(self) -> list[EdgeRef]:
        """Get all edges in the graph.

        Returns:
            List of all edges
        """
        return list(self._edges.values())

    def get_edges_by_type(self, edge_type: str) -> list[EdgeRef]:
        """Get all edges of a specific type.

        Args:
            edge_type: The edge type to filter by

        Returns:
            List of edges with the specified type
        """
        edge_ids = self._type_index.get(edge_type, set())
        return [self._edges[edge_id] for edge_id in edge_ids]

    def get_outgoing_edges(self, node_id: int | str) -> list[EdgeRef]:
        """Get all edges going out from a node.

        Args:
            node_id: The source node ID

        Returns:
            List of outgoing edges (empty list if node doesn't exist)
        """
        return list(self._outgoing.get(node_id, []))

    def get_incoming_edges(self, node_id: int | str) -> list[EdgeRef]:
        """Get all edges coming into a node.

        Args:
            node_id: The destination node ID

        Returns:
            List of incoming edges (empty list if node doesn't exist)
        """
        return list(self._incoming.get(node_id, []))

    def clear(self) -> None:
        """Clear all graph data, resetting to an empty state.

        Removes all nodes, edges, indexes, and statistics.
        This is equivalent to creating a new Graph() but reuses the same object.
        """
        self._nodes.clear()
        self._edges.clear()
        self._outgoing.clear()
        self._incoming.clear()
        self._label_index.clear()
        self._type_index.clear()
        self._statistics = GraphStatistics.empty()

    def snapshot(self) -> dict:
        """Create a snapshot of the current graph state.

        Returns:
            Dictionary containing all graph data for restoration

        Note:
            This creates a deep copy of all internal structures to support
            transaction rollback. For large graphs, this may be memory intensive.
        """
        import copy

        return {
            "nodes": copy.deepcopy(self._nodes),
            "edges": copy.deepcopy(self._edges),
            "outgoing": copy.deepcopy(dict(self._outgoing)),
            "incoming": copy.deepcopy(dict(self._incoming)),
            "label_index": copy.deepcopy(dict(self._label_index)),
            "type_index": copy.deepcopy(dict(self._type_index)),
            "statistics": self._statistics,  # Immutable, no need to deep copy
        }

    def restore(self, snapshot: dict) -> None:
        """Restore graph state from a snapshot.

        Args:
            snapshot: Snapshot dictionary created by snapshot()

        Note:
            Completely replaces the current graph state with the snapshot state.
        """
        self._nodes = snapshot["nodes"]
        self._edges = snapshot["edges"]
        self._outgoing = defaultdict(list, snapshot["outgoing"])
        self._incoming = defaultdict(list, snapshot["incoming"])
        self._label_index = defaultdict(set, snapshot["label_index"])
        self._type_index = defaultdict(set, snapshot["type_index"])
        self._statistics = snapshot.get("statistics", GraphStatistics.empty())
