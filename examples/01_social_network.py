"""Social Network Analysis with GraphForge

This example demonstrates building and analyzing a social network graph.

Use Case: Friend recommendations based on mutual connections
"""

from graphforge import GraphForge


def main():
    # Create in-memory graph for this example
    db = GraphForge()

    print("Building social network...")

    # Create people
    people = [
        ("Alice", 30, "NYC"),
        ("Bob", 25, "NYC"),
        ("Charlie", 35, "LA"),
        ("Diana", 28, "NYC"),
        ("Eve", 32, "Boston"),
        ("Frank", 27, "NYC"),
        ("Grace", 29, "LA"),
    ]

    for name, age, city in people:
        db.execute(f"""
            CREATE (:Person {{name: '{name}', age: {age}, city: '{city}'}})
        """)

    # Create friendships (undirected in social context, but we model as directed)
    friendships = [
        ("Alice", "Bob", 2015),
        ("Alice", "Charlie", 2018),
        ("Bob", "Diana", 2019),
        ("Charlie", "Eve", 2017),
        ("Diana", "Frank", 2020),
        ("Eve", "Grace", 2016),
        ("Bob", "Frank", 2021),
    ]

    for person1, person2, year in friendships:
        db.execute(f"""
            MATCH (a:Person {{name: '{person1}'}}), (b:Person {{name: '{person2}'}})
            CREATE (a)-[:KNOWS {{since: {year}}}]->(b),
                   (b)-[:KNOWS {{since: {year}}}]->(a)
        """)

    print(f"Created {len(people)} people and {len(friendships) * 2} friendships\n")

    # Analysis 1: Find all of Alice's friends
    print("=" * 60)
    print("ANALYSIS 1: Alice's Direct Friends")
    print("=" * 60)

    results = db.execute("""
        MATCH (alice:Person {name: 'Alice'})-[r:KNOWS]->(friend:Person)
        RETURN friend.name AS name, r.since AS since
        ORDER BY r.since
    """)

    for row in results:
        print(f"  {row['name'].value} (friends since {row['since'].value})")

    # Analysis 2: Friend recommendations (friends of friends)
    print("\n" + "=" * 60)
    print("ANALYSIS 2: Friend Recommendations for Alice")
    print("=" * 60)
    print("(People who are friends with Alice's friends, but not with Alice)")

    results = db.execute("""
        MATCH (alice:Person {name: 'Alice'})-[:KNOWS]->(friend)-[:KNOWS]->(foaf)
        WHERE NOT (alice)-[:KNOWS]->(foaf) AND alice <> foaf
        RETURN DISTINCT foaf.name AS recommendation
    """)

    for row in results:
        print(f"  → {row['recommendation'].value}")

    # Analysis 3: Most connected people
    print("\n" + "=" * 60)
    print("ANALYSIS 3: Most Connected People")
    print("=" * 60)

    results = db.execute("""
        MATCH (p:Person)-[:KNOWS]->(friend)
        RETURN p.name AS person, count(friend) AS connections
        ORDER BY connections DESC
        LIMIT 3
    """)

    for row in results:
        print(f"  {row['person'].value}: {row['connections'].value} connections")

    # Analysis 4: People in the same city
    print("\n" + "=" * 60)
    print("ANALYSIS 4: People by City")
    print("=" * 60)

    results = db.execute("""
        MATCH (p:Person)
        RETURN p.city AS city, count(*) AS population
        ORDER BY population DESC
    """)

    for row in results:
        print(f"  {row['city'].value}: {row['population'].value} people")

    # Analysis 5: Find mutual friends
    print("\n" + "=" * 60)
    print("ANALYSIS 5: Mutual Friends (Alice & Bob)")
    print("=" * 60)

    results = db.execute("""
        MATCH (alice:Person {name: 'Alice'})-[:KNOWS]->(mutual)<-[:KNOWS]-(bob:Person {name: 'Bob'})
        WHERE alice <> bob
        RETURN mutual.name AS mutual_friend
    """)

    mutual_friends = [row["mutual_friend"].value for row in results]
    if mutual_friends:
        for friend in mutual_friends:
            print(f"  → {friend}")
    else:
        print("  (no mutual friends)")

    # Analysis 6: Degrees of separation
    print("\n" + "=" * 60)
    print("ANALYSIS 6: Two-Hop Connections from Alice")
    print("=" * 60)
    print("(People Alice can reach through exactly 2 connections)")

    results = db.execute("""
        MATCH (alice:Person {name: 'Alice'})-[:KNOWS]->()-[:KNOWS]->(person)
        WHERE alice <> person
        RETURN DISTINCT person.name AS name
    """)

    for row in results:
        print(f"  → {row['name'].value}")

    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
