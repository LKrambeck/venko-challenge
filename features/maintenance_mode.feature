Feature: Maintenance mode

  @mqtt
  Scenario: Toggle maintenance mode
    When I send command "MAINTENANCE_ON" via MQTT
    Then maintenance_mode should be true
    When I send command "MAINTENANCE_OFF" via MQTT
    Then maintenance_mode should be false

  @mqtt
  Scenario: Block MOVE_TO while in maintenance mode
    When I send command "MAINTENANCE_ON" via MQTT
    Then maintenance_mode should be true
    When I send command "MOVE_TO_5" via MQTT
    Then an error event should be published containing "maintenance"
    When I send command "MAINTENANCE_OFF" via MQTT
    Then maintenance_mode should be false
    When I send command "MOVE_TO_5" via MQTT
    Then elevator position should become 5