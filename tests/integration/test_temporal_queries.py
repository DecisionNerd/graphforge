"""Integration tests for temporal types in queries.

Tests end-to-end temporal functionality:
- Creating nodes with temporal properties
- Querying with temporal comparisons
- Temporal function usage in queries
- Persistence of temporal values
"""

import datetime
from pathlib import Path
import tempfile

import pytest

from graphforge import GraphForge


@pytest.mark.integration
class TestTemporalProperties:
    """Tests for storing and retrieving temporal properties."""

    def test_create_node_with_date_property(self):
        """Test creating node with DATE property."""
        gf = GraphForge()

        gf.execute("""
            CREATE (p:Person {
                name: 'Alice',
                birthday: date('1990-05-15')
            })
        """)

        results = gf.execute("MATCH (p:Person) RETURN p.birthday AS birthday")
        assert len(results) == 1

        birthday = results[0]["birthday"]
        assert birthday.value == datetime.date(1990, 5, 15)

    def test_create_node_with_datetime_property(self):
        """Test creating node with DATETIME property."""
        gf = GraphForge()

        gf.execute("""
            CREATE (p:Post {
                title: 'My Post',
                createdAt: datetime('2023-01-15T10:30:00')
            })
        """)

        results = gf.execute("MATCH (p:Post) RETURN p.createdAt AS createdAt")
        assert len(results) == 1

        created_at = results[0]["createdAt"]
        expected = datetime.datetime(2023, 1, 15, 10, 30, 0)
        assert created_at.value == expected

    def test_create_node_with_time_property(self):
        """Test creating node with TIME property."""
        gf = GraphForge()

        gf.execute("""
            CREATE (m:Meeting {
                name: 'Standup',
                startTime: time('09:00:00')
            })
        """)

        results = gf.execute("MATCH (m:Meeting) RETURN m.startTime AS startTime")
        assert len(results) == 1

        start_time = results[0]["startTime"]
        assert start_time.value == datetime.time(9, 0, 0)

    def test_create_node_with_duration_property(self):
        """Test creating node with DURATION property."""
        gf = GraphForge()

        gf.execute("""
            CREATE (t:Task {
                name: 'Build',
                estimatedDuration: duration('PT2H30M')
            })
        """)

        results = gf.execute("MATCH (t:Task) RETURN t.estimatedDuration AS duration")
        assert len(results) == 1

        duration = results[0]["duration"]
        expected = datetime.timedelta(hours=2, minutes=30)
        assert duration.value == expected


@pytest.mark.integration
class TestTemporalComparisons:
    """Tests for temporal comparisons in WHERE clauses."""

    def test_filter_by_date_greater_than(self):
        """Test filtering nodes by date > comparison."""
        gf = GraphForge()

        # Create people with different birthdays
        gf.execute("CREATE (p:Person {name: 'Alice', birthday: date('1985-01-01')})")
        gf.execute("CREATE (p:Person {name: 'Bob', birthday: date('1995-01-01')})")
        gf.execute("CREATE (p:Person {name: 'Charlie', birthday: date('2000-01-01')})")

        # Filter for people born after 1990
        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.birthday > date('1990-01-01')
            RETURN p.name AS name
            ORDER BY name
        """)

        assert len(results) == 2
        assert results[0]["name"].value == "Bob"
        assert results[1]["name"].value == "Charlie"

    def test_filter_by_datetime_less_than(self):
        """Test filtering nodes by datetime < comparison."""
        gf = GraphForge()

        # Create posts with different timestamps
        gf.execute("CREATE (p:Post {title: 'Old', createdAt: datetime('2023-01-01T10:00:00')})")
        gf.execute("CREATE (p:Post {title: 'Recent', createdAt: datetime('2023-06-01T10:00:00')})")

        # Filter for old posts
        results = gf.execute("""
            MATCH (p:Post)
            WHERE p.createdAt < datetime('2023-03-01T00:00:00')
            RETURN p.title AS title
        """)

        assert len(results) == 1
        assert results[0]["title"].value == "Old"

    def test_filter_by_date_equality(self):
        """Test filtering nodes by date = comparison."""
        gf = GraphForge()

        gf.execute("CREATE (e:Event {name: 'Meeting', date: date('2023-05-15')})")
        gf.execute("CREATE (e:Event {name: 'Conference', date: date('2023-06-20')})")

        results = gf.execute("""
            MATCH (e:Event)
            WHERE e.date = date('2023-05-15')
            RETURN e.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Meeting"


@pytest.mark.integration
class TestTemporalFunctionsInQueries:
    """Tests for temporal functions in query context."""

    def test_extract_year_from_date_property(self):
        """Test extracting year from date property."""
        gf = GraphForge()

        gf.execute("CREATE (p:Person {name: 'Alice', birthday: date('1990-05-15')})")

        results = gf.execute("""
            MATCH (p:Person)
            RETURN year(p.birthday) AS birthYear
        """)

        assert len(results) == 1
        assert results[0]["birthYear"].value == 1990

    def test_extract_month_and_day(self):
        """Test extracting month and day from date."""
        gf = GraphForge()

        gf.execute("CREATE (e:Event {name: 'Party', date: date('2023-12-25')})")

        results = gf.execute("""
            MATCH (e:Event)
            RETURN month(e.date) AS month, day(e.date) AS day
        """)

        assert len(results) == 1
        assert results[0]["month"].value == 12
        assert results[0]["day"].value == 25

    def test_extract_time_components(self):
        """Test extracting hour, minute, second from datetime."""
        gf = GraphForge()

        gf.execute("CREATE (m:Meeting {name: 'Standup', time: datetime('2023-01-15T14:30:45')})")

        results = gf.execute("""
            MATCH (m:Meeting)
            RETURN hour(m.time) AS hour,
                   minute(m.time) AS minute,
                   second(m.time) AS second
        """)

        assert len(results) == 1
        assert results[0]["hour"].value == 14
        assert results[0]["minute"].value == 30
        assert results[0]["second"].value == 45

    def test_current_date_function(self):
        """Test date() without arguments returns current date."""
        gf = GraphForge()

        results = gf.execute("RETURN date() AS today")

        assert len(results) == 1
        today = results[0]["today"]
        assert today.value == datetime.date.today()

    def test_current_datetime_function(self):
        """Test datetime() without arguments returns current datetime."""
        gf = GraphForge()

        results = gf.execute("RETURN datetime() AS now")

        assert len(results) == 1
        now_result = results[0]["now"]
        # Check it's within 1 second of actual now
        now_actual = datetime.datetime.now()
        diff = abs((now_result.value.replace(tzinfo=None) - now_actual).total_seconds())
        assert diff < 1.0


@pytest.mark.integration
class TestTemporalPersistence:
    """Tests for temporal values persisting to disk."""

    def test_temporal_properties_persist(self):
        """Test temporal properties survive database close/reopen."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create and populate database
            gf = GraphForge(str(db_path))
            gf.execute("""
                CREATE (p:Person {
                    name: 'Alice',
                    birthday: date('1990-05-15'),
                    lastLogin: datetime('2023-01-15T10:30:00'),
                    workStartTime: time('09:00:00'),
                    sessionDuration: duration('PT1H30M')
                })
            """)
            gf.close()

            # Reopen and verify
            gf = GraphForge(str(db_path))
            results = gf.execute("""
                MATCH (p:Person)
                RETURN p.birthday AS birthday,
                       p.lastLogin AS lastLogin,
                       p.workStartTime AS workStartTime,
                       p.sessionDuration AS duration
            """)

            assert len(results) == 1

            # Verify all temporal types persisted correctly
            assert results[0]["birthday"].value == datetime.date(1990, 5, 15)
            expected_login = datetime.datetime(2023, 1, 15, 10, 30, 0)
            assert results[0]["lastLogin"].value == expected_login
            assert results[0]["workStartTime"].value == datetime.time(9, 0, 0)
            assert results[0]["duration"].value == datetime.timedelta(hours=1, minutes=30)

            gf.close()


@pytest.mark.integration
class TestTemporalEdgeProperties:
    """Tests for temporal properties on relationships."""

    def test_relationship_with_temporal_property(self):
        """Test creating relationship with temporal properties."""
        gf = GraphForge()

        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'}),
                   (a)-[:FRIENDS_SINCE {since: date('2010-06-15')}]->(b)
        """)

        results = gf.execute("""
            MATCH (a:Person)-[r:FRIENDS_SINCE]->(b:Person)
            RETURN r.since AS since
        """)

        assert len(results) == 1
        assert results[0]["since"].value == datetime.date(2010, 6, 15)

    def test_filter_relationships_by_temporal_property(self):
        """Test filtering relationships by temporal comparison."""
        gf = GraphForge()

        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'}),
                   (c:Person {name: 'Charlie'}),
                   (a)-[:FRIENDS_SINCE {since: date('2005-01-01')}]->(b),
                   (a)-[:FRIENDS_SINCE {since: date('2015-01-01')}]->(c)
        """)

        # Find old friendships (before 2010)
        results = gf.execute("""
            MATCH (a:Person)-[r:FRIENDS_SINCE]->(b:Person)
            WHERE r.since < date('2010-01-01')
            RETURN b.name AS friend
        """)

        assert len(results) == 1
        assert results[0]["friend"].value == "Bob"


@pytest.mark.integration
class TestTemporalMixedTypes:
    """Tests for queries mixing temporal and non-temporal types."""

    def test_mixed_property_types(self):
        """Test node with both temporal and non-temporal properties."""
        gf = GraphForge()

        gf.execute("""
            CREATE (e:Employee {
                name: 'Alice',
                age: 33,
                startDate: date('2020-01-15'),
                salary: 75000.0,
                lastReview: datetime('2023-06-01T14:00:00')
            })
        """)

        results = gf.execute("""
            MATCH (e:Employee)
            RETURN e.name AS name,
                   e.age AS age,
                   e.startDate AS startDate,
                   e.salary AS salary,
                   year(e.startDate) AS startYear
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 33
        assert results[0]["startDate"].value == datetime.date(2020, 1, 15)
        assert results[0]["salary"].value == 75000.0
        assert results[0]["startYear"].value == 2020
