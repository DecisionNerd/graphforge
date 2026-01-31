"""Clause AST nodes for openCypher queries.

This module defines the major query clauses:
- MatchClause: MATCH patterns
- CreateClause: CREATE patterns
- SetClause: SET property updates
- DeleteClause: DELETE nodes/relationships
- MergeClause: MERGE patterns
- WhereClause: WHERE predicates
- ReturnClause: RETURN projections
- WithClause: WITH query chaining
- LimitClause: LIMIT row count
- SkipClause: SKIP offset
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class MatchClause:
    """MATCH clause for pattern matching.

    Examples:
        MATCH (n:Person)
        MATCH (a)-[r:KNOWS]->(b)
    """

    patterns: list[Any]  # List of NodePattern or RelationshipPattern


@dataclass
class CreateClause:
    """CREATE clause for creating graph elements.

    Examples:
        CREATE (n:Person {name: 'Alice'})
        CREATE (a)-[r:KNOWS]->(b)
    """

    patterns: list[Any]  # List of NodePattern or RelationshipPattern


@dataclass
class SetClause:
    """SET clause for updating properties.

    Examples:
        SET n.age = 30
        SET n.age = 30, n.name = 'Alice'
    """

    items: list[tuple[Any, Any]]  # List of (property_access, expression) tuples


@dataclass
class DeleteClause:
    """DELETE clause for removing nodes and relationships.

    Examples:
        DELETE n
        DELETE n, r
    """

    variables: list[str]  # List of variable names to delete


@dataclass
class MergeClause:
    """MERGE clause for creating or matching patterns.

    Examples:
        MERGE (n:Person {name: 'Alice'})
        MERGE (a)-[r:KNOWS]->(b)
    """

    patterns: list[Any]  # List of NodePattern or RelationshipPattern


@dataclass
class WhereClause:
    """WHERE clause for filtering.

    Examples:
        WHERE n.age > 30
        WHERE n.name = "Alice" AND n.age < 50
    """

    predicate: Any  # Expression


@dataclass
class ReturnItem:
    """A single return item with optional alias.

    Examples:
        n (no alias)
        n.name AS name (with alias)
    """

    expression: Any  # Expression to evaluate
    alias: str | None = None  # Optional alias


@dataclass
class ReturnClause:
    """RETURN clause for projection.

    Examples:
        RETURN n
        RETURN n.name AS name, n.age AS age
        RETURN count(n) AS count
    """

    items: list[ReturnItem]  # List of ReturnItems


@dataclass
class LimitClause:
    """LIMIT clause for limiting result rows.

    Examples:
        LIMIT 10
        LIMIT 100
    """

    count: int


@dataclass
class SkipClause:
    """SKIP clause for offsetting results.

    Examples:
        SKIP 5
        SKIP 20
    """

    count: int


@dataclass
class OrderByItem:
    """A single ORDER BY item with direction.

    Examples:
        n.name (default ASC)
        n.age DESC
    """

    expression: Any  # Expression to sort by
    ascending: bool = True  # True for ASC, False for DESC


@dataclass
class OrderByClause:
    """ORDER BY clause for sorting results.

    Examples:
        ORDER BY n.name
        ORDER BY n.age DESC
        ORDER BY n.age DESC, n.name ASC
    """

    items: list[OrderByItem]  # List of OrderByItems


@dataclass
class WithClause:
    """WITH clause for query chaining and subqueries.

    The WITH clause allows you to pipe the results of one part of a query
    to another, enabling complex multi-step queries.

    Examples:
        WITH n.name AS name, count(*) AS connections
        WITH person WHERE person.age > 25
        WITH person ORDER BY person.age LIMIT 10
    """

    items: list[ReturnItem]  # Projection items (same as RETURN)
    where: WhereClause | None = None  # Optional WHERE after WITH
    order_by: OrderByClause | None = None  # Optional ORDER BY
    skip: SkipClause | None = None  # Optional SKIP
    limit: LimitClause | None = None  # Optional LIMIT
