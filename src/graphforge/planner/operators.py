"""Logical plan operators for query execution.

This module defines the operators used in logical query plans:
- ScanNodes: Scan nodes by label
- ExpandEdges: Traverse relationships
- OptionalExpandEdges: Optional relationship expansion (left outer join)
- Filter: Apply predicates
- Project: Select return items
- With: Pipeline boundary for query chaining
- Limit: Limit result rows
- Skip: Skip result rows
- Create: Create nodes and relationships
- Set: Update properties
- Remove: Remove properties and labels
- Delete: Delete nodes and relationships
- Merge: Create or match patterns
- Unwind: Expand lists into rows
- Union: Combine results from multiple queries
- Subquery: Nested query expressions (EXISTS, COUNT)
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ScanNodes(BaseModel):
    """Operator for scanning nodes.

    Scans all nodes or filters by labels.

    Attributes:
        variable: Variable name to bind nodes to
        labels: Optional list of labels to filter by (None = all nodes)
    """

    variable: str = Field(..., min_length=1, description="Variable name to bind nodes")
    labels: list[str] | None = Field(default=None, description="Optional label filter")

    @field_validator("variable")
    @classmethod
    def validate_variable(cls, v: str) -> str:
        """Validate variable name."""
        if not v[0].isalpha() and v[0] != "_":
            raise ValueError(f"Variable must start with letter or underscore: {v}")
        return v

    model_config = {"frozen": True}


class ExpandEdges(BaseModel):
    """Operator for expanding (traversing) relationships.

    Follows relationships from source nodes to destination nodes.

    Attributes:
        src_var: Variable name for source nodes
        edge_var: Variable name to bind edges to
        dst_var: Variable name to bind destination nodes to
        edge_types: List of edge types to match
        direction: Direction to traverse ('OUT', 'IN', 'UNDIRECTED')
    """

    src_var: str = Field(..., min_length=1, description="Source variable name")
    edge_var: str | None = Field(default=None, description="Edge variable name")
    dst_var: str = Field(..., min_length=1, description="Destination variable name")
    edge_types: list[str] = Field(..., description="Edge types to match")
    direction: str = Field(..., description="Traversal direction")

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        """Validate direction is valid."""
        valid_dirs = {"OUT", "IN", "UNDIRECTED"}
        if v not in valid_dirs:
            raise ValueError(f"Direction must be one of {valid_dirs}, got {v}")
        return v

    model_config = {"frozen": True}


class Filter(BaseModel):
    """Operator for filtering rows based on a predicate.

    Evaluates a boolean expression and keeps only rows where it's true.

    Attributes:
        predicate: Expression AST node to evaluate
    """

    predicate: Any = Field(..., description="Filter predicate expression")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class Project(BaseModel):
    """Operator for projecting (selecting) return items.

    Evaluates expressions and returns specified columns with optional aliases.

    Attributes:
        items: List of ReturnItem AST nodes (expression + optional alias)
    """

    items: list[Any] = Field(..., min_length=1, description="List of ReturnItems")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class Limit(BaseModel):
    """Operator for limiting the number of result rows.

    Attributes:
        count: Maximum number of rows to return
    """

    count: int = Field(..., ge=0, description="Maximum number of rows")

    model_config = {"frozen": True}


class Skip(BaseModel):
    """Operator for skipping result rows.

    Attributes:
        count: Number of rows to skip
    """

    count: int = Field(..., ge=0, description="Number of rows to skip")

    model_config = {"frozen": True}


class Sort(BaseModel):
    """Operator for sorting result rows.

    Sorts rows by one or more expressions with specified directions.
    Can reference RETURN aliases if return_items is provided.

    Attributes:
        items: List of OrderByItem AST nodes (expression + ascending flag)
        return_items: Optional list of ReturnItem AST nodes for alias resolution
    """

    items: list[Any] = Field(..., min_length=1, description="List of OrderByItems")
    return_items: list[Any] | None = Field(
        default=None, description="Optional ReturnItems for alias resolution"
    )

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class Aggregate(BaseModel):
    """Operator for aggregating rows.

    Groups rows by grouping expressions and computes aggregation functions.

    Attributes:
        grouping_exprs: List of expressions to group by (non-aggregated RETURN items)
        agg_exprs: List of aggregation function calls (FunctionCall nodes)
        return_items: All ReturnItems from RETURN clause (for result projection)
    """

    grouping_exprs: list[Any] = Field(..., description="Grouping expressions")
    agg_exprs: list[Any] = Field(..., description="Aggregation functions")
    return_items: list[Any] = Field(..., min_length=1, description="All ReturnItems")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class With(BaseModel):
    """Operator for WITH clause (query chaining and subqueries).

    Acts as a pipeline boundary between query parts. Projects columns
    (like RETURN) and optionally filters, sorts, and paginates.

    The WITH clause allows chaining multiple query parts together:
        MATCH (n) WITH n ORDER BY n.age LIMIT 10 MATCH (n)-[r]->(m) RETURN n, m

    Attributes:
        items: List of ReturnItem AST nodes (expressions to project)
        distinct: True for WITH DISTINCT (deduplication)
        predicate: Optional filter predicate (WHERE after WITH)
        sort_items: Optional list of OrderByItem AST nodes
        skip_count: Optional number of rows to skip
        limit_count: Optional maximum number of rows
    """

    items: list[Any] = Field(..., min_length=1, description="List of ReturnItems")
    distinct: bool = Field(default=False, description="True for WITH DISTINCT")
    predicate: Any | None = Field(default=None, description="Optional WHERE expression")
    sort_items: list[Any] | None = Field(default=None, description="Optional OrderByItem list")
    skip_count: int | None = Field(default=None, ge=0, description="Optional SKIP count")
    limit_count: int | None = Field(default=None, gt=0, description="Optional LIMIT count")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class Distinct(BaseModel):
    """Operator for deduplication.

    Removes duplicate rows from input by comparing all bound variables.
    Used to implement RETURN DISTINCT and WITH DISTINCT.
    """

    model_config = {"frozen": True}


class Create(BaseModel):
    """Operator for creating graph elements.

    Creates nodes and relationships from patterns.

    Attributes:
        patterns: List of patterns to create (from CREATE clause)
    """

    patterns: list[Any] = Field(..., min_length=1, description="Patterns to create")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class Set(BaseModel):
    """Operator for updating properties.

    Updates properties on nodes and relationships.

    Attributes:
        items: List of (property_access, expression) tuples
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


class Remove(BaseModel):
    """Operator for removing properties and labels.

    Removes properties from nodes/relationships or labels from nodes.

    Attributes:
        items: List of RemoveItem objects (from AST)
    """

    items: list[Any] = Field(..., min_length=1, description="List of RemoveItems")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class Delete(BaseModel):
    """Operator for deleting graph elements.

    Removes nodes and relationships from the graph.

    Attributes:
        variables: List of variable names to delete
        detach: If True, delete relationships before deleting nodes (DETACH DELETE)
    """

    variables: list[str] = Field(..., min_length=1, description="Variables to delete")
    detach: bool = Field(default=False, description="True for DETACH DELETE")

    model_config = {"frozen": True}


class Merge(BaseModel):
    """Operator for merging patterns with conditional SET support.

    Creates patterns if they don't exist, or matches them if they do.
    Optionally executes SET operations when creating (ON CREATE SET) or
    matching (ON MATCH SET).

    Attributes:
        patterns: List of patterns to merge
        on_create: Optional SetClause to execute when creating new elements
        on_match: Optional SetClause to execute when matching existing elements
    """

    patterns: list[Any] = Field(..., min_length=1, description="Patterns to merge")
    on_create: Any = Field(default=None, description="Optional SetClause for ON CREATE SET")
    on_match: Any = Field(default=None, description="Optional SetClause for ON MATCH SET")

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class Unwind(BaseModel):
    """Operator for expanding lists into rows.

    Takes a list expression and expands it into multiple rows, binding each
    element to a variable. Similar to SQL UNNEST or array unnesting.

    Example:
        UNWIND [1, 2, 3] AS num
        -> Creates 3 rows with num=1, num=2, num=3

    Attributes:
        expression: Expression that evaluates to a list
        variable: Variable name to bind each list element to
    """

    expression: Any = Field(..., description="Expression that evaluates to a list")
    variable: str = Field(..., min_length=1, description="Variable name for each element")

    @field_validator("variable")
    @classmethod
    def validate_variable(cls, v: str) -> str:
        """Validate variable name."""
        if not v[0].isalpha() and v[0] != "_":
            raise ValueError(f"Variable must start with letter or underscore: {v}")
        return v

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class Union(BaseModel):
    """Operator for UNION/UNION ALL query combination.

    Combines results from multiple query branches. Each branch is a complete
    execution pipeline (list of operators).

    Example:
        MATCH (p:Person) RETURN p.name
        UNION
        MATCH (c:Company) RETURN c.name

    Attributes:
        branches: List of operator pipelines (each branch is a list of operators)
        all: False for UNION (deduplicate), True for UNION ALL (keep duplicates)
    """

    branches: list[list[Any]] = Field(..., min_length=2, description="List of operator pipelines")
    all: bool = Field(default=False, description="True for UNION ALL, False for UNION")

    @field_validator("branches")
    @classmethod
    def validate_branches(cls, v: list[list[Any]]) -> list[list[Any]]:
        """Validate that we have at least 2 branches."""
        if len(v) < 2:
            raise ValueError("Union must have at least 2 branches")
        return v

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class Subquery(BaseModel):
    """Operator for subquery expressions (EXISTS, COUNT, etc.).

    Executes a nested query pipeline and returns a result for use in expressions.

    Example:
        WHERE EXISTS { MATCH (n)-[:KNOWS]->(m) WHERE m.age > 30 }

    Attributes:
        operators: List of operators in the subquery pipeline
        expression_type: Type of subquery expression ("EXISTS", "COUNT")
        correlated_vars: Variables from outer scope that the subquery references
    """

    operators: list[Any] = Field(..., min_length=1, description="Subquery pipeline")
    expression_type: str = Field(..., description="Subquery type (EXISTS, COUNT)")
    correlated_vars: list[str] = Field(
        default_factory=list, description="Variables from outer scope"
    )

    @field_validator("expression_type")
    @classmethod
    def validate_expression_type(cls, v: str) -> str:
        """Validate expression type."""
        valid_types = {"EXISTS", "COUNT"}
        if v not in valid_types:
            raise ValueError(f"Subquery expression type must be one of {valid_types}, got {v}")
        return v

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class OptionalExpandEdges(BaseModel):
    """Operator for optional relationship expansion (left outer join).

    Like ExpandEdges, but preserves rows with NULL bindings when no matches found.
    Used to implement OPTIONAL MATCH.

    Example:
        MATCH (p:Person)
        OPTIONAL MATCH (p)-[:KNOWS]->(f)
        -> If p has no KNOWS edges, returns (p, f=NULL)

    Attributes:
        src_var: Variable name for source nodes
        edge_var: Variable name to bind edges to (None if not specified)
        dst_var: Variable name to bind destination nodes to
        edge_types: List of edge types to match (empty = all types)
        direction: Direction to traverse ('OUT', 'IN', 'UNDIRECTED')
    """

    src_var: str = Field(..., min_length=1, description="Source variable name")
    edge_var: str | None = Field(default=None, description="Edge variable name")
    dst_var: str = Field(..., min_length=1, description="Destination variable name")
    edge_types: list[str] = Field(..., description="Edge types to match")
    direction: str = Field(..., description="Traversal direction")

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        """Validate direction is valid."""
        valid_dirs = {"OUT", "IN", "UNDIRECTED"}
        if v not in valid_dirs:
            raise ValueError(f"Direction must be one of {valid_dirs}, got {v}")
        return v

    model_config = {"frozen": True}
