"""Integration tests for LDBC loader.

These tests instantiate GraphForge and execute Cypher queries,
making them integration tests rather than unit tests.
"""

from pathlib import Path

import pytest

from graphforge import GraphForge
from graphforge.datasets.loaders.ldbc import LDBCLoader
from graphforge.datasets.loaders.ldbc_schema import PropertyMapping, parse_int, parse_string

pytestmark = pytest.mark.integration


class TestLDBCLoader:
    """Tests for LDBC loader."""

    def test_get_format(self):
        """Test format identifier."""
        loader = LDBCLoader()
        assert loader.get_format() == "ldbc"

    def test_default_delimiter(self):
        """Test default pipe delimiter."""
        loader = LDBCLoader()
        assert loader.delimiter == "|"

    def test_custom_delimiter(self):
        """Test custom delimiter."""
        loader = LDBCLoader(delimiter=",")
        assert loader.delimiter == ","


class TestParseProperties:
    """Tests for property parsing."""

    def test_parse_simple_properties(self):
        """Test parsing simple string properties."""
        loader = LDBCLoader()
        row = {"name": "Alice", "age": "30"}
        mappings = [
            PropertyMapping("name", "name", parse_string),
            PropertyMapping("age", "age", parse_int),
        ]

        properties = loader._parse_properties(row, mappings)

        assert properties == {"name": "Alice", "age": 30}

    def test_parse_optional_property_present(self):
        """Test parsing optional property when present."""
        loader = LDBCLoader()
        row = {"name": "Alice", "nickname": "Ally"}
        mappings = [
            PropertyMapping("name", "name", parse_string),
            PropertyMapping("nickname", "nickname", parse_string, required=False),
        ]

        properties = loader._parse_properties(row, mappings)

        assert properties == {"name": "Alice", "nickname": "Ally"}

    def test_parse_optional_property_missing(self):
        """Test parsing optional property when missing."""
        loader = LDBCLoader()
        row = {"name": "Alice"}
        mappings = [
            PropertyMapping("name", "name", parse_string),
            PropertyMapping("nickname", "nickname", parse_string, required=False),
        ]

        properties = loader._parse_properties(row, mappings)

        assert properties == {"name": "Alice"}
        assert "nickname" not in properties

    def test_parse_optional_property_empty_string(self):
        """Test parsing optional property with empty string."""
        loader = LDBCLoader()
        row = {"name": "Alice", "nickname": ""}
        mappings = [
            PropertyMapping("name", "name", parse_string),
            PropertyMapping("nickname", "nickname", parse_string, required=False),
        ]

        properties = loader._parse_properties(row, mappings)

        assert properties == {"name": "Alice"}
        assert "nickname" not in properties

    def test_parse_required_property_missing_raises_error(self):
        """Test missing required property raises error."""
        loader = LDBCLoader()
        row = {}
        mappings = [
            PropertyMapping("name", "name", parse_string, required=True),
        ]

        with pytest.raises(ValueError, match="Required property .* is missing"):
            loader._parse_properties(row, mappings)

    def test_parse_invalid_type_required_raises_error(self):
        """Test invalid type for required property raises error."""
        loader = LDBCLoader()
        row = {"age": "not a number"}
        mappings = [
            PropertyMapping("age", "age", parse_int, required=True),
        ]

        with pytest.raises(ValueError, match="Failed to parse required property"):
            loader._parse_properties(row, mappings)

    def test_parse_invalid_type_optional_skipped(self):
        """Test invalid type for optional property is skipped."""
        loader = LDBCLoader()
        row = {"name": "Alice", "age": "not a number"}
        mappings = [
            PropertyMapping("name", "name", parse_string),
            PropertyMapping("age", "age", parse_int, required=False),
        ]

        properties = loader._parse_properties(row, mappings)

        # Should skip invalid optional property
        assert properties == {"name": "Alice"}
        assert "age" not in properties


class TestFindCSVFile:
    """Tests for CSV file finding."""

    def test_find_direct_path(self, tmp_path):
        """Test finding CSV in direct path."""
        loader = LDBCLoader()

        # Create CSV file
        csv_file = tmp_path / "person_0_0.csv"
        csv_file.write_text("id|name\n1|Alice")

        result = loader._find_csv_file(tmp_path, "person_0_0.csv")

        assert result == csv_file

    def test_find_in_subdirectory(self, tmp_path):
        """Test finding CSV in subdirectory."""
        loader = LDBCLoader()

        # Create subdirectory with CSV
        subdir = tmp_path / "social-network"
        subdir.mkdir()
        csv_file = subdir / "person_0_0.csv"
        csv_file.write_text("id|name\n1|Alice")

        result = loader._find_csv_file(tmp_path, "person_0_0.csv")

        assert result == csv_file

    def test_find_nonexistent_file(self, tmp_path):
        """Test finding nonexistent file returns None."""
        loader = LDBCLoader()

        result = loader._find_csv_file(tmp_path, "nonexistent.csv")

        assert result is None

    def test_find_prefers_direct_path(self, tmp_path):
        """Test direct path is preferred over subdirectory."""
        loader = LDBCLoader()

        # Create file in both root and subdirectory
        direct_file = tmp_path / "test.csv"
        direct_file.write_text("direct")

        subdir = tmp_path / "sub"
        subdir.mkdir()
        subdir_file = subdir / "test.csv"
        subdir_file.write_text("subdir")

        result = loader._find_csv_file(tmp_path, "test.csv")

        # Should return direct path
        assert result == direct_file


class TestLoadNonexistentPath:
    """Tests for loading from nonexistent paths."""

    def test_load_nonexistent_path_raises_error(self):
        """Test loading from nonexistent path raises error."""
        loader = LDBCLoader()
        gf = GraphForge()

        with pytest.raises(FileNotFoundError, match="Dataset path not found"):
            loader.load(gf, Path("/nonexistent/path"))


class TestLoadDirectory:
    """Tests for loading from directory."""

    def test_load_empty_directory(self, tmp_path):
        """Test loading from empty directory completes without error."""
        loader = LDBCLoader()
        gf = GraphForge()

        # Should complete without error (no CSVs found)
        loader.load(gf, tmp_path)

        # Graph should be empty
        results = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert results[0]["count"].value == 0

    def test_load_simple_nodes(self, tmp_path):
        """Test loading simple node data."""
        loader = LDBCLoader()
        gf = GraphForge()

        # Create minimal person CSV
        person_csv = tmp_path / "person_0_0.csv"
        person_csv.write_text(
            "id|firstName|lastName|gender|birthday|creationDate|locationIP|browserUsed\n"
            "1|Alice|Smith|female|1990-01-01|2023-01-01T00:00:00.000+0000|192.168.1.1|Firefox"
        )

        loader.load(gf, tmp_path)

        # Verify node was created
        results = gf.execute("MATCH (p:Person) RETURN p.firstName AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_load_nodes_and_relationships(self, tmp_path):
        """Test loading nodes and relationships."""
        loader = LDBCLoader()
        gf = GraphForge()

        # Create person CSV
        person_csv = tmp_path / "person_0_0.csv"
        person_csv.write_text(
            "id|firstName|lastName|gender|birthday|creationDate|locationIP|browserUsed\n"
            "1|Alice|Smith|female|1990-01-01|2023-01-01T00:00:00.000+0000|192.168.1.1|Firefox\n"
            "2|Bob|Jones|male|1985-05-15|2023-01-02T00:00:00.000+0000|192.168.1.2|Chrome"
        )

        # Create knows relationship CSV
        knows_csv = tmp_path / "person_knows_person_0_0.csv"
        knows_csv.write_text("Person.id|Person.id.1|creationDate\n1|2|2023-02-01T00:00:00.000+0000")

        loader.load(gf, tmp_path)

        # Verify relationship was created
        results = gf.execute(
            "MATCH (a:Person)-[r:KNOWS]->(b:Person) RETURN a.firstName AS from, b.firstName AS to"
        )
        assert len(results) == 1
        assert results[0]["from"].value == "Alice"
        assert results[0]["to"].value == "Bob"
