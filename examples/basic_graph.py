"""Basic GraphForge example - Creating and querying a simple graph.

This example demonstrates:
- Creating nodes with labels and properties
- Creating relationships
- Querying with openCypher
- Using aggregation functions
"""

from graphforge import GraphForge

# Create a graph workbench
print("Creating GraphForge instance...")
db = GraphForge()

# Create some people
print("\n Creating nodes...")
alice = db.create_node(["Person"], name="Alice", age=30, city="NYC")
bob = db.create_node(["Person"], name="Bob", age=25, city="NYC")
charlie = db.create_node(["Person"], name="Charlie", age=35, city="LA")
dave = db.create_node(["Person"], name="Dave", age=28, city="LA")

print(f"Created {4} people")

# Create friendships
print("\nCreating relationships...")
db.create_relationship(alice, bob, "KNOWS", since=2015)
db.create_relationship(alice, charlie, "KNOWS", since=2018)
db.create_relationship(bob, dave, "KNOWS", since=2020)
db.create_relationship(charlie, dave, "KNOWS", since=2019)

print(f"Created {4} friendships")

# Query 1: Find all people
print("\n--- Query 1: All people ---")
results = db.execute("MATCH (p:Person) RETURN p.name AS name, p.age AS age ORDER BY name")
for row in results:
    print(f"  {row['name'].value}, age {row['age'].value}")

# Query 2: Find people over 28
print("\n--- Query 2: People over 28 ---")
results = db.execute("""
    MATCH (p:Person)
    WHERE p.age > 28
    RETURN p.name AS name, p.age AS age
    ORDER BY p.age DESC
""")
for row in results:
    print(f"  {row['name'].value}, age {row['age'].value}")

# Query 3: Find Alice's friends
print("\n--- Query 3: Alice's friends ---")
results = db.execute("""
    MATCH (alice:Person)-[r:KNOWS]->(friend:Person)
    WHERE alice.name = 'Alice'
    RETURN friend.name AS name, r.since AS since
    ORDER BY r.since
""")
for row in results:
    print(f"  {row['name'].value} (friends since {row['since'].value})")

# Query 4: Count people by city (sorted by city name)
print("\n--- Query 4: People by city ---")
results = db.execute("""
    MATCH (p:Person)
    RETURN p.city AS city, COUNT(*) AS count
    ORDER BY city
""")
for row in results:
    print(f"  {row['city'].value}: {row['count'].value} people")

# Query 5: Average age by city (sorted by city name)
print("\n--- Query 5: Average age by city ---")
results = db.execute("""
    MATCH (p:Person)
    RETURN p.city AS city, AVG(p.age) AS avg_age
    ORDER BY city
""")
for row in results:
    print(f"  {row['city'].value}: {row['avg_age'].value:.1f} years average")

print("\nDone!")
