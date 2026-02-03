"""Clause AST nodes for openCypher queries.

This module defines the major query clauses:
- MatchClause: MATCH patterns
- CreateClause: CREATE patterns
- SetClause: SET property updates
- RemoveClause: REMOVE properties and labels
- DeleteClause: DELETE nodes/relationships
- MergeClause: MERGE patterns
- UnwindClause: UNWIND list expansion
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
class RemoveItem:
    """A single REMOVE item (property or label).

    Attributes:
        item_type: 'property' or 'label'
        variable: Variable name
        name: Property name or label name
    """

    item_type: str  # 'property' or 'label'
    variable: str  # Variable name
    name: str  # Property or label name


@dataclass
class RemoveClause:
    """REMOVE clause for removing properties and labels.

    Examples:
        REMOVE n.age
        REMOVE n:Person
        REMOVE n.age, n.name
        REMOVE n:Person:Employee
    """

    items: list[RemoveItem]  # List of RemoveItems


@dataclass
class DeleteClause:
    """DELETE clause for removing nodes and relationships.

    Examples:
        DELETE n
        DETACH DELETE n
        DELETE n, r
    """

    variables: list[str]  # List of variable names to delete
    detach: bool = False  # True for DETACH DELETE


@dataclass
class MergeClause:
    """MERGE clause for creating or matching patterns.

    Examples:
        MERGE (n:Person {name: 'Alice'})
        MERGE (n:Person {id: 1}) ON CREATE SET n.created = timestamp()
        MERGE (n:Person {id: 1}) ON MATCH SET n.updated = timestamp()
        MERGE (n:Person {id: 1}) ON CREATE SET n.created = 1 ON MATCH SET n.updated = 1
        MERGE (a)-[r:KNOWS]->(b)
    """

    patterns: list[Any]  # List of NodePattern or RelationshipPattern
    on_create: "SetClause | None" = None  # Optional ON CREATE SET clause
    on_match: "SetClause | None" = None  # Optional ON MATCH SET clause


@dataclass
class UnwindClause:
    """UNWIND clause for expanding lists into rows.

    Examples:
        UNWIND [1, 2, 3] AS num
        UNWIND p.tags AS tag
        UNWIND ['Alice', 'Bob'] AS name
    """

    expression: Any  # Expression that evaluates to a list
    variable: str  # Variable name to bind each list item to


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
        RETURN DISTINCT n.name
    """

    items: list[ReturnItem]  # List of ReturnItems
    distinct: bool = False  # True for RETURN DISTINCT


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
        WITH DISTINCT n.name AS name
    """

    items: list[ReturnItem]  # Projection items (same as RETURN)
    distinct: bool = False  # True for WITH DISTINCT
    where: WhereClause | None = None  # Optional WHERE after WITH
    order_by: OrderByClause | None = None  # Optional ORDER BY
    skip: SkipClause | None = None  # Optional SKIP
    limit: LimitClause | None = None  # Optional LIMIT
