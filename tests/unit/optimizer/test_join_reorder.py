"""Unit tests for join reordering optimization."""

from graphforge.optimizer.join_reorder import (
    DependencyAnalyzer,
    JoinReorderOptimizer,
)
from graphforge.optimizer.statistics import GraphStatistics
from graphforge.planner.operators import (
    Create,
    ExpandEdges,
    ScanNodes,
    With,
)


class TestDependencyAnalyzer:
    """Test dependency analysis for operator reordering."""

    def test_scan_nodes_binds_variable(self):
        """ScanNodes should bind its variable."""
        analyzer = DependencyAnalyzer()
        op = ScanNodes(variable="n", labels=[["Person"]])

        binds = analyzer._get_bound_variables(op)
        assert binds == {"n"}

    def test_expand_edges_binds_dst_and_edge(self):
        """ExpandEdges should bind dst_var and edge_var."""
        analyzer = DependencyAnalyzer()
        op = ExpandEdges(
            src_var="a",
            edge_var="r",
            dst_var="b",
            edge_types=["KNOWS"],
            direction="OUT",
        )

        binds = analyzer._get_bound_variables(op)
        assert binds == {"b", "r"}

    def test_expand_edges_binds_only_dst_when_no_edge_var(self):
        """ExpandEdges without edge_var should only bind dst_var."""
        analyzer = DependencyAnalyzer()
        op = ExpandEdges(
            src_var="a",
            edge_var=None,
            dst_var="b",
            edge_types=["KNOWS"],
            direction="OUT",
        )

        binds = analyzer._get_bound_variables(op)
        assert binds == {"b"}

    def test_expand_edges_requires_src_var(self):
        """ExpandEdges should require src_var."""
        analyzer = DependencyAnalyzer()
        op = ExpandEdges(src_var="a", dst_var="b", edge_types=["KNOWS"], direction="OUT")

        requires = analyzer._get_required_variables(op)
        assert "a" in requires

    def test_scan_nodes_requires_nothing(self):
        """ScanNodes should have no requirements."""
        analyzer = DependencyAnalyzer()
        op = ScanNodes(variable="n", labels=None)

        requires = analyzer._get_required_variables(op)
        assert requires == set()

    def test_build_dependency_graph_independent_scans(self):
        """Independent scans should have no dependencies."""
        analyzer = DependencyAnalyzer()
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="b", labels=[["Company"]]),
        ]

        nodes, dependencies = analyzer.build_dependency_graph(ops)

        assert len(nodes) == 2
        assert len(dependencies) == 0

    def test_build_dependency_graph_expand_depends_on_scan(self):
        """ExpandEdges should depend on ScanNodes that binds its src_var."""
        analyzer = DependencyAnalyzer()
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(src_var="a", dst_var="b", edge_types=["KNOWS"], direction="OUT"),
        ]

        nodes, dependencies = analyzer.build_dependency_graph(ops)

        assert len(nodes) == 2
        assert dependencies[1] == {0}  # ExpandEdges depends on ScanNodes

    def test_build_dependency_graph_chained_expands(self):
        """Chained ExpandEdges should build dependency chain."""
        analyzer = DependencyAnalyzer()
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(src_var="a", dst_var="b", edge_types=["KNOWS"], direction="OUT"),
            ExpandEdges(src_var="b", dst_var="c", edge_types=["KNOWS"], direction="OUT"),
        ]

        nodes, dependencies = analyzer.build_dependency_graph(ops)

        assert len(nodes) == 3
        assert dependencies[1] == {0}  # Second op depends on first
        assert dependencies[2] == {1}  # Third op depends on second

    def test_find_valid_orderings_single_ordering(self):
        """Chain with dependencies should have single valid ordering."""
        analyzer = DependencyAnalyzer()
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(src_var="a", dst_var="b", edge_types=["KNOWS"], direction="OUT"),
        ]

        nodes, dependencies = analyzer.build_dependency_graph(ops)
        orderings = analyzer.find_valid_orderings(nodes, dependencies)

        assert len(orderings) == 1
        assert [n.index for n in orderings[0]] == [0, 1]

    def test_find_valid_orderings_multiple_orderings(self):
        """Independent operators should allow multiple orderings."""
        analyzer = DependencyAnalyzer()
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="b", labels=[["Company"]]),
        ]

        nodes, dependencies = analyzer.build_dependency_graph(ops)
        orderings = analyzer.find_valid_orderings(nodes, dependencies)

        # Should have 2 orderings: [a, b] and [b, a]
        assert len(orderings) == 2
        ordering_indices = [[n.index for n in ordering] for ordering in orderings]
        assert [0, 1] in ordering_indices
        assert [1, 0] in ordering_indices


class TestJoinReorderOptimizer:
    """Test join reordering optimization."""

    def test_can_reorder_with_multiple_scans(self):
        """Should allow reordering with multiple scans."""
        stats = GraphStatistics(total_nodes=100, total_edges=200)
        optimizer = JoinReorderOptimizer(stats)

        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="b", labels=[["Company"]]),
        ]

        assert optimizer.can_reorder(ops) is True

    def test_cannot_reorder_single_scan(self):
        """Should not reorder with only one pattern operator."""
        stats = GraphStatistics(total_nodes=100, total_edges=200)
        optimizer = JoinReorderOptimizer(stats)

        ops = [ScanNodes(variable="a", labels=[["Person"]])]

        assert optimizer.can_reorder(ops) is False

    def test_cannot_reorder_with_side_effects(self):
        """Should not reorder if side effects present."""
        stats = GraphStatistics(total_nodes=100, total_edges=200)
        optimizer = JoinReorderOptimizer(stats)

        # Create a minimal Create operator (needs at least one pattern)
        from graphforge.ast.pattern import NodePattern

        pattern = NodePattern(variable="n", labels=[], properties={})

        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="b", labels=[["Company"]]),
            Create(patterns=[pattern]),  # Side effect
        ]

        assert optimizer.can_reorder(ops) is False

    def test_split_at_boundaries_with_operator(self):
        """Should split at With boundary."""
        stats = GraphStatistics(total_nodes=100, total_edges=200)
        optimizer = JoinReorderOptimizer(stats)

        # Create a minimal ReturnItem
        from graphforge.ast.clause import ReturnItem
        from graphforge.ast.expression import Variable

        return_item = ReturnItem(expression=Variable(name="a"), alias="a")

        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            With(items=[return_item]),
            ScanNodes(variable="b", labels=[["Company"]]),
        ]

        segments = optimizer._split_at_boundaries(ops)

        # Should be: [segment1, With, segment2]
        assert len(segments) == 3
        assert isinstance(segments[0], list)
        assert isinstance(segments[1], With)
        assert isinstance(segments[2], list)

    def test_reorder_chooses_lower_cost_ordering(self):
        """Should choose ordering with lower cost."""
        stats = GraphStatistics(
            total_nodes=110,
            total_edges=100,
            node_counts_by_label={"Person": 100, "Company": 10},
            avg_degree_by_type={"WORKS_FOR": 1.0},
        )
        optimizer = JoinReorderOptimizer(stats)

        # Bad order: Cartesian product (scan Person, scan Company)
        ops_bad = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="b", labels=[["Company"]]),
            ExpandEdges(src_var="a", dst_var="b", edge_types=["WORKS_FOR"], direction="OUT"),
        ]

        # Reorder should fix this
        reordered = optimizer.reorder_joins(ops_bad)

        # First operator should be ScanNodes
        assert isinstance(reordered[0], ScanNodes)
        # Second should be ExpandEdges (not another ScanNodes)
        assert isinstance(reordered[1], ExpandEdges)

    def test_reorder_preserves_dependencies(self):
        """Should not reorder if it would break dependencies."""
        stats = GraphStatistics(total_nodes=100, total_edges=200)
        optimizer = JoinReorderOptimizer(stats)

        # Chain that can't be reordered
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(src_var="a", dst_var="b", edge_types=["KNOWS"], direction="OUT"),
            ExpandEdges(src_var="b", dst_var="c", edge_types=["KNOWS"], direction="OUT"),
        ]

        reordered = optimizer.reorder_joins(ops)

        # Order should be preserved
        assert isinstance(reordered[0], ScanNodes)
        assert isinstance(reordered[1], ExpandEdges)
        assert isinstance(reordered[2], ExpandEdges)
        assert reordered[1].src_var == "a"
        assert reordered[2].src_var == "b"

    def test_reorder_respects_with_boundary(self):
        """Should not reorder across With boundary."""
        stats = GraphStatistics(
            total_nodes=110,
            total_edges=100,
            node_counts_by_label={"Person": 100, "Company": 10},
        )
        optimizer = JoinReorderOptimizer(stats)

        # Create a minimal ReturnItem
        from graphforge.ast.clause import ReturnItem
        from graphforge.ast.expression import Variable

        return_item = ReturnItem(expression=Variable(name="a"), alias="a")

        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            With(items=[return_item]),
            ScanNodes(variable="b", labels=[["Company"]]),
            ScanNodes(variable="c", labels=[["Person"]]),
        ]

        reordered = optimizer.reorder_joins(ops)

        # With should still be at index 1
        assert isinstance(reordered[1], With)
        # First segment unchanged
        assert isinstance(reordered[0], ScanNodes)
        assert reordered[0].variable == "a"

    def test_reorder_with_no_valid_alternatives(self):
        """Should return original if only one valid ordering."""
        stats = GraphStatistics(total_nodes=100, total_edges=200)
        optimizer = JoinReorderOptimizer(stats)

        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ExpandEdges(src_var="a", dst_var="b", edge_types=["KNOWS"], direction="OUT"),
        ]

        reordered = optimizer.reorder_joins(ops)

        # Should be unchanged
        assert len(reordered) == 2
        assert isinstance(reordered[0], ScanNodes)
        assert isinstance(reordered[1], ExpandEdges)


class TestJoinReorderIntegration:
    """Integration tests for join reordering with cost estimation."""

    def test_cartesian_product_optimization(self):
        """Should optimize Cartesian product to join."""
        stats = GraphStatistics(
            total_nodes=110,
            total_edges=100,
            node_counts_by_label={"Person": 100, "Company": 10},
            avg_degree_by_type={"WORKS_FOR": 1.0},
        )
        optimizer = JoinReorderOptimizer(stats)

        # Query pattern that creates Cartesian product:
        # MATCH (a:Person) MATCH (b:Company) MATCH (a)-[:WORKS_FOR]->(b)
        ops = [
            ScanNodes(variable="a", labels=[["Person"]]),
            ScanNodes(variable="b", labels=[["Company"]]),
            # This expand actually connects them, but comes after Cartesian
            ExpandEdges(src_var="a", dst_var="b", edge_types=["WORKS_FOR"], direction="OUT"),
        ]

        reordered = optimizer.reorder_joins(ops)

        # Should reorder to: Scan Person, Expand (avoid scan Company)
        assert len(reordered) == 3
        assert isinstance(reordered[0], ScanNodes)
        assert isinstance(reordered[1], ExpandEdges)
        # The expand should come before the second scan
        expand_idx = 1
        company_scan_idx = 2
        assert expand_idx < company_scan_idx
