"""Data Lineage Tracking with GraphForge

This example demonstrates tracking data transformations and dependencies.

Use Case: Understand data flow in an ETL pipeline and impact analysis
"""

from graphforge import GraphForge


def main():
    # Create persistent graph
    db = GraphForge("data-lineage.db")

    print("Building data lineage graph...")

    try:
        db.begin()

        # Create data sources
        sources = [
            ("users_db", "Database", "production"),
            ("orders_db", "Database", "production"),
            ("events_s3", "S3 Bucket", "raw"),
        ]

        for name, source_type, environment in sources:
            db.execute(f"""
                CREATE (:DataSource {{
                    name: '{name}',
                    type: '{source_type}',
                    environment: '{environment}'
                }})
            """)

        # Create datasets/tables
        datasets = [
            ("users", "Table", "production"),
            ("orders", "Table", "production"),
            ("events", "Table", "raw"),
            ("user_activity", "Table", "analytics"),
            ("order_summary", "Table", "analytics"),
            ("daily_revenue", "View", "reporting"),
        ]

        for name, dataset_type, environment in datasets:
            db.execute(f"""
                CREATE (:Dataset {{
                    name: '{name}',
                    type: '{dataset_type}',
                    environment: '{environment}'
                }})
            """)

        # Create transformations/jobs
        jobs = [
            ("extract_users", "ETL", "daily"),
            ("extract_orders", "ETL", "daily"),
            ("join_user_orders", "Transform", "daily"),
            ("aggregate_revenue", "Transform", "daily"),
        ]

        for name, job_type, schedule in jobs:
            db.execute(f"""
                CREATE (:Job {{
                    name: '{name}',
                    type: '{job_type}',
                    schedule: '{schedule}'
                }})
            """)

        # Create lineage relationships

        # Sources → Datasets
        lineage = [
            ("users_db", "PROVIDES", "users"),
            ("orders_db", "PROVIDES", "orders"),
            ("events_s3", "PROVIDES", "events"),
        ]

        for src, rel, dst in lineage:
            db.execute(f"""
                MATCH (a:DataSource {{name: '{src}'}}), (b:Dataset {{name: '{dst}'}})
                CREATE (a)-[:{rel}]->(b)
            """)

        # Jobs → Data Flow
        job_flows = [
            ("users", "INPUT_TO", "extract_users"),
            ("extract_users", "PRODUCES", "user_activity"),
            ("orders", "INPUT_TO", "extract_orders"),
            ("extract_orders", "PRODUCES", "order_summary"),
            ("user_activity", "INPUT_TO", "join_user_orders"),
            ("order_summary", "INPUT_TO", "join_user_orders"),
            ("join_user_orders", "PRODUCES", "daily_revenue"),
        ]

        for src, rel, dst in job_flows:
            # Handle both Dataset and Job nodes
            db.execute(f"""
                MATCH (a {{name: '{src}'}}), (b {{name: '{dst}'}})
                CREATE (a)-[:{rel}]->(b)
            """)

        db.commit()
        print(
            f"Created lineage graph with {len(sources)} sources, {len(datasets)} datasets, and {len(jobs)} jobs\n"
        )

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        return

    # Analysis 1: Trace lineage of daily_revenue
    print("=" * 60)
    print("ANALYSIS 1: Upstream Dependencies of 'daily_revenue'")
    print("=" * 60)
    print("(What data sources does this report depend on?)")

    results = db.execute("""
        MATCH (source)-[*1..5]->(report:Dataset {name: 'daily_revenue'})
        WHERE source:DataSource
        RETURN DISTINCT source.name AS source, source.type AS type
    """)

    # Note: Variable-length paths not yet supported, so we'll do 2-hop manually
    results = db.execute("""
        MATCH (source:DataSource)-[]->(dataset)-[*1..3]->(report:Dataset {name: 'daily_revenue'})
        RETURN DISTINCT source.name AS source, source.type AS type
    """)

    # Since variable-length is not supported, let's trace manually
    print("  Direct dependencies:")
    results = db.execute("""
        MATCH (upstream)-[]->(job)-[:PRODUCES]->(report:Dataset {name: 'daily_revenue'})
        RETURN DISTINCT upstream.name AS name
    """)
    for row in results:
        print(f"    → {row['name'].value}")

    # Analysis 2: Find all datasets in analytics environment
    print("\n" + "=" * 60)
    print("ANALYSIS 2: Analytics Datasets")
    print("=" * 60)

    results = db.execute("""
        MATCH (d:Dataset)
        WHERE d.environment = 'analytics'
        RETURN d.name AS dataset, d.type AS type
    """)

    for row in results:
        print(f"  {row['dataset'].value} ({row['type'].value})")

    # Analysis 3: Impact analysis - what depends on users table?
    print("\n" + "=" * 60)
    print("ANALYSIS 3: Impact Analysis - What Depends on 'users'?")
    print("=" * 60)
    print("(If we change the users table, what breaks?)")

    results = db.execute("""
        MATCH (users:Dataset {name: 'users'})-[]->(job:Job)
        RETURN job.name AS affected_job
    """)

    for row in results:
        print(f"  ⚠ Job: {row['affected_job'].value}")

    # Analysis 4: Find daily jobs
    print("\n" + "=" * 60)
    print("ANALYSIS 4: Daily ETL Jobs")
    print("=" * 60)

    results = db.execute("""
        MATCH (j:Job)
        WHERE j.schedule = 'daily'
        RETURN j.name AS job, j.type AS type
        ORDER BY j.name
    """)

    for row in results:
        print(f"  {row['job'].value} ({row['type'].value})")

    # Analysis 5: Data sources by environment
    print("\n" + "=" * 60)
    print("ANALYSIS 5: Data Sources by Environment")
    print("=" * 60)

    results = db.execute("""
        MATCH (s:DataSource)
        RETURN s.environment AS environment, count(*) AS count
        ORDER BY count DESC
    """)

    for row in results:
        print(f"  {row['environment'].value}: {row['count'].value} sources")

    # Analysis 6: Trace a specific transformation
    print("\n" + "=" * 60)
    print("ANALYSIS 6: Join User Orders Transformation")
    print("=" * 60)

    # Inputs
    print("  Inputs:")
    results = db.execute("""
        MATCH (input)-[:INPUT_TO]->(job:Job {name: 'join_user_orders'})
        RETURN input.name AS input
    """)
    for row in results:
        print(f"    ← {row['input'].value}")

    # Outputs
    print("  Outputs:")
    results = db.execute("""
        MATCH (job:Job {name: 'join_user_orders'})-[:PRODUCES]->(output)
        RETURN output.name AS output
    """)
    for row in results:
        print(f"    → {row['output'].value}")

    # Analysis 7: Count nodes by type
    print("\n" + "=" * 60)
    print("ANALYSIS 7: Lineage Graph Statistics")
    print("=" * 60)

    # Count each node type
    for node_type in ["DataSource", "Dataset", "Job"]:
        results = db.execute(f"""
            MATCH (n:{node_type})
            RETURN count(*) AS count
        """)
        count = results[0]["count"].value
        print(f"  {node_type}s: {count}")

    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
    print("\nData lineage graph saved to: data-lineage.db")

    db.close()


if __name__ == "__main__":
    main()
