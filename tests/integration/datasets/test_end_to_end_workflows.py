"""End-to-end workflow tests for dataset integration.

These tests demonstrate typical use cases for loading and querying datasets
with GraphForge, showcasing real-world query patterns and workflows.
"""

import pytest

from graphforge import GraphForge
from graphforge.datasets import get_dataset_info, list_datasets, load_dataset


class TestDatasetDiscovery:
    """Test dataset discovery and metadata access."""

    def test_list_all_datasets(self):
        """List all available datasets."""
        datasets = list_datasets()
        assert len(datasets) > 0, "Should have registered datasets"

        # Verify each dataset has required metadata
        for ds_info in datasets:
            assert hasattr(ds_info, "name")
            assert hasattr(ds_info, "nodes")
            assert hasattr(ds_info, "edges")
            assert hasattr(ds_info, "category")

    def test_filter_by_category(self):
        """Filter datasets by category."""
        social_datasets = list_datasets(category="social")
        assert len(social_datasets) > 0

        # Verify all are social category
        for ds in social_datasets:
            assert ds.category == "social"

    def test_filter_by_size(self):
        """Filter datasets by maximum size."""
        small_datasets = list_datasets(max_size_mb=5.0)
        assert len(small_datasets) > 0

        # Verify all are within size limit
        for ds in small_datasets:
            if hasattr(ds, "size_mb") and ds.size_mb is not None:
                assert ds.size_mb <= 5.0

    def test_get_dataset_info_by_name(self):
        """Get specific dataset metadata by name."""
        # Use a known small dataset
        info = get_dataset_info("snap-ca-grqc")
        assert info.name == "snap-ca-grqc"
        assert info.category == "collaboration"
        assert info.nodes == 5242
        assert info.edges == 14496


class TestSmallDatasetLoading:
    """Test loading and querying small datasets (<5MB)."""

    def test_load_collaboration_network(self):
        """Load and query a collaboration network."""
        gf = GraphForge()

        # Load small collaboration dataset (General Relativity)
        load_dataset(gf, "snap-ca-grqc")

        # Verify data loaded
        node_count = gf.execute("MATCH (n) RETURN count(n) AS count")[0]["count"].value
        assert node_count == 5242

        # SNAP datasets are undirected, so edges are stored bidirectionally
        # (approximately 2x the listed edge count, accounting for any self-loops)
        edge_count = gf.execute("MATCH ()-[r]->() RETURN count(r) AS count")[0]["count"].value
        assert edge_count > 28000 and edge_count < 30000  # ~2x edges for undirected

    @pytest.mark.skip(reason="size() with list comprehension in WITH not yet supported")
    def test_query_degree_distribution(self):
        """Query degree distribution of a network."""
        gf = GraphForge()
        load_dataset(gf, "snap-ca-grqc")

        # Get degree distribution
        results = gf.execute("""
            MATCH (n)
            WITH n, size([(n)-->() | 1]) AS out_degree
            RETURN out_degree, count(*) AS count
            ORDER BY out_degree DESC
            LIMIT 5
        """)

        assert len(results) > 0
        # Verify results are sorted by degree descending
        prev_degree = float("inf")
        for row in results:
            degree = row["out_degree"].value
            assert degree <= prev_degree
            prev_degree = degree

    @pytest.mark.skip(reason="size() with list comprehension in WITH not yet supported")
    def test_find_high_degree_nodes(self):
        """Find nodes with highest connectivity."""
        gf = GraphForge()
        load_dataset(gf, "snap-ca-grqc")

        # Find top 10 most connected nodes
        results = gf.execute("""
            MATCH (n)
            WITH n, size([(n)--() | 1]) AS degree
            WHERE degree > 10
            RETURN n.id AS node_id, degree
            ORDER BY degree DESC
            LIMIT 10
        """)

        assert len(results) > 0
        # Verify all have degree > 10
        for row in results:
            assert row["degree"].value > 10


class TestComplexQueries:
    """Test complex query patterns on real datasets."""

    @pytest.mark.skip(reason="size() with list comprehension in WITH not yet supported")
    def test_optional_match_pattern(self):
        """Use OPTIONAL MATCH to find nodes with optional relationships."""
        gf = GraphForge()
        load_dataset(gf, "snap-ca-grqc")

        # Find nodes and their optional connections to high-degree nodes
        results = gf.execute("""
            MATCH (n)
            WITH n, size([(n)-->() | 1]) AS n_degree
            WHERE n_degree > 0
            OPTIONAL MATCH (n)-->(m)
            WITH n, n_degree, count(m) AS connection_count
            RETURN n_degree, connection_count
            LIMIT 5
        """)

        assert len(results) > 0

    @pytest.mark.skip(reason="size() with list comprehension in WITH not yet supported")
    def test_union_query_pattern(self):
        """Use UNION to combine results from different patterns."""
        gf = GraphForge()
        load_dataset(gf, "snap-ca-grqc")

        # Get high and low degree nodes separately, then combine
        results = gf.execute("""
            MATCH (n)
            WITH n, size([(n)-->() | 1]) AS degree
            WHERE degree > 20
            RETURN 'high' AS category, count(*) AS count
            UNION ALL
            MATCH (n)
            WITH n, size([(n)-->() | 1]) AS degree
            WHERE degree <= 20
            RETURN 'low' AS category, count(*) AS count
        """)

        assert len(results) == 2
        categories = {r["category"].value for r in results}
        assert categories == {"high", "low"}

    @pytest.mark.skip(reason="size() function in WHERE not parsing correctly")
    def test_list_comprehension_pattern(self):
        """Use list comprehensions for filtering."""
        gf = GraphForge()

        # Create simple test graph
        gf.execute("""
            CREATE (a:Person {scores: [90, 85, 95, 88]}),
                   (b:Person {scores: [70, 65, 72]}),
                   (c:Person {scores: [95, 98, 100, 92, 96]})
        """)

        # Use list comprehension to filter high scores
        results = gf.execute("""
            MATCH (p:Person)
            WITH p, [score IN p.scores WHERE score > 90] AS high_scores
            WITH p, high_scores, size(high_scores) AS count_high
            WHERE count_high > 2
            RETURN count_high AS count_high_scores
        """)

        assert len(results) > 0
        for row in results:
            assert row["count_high_scores"].value > 2

    def test_exists_subquery_pattern(self):
        """Use EXISTS to check for pattern existence."""
        gf = GraphForge()
        load_dataset(gf, "snap-ca-grqc")

        # Find nodes that have outgoing connections
        results = gf.execute("""
            MATCH (n)
            WHERE EXISTS { MATCH (n)-[]->(m) }
            RETURN count(*) AS nodes_with_outgoing
        """)

        assert len(results) == 1
        count = results[0]["nodes_with_outgoing"].value
        assert count > 0

    def test_quantifier_pattern(self):
        """Use list quantifiers (all/any/none/single)."""
        gf = GraphForge()

        # Create people with lists of scores
        gf.execute("""
            CREATE (a:Person {name: 'Alice', test_scores: [90, 95, 88]}),
                   (b:Person {name: 'Bob', test_scores: [70, 65, 72]}),
                   (c:Person {name: 'Carol', test_scores: [85, 88, 90]})
        """)

        # Find people where all test scores are above 85
        results = gf.execute("""
            MATCH (p:Person)
            WHERE all(score IN p.test_scores WHERE score >= 85)
            RETURN p.name AS name
        """)

        assert len(results) > 0
        names = [r["name"].value for r in results]
        assert "Alice" in names or "Carol" in names


class TestDataExportWorkflow:
    """Test data export workflows."""

    def test_export_to_json(self, tmp_path):
        """Export graph data to JSON format."""
        from pathlib import Path

        from graphforge.datasets.exporters import JSONGraphExporter
        from graphforge.datasets.loaders import JSONGraphLoader

        gf = GraphForge()
        # Create simple graph
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 30}),
                   (b:Person {name: 'Bob', age: 25}),
                   (a)-[:KNOWS {since: 2020}]->(b)
        """)

        # Export to JSON
        output_file = Path(tmp_path) / "graph.json"
        exporter = JSONGraphExporter()
        exporter.export(gf, output_file)

        # Verify file created
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Load into new instance using loader directly
        gf2 = GraphForge()
        loader = JSONGraphLoader()
        loader.load(gf2, output_file)

        # Verify data
        node_count = gf2.execute("MATCH (n) RETURN count(n) AS count")[0]["count"].value
        assert node_count == 2

        edge_count = gf2.execute("MATCH ()-[r]->() RETURN count(r) AS count")[0]["count"].value
        assert edge_count == 1


class TestRealWorldUseCases:
    """Test real-world use case scenarios."""

    def test_find_common_neighbors(self):
        """Find common neighbors between two nodes."""
        gf = GraphForge()

        # Create friendship network
        gf.execute("""
            CREATE (alice:Person {name: 'Alice'}),
                   (bob:Person {name: 'Bob'}),
                   (carol:Person {name: 'Carol'}),
                   (dave:Person {name: 'Dave'}),
                   (alice)-[:KNOWS]->(carol),
                   (alice)-[:KNOWS]->(dave),
                   (bob)-[:KNOWS]->(carol),
                   (bob)-[:KNOWS]->(dave)
        """)

        # Find common friends of Alice and Bob
        results = gf.execute("""
            MATCH (alice:Person {name: 'Alice'})-[:KNOWS]->(common)<-[:KNOWS]-(bob:Person {name: 'Bob'})
            RETURN common.name AS common_friend
            ORDER BY common_friend
        """)

        assert len(results) == 2
        names = [r["common_friend"].value for r in results]
        assert names == ["Carol", "Dave"]

    def test_variable_length_paths(self):
        """Find variable-length paths between nodes."""
        gf = GraphForge()

        # Create chain: A -> B -> C -> D
        gf.execute("""
            CREATE (a:Node {id: 'A'}),
                   (b:Node {id: 'B'}),
                   (c:Node {id: 'C'}),
                   (d:Node {id: 'D'}),
                   (a)-[:CONNECTED]->(b),
                   (b)-[:CONNECTED]->(c),
                   (c)-[:CONNECTED]->(d)
        """)

        # Find all nodes reachable from A in 1-3 hops
        results = gf.execute("""
            MATCH (a:Node {id: 'A'})-[:CONNECTED*1..3]->(d)
            RETURN d.id AS destination
            ORDER BY destination
        """)

        # Should find B (1 hop), C (2 hops), and D (3 hops)
        assert len(results) == 3
        destinations = [r["destination"].value for r in results]
        assert destinations == ["B", "C", "D"]

    def test_aggregation_with_grouping(self):
        """Aggregate data with grouping."""
        gf = GraphForge()

        # Create tagged items
        gf.execute("""
            CREATE (i1:Item {name: 'Item1', category: 'A', price: 10}),
                   (i2:Item {name: 'Item2', category: 'A', price: 20}),
                   (i3:Item {name: 'Item3', category: 'B', price: 15}),
                   (i4:Item {name: 'Item4', category: 'B', price: 25})
        """)

        # Get average price per category
        results = gf.execute("""
            MATCH (i:Item)
            RETURN i.category AS category, avg(i.price) AS avg_price
            ORDER BY category
        """)

        assert len(results) == 2
        results_dict = {r["category"].value: r["avg_price"].value for r in results}
        assert results_dict["A"] == 15.0
        assert results_dict["B"] == 20.0

    def test_filtering_with_multiple_conditions(self):
        """Complex filtering with multiple WHERE conditions."""
        gf = GraphForge()

        # Create people with various properties
        gf.execute("""
            CREATE (p1:Person {name: 'Alice', age: 30, city: 'NYC'}),
                   (p2:Person {name: 'Bob', age: 25, city: 'LA'}),
                   (p3:Person {name: 'Carol', age: 35, city: 'NYC'}),
                   (p4:Person {name: 'Dave', age: 28, city: 'SF'})
        """)

        # Find people in NYC over 25
        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.city = 'NYC' AND p.age > 25
            RETURN p.name AS name, p.age AS age
            ORDER BY age
        """)

        assert len(results) == 2
        names = [r["name"].value for r in results]
        assert "Alice" in names
        assert "Carol" in names
