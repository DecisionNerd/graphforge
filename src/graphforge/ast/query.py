"""Top-level query AST node.

This module defines the root AST node for openCypher queries.
"""

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


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


class UnionQuery(BaseModel):
    """AST node for UNION queries.

    Combines results from multiple query branches using UNION or UNION ALL.

    Attributes:
        branches: List of CypherQuery objects representing each branch
        all: True for UNION ALL (keeps duplicates), False for UNION (removes duplicates)

    Examples:
        MATCH (n:Person) RETURN n UNION MATCH (m:Company) RETURN m
        MATCH (n) RETURN n.name UNION ALL MATCH (m) RETURN m.name
    """

    branches: list[CypherQuery] = Field(
        ..., description="List of query branches to combine with UNION"
    )
    all: bool = Field(..., description="True for UNION ALL, False for UNION")

    @field_validator("branches")
    @classmethod
    def validate_branches(cls, v: list[CypherQuery]) -> list[CypherQuery]:
        """Validate that branches is non-empty and contains CypherQuery objects."""
        if not v:
            raise ValueError("UNION must have at least one branch")
        if not all(isinstance(b, CypherQuery) for b in v):
            raise ValueError("All branches must be CypherQuery objects")
        return v

    @model_validator(mode="after")
    def validate_union_query(self) -> "UnionQuery":
        """Validate cross-field constraints."""
        if len(self.branches) < 2:
            raise ValueError("UNION requires at least two branches")
        return self

    model_config = {"frozen": True}
