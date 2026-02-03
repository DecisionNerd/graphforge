"""SNAP (Stanford Network Analysis Project) dataset registrations.

SNAP provides a collection of large network datasets from real-world sources
including social networks, web graphs, collaboration networks, and more.

Source: https://snap.stanford.edu/data/
"""

from graphforge.datasets.base import DatasetInfo
from graphforge.datasets.registry import register_dataset, register_loader


def register_snap_datasets() -> None:
    """Register all SNAP datasets in the global registry."""
    # Register the CSV loader
    from graphforge.datasets.loaders.csv import CSVLoader

    register_loader("csv", CSVLoader)

    # Register SNAP datasets
    datasets = [
        DatasetInfo(
            name="snap-ego-facebook",
            description="Facebook social circles (ego networks)",
            source="snap",
            url="https://snap.stanford.edu/data/facebook_combined.txt.gz",
            nodes=4039,
            edges=88234,
            labels=["Node"],
            relationship_types=["CONNECTED_TO"],
            size_mb=0.5,
            license="Public Domain",
            category="social",
            loader_class="csv",
        ),
        DatasetInfo(
            name="snap-email-enron",
            description="Enron email communication network",
            source="snap",
            url="https://snap.stanford.edu/data/email-Enron.txt.gz",
            nodes=36692,
            edges=183831,
            labels=["Node"],
            relationship_types=["CONNECTED_TO"],
            size_mb=2.5,
            license="Public Domain",
            category="communication",
            loader_class="csv",
        ),
        DatasetInfo(
            name="snap-ca-astroph",
            description="Astrophysics collaboration network",
            source="snap",
            url="https://snap.stanford.edu/data/ca-AstroPh.txt.gz",
            nodes=18772,
            edges=198110,
            labels=["Node"],
            relationship_types=["CONNECTED_TO"],
            size_mb=1.8,
            license="Public Domain",
            category="collaboration",
            loader_class="csv",
        ),
        DatasetInfo(
            name="snap-web-google",
            description="Google web graph from 2002",
            source="snap",
            url="https://snap.stanford.edu/data/web-Google.txt.gz",
            nodes=875713,
            edges=5105039,
            labels=["Node"],
            relationship_types=["CONNECTED_TO"],
            size_mb=75.0,
            license="Public Domain",
            category="web",
            loader_class="csv",
        ),
        DatasetInfo(
            name="snap-twitter-combined",
            description="Twitter social circles (combined ego networks)",
            source="snap",
            url="https://snap.stanford.edu/data/twitter_combined.txt.gz",
            nodes=81306,
            edges=1768149,
            labels=["Node"],
            relationship_types=["CONNECTED_TO"],
            size_mb=25.0,
            license="Public Domain",
            category="social",
            loader_class="csv",
        ),
    ]

    for dataset in datasets:
        register_dataset(dataset)
