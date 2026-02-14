"""Tests for operator validation errors.

This module tests Pydantic validation on operator models to ensure
error paths are covered.
"""

from pydantic import ValidationError
import pytest

from graphforge.planner.operators import (
    Delete,
    ExpandEdges,
    ExpandMultiHop,
    ExpandVariableLength,
    Limit,
    Merge,
    OptionalExpandEdges,
    OptionalScanNodes,
    Remove,
    ScanNodes,
    Set,
    Skip,
    Subquery,
    Union,
    Unwind,
)


@pytest.mark.unit
class TestScanNodesValidation:
    """Test ScanNodes operator validation."""

    def test_invalid_variable_starts_with_digit(self):
        """ScanNodes rejects variable starting with digit."""
        with pytest.raises(ValidationError, match="Variable must start with letter or underscore"):
            ScanNodes(variable="1invalid", labels=None)

    def test_invalid_variable_starts_with_special_char(self):
        """ScanNodes rejects variable starting with special character."""
        with pytest.raises(ValidationError, match="Variable must start with letter or underscore"):
            ScanNodes(variable="$invalid", labels=None)

    def test_valid_variable_starts_with_underscore(self):
        """ScanNodes accepts variable starting with underscore."""
        op = ScanNodes(variable="_valid", labels=None)
        assert op.variable == "_valid"


@pytest.mark.unit
class TestOptionalScanNodesValidation:
    """Test OptionalScanNodes operator validation."""

    def test_invalid_variable_starts_with_digit(self):
        """OptionalScanNodes rejects variable starting with digit."""
        with pytest.raises(ValidationError, match="Variable must start with letter or underscore"):
            OptionalScanNodes(variable="1invalid", labels=None)

    def test_invalid_variable_starts_with_special_char(self):
        """OptionalScanNodes rejects variable starting with special character."""
        with pytest.raises(ValidationError, match="Variable must start with letter or underscore"):
            OptionalScanNodes(variable="@invalid", labels=None)

    def test_valid_variable_starts_with_underscore(self):
        """OptionalScanNodes accepts variable starting with underscore."""
        op = OptionalScanNodes(variable="_valid", labels=None)
        assert op.variable == "_valid"


@pytest.mark.unit
class TestExpandEdgesValidation:
    """Test ExpandEdges operator validation."""

    def test_invalid_direction(self):
        """ExpandEdges rejects invalid direction."""
        with pytest.raises(ValidationError, match="Direction must be one of"):
            ExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=[],
                direction="INVALID",
            )

    @pytest.mark.parametrize(
        "direction",
        ["OUT", "IN", "UNDIRECTED"],
        ids=["outgoing", "incoming", "undirected"],
    )
    def test_valid_directions(self, direction):
        """ExpandEdges accepts valid directions."""
        op = ExpandEdges(
            src_var="a",
            edge_var="r",
            dst_var="b",
            edge_types=[],
            direction=direction,
        )
        assert op.direction == direction


@pytest.mark.unit
class TestOptionalExpandEdgesValidation:
    """Test OptionalExpandEdges operator validation."""

    def test_invalid_direction(self):
        """OptionalExpandEdges rejects invalid direction."""
        with pytest.raises(ValidationError, match="Direction must be one of"):
            OptionalExpandEdges(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=[],
                direction="SIDEWAYS",
            )

    @pytest.mark.parametrize(
        "direction",
        ["OUT", "IN", "UNDIRECTED"],
        ids=["outgoing", "incoming", "undirected"],
    )
    def test_valid_directions(self, direction):
        """OptionalExpandEdges accepts valid directions."""
        op = OptionalExpandEdges(
            src_var="a",
            edge_var="r",
            dst_var="b",
            edge_types=[],
            direction=direction,
        )
        assert op.direction == direction


@pytest.mark.unit
class TestExpandVariableLengthValidation:
    """Test ExpandVariableLength operator validation."""

    def test_invalid_direction(self):
        """ExpandVariableLength rejects invalid direction."""
        with pytest.raises(ValidationError, match="Direction must be one of"):
            ExpandVariableLength(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=[],
                direction="DIAGONAL",
            )

    def test_negative_min_hops(self):
        """ExpandVariableLength rejects negative min_hops."""
        with pytest.raises(ValidationError, match="Minimum hops must be non-negative"):
            ExpandVariableLength(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=[],
                direction="OUT",
                min_hops=-1,
            )

    def test_negative_max_hops(self):
        """ExpandVariableLength rejects negative max_hops."""
        with pytest.raises(ValidationError, match="Maximum hops must be non-negative"):
            ExpandVariableLength(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=[],
                direction="OUT",
                min_hops=1,
                max_hops=-1,
            )

    def test_max_hops_less_than_min_hops(self):
        """ExpandVariableLength rejects max_hops < min_hops."""
        with pytest.raises(ValidationError, match="Maximum hops .* must be >= minimum hops"):
            ExpandVariableLength(
                src_var="a",
                edge_var="r",
                dst_var="b",
                edge_types=[],
                direction="OUT",
                min_hops=5,
                max_hops=2,
            )

    def test_valid_hop_range(self):
        """ExpandVariableLength accepts valid hop range."""
        op = ExpandVariableLength(
            src_var="a",
            edge_var="r",
            dst_var="b",
            edge_types=[],
            direction="OUT",
            min_hops=1,
            max_hops=5,
        )
        assert op.min_hops == 1
        assert op.max_hops == 5

    def test_zero_min_hops_valid(self):
        """ExpandVariableLength accepts zero min_hops."""
        op = ExpandVariableLength(
            src_var="a",
            edge_var="r",
            dst_var="b",
            edge_types=[],
            direction="OUT",
            min_hops=0,
        )
        assert op.min_hops == 0


@pytest.mark.unit
class TestExpandMultiHopValidation:
    """Test ExpandMultiHop operator validation (additional cases)."""

    def test_invalid_hop_tuple_format(self):
        """ExpandMultiHop rejects hop with wrong tuple length."""
        with pytest.raises(ValidationError):
            ExpandMultiHop(
                src_var="a",
                hops=[
                    ("incomplete", ["KNOWS"], "OUT"),  # Missing dst_var
                ],
                path_var="p",
            )

    def test_invalid_hop_not_tuple(self):
        """ExpandMultiHop rejects hop that's not a tuple."""
        with pytest.raises(ValidationError):
            ExpandMultiHop(
                src_var="a",
                hops=[
                    "not_a_tuple",  # type: ignore[list-item]
                ],
                path_var="p",
            )


@pytest.mark.unit
class TestSetValidation:
    """Test Set operator validation."""

    def test_invalid_set_item_not_tuple(self):
        """Set rejects items that aren't tuples."""

        with pytest.raises(ValidationError):
            Set(
                items=[
                    "not_a_tuple",  # type: ignore[list-item]
                ]
            )

    def test_invalid_set_item_wrong_length(self):
        """Set rejects tuples with wrong number of elements."""
        from graphforge.ast.expression import Literal

        with pytest.raises(ValidationError):
            Set(
                items=[
                    (Literal(value=1),),  # Missing second element
                ]
            )

    def test_valid_set_items(self):
        """Set accepts valid property assignment tuples."""
        from graphforge.ast.expression import Literal, PropertyAccess

        prop = PropertyAccess(variable="n", property="age")
        value = Literal(value=30)

        op = Set(items=[(prop, value)])
        assert len(op.items) == 1
        assert op.items[0][0] == prop
        assert op.items[0][1] == value


@pytest.mark.unit
class TestUnwindValidation:
    """Test Unwind operator validation."""

    def test_invalid_variable_starts_with_digit(self):
        """Unwind rejects variable starting with digit."""
        from graphforge.ast.expression import Literal

        with pytest.raises(ValidationError, match="Variable must start with letter or underscore"):
            Unwind(
                expression=Literal(value=[1, 2, 3]),
                variable="1invalid",
            )

    def test_invalid_variable_starts_with_special_char(self):
        """Unwind rejects variable starting with special character."""
        from graphforge.ast.expression import Literal

        with pytest.raises(ValidationError, match="Variable must start with letter or underscore"):
            Unwind(
                expression=Literal(value=[1, 2, 3]),
                variable="#invalid",
            )

    def test_valid_variable_starts_with_underscore(self):
        """Unwind accepts variable starting with underscore."""
        from graphforge.ast.expression import Literal

        op = Unwind(
            expression=Literal(value=[1, 2, 3]),
            variable="_valid",
        )
        assert op.variable == "_valid"


@pytest.mark.unit
class TestUnionValidation:
    """Test Union operator validation."""

    def test_union_with_zero_branches(self):
        """Union rejects empty branch list."""
        with pytest.raises(ValidationError):
            Union(branches=[])

    def test_union_with_one_branch(self):
        """Union rejects single branch."""
        with pytest.raises(ValidationError):
            Union(
                branches=[
                    [ScanNodes(variable="n", labels=None)],
                ]
            )

    def test_union_with_two_branches_valid(self):
        """Union accepts two or more branches."""
        op = Union(
            branches=[
                [ScanNodes(variable="n", labels=[["Person"]])],
                [ScanNodes(variable="n", labels=[["Company"]])],
            ]
        )
        assert len(op.branches) == 2

    def test_union_all_flag(self):
        """Union respects the all flag."""
        op = Union(
            branches=[
                [ScanNodes(variable="n", labels=[["Person"]])],
                [ScanNodes(variable="n", labels=[["Company"]])],
            ],
            all=True,
        )
        assert op.all is True


@pytest.mark.unit
class TestSubqueryValidation:
    """Test Subquery operator validation."""

    def test_invalid_expression_type(self):
        """Subquery rejects invalid expression_type."""
        with pytest.raises(ValidationError, match="must be one of"):
            Subquery(
                operators=[ScanNodes(variable="n", labels=None)],
                expression_type="INVALID",
            )

    @pytest.mark.parametrize(
        "expr_type",
        ["EXISTS", "COUNT"],
        ids=["exists", "count"],
    )
    def test_valid_expression_types(self, expr_type):
        """Subquery accepts valid expression types."""
        op = Subquery(
            operators=[ScanNodes(variable="n", labels=None)],
            expression_type=expr_type,
        )
        assert op.expression_type == expr_type


@pytest.mark.unit
class TestDeleteValidation:
    """Test Delete operator validation."""

    def test_delete_without_detach(self):
        """Delete defaults to detach=False."""
        op = Delete(variables=["n"])
        assert op.detach is False

    def test_delete_with_detach(self):
        """Delete accepts detach=True."""
        op = Delete(variables=["n"], detach=True)
        assert op.detach is True


@pytest.mark.unit
class TestMergeValidation:
    """Test Merge operator validation."""

    def test_merge_with_on_create(self):
        """Merge accepts on_create SetClause."""
        from graphforge.ast.clause import SetClause
        from graphforge.ast.expression import Literal, PropertyAccess
        from graphforge.ast.pattern import NodePattern

        patterns = [NodePattern(variable="n", labels=[["Person"]])]
        prop = PropertyAccess(variable="n", property="created")
        set_clause = SetClause(items=[(prop, Literal(value=True))])

        op = Merge(patterns=patterns, on_create=set_clause)
        assert op.on_create == set_clause

    def test_merge_with_on_match(self):
        """Merge accepts on_match SetClause."""
        from graphforge.ast.clause import SetClause
        from graphforge.ast.expression import Literal, PropertyAccess
        from graphforge.ast.pattern import NodePattern

        patterns = [NodePattern(variable="n", labels=[["Person"]])]
        prop = PropertyAccess(variable="n", property="matched")
        set_clause = SetClause(items=[(prop, Literal(value=True))])

        op = Merge(patterns=patterns, on_match=set_clause)
        assert op.on_match == set_clause


@pytest.mark.unit
class TestRemoveValidation:
    """Test Remove operator validation."""

    def test_remove_with_empty_items(self):
        """Remove requires at least one item."""
        with pytest.raises(ValidationError):
            Remove(items=[])


@pytest.mark.unit
class TestLimitSkipValidation:
    """Test Limit and Skip operator validation."""

    def test_limit_negative_count(self):
        """Limit rejects negative count."""
        with pytest.raises(ValidationError):
            Limit(count=-1)

    def test_skip_negative_count(self):
        """Skip rejects negative count."""
        with pytest.raises(ValidationError):
            Skip(count=-1)

    def test_limit_zero_valid(self):
        """Limit accepts zero count."""
        op = Limit(count=0)
        assert op.count == 0

    def test_skip_zero_valid(self):
        """Skip accepts zero count."""
        op = Skip(count=0)
        assert op.count == 0
