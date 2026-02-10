"""Unit tests for ExpandMultiHop operator."""

from pydantic import ValidationError
import pytest

from graphforge.planner.operators import ExpandMultiHop


class TestExpandMultiHopOperator:
    """Test ExpandMultiHop operator validation."""

    def test_valid_expand_multi_hop(self):
        """Test creating valid ExpandMultiHop operator."""
        op = ExpandMultiHop(
            src_var="a",
            hops=[
                ("r1", ["KNOWS"], "OUT", "b"),
                ("r2", ["LIKES"], "OUT", "c"),
            ],
            path_var="p",
        )

        assert op.src_var == "a"
        assert len(op.hops) == 2
        assert op.path_var == "p"

    def test_expand_multi_hop_without_path_var(self):
        """Test ExpandMultiHop without path variable."""
        op = ExpandMultiHop(
            src_var="a",
            hops=[
                (None, ["KNOWS"], "OUT", "b"),
            ],
            path_var=None,
        )

        assert op.path_var is None

    def test_expand_multi_hop_with_anonymous_edges(self):
        """Test ExpandMultiHop with anonymous edge variables."""
        op = ExpandMultiHop(
            src_var="a",
            hops=[
                (None, ["KNOWS"], "OUT", "b"),
                (None, ["LIKES"], "OUT", "c"),
            ],
            path_var="p",
        )

        assert op.hops[0][0] is None
        assert op.hops[1][0] is None

    def test_expand_multi_hop_empty_type_list(self):
        """Test ExpandMultiHop with empty relationship types (matches any)."""
        op = ExpandMultiHop(
            src_var="a",
            hops=[
                (None, [], "OUT", "b"),
            ],
            path_var="p",
        )

        assert op.hops[0][1] == []

    def test_expand_multi_hop_invalid_direction(self):
        """Test ExpandMultiHop validation fails for invalid direction."""
        with pytest.raises(ValidationError):
            ExpandMultiHop(
                src_var="a",
                hops=[
                    (None, ["KNOWS"], "INVALID", "b"),
                ],
                path_var="p",
            )

    def test_expand_multi_hop_invalid_src_var(self):
        """Test ExpandMultiHop validation fails for empty src_var."""
        with pytest.raises(ValidationError):
            ExpandMultiHop(
                src_var="",
                hops=[
                    (None, ["KNOWS"], "OUT", "b"),
                ],
                path_var="p",
            )

    def test_expand_multi_hop_invalid_hop_format(self):
        """Test ExpandMultiHop validation fails for invalid hop format."""
        with pytest.raises(ValidationError):
            ExpandMultiHop(
                src_var="a",
                hops=[
                    ("incomplete_tuple",),  # Wrong number of elements
                ],
                path_var="p",
            )

    def test_expand_multi_hop_empty_hops(self):
        """Test ExpandMultiHop validation fails for empty hops."""
        with pytest.raises(ValidationError):
            ExpandMultiHop(
                src_var="a",
                hops=[],
                path_var="p",
            )

    def test_expand_multi_hop_multiple_relationship_types(self):
        """Test ExpandMultiHop with multiple relationship types per hop."""
        op = ExpandMultiHop(
            src_var="a",
            hops=[
                (None, ["KNOWS", "LIKES"], "OUT", "b"),
            ],
            path_var="p",
        )

        assert op.hops[0][1] == ["KNOWS", "LIKES"]

    def test_expand_multi_hop_undirected(self):
        """Test ExpandMultiHop with undirected relationships."""
        op = ExpandMultiHop(
            src_var="a",
            hops=[
                (None, ["KNOWS"], "UNDIRECTED", "b"),
            ],
            path_var="p",
        )

        assert op.hops[0][2] == "UNDIRECTED"

    def test_expand_multi_hop_in_direction(self):
        """Test ExpandMultiHop with incoming relationships."""
        op = ExpandMultiHop(
            src_var="a",
            hops=[
                (None, ["KNOWS"], "IN", "b"),
            ],
            path_var="p",
        )

        assert op.hops[0][2] == "IN"

    def test_expand_multi_hop_three_hops(self):
        """Test ExpandMultiHop with three hops."""
        op = ExpandMultiHop(
            src_var="a",
            hops=[
                ("r1", ["R1"], "OUT", "b"),
                ("r2", ["R2"], "OUT", "c"),
                ("r3", ["R3"], "OUT", "d"),
            ],
            path_var="p",
        )

        assert len(op.hops) == 3
        assert op.hops[2][3] == "d"

    def test_expand_multi_hop_immutable(self):
        """Test ExpandMultiHop is immutable."""
        op = ExpandMultiHop(
            src_var="a",
            hops=[
                (None, ["KNOWS"], "OUT", "b"),
            ],
            path_var="p",
        )

        with pytest.raises((ValidationError, AttributeError)):
            op.src_var = "changed"
