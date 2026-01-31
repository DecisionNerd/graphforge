"""High-level API for GraphForge.

This module provides the main public interface for GraphForge.
"""

from pathlib import Path

from graphforge.executor.executor import QueryExecutor
from graphforge.parser.parser import CypherParser
from graphforge.planner.planner import QueryPlanner
from graphforge.storage.memory import Graph


class GraphForge:
    """Main GraphForge interface for graph operations.

    GraphForge provides an embedded graph database with openCypher query support.

    Examples:
        >>> gf = GraphForge()
        >>> # Add nodes and edges using the graph directly
        >>> from graphforge.types.graph import NodeRef
        >>> node = NodeRef(id=1, labels=frozenset(["Person"]), properties={})
        >>> gf.graph.add_node(node)
        >>> # Query with openCypher
        >>> results = gf.execute("MATCH (n:Person) RETURN n")
    """

    def __init__(self, path: str | Path | None = None):
        """Initialize GraphForge.

        Args:
            path: Optional path to persistent storage (not yet implemented)
                  If None, uses in-memory storage.
        """
        # For now, always use in-memory storage
        self.graph = Graph()
        self.parser = CypherParser()
        self.planner = QueryPlanner()
        self.executor = QueryExecutor(self.graph)

    def execute(self, query: str) -> list[dict]:
        """Execute an openCypher query.

        Args:
            query: openCypher query string

        Returns:
            List of result rows as dictionaries

        Examples:
            >>> gf = GraphForge()
            >>> results = gf.execute("MATCH (n) RETURN n LIMIT 10")
        """
        # Parse query
        ast = self.parser.parse(query)

        # Plan execution
        operators = self.planner.plan(ast)

        # Execute
        results = self.executor.execute(operators)

        return results
