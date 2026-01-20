#!/usr/bin/env bash
set -euo pipefail

# quick pre-check for MQTT broker (port 1883) on localhost
if ! ss -ltn | grep -q ':1883'; then
  echo "MQTT broker not detected on localhost:1883"
  echo "Please start Mosquitto, for example:"
  echo "  sudo apt-get install -y mosquitto mosquitto-clients && sudo systemctl enable --now mosquitto"
  exit 1
fi

rm -rf logs allure-results
mkdir -p logs allure-results

behave -f allure_behave.formatter:AllureFormatter -o allure-results ./features

echo "Allure results generated in ./allure-results"
echo "To view the report, run: allure serve allure-results"