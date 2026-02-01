"""Serialization layer for CypherValue types.

This module handles conversion between CypherValue types and bytes
for storage in SQLite.
"""

import msgpack

from graphforge.types.values import (
    CypherBool,
    CypherFloat,
    CypherInt,
    CypherList,
    CypherMap,
    CypherNull,
    CypherString,
)


def serialize_cypher_value(value) -> dict:
    """Serialize a CypherValue to a dict for msgpack.

    Args:
        value: CypherValue instance

    Returns:
        Dict with 'type' and 'value' keys
    """
    if isinstance(value, CypherNull):
        return {"type": "null"}

    if isinstance(value, CypherBool):
        return {"type": "bool", "value": value.value}

    if isinstance(value, CypherInt):
        return {"type": "int", "value": value.value}

    if isinstance(value, CypherFloat):
        return {"type": "float", "value": value.value}

    if isinstance(value, CypherString):
        return {"type": "string", "value": value.value}

    if isinstance(value, CypherList):
        return {
            "type": "list",
            "value": [serialize_cypher_value(item) for item in value.value],
        }

    if isinstance(value, CypherMap):
        return {
            "type": "map",
            "value": {key: serialize_cypher_value(val) for key, val in value.value.items()},
        }

    raise TypeError(f"Cannot serialize CypherValue type: {type(value).__name__}")


def deserialize_cypher_value(data: dict):
    """Deserialize a dict to a CypherValue.

    Args:
        data: Dict with 'type' and optional 'value' keys

    Returns:
        CypherValue instance
    """
    value_type = data["type"]

    if value_type == "null":
        return CypherNull()

    if value_type == "bool":
        return CypherBool(data["value"])

    if value_type == "int":
        return CypherInt(data["value"])

    if value_type == "float":
        return CypherFloat(data["value"])

    if value_type == "string":
        return CypherString(data["value"])

    if value_type == "list":
        return CypherList([deserialize_cypher_value(item) for item in data["value"]])

    if value_type == "map":
        return CypherMap({key: deserialize_cypher_value(val) for key, val in data["value"].items()})

    raise TypeError(f"Cannot deserialize type: {value_type}")


def serialize_properties(properties: dict) -> bytes:
    """Serialize a properties dict to bytes.

    Args:
        properties: Dict mapping str to CypherValue

    Returns:
        MessagePack encoded bytes
    """
    serialized = {key: serialize_cypher_value(val) for key, val in properties.items()}
    return msgpack.packb(serialized)  # type: ignore[no-any-return]


def deserialize_properties(data: bytes) -> dict:
    """Deserialize bytes to a properties dict.

    Args:
        data: MessagePack encoded bytes

    Returns:
        Dict mapping str to CypherValue
    """
    if not data:
        return {}

    unpacked = msgpack.unpackb(data)
    return {key: deserialize_cypher_value(val) for key, val in unpacked.items()}


def serialize_labels(labels: frozenset[str]) -> bytes:
    """Serialize labels to bytes.

    Args:
        labels: Frozenset of label strings

    Returns:
        MessagePack encoded bytes
    """
    return msgpack.packb(list(labels))  # type: ignore[no-any-return]


def deserialize_labels(data: bytes) -> frozenset[str]:
    """Deserialize bytes to labels.

    Args:
        data: MessagePack encoded bytes

    Returns:
        Frozenset of label strings
    """
    if not data:
        return frozenset()

    unpacked = msgpack.unpackb(data)
    return frozenset(unpacked)
