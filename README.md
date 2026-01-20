<!-- ...existing code... -->
# Elevator Test Automation

## Requirements
- Python 3.8+
- pip
- MQTT broker (e.g. Mosquitto)

## Setup
1. Enter project directory:
```bash
cd /QA_challenge
```
2. Install Python dependencies:
```bash
pip install -r requirements.txt
```
3. Install and run Mosquitto (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install -y mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
```

## Running tests (automatic)
Execute the test runner which starts API, elevator simulator and bridge, then runs Behave and produces Allure results:
```bash
chmod +x run_tests.sh
./run_tests.sh
# view report: allure serve allure-results   (requires Allure installed)
```

## Running components manually (for debugging)
1. API:
```bash
python3 mock_api.py
```
2. Elevator simulator (MQTT):
```bash
python3 mock_elevator_mqtt.py
```
3. Bridge (MQTT → API):
```bash
python3 bridge.py
```

## Commands supported by the elevator simulator (MQTT)
- MAINTENANCE_ON / MAINTENANCE_OFF
- MOVE_TO_<N> (N = 1..10)
- OPEN_DOOR / CLOSE_DOOR

When maintenance mode is active, MOVE_TO commands are rejected and an error event is published.

## Useful endpoints & files
- POST /elevator-data — API endpoint that receives elevator data
- GET /received — inspect messages received by API
- POST /simulate_failure {"down": true|false} — toggle API failure simulation
- bridge_queue.jsonl — local queue file used by bridge (default /tmp/bridge_queue.jsonl when run via tests)
- logs/ — logs produced when tests run via Behave

## Notes
- Features/ contains Behave Gherkin scenarios and step implementations.
- The test environment starts mock_api, mock_elevator_mqtt and bridge automatically.
- MQTT scenarios are tagged with @mqtt; the MQTT client is initialized only for those scenarios.