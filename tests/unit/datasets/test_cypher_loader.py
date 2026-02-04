"""Unit tests for Cypher script loader."""

import logging
from pathlib import Path

import pytest

from graphforge import GraphForge
from graphforge.datasets.loaders.cypher import CypherLoader


class TestCypherLoaderBasic:
    """Basic functionality tests for CypherLoader."""

    def test_load_simple_create_statement(self, tmp_path: Path):
        """Test loading simple CREATE statement."""
        script = tmp_path / "test.cypher"
        script.write_text("CREATE (n:Person {name: 'Alice', age: 30});")

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        # Verify node was created
        result = gf.execute("MATCH (n:Person) RETURN n.name AS name, n.age AS age")
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"
        assert result[0]["age"].value == 30

    def test_load_multiple_statements(self, tmp_path: Path):
        """Test loading multiple statements."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE (a:Person {name: 'Alice'});
            CREATE (b:Person {name: 'Bob'});
            CREATE (c:Person {name: 'Charlie'});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        # Verify all nodes created
        result = gf.execute("MATCH (n:Person) RETURN count(n) AS count")
        assert result[0]["count"].value == 3

    def test_load_with_relationships(self, tmp_path: Path):
        """Test loading nodes and relationships."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE (a:Person {name: 'Alice'});
            CREATE (b:Person {name: 'Bob'});
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            CREATE (a)-[:KNOWS {since: 2020}]->(b);
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        # Verify relationship created
        result = gf.execute(
            """
            MATCH (a:Person)-[r:KNOWS]->(b:Person)
            RETURN a.name AS from, b.name AS to, r.since AS since
        """
        )
        assert len(result) == 1
        assert result[0]["from"].value == "Alice"
        assert result[0]["to"].value == "Bob"
        assert result[0]["since"].value == 2020


class TestConstraintSkipping:
    """Tests for skipping CREATE/DROP CONSTRAINT statements."""

    def test_skip_create_constraint_unique(self, tmp_path: Path):
        """Test skipping CREATE CONSTRAINT for unique."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE CONSTRAINT movie_title IF NOT EXISTS
            FOR (m:Movie) REQUIRE m.title IS UNIQUE;

            CREATE (m:Movie {title: 'The Matrix'});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)  # Should not raise error

        # Verify node created, constraint skipped
        result = gf.execute("MATCH (m:Movie) RETURN m.title AS title")
        assert len(result) == 1
        assert result[0]["title"].value == "The Matrix"

    def test_skip_create_constraint_exists(self, tmp_path: Path):
        """Test skipping CREATE CONSTRAINT for exists."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE CONSTRAINT person_name IF NOT EXISTS
            FOR (p:Person) REQUIRE p.name IS NOT NULL;

            CREATE (p:Person {name: 'Alice'});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        result = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert result[0]["count"].value == 1

    def test_skip_drop_constraint(self, tmp_path: Path):
        """Test skipping DROP CONSTRAINT."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            DROP CONSTRAINT movie_title IF EXISTS;
            CREATE (m:Movie {title: 'Test'});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        result = gf.execute("MATCH (m:Movie) RETURN count(m) AS count")
        assert result[0]["count"].value == 1

    def test_skip_multiple_constraints(self, tmp_path: Path):
        """Test skipping multiple constraint statements."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE CONSTRAINT c1 FOR (n:Node) REQUIRE n.id IS UNIQUE;
            CREATE CONSTRAINT c2 FOR (m:Movie) REQUIRE m.title IS UNIQUE;
            DROP CONSTRAINT c1 IF EXISTS;

            CREATE (n:Node {id: 1});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        result = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert result[0]["count"].value == 1


class TestIndexSkipping:
    """Tests for skipping CREATE/DROP INDEX statements."""

    def test_skip_create_index(self, tmp_path: Path):
        """Test skipping CREATE INDEX."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);
            CREATE (p:Person {name: 'Alice'});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        result = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert result[0]["count"].value == 1

    def test_skip_drop_index(self, tmp_path: Path):
        """Test skipping DROP INDEX."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            DROP INDEX person_name IF EXISTS;
            CREATE (p:Person {name: 'Bob'});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        result = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert result[0]["count"].value == 1


class TestCallSkipping:
    """Tests for skipping CALL procedure statements."""

    def test_skip_call_procedure(self, tmp_path: Path):
        """Test skipping CALL procedure."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CALL db.stats.clear();
            CREATE (n:Node {value: 42});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        result = gf.execute("MATCH (n:Node) RETURN n.value AS value")
        assert result[0]["value"].value == 42


class TestCommentHandling:
    """Tests for handling comments in scripts."""

    def test_skip_single_line_comments(self, tmp_path: Path):
        """Test skipping single-line comments."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            // This is a comment
            CREATE (n:Node {id: 1});
            // Another comment
            CREATE (m:Node {id: 2}); // Inline comment
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        result = gf.execute("MATCH (n:Node) RETURN count(n) AS count")
        assert result[0]["count"].value == 2

    def test_preserve_urls_with_double_slash(self, tmp_path: Path):
        """Test that URLs with // are preserved."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE (n:Website {url: 'https://example.com'});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        result = gf.execute("MATCH (n:Website) RETURN n.url AS url")
        assert result[0]["url"].value == "https://example.com"


class TestStatementSplitting:
    """Tests for statement splitting logic."""

    def test_split_on_semicolons(self, tmp_path: Path):
        """Test splitting statements on semicolons."""
        script = tmp_path / "test.cypher"
        script.write_text("CREATE (a:A); CREATE (b:B); CREATE (c:C);")

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        result = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert result[0]["count"].value == 3

    def test_handle_empty_statements(self, tmp_path: Path):
        """Test handling empty statements (multiple semicolons)."""
        script = tmp_path / "test.cypher"
        script.write_text("CREATE (a:A);;; CREATE (b:B);;")

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        result = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert result[0]["count"].value == 2

    def test_multiline_statements(self, tmp_path: Path):
        """Test handling statements spanning multiple lines."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE (a:Person {
                name: 'Alice',
                age: 30
            });
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        result = gf.execute("MATCH (p:Person) RETURN p.name AS name, p.age AS age")
        assert result[0]["name"].value == "Alice"
        assert result[0]["age"].value == 30


class TestErrorHandling:
    """Tests for error handling."""

    def test_file_not_found(self):
        """Test error when file doesn't exist."""
        gf = GraphForge()
        loader = CypherLoader()

        with pytest.raises(FileNotFoundError, match="Cypher script not found"):
            loader.load(gf, Path("/nonexistent/file.cypher"))

    def test_syntax_error_in_statement(self, tmp_path: Path):
        """Test error when statement has syntax error."""
        script = tmp_path / "test.cypher"
        script.write_text("CREATE (n:Person INVALID SYNTAX;")

        gf = GraphForge()
        loader = CypherLoader()

        with pytest.raises(ValueError, match="Cypher execution error"):
            loader.load(gf, script)


class TestLogging:
    """Tests for logging behavior."""

    def test_debug_logging_for_skipped_statements(self, tmp_path: Path, caplog):
        """Test DEBUG logging when skipping statements."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE CONSTRAINT test FOR (n:Node) REQUIRE n.id IS UNIQUE;
            CREATE (n:Node {id: 1});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()

        with caplog.at_level(logging.DEBUG):
            loader.load(gf, script)

        # Check that skipped statement was logged at DEBUG level
        assert any("Skipping unsupported statement" in record.message for record in caplog.records)

    def test_info_logging_for_load_summary(self, tmp_path: Path, caplog):
        """Test INFO logging shows execution summary."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE CONSTRAINT test FOR (n:Node) REQUIRE n.id IS UNIQUE;
            CREATE (n:Node {id: 1});
            CREATE (m:Node {id: 2});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()

        with caplog.at_level(logging.INFO):
            loader.load(gf, script)

        # Check summary log: 2 executed, 1 skipped
        assert any(
            "2 statements executed, 1 skipped" in record.message for record in caplog.records
        )


class TestRealWorldPatterns:
    """Tests with patterns from real Neo4j datasets."""

    def test_movie_graph_pattern(self, tmp_path: Path):
        """Test Neo4j Movie Graph pattern."""
        script = tmp_path / "movies.cypher"
        script.write_text(
            """
            CREATE CONSTRAINT movie_title IF NOT EXISTS
            FOR (m:Movie) REQUIRE m.title IS UNIQUE;

            CREATE (TheMatrix:Movie {title:'The Matrix', released:1999, tagline:'Welcome to the Real World'});
            CREATE (Keanu:Person {name:'Keanu Reeves', born:1964});

            MATCH (keanu:Person {name:'Keanu Reeves'}), (matrix:Movie {title:'The Matrix'})
            CREATE (keanu)-[:ACTED_IN]->(matrix);
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        # Verify movie and person created
        result = gf.execute("MATCH (m:Movie) RETURN m.title AS title, m.released AS year")
        assert result[0]["title"].value == "The Matrix"
        assert result[0]["year"].value == 1999

        result = gf.execute("MATCH (p:Person) RETURN p.name AS name")
        assert result[0]["name"].value == "Keanu Reeves"

        # Verify relationship exists
        result = gf.execute("MATCH (p:Person)-[r:ACTED_IN]->(m:Movie) RETURN count(r) AS count")
        assert len(result) == 1
        assert result[0]["count"].value == 1
