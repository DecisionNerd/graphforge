"""GraphML format loader registration.

GraphML is an XML-based graph format widely used in network analysis. It supports:
- Typed properties (boolean, int, long, float, double, string)
- Node and edge attributes with schema declarations
- Default values
- Directed and undirected graphs
- Namespaces

This format is used for:
- Loading NetworkRepository datasets
- Importing graphs from Gephi, yEd, NetworkX, igraph
- Standard graph interchange format
- Academic research datasets

Unlike SNAP and LDBC which are public dataset repositories, GraphML is
an interchange format, so no public datasets are registered here.
NetworkRepository datasets will be registered separately when that integration
is complete (Issue #52).
"""

from graphforge.datasets.registry import register_loader


def register_graphml_loader() -> None:
    """Register the GraphML loader in the global registry.

    This registers the loader but does not register any datasets, as GraphML
    is an interchange format rather than a public dataset source. Specific
    GraphML datasets (e.g., NetworkRepository) will be registered separately.
    """
    # Register the GraphML loader (idempotent - ignore if already registered)
    from graphforge.datasets.loaders.graphml import GraphMLLoader

    try:
        register_loader("graphml", GraphMLLoader)
    except ValueError as e:
        # Loader already registered - this is fine
        if "already registered" not in str(e):
            # Re-raise if it's a different ValueError
            raise
