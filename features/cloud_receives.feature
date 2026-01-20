Feature: Cloud receives periodic data

  Scenario: Cloud receives data periodically
    Given I record current received count
    Then cloud should have received at least 1 new messages within 8 seconds
    Then cloud should have received at least 2 new messages within 15 seconds