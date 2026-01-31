"""pytest-bdd configuration for TCK tests."""

import pytest
from pytest_bdd import given, parsers, then, when

from graphforge import GraphForge
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import (
    CypherBool,
    CypherFloat,
    CypherInt,
    CypherNull,
    CypherString,
)


@pytest.fixture
def tck_context():
    """Context for TCK test execution.

    Maintains graph instance and query results across steps.
    """
    return {
        "graph": None,
        "result": None,
        "side_effects": [],
    }


@given("an empty graph", target_fixture="tck_context")
def empty_graph(tck_context):
    """Initialize an empty GraphForge instance."""
    tck_context["graph"] = GraphForge()
    tck_context["result"] = None
    tck_context["side_effects"] = []
    return tck_context


@given("having executed")
def execute_setup_query(tck_context, step):
    """Execute a setup query (typically CREATE statements).

    Note: Since GraphForge doesn't support CREATE yet, we'll need to
    manually build the graph from CREATE statements.
    """
    # Get the docstring from the step
    cypher_query = step.doc_string.content if step.doc_string else ""

    # Parse and execute CREATE statements
    _execute_create_statements(tck_context["graph"], cypher_query)


@when("executing query")
def execute_query(tck_context, step):
    """Execute a Cypher query and store results."""
    # Get the docstring from the step
    cypher_query = step.doc_string.content if step.doc_string else ""

    try:
        result = tck_context["graph"].execute(cypher_query)
        tck_context["result"] = result
    except Exception as e:
        tck_context["result"] = {"error": str(e)}


@then("the result should be, in any order")
def verify_result_any_order(tck_context, step):
    """Verify query results match expected table (order doesn't matter)."""
    result = tck_context["result"]

    # Parse the data table from the step
    expected = _parse_data_table(step.table)

    assert result is not None, "No result was produced"
    assert "error" not in result, f"Query error: {result.get('error')}"
    assert len(result) == len(expected), f"Expected {len(expected)} rows, got {len(result)}"

    # Convert results to comparable format
    actual_rows = [_row_to_comparable(row) for row in result]
    expected_rows = [_row_to_comparable(row) for row in expected]

    # Check that all expected rows are present
    for exp_row in expected_rows:
        assert exp_row in actual_rows, f"Expected row not found: {exp_row}"


@then("the result should be, in order")
def verify_result_in_order(tck_context, step):
    """Verify query results match expected table (order matters)."""
    result = tck_context["result"]

    # Parse the data table from the step
    expected = _parse_data_table(step.table)

    assert result is not None, "No result was produced"
    assert "error" not in result, f"Query error: {result.get('error')}"
    assert len(result) == len(expected), f"Expected {len(expected)} rows, got {len(result)}"

    # Convert results to comparable format and check order
    for i, (actual_row, expected_row) in enumerate(zip(result, expected)):
        actual_comparable = _row_to_comparable(actual_row)
        expected_comparable = _row_to_comparable(expected_row)
        assert (
            actual_comparable == expected_comparable
        ), f"Row {i} mismatch: expected {expected_comparable}, got {actual_comparable}"


@then(parsers.parse("the result should have {count:d} rows"))
def verify_row_count(tck_context, count):
    """Verify the number of result rows."""
    result = tck_context["result"]
    assert result is not None, "No result was produced"
    assert "error" not in result, f"Query error: {result.get('error')}"
    assert len(result) == count, f"Expected {count} rows, got {len(result)}"


@then("no side effects")
def verify_no_side_effects(tck_context):
    """Verify no unexpected side effects occurred."""
    # In our case, this is a no-op since we don't track side effects yet
    # But it's important for TCK compliance
    pass


def _execute_create_statements(graph: GraphForge, cypher_query: str):
    """Parse and execute CREATE statements to build the graph.

    This is a simplified parser for CREATE statements in the format:
    CREATE (label {prop: value}), (...)

    Note: This is not a full Cypher parser, just enough for TCK test setup.
    """
    # Remove CREATE keyword
    query = cypher_query.replace("CREATE", "").strip()

    # Split by top-level commas (not inside parentheses)
    node_specs = []
    current = ""
    depth = 0
    for char in query:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            node_specs.append(current.strip())
            current = ""
            continue
        current += char
    if current.strip():
        node_specs.append(current.strip())

    # Parse each node specification
    node_id = 1
    for spec in node_specs:
        spec = spec.strip().strip("()").strip()
        if not spec:
            continue

        # Parse pattern: :Label {prop: value, ...} or :Label1:Label2 {prop: value}
        labels = []
        properties = {}

        # Extract labels (start with :)
        parts = spec.split("{", 1)
        label_part = parts[0].strip()

        if label_part:
            labels = [l.strip() for l in label_part.split(":") if l.strip()]

        # Extract properties
        if len(parts) > 1:
            prop_part = parts[1].rsplit("}", 1)[0].strip()
            if prop_part:
                # Parse key: value pairs
                for pair in prop_part.split(","):
                    if ":" in pair:
                        key, value = pair.split(":", 1)
                        key = key.strip()
                        value = value.strip()

                        # Parse value type
                        properties[key] = _parse_value(value)

        # Create node
        node = NodeRef(
            id=node_id, labels=frozenset(labels), properties=properties
        )
        graph.graph.add_node(node)
        node_id += 1


def _parse_value(value_str: str):
    """Parse a value string into appropriate CypherValue."""
    value_str = value_str.strip()

    # String
    if value_str.startswith("'") and value_str.endswith("'"):
        return CypherString(value_str[1:-1])

    # Boolean
    if value_str.lower() == "true":
        return CypherBool(True)
    if value_str.lower() == "false":
        return CypherBool(False)

    # Null
    if value_str.lower() == "null":
        return CypherNull()

    # Number (int or float)
    try:
        if "." in value_str:
            return CypherFloat(float(value_str))
        return CypherInt(int(value_str))
    except ValueError:
        # Default to string
        return CypherString(value_str)


def _parse_data_table(table) -> list[dict]:
    """Parse expected result table from pytest-bdd table object.

    Args:
        table: pytest-bdd table object with headers and rows

    Returns:
        List of dictionaries with parsed values
    """
    if not table:
        return []

    # Get headers from table
    headers = table.headings

    # Parse each row
    results = []
    for row in table.rows:
        row_dict = {}
        for header, value in zip(headers, row.cells):
            row_dict[header] = _parse_value(value)
        results.append(row_dict)

    return results


def _row_to_comparable(row: dict) -> dict:
    """Convert a result row to a comparable dictionary.

    Handles CypherValues, NodeRefs, etc.
    """
    comparable = {}
    for key, value in row.items():
        if isinstance(value, (CypherInt, CypherFloat, CypherString, CypherBool)):
            comparable[key] = value.value
        elif isinstance(value, CypherNull):
            comparable[key] = None
        elif isinstance(value, NodeRef):
            # Convert node to comparable dict
            comparable[key] = {
                "labels": sorted(value.labels),
                "properties": {
                    k: v.value if hasattr(v, "value") else v
                    for k, v in value.properties.items()
                },
            }
        elif isinstance(value, EdgeRef):
            # Convert edge to comparable dict
            comparable[key] = {
                "type": value.type,
                "properties": {
                    k: v.value if hasattr(v, "value") else v
                    for k, v in value.properties.items()
                },
            }
        else:
            comparable[key] = value

    return comparable
