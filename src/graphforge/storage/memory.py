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

    def add_node(self, node: NodeRef) -> None:
        """Add a node to the graph.

        Args:
            node: The node to add

        Note:
            If a node with this ID already exists, it will be replaced.
        """
        # Remove old node from label index if it exists
        if node.id in self._nodes:
            old_node = self._nodes[node.id]
            for label in old_node.labels:
                self._label_index[label].discard(node.id)

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

        # Remove old edge from indexes if it exists
        if edge.id in self._edges:
            old_edge = self._edges[edge.id]
            self._outgoing[old_edge.src.id].remove(old_edge)
            self._incoming[old_edge.dst.id].remove(old_edge)
            self._type_index[old_edge.type].discard(edge.id)

        # Store edge
        self._edges[edge.id] = edge

        # Update adjacency lists
        self._outgoing[edge.src.id].append(edge)
        self._incoming[edge.dst.id].append(edge)

        # Update type index
        self._type_index[edge.type].add(edge.id)

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
