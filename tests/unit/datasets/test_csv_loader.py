"""Unit tests for CSV loader."""

import gzip
from pathlib import Path
import tempfile
import zipfile

import pytest

from graphforge import GraphForge
from graphforge.datasets.loaders.csv import CSVLoader


class TestCSVLoader:
    """Test CSV loader functionality."""

    def test_load_simple_edge_list(self):
        """Test loading a simple tab-separated edge list."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("# Comment line\n")
            f.write("0\t1\n")
            f.write("1\t2\n")
            f.write("2\t3\n")
            temp_path = Path(f.name)

        try:
            gf = GraphForge()
            loader = CSVLoader()
            loader.load(gf, temp_path)

            # Check nodes created
            nodes = gf.execute("MATCH (n) RETURN count(n) as count")
            assert nodes[0]["count"].value == 4

            # Check edges created
            edges = gf.execute("MATCH ()-[r]->() RETURN count(r) as count")
            assert edges[0]["count"].value == 3
        finally:
            temp_path.unlink()

    def test_load_comma_separated_values(self):
        """Test loading comma-separated values."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("0,1\n")
            f.write("1,2\n")
            temp_path = Path(f.name)

        try:
            gf = GraphForge()
            loader = CSVLoader()
            loader.load(gf, temp_path)

            edges = gf.execute("MATCH ()-[r]->() RETURN count(r) as count")
            assert edges[0]["count"].value == 2
        finally:
            temp_path.unlink()

    def test_load_space_delimited_values(self):
        """Test loading space-delimited values."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("0 1\n")
            f.write("1 2\n")
            temp_path = Path(f.name)

        try:
            gf = GraphForge()
            loader = CSVLoader()
            loader.load(gf, temp_path)

            edges = gf.execute("MATCH ()-[r]->() RETURN count(r) as count")
            assert edges[0]["count"].value == 2
        finally:
            temp_path.unlink()

    def test_load_multiple_consecutive_spaces(self):
        """Test loading space-delimited values with consecutive spaces."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("0  1\n")  # Two spaces
            f.write("1   2  0.5\n")  # Three spaces, then two spaces before weight
            f.write("2    3\n")  # Four spaces
            temp_path = Path(f.name)

        try:
            gf = GraphForge()
            loader = CSVLoader()
            loader.load(gf, temp_path)

            # Check nodes created (should be 0, 1, 2, 3)
            nodes = gf.execute("MATCH (n) RETURN count(n) as count")
            assert nodes[0]["count"].value == 4

            # Check edges created
            edges = gf.execute("MATCH ()-[r]->() RETURN count(r) as count")
            assert edges[0]["count"].value == 3

            # Check that weighted edge was parsed correctly
            weighted = gf.execute("MATCH ()-[r]->() WHERE r.weight = 0.5 RETURN count(r) as count")
            assert weighted[0]["count"].value == 1

            # Verify no empty node IDs were created
            result = gf.execute('MATCH (n) WHERE n.id = "" RETURN count(n) as count')
            assert result[0]["count"].value == 0
        finally:
            temp_path.unlink()

    def test_load_weighted_edges(self):
        """Test loading edges with weights."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("0\t1\t0.5\n")
            f.write("1\t2\t0.8\n")
            f.write("2\t3\t1.0\n")
            temp_path = Path(f.name)

        try:
            gf = GraphForge()
            loader = CSVLoader()
            loader.load(gf, temp_path)

            # Check edge weights
            result = gf.execute("""
                MATCH ()-[r]->()
                RETURN r.weight as weight
                ORDER BY weight
            """)

            assert len(result) == 3
            assert result[0]["weight"].value == 0.5
            assert result[1]["weight"].value == 0.8
            assert result[2]["weight"].value == 1.0
        finally:
            temp_path.unlink()

    def test_load_gzipped_file(self):
        """Test loading gzip-compressed file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt.gz") as f:
            temp_path = Path(f.name)

        try:
            # Write gzipped content
            with gzip.open(temp_path, "wt") as f:
                f.write("0\t1\n")
                f.write("1\t2\n")
                f.write("2\t3\n")

            gf = GraphForge()
            loader = CSVLoader()
            loader.load(gf, temp_path)

            edges = gf.execute("MATCH ()-[r]->() RETURN count(r) as count")
            assert edges[0]["count"].value == 3
        finally:
            temp_path.unlink()

    def test_skip_comment_lines(self):
        """Test that comment lines are skipped."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("# This is a comment\n")
            f.write("# Another comment\n")
            f.write("0\t1\n")
            f.write("# Comment in the middle\n")
            f.write("1\t2\n")
            temp_path = Path(f.name)

        try:
            gf = GraphForge()
            loader = CSVLoader()
            loader.load(gf, temp_path)

            edges = gf.execute("MATCH ()-[r]->() RETURN count(r) as count")
            assert edges[0]["count"].value == 2
        finally:
            temp_path.unlink()

    def test_skip_empty_lines(self):
        """Test that empty lines are skipped."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("0\t1\n")
            f.write("\n")
            f.write("1\t2\n")
            f.write("   \n")
            f.write("2\t3\n")
            temp_path = Path(f.name)

        try:
            gf = GraphForge()
            loader = CSVLoader()
            loader.load(gf, temp_path)

            edges = gf.execute("MATCH ()-[r]->() RETURN count(r) as count")
            assert edges[0]["count"].value == 3
        finally:
            temp_path.unlink()

    def test_deduplicates_nodes(self):
        """Test that duplicate nodes are not created."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("0\t1\n")
            f.write("0\t2\n")  # 0 appears again
            f.write("1\t2\n")  # 1 and 2 appear again
            temp_path = Path(f.name)

        try:
            gf = GraphForge()
            loader = CSVLoader()
            loader.load(gf, temp_path)

            # Should only create 3 unique nodes
            nodes = gf.execute("MATCH (n) RETURN count(n) as count")
            assert nodes[0]["count"].value == 3

            # Should create 3 edges
            edges = gf.execute("MATCH ()-[r]->() RETURN count(r) as count")
            assert edges[0]["count"].value == 3
        finally:
            temp_path.unlink()

    def test_node_ids_stored_as_property(self):
        """Test that node IDs are stored as properties."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("alice\tbob\n")
            f.write("bob\tcharlie\n")
            temp_path = Path(f.name)

        try:
            gf = GraphForge()
            loader = CSVLoader()
            loader.load(gf, temp_path)

            # Check node IDs
            result = gf.execute("""
                MATCH (n)
                RETURN n.id as id
                ORDER BY id
            """)

            assert len(result) == 3
            assert result[0]["id"].value == "alice"
            assert result[1]["id"].value == "bob"
            assert result[2]["id"].value == "charlie"
        finally:
            temp_path.unlink()

    def test_relationship_type(self):
        """Test that relationships have correct type."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("0\t1\n")
            temp_path = Path(f.name)

        try:
            gf = GraphForge()
            loader = CSVLoader()
            loader.load(gf, temp_path)

            # Check relationship type
            result = gf.execute("""
                MATCH ()-[r:CONNECTED_TO]->()
                RETURN count(r) as count
            """)

            assert result[0]["count"].value == 1
        finally:
            temp_path.unlink()

    def test_load_nonexistent_file_raises_error(self):
        """Test that loading nonexistent file raises FileNotFoundError."""
        gf = GraphForge()
        loader = CSVLoader()

        with pytest.raises(FileNotFoundError, match="Dataset file not found"):
            loader.load(gf, Path("/nonexistent/file.txt"))

    def test_load_invalid_format_raises_error(self):
        """Test that invalid line format raises ValueError."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("0\n")  # Only one column
            temp_path = Path(f.name)

        try:
            gf = GraphForge()
            loader = CSVLoader()

            with pytest.raises(ValueError, match="Invalid edge format"):
                loader.load(gf, temp_path)
        finally:
            temp_path.unlink()

    def test_load_invalid_weight_raises_error(self):
        """Test that invalid weight raises ValueError."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("0\t1\tinvalid\n")
            temp_path = Path(f.name)

        try:
            gf = GraphForge()
            loader = CSVLoader()

            with pytest.raises(ValueError, match="Invalid weight"):
                loader.load(gf, temp_path)
        finally:
            temp_path.unlink()

    def test_get_format(self):
        """Test get_format returns correct format name."""
        loader = CSVLoader()
        assert loader.get_format() == "csv"

    def test_load_zip_file(self):
        """Test loading from a zip archive."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as f:
            temp_path = Path(f.name)

        try:
            # Create zip file with CSV content
            with zipfile.ZipFile(temp_path, "w") as zf:
                zf.writestr("edges.csv", "0,1\n1,2\n2,3\n")

            gf = GraphForge()
            loader = CSVLoader()
            loader.load(gf, temp_path)

            # Check edges created
            edges = gf.execute("MATCH ()-[r]->() RETURN count(r) as count")
            assert edges[0]["count"].value == 3
        finally:
            temp_path.unlink()

    def test_load_zip_file_no_csv_raises_error(self):
        """Test that loading zip with no CSV files raises error."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as f:
            temp_path = Path(f.name)

        try:
            # Create zip file with non-CSV/TXT content only
            with zipfile.ZipFile(temp_path, "w") as zf:
                zf.writestr("README.md", "This is a markdown file\n")
                zf.writestr("data.json", '{"key": "value"}\n')

            gf = GraphForge()
            loader = CSVLoader()

            with pytest.raises(ValueError, match="No CSV/TXT/TSV/MTX files found in zip archive"):
                loader.load(gf, temp_path)
        finally:
            temp_path.unlink()
