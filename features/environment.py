import os
import time
import subprocess
import signal

# Import MQTT helpers from steps; environment.py runs as part of Behave's
# lifecycle so we centralize per-scenario setup here.
from features.steps import mqtt_steps as mqtt_helpers

def before_all(context):
    # Ensure a logs directory exists so subprocess stdout/stderr can be captured
    os.makedirs("logs", exist_ok=True)

    # Keep references to launched subprocesses so we can terminate them later
    context.processes = []

    # Prepare environment variables for subprocesses. These values can be
    # overridden by real environment variables (useful in CI or local .env).
    env = os.environ.copy()
    env["API_URL"] = "http://localhost:5000/elevator-data"
    env["QUEUE_FILE"] = "/tmp/bridge_queue.jsonl"
    env["FLUSH_INTERVAL"] = "2.0"

    # Open log files for capturing each component's output. We keep the file
    # handles in context so they can be closed in after_all.
    api_log = open("logs/mock_api.log", "w")
    elev_log = open("logs/mock_elevator.log", "w")
    bridge_log = open("logs/bridge.log", "w")

    context._log_files = [api_log, elev_log, bridge_log]

    # Start the mock API first so it can bind its HTTP port before other
    # components try to contact it.
    # -u: run Python in unbuffered mode so stdout/stderr are flushed immediately (ensures subprocess log output is written to log files without buffering)
    context.processes.append(
        subprocess.Popen(["python3", "-u", "mock_api.py"], stdout=api_log, stderr=api_log, env=env)
    )
    # A short sleep gives the process time to initialize.
    time.sleep(1.0)

    # Start the elevator simulator which will connect to the MQTT broker and
    # begin publishing sensor messages and listening for commands.
    # -u: run Python in unbuffered mode so stdout/stderr are flushed immediately (ensures subprocess log output is written to log files without buffering)
    context.processes.append(
        subprocess.Popen(["python3", "-u", "mock_elevator_mqtt.py"], stdout=elev_log, stderr=elev_log, env=env)
    )
    # Allow the elevator simulator a moment to connect to the broker.
    time.sleep(1.0)

    # Finally start the bridge which subscribes to MQTT sensor data and
    # forwards it to the API. The bridge depends on both the broker and the
    # API being available, so start it last.
    # -u: run Python in unbuffered mode so stdout/stderr are flushed immediately (ensures subprocess log output is written to log files without buffering)
    context.processes.append(
        subprocess.Popen(["python3", "-u", "bridge.py"], stdout=bridge_log, stderr=bridge_log, env=env)
    )
    time.sleep(1.0)


def after_all(context):
    # Gracefully terminate any subprocesses we started. We first check whether
    # the process is still running (poll() is None). If it is, we send
    # SIGTERM to request termination.
    for p in context.processes:
        if p.poll() is None:
            # Send SIGTERM: this politely asks the process to terminate so it
            # can perform cleanup (flush logs, close sockets). Many programs
            # will exit cleanly on SIGTERM.
            p.send_signal(signal.SIGTERM)
            try:
                # Wait briefly for the process to exit. If it doesn't exit in
                # time, fall back to killing it to avoid hanging the test
                # teardown.
                p.wait(timeout=5)
            except Exception:
                # Force kill if polite termination didn't work.
                p.kill()

    # Close any log files we opened earlier.
    for f in getattr(context, "_log_files", []):
        try:
            f.close()
        except Exception:
            pass


def before_scenario(context, scenario):
    """Per-scenario hook. Initialize MQTT helper only for scenarios
    tagged with @mqtt to avoid starting MQTT client for unrelated tests."""
    tags = getattr(scenario, "tags", [])
    if "mqtt" in tags:
        mqtt_helpers.setup_mqtt(context)


def after_scenario(context, scenario):
    """Per-scenario teardown. Only teardown MQTT if it was setup."""
    tags = getattr(scenario, "tags", [])
    if "mqtt" in tags:
        mqtt_helpers.teardown_mqtt(context)