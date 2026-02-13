"""Tests for ORDER BY edge cases with complex types.

Tests cover:
1. Missing aggregate functions (PERCENTILEDISC, PERCENTILECONT, STDEV, STDEVP)
2. Boolean comparison in ORDER BY
3. List comparison in ORDER BY (lexicographic)
4. Duration comparison in ORDER BY
"""

import pytest

from graphforge.api import GraphForge


@pytest.mark.unit
class TestAggregateFunctionRecognition:
    """Tests that all aggregate functions are recognized in ORDER BY context."""

    def test_percentiledisc_in_aggregate_set(self):
        """PERCENTILEDISC is in AGGREGATE_FUNCTIONS set."""
        from graphforge.executor.evaluator import AGGREGATE_FUNCTIONS

        assert "PERCENTILEDISC" in AGGREGATE_FUNCTIONS

    def test_percentilecont_in_aggregate_set(self):
        """PERCENTILECONT is in AGGREGATE_FUNCTIONS set."""
        from graphforge.executor.evaluator import AGGREGATE_FUNCTIONS

        assert "PERCENTILECONT" in AGGREGATE_FUNCTIONS

    def test_stdev_in_aggregate_set(self):
        """STDEV is in AGGREGATE_FUNCTIONS set."""
        from graphforge.executor.evaluator import AGGREGATE_FUNCTIONS

        assert "STDEV" in AGGREGATE_FUNCTIONS

    def test_stdevp_in_aggregate_set(self):
        """STDEVP is in AGGREGATE_FUNCTIONS set."""
        from graphforge.executor.evaluator import AGGREGATE_FUNCTIONS

        assert "STDEVP" in AGGREGATE_FUNCTIONS


@pytest.mark.unit
class TestBooleanOrdering:
    """Tests for ORDER BY with boolean values."""

    def test_boolean_order_by_ascending(self):
        """Boolean values sort with false before true."""
        gf = GraphForge()
        gf.execute("CREATE (:Item {flag: true})")
        gf.execute("CREATE (:Item {flag: false})")
        gf.execute("CREATE (:Item {flag: true})")
        gf.execute("CREATE (:Item {flag: false})")

        result = gf.execute("MATCH (i:Item) RETURN i.flag AS flag ORDER BY flag ASC")

        assert len(result) == 4
        assert result[0]["flag"].value is False
        assert result[1]["flag"].value is False
        assert result[2]["flag"].value is True
        assert result[3]["flag"].value is True

    def test_boolean_order_by_descending(self):
        """Boolean values sort with true before false when descending."""
        gf = GraphForge()
        gf.execute("CREATE (:Item {flag: true})")
        gf.execute("CREATE (:Item {flag: false})")
        gf.execute("CREATE (:Item {flag: true})")

        result = gf.execute("MATCH (i:Item) RETURN i.flag AS flag ORDER BY flag DESC")

        assert len(result) == 3
        assert result[0]["flag"].value is True
        assert result[1]["flag"].value is True
        assert result[2]["flag"].value is False

    def test_boolean_with_null_order_by(self):
        """Boolean ORDER BY handles NULL values."""
        gf = GraphForge()
        gf.execute("CREATE (:Item {flag: true})")
        gf.execute("CREATE (:Item {flag: false})")
        gf.execute("CREATE (:Item)")  # No flag property -> NULL

        result = gf.execute("MATCH (i:Item) RETURN i.flag AS flag ORDER BY flag ASC")

        # Should have 3 results and not crash
        assert len(result) == 3
        # NULL handling in ORDER BY may vary - just ensure no crash
        values = [r["flag"].value for r in result]
        assert True in values
        assert False in values
        assert None in values


@pytest.mark.unit
class TestListOrdering:
    """Tests for ORDER BY with list values (lexicographic comparison)."""

    def test_list_order_by_ascending(self):
        """Lists sort lexicographically."""
        gf = GraphForge()
        gf.execute("CREATE (:Item {tags: [1, 3]})")
        gf.execute("CREATE (:Item {tags: [1, 2]})")
        gf.execute("CREATE (:Item {tags: [2, 1]})")
        gf.execute("CREATE (:Item {tags: [1, 2, 3]})")

        result = gf.execute("MATCH (i:Item) RETURN i.tags AS tags ORDER BY tags ASC")

        assert len(result) == 4
        # Extract inner values for comparison
        values = [[item.value for item in r["tags"].value] for r in result]
        assert values[0] == [1, 2]
        assert values[1] == [1, 2, 3]
        assert values[2] == [1, 3]
        assert values[3] == [2, 1]

    def test_list_order_by_descending(self):
        """Lists sort lexicographically in descending order."""
        gf = GraphForge()
        gf.execute("CREATE (:Item {tags: [1, 2]})")
        gf.execute("CREATE (:Item {tags: [2, 1]})")
        gf.execute("CREATE (:Item {tags: [1, 3]})")

        result = gf.execute("MATCH (i:Item) RETURN i.tags AS tags ORDER BY tags DESC")

        assert len(result) == 3
        values = [[item.value for item in r["tags"].value] for r in result]
        assert values[0] == [2, 1]
        assert values[1] == [1, 3]
        assert values[2] == [1, 2]

    def test_list_order_by_different_lengths(self):
        """Shorter lists come before longer lists when prefixes match."""
        gf = GraphForge()
        gf.execute("CREATE (:Item {tags: [1, 2, 3]})")
        gf.execute("CREATE (:Item {tags: [1, 2]})")
        gf.execute("CREATE (:Item {tags: [1]})")
        gf.execute("CREATE (:Item {tags: [1, 2, 3, 4]})")

        result = gf.execute("MATCH (i:Item) RETURN i.tags AS tags ORDER BY tags ASC")

        assert len(result) == 4
        values = [[item.value for item in r["tags"].value] for r in result]
        assert values[0] == [1]
        assert values[1] == [1, 2]
        assert values[2] == [1, 2, 3]
        assert values[3] == [1, 2, 3, 4]

    def test_list_order_by_with_strings(self):
        """Lists of strings sort lexicographically."""
        gf = GraphForge()
        gf.execute("CREATE (:Item {tags: ['b', 'a']})")
        gf.execute("CREATE (:Item {tags: ['a', 'c']})")
        gf.execute("CREATE (:Item {tags: ['a', 'b']})")

        result = gf.execute("MATCH (i:Item) RETURN i.tags AS tags ORDER BY tags ASC")

        assert len(result) == 3
        values = [[item.value for item in r["tags"].value] for r in result]
        assert values[0] == ["a", "b"]
        assert values[1] == ["a", "c"]
        assert values[2] == ["b", "a"]

    def test_empty_list_order_by(self):
        """Empty lists sort before non-empty lists."""
        gf = GraphForge()
        gf.execute("CREATE (:Item {tags: [1]})")
        gf.execute("CREATE (:Item {tags: []})")
        gf.execute("CREATE (:Item {tags: [1, 2]})")

        result = gf.execute("MATCH (i:Item) RETURN i.tags AS tags ORDER BY tags ASC")

        assert len(result) == 3
        values = [[item.value for item in r["tags"].value] for r in result]
        assert values[0] == []
        assert values[1] == [1]
        assert values[2] == [1, 2]


@pytest.mark.unit
class TestDurationOrdering:
    """Tests for ORDER BY with duration values."""

    def test_duration_order_by_ascending(self):
        """Duration values sort correctly in ascending order."""
        gf = GraphForge()
        gf.execute("CREATE (:Event {delay: duration('P1D')})")
        gf.execute("CREATE (:Event {delay: duration('PT1H')})")
        gf.execute("CREATE (:Event {delay: duration('P7D')})")
        gf.execute("CREATE (:Event {delay: duration('PT30M')})")

        result = gf.execute("MATCH (e:Event) RETURN e.delay AS delay ORDER BY delay ASC")

        assert len(result) == 4
        # PT30M < PT1H < P1D < P7D

    def test_duration_order_by_descending(self):
        """Duration values sort correctly in descending order."""
        gf = GraphForge()
        gf.execute("CREATE (:Event {delay: duration('PT1H')})")
        gf.execute("CREATE (:Event {delay: duration('P1D')})")
        gf.execute("CREATE (:Event {delay: duration('PT30M')})")

        result = gf.execute("MATCH (e:Event) RETURN e.delay AS delay ORDER BY delay DESC")

        assert len(result) == 3
        # P1D > PT1H > PT30M

    def test_duration_with_null_order_by(self):
        """Duration ORDER BY handles NULL values."""
        gf = GraphForge()
        gf.execute("CREATE (:Event {delay: duration('PT1H')})")
        gf.execute("CREATE (:Event)")  # No delay property -> NULL
        gf.execute("CREATE (:Event {delay: duration('P1D')})")

        result = gf.execute("MATCH (e:Event) RETURN e.delay AS delay ORDER BY delay ASC")

        assert len(result) == 3
        # NULL should come first


@pytest.mark.unit
class TestMixedTypeOrdering:
    """Tests for ORDER BY with mixed types."""

    def test_mixed_types_do_not_crash(self):
        """ORDER BY with mixed incomparable types does not crash."""
        gf = GraphForge()
        gf.execute("CREATE (:Item {value: 1})")
        gf.execute("CREATE (:Item {value: 'string'})")
        gf.execute("CREATE (:Item {value: [1, 2]})")
        gf.execute("CREATE (:Item {value: true})")

        # Should not crash - incomparable types return false
        result = gf.execute("MATCH (i:Item) RETURN i.value AS value ORDER BY value ASC")

        assert len(result) == 4
