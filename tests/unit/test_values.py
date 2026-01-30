"""Tests for openCypher value types.

Tests cover the runtime value model including:
- Scalar types (null, int, float, bool, string)
- Collection types (list, map)
- Comparison and equality semantics
- Null propagation
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
    CypherType,
)


@pytest.mark.unit
class TestCypherNull:
    """Tests for CypherNull type."""

    def test_null_creation(self):
        """Null can be created."""
        null = CypherNull()
        assert null.type == CypherType.NULL
        assert null.value is None

    def test_null_equality_returns_null(self):
        """NULL = NULL should return NULL (not True)."""
        null1 = CypherNull()
        null2 = CypherNull()
        result = null1.equals(null2)
        assert isinstance(result, CypherNull)

    def test_null_comparison_returns_null(self):
        """NULL < NULL should return NULL."""
        null1 = CypherNull()
        null2 = CypherNull()
        result = null1.less_than(null2)
        assert isinstance(result, CypherNull)


@pytest.mark.unit
class TestCypherInt:
    """Tests for CypherInt type."""

    def test_int_creation(self):
        """Integer can be created with a value."""
        val = CypherInt(42)
        assert val.type == CypherType.INTEGER
        assert val.value == 42

    def test_int_equality(self):
        """Integers with same value are equal."""
        val1 = CypherInt(42)
        val2 = CypherInt(42)
        result = val1.equals(val2)
        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_int_inequality(self):
        """Integers with different values are not equal."""
        val1 = CypherInt(42)
        val2 = CypherInt(99)
        result = val1.equals(val2)
        assert isinstance(result, CypherBool)
        assert result.value is False

    def test_int_less_than(self):
        """Integer comparison works correctly."""
        val1 = CypherInt(42)
        val2 = CypherInt(99)
        result = val1.less_than(val2)
        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_int_with_null_returns_null(self):
        """42 = NULL should return NULL."""
        val = CypherInt(42)
        null = CypherNull()
        result = val.equals(null)
        assert isinstance(result, CypherNull)


@pytest.mark.unit
class TestCypherFloat:
    """Tests for CypherFloat type."""

    def test_float_creation(self):
        """Float can be created with a value."""
        val = CypherFloat(3.14)
        assert val.type == CypherType.FLOAT
        assert val.value == 3.14

    def test_float_equality(self):
        """Floats with same value are equal."""
        val1 = CypherFloat(3.14)
        val2 = CypherFloat(3.14)
        result = val1.equals(val2)
        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_float_comparison(self):
        """Float comparison works correctly."""
        val1 = CypherFloat(1.5)
        val2 = CypherFloat(2.5)
        result = val1.less_than(val2)
        assert isinstance(result, CypherBool)
        assert result.value is True


@pytest.mark.unit
class TestCypherBool:
    """Tests for CypherBool type."""

    def test_bool_true_creation(self):
        """Boolean true can be created."""
        val = CypherBool(True)
        assert val.type == CypherType.BOOLEAN
        assert val.value is True

    def test_bool_false_creation(self):
        """Boolean false can be created."""
        val = CypherBool(False)
        assert val.type == CypherType.BOOLEAN
        assert val.value is False

    def test_bool_equality(self):
        """Booleans with same value are equal."""
        val1 = CypherBool(True)
        val2 = CypherBool(True)
        result = val1.equals(val2)
        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_bool_inequality(self):
        """Booleans with different values are not equal."""
        val1 = CypherBool(True)
        val2 = CypherBool(False)
        result = val1.equals(val2)
        assert isinstance(result, CypherBool)
        assert result.value is False


@pytest.mark.unit
class TestCypherString:
    """Tests for CypherString type."""

    def test_string_creation(self):
        """String can be created with a value."""
        val = CypherString("hello")
        assert val.type == CypherType.STRING
        assert val.value == "hello"

    def test_string_equality(self):
        """Strings with same value are equal."""
        val1 = CypherString("hello")
        val2 = CypherString("hello")
        result = val1.equals(val2)
        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_string_comparison(self):
        """String comparison works lexicographically."""
        val1 = CypherString("apple")
        val2 = CypherString("banana")
        result = val1.less_than(val2)
        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_empty_string(self):
        """Empty string can be created."""
        val = CypherString("")
        assert val.value == ""


@pytest.mark.unit
class TestCypherList:
    """Tests for CypherList type."""

    def test_list_creation(self):
        """List can be created with elements."""
        val = CypherList([CypherInt(1), CypherInt(2), CypherInt(3)])
        assert val.type == CypherType.LIST
        assert len(val.value) == 3

    def test_empty_list(self):
        """Empty list can be created."""
        val = CypherList([])
        assert val.type == CypherType.LIST
        assert len(val.value) == 0

    def test_list_equality(self):
        """Lists with same elements are equal."""
        val1 = CypherList([CypherInt(1), CypherInt(2)])
        val2 = CypherList([CypherInt(1), CypherInt(2)])
        result = val1.equals(val2)
        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_list_with_null(self):
        """List can contain null values."""
        val = CypherList([CypherInt(1), CypherNull(), CypherInt(3)])
        assert len(val.value) == 3
        assert isinstance(val.value[1], CypherNull)


@pytest.mark.unit
class TestCypherMap:
    """Tests for CypherMap type."""

    def test_map_creation(self):
        """Map can be created with key-value pairs."""
        val = CypherMap({"name": CypherString("Alice"), "age": CypherInt(30)})
        assert val.type == CypherType.MAP
        assert len(val.value) == 2

    def test_empty_map(self):
        """Empty map can be created."""
        val = CypherMap({})
        assert val.type == CypherType.MAP
        assert len(val.value) == 0

    def test_map_equality(self):
        """Maps with same key-value pairs are equal."""
        val1 = CypherMap({"name": CypherString("Alice")})
        val2 = CypherMap({"name": CypherString("Alice")})
        result = val1.equals(val2)
        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_map_with_null_value(self):
        """Map can have null values."""
        val = CypherMap({"name": CypherString("Alice"), "age": CypherNull()})
        assert isinstance(val.value["age"], CypherNull)


@pytest.mark.unit
class TestMixedTypeComparisons:
    """Tests for comparisons between different types."""

    def test_int_float_equality(self):
        """Integer and float with same numeric value are equal."""
        val1 = CypherInt(42)
        val2 = CypherFloat(42.0)
        result = val1.equals(val2)
        assert isinstance(result, CypherBool)
        assert result.value is True

    def test_different_types_not_equal(self):
        """Different types are not equal."""
        val1 = CypherString("42")
        val2 = CypherInt(42)
        result = val1.equals(val2)
        assert isinstance(result, CypherBool)
        assert result.value is False


@pytest.mark.unit
class TestPythonConversion:
    """Tests for converting to/from Python values."""

    def test_to_python_int(self):
        """CypherInt can be converted to Python int."""
        val = CypherInt(42)
        assert val.to_python() == 42

    def test_to_python_null(self):
        """CypherNull converts to Python None."""
        val = CypherNull()
        assert val.to_python() is None

    def test_to_python_list(self):
        """CypherList converts to Python list."""
        val = CypherList([CypherInt(1), CypherInt(2)])
        result = val.to_python()
        assert result == [1, 2]

    def test_to_python_map(self):
        """CypherMap converts to Python dict."""
        val = CypherMap({"name": CypherString("Alice"), "age": CypherInt(30)})
        result = val.to_python()
        assert result == {"name": "Alice", "age": 30}

    def test_from_python_int(self):
        """Python int converts to CypherInt."""
        from graphforge.types.values import from_python

        val = from_python(42)
        assert isinstance(val, CypherInt)
        assert val.value == 42

    def test_from_python_none(self):
        """Python None converts to CypherNull."""
        from graphforge.types.values import from_python

        val = from_python(None)
        assert isinstance(val, CypherNull)

    def test_from_python_list(self):
        """Python list converts to CypherList."""
        from graphforge.types.values import from_python

        val = from_python([1, 2, 3])
        assert isinstance(val, CypherList)
        assert val.to_python() == [1, 2, 3]

    def test_from_python_dict(self):
        """Python dict converts to CypherMap."""
        from graphforge.types.values import from_python

        val = from_python({"name": "Alice", "age": 30})
        assert isinstance(val, CypherMap)
        assert val.to_python() == {"name": "Alice", "age": 30}

    def test_from_python_unsupported_type(self):
        """Unsupported Python type raises TypeError."""
        from graphforge.types.values import from_python

        with pytest.raises(TypeError, match="Cannot convert Python type"):
            from_python(object())
