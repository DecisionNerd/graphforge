"""Unit tests for REMOVE clause planner."""

from graphforge.ast.clause import MatchClause, RemoveClause, RemoveItem
from graphforge.ast.expression import Literal
from graphforge.ast.pattern import NodePattern
from graphforge.ast.query import CypherQuery
from graphforge.planner.operators import Remove, ScanNodes
from graphforge.planner.planner import QueryPlanner


class TestRemovePlanner:
    """Tests for planning REMOVE clauses."""

    def test_plan_simple_remove_property(self):
        """Plan simple REMOVE property query."""
        # MATCH (n) REMOVE n.age
        node_pattern = NodePattern(variable="n", labels=None, properties=None)
        match_clause = MatchClause(patterns=[[node_pattern]])

        remove_item = RemoveItem(item_type="property", variable="n", name="age")
        remove_clause = RemoveClause(items=[remove_item])

        query = CypherQuery(clauses=[match_clause, remove_clause])

        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have ScanNodes and Remove operators
        assert len(operators) == 2
        assert isinstance(operators[0], ScanNodes)
        assert isinstance(operators[1], Remove)

        # Check Remove operator
        assert len(operators[1].items) == 1
        assert operators[1].items[0].item_type == "property"
        assert operators[1].items[0].variable == "n"
        assert operators[1].items[0].name == "age"

    def test_plan_remove_multiple_properties(self):
        """Plan REMOVE with multiple properties."""
        # MATCH (n) REMOVE n.age, n.city
        node_pattern = NodePattern(variable="n", labels=None, properties=None)
        match_clause = MatchClause(patterns=[[node_pattern]])

        remove_items = [
            RemoveItem(item_type="property", variable="n", name="age"),
            RemoveItem(item_type="property", variable="n", name="city"),
        ]
        remove_clause = RemoveClause(items=remove_items)

        query = CypherQuery(clauses=[match_clause, remove_clause])

        planner = QueryPlanner()
        operators = planner.plan(query)

        # Check Remove operator has both items
        remove_op = operators[1]
        assert len(remove_op.items) == 2
        assert remove_op.items[0].name == "age"
        assert remove_op.items[1].name == "city"

    def test_plan_remove_label(self):
        """Plan REMOVE label query."""
        # MATCH (n) REMOVE n:Person
        node_pattern = NodePattern(variable="n", labels=None, properties=None)
        match_clause = MatchClause(patterns=[[node_pattern]])

        remove_item = RemoveItem(item_type="label", variable="n", name="Person")
        remove_clause = RemoveClause(items=[remove_item])

        query = CypherQuery(clauses=[match_clause, remove_clause])

        planner = QueryPlanner()
        operators = planner.plan(query)

        # Check Remove operator
        remove_op = operators[1]
        assert len(remove_op.items) == 1
        assert remove_op.items[0].item_type == "label"
        assert remove_op.items[0].name == "Person"

    def test_plan_remove_mixed(self):
        """Plan REMOVE with mixed properties and labels."""
        # MATCH (n) REMOVE n.age, n:Temp
        node_pattern = NodePattern(variable="n", labels=None, properties=None)
        match_clause = MatchClause(patterns=[[node_pattern]])

        remove_items = [
            RemoveItem(item_type="property", variable="n", name="age"),
            RemoveItem(item_type="label", variable="n", name="Temp"),
        ]
        remove_clause = RemoveClause(items=remove_items)

        query = CypherQuery(clauses=[match_clause, remove_clause])

        planner = QueryPlanner()
        operators = planner.plan(query)

        # Check Remove operator has both types
        remove_op = operators[1]
        assert len(remove_op.items) == 2
        assert remove_op.items[0].item_type == "property"
        assert remove_op.items[1].item_type == "label"

    def test_remove_in_update_query(self):
        """Test REMOVE appears in correct position in update query."""
        from graphforge.ast.clause import SetClause

        # MATCH (n) SET n.x = 1 REMOVE n.y
        node_pattern = NodePattern(variable="n", labels=None, properties=None)
        match_clause = MatchClause(patterns=[[node_pattern]])

        # Create a simple SET clause (we'll mock the property access)
        from graphforge.ast.expression import PropertyAccess

        prop_access = PropertyAccess(variable="n", property="x")
        set_clause = SetClause(items=[(prop_access, Literal(value=1))])

        remove_item = RemoveItem(item_type="property", variable="n", name="y")
        remove_clause = RemoveClause(items=[remove_item])

        query = CypherQuery(clauses=[match_clause, set_clause, remove_clause])

        planner = QueryPlanner()
        operators = planner.plan(query)

        # Should have: ScanNodes, Set, Remove (in that order)
        from graphforge.planner.operators import Set

        assert isinstance(operators[0], ScanNodes)
        assert isinstance(operators[1], Set)
        assert isinstance(operators[2], Remove)
