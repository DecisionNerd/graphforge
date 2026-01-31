@tck
Feature: Match1 - Basic MATCH patterns

  # openCypher TCK Scenario: Match all nodes
  Scenario: Match all nodes
    Given an empty graph
    And having executed
      """
      CREATE ({name: 'A'}),
             ({name: 'B'}),
             ({name: 'C'})
      """
    When executing query
      """
      MATCH (n)
      RETURN n
      """
    Then the result should be, in any order
      | n             |
      | ({name: 'A'}) |
      | ({name: 'B'}) |
      | ({name: 'C'}) |
    And no side effects

  # openCypher TCK Scenario: Match nodes by label
  Scenario: Match nodes with a specific label
    Given an empty graph
    And having executed
      """
      CREATE (:Person {name: 'Alice'}),
             (:Person {name: 'Bob'}),
             (:Dog {name: 'Rex'})
      """
    When executing query
      """
      MATCH (p:Person)
      RETURN p.name AS name
      """
    Then the result should be, in any order
      | name    |
      | 'Alice' |
      | 'Bob'   |
    And no side effects

  # openCypher TCK Scenario: Match with property filter
  Scenario: Match nodes with WHERE clause on property
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
      WHERE p.age > 30
      RETURN p.name AS name
      """
    Then the result should be, in any order
      | name      |
      | 'Charlie' |
    And no side effects

  # openCypher TCK Scenario: Return with LIMIT
  Scenario: Match with LIMIT clause
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
      RETURN p.name AS name
      LIMIT 2
      """
    Then the result should have 2 rows
    And no side effects

  # openCypher TCK Scenario: Return with SKIP
  Scenario: Match with SKIP clause
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
      RETURN p.name AS name
      ORDER BY name
      SKIP 1
      """
    Then the result should be, in order
      | name      |
      | 'Bob'     |
      | 'Charlie' |
    And no side effects
