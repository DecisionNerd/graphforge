@tck
Feature: Aggregation1 - Basic aggregation functions

  # openCypher TCK Scenario: COUNT(*)
  Scenario: Count all rows with COUNT(*)
    Given an empty graph
    And having executed
      """
      CREATE (:Person {name: 'Alice'}),
             (:Person {name: 'Bob'}),
             (:Person {name: 'Charlie'})
      """
    When executing query
      """
      MATCH (p:Person)
      RETURN COUNT(*) AS count
      """
    Then the result should be, in any order
      | count |
      | 3     |
    And no side effects

  # openCypher TCK Scenario: COUNT with expression
  Scenario: Count non-null values with COUNT(expr)
    Given an empty graph
    And having executed
      """
      CREATE (:Person {name: 'Alice', age: 30}),
             (:Person {name: 'Bob', age: 25}),
             (:Person {name: 'Charlie'})
      """
    When executing query
      """
      MATCH (p:Person)
      RETURN COUNT(p.age) AS count
      """
    Then the result should be, in any order
      | count |
      | 2     |
    And no side effects

  # openCypher TCK Scenario: SUM aggregation
  Scenario: Sum numeric values with SUM
    Given an empty graph
    And having executed
      """
      CREATE (:Person {name: 'Alice', age: 30}),
             (:Person {name: 'Bob', age: 25}),
             (:Person {name: 'Charlie', age: 35})
      """
    When executing query
      """
      MATCH (p:Person)
      RETURN SUM(p.age) AS total
      """
    Then the result should be, in any order
      | total |
      | 90    |
    And no side effects

  # openCypher TCK Scenario: AVG aggregation
  Scenario: Average numeric values with AVG
    Given an empty graph
    And having executed
      """
      CREATE (:Person {name: 'Alice', age: 30}),
             (:Person {name: 'Bob', age: 25}),
             (:Person {name: 'Charlie', age: 35})
      """
    When executing query
      """
      MATCH (p:Person)
      RETURN AVG(p.age) AS average
      """
    Then the result should be, in any order
      | average |
      | 30.0    |
    And no side effects

  # openCypher TCK Scenario: MIN and MAX
  Scenario: Find minimum and maximum with MIN and MAX
    Given an empty graph
    And having executed
      """
      CREATE (:Person {name: 'Alice', age: 30}),
             (:Person {name: 'Bob', age: 25}),
             (:Person {name: 'Charlie', age: 35})
      """
    When executing query
      """
      MATCH (p:Person)
      RETURN MIN(p.age) AS minimum, MAX(p.age) AS maximum
      """
    Then the result should be, in any order
      | minimum | maximum |
      | 25      | 35      |
    And no side effects

  # openCypher TCK Scenario: Grouping with aggregation
  Scenario: Group by property and count
    Given an empty graph
    And having executed
      """
      CREATE (:Person {name: 'Alice', city: 'NYC'}),
             (:Person {name: 'Bob', city: 'NYC'}),
             (:Person {name: 'Charlie', city: 'LA'})
      """
    When executing query
      """
      MATCH (p:Person)
      RETURN p.city AS city, COUNT(*) AS count
      ORDER BY city
      """
    Then the result should be, in order
      | city  | count |
      | 'LA'  | 1     |
      | 'NYC' | 2     |
    And no side effects
