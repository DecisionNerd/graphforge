"""Academic Citation Network with GraphForge

This example demonstrates analyzing research paper citations.

Use Case: Find influential papers, co-author networks, and citation patterns
"""

from graphforge import GraphForge


def main():
    db = GraphForge()

    print("Building citation network...")

    # Create papers
    papers = [
        ("P1", "Attention Is All You Need", 2017, 15000),
        ("P2", "BERT: Pre-training of Deep Transformers", 2018, 12000),
        ("P3", "GPT-3: Language Models are Few-Shot Learners", 2020, 8000),
        ("P4", "ResNet: Deep Residual Learning", 2015, 20000),
        ("P5", "Graph Neural Networks: A Review", 2019, 3000),
        ("P6", "Node2Vec: Scalable Feature Learning", 2016, 5000),
    ]

    for paper_id, title, year, citations in papers:
        db.execute(f"""
            CREATE (:Paper {{
                id: '{paper_id}',
                title: '{title}',
                year: {year},
                citations: {citations}
            }})
        """)

    # Create authors
    authors = [
        ("Vaswani", "Google"),
        ("Devlin", "Google"),
        ("Brown", "OpenAI"),
        ("He", "Microsoft"),
        ("Zhou", "Tsinghua"),
        ("Grover", "Stanford"),
    ]

    for name, affiliation in authors:
        db.execute(f"""
            CREATE (:Author {{name: '{name}', affiliation: '{affiliation}'}})
        """)

    # Link authors to papers
    authorships = [
        ("Vaswani", "P1"),
        ("Devlin", "P2"),
        ("Brown", "P3"),
        ("He", "P4"),
        ("Zhou", "P5"),
        ("Grover", "P6"),
        ("Zhou", "P6"),  # Co-authorship
    ]

    for author, paper in authorships:
        db.execute(f"""
            MATCH (a:Author {{name: '{author}'}}), (p:Paper {{id: '{paper}'}})
            CREATE (a)-[:AUTHORED]->(p)
        """)

    # Create citations
    citations_data = [
        ("P2", "P1"),  # BERT cites Attention
        ("P3", "P1"),  # GPT-3 cites Attention
        ("P3", "P2"),  # GPT-3 cites BERT
        ("P5", "P6"),  # GNN Review cites Node2Vec
    ]

    for citing, cited in citations_data:
        db.execute(f"""
            MATCH (citing:Paper {{id: '{citing}'}}), (cited:Paper {{id: '{cited}'}})
            CREATE (citing)-[:CITES]->(cited)
        """)

    print(
        f"Created {len(papers)} papers, {len(authors)} authors, {len(citations_data)} citations\n"
    )

    # Analysis 1: Most cited papers (in-network)
    print("=" * 60)
    print("ANALYSIS 1: Most Cited Papers (In-Network)")
    print("=" * 60)

    results = db.execute("""
        MATCH (p:Paper)<-[:CITES]-(citing)
        RETURN p.title AS paper, count(citing) AS in_network_citations
        ORDER BY in_network_citations DESC
    """)

    for row in results:
        print(f"  {row['paper'].value}: {row['in_network_citations'].value} citations")

    # Analysis 2: Find co-authors
    print("\n" + "=" * 60)
    print("ANALYSIS 2: Co-Author Pairs")
    print("=" * 60)

    results = db.execute("""
        MATCH (a1:Author)-[:AUTHORED]->(p:Paper)<-[:AUTHORED]-(a2:Author)
        WHERE a1.name < a2.name
        RETURN a1.name AS author1, a2.name AS author2, p.title AS paper
    """)

    co_author_pairs = list(results)
    if co_author_pairs:
        for row in co_author_pairs:
            print(f"  {row['author1'].value} & {row['author2'].value}: {row['paper'].value}")
    else:
        print("  (no co-authors with multiple papers)")

    # Analysis 3: Papers by affiliation
    print("\n" + "=" * 60)
    print("ANALYSIS 3: Papers by Institution")
    print("=" * 60)

    results = db.execute("""
        MATCH (a:Author)-[:AUTHORED]->(p:Paper)
        RETURN a.affiliation AS institution, count(p) AS papers
        ORDER BY papers DESC
    """)

    for row in results:
        print(f"  {row['institution'].value}: {row['papers'].value} papers")

    # Analysis 4: Papers by year
    print("\n" + "=" * 60)
    print("ANALYSIS 4: Papers by Year")
    print("=" * 60)

    results = db.execute("""
        MATCH (p:Paper)
        RETURN p.year AS year, count(*) AS papers
        ORDER BY year
    """)

    for row in results:
        print(f"  {row['year'].value}: {row['papers'].value} papers")

    # Analysis 5: What does GPT-3 cite?
    print("\n" + "=" * 60)
    print("ANALYSIS 5: GPT-3 References")
    print("=" * 60)

    results = db.execute("""
        MATCH (gpt:Paper {title: 'GPT-3: Language Models are Few-Shot Learners'})-[:CITES]->(cited:Paper)
        RETURN cited.title AS paper, cited.year AS year
        ORDER BY year
    """)

    for row in results:
        print(f"  → {row['paper'].value} ({row['year'].value})")

    # Analysis 6: Find highly cited papers
    print("\n" + "=" * 60)
    print("ANALYSIS 6: Highly Cited Papers (>10K citations)")
    print("=" * 60)

    results = db.execute("""
        MATCH (p:Paper)
        WHERE p.citations > 10000
        RETURN p.title AS paper, p.citations AS citations
        ORDER BY citations DESC
    """)

    for row in results:
        print(f"  {row['paper'].value}: {row['citations'].value:,} citations")

    # Analysis 7: Prolific authors
    print("\n" + "=" * 60)
    print("ANALYSIS 7: Most Prolific Authors")
    print("=" * 60)

    results = db.execute("""
        MATCH (a:Author)-[:AUTHORED]->(p:Paper)
        RETURN a.name AS author, a.affiliation AS affiliation, count(p) AS papers
        ORDER BY papers DESC
        LIMIT 3
    """)

    for row in results:
        print(f"  {row['author'].value} ({row['affiliation'].value}): {row['papers'].value} papers")

    # Analysis 8: Citation chain
    print("\n" + "=" * 60)
    print("ANALYSIS 8: Citation Chains from GPT-3")
    print("=" * 60)
    print("(Papers cited by papers cited by GPT-3)")

    results = db.execute("""
        MATCH (gpt:Paper {id: 'P3'})-[:CITES]->(cited)-[:CITES]->(second_level)
        RETURN DISTINCT second_level.title AS paper
    """)

    chain_papers = list(results)
    if chain_papers:
        for row in chain_papers:
            print(f"  → {row['paper'].value}")
    else:
        print("  (no second-level citations in network)")

    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
