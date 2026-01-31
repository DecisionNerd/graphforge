"""Top-level query AST node.

This module defines the root AST node for openCypher queries.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class CypherQuery:
    """Root AST node for an openCypher query.

    A query consists of a sequence of clauses:
    - MATCH
    - WHERE
    - RETURN
    - LIMIT
    - SKIP

    Examples:
        MATCH (n:Person) RETURN n
        MATCH (n) WHERE n.age > 30 RETURN n.name LIMIT 10
    """

    clauses: list[Any]  # List of Clause nodes
