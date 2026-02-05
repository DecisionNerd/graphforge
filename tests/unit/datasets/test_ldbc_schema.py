"""Unit tests for LDBC schema definitions."""

from datetime import date, datetime

import pytest

from graphforge.datasets.loaders.ldbc_schema import (
    COMMENT_SCHEMA,
    KNOWS_SCHEMA,
    LIKES_COMMENT_SCHEMA,
    LIKES_POST_SCHEMA,
    NODE_SCHEMAS,
    PERSON_SCHEMA,
    POST_SCHEMA,
    RELATIONSHIP_SCHEMAS,
    parse_date,
    parse_datetime,
    parse_float,
    parse_int,
    parse_list,
    parse_string,
)

pytestmark = pytest.mark.unit


class TestTypeParsers:
    """Tests for type conversion functions."""

    def test_parse_string(self):
        """Test string parsing (passthrough)."""
        assert parse_string("hello") == "hello"
        assert parse_string("") == ""

    def test_parse_int(self):
        """Test integer parsing."""
        assert parse_int("42") == 42
        assert parse_int("0") == 0
        assert parse_int("-10") == -10

    def test_parse_int_invalid(self):
        """Test invalid integer raises error."""
        with pytest.raises(ValueError):
            parse_int("not a number")

    def test_parse_float(self):
        """Test float parsing."""
        assert parse_float("3.14") == 3.14
        assert parse_float("0.0") == 0.0
        assert parse_float("-2.5") == -2.5

    def test_parse_float_invalid(self):
        """Test invalid float raises error."""
        with pytest.raises(ValueError):
            parse_float("not a float")

    def test_parse_date(self):
        """Test date parsing."""
        result = parse_date("2023-01-15")
        assert result == date(2023, 1, 15)

    def test_parse_date_invalid(self):
        """Test invalid date raises error."""
        with pytest.raises(ValueError):
            parse_date("not a date")

    def test_parse_datetime(self):
        """Test datetime parsing."""
        result = parse_datetime("2023-01-15T10:30:00.000+0000")
        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_datetime_without_milliseconds(self):
        """Test datetime parsing without milliseconds."""
        result = parse_datetime("2023-01-15T10:30:00+0000")
        assert isinstance(result, datetime)

    def test_parse_list_empty(self):
        """Test parsing empty list."""
        assert parse_list("") == []

    def test_parse_list_single_item(self):
        """Test parsing single-item list."""
        assert parse_list("English") == ["English"]

    def test_parse_list_multiple_items(self):
        """Test parsing multiple-item list."""
        result = parse_list("English;Spanish;French")
        assert result == ["English", "Spanish", "French"]

    def test_parse_list_with_spaces(self):
        """Test parsing list strips whitespace."""
        result = parse_list("English ; Spanish ; French")
        assert result == ["English", "Spanish", "French"]

    def test_parse_list_empty_items_filtered(self):
        """Test parsing list filters empty items."""
        result = parse_list("English;;Spanish")
        assert result == ["English", "Spanish"]


class TestNodeSchemas:
    """Tests for node schema definitions."""

    def test_person_schema(self):
        """Test Person node schema."""
        assert PERSON_SCHEMA.label == "Person"
        assert PERSON_SCHEMA.csv_file == "person_0_0.csv"
        assert PERSON_SCHEMA.id_column == "id"
        assert len(PERSON_SCHEMA.properties) == 9

        # Check required properties
        prop_names = [p.property_name for p in PERSON_SCHEMA.properties if p.required]
        assert "firstName" in prop_names
        assert "lastName" in prop_names
        assert "birthday" in prop_names

    def test_post_schema(self):
        """Test Post node schema."""
        assert POST_SCHEMA.label == "Post"
        assert POST_SCHEMA.csv_file == "post_0_0.csv"
        assert POST_SCHEMA.id_column == "id"

        # Check for temporal property
        creation_date_prop = next(
            p for p in POST_SCHEMA.properties if p.property_name == "creationDate"
        )
        assert creation_date_prop.type_converter == parse_datetime

    def test_comment_schema(self):
        """Test Comment node schema."""
        assert COMMENT_SCHEMA.label == "Comment"
        assert COMMENT_SCHEMA.csv_file == "comment_0_0.csv"

    def test_all_node_schemas_registered(self):
        """Test all node schemas are in NODE_SCHEMAS."""
        assert len(NODE_SCHEMAS) == 8
        labels = [schema.label for schema in NODE_SCHEMAS]
        assert "Person" in labels
        assert "Post" in labels
        assert "Comment" in labels
        assert "Forum" in labels
        assert "Organisation" in labels
        assert "Place" in labels
        assert "Tag" in labels
        assert "TagClass" in labels


class TestRelationshipSchemas:
    """Tests for relationship schema definitions."""

    def test_knows_schema(self):
        """Test KNOWS relationship schema."""
        assert KNOWS_SCHEMA.type == "KNOWS"
        assert KNOWS_SCHEMA.csv_file == "person_knows_person_0_0.csv"
        assert KNOWS_SCHEMA.source_label == "Person"
        assert KNOWS_SCHEMA.target_label == "Person"
        assert KNOWS_SCHEMA.source_id_column == "Person.id"
        assert KNOWS_SCHEMA.target_id_column == "Person.id.1"

    def test_likes_post_schema(self):
        """Test LIKES Post relationship schema."""
        assert LIKES_POST_SCHEMA.type == "LIKES"
        assert LIKES_POST_SCHEMA.csv_file == "person_likes_post_0_0.csv"
        assert LIKES_POST_SCHEMA.source_label == "Person"
        assert LIKES_POST_SCHEMA.target_label == "Post"

    def test_likes_comment_schema(self):
        """Test LIKES Comment relationship schema."""
        assert LIKES_COMMENT_SCHEMA.type == "LIKES"
        assert LIKES_COMMENT_SCHEMA.csv_file == "person_likes_comment_0_0.csv"
        assert LIKES_COMMENT_SCHEMA.source_label == "Person"
        assert LIKES_COMMENT_SCHEMA.target_label == "Comment"

    def test_all_relationship_schemas_registered(self):
        """Test all relationship schemas are in RELATIONSHIP_SCHEMAS."""
        assert len(RELATIONSHIP_SCHEMAS) >= 3
        types = [schema.type for schema in RELATIONSHIP_SCHEMAS]
        assert "KNOWS" in types
        assert "LIKES" in types


class TestPropertyMappings:
    """Tests for property mapping structures."""

    def test_required_property(self):
        """Test required property mapping."""
        prop = next(p for p in PERSON_SCHEMA.properties if p.property_name == "firstName")
        assert prop.required is True
        assert prop.csv_column == "firstName"
        assert prop.type_converter == parse_string

    def test_optional_property(self):
        """Test optional property mapping."""
        prop = next(p for p in PERSON_SCHEMA.properties if p.property_name == "languages")
        assert prop.required is False
        assert prop.csv_column == "language"
        assert prop.type_converter == parse_list

    def test_temporal_property(self):
        """Test temporal property uses correct converter."""
        prop = next(p for p in PERSON_SCHEMA.properties if p.property_name == "birthday")
        assert prop.type_converter == parse_date

        prop = next(p for p in PERSON_SCHEMA.properties if p.property_name == "creationDate")
        assert prop.type_converter == parse_datetime
