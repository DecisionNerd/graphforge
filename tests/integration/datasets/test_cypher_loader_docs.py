"""Integration tests for CypherLoader documentation examples.

These tests verify that all code examples in docs/datasets/cypher-script-loading.md work correctly.
"""

import logging
from pathlib import Path

import pytest

from graphforge import GraphForge
from graphforge.datasets.loaders import CypherLoader


class TestBasicUsage:
    """Tests for basic usage examples from documentation."""

    def test_loading_script_file(self, tmp_path: Path):
        """Test basic script loading example."""
        script = tmp_path / "movies.cypher"
        script.write_text(
            """
            CREATE (TheMatrix:Movie {title:'The Matrix', released:1999});
            CREATE (Keanu:Person {name:'Keanu Reeves', born:1964});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        results = gf.execute("MATCH (m:Movie) RETURN m.title AS title")
        assert len(results) == 1
        assert results[0]["title"].value == "The Matrix"

    def test_example_script_with_skipped_statements(self, tmp_path: Path):
        """Test example script with constraints and indexes."""
        script = tmp_path / "movies.cypher"
        script.write_text(
            """
            CREATE CONSTRAINT movie_title IF NOT EXISTS
            FOR (m:Movie) REQUIRE m.title IS UNIQUE;

            CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);

            CREATE (TheMatrix:Movie {title:'The Matrix', released:1999});
            CREATE (Keanu:Person {name:'Keanu Reeves', born:1964});

            MATCH (keanu:Person {name:'Keanu Reeves'}), (matrix:Movie {title:'The Matrix'})
            CREATE (keanu)-[:ACTED_IN]->(matrix);
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        # Verify movie created
        results = gf.execute("MATCH (m:Movie) RETURN m.title AS title, m.released AS released")
        assert len(results) == 1
        assert results[0]["title"].value == "The Matrix"
        assert results[0]["released"].value == 1999

        # Verify person created
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name, p.born AS born")
        assert len(results) == 1
        assert results[0]["name"].value == "Keanu Reeves"
        assert results[0]["born"].value == 1964

        # Verify relationship created
        results = gf.execute("MATCH (p:Person)-[r:ACTED_IN]->(m:Movie) RETURN count(r) AS count")
        assert results[0]["count"].value == 1


class TestScriptFormat:
    """Tests for script format examples."""

    def test_statement_separation(self, tmp_path: Path):
        """Test semicolon-separated statements."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE (a:Person {name: 'Alice'});
            CREATE (b:Person {name: 'Bob'});
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            CREATE (a)-[:KNOWS]->(b);
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        results = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert results[0]["count"].value == 2

        results = gf.execute("MATCH ()-[r:KNOWS]->() RETURN count(r) AS count")
        assert results[0]["count"].value == 1

    def test_comments(self, tmp_path: Path):
        """Test comment handling."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            // This is a comment
            CREATE (n:Node {id: 1}); // Inline comment
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        results = gf.execute("MATCH (n:Node) RETURN count(n) AS count")
        assert results[0]["count"].value == 1

    def test_urls_preserved(self, tmp_path: Path):
        """Test that URLs with // are preserved."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE (w:Website {url: 'https://example.com'}); // This comment is removed
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        results = gf.execute("MATCH (w:Website) RETURN w.url AS url")
        assert results[0]["url"].value == "https://example.com"

    def test_multiline_statements(self, tmp_path: Path):
        """Test multi-line statement handling."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE (matrix:Movie {
                title: 'The Matrix',
                released: 1999,
                tagline: 'Welcome to the Real World'
            });
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        results = gf.execute(
            "MATCH (m:Movie) RETURN m.title AS title, m.released AS released, m.tagline AS tagline"
        )
        assert results[0]["title"].value == "The Matrix"
        assert results[0]["released"].value == 1999
        assert results[0]["tagline"].value == "Welcome to the Real World"

    def test_empty_statements(self, tmp_path: Path):
        """Test multiple semicolons and empty statements."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE (a:A);;;
            CREATE (b:B);;
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        results = gf.execute("MATCH (n) RETURN count(n) AS count")
        assert results[0]["count"].value == 2


class TestLogging:
    """Tests for logging examples."""

    def test_debug_logging(self, tmp_path: Path, caplog):
        """Test DEBUG level logging shows skipped statements."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE CONSTRAINT test FOR (n:Node) REQUIRE n.id IS UNIQUE;
            CREATE INDEX test_idx FOR (n:Node) ON (n.name);
            CREATE (n:Node {id: 1});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()

        with caplog.at_level(logging.DEBUG):
            loader.load(gf, script)

        # Verify DEBUG messages for skipped statements
        assert any("Skipping unsupported statement" in record.message for record in caplog.records)

    def test_info_logging(self, tmp_path: Path, caplog):
        """Test INFO level logging shows execution summary."""
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

        # Verify INFO summary message
        assert any(
            "2 statements executed, 1 skipped" in record.message for record in caplog.records
        )


class TestErrorHandling:
    """Tests for error handling examples."""

    def test_file_not_found(self):
        """Test FileNotFoundError for missing file."""
        gf = GraphForge()
        loader = CypherLoader()

        with pytest.raises(FileNotFoundError, match="Cypher script not found"):
            loader.load(gf, Path("nonexistent.cypher"))

    def test_syntax_error(self, tmp_path: Path):
        """Test ValueError for syntax errors."""
        script = tmp_path / "invalid.cypher"
        script.write_text("CREATE (n:Node INVALID;")

        gf = GraphForge()
        loader = CypherLoader()

        with pytest.raises(ValueError, match="Cypher execution error"):
            loader.load(gf, script)


class TestBestPractices:
    """Tests for best practices examples."""

    def test_grouped_operations(self, tmp_path: Path):
        """Test organized script with grouped sections."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            // Schema (auto-skipped)
            CREATE CONSTRAINT movie_title FOR (m:Movie) REQUIRE m.title IS UNIQUE;

            // Nodes
            CREATE (m1:Movie {title:'The Matrix'});
            CREATE (m2:Movie {title:'The Matrix Reloaded'});

            // Relationships
            MATCH (m1:Movie {title:'The Matrix'}), (m2:Movie {title:'The Matrix Reloaded'})
            CREATE (m1)-[:SEQUEL]->(m2);
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        # Verify movies created
        results = gf.execute("MATCH (m:Movie) RETURN count(m) AS count")
        assert results[0]["count"].value == 2

        # Verify relationship created
        results = gf.execute("MATCH ()-[r:SEQUEL]->() RETURN count(r) AS count")
        assert results[0]["count"].value == 1

    def test_variables_for_complex_patterns(self, tmp_path: Path):
        """Test using variables for readability."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            // Create nodes
            CREATE (neo:Character {name:'Neo'});
            CREATE (morpheus:Character {name:'Morpheus'});
            CREATE (matrix:Movie {title:'The Matrix'});

            // Create relationships using variables
            MATCH (neo:Character {name:'Neo'}),
                  (morpheus:Character {name:'Morpheus'}),
                  (matrix:Movie {title:'The Matrix'})
            CREATE (neo)-[:APPEARS_IN]->(matrix),
                   (morpheus)-[:APPEARS_IN]->(matrix),
                   (morpheus)-[:MENTORS]->(neo);
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        # Verify nodes created
        results = gf.execute("MATCH (c:Character) RETURN count(c) AS count")
        assert results[0]["count"].value == 2

        results = gf.execute("MATCH (m:Movie) RETURN count(m) AS count")
        assert results[0]["count"].value == 1

        # Verify relationships created
        results = gf.execute("MATCH ()-[r:APPEARS_IN]->() RETURN count(r) AS count")
        assert results[0]["count"].value == 2

        results = gf.execute("MATCH ()-[r:MENTORS]->() RETURN count(r) AS count")
        assert results[0]["count"].value == 1


class TestPerformanceTips:
    """Tests for performance tip examples."""

    def test_batched_creates(self, tmp_path: Path):
        """Test batched CREATE statements."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'}),
                   (c:Person {name: 'Charlie'});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        results = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert results[0]["count"].value == 3

    def test_create_vs_merge(self, tmp_path: Path):
        """Test CREATE vs MERGE usage."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            // Use CREATE when you know nodes don't exist
            CREATE (n:Person {id: 123, name: 'Alice'});

            // Use MERGE when you need idempotency
            MERGE (m:Person {id: 456})
            ON CREATE SET m.name = 'Bob', m.created = 123
            ON MATCH SET m.accessed = 456;
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        results = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert results[0]["count"].value == 2


class TestTroubleshooting:
    """Tests for troubleshooting examples."""

    def test_verify_loaded_data(self, tmp_path: Path):
        """Test data verification after loading."""
        script = tmp_path / "test.cypher"
        script.write_text(
            """
            CREATE (m:Movie {title:'The Matrix'});
            CREATE (p:Person {name:'Keanu Reeves'});
        """
        )

        gf = GraphForge()
        loader = CypherLoader()
        loader.load(gf, script)

        # Verify using separate queries (labels() function not yet supported)
        movie_results = gf.execute("MATCH (m:Movie) RETURN count(m) AS count")
        assert movie_results[0]["count"].value == 1

        person_results = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert person_results[0]["count"].value == 1


class TestAPIReference:
    """Tests for API reference examples."""

    def test_get_format(self):
        """Test get_format() method."""
        loader = CypherLoader()
        assert loader.get_format() == "cypher"

    def test_skip_prefixes(self):
        """Test SKIP_PREFIXES constant."""
        expected_prefixes = [
            "CREATE CONSTRAINT",
            "DROP CONSTRAINT",
            "CREATE INDEX",
            "DROP INDEX",
            "CALL",
        ]
        assert expected_prefixes == CypherLoader.SKIP_PREFIXES
