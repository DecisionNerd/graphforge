"""Integration tests for ORDER BY after aggregation (issue #36).

Tests for ORDER BY working correctly after WITH + aggregation.
"""

from graphforge import GraphForge


class TestSortAfterAggregation:
    """Tests for ORDER BY after aggregation."""

    def test_order_by_aggregated_column(self):
        """ORDER BY on aggregated column."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Sale {product: 'A', amount: 100}),
                   (b:Sale {product: 'A', amount: 150}),
                   (c:Sale {product: 'B', amount: 200}),
                   (d:Sale {product: 'C', amount: 50})
        """)

        results = gf.execute("""
            MATCH (s:Sale)
            WITH s.product AS product, SUM(s.amount) AS total
            ORDER BY total DESC
            RETURN product, total
        """)

        assert len(results) == 3
        assert results[0]["product"].value == "A"
        assert results[0]["total"].value == 250
        assert results[1]["product"].value == "B"
        assert results[1]["total"].value == 200
        assert results[2]["product"].value == "C"
        assert results[2]["total"].value == 50

    def test_order_by_grouping_column(self):
        """ORDER BY on grouping column (not aggregated)."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {category: 'Z', val: 10}),
                   (b:Item {category: 'A', val: 20}),
                   (c:Item {category: 'M', val: 30})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH i.category AS cat, COUNT(i) AS count
            ORDER BY cat ASC
            RETURN cat, count
        """)

        assert len(results) == 3
        assert results[0]["cat"].value == "A"
        assert results[1]["cat"].value == "M"
        assert results[2]["cat"].value == "Z"

    def test_order_by_with_skip_limit(self):
        """ORDER BY after aggregation with SKIP and LIMIT."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {type: 'A', val: 10}),
                   (b:Item {type: 'A', val: 20}),
                   (c:Item {type: 'B', val: 30}),
                   (d:Item {type: 'B', val: 40}),
                   (e:Item {type: 'C', val: 50}),
                   (f:Item {type: 'C', val: 60})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH i.type AS type, SUM(i.val) AS total
            ORDER BY total DESC
            SKIP 1
            LIMIT 1
            RETURN type, total
        """)

        # Order: C(110), B(70), A(30) -> Skip 1 -> Limit 1 -> B(70)
        assert len(results) == 1
        assert results[0]["type"].value == "B"
        assert results[0]["total"].value == 70

    def test_order_by_ascending(self):
        """ORDER BY ASC after aggregation."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {cat: 'A', val: 100}),
                   (b:Item {cat: 'B', val: 50}),
                   (c:Item {cat: 'C', val: 75})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH i.cat AS category, SUM(i.val) AS total
            ORDER BY total ASC
            RETURN category, total
        """)

        assert len(results) == 3
        assert results[0]["total"].value == 50
        assert results[1]["total"].value == 75
        assert results[2]["total"].value == 100

    def test_order_by_multiple_aggregates(self):
        """ORDER BY with multiple aggregate functions."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {cat: 'A', val: 10}),
                   (b:Item {cat: 'A', val: 20}),
                   (c:Item {cat: 'B', val: 30}),
                   (d:Item {cat: 'B', val: 40}),
                   (e:Item {cat: 'C', val: 50})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH i.cat AS category, COUNT(i) AS count, SUM(i.val) AS total
            ORDER BY count DESC, total ASC
            RETURN category, count, total
        """)

        # A: count=2, total=30
        # B: count=2, total=70
        # C: count=1, total=50
        # Order by count DESC, total ASC: A(2,30), B(2,70), C(1,50)
        assert len(results) == 3
        assert results[0]["category"].value == "A"
        assert results[0]["count"].value == 2
        assert results[0]["total"].value == 30

    def test_order_by_avg_aggregate(self):
        """ORDER BY with AVG aggregate."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Student {class: 'A', score: 80}),
                   (b:Student {class: 'A', score: 90}),
                   (c:Student {class: 'B', score: 70}),
                   (d:Student {class: 'B', score: 80}),
                   (e:Student {class: 'C', score: 95})
        """)

        results = gf.execute("""
            MATCH (s:Student)
            WITH s.class AS class, AVG(s.score) AS avg_score
            ORDER BY avg_score DESC
            RETURN class, avg_score
        """)

        # C: 95, A: 85, B: 75
        assert len(results) == 3
        assert results[0]["class"].value == "C"
        assert results[0]["avg_score"].value == 95.0
        assert results[1]["class"].value == "A"
        assert results[1]["avg_score"].value == 85.0

    def test_order_by_min_max(self):
        """ORDER BY with MIN and MAX aggregates."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {group: 'X', val: 10}),
                   (b:Item {group: 'X', val: 50}),
                   (c:Item {group: 'Y', val: 20}),
                   (d:Item {group: 'Y', val: 60})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH i.group AS grp, MIN(i.val) AS min_val, MAX(i.val) AS max_val
            ORDER BY max_val DESC
            RETURN grp, min_val, max_val
        """)

        # Y: min=20, max=60
        # X: min=10, max=50
        assert len(results) == 2
        assert results[0]["grp"].value == "Y"
        assert results[0]["max_val"].value == 60

    def test_order_by_count(self):
        """ORDER BY with COUNT aggregate."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {type: 'A'}),
                   (b:Item {type: 'A'}),
                   (c:Item {type: 'A'}),
                   (d:Item {type: 'B'}),
                   (e:Item {type: 'C'}),
                   (f:Item {type: 'C'})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH i.type AS type, COUNT(i) AS count
            ORDER BY count DESC
            RETURN type, count
        """)

        # A: 3, C: 2, B: 1
        assert len(results) == 3
        assert results[0]["type"].value == "A"
        assert results[0]["count"].value == 3
        assert results[1]["type"].value == "C"
        assert results[1]["count"].value == 2

    def test_order_by_with_where_before_aggregation(self):
        """ORDER BY after aggregation with WHERE before aggregation."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {cat: 'A', val: 10}),
                   (b:Item {cat: 'A', val: 20}),
                   (c:Item {cat: 'B', val: 5}),
                   (d:Item {cat: 'B', val: 30}),
                   (e:Item {cat: 'C', val: 50})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WHERE i.val > 10
            WITH i.cat AS category, SUM(i.val) AS total
            ORDER BY total DESC
            RETURN category, total
        """)

        # After filter: A(20), B(30), C(50)
        # Aggregated: A: 20, B: 30, C: 50
        # Ordered DESC: C(50), B(30), A(20)
        assert len(results) == 3
        assert results[0]["category"].value == "C"
        assert results[0]["total"].value == 50

    def test_order_by_without_aggregation_still_works(self):
        """Ensure ORDER BY without aggregation still works (regression test)."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {name: 'C', val: 3}),
                   (b:Item {name: 'A', val: 1}),
                   (c:Item {name: 'B', val: 2})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH i.name AS name, i.val AS value
            ORDER BY value ASC
            RETURN name, value
        """)

        assert len(results) == 3
        assert results[0]["name"].value == "A"
        assert results[0]["value"].value == 1
        assert results[1]["name"].value == "B"
        assert results[1]["value"].value == 2

    def test_order_by_alias_defined_in_return(self):
        """ORDER BY can reference alias defined in RETURN (without aggregation)."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {x: 3}),
                   (b:Item {x: 1}),
                   (c:Item {x: 2})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            RETURN i.x AS value
            ORDER BY value ASC
        """)

        assert len(results) == 3
        assert results[0]["value"].value == 1
        assert results[1]["value"].value == 2
        assert results[2]["value"].value == 3

    def test_order_by_multiple_columns_after_aggregation(self):
        """ORDER BY multiple columns after aggregation."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {cat: 'A', type: 'X', val: 10}),
                   (b:Item {cat: 'A', type: 'Y', val: 20}),
                   (c:Item {cat: 'B', type: 'X', val: 30}),
                   (d:Item {cat: 'B', type: 'Y', val: 40})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            WITH i.cat AS category, i.type AS type, SUM(i.val) AS total
            ORDER BY category DESC, type ASC
            RETURN category, type, total
        """)

        # B,X: 30; B,Y: 40; A,X: 10; A,Y: 20
        # Order by cat DESC, type ASC: B,X; B,Y; A,X; A,Y
        assert len(results) == 4
        assert results[0]["category"].value == "B"
        assert results[0]["type"].value == "X"
        assert results[1]["category"].value == "B"
        assert results[1]["type"].value == "Y"
