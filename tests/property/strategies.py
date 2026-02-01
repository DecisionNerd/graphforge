"""Hypothesis strategies for generating test data.

These strategies generate valid GraphForge data structures for property-based testing.
"""

from hypothesis import strategies as st

# openCypher value types
cypher_int = st.integers(min_value=-(2**63), max_value=2**63 - 1)
cypher_float = st.floats(allow_nan=False, allow_infinity=False)
cypher_bool = st.booleans()
cypher_string = st.text()
cypher_null = st.none()


def cypher_list(max_size=5):
    """Strategy for generating openCypher lists."""
    return st.lists(cypher_scalar(), max_size=max_size)


def cypher_map(max_size=5):
    """Strategy for generating openCypher maps."""
    return st.dictionaries(
        keys=st.text(min_size=1),
        values=cypher_scalar(),
        max_size=max_size,
    )


def cypher_scalar():
    """Strategy for generating any openCypher scalar value."""
    return st.one_of(
        cypher_null,
        cypher_bool,
        cypher_int,
        cypher_float,
        cypher_string,
    )


def cypher_value():
    """Strategy for generating any openCypher value (including collections)."""
    return st.recursive(
        cypher_scalar(),
        lambda children: st.one_of(
            st.lists(children, max_size=5),
            st.dictionaries(st.text(min_size=1), children, max_size=5),
        ),
        max_leaves=10,
    )


def property_map():
    """Strategy for generating node/relationship property maps."""
    return st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=cypher_value(),
        max_size=10,
    )
