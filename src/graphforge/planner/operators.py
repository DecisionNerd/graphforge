"""Logical plan operators for query execution.

This module defines the operators used in logical query plans:
- ScanNodes: Scan nodes by label
- ExpandEdges: Traverse relationships
- Filter: Apply predicates
- Project: Select return items
- With: Pipeline boundary for query chaining
- Limit: Limit result rows
- Skip: Skip result rows
- Create: Create nodes and relationships
- Set: Update properties
- Delete: Delete nodes and relationships
- Merge: Create or match patterns
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ScanNodes:
    """Operator for scanning nodes.

    Scans all nodes or filters by labels.

    Attributes:
        variable: Variable name to bind nodes to
        labels: Optional list of labels to filter by (None = all nodes)
    """

    variable: str
    labels: list[str] | None


@dataclass
class ExpandEdges:
    """Operator for expanding (traversing) relationships.

    Follows relationships from source nodes to destination nodes.

    Attributes:
        src_var: Variable name for source nodes
        edge_var: Variable name to bind edges to
        dst_var: Variable name to bind destination nodes to
        edge_types: List of edge types to match
        direction: Direction to traverse ('OUT', 'IN', 'UNDIRECTED')
    """

    src_var: str
    edge_var: str | None
    dst_var: str
    edge_types: list[str]
    direction: str  # 'OUT', 'IN', 'UNDIRECTED'


@dataclass
class Filter:
    """Operator for filtering rows based on a predicate.

    Evaluates a boolean expression and keeps only rows where it's true.

    Attributes:
        predicate: Expression AST node to evaluate
    """

    predicate: Any  # Expression AST node


@dataclass
class Project:
    """Operator for projecting (selecting) return items.

    Evaluates expressions and returns specified columns with optional aliases.

    Attributes:
        items: List of ReturnItem AST nodes (expression + optional alias)
    """

    items: list[Any]  # List of ReturnItem AST nodes


@dataclass
class Limit:
    """Operator for limiting the number of result rows.

    Attributes:
        count: Maximum number of rows to return
    """

    count: int


@dataclass
class Skip:
    """Operator for skipping result rows.

    Attributes:
        count: Number of rows to skip
    """

    count: int


@dataclass
class Sort:
    """Operator for sorting result rows.

    Sorts rows by one or more expressions with specified directions.
    Can reference RETURN aliases if return_items is provided.

    Attributes:
        items: List of OrderByItem AST nodes (expression + ascending flag)
        return_items: Optional list of ReturnItem AST nodes for alias resolution
    """

    items: list[Any]  # List of OrderByItem AST nodes
    return_items: list[Any] | None = None  # Optional ReturnItems for alias resolution


@dataclass
class Aggregate:
    """Operator for aggregating rows.

    Groups rows by grouping expressions and computes aggregation functions.

    Attributes:
        grouping_exprs: List of expressions to group by (non-aggregated RETURN items)
        agg_exprs: List of aggregation function calls (FunctionCall nodes)
        return_items: All ReturnItems from RETURN clause (for result projection)
    """

    grouping_exprs: list[Any]  # List of non-aggregate expressions
    agg_exprs: list[Any]  # List of FunctionCall nodes
    return_items: list[Any]  # List of ReturnItems


@dataclass
class With:
    """Operator for WITH clause (query chaining and subqueries).

    Acts as a pipeline boundary between query parts. Projects columns
    (like RETURN) and optionally filters, sorts, and paginates.

    The WITH clause allows chaining multiple query parts together:
        MATCH (n) WITH n ORDER BY n.age LIMIT 10 MATCH (n)-[r]->(m) RETURN n, m

    Attributes:
        items: List of ReturnItem AST nodes (expressions to project)
        predicate: Optional filter predicate (WHERE after WITH)
        sort_items: Optional list of OrderByItem AST nodes
        skip_count: Optional number of rows to skip
        limit_count: Optional maximum number of rows
    """

    items: list[Any]  # List of ReturnItem AST nodes
    predicate: Any | None = None  # Optional WHERE expression
    sort_items: list[Any] | None = None  # Optional OrderByItem list
    skip_count: int | None = None  # Optional SKIP count
    limit_count: int | None = None  # Optional LIMIT count


@dataclass
class Create:
    """Operator for creating graph elements.

    Creates nodes and relationships from patterns.

    Attributes:
        patterns: List of patterns to create (from CREATE clause)
    """

    patterns: list[Any]  # List of node and relationship patterns to create


@dataclass
class Set:
    """Operator for updating properties.

    Updates properties on nodes and relationships.

    Attributes:
        items: List of (property_access, expression) tuples
    """

    items: list[tuple[Any, Any]]  # List of (property_access, expression) tuples


@dataclass
class Delete:
    """Operator for deleting graph elements.

    Removes nodes and relationships from the graph.

    Attributes:
        variables: List of variable names to delete
    """

    variables: list[str]  # List of variable names to delete


@dataclass
class Merge:
    """Operator for merging patterns.

    Creates patterns if they don't exist, or matches them if they do.

    Attributes:
        patterns: List of patterns to merge
    """

    patterns: list[Any]  # List of node and relationship patterns to merge
