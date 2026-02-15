"""Utilities for analyzing and manipulating predicate expressions."""

from typing import Any

from graphforge.ast.expression import (
    BinaryOp,
    PropertyAccess,
    UnaryOp,
    Variable,
)


class PredicateAnalysis:
    """Utilities for analyzing predicate expressions."""

    @staticmethod
    def extract_conjuncts(predicate: Any) -> list[Any]:
        """Extract AND conjuncts from a predicate expression.

        Splits AND chains into a flat list. Does not split OR predicates
        as they must be evaluated together.

        Args:
            predicate: AST expression node

        Returns:
            List of conjunct expressions (single element if not an AND chain)

        Examples:
            a AND b AND c → [a, b, c]
            a OR b → [a OR b]
            a → [a]
        """
        if not isinstance(predicate, BinaryOp) or predicate.op != "AND":
            return [predicate]

        # Recursively extract from left and right
        conjuncts = []
        conjuncts.extend(PredicateAnalysis.extract_conjuncts(predicate.left))
        conjuncts.extend(PredicateAnalysis.extract_conjuncts(predicate.right))
        return conjuncts

    @staticmethod
    def combine_with_and(predicates: list[Any]) -> Any | None:
        """Combine multiple predicates with AND operator.

        Args:
            predicates: List of predicate expressions

        Returns:
            Single AND-combined expression, or None if empty list

        Examples:
            [a, b, c] → a AND b AND c
            [a] → a
            [] → None
        """
        if not predicates:
            return None

        if len(predicates) == 1:
            return predicates[0]

        # Build right-associative AND chain
        result = predicates[-1]
        for pred in reversed(predicates[:-1]):
            result = BinaryOp(op="AND", left=pred, right=result)
        return result

    @staticmethod
    def get_referenced_variables(expr: Any) -> set[str]:
        """Extract all variable names referenced in an expression.

        Walks the expression tree and collects Variable and PropertyAccess references.

        Args:
            expr: AST expression node

        Returns:
            Set of variable names referenced in the expression

        Examples:
            a.name = "Alice" → {"a"}
            a.age > b.age → {"a", "b"}
            5 = 5 → {}
        """
        variables = set()

        def walk(node: Any) -> None:
            """Recursively walk expression tree."""
            if isinstance(node, Variable):
                variables.add(node.name)
            elif isinstance(node, PropertyAccess):
                if node.variable is not None:
                    variables.add(node.variable)
                elif node.base is not None:
                    walk(node.base)
            elif isinstance(node, BinaryOp):
                walk(node.left)
                walk(node.right)
            elif isinstance(node, UnaryOp):
                walk(node.operand)
            elif isinstance(node, dict):
                # FunctionCall arguments
                for value in node.values():
                    if isinstance(value, list):
                        for item in value:
                            walk(item)
                    else:
                        walk(value)
            # Literals don't reference variables

        walk(expr)
        return variables

    @staticmethod
    def estimate_selectivity(predicate: Any) -> float:
        """Estimate selectivity of a predicate (0.0 = very selective, 1.0 = not selective).

        Uses heuristics based on operator type. Lower values = more selective
        = fewer rows pass = should evaluate first.

        Args:
            predicate: AST expression node

        Returns:
            Estimated selectivity between 0.0 and 1.0

        Selectivity heuristics:
            - Equality (=): 0.1 (highly selective)
            - IS NULL: 0.1
            - IS NOT NULL: 0.9
            - Inequality (<, >, <=, >=): 0.5 (moderate)
            - <> (not equals): 0.9 (not selective)
            - OR: max(left, right) (least selective branch)
            - AND: min(left, right) (most selective branch)
            - Default: 0.5
        """
        if not isinstance(predicate, (BinaryOp, UnaryOp)):
            return 0.5

        if isinstance(predicate, BinaryOp):
            op = predicate.op

            # Equality is highly selective
            if op == "=":
                return 0.1

            # Not equals is not selective
            if op == "<>":
                return 0.9

            # Inequality is moderately selective
            if op in ("<", ">", "<=", ">="):
                return 0.5

            # OR takes max selectivity (least selective branch dominates)
            if op == "OR":
                left_sel = PredicateAnalysis.estimate_selectivity(predicate.left)
                right_sel = PredicateAnalysis.estimate_selectivity(predicate.right)
                return max(left_sel, right_sel)

            # AND takes min selectivity (most selective branch dominates)
            if op == "AND":
                left_sel = PredicateAnalysis.estimate_selectivity(predicate.left)
                right_sel = PredicateAnalysis.estimate_selectivity(predicate.right)
                return min(left_sel, right_sel)

        if isinstance(predicate, UnaryOp):
            op = predicate.op

            # IS NULL is highly selective (few NULLs in most datasets)
            if op == "IS NULL":
                return 0.1

            # IS NOT NULL is not selective (most values are non-NULL)
            if op == "IS NOT NULL":
                return 0.9

        # Default moderate selectivity
        return 0.5
