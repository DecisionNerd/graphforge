"""Expression AST nodes for openCypher.

This module defines expression nodes for:
- Literals (integers, strings, booleans, null)
- Variable references
- Property access
- Binary operations (comparisons, logical operators)
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class Wildcard(BaseModel):
    """Wildcard expression for RETURN * and WITH *.

    Represents the special * syntax that expands to all variables in scope.
    """

    model_config = {"frozen": True}


class Literal(BaseModel):
    """Literal value expression.

    Examples:
        Literal(value=42), Literal(value="hello"), Literal(value=True), Literal(value=None)
    """

    value: Any = Field(..., description="Literal value (int, str, bool, None, float)")

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Any) -> Any:
        """Validate literal value is a supported type."""
        if v is not None and not isinstance(v, (int, str, bool, float, list, dict)):
            raise ValueError(
                f"Literal value must be int, str, bool, None, float, list, or dict, got {type(v)}"
            )
        return v

    model_config = {"frozen": True}


class Variable(BaseModel):
    """Variable reference expression.

    Examples:
        Variable(name="n"), Variable(name="person"), Variable(name="r")
    """

    name: str = Field(..., min_length=1, description="Variable name")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate variable name format."""
        if not v[0].isalpha() and v[0] != "_":
            raise ValueError(f"Variable name must start with letter or underscore: {v}")
        if not v.replace("_", "").isalnum():
            raise ValueError(f"Variable name must contain only alphanumeric and underscore: {v}")
        return v

    model_config = {"frozen": True}


class PropertyAccess(BaseModel):
    """Property access expression.

    Supports both variable property access and expression property access:
    - variable.property: PropertyAccess(variable="n", property="name")
    - {key: val}.property: PropertyAccess(base=Literal(...), property="key")
    - [1, 2, 3][0].property: PropertyAccess(base=ListIndex(...), property="...")

    For backward compatibility, 'variable' can still be used for simple cases.
    When 'base' is provided, it takes precedence over 'variable'.
    """

    variable: str | None = Field(default=None, description="Variable name (legacy)")
    base: Any | None = Field(default=None, description="Base expression for property access")
    property: str = Field(..., min_length=1, description="Property name")

    @model_validator(mode="after")
    def validate_variable_or_base(self) -> "PropertyAccess":
        """Ensure either variable or base is provided."""
        if self.variable is None and self.base is None:
            raise ValueError("PropertyAccess requires either 'variable' or 'base'")
        return self

    @field_validator("variable", "property")
    @classmethod
    def validate_identifier(cls, v: str | None) -> str | None:
        """Validate identifier format."""
        if v is None:
            return v
        if not v[0].isalpha() and v[0] != "_":
            raise ValueError(f"Identifier must start with letter or underscore: {v}")
        if not v.replace("_", "").isalnum():
            raise ValueError(f"Identifier must contain only alphanumeric and underscore: {v}")
        return v

    model_config = {"frozen": True}


class BinaryOp(BaseModel):
    """Binary operation expression.

    Supports:
    - Comparisons: =, <>, <, >, <=, >=
    - Logical: AND, OR
    - Arithmetic: +, -, *, / (future)
    """

    op: str = Field(..., description="Operator")
    left: Any = Field(..., description="Left expression")
    right: Any = Field(..., description="Right expression")

    @field_validator("op")
    @classmethod
    def validate_op(cls, v: str) -> str:
        """Validate operator is supported."""
        valid_ops = {
            "=",
            "<>",
            "<",
            ">",
            "<=",
            ">=",
            "AND",
            "OR",
            "+",
            "-",
            "*",
            "/",
            "%",
            "^",
            "STARTS WITH",
            "ENDS WITH",
            "CONTAINS",
            "IN",
        }
        if v not in valid_ops:
            raise ValueError(f"Unsupported binary operator: {v}")
        return v

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class UnaryOp(BaseModel):
    """Unary operation expression.

    Supports:
    - Logical: NOT
    - Arithmetic: - (negation, future)
    """

    op: str = Field(..., description="Operator")
    operand: Any = Field(..., description="Operand expression")

    @field_validator("op")
    @classmethod
    def validate_op(cls, v: str) -> str:
        """Validate operator is supported."""
        valid_ops = {"NOT", "-", "IS NULL", "IS NOT NULL"}
        if v not in valid_ops:
            raise ValueError(f"Unsupported unary operator: {v}")
        return v

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class FunctionCall(BaseModel):
    """Function call expression.

    Examples:
        COUNT(n), SUM(n.age), AVG(n.salary)
        COUNT(*) for counting all rows
    """

    name: str = Field(..., min_length=1, description="Function name")
    args: list[Any] = Field(default_factory=list, description="Function arguments")
    distinct: bool = Field(default=False, description="True for DISTINCT modifier")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and normalize function name."""
        return v.upper()  # Normalize to uppercase

    @model_validator(mode="after")
    def validate_function_call(self) -> "FunctionCall":
        """Validate function call constraints."""
        # COUNT(*) should have empty args
        # For now, just validate that args is a list
        if not isinstance(self.args, list):
            raise ValueError("Function args must be a list")
        return self

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class CaseExpression(BaseModel):
    """CASE expression for conditional logic.

    Examples:
        CASE WHEN n.age < 18 THEN 'minor' ELSE 'adult' END
        CASE WHEN n.status = 'active' THEN 1 WHEN n.status = 'pending' THEN 2 ELSE 0 END
    """

    when_clauses: list[tuple[Any, Any]] = Field(
        ..., min_length=1, description="List of (condition, result) tuples"
    )
    else_expr: Any | None = Field(default=None, description="Optional ELSE expression")

    @field_validator("when_clauses")
    @classmethod
    def validate_when_clauses(cls, v: list[tuple[Any, Any]]) -> list[tuple[Any, Any]]:
        """Validate WHEN clauses format."""
        if not v:
            raise ValueError("CASE expression must have at least one WHEN clause")
        for i, clause in enumerate(v):
            if not isinstance(clause, tuple) or len(clause) != 2:
                raise ValueError(
                    f"WHEN clause {i} must be a tuple of (condition, result), got {clause}"
                )
        return v

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class ListComprehension(BaseModel):
    """List comprehension expression for filtering and transforming lists.

    Examples:
        [x IN [1,2,3] WHERE x > 1] → [2, 3]
        [x IN [1,2,3] | x * 2] → [2, 4, 6]
        [x IN [1,2,3] WHERE x > 1 | x * 2] → [4, 6]
    """

    variable: str = Field(..., min_length=1, description="Loop variable name")
    list_expr: Any = Field(..., description="Expression that evaluates to a list")
    filter_expr: Any | None = Field(default=None, description="Optional WHERE filter expression")
    map_expr: Any | None = Field(
        default=None, description="Optional transformation expression (after |)"
    )

    @field_validator("variable")
    @classmethod
    def validate_variable(cls, v: str) -> str:
        """Validate variable name."""
        if not v[0].isalpha() and v[0] != "_":
            raise ValueError(f"Variable must start with letter or underscore: {v}")
        return v

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class SubqueryExpression(BaseModel):
    """Subquery expression for EXISTS and COUNT.

    Examples:
        EXISTS { MATCH (p)-[:KNOWS]->() }
        COUNT { MATCH (p)-[:KNOWS]->() }
    """

    type: str = Field(..., description="Subquery type: EXISTS or COUNT")
    query: Any = Field(..., description="Nested query (CypherQuery AST)")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate subquery type."""
        if v not in ("EXISTS", "COUNT"):
            raise ValueError(f"Subquery type must be EXISTS or COUNT, got {v}")
        return v

    model_config = {"frozen": True, "arbitrary_types_allowed": True}


class QuantifierExpression(BaseModel):
    """List quantifier expression for all(), any(), none(), single().

    Examples:
        all(x IN [1,2,3] WHERE x > 0)
        any(x IN [1,2,3] WHERE x > 2)
        none(x IN [1,2,3] WHERE x < 0)
        single(x IN [1,2,3] WHERE x = 2)
    """

    quantifier: str = Field(..., description="Quantifier type: ALL, ANY, NONE, or SINGLE")
    variable: str = Field(..., min_length=1, description="Loop variable name")
    list_expr: Any = Field(..., description="Expression that evaluates to a list")
    predicate: Any = Field(..., description="Boolean predicate expression")

    @field_validator("quantifier")
    @classmethod
    def validate_quantifier(cls, v: str) -> str:
        """Validate quantifier type."""
        if v not in ("ALL", "ANY", "NONE", "SINGLE"):
            raise ValueError(f"Quantifier must be ALL, ANY, NONE, or SINGLE, got {v}")
        return v

    @field_validator("variable")
    @classmethod
    def validate_variable(cls, v: str) -> str:
        """Validate variable name."""
        if not v[0].isalpha() and v[0] != "_":
            raise ValueError(f"Variable must start with letter or underscore: {v}")
        return v

    model_config = {"frozen": True, "arbitrary_types_allowed": True}
