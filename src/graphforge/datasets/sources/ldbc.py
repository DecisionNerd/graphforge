"""LDBC (Linked Data Benchmark Council) dataset registrations.

LDBC provides benchmark datasets for graph databases, including the
Social Network Benchmark (SNB) which models a social network similar
to Facebook.

Source: https://ldbcouncil.org/resources/datasets/
"""

from graphforge.datasets.base import DatasetInfo
from graphforge.datasets.loaders.ldbc import LDBCLoader
from graphforge.datasets.registry import register_dataset, register_loader


def register_ldbc_datasets() -> None:
    """Register LDBC datasets and loader.

    Registers:
    - LDBCLoader for multi-file CSV format
    - LDBC SNB datasets at various scale factors
    """
    # Register loader
    register_loader("ldbc", LDBCLoader)

    # LDBC SNB SF0.001 (smallest scale factor)
    # Note: Actual node/edge counts are approximate and vary by generation
    register_dataset(
        DatasetInfo(
            name="ldbc-snb-sf0.001",
            description="LDBC Social Network Benchmark SF0.001 (smallest scale)",
            source="ldbc",
            url="https://repository.surfsara.nl/datasets/cwi/snb/files/social-network-sf0.001-partitioned-by-activity-CsvComposite-LongDateFormatter.tar.zst",
            nodes=3_000,
            edges=17_000,
            labels=[
                "Person",
                "Post",
                "Comment",
                "Forum",
                "Organisation",
                "Place",
                "Tag",
                "TagClass",
            ],
            relationship_types=[
                "KNOWS",
                "LIKES",
                "HAS_CREATOR",
                "CONTAINER_OF",
                "HAS_MEMBER",
                "HAS_MODERATOR",
                "HAS_TAG",
                "HAS_TYPE",
                "HAS_INTEREST",
                "IS_LOCATED_IN",
                "IS_PART_OF",
                "IS_SUBCLASS_OF",
                "REPLY_OF",
                "STUDY_AT",
                "WORK_AT",
            ],
            size_mb=0.5,
            license="CC BY 4.0",
            category="social",
            loader_class="ldbc",
        )
    )

    # LDBC SNB SF0.1
    register_dataset(
        DatasetInfo(
            name="ldbc-snb-sf0.1",
            description="LDBC Social Network Benchmark SF0.1",
            source="ldbc",
            url="https://repository.surfsara.nl/datasets/cwi/snb/files/social-network-sf0.1-partitioned-by-activity-CsvComposite-LongDateFormatter.tar.zst",
            nodes=32_000,
            edges=180_000,
            labels=[
                "Person",
                "Post",
                "Comment",
                "Forum",
                "Organisation",
                "Place",
                "Tag",
                "TagClass",
            ],
            relationship_types=[
                "KNOWS",
                "LIKES",
                "HAS_CREATOR",
                "CONTAINER_OF",
                "HAS_MEMBER",
                "HAS_MODERATOR",
                "HAS_TAG",
                "HAS_TYPE",
                "HAS_INTEREST",
                "IS_LOCATED_IN",
                "IS_PART_OF",
                "IS_SUBCLASS_OF",
                "REPLY_OF",
                "STUDY_AT",
                "WORK_AT",
            ],
            size_mb=5.0,
            license="CC BY 4.0",
            category="social",
            loader_class="ldbc",
        )
    )

    # LDBC SNB SF1
    register_dataset(
        DatasetInfo(
            name="ldbc-snb-sf1",
            description="LDBC Social Network Benchmark SF1",
            source="ldbc",
            url="https://repository.surfsara.nl/datasets/cwi/snb/files/social-network-sf1-partitioned-by-activity-CsvComposite-LongDateFormatter.tar.zst",
            nodes=328_000,
            edges=1_800_000,
            labels=[
                "Person",
                "Post",
                "Comment",
                "Forum",
                "Organisation",
                "Place",
                "Tag",
                "TagClass",
            ],
            relationship_types=[
                "KNOWS",
                "LIKES",
                "HAS_CREATOR",
                "CONTAINER_OF",
                "HAS_MEMBER",
                "HAS_MODERATOR",
                "HAS_TAG",
                "HAS_TYPE",
                "HAS_INTEREST",
                "IS_LOCATED_IN",
                "IS_PART_OF",
                "IS_SUBCLASS_OF",
                "REPLY_OF",
                "STUDY_AT",
                "WORK_AT",
            ],
            size_mb=50.0,
            license="CC BY 4.0",
            category="social",
            loader_class="ldbc",
        )
    )

    # LDBC SNB SF10
    register_dataset(
        DatasetInfo(
            name="ldbc-snb-sf10",
            description="LDBC Social Network Benchmark SF10",
            source="ldbc",
            url="https://repository.surfsara.nl/datasets/cwi/snb/files/social-network-sf10-partitioned-by-activity-CsvComposite-LongDateFormatter.tar.zst",
            nodes=3_280_000,
            edges=18_000_000,
            labels=[
                "Person",
                "Post",
                "Comment",
                "Forum",
                "Organisation",
                "Place",
                "Tag",
                "TagClass",
            ],
            relationship_types=[
                "KNOWS",
                "LIKES",
                "HAS_CREATOR",
                "CONTAINER_OF",
                "HAS_MEMBER",
                "HAS_MODERATOR",
                "HAS_TAG",
                "HAS_TYPE",
                "HAS_INTEREST",
                "IS_LOCATED_IN",
                "IS_PART_OF",
                "IS_SUBCLASS_OF",
                "REPLY_OF",
                "STUDY_AT",
                "WORK_AT",
            ],
            size_mb=500.0,
            license="CC BY 4.0",
            category="social",
            loader_class="ldbc",
        )
    )
