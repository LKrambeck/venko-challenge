Feature: API validation

  Scenario Outline: Missing a required field
    When I POST invalid payload <payload>
    Then response status should be 400
    And response error should contain "Missing fields"

    Examples:
      | payload                               |
      | {"door_status":"closed","weight":0}   |
      | {"position":1,"weight":0}             |
      | {"position":1,"door_status":"closed"} |
      | {}                                    |

  Scenario Outline: Invalid position (edge cases)
    When I POST invalid payload {"position": <pos>, "door_status": "open", "weight": 10}
    Then response status should be 400
    And response error should contain "Invalid position"

    Examples:
      | pos |
      | 0   |
      | 11  |

  Scenario: Invalid door_status
    When I POST invalid payload {"position": 1, "door_status": "bug", "weight": 10}
    Then response status should be 400
    And response error should contain "Invalid door_status"

  Scenario Outline: Invalid weight (edge cases)
    When I POST invalid payload {"position": 1, "door_status": "open", "weight": <w>}
    Then response status should be 400
    And response error should contain "Invalid weight"

    Examples:
      | w    |
      | -1   |
      | 1001 |