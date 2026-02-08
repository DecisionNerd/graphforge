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
    - WITH
    - RETURN
    - LIMIT
    - SKIP

    Examples:
        MATCH (n:Person) RETURN n
        MATCH (n) WHERE n.age > 30 RETURN n.name LIMIT 10
        MATCH (n) WITH n ORDER BY n.age MATCH (n)-[r]->(m) RETURN n, m
    """

    clauses: list[Any]  # List of Clause nodes


@dataclass
class UnionQuery:
    """AST node for UNION queries.

    Combines results from multiple query branches using UNION or UNION ALL.

    Attributes:
        branches: List of CypherQuery objects representing each branch
        all: True for UNION ALL (keeps duplicates), False for UNION (removes duplicates)

    Examples:
        MATCH (n:Person) RETURN n UNION MATCH (m:Company) RETURN m
        MATCH (n) RETURN n.name UNION ALL MATCH (m) RETURN m.name
    """

    branches: list[CypherQuery]
    all: bool
