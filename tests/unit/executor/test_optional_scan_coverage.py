"""Unit tests for OptionalScanNodes operator to improve executor coverage.

These tests target the _execute_optional_scan method (lines 293-347) which is
largely uncovered. The method handles OPTIONAL MATCH with node scans and
supports both bound and unbound variables with label validation.
"""

import pytest

from graphforge import GraphForge
from graphforge.executor.evaluator import ExecutionContext
from graphforge.executor.executor import QueryExecutor
from graphforge.planner.operators import OptionalScanNodes
from graphforge.types.values import CypherNull, CypherString


@pytest.mark.unit
class TestOptionalScanBoundVariables:
    """Test OptionalScanNodes with already-bound variables."""

    @pytest.mark.parametrize(
        "node_labels,required_labels,should_match",
        [
            (["Person", "Employee"], ["Person"], True),
            (["Person", "Employee", "Manager"], ["Person", "Employee"], True),
            (["Person"], ["Person", "Employee"], False),
            (["Person"], [], True),
        ],
        ids=[
            "single_label_match",
            "multiple_labels_match",
            "missing_required_label",
            "no_label_requirements",
        ],
    )
    def test_bound_variable_label_matching(self, node_labels, required_labels, should_match):
        """Test OptionalScanNodes validates bound variables against label requirements."""
        gf = GraphForge()
        node = gf.create_node(node_labels, name="Alice")

        executor = QueryExecutor(gf.graph, gf)

        ctx = ExecutionContext()
        ctx.bind("n", node)

        op = OptionalScanNodes(variable="n", labels=[required_labels] if required_labels else [])
        result = executor._execute_optional_scan(op, [ctx])

        assert len(result) == 1
        if should_match:
            # Should preserve node binding
            assert result[0].get("n") == node
        else:
            # OPTIONAL semantics: Should preserve row with NULL binding
            assert isinstance(result[0].get("n"), CypherNull)


@pytest.mark.unit
class TestOptionalScanUnboundVariables:
    """Test OptionalScanNodes with unbound variables (standard scan behavior)."""

    @pytest.mark.parametrize(
        "setup_func,labels,var_name,expected_count,check_func",
        [
            # Single label filter - finds matching nodes
            (
                lambda gf: (
                    gf.create_node(["Person"], name="Alice"),
                    gf.create_node(["Person"], name="Bob"),
                    gf.create_node(["Company"], name="Acme"),
                ),
                [["Person"]],
                "p",
                2,
                lambda res, nodes: {r.get("p").id for r in res} == {nodes[0].id, nodes[1].id},
            ),
            # Multiple labels - requires all
            (
                lambda gf: (
                    gf.create_node(["Person", "Employee"], name="Alice"),
                    gf.create_node(["Person"], name="Bob"),
                    gf.create_node(["Employee"], name="Charlie"),
                ),
                [["Person", "Employee"]],
                "p",
                1,
                lambda res, nodes: res[0].get("p").id == nodes[0].id,
            ),
            # No matches - returns NULL
            (
                lambda gf: (gf.create_node(["Company"], name="Acme"),),
                [["Person"]],
                "p",
                1,
                lambda res, _nodes: isinstance(res[0].get("p"), CypherNull),
            ),
            # No label filter - scans all
            (
                lambda gf: (
                    gf.create_node(["Person"], name="Alice"),
                    gf.create_node(["Company"], name="Acme"),
                    gf.create_node(["Product"], name="Widget"),
                ),
                [],
                "n",
                3,
                lambda res, nodes: {r.get("n").id for r in res} == {n.id for n in nodes},
            ),
            # Empty graph - returns NULL
            (
                lambda _gf: (),
                [["Person"]],
                "n",
                1,
                lambda res, _nodes: isinstance(res[0].get("n"), CypherNull),
            ),
        ],
        ids=[
            "single_label_filter",
            "multiple_labels_required",
            "no_matches_returns_null",
            "no_label_filter_scans_all",
            "empty_graph_returns_null",
        ],
    )
    def test_unbound_variable_scan_behavior(
        self, setup_func, labels, var_name, expected_count, check_func
    ):
        """Test OptionalScanNodes scanning behavior with unbound variables."""
        gf = GraphForge()
        nodes = setup_func(gf)

        executor = QueryExecutor(gf.graph, gf)
        ctx = ExecutionContext()

        op = OptionalScanNodes(variable=var_name, labels=labels)
        result = executor._execute_optional_scan(op, [ctx])

        assert len(result) == expected_count
        assert check_func(result, nodes)


@pytest.mark.unit
class TestOptionalScanMultipleInputRows:
    """Test OptionalScanNodes with multiple input contexts."""

    def test_multiple_input_rows_all_match(self):
        """Test OptionalScanNodes with multiple input rows that all match."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")

        executor = QueryExecutor(gf.graph, gf)

        # Create two input contexts with bound variables
        ctx1 = ExecutionContext()
        ctx1.bind("p", alice)

        ctx2 = ExecutionContext()
        ctx2.bind("p", bob)

        # OptionalScanNodes validates Person label
        op = OptionalScanNodes(variable="p", labels=[["Person"]])
        result = executor._execute_optional_scan(op, [ctx1, ctx2])

        # Should preserve both contexts (both match)
        assert len(result) == 2
        assert result[0].get("p") == alice
        assert result[1].get("p") == bob

    def test_multiple_input_rows_some_match(self):
        """Test OptionalScanNodes with mixed matches and non-matches."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        acme = gf.create_node(["Company"], name="Acme")

        executor = QueryExecutor(gf.graph, gf)

        # Create two input contexts
        ctx1 = ExecutionContext()
        ctx1.bind("n", alice)  # Matches Person

        ctx2 = ExecutionContext()
        ctx2.bind("n", acme)  # Doesn't match Person

        # OptionalScanNodes requires Person label
        op = OptionalScanNodes(variable="n", labels=[["Person"]])
        result = executor._execute_optional_scan(op, [ctx1, ctx2])

        # Should preserve both contexts, second with NULL
        assert len(result) == 2
        assert result[0].get("n") == alice
        assert isinstance(result[1].get("n"), CypherNull)

    def test_multiple_input_rows_with_unbound_variable(self):
        """Test OptionalScanNodes with multiple input rows and unbound variable."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")

        executor = QueryExecutor(gf.graph, gf)

        # Create two input contexts with different existing bindings
        ctx1 = ExecutionContext()
        ctx1.bind("x", CypherString("value1"))

        ctx2 = ExecutionContext()
        ctx2.bind("x", CypherString("value2"))

        # OptionalScanNodes for unbound variable "p"
        op = OptionalScanNodes(variable="p", labels=[["Person"]])
        result = executor._execute_optional_scan(op, [ctx1, ctx2])

        # Should produce cartesian product: 2 input rows * 2 Person nodes = 4 results
        assert len(result) == 4

        # Check that all combinations exist
        results_by_x = {}
        for r in result:
            x_val = r.get("x").value
            if x_val not in results_by_x:
                results_by_x[x_val] = []
            results_by_x[x_val].append(r.get("p").id)

        assert len(results_by_x["value1"]) == 2
        assert set(results_by_x["value1"]) == {alice.id, bob.id}
        assert len(results_by_x["value2"]) == 2
        assert set(results_by_x["value2"]) == {alice.id, bob.id}


@pytest.mark.unit
class TestOptionalScanEdgeCases:
    """Test edge cases for OptionalScanNodes."""

    def test_preserves_existing_bindings(self):
        """Test OptionalScanNodes preserves existing variable bindings."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")

        executor = QueryExecutor(gf.graph, gf)

        # Context with existing bindings
        ctx = ExecutionContext()
        ctx.bind("other", CypherString("preserved"))

        # OptionalScanNodes for new variable
        op = OptionalScanNodes(variable="p", labels=[["Person"]])
        result = executor._execute_optional_scan(op, [ctx])

        # Should preserve existing bindings
        assert len(result) == 2
        assert all(r.get("other").value == "preserved" for r in result)
        node_ids = {r.get("p").id for r in result}
        assert node_ids == {alice.id, bob.id}

    def test_first_label_optimization(self):
        """Test OptionalScanNodes uses first label for efficient lookup."""
        gf = GraphForge()
        # Create nodes with multiple labels
        alice = gf.create_node(["Person", "Employee"], name="Alice")
        gf.create_node(["Person"], name="Bob")
        gf.create_node(["Employee"], name="Charlie")

        executor = QueryExecutor(gf.graph, gf)

        ctx = ExecutionContext()

        # OptionalScanNodes with multiple labels (should use Person for scan)
        op = OptionalScanNodes(variable="p", labels=[["Person", "Employee"]])
        result = executor._execute_optional_scan(op, [ctx])

        # Should only find Alice (has both labels)
        assert len(result) == 1
        assert result[0].get("p").id == alice.id

    def test_empty_labels_list(self):
        """Test OptionalScanNodes with empty labels list (no filter)."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        acme = gf.create_node(["Company"], name="Acme")

        executor = QueryExecutor(gf.graph, gf)

        ctx = ExecutionContext()

        # OptionalScanNodes with empty labels (should match all nodes)
        op = OptionalScanNodes(variable="n", labels=[])
        result = executor._execute_optional_scan(op, [ctx])

        # Should find all nodes
        assert len(result) == 2
        node_ids = {r.get("n").id for r in result}
        assert node_ids == {alice.id, acme.id}
