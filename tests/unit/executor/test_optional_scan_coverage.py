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

    def test_bound_variable_matches_labels(self):
        """Test OptionalScanNodes when bound variable has matching labels."""
        gf = GraphForge()
        node = gf.create_node(["Person", "Employee"], name="Alice")

        executor = QueryExecutor(gf.graph, gf)

        # Create input context with variable already bound
        ctx = ExecutionContext()
        ctx.bind("n", node)

        # OptionalScanNodes should validate the bound node matches pattern
        op = OptionalScanNodes(variable="n", labels=["Person"])
        result = executor._execute_optional_scan(op, [ctx])

        # Should preserve context since node matches
        assert len(result) == 1
        assert result[0].get("n") == node

    def test_bound_variable_matches_multiple_labels(self):
        """Test OptionalScanNodes when bound variable has all required labels."""
        gf = GraphForge()
        node = gf.create_node(["Person", "Employee", "Manager"], name="Alice")

        executor = QueryExecutor(gf.graph, gf)

        ctx = ExecutionContext()
        ctx.bind("n", node)

        # OptionalScanNodes with multiple label requirements
        op = OptionalScanNodes(variable="n", labels=["Person", "Employee"])
        result = executor._execute_optional_scan(op, [ctx])

        # Should preserve context since node has both labels
        assert len(result) == 1
        assert result[0].get("n") == node

    def test_bound_variable_missing_required_label(self):
        """Test OptionalScanNodes when bound variable missing a required label."""
        gf = GraphForge()
        # Node has only Person label, not Employee
        node = gf.create_node(["Person"], name="Alice")

        executor = QueryExecutor(gf.graph, gf)

        ctx = ExecutionContext()
        ctx.bind("n", node)

        # OptionalScanNodes requires both Person and Employee
        op = OptionalScanNodes(variable="n", labels=["Person", "Employee"])
        result = executor._execute_optional_scan(op, [ctx])

        # Should preserve row with NULL binding (OPTIONAL semantics)
        assert len(result) == 1
        assert isinstance(result[0].get("n"), CypherNull)

    def test_bound_variable_no_label_requirements(self):
        """Test OptionalScanNodes when bound variable and no label filter."""
        gf = GraphForge()
        node = gf.create_node(["Person"], name="Alice")

        executor = QueryExecutor(gf.graph, gf)

        ctx = ExecutionContext()
        ctx.bind("n", node)

        # OptionalScanNodes with no label requirements
        op = OptionalScanNodes(variable="n", labels=[])
        result = executor._execute_optional_scan(op, [ctx])

        # Should preserve context (any node matches)
        assert len(result) == 1
        assert result[0].get("n") == node


@pytest.mark.unit
class TestOptionalScanUnboundVariables:
    """Test OptionalScanNodes with unbound variables (standard scan behavior)."""

    def test_unbound_variable_with_label_filter(self):
        """Test OptionalScanNodes scans nodes by label when variable unbound."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        gf.create_node(["Company"], name="Acme Corp")

        executor = QueryExecutor(gf.graph, gf)

        # Start with empty context
        ctx = ExecutionContext()

        # OptionalScanNodes should scan for Person nodes
        op = OptionalScanNodes(variable="p", labels=["Person"])
        result = executor._execute_optional_scan(op, [ctx])

        # Should find both Person nodes
        assert len(result) == 2
        nodes = {r.get("p").id for r in result}
        assert nodes == {alice.id, bob.id}

    def test_unbound_variable_with_multiple_labels(self):
        """Test OptionalScanNodes filters by multiple labels when variable unbound."""
        gf = GraphForge()
        # Node with both Person and Employee labels
        alice = gf.create_node(["Person", "Employee"], name="Alice")
        # Node with only Person label
        _bob = gf.create_node(["Person"], name="Bob")
        # Node with only Employee label
        _charlie = gf.create_node(["Employee"], name="Charlie")

        executor = QueryExecutor(gf.graph, gf)

        ctx = ExecutionContext()

        # OptionalScanNodes requires both Person AND Employee
        op = OptionalScanNodes(variable="p", labels=["Person", "Employee"])
        result = executor._execute_optional_scan(op, [ctx])

        # Should only find Alice (has both labels)
        assert len(result) == 1
        assert result[0].get("p").id == alice.id

    def test_unbound_variable_no_matches_returns_null(self):
        """Test OptionalScanNodes returns NULL binding when no nodes match."""
        gf = GraphForge()
        # Create only Company nodes, no Person nodes
        gf.create_node(["Company"], name="Acme Corp")

        executor = QueryExecutor(gf.graph, gf)

        ctx = ExecutionContext()

        # OptionalScanNodes looking for Person nodes
        op = OptionalScanNodes(variable="p", labels=["Person"])
        result = executor._execute_optional_scan(op, [ctx])

        # OPTIONAL semantics: Should preserve row with NULL binding
        assert len(result) == 1
        assert isinstance(result[0].get("p"), CypherNull)

    def test_unbound_variable_no_label_filter(self):
        """Test OptionalScanNodes scans all nodes when no label filter."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        acme = gf.create_node(["Company"], name="Acme Corp")
        product = gf.create_node(["Product"], name="Widget")

        executor = QueryExecutor(gf.graph, gf)

        ctx = ExecutionContext()

        # OptionalScanNodes with no label requirements
        op = OptionalScanNodes(variable="n", labels=[])
        result = executor._execute_optional_scan(op, [ctx])

        # Should find all nodes
        assert len(result) == 3
        node_ids = {r.get("n").id for r in result}
        assert node_ids == {alice.id, acme.id, product.id}

    def test_unbound_variable_empty_graph_returns_null(self):
        """Test OptionalScanNodes returns NULL binding when graph is empty."""
        gf = GraphForge()

        executor = QueryExecutor(gf.graph, gf)

        ctx = ExecutionContext()

        # OptionalScanNodes on empty graph
        op = OptionalScanNodes(variable="n", labels=["Person"])
        result = executor._execute_optional_scan(op, [ctx])

        # OPTIONAL semantics: Should preserve row with NULL binding
        assert len(result) == 1
        assert isinstance(result[0].get("n"), CypherNull)


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
        op = OptionalScanNodes(variable="p", labels=["Person"])
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
        op = OptionalScanNodes(variable="n", labels=["Person"])
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
        op = OptionalScanNodes(variable="p", labels=["Person"])
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
        op = OptionalScanNodes(variable="p", labels=["Person"])
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
        op = OptionalScanNodes(variable="p", labels=["Person", "Employee"])
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
