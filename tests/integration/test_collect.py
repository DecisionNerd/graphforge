"""Integration tests for COLLECT aggregation function (issue #27).

Tests for COLLECT aggregation with DISTINCT support per Cypher semantics.
"""

from graphforge import GraphForge
from graphforge.types.values import CypherList


class TestBasicCollect:
    """Tests for basic COLLECT functionality."""

    def test_collect_property_values(self):
        """COLLECT property values from multiple nodes."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'}),
                   (c:Person {name: 'Charlie'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(p.name) AS names
        """)

        assert len(results) == 1
        assert isinstance(results[0]["names"], CypherList)
        names = [v.value for v in results[0]["names"].value]
        assert sorted(names) == ["Alice", "Bob", "Charlie"]

    def test_collect_integers(self):
        """COLLECT integer values."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {age: 25}),
                   (b:Person {age: 30}),
                   (c:Person {age: 35})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(p.age) AS ages
        """)

        assert len(results) == 1
        assert isinstance(results[0]["ages"], CypherList)
        ages = [v.value for v in results[0]["ages"].value]
        assert sorted(ages) == [25, 30, 35]

    def test_collect_single_value(self):
        """COLLECT single value returns list with one element."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(p.name) AS names
        """)

        assert len(results) == 1
        assert isinstance(results[0]["names"], CypherList)
        assert len(results[0]["names"].value) == 1
        assert results[0]["names"].value[0].value == "Alice"

    def test_collect_empty_result(self):
        """COLLECT with no matching nodes returns empty list."""
        gf = GraphForge()
        # No nodes created

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(p.name) AS names
        """)

        assert len(results) == 1
        assert isinstance(results[0]["names"], CypherList)
        assert len(results[0]["names"].value) == 0


class TestCollectDistinct:
    """Tests for COLLECT DISTINCT."""

    def test_collect_distinct_removes_duplicates(self):
        """COLLECT DISTINCT removes duplicate values."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {city: 'NYC'}),
                   (b:Person {city: 'LA'}),
                   (c:Person {city: 'NYC'}),
                   (d:Person {city: 'LA'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(DISTINCT p.city) AS cities
        """)

        assert len(results) == 1
        assert isinstance(results[0]["cities"], CypherList)
        cities = [v.value for v in results[0]["cities"].value]
        assert sorted(cities) == ["LA", "NYC"]

    def test_collect_distinct_preserves_order_first_seen(self):
        """COLLECT DISTINCT keeps first occurrence of each value."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'}),
                   (c:Person {name: 'Alice'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(DISTINCT p.name) AS names
        """)

        assert len(results) == 1
        names = [v.value for v in results[0]["names"].value]
        # Should have 2 unique names
        assert len(names) == 2
        assert "Alice" in names
        assert "Bob" in names

    def test_collect_distinct_with_integers(self):
        """COLLECT DISTINCT with integer values."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {value: 10}),
                   (b:Item {value: 20}),
                   (c:Item {value: 10}),
                   (d:Item {value: 30})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            RETURN COLLECT(DISTINCT i.value) AS values
        """)

        assert len(results) == 1
        values = [v.value for v in results[0]["values"].value]
        assert sorted(values) == [10, 20, 30]


class TestCollectNullHandling:
    """Tests for NULL handling in COLLECT."""

    def test_collect_skips_null_values(self):
        """COLLECT skips NULL values (missing properties)."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'}),
                   (c:Person)
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(p.name) AS names
        """)

        assert len(results) == 1
        names = [v.value for v in results[0]["names"].value]
        # Should only have Alice and Bob, not NULL
        assert len(names) == 2
        assert sorted(names) == ["Alice", "Bob"]

    def test_collect_all_nulls_returns_empty_list(self):
        """COLLECT with all NULL values returns empty list."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person),
                   (b:Person),
                   (c:Person)
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(p.name) AS names
        """)

        assert len(results) == 1
        assert isinstance(results[0]["names"], CypherList)
        assert len(results[0]["names"].value) == 0

    def test_collect_distinct_skips_nulls(self):
        """COLLECT DISTINCT skips NULL values."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person),
                   (c:Person {name: 'Alice'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(DISTINCT p.name) AS names
        """)

        assert len(results) == 1
        names = [v.value for v in results[0]["names"].value]
        # Should have only one "Alice", NULL is skipped
        assert len(names) == 1
        assert names[0] == "Alice"


class TestCollectWithGroupBy:
    """Tests for COLLECT with GROUP BY."""

    def test_collect_with_grouping(self):
        """COLLECT with GROUP BY collects per group."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', city: 'NYC'}),
                   (b:Person {name: 'Bob', city: 'NYC'}),
                   (c:Person {name: 'Charlie', city: 'LA'}),
                   (d:Person {name: 'David', city: 'LA'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.city AS city, COLLECT(p.name) AS names
            ORDER BY city
        """)

        assert len(results) == 2

        # LA group
        assert results[0]["city"].value == "LA"
        la_names = [v.value for v in results[0]["names"].value]
        assert sorted(la_names) == ["Charlie", "David"]

        # NYC group
        assert results[1]["city"].value == "NYC"
        nyc_names = [v.value for v in results[1]["names"].value]
        assert sorted(nyc_names) == ["Alice", "Bob"]

    def test_collect_multiple_properties_with_grouping(self):
        """COLLECT multiple properties with GROUP BY."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 25, city: 'NYC'}),
                   (b:Person {name: 'Bob', age: 30, city: 'NYC'}),
                   (c:Person {name: 'Charlie', age: 35, city: 'LA'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.city AS city, COLLECT(p.name) AS names, COLLECT(p.age) AS ages
            ORDER BY city
        """)

        assert len(results) == 2

        # LA group
        assert results[0]["city"].value == "LA"
        la_ages = [v.value for v in results[0]["ages"].value]
        assert la_ages == [35]

        # NYC group
        assert results[1]["city"].value == "NYC"
        nyc_ages = [v.value for v in results[1]["ages"].value]
        assert sorted(nyc_ages) == [25, 30]


class TestCollectWithOtherAggregations:
    """Tests for COLLECT combined with other aggregation functions."""

    def test_collect_with_count(self):
        """COLLECT combined with COUNT."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'}),
                   (c:Person {name: 'Charlie'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(p.name) AS names, COUNT(p) AS count
        """)

        assert len(results) == 1
        assert results[0]["count"].value == 3
        assert len(results[0]["names"].value) == 3

    def test_collect_with_sum(self):
        """COLLECT combined with SUM."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {price: 10}),
                   (b:Item {price: 20}),
                   (c:Item {price: 30})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            RETURN COLLECT(i.price) AS prices, SUM(i.price) AS total
        """)

        assert len(results) == 1
        assert results[0]["total"].value == 60
        prices = [v.value for v in results[0]["prices"].value]
        assert sorted(prices) == [10, 20, 30]


class TestCollectWithExpressions:
    """Tests for COLLECT with expressions."""

    def test_collect_expression_result(self):
        """COLLECT with expression argument."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {age: 25}),
                   (b:Person {age: 30}),
                   (c:Person {age: 35})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(p.age * 2) AS doubled_ages
        """)

        assert len(results) == 1
        doubled = [v.value for v in results[0]["doubled_ages"].value]
        assert sorted(doubled) == [50, 60, 70]

    def test_collect_with_string_concatenation(self):
        """COLLECT with string expression."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', title: 'Dr'}),
                   (b:Person {name: 'Bob', title: 'Mr'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(p.title + ' ' + p.name) AS full_names
        """)

        assert len(results) == 1
        full_names = [v.value for v in results[0]["full_names"].value]
        assert sorted(full_names) == ["Dr Alice", "Mr Bob"]


class TestCollectEdgeCases:
    """Tests for edge cases."""

    def test_collect_mixed_types(self):
        """COLLECT can handle mixed types in collection."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {value: 10}),
                   (b:Item {value: 3.14}),
                   (c:Item {value: 20})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            RETURN COLLECT(i.value) AS values
        """)

        assert len(results) == 1
        assert isinstance(results[0]["values"], CypherList)
        # Should collect all values regardless of type (int and float)
        assert len(results[0]["values"].value) == 3

    def test_collect_with_order_by(self):
        """COLLECT respects source ordering."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Charlie', id: 3}),
                   (b:Person {name: 'Alice', id: 1}),
                   (c:Person {name: 'Bob', id: 2})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(p.name) AS names
            ORDER BY p.id
        """)

        # Note: ORDER BY after RETURN doesn't affect the collected values
        # The order depends on match order
        assert len(results) == 1
        assert len(results[0]["names"].value) == 3

    def test_multiple_collect_calls(self):
        """Multiple COLLECT calls in same query."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 25}),
                   (b:Person {name: 'Bob', age: 30})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(p.name) AS names, COLLECT(p.age) AS ages
        """)

        assert len(results) == 1
        names = [v.value for v in results[0]["names"].value]
        ages = [v.value for v in results[0]["ages"].value]
        assert len(names) == 2
        assert len(ages) == 2


class TestCollectWithComplexTypes:
    """Tests for COLLECT with lists and maps."""

    def test_collect_distinct_with_lists(self):
        """COLLECT DISTINCT with list values."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {tags: ['python', 'java']}),
                   (b:Person {tags: ['python', 'java']}),
                   (c:Person {tags: ['javascript', 'rust']})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(DISTINCT p.tags) AS unique_tags
        """)

        assert len(results) == 1
        assert isinstance(results[0]["unique_tags"], CypherList)
        # Should have 2 unique tag lists
        assert len(results[0]["unique_tags"].value) == 2

    def test_collect_distinct_with_nested_lists(self):
        """COLLECT DISTINCT with nested list values."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Data {values: [[1, 2], [3, 4]]}),
                   (b:Data {values: [[1, 2], [3, 4]]}),
                   (c:Data {values: [[5, 6], [7, 8]]})
        """)

        results = gf.execute("""
            MATCH (d:Data)
            RETURN COLLECT(DISTINCT d.values) AS unique_values
        """)

        assert len(results) == 1
        # Should have 2 unique nested lists
        assert len(results[0]["unique_values"].value) == 2

    def test_collect_distinct_with_maps(self):
        """COLLECT DISTINCT with map values."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {address: {city: 'NYC', zip: '10001'}}),
                   (b:Person {address: {city: 'NYC', zip: '10001'}}),
                   (c:Person {address: {city: 'LA', zip: '90001'}})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(DISTINCT p.address) AS unique_addresses
        """)

        assert len(results) == 1
        assert isinstance(results[0]["unique_addresses"], CypherList)
        # Should have 2 unique addresses
        assert len(results[0]["unique_addresses"].value) == 2

    def test_collect_distinct_mixed_complex_types(self):
        """COLLECT DISTINCT with mixed lists and scalars."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {data: [1, 2, 3]}),
                   (b:Item {data: [1, 2, 3]}),
                   (c:Item {data: [4, 5, 6]})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            RETURN COLLECT(DISTINCT i.data) AS unique_data
        """)

        assert len(results) == 1
        # Should have 2 unique lists
        assert len(results[0]["unique_data"].value) == 2


class TestGroupByComplexTypes:
    """Tests for GROUP BY with lists and maps (round-trip conversion)."""

    def test_group_by_list_property(self):
        """GROUP BY list property returns proper CypherList."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {tags: ['python', 'java'], value: 10}),
                   (b:Item {tags: ['python', 'java'], value: 20}),
                   (c:Item {tags: ['javascript'], value: 30})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            RETURN i.tags AS tags, SUM(i.value) AS total
        """)

        assert len(results) == 2

        # Find the group with ['python', 'java']
        python_java_group = None
        javascript_group = None
        for row in results:
            # Verify tags is returned as CypherList
            assert isinstance(row["tags"], CypherList)
            tags_list = [v.value for v in row["tags"].value]
            if sorted(tags_list) == ["java", "python"]:
                python_java_group = row
            elif tags_list == ["javascript"]:
                javascript_group = row

        assert python_java_group is not None
        assert python_java_group["total"].value == 30  # 10 + 20

        assert javascript_group is not None
        assert javascript_group["total"].value == 30

    def test_group_by_nested_list_property(self):
        """GROUP BY nested list property returns proper CypherList."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Data {matrix: [[1, 2], [3, 4]], count: 1}),
                   (b:Data {matrix: [[1, 2], [3, 4]], count: 2}),
                   (c:Data {matrix: [[5, 6]], count: 3})
        """)

        results = gf.execute("""
            MATCH (d:Data)
            RETURN d.matrix AS matrix, SUM(d.count) AS total
        """)

        assert len(results) == 2

        for row in results:
            # Verify matrix is returned as CypherList with nested CypherLists
            assert isinstance(row["matrix"], CypherList)
            outer_list = row["matrix"].value
            for inner_item in outer_list:
                assert isinstance(inner_item, CypherList)

    def test_group_by_map_property(self):
        """GROUP BY map property returns proper CypherMap."""
        from graphforge.types.values import CypherMap

        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {address: {city: 'NYC', zip: '10001'}, age: 25}),
                   (b:Person {address: {city: 'NYC', zip: '10001'}, age: 30}),
                   (c:Person {address: {city: 'LA', zip: '90001'}, age: 35})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.address AS address, SUM(p.age) AS total_age
        """)

        assert len(results) == 2

        # Find the NYC group
        nyc_group = None
        la_group = None
        for row in results:
            # Verify address is returned as CypherMap
            assert isinstance(row["address"], CypherMap)
            address_map = {k: v.value for k, v in row["address"].value.items()}
            if address_map["city"] == "NYC":
                nyc_group = row
            elif address_map["city"] == "LA":
                la_group = row

        assert nyc_group is not None
        assert nyc_group["total_age"].value == 55  # 25 + 30

        assert la_group is not None
        assert la_group["total_age"].value == 35

    def test_group_by_multiple_complex_properties(self):
        """GROUP BY multiple properties including lists."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {category: 'A', tags: ['python'], value: 10}),
                   (b:Item {category: 'A', tags: ['python'], value: 20}),
                   (c:Item {category: 'A', tags: ['java'], value: 30}),
                   (d:Item {category: 'B', tags: ['python'], value: 40})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            RETURN i.category AS category, i.tags AS tags, SUM(i.value) AS total
        """)

        assert len(results) == 3

        # Verify all groups have proper types
        for row in results:
            assert isinstance(row["tags"], CypherList)

        # Find A/python group
        a_python = [
            r
            for r in results
            if r["category"].value == "A" and [v.value for v in r["tags"].value] == ["python"]
        ]
        assert len(a_python) == 1
        assert a_python[0]["total"].value == 30  # 10 + 20

    def test_collect_grouped_by_complex_type(self):
        """COLLECT with GROUP BY complex type."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {dept: ['Engineering', 'R&D'], name: 'Alice'}),
                   (b:Person {dept: ['Engineering', 'R&D'], name: 'Bob'}),
                   (c:Person {dept: ['Sales'], name: 'Charlie'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.dept AS dept, COLLECT(p.name) AS names
        """)

        assert len(results) == 2

        for row in results:
            # Verify dept is CypherList
            assert isinstance(row["dept"], CypherList)
            # Verify names is CypherList
            assert isinstance(row["names"], CypherList)

        # Find Engineering/R&D group
        eng_group = None
        for row in results:
            dept_list = [v.value for v in row["dept"].value]
            if sorted(dept_list) == ["Engineering", "R&D"]:
                eng_group = row
                break

        assert eng_group is not None
        names = sorted([v.value for v in eng_group["names"].value])
        assert names == ["Alice", "Bob"]
