"""Logical plan operators for query execution.

This module defines the operators used in logical query plans:
- ScanNodes: Scan nodes by label
- ExpandEdges: Traverse relationships
- Filter: Apply predicates
- Project: Select return items
- Limit: Limit result rows
- Skip: Skip result rows
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
