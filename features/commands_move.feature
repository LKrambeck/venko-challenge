Feature: Move elevator by cloud commands

  @mqtt
  Scenario Outline: Move to a valid floor
    When I send command "<cmd>" via MQTT
    Then elevator position should become <floor>

    Examples:
      | cmd       | floor |
      | MOVE_TO_1 | 1     |
      | MOVE_TO_5 | 5     |
      | MOVE_TO_10| 10    |

  @mqtt
  Scenario: Move to same floor is idempotent
    When I send command "MOVE_TO_5" via MQTT
    Then elevator position should become 5
    When I send command "MOVE_TO_5" via MQTT
    Then elevator position should become 5
    And no error event should be published within 3 seconds