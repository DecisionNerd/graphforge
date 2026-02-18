"""Clause AST nodes for openCypher queries.

This module defines the major query clauses:
- MatchClause: MATCH patterns
- OptionalMatchClause: OPTIONAL MATCH patterns
- CreateClause: CREATE patterns
- SetClause: SET property updates
- RemoveClause: REMOVE properties and labels
- DeleteClause: DELETE nodes/relationships
- MergeClause: MERGE patterns
- UnwindClause: UNWIND list expansion
- WhereClause: WHERE predicates
- ReturnClause: RETURN projections
- CallClause: CALL subqueries
- WithClause: WITH query chaining
- LimitClause: LIMIT row count
- SkipClause: SKIP offset
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class MatchClause(BaseModel):
    """MATCH clause for pattern matching.

    Examples:
        MATCH (n:Person)
        MATCH (a)-[r:KNOWS]->(b)
    """

    patterns: list[Any] = Field(..., min_length=1, description="List of patterns")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class OptionalMatchClause(BaseModel):
    """OPTIONAL MATCH clause for optional pattern matching (left outer join).

    Like MATCH, but preserves rows with NULL bindings when patterns don't match.

    Examples:
        OPTIONAL MATCH (p)-[:KNOWS]->(f)
        OPTIONAL MATCH (a)-[r:LIKES]->(b)
    """

    patterns: list[Any] = Field(..., min_length=1, description="List of patterns")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class CreateClause(BaseModel):
    """CREATE clause for creating graph elements.

    Examples:
        CREATE (n:Person {name: 'Alice'})
        CREATE (a)-[r:KNOWS]->(b)
    """

    patterns: list[Any] = Field(..., min_length=1, description="List of patterns")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class SetClause(BaseModel):
    """SET clause for updating properties.

    Examples:
        SET n.age = 30
        SET n.age = 30, n.name = 'Alice'
    """

    items: list[tuple[Any, Any]] = Field(
        ..., min_length=1, description="List of (property, expression) tuples"
    )

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: list[tuple[Any, Any]]) -> list[tuple[Any, Any]]:
        """Validate SET items format."""
        for i, item in enumerate(v):
            if not isinstance(item, tuple) or len(item) != 2:
                raise ValueError(
                    f"SET item {i} must be a tuple of (property_access, expression), got {item}"
                )
        return v

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class RemoveItem(BaseModel):
    """A single REMOVE item (property or label).

    Attributes:
        item_type: 'property' or 'label'
        variable: Variable name
        name: Property name or label name
    """

    item_type: str = Field(..., description="'property' or 'label'")
    variable: str = Field(..., min_length=1, description="Variable name")
    name: str = Field(..., min_length=1, description="Property or label name")

    @field_validator("item_type")
    @classmethod
    def validate_item_type(cls, v: str) -> str:
        """Validate item_type is 'property' or 'label'."""
        if v not in {"property", "label"}:
            raise ValueError(f"item_type must be 'property' or 'label', got {v}")
        return v

    model_config = {"frozen": True}


class RemoveClause(BaseModel):
    """REMOVE clause for removing properties and labels.

    Examples:
        REMOVE n.age
        REMOVE n:Person
        REMOVE n.age, n.name
        REMOVE n:Person:Employee
    """

    items: list[RemoveItem] = Field(..., min_length=1, description="List of RemoveItems")

    model_config = {"frozen": True}


class DeleteClause(BaseModel):
    """DELETE clause for removing nodes and relationships.

    Examples:
        DELETE n
        DETACH DELETE n
        DELETE n, r
    """

    variables: list[str] = Field(..., min_length=1, description="Variables to delete")
    detach: bool = Field(default=False, description="True for DETACH DELETE")

    model_config = {"frozen": True}


class MergeClause(BaseModel):
    """MERGE clause for creating or matching patterns.

    Examples:
        MERGE (n:Person {name: 'Alice'})
        MERGE (n:Person {id: 1}) ON CREATE SET n.created = timestamp()
        MERGE (n:Person {id: 1}) ON MATCH SET n.updated = timestamp()
        MERGE (n:Person {id: 1}) ON CREATE SET n.created = 1 ON MATCH SET n.updated = 1
        MERGE (a)-[r:KNOWS]->(b)
    """

    patterns: list[Any] = Field(..., min_length=1, description="List of patterns")
    on_create: "SetClause | None" = Field(default=None, description="ON CREATE SET clause")
    on_match: "SetClause | None" = Field(default=None, description="ON MATCH SET clause")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class UnwindClause(BaseModel):
    """UNWIND clause for expanding lists into rows.

    Examples:
        UNWIND [1, 2, 3] AS num
        UNWIND p.tags AS tag
        UNWIND ['Alice', 'Bob'] AS name
    """

    expression: Any = Field(..., description="Expression that evaluates to a list")
    variable: str = Field(..., min_length=1, description="Variable name for each item")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class WhereClause(BaseModel):
    """WHERE clause for filtering.

    Examples:
        WHERE n.age > 30
        WHERE n.name = "Alice" AND n.age < 50
    """

    predicate: Any = Field(..., description="Filter predicate expression")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class ReturnItem(BaseModel):
    """A single return item with optional alias.

    Examples:
        n (no alias)
        n.name AS name (with alias)
    """

    expression: Any = Field(..., description="Expression to evaluate")
    alias: str | None = Field(default=None, description="Optional alias")

    @field_validator("alias")
    @classmethod
    def validate_alias(cls, v: str | None) -> str | None:
        """Validate alias format if provided."""
        if v is not None and len(v) == 0:
            raise ValueError("Alias cannot be empty string")
        return v

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class ReturnClause(BaseModel):
    """RETURN clause for projection.

    Examples:
        RETURN n
        RETURN n.name AS name, n.age AS age
        RETURN count(n) AS count
        RETURN DISTINCT n.name
    """

    items: list[ReturnItem] = Field(..., min_length=1, description="List of ReturnItems")
    distinct: bool = Field(default=False, description="True for RETURN DISTINCT")

    model_config = {"frozen": True}


class LimitClause(BaseModel):
    """LIMIT clause for limiting result rows.

    Examples:
        LIMIT 10
        LIMIT 100
        LIMIT 0  (valid - returns no rows)
    """

    count: int = Field(..., ge=0, description="Maximum number of rows")

    model_config = {"frozen": True}


class SkipClause(BaseModel):
    """SKIP clause for offsetting results.

    Examples:
        SKIP 5
        SKIP 20
    """

    count: int = Field(..., ge=0, description="Number of rows to skip")

    model_config = {"frozen": True}


class OrderByItem(BaseModel):
    """A single ORDER BY item with direction.

    Examples:
        n.name (default ASC)
        n.age DESC
    """

    expression: Any = Field(..., description="Expression to sort by")
    ascending: bool = Field(default=True, description="True for ASC, False for DESC")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class OrderByClause(BaseModel):
    """ORDER BY clause for sorting results.

    Examples:
        ORDER BY n.name
        ORDER BY n.age DESC
        ORDER BY n.age DESC, n.name ASC
    """

    items: list[OrderByItem] = Field(..., min_length=1, description="List of OrderByItems")

    model_config = {"frozen": True}


class CallClause(BaseModel):
    """CALL clause for general subqueries.

    The CALL clause executes a subquery and returns its results, optionally
    importing variables from the outer scope. Unlike EXISTS/COUNT expressions,
    CALL can execute arbitrary queries including UNION.

    Examples:
        CALL { MATCH (p:Person) RETURN p.name }
        CALL { MATCH (p) RETURN p UNION MATCH (c) RETURN c }
        MATCH (p:Person) CALL { MATCH (p)-[:KNOWS]->(f) RETURN f }
    """

    query: Any = Field(..., description="Nested query (CypherQuery AST, can include UNION)")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class WithClause(BaseModel):
    """WITH clause for query chaining and subqueries.

    The WITH clause allows you to pipe the results of one part of a query
    to another, enabling complex multi-step queries.

    Examples:
        WITH n.name AS name, count(*) AS connections
        WITH person WHERE person.age > 25
        WITH person ORDER BY person.age LIMIT 10
        WITH DISTINCT n.name AS name
    """

    items: list[ReturnItem] = Field(..., min_length=1, description="Projection items")
    distinct: bool = Field(default=False, description="True for WITH DISTINCT")
    where: "WhereClause | None" = Field(default=None, description="Optional WHERE after WITH")
    order_by: "OrderByClause | None" = Field(default=None, description="Optional ORDER BY")
    skip: "SkipClause | None" = Field(default=None, description="Optional SKIP")
    limit: "LimitClause | None" = Field(default=None, description="Optional LIMIT")

    model_config = {"frozen": True}
