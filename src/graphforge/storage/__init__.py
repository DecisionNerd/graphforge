"""Storage backends for GraphForge.

This module contains storage implementations:
- In-memory graph store
- SQLite persistent storage backend
- TWO separate serialization systems (see below)

CRITICAL: Two Serialization Systems
====================================

GraphForge uses TWO separate serialization systems for different purposes:

1. SQLite + MessagePack (serialization.py)
   - For: Graph data (nodes, edges, properties)
   - Format: Binary MessagePack (fast, compact)
   - Types: CypherValue types (CypherInt, CypherString, etc.)
   - Storage: SQLite database files (*.db)
   - Use for: Runtime graph operations

2. Pydantic + JSON (pydantic_serialization.py)
   - For: Metadata, schemas, dataset definitions
   - Format: JSON (human-readable, validatable)
   - Types: Pydantic models (DatasetInfo, AST nodes, ontologies)
   - Storage: JSON metadata files (*.json)
   - Use for: Configuration and schema definitions

NEVER mix these systems:
- Don't serialize graph data with Pydantic (performance disaster)
- Don't serialize metadata with MessagePack (loses validation)

See CLAUDE.md "Two Serialization Systems" for detailed explanation.
"""

from graphforge.storage.memory import Graph
from graphforge.storage.pydantic_serialization import (
    deserialize_model,
    deserialize_model_from_json,
    deserialize_models_batch,
    load_model_from_file,
    load_models_batch_from_file,
    save_model_to_file,
    save_models_batch_to_file,
    serialize_model,
    serialize_model_to_json,
    serialize_models_batch,
)
from graphforge.storage.serialization import (
    deserialize_cypher_value,
    deserialize_labels,
    deserialize_properties,
    serialize_cypher_value,
    serialize_labels,
    serialize_properties,
)
from graphforge.storage.sqlite_backend import SQLiteBackend

__all__ = [
    "Graph",
    "SQLiteBackend",
    "deserialize_cypher_value",
    "deserialize_labels",
    "deserialize_model",
    "deserialize_model_from_json",
    "deserialize_models_batch",
    "deserialize_properties",
    "load_model_from_file",
    "load_models_batch_from_file",
    "save_model_to_file",
    "save_models_batch_to_file",
    "serialize_cypher_value",
    "serialize_labels",
    "serialize_model",
    "serialize_model_to_json",
    "serialize_models_batch",
    "serialize_properties",
]
