"""Tests for logical plan operators.

Tests cover the operator data structures used in query planning.
"""

import pytest

from graphforge.planner.operators import (
    ExpandEdges,
    Filter,
    Limit,
    Project,
    ScanNodes,
    Skip,
)


@pytest.mark.unit
class TestScanNodes:
    """Tests for ScanNodes operator."""

    def test_scan_all_nodes(self):
        """ScanNodes can scan all nodes."""
        op = ScanNodes(variable="n", labels=None)
        assert op.variable == "n"
        assert op.labels is None

    def test_scan_by_label(self):
        """ScanNodes can filter by label."""
        op = ScanNodes(variable="n", labels=["Person"])
        assert op.variable == "n"
        assert "Person" in op.labels

    def test_scan_multiple_labels(self):
        """ScanNodes can filter by multiple labels."""
        op = ScanNodes(variable="n", labels=["Person", "Employee"])
        assert len(op.labels) == 2


@pytest.mark.unit
class TestExpandEdges:
    """Tests for ExpandEdges operator."""

    def test_expand_outgoing(self):
        """ExpandEdges can expand outgoing edges."""
        op = ExpandEdges(
            src_var="a",
            edge_var="r",
            dst_var="b",
            edge_types=["KNOWS"],
            direction="OUT",
        )
        assert op.src_var == "a"
        assert op.edge_var == "r"
        assert op.dst_var == "b"
        assert op.direction == "OUT"

    def test_expand_incoming(self):
        """ExpandEdges can expand incoming edges."""
        op = ExpandEdges(
            src_var="a",
            edge_var="r",
            dst_var="b",
            edge_types=["KNOWS"],
            direction="IN",
        )
        assert op.direction == "IN"

    def test_expand_undirected(self):
        """ExpandEdges can expand undirected edges."""
        op = ExpandEdges(
            src_var="a",
            edge_var="r",
            dst_var="b",
            edge_types=["KNOWS"],
            direction="UNDIRECTED",
        )
        assert op.direction == "UNDIRECTED"

    def test_expand_multiple_types(self):
        """ExpandEdges can match multiple edge types."""
        op = ExpandEdges(
            src_var="a",
            edge_var="r",
            dst_var="b",
            edge_types=["KNOWS", "LIKES"],
            direction="OUT",
        )
        assert len(op.edge_types) == 2


@pytest.mark.unit
class TestFilter:
    """Tests for Filter operator."""

    def test_filter_with_predicate(self):
        """Filter contains a predicate expression."""
        from graphforge.ast.expression import BinaryOp, Literal, PropertyAccess

        predicate = BinaryOp(
            op=">",
            left=PropertyAccess(variable="n", property="age"),
            right=Literal(30),
        )
        op = Filter(predicate=predicate)
        assert op.predicate.op == ">"


@pytest.mark.unit
class TestProject:
    """Tests for Project operator."""

    def test_project_single_item(self):
        """Project can project single item."""
        from graphforge.ast.expression import Variable

        op = Project(items=[Variable("n")])
        assert len(op.items) == 1

    def test_project_multiple_items(self):
        """Project can project multiple items."""
        from graphforge.ast.expression import PropertyAccess, Variable

        op = Project(
            items=[
                Variable("n"),
                PropertyAccess(variable="n", property="name"),
            ]
        )
        assert len(op.items) == 2


@pytest.mark.unit
class TestLimit:
    """Tests for Limit operator."""

    def test_limit_count(self):
        """Limit specifies row count."""
        op = Limit(count=10)
        assert op.count == 10


@pytest.mark.unit
class TestSkip:
    """Tests for Skip operator."""

    def test_skip_count(self):
        """Skip specifies offset count."""
        op = Skip(count=5)
        assert op.count == 5


@pytest.mark.unit
class TestOperatorChaining:
    """Tests for operator pipeline construction."""

    def test_simple_pipeline(self):
        """Operators can be chained together."""
        from graphforge.ast.expression import Variable

        scan = ScanNodes(variable="n", labels=["Person"])
        project = Project(items=[Variable("n")])
        limit = Limit(count=10)

        # Create pipeline
        pipeline = [scan, project, limit]
        assert len(pipeline) == 3
        assert isinstance(pipeline[0], ScanNodes)
        assert isinstance(pipeline[1], Project)
        assert isinstance(pipeline[2], Limit)
