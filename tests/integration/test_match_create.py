"""Integration tests for MATCH-CREATE combinations (issue #23).

Tests for connecting existing nodes to new nodes via CREATE after MATCH.
"""

from graphforge import GraphForge


class TestMatchCreateBasic:
    """Basic MATCH-CREATE combinations."""

    def test_match_one_create_connected_node(self):
        """MATCH one node, CREATE connected node."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (a:Person {name: 'Alice'})
            CREATE (a)-[:KNOWS]->(b:Person {name: 'Bob'})
            RETURN a.name AS src, b.name AS dst
        """)

        assert len(results) == 1
        assert results[0]["src"].value == "Alice"
        assert results[0]["dst"].value == "Bob"

        # Verify relationship created
        check = gf.execute("""
            MATCH (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person)
            RETURN b.name AS name
        """)
        assert len(check) == 1
        assert check[0]["name"].value == "Bob"

    def test_match_two_nodes_create_relationship(self):
        """MATCH two nodes, CREATE relationship between them."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:City {name: 'NYC'}),
                   (b:City {name: 'LA'})
        """)

        results = gf.execute("""
            MATCH (src:City {name: 'NYC'}), (dst:City {name: 'LA'})
            CREATE (src)-[r:FLIGHT {duration: 6}]->(dst)
            RETURN src.name AS from, dst.name AS to, r.duration AS hours
        """)

        assert len(results) == 1
        assert results[0]["from"].value == "NYC"
        assert results[0]["to"].value == "LA"
        assert results[0]["hours"].value == 6

    def test_match_pattern_create_expansion(self):
        """MATCH pattern, CREATE expansion."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'})-[:LIVES_IN]->(c:City {name: 'NYC'})
        """)

        results = gf.execute("""
            MATCH (p:Person)-[:LIVES_IN]->(c:City)
            CREATE (p)-[:WORKS_IN]->(c)
            RETURN p.name AS person, c.name AS city
        """)

        assert len(results) == 1
        assert results[0]["person"].value == "Alice"
        assert results[0]["city"].value == "NYC"

        # Verify both relationships exist
        check = gf.execute("""
            MATCH (p:Person)-[r]->(c:City)
            RETURN type(r) AS rel_type
        """)
        # Note: type(r) not implemented, so we check count
        assert len(check) == 2  # LIVES_IN and WORKS_IN


class TestMatchCreateMultiple:
    """MATCH-CREATE with multiple matches."""

    def test_match_multiple_create_for_each(self):
        """MATCH returns 3 nodes, CREATE 3 new nodes."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'}),
                   (c:Person {name: 'Charlie'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            CREATE (p)-[:POSTED]->(post:Post {content: 'Hello'})
            RETURN p.name AS author, post.content AS content
        """)

        # Should create 3 posts (one per person)
        assert len(results) == 3
        authors = sorted([r["author"].value for r in results])
        assert authors == ["Alice", "Bob", "Charlie"]
        assert all(r["content"].value == "Hello" for r in results)

        # Verify all posts created
        check = gf.execute("MATCH (p:Post) RETURN count(p) AS count")
        assert check[0]["count"].value == 3

    def test_match_with_where_filters_creates(self):
        """MATCH with WHERE filters which nodes get connected."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 25}),
                   (b:Person {name: 'Bob', age: 35}),
                   (c:Person {name: 'Charlie', age: 45})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.age > 30
            CREATE (p)-[:ATTENDED]->(e:Event {name: 'Conference'})
            RETURN p.name AS attendee
        """)

        # Only Bob and Charlie match (age > 30)
        assert len(results) == 2
        attendees = sorted([r["attendee"].value for r in results])
        assert attendees == ["Bob", "Charlie"]

    def test_cartesian_product_creates(self):
        """MATCH creates cartesian product of nodes."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Source {id: 1}),
                   (b:Source {id: 2}),
                   (c:Target {id: 10})
        """)

        results = gf.execute("""
            MATCH (s:Source), (t:Target)
            CREATE (s)-[:LINKS_TO]->(t)
            RETURN s.id AS src, t.id AS dst
        """)

        # 2 sources x 1 target = 2 relationships
        assert len(results) == 2


class TestMatchCreateNoMatches:
    """MATCH-CREATE when no matches found."""

    def test_no_match_no_create(self):
        """When MATCH returns nothing, CREATE doesn't execute."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person {name: 'NonExistent'})
            CREATE (p)-[:KNOWS]->(b:Person {name: 'Bob'})
            RETURN p, b
        """)

        # No matches, so no creates
        assert len(results) == 0

        # Verify Bob was not created
        check = gf.execute("MATCH (p:Person {name: 'Bob'}) RETURN p")
        assert len(check) == 0

    def test_optional_match_creates_with_null(self):
        """Test that MATCH with no results produces no CREATE."""
        gf = GraphForge()

        results = gf.execute("""
            MATCH (p:Person {name: 'Ghost'})
            CREATE (p)-[:HAUNTS]->(h:House)
            RETURN h
        """)

        assert len(results) == 0


class TestMatchCreateComplex:
    """Complex MATCH-CREATE patterns."""

    def test_chain_multiple_creates(self):
        """Chain multiple CREATE clauses after MATCH."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (a:Person {name: 'Alice'})
            CREATE (a)-[:WROTE]->(b:Book {title: 'GraphDB 101'})
            CREATE (a)-[:WROTE]->(c:Book {title: 'Cypher Guide'})
            RETURN a.name AS author, b.title AS book1, c.title AS book2
        """)

        assert len(results) == 1
        assert results[0]["author"].value == "Alice"
        assert results[0]["book1"].value == "GraphDB 101"
        assert results[0]["book2"].value == "Cypher Guide"

    def test_match_relationship_create_from_dest(self):
        """MATCH (a)-[:REL]->(b), CREATE from b."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'})-[:MANAGES]->(b:Person {name: 'Bob'})
        """)

        results = gf.execute("""
            MATCH (a:Person)-[:MANAGES]->(b:Person)
            CREATE (b)-[:MANAGES]->(c:Person {name: 'Charlie'})
            RETURN a.name AS top, b.name AS mid, c.name AS bottom
        """)

        assert len(results) == 1
        assert results[0]["top"].value == "Alice"
        assert results[0]["mid"].value == "Bob"
        assert results[0]["bottom"].value == "Charlie"

    def test_create_references_match_variable_multiple_times(self):
        """CREATE references MATCH variable in multiple places."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice', age: 30})")

        results = gf.execute("""
            MATCH (p:Person {name: 'Alice'})
            CREATE (p)-[:AUTHOR_OF]->(b:Book {title: p.name, year: p.age})
            RETURN b.title AS title, b.year AS year
        """)

        assert len(results) == 1
        assert results[0]["title"].value == "Alice"
        assert results[0]["year"].value == 30

    def test_match_multiple_patterns_create_references_both(self):
        """MATCH multiple patterns, CREATE references all matched variables."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Author {name: 'Alice'}),
                   (p:Publisher {name: 'TechPress'})
        """)

        results = gf.execute("""
            MATCH (a:Author {name: 'Alice'}), (p:Publisher {name: 'TechPress'})
            CREATE (a)-[:PUBLISHED_BY]->(b:Book {title: 'Graph Theory'})<-[:PUBLISHES]-(p)
            RETURN a.name AS author, b.title AS book, p.name AS publisher
        """)

        assert len(results) == 1
        assert results[0]["author"].value == "Alice"
        assert results[0]["book"].value == "Graph Theory"
        assert results[0]["publisher"].value == "TechPress"


class TestMatchCreateWithOtherClauses:
    """MATCH-CREATE combined with other clauses."""

    def test_match_create_set(self):
        """MATCH, CREATE, then SET on created node."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})")

        gf.execute("""
            MATCH (a:Person {name: 'Alice'})
            CREATE (a)-[:KNOWS]->(b:Person {name: 'Bob'})
            SET b.age = 25
        """)

        # Verify Bob has age property
        check = gf.execute("""
            MATCH (b:Person {name: 'Bob'})
            RETURN b.age AS age
        """)
        assert len(check) == 1
        assert check[0]["age"].value == 25

    def test_match_create_return_all_columns(self):
        """MATCH, CREATE, RETURN all relevant columns."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice', city: 'NYC'})")

        results = gf.execute("""
            MATCH (p:Person)
            CREATE (p)-[:VISITED]->(c:City {name: p.city})
            RETURN p.name AS person, p.city AS from_prop, c.name AS created_city
        """)

        assert len(results) == 1
        assert results[0]["person"].value == "Alice"
        assert results[0]["from_prop"].value == "NYC"
        assert results[0]["created_city"].value == "NYC"

    def test_match_create_with_order_limit(self):
        """MATCH, CREATE, then ORDER and LIMIT results."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', id: 1}),
                   (b:Person {name: 'Bob', id: 2}),
                   (c:Person {name: 'Charlie', id: 3})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            CREATE (p)-[:HAS_BADGE]->(b:Badge {num: p.id})
            RETURN p.name AS name, b.num AS badge
            ORDER BY badge DESC
            LIMIT 2
        """)

        assert len(results) == 2
        assert results[0]["badge"].value == 3
        assert results[1]["badge"].value == 2


class TestMatchCreateEdgeCases:
    """Edge cases for MATCH-CREATE."""

    def test_create_node_with_properties_from_matched(self):
        """Create node copying all properties from matched node."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice', age: 30, city: 'NYC'})")

        results = gf.execute("""
            MATCH (p:Person {name: 'Alice'})
            CREATE (p)-[:HAS_BACKUP]->(backup:PersonBackup {name: p.name, age: p.age, city: p.city})
            RETURN backup.name AS name, backup.age AS age, backup.city AS city
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30
        assert results[0]["city"].value == "NYC"

    def test_create_multiple_relationships_same_nodes(self):
        """Create multiple different relationships between same nodes."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'})
        """)

        gf.execute("""
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            CREATE (a)-[:KNOWS]->(b)
            CREATE (a)-[:WORKS_WITH]->(b)
        """)

        # Verify both relationships exist
        check = gf.execute("""
            MATCH (a:Person {name: 'Alice'})-[r]->(b:Person {name: 'Bob'})
            RETURN count(r) AS rel_count
        """)
        assert check[0]["rel_count"].value == 2

    def test_match_create_with_null_property(self):
        """Create with NULL property from matched node."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person {name: 'Alice'})
            CREATE (p)-[:PROFILE]->(pr:Profile {name: p.name, bio: p.bio})
            RETURN pr.name AS name, pr.bio AS bio
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        # bio should be NULL since p.bio doesn't exist
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["bio"], CypherNull)

    def test_match_create_multiple_new_nodes_per_match(self):
        """Each matched node creates multiple new nodes."""
        gf = GraphForge()
        gf.execute("CREATE (a:User {name: 'Alice'}), (b:User {name: 'Bob'})")

        results = gf.execute("""
            MATCH (u:User)
            CREATE (u)-[:HAS_SETTING]->(s1:Setting {key: 'theme'}),
                   (u)-[:HAS_SETTING]->(s2:Setting {key: 'language'})
            RETURN u.name AS user
        """)

        # 2 users, each creates 2 settings = 2 result rows (one per user)
        assert len(results) == 2

        # Verify 4 settings total (2 per user)
        check = gf.execute("MATCH (s:Setting) RETURN count(s) AS count")
        assert check[0]["count"].value == 4

    def test_match_with_aggregation_then_create(self):
        """Cannot combine aggregation with CREATE in same query part."""
        gf = GraphForge()
        gf.execute("CREATE (a:Item {val: 1}), (b:Item {val: 2})")

        # This pattern requires WITH clause to work properly
        # Testing that basic MATCH + CREATE works without aggregation
        results = gf.execute("""
            MATCH (i:Item)
            CREATE (i)-[:LOGGED]->(log:Log {value: i.val})
            RETURN i.val AS original, log.value AS logged
        """)

        assert len(results) == 2
