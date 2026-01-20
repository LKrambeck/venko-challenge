Feature: Offline buffering

  Scenario: Buffer data while API is down
    Given API is down
    When I wait up to 15 seconds until queue has at least 2 items
    Then bridge queue file should have at least 2 items
    Given API is up
    Then bridge queue file should be empty within 15 seconds