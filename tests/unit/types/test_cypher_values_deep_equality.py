"""Unit tests for CypherValue deep equality edge cases.

Tests for list and map equality with NULL handling.
"""

from graphforge.types.values import (
    CypherBool,
    CypherInt,
    CypherList,
    CypherMap,
    CypherNull,
    CypherString,
)


class TestListDeepEquality:
    """Tests for CypherList deep equality edge cases."""

    def test_list_different_lengths(self):
        """Lists with different lengths are not equal."""
        list1 = CypherList([CypherInt(1), CypherInt(2)])
        list2 = CypherList([CypherInt(1), CypherInt(2), CypherInt(3)])

        result = list1.equals(list2)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_list_element_equals_null(self):
        """List comparison returns NULL if any element comparison is NULL."""
        list1 = CypherList([CypherInt(1), CypherNull()])
        list2 = CypherList([CypherInt(1), CypherInt(2)])

        result = list1.equals(list2)
        # When comparing with NULL, result should be NULL
        assert isinstance(result, CypherNull)

    def test_list_element_not_equal(self):
        """List comparison returns false if elements don't match."""
        list1 = CypherList([CypherInt(1), CypherInt(2)])
        list2 = CypherList([CypherInt(1), CypherInt(999)])

        result = list1.equals(list2)
        assert isinstance(result, CypherBool)
        assert result.value is False


class TestMapDeepEquality:
    """Tests for CypherMap deep equality edge cases."""

    def test_map_different_keys(self):
        """Maps with different keys are not equal."""
        map1 = CypherMap({"a": CypherInt(1), "b": CypherInt(2)})
        map2 = CypherMap({"a": CypherInt(1), "c": CypherInt(2)})

        result = map1.equals(map2)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_map_value_equals_null(self):
        """Map comparison returns NULL if any value comparison is NULL."""
        map1 = CypherMap({"a": CypherInt(1), "b": CypherNull()})
        map2 = CypherMap({"a": CypherInt(1), "b": CypherInt(2)})

        result = map1.equals(map2)
        # When comparing with NULL, result should be NULL
        assert isinstance(result, CypherNull)

    def test_map_value_not_equal(self):
        """Map comparison returns false if values don't match."""
        map1 = CypherMap({"a": CypherInt(1), "b": CypherInt(2)})
        map2 = CypherMap({"a": CypherInt(1), "b": CypherInt(999)})

        result = map1.equals(map2)
        assert isinstance(result, CypherBool)
        assert result.value is False


class TestUnsupportedComparisons:
    """Tests for unsupported comparison operations."""

    def test_less_than_unsupported_types(self):
        """Less than comparison between unsupported types returns false."""
        # String vs Int is not supported
        str_val = CypherString("hello")
        int_val = CypherInt(5)

        result = str_val.less_than(int_val)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_deep_equals_unsupported_collection(self):
        """Deep equals on unsupported collection types returns false."""
        # Test comparing different collection types (list vs map)
        list_val = CypherList([CypherInt(1)])
        map_val = CypherMap({"a": CypherInt(1)})

        result = list_val.equals(map_val)
        assert isinstance(result, CypherBool)
        assert result.value is False
