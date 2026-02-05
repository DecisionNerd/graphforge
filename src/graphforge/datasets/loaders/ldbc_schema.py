"""LDBC Social Network Benchmark schema definitions.

Defines the schema for LDBC SNB datasets including:
- Node types (Person, Post, Comment, Forum, etc.)
- Relationship types (KNOWS, LIKES, HAS_CREATOR, etc.)
- Property mappings with types
- CSV column mappings

References:
- https://ldbcouncil.org/ldbc_snb_docs/ldbc-snb-specification.pdf
- https://github.com/ldbc/ldbc_snb_datagen_hadoop
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass
class PropertyMapping:
    """Mapping for a single property from CSV column to graph property.

    Attributes:
        csv_column: Name of the column in the CSV file
        property_name: Name of the property in the graph
        type_converter: Function to convert string value to proper type
        required: Whether this property must be present
    """

    csv_column: str
    property_name: str
    type_converter: Callable[[str], Any]
    required: bool = True


@dataclass
class NodeSchema:
    """Schema definition for a node type.

    Attributes:
        label: Node label (e.g., "Person", "Post")
        csv_file: Name of the CSV file containing this node type
        id_column: Name of the column containing node IDs
        properties: List of property mappings
    """

    label: str
    csv_file: str
    id_column: str
    properties: list[PropertyMapping]


@dataclass
class RelationshipSchema:
    """Schema definition for a relationship type.

    Attributes:
        type: Relationship type (e.g., "KNOWS", "LIKES")
        csv_file: Name of the CSV file containing this relationship type
        source_id_column: Name of the column containing source node IDs
        target_id_column: Name of the column containing target node IDs
        source_label: Label of source nodes
        target_label: Label of target nodes
        properties: List of property mappings
    """

    type: str
    csv_file: str
    source_id_column: str
    target_id_column: str
    source_label: str
    target_label: str
    properties: list[PropertyMapping]


def parse_datetime(value: str) -> datetime:
    """Parse LDBC datetime format: YYYY-MM-DDThh:mm:ss.sss+0000"""
    # LDBC uses ISO 8601 format
    return datetime.fromisoformat(value.replace("+0000", "+00:00"))


def parse_date(value: str) -> date:
    """Parse LDBC date format: YYYY-MM-DD"""
    return date.fromisoformat(value)


def parse_int(value: str) -> int:
    """Parse integer value."""
    return int(value)


def parse_float(value: str) -> float:
    """Parse float value."""
    return float(value)


def parse_string(value: str) -> str:
    """Parse string value (passthrough)."""
    return value


def parse_list(value: str) -> list[str]:
    """Parse semicolon-separated list."""
    if not value or value == "":
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


# LDBC SNB Node Schemas

PERSON_SCHEMA = NodeSchema(
    label="Person",
    csv_file="person_0_0.csv",
    id_column="id",
    properties=[
        PropertyMapping("firstName", "firstName", parse_string),
        PropertyMapping("lastName", "lastName", parse_string),
        PropertyMapping("gender", "gender", parse_string),
        PropertyMapping("birthday", "birthday", parse_date),
        PropertyMapping("creationDate", "creationDate", parse_datetime),
        PropertyMapping("locationIP", "locationIP", parse_string),
        PropertyMapping("browserUsed", "browserUsed", parse_string),
        PropertyMapping("language", "languages", parse_list, required=False),
        PropertyMapping("email", "emails", parse_list, required=False),
    ],
)

POST_SCHEMA = NodeSchema(
    label="Post",
    csv_file="post_0_0.csv",
    id_column="id",
    properties=[
        PropertyMapping("imageFile", "imageFile", parse_string, required=False),
        PropertyMapping("creationDate", "creationDate", parse_datetime),
        PropertyMapping("locationIP", "locationIP", parse_string),
        PropertyMapping("browserUsed", "browserUsed", parse_string),
        PropertyMapping("language", "language", parse_string, required=False),
        PropertyMapping("content", "content", parse_string, required=False),
        PropertyMapping("length", "length", parse_int),
    ],
)

COMMENT_SCHEMA = NodeSchema(
    label="Comment",
    csv_file="comment_0_0.csv",
    id_column="id",
    properties=[
        PropertyMapping("creationDate", "creationDate", parse_datetime),
        PropertyMapping("locationIP", "locationIP", parse_string),
        PropertyMapping("browserUsed", "browserUsed", parse_string),
        PropertyMapping("content", "content", parse_string, required=False),
        PropertyMapping("length", "length", parse_int),
    ],
)

FORUM_SCHEMA = NodeSchema(
    label="Forum",
    csv_file="forum_0_0.csv",
    id_column="id",
    properties=[
        PropertyMapping("title", "title", parse_string),
        PropertyMapping("creationDate", "creationDate", parse_datetime),
    ],
)

ORGANISATION_SCHEMA = NodeSchema(
    label="Organisation",
    csv_file="organisation_0_0.csv",
    id_column="id",
    properties=[
        PropertyMapping("type", "type", parse_string),
        PropertyMapping("name", "name", parse_string),
        PropertyMapping("url", "url", parse_string),
    ],
)

PLACE_SCHEMA = NodeSchema(
    label="Place",
    csv_file="place_0_0.csv",
    id_column="id",
    properties=[
        PropertyMapping("name", "name", parse_string),
        PropertyMapping("url", "url", parse_string),
        PropertyMapping("type", "type", parse_string),
    ],
)

TAG_SCHEMA = NodeSchema(
    label="Tag",
    csv_file="tag_0_0.csv",
    id_column="id",
    properties=[
        PropertyMapping("name", "name", parse_string),
        PropertyMapping("url", "url", parse_string),
    ],
)

TAGCLASS_SCHEMA = NodeSchema(
    label="TagClass",
    csv_file="tagclass_0_0.csv",
    id_column="id",
    properties=[
        PropertyMapping("name", "name", parse_string),
        PropertyMapping("url", "url", parse_string),
    ],
)

# LDBC SNB Relationship Schemas

KNOWS_SCHEMA = RelationshipSchema(
    type="KNOWS",
    csv_file="person_knows_person_0_0.csv",
    source_id_column="Person.id",
    target_id_column="Person.id.1",
    source_label="Person",
    target_label="Person",
    properties=[
        PropertyMapping("creationDate", "creationDate", parse_datetime),
    ],
)

LIKES_POST_SCHEMA = RelationshipSchema(
    type="LIKES",
    csv_file="person_likes_post_0_0.csv",
    source_id_column="Person.id",
    target_id_column="Post.id",
    source_label="Person",
    target_label="Post",
    properties=[
        PropertyMapping("creationDate", "creationDate", parse_datetime),
    ],
)

LIKES_COMMENT_SCHEMA = RelationshipSchema(
    type="LIKES",
    csv_file="person_likes_comment_0_0.csv",
    source_id_column="Person.id",
    target_id_column="Comment.id",
    source_label="Person",
    target_label="Comment",
    properties=[
        PropertyMapping("creationDate", "creationDate", parse_datetime),
    ],
)

# All node and relationship schemas
NODE_SCHEMAS = [
    PERSON_SCHEMA,
    POST_SCHEMA,
    COMMENT_SCHEMA,
    FORUM_SCHEMA,
    ORGANISATION_SCHEMA,
    PLACE_SCHEMA,
    TAG_SCHEMA,
    TAGCLASS_SCHEMA,
]

RELATIONSHIP_SCHEMAS = [
    KNOWS_SCHEMA,
    LIKES_POST_SCHEMA,
    LIKES_COMMENT_SCHEMA,
]
