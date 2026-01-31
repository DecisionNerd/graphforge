"""Query execution engine.

This module contains the execution engine that executes logical
plans against graph stores.
"""

from graphforge.executor.evaluator import ExecutionContext, evaluate_expression

__all__ = [
    "ExecutionContext",
    "evaluate_expression",
]
