"""Unit tests for list subscript and slice operations."""

import pytest

from graphforge.api import GraphForge


@pytest.fixture
def gf():
    """Create a fresh GraphForge instance."""
    return GraphForge()


class TestListIndexAccess:
    """Tests for list[index] operations."""

    def test_index_first_element(self, gf):
        """Access first element with index 0."""
        result = gf.execute("RETURN [1, 2, 3][0] AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 1

    def test_index_middle_element(self, gf):
        """Access middle element."""
        result = gf.execute("RETURN [1, 2, 3][1] AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 2

    def test_index_last_element(self, gf):
        """Access last element with positive index."""
        result = gf.execute("RETURN [1, 2, 3][2] AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 3

    def test_index_negative_last(self, gf):
        """Access last element with negative index -1."""
        result = gf.execute("RETURN [1, 2, 3][-1] AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 3

    def test_index_negative_first(self, gf):
        """Access first element with negative index -3."""
        result = gf.execute("RETURN [1, 2, 3][-3] AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 1

    def test_index_negative_middle(self, gf):
        """Access middle element with negative index."""
        result = gf.execute("RETURN [1, 2, 3][-2] AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 2

    def test_index_out_of_bounds_positive(self, gf):
        """Out of bounds positive index returns NULL."""
        result = gf.execute("RETURN [1, 2, 3][10] AS result")
        assert len(result) == 1
        assert result[0]["result"].value is None

    def test_index_out_of_bounds_negative(self, gf):
        """Out of bounds negative index returns NULL."""
        result = gf.execute("RETURN [1, 2, 3][-10] AS result")
        assert len(result) == 1
        assert result[0]["result"].value is None

    def test_index_empty_list(self, gf):
        """Indexing empty list returns NULL."""
        result = gf.execute("RETURN [][0] AS result")
        assert len(result) == 1
        assert result[0]["result"].value is None

    def test_index_null_list(self, gf):
        """Indexing NULL list returns NULL."""
        result = gf.execute("WITH null AS x RETURN x[0] AS result")
        assert len(result) == 1
        assert result[0]["result"].value is None

    def test_index_null_index(self, gf):
        """NULL index returns NULL."""
        result = gf.execute("RETURN [1, 2, 3][null] AS result")
        assert len(result) == 1
        assert result[0]["result"].value is None

    def test_index_string_elements(self, gf):
        """Index access on list of strings."""
        result = gf.execute("RETURN ['a', 'b', 'c'][1] AS result")
        assert len(result) == 1
        assert result[0]["result"].value == "b"

    def test_index_mixed_types(self, gf):
        """Index access on list with mixed types."""
        result = gf.execute("RETURN [1, 'two', 3.0][1] AS result")
        assert len(result) == 1
        assert result[0]["result"].value == "two"

    def test_index_nested_list(self, gf):
        """Index access on nested list."""
        result = gf.execute("RETURN [[1, 2], [3, 4]][0] AS result")
        assert len(result) == 1
        inner_list = result[0]["result"].value
        assert len(inner_list) == 2
        assert inner_list[0].value == 1
        assert inner_list[1].value == 2


class TestListSliceOperations:
    """Tests for list[start..end] slice operations."""

    def test_slice_range(self, gf):
        """Slice with start and end."""
        result = gf.execute("RETURN [1, 2, 3, 4, 5][1..3] AS result")
        assert len(result) == 1
        values = [v.value for v in result[0]["result"].value]
        assert values == [2, 3]

    def test_slice_from_start(self, gf):
        """Slice from beginning with ..end."""
        result = gf.execute("RETURN [1, 2, 3, 4, 5][..3] AS result")
        assert len(result) == 1
        values = [v.value for v in result[0]["result"].value]
        assert values == [1, 2, 3]

    def test_slice_to_end(self, gf):
        """Slice to end with start.."""
        result = gf.execute("RETURN [1, 2, 3, 4, 5][2..] AS result")
        assert len(result) == 1
        values = [v.value for v in result[0]["result"].value]
        assert values == [3, 4, 5]

    def test_slice_full_list(self, gf):
        """Slice entire list with [..]."""
        result = gf.execute("RETURN [1, 2, 3][..] AS result")
        assert len(result) == 1
        values = [v.value for v in result[0]["result"].value]
        assert values == [1, 2, 3]

    def test_slice_negative_start(self, gf):
        """Slice with negative start index."""
        result = gf.execute("RETURN [1, 2, 3, 4, 5][-3..] AS result")
        assert len(result) == 1
        values = [v.value for v in result[0]["result"].value]
        assert values == [3, 4, 5]

    def test_slice_negative_end(self, gf):
        """Slice with negative end index."""
        result = gf.execute("RETURN [1, 2, 3, 4, 5][..-2] AS result")
        assert len(result) == 1
        values = [v.value for v in result[0]["result"].value]
        assert values == [1, 2, 3]

    def test_slice_negative_both(self, gf):
        """Slice with negative start and end."""
        result = gf.execute("RETURN [1, 2, 3, 4, 5][-4..-1] AS result")
        assert len(result) == 1
        values = [v.value for v in result[0]["result"].value]
        assert values == [2, 3, 4]

    def test_slice_empty_result(self, gf):
        """Slice with start >= end returns empty list."""
        result = gf.execute("RETURN [1, 2, 3][2..1] AS result")
        assert len(result) == 1
        assert result[0]["result"].value == []

    def test_slice_out_of_bounds(self, gf):
        """Slice with out of bounds indices is clamped."""
        result = gf.execute("RETURN [1, 2, 3][1..10] AS result")
        assert len(result) == 1
        values = [v.value for v in result[0]["result"].value]
        assert values == [2, 3]

    def test_slice_empty_list(self, gf):
        """Slicing empty list returns empty list."""
        result = gf.execute("RETURN [][1..3] AS result")
        assert len(result) == 1
        assert result[0]["result"].value == []

    def test_slice_null_list(self, gf):
        """Slicing NULL list returns NULL."""
        result = gf.execute("WITH null AS x RETURN x[1..3] AS result")
        assert len(result) == 1
        assert result[0]["result"].value is None

    def test_slice_null_start(self, gf):
        """NULL start in slice returns NULL."""
        result = gf.execute("RETURN [1, 2, 3][null..2] AS result")
        assert len(result) == 1
        assert result[0]["result"].value is None

    def test_slice_null_end(self, gf):
        """NULL end in slice returns NULL."""
        result = gf.execute("RETURN [1, 2, 3][1..null] AS result")
        assert len(result) == 1
        assert result[0]["result"].value is None

    def test_slice_strings(self, gf):
        """Slice list of strings."""
        result = gf.execute("RETURN ['a', 'b', 'c', 'd'][1..3] AS result")
        assert len(result) == 1
        values = [v.value for v in result[0]["result"].value]
        assert values == ["b", "c"]


class TestListSubscriptChaining:
    """Tests for chaining subscript operations."""

    def test_nested_index_access(self, gf):
        """Chain two index operations on nested list."""
        result = gf.execute("RETURN [[1, 2], [3, 4]][0][1] AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 2

    def test_slice_then_index(self, gf):
        """Slice list then index into result."""
        result = gf.execute("RETURN [1, 2, 3, 4, 5][1..4][1] AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 3


class TestSubscriptWithVariables:
    """Tests for subscript operations with variables."""

    def test_index_from_variable(self, gf):
        """Use variable for index."""
        gf.execute("CREATE (:Node {list: [1, 2, 3], idx: 1})")
        result = gf.execute("MATCH (n:Node) RETURN n.list[n.idx] AS result")
        assert len(result) == 1
        assert result[0]["result"].value == 2

    def test_slice_with_variable_bounds(self, gf):
        """Use variables for slice bounds."""
        gf.execute("CREATE (:Node {list: [1, 2, 3, 4, 5], start: 1, end: 3})")
        result = gf.execute("MATCH (n:Node) RETURN n.list[n.start..n.end] AS result")
        assert len(result) == 1
        values = [v.value for v in result[0]["result"].value]
        assert values == [2, 3]


class TestSubscriptErrorCases:
    """Tests for error conditions."""

    def test_subscript_non_list(self, gf):
        """Subscripting non-list raises TypeError."""
        with pytest.raises(TypeError, match="Subscript operation requires list"):
            gf.execute("WITH 'hello' AS x RETURN x[0] AS result")

    def test_non_integer_index(self, gf):
        """Non-integer index raises TypeError."""
        with pytest.raises(TypeError, match="List index must be integer"):
            gf.execute("RETURN [1, 2, 3]['x'] AS result")

    def test_non_integer_slice_start(self, gf):
        """Non-integer slice start raises TypeError."""
        with pytest.raises(TypeError, match="Slice start must be integer"):
            gf.execute("RETURN [1, 2, 3]['x'..2] AS result")

    def test_non_integer_slice_end(self, gf):
        """Non-integer slice end raises TypeError."""
        with pytest.raises(TypeError, match="Slice end must be integer"):
            gf.execute("RETURN [1, 2, 3][1..'x'] AS result")
