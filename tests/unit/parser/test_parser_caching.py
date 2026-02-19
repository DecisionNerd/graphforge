"""Tests for global parser caching behavior.

Verifies that the Lark grammar parser is compiled once and shared
across all CypherParser instances, avoiding redundant compilation overhead.
"""

import pytest

from graphforge.parser.parser import CypherParser, _get_lark_parser, parse_cypher


@pytest.mark.unit
class TestParserCaching:
    """Tests for global Lark parser caching."""

    def test_multiple_instances_share_lark_parser(self):
        """Multiple CypherParser instances must share the same Lark parser object."""
        parser1 = CypherParser()
        parser2 = CypherParser()
        parser3 = CypherParser()

        assert parser1._lark is parser2._lark
        assert parser2._lark is parser3._lark

    def test_cached_function_returns_same_object(self):
        """_get_lark_parser must return the same object on repeated calls."""
        lark1 = _get_lark_parser()
        lark2 = _get_lark_parser()

        assert lark1 is lark2

    def test_transformers_are_independent(self):
        """Each CypherParser must have its own transformer instance."""
        parser1 = CypherParser()
        parser2 = CypherParser()

        assert parser1._transformer is not parser2._transformer

    def test_cached_parser_produces_correct_results(self):
        """Cached parser must produce correct AST output."""
        from graphforge.ast.query import CypherQuery

        parser1 = CypherParser()
        parser2 = CypherParser()

        ast1 = parser1.parse("MATCH (n:Person) RETURN n")
        ast2 = parser2.parse("MATCH (n:Person) RETURN n")

        assert isinstance(ast1, CypherQuery)
        assert isinstance(ast2, CypherQuery)
        assert len(ast1.clauses) == len(ast2.clauses)

    def test_convenience_function_uses_cached_parser(self):
        """parse_cypher convenience function must use the cached Lark parser."""
        # Call parse_cypher to ensure the cache is populated
        parse_cypher("RETURN 1")

        # Create a new CypherParser -- it should share the cached Lark object
        parser = CypherParser()
        assert parser._lark is _get_lark_parser()

    def test_cache_info_shows_hits(self):
        """lru_cache must report cache hits after multiple instantiations."""
        # Clear cache to start fresh
        _get_lark_parser.cache_clear()

        # First call compiles grammar
        _get_lark_parser()
        info1 = _get_lark_parser.cache_info()
        assert info1.misses == 1
        assert info1.hits == 0

        # Second call should be a cache hit
        _get_lark_parser()
        info2 = _get_lark_parser.cache_info()
        assert info2.misses == 1
        assert info2.hits == 1

    def test_different_queries_work_with_shared_parser(self):
        """Shared parser must handle diverse query types correctly."""
        from graphforge.ast.query import CypherQuery

        parser = CypherParser()

        queries = [
            "MATCH (n) RETURN n",
            "CREATE (n:Person {name: 'Alice'})",
            "MATCH (a)-[r]->(b) RETURN a, r, b",
            "MATCH (n) WHERE n.age > 30 RETURN n.name",
            "RETURN 1 + 2 AS result",
        ]

        for query in queries:
            ast = parser.parse(query)
            assert isinstance(ast, CypherQuery), f"Failed to parse: {query}"
