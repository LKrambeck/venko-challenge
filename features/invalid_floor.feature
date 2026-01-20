Feature: Invalid floor command

  @mqtt
  Scenario Outline: Send invalid floor (out of range)
    When I send command "<cmd>" via MQTT
    Then an error event should be published containing "only supports floors between 1 and 10"

    Examples:
      | cmd        |
      | MOVE_TO_0  |
      | MOVE_TO_11 |
      | MOVE_TO_-1 |

  @mqtt
  Scenario: Send non-numeric floor
    When I send command "MOVE_TO_X" via MQTT
    Then an error event should be published containing "Invalid floor value"