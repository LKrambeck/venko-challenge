Feature: Door control

  @mqtt
  Scenario: Open and close the door
    When I send command "OPEN_DOOR" via MQTT
    Then door_status should be "open"
    When I send command "CLOSE_DOOR" via MQTT
    Then door_status should be "closed"