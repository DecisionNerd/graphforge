"""Unit tests for CypherValue edge cases.

Tests for type comparison, coercion, and edge cases.
"""

import pytest

from graphforge.types.values import (
    CypherBool,
    CypherFloat,
    CypherInt,
    CypherList,
    CypherMap,
    CypherNull,
    CypherString,
)


class TestCypherValueComparisons:
    """Tests for CypherValue comparison operations."""

    def test_cypher_int_less_than_float(self):
        """CypherInt < CypherFloat comparison."""
        int_val = CypherInt(5)
        float_val = CypherFloat(5.5)

        result = int_val.less_than(float_val)
        assert result.value is True

    def test_cypher_float_less_than_int(self):
        """CypherFloat < CypherInt comparison."""
        float_val = CypherFloat(4.5)
        int_val = CypherInt(5)

        result = float_val.less_than(int_val)
        assert result.value is True

    def test_cypher_string_comparison(self):
        """CypherString comparison."""
        str1 = CypherString("apple")
        str2 = CypherString("banana")

        result = str1.less_than(str2)
        assert result.value is True

        result = str2.less_than(str1)
        assert result.value is False

    def test_cypher_null_comparison(self):
        """NULL comparisons return NULL."""
        null_val = CypherNull()
        int_val = CypherInt(5)

        result = null_val.less_than(int_val)
        assert isinstance(result, CypherNull)

        result = int_val.less_than(null_val)
        assert isinstance(result, CypherNull)

    def test_cypher_bool_to_python(self):
        """CypherBool to Python conversion."""
        true_val = CypherBool(True)
        false_val = CypherBool(False)

        assert true_val.to_python() is True
        assert false_val.to_python() is False

    def test_cypher_list_to_python(self):
        """CypherList to Python list conversion."""
        cypher_list = CypherList([CypherInt(1), CypherInt(2), CypherInt(3)])
        python_list = cypher_list.to_python()

        assert python_list == [1, 2, 3]
        assert isinstance(python_list, list)

    def test_cypher_map_to_python(self):
        """CypherMap to Python dict conversion."""
        cypher_map = CypherMap({"name": CypherString("Alice"), "age": CypherInt(30)})
        python_dict = cypher_map.to_python()

        assert python_dict == {"name": "Alice", "age": 30}
        assert isinstance(python_dict, dict)

    def test_cypher_null_to_python(self):
        """CypherNull to Python None conversion."""
        null_val = CypherNull()
        assert null_val.to_python() is None

    def test_cypher_int_equality(self):
        """CypherInt equality comparison."""
        int1 = CypherInt(5)
        int2 = CypherInt(5)
        int3 = CypherInt(10)

        result = int1.equals(int2)
        assert result.value is True

        result = int1.equals(int3)
        assert result.value is False

    def test_cypher_float_equality(self):
        """CypherFloat equality comparison."""
        float1 = CypherFloat(5.5)
        float2 = CypherFloat(5.5)
        float3 = CypherFloat(5.6)

        result = float1.equals(float2)
        assert result.value is True

        result = float1.equals(float3)
        assert result.value is False

    def test_cypher_string_equality(self):
        """CypherString equality comparison."""
        str1 = CypherString("hello")
        str2 = CypherString("hello")
        str3 = CypherString("world")

        result = str1.equals(str2)
        assert result.value is True

        result = str1.equals(str3)
        assert result.value is False

    def test_cypher_bool_equality(self):
        """CypherBool equality comparison."""
        true1 = CypherBool(True)
        true2 = CypherBool(True)
        false1 = CypherBool(False)

        result = true1.equals(true2)
        assert result.value is True

        result = true1.equals(false1)
        assert result.value is False

    def test_cypher_null_equality(self):
        """NULL equality returns NULL."""
        null1 = CypherNull()
        null2 = CypherNull()
        int_val = CypherInt(5)

        result = null1.equals(null2)
        assert isinstance(result, CypherNull)

        result = null1.equals(int_val)
        assert isinstance(result, CypherNull)

    def test_cypher_list_equality(self):
        """CypherList equality comparison."""
        list1 = CypherList([CypherInt(1), CypherInt(2)])
        list2 = CypherList([CypherInt(1), CypherInt(2)])
        list3 = CypherList([CypherInt(1), CypherInt(3)])

        result = list1.equals(list2)
        assert result.value is True

        result = list1.equals(list3)
        assert result.value is False

    def test_cypher_map_equality(self):
        """CypherMap equality comparison."""
        map1 = CypherMap({"a": CypherInt(1)})
        map2 = CypherMap({"a": CypherInt(1)})
        map3 = CypherMap({"a": CypherInt(2)})

        result = map1.equals(map2)
        assert result.value is True

        result = map1.equals(map3)
        assert result.value is False

    def test_mixed_type_equality(self):
        """Equality between different types returns false."""
        int_val = CypherInt(5)
        str_val = CypherString("5")

        result = int_val.equals(str_val)
        assert result.value is False
