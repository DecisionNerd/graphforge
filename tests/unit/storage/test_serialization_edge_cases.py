"""Unit tests for serialization edge cases.

Tests for error handling and edge cases in serialization.
"""

import pytest

from graphforge.storage.serialization import (
    deserialize_cypher_value,
    deserialize_labels,
    deserialize_properties,
    serialize_cypher_value,
    serialize_labels,
    serialize_properties,
)
from graphforge.types.values import (
    CypherBool,
    CypherFloat,
    CypherInt,
    CypherList,
    CypherMap,
    CypherNull,
    CypherString,
)


class TestSerializationErrorHandling:
    """Tests for serialization error handling."""

    def test_serialize_unsupported_type(self):
        """Serializing unsupported CypherValue type raises TypeError."""

        # Create a fake CypherValue subclass
        class FakeCypherValue:
            pass

        fake_value = FakeCypherValue()

        with pytest.raises(TypeError, match="Cannot serialize CypherValue type"):
            serialize_cypher_value(fake_value)  # type: ignore[arg-type]

    def test_deserialize_unsupported_type(self):
        """Deserializing unsupported type string raises TypeError."""
        data = {"type": "unsupported_type", "value": 123}

        with pytest.raises(TypeError, match="Cannot deserialize type"):
            deserialize_cypher_value(data)


class TestEmptyDataHandling:
    """Tests for empty data handling."""

    def test_deserialize_empty_properties(self):
        """Deserializing empty bytes for properties returns empty dict."""
        result = deserialize_properties(b"")
        assert result == {}

    def test_deserialize_empty_labels(self):
        """Deserializing empty bytes for labels returns empty frozenset."""
        result = deserialize_labels(b"")
        assert result == frozenset()


class TestRoundTripSerialization:
    """Tests for round-trip serialization."""

    def test_serialize_deserialize_nested_list(self):
        """Nested list serializes and deserializes correctly."""
        nested_list = CypherList(
            [CypherInt(1), CypherList([CypherString("a"), CypherString("b")]), CypherInt(3)]
        )

        serialized = serialize_cypher_value(nested_list)
        deserialized = deserialize_cypher_value(serialized)

        assert isinstance(deserialized, CypherList)
        assert len(deserialized.value) == 3
        assert isinstance(deserialized.value[1], CypherList)

    def test_serialize_deserialize_nested_map(self):
        """Nested map serializes and deserializes correctly."""
        nested_map = CypherMap(
            {
                "outer": CypherMap({"inner": CypherInt(42)}),
                "list": CypherList([CypherBool(True), CypherNull()]),
            }
        )

        serialized = serialize_cypher_value(nested_map)
        deserialized = deserialize_cypher_value(serialized)

        assert isinstance(deserialized, CypherMap)
        assert isinstance(deserialized.value["outer"], CypherMap)
        assert isinstance(deserialized.value["list"], CypherList)

    def test_properties_round_trip(self):
        """Properties with various types round-trip correctly."""
        properties = {
            "name": CypherString("Alice"),
            "age": CypherInt(30),
            "salary": CypherFloat(50000.50),
            "active": CypherBool(True),
            "metadata": CypherNull(),
            "tags": CypherList([CypherString("admin"), CypherString("user")]),
        }

        serialized = serialize_properties(properties)
        deserialized = deserialize_properties(serialized)

        assert len(deserialized) == 6
        assert deserialized["name"].value == "Alice"
        assert deserialized["age"].value == 30
        assert isinstance(deserialized["metadata"], CypherNull)

    def test_labels_round_trip(self):
        """Labels serialize and deserialize correctly."""
        labels = frozenset(["Person", "Employee", "Manager"])

        serialized = serialize_labels(labels)
        deserialized = deserialize_labels(serialized)

        assert deserialized == labels
        assert isinstance(deserialized, frozenset)

    def test_empty_properties_round_trip(self):
        """Empty properties dict round-trips correctly."""
        properties = {}

        serialized = serialize_properties(properties)
        deserialized = deserialize_properties(serialized)

        assert deserialized == {}

    def test_empty_labels_round_trip(self):
        """Empty labels frozenset round-trips correctly."""
        labels = frozenset()

        serialized = serialize_labels(labels)
        deserialized = deserialize_labels(serialized)

        assert deserialized == frozenset()
