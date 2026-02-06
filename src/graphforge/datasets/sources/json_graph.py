"""JSON Graph format loader registration.

JSON Graph is a typed property graph interchange format used for lossless
import/export of GraphForge graphs. It preserves full type information for
all CypherValue types including primitives, temporal, spatial, and collections.

This format is primarily used for:
- Exporting GraphForge graphs to JSON
- Importing typed graph data from JSON
- Testing and development workflows
- Programmatic graph construction

Unlike SNAP and LDBC which are public dataset repositories, JSON Graph is
an interchange format, so no public datasets are registered here.
"""

from graphforge.datasets.registry import register_loader


def register_json_graph_loader() -> None:
    """Register the JSON Graph loader in the global registry.

    This registers the loader but does not register any datasets, as JSON Graph
    is an interchange format rather than a public dataset source.
    """
    # Register the JSON Graph loader (idempotent - ignore if already registered)
    from graphforge.datasets.loaders.json_graph import JSONGraphLoader

    try:
        register_loader("json_graph", JSONGraphLoader)
    except ValueError as e:
        # Loader already registered - this is fine
        if "already registered" not in str(e):
            # Re-raise if it's a different ValueError
            raise
