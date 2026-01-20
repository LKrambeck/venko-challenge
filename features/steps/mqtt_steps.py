import json
import time
import paho.mqtt.client as mqtt
from behave import when, then

# MQTT topics used by the elevator simulator and tests
TOPIC_DATA = "elevator/sensor_data"
TOPIC_COMMAND = "elevator/command"
TOPIC_EVENTS = "elevator/events"


def setup_mqtt(context, host="localhost", port=1883):
    """Create per-scenario MQTT client and message store and attach to
    `context`. This helper is intended to be called from
    `features/environment.py`'s hooks (not as a step-level hook).
    """
    context.mqtt_messages = {TOPIC_DATA: [], TOPIC_EVENTS: []}
    context.mqtt_client = mqtt.Client()

    def on_message(client, userdata, msg):
        payload = msg.payload.decode()
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = payload
        context.mqtt_messages.setdefault(msg.topic, []).append(data)

    context.mqtt_client.on_message = on_message
    context.mqtt_client.connect(host, port)
    context.mqtt_client.subscribe(TOPIC_DATA)
    context.mqtt_client.subscribe(TOPIC_EVENTS)
    context.mqtt_client.loop_start()


def teardown_mqtt(context):
    """Stop and disconnect the MQTT client attached to `context`.

    Safe to call even if the client is missing.
    """
    try:
        context.mqtt_client.loop_stop()
        context.mqtt_client.disconnect()
    except Exception:
        pass


def wait_for(context, topic, predicate, timeout=10):
    """Polling helper used by steps to wait for a message on `topic` that
    satisfies `predicate`. Returns the matching message or None on timeout.
    """
    start = time.time()
    while time.time() - start < timeout:
        for msg in list(context.mqtt_messages.get(topic, [])):
            if predicate(msg):
                return msg
        time.sleep(0.1)
    return None


@when('I send command "{command}" via MQTT')
def step_send_command(context, command):
    """Publish a raw command string to the `TOPIC_COMMAND` topic
    This simulates the cloud (or a user) sending a command to the elevator.
    """
    context.mqtt_client.publish(TOPIC_COMMAND, command)


@then('elevator position should become {floor:d}')
def step_wait_position(context, floor):
    """Wait for a `sensor_data` message whose `position` field equals
    the expected floor. The helper returns the matched message or fails the
    assertion if none arrives within the timeout.
    """
    msg = wait_for(
        context,
        TOPIC_DATA,
        lambda m: isinstance(m, dict) and m.get("position") == floor,
        timeout=10,
    )
    assert msg is not None, f"Position {floor} not observed"


@then('maintenance_mode should be {state}')
def step_maintenance(context, state):
    """Assert that a subsequent `sensor_data` message reports the
    requested `maintenance_mode` boolean value.
    """
    expected = state.strip().lower() in ("true", "1", "yes")
    msg = wait_for(
        context,
        TOPIC_DATA,
        lambda m: isinstance(m, dict) and m.get("maintenance_mode") == expected,
        timeout=10,
    )
    assert msg is not None, f"maintenance_mode {expected} not observed"


@then('door_status should be "{state}"')
def step_door_status(context, state):
    """Assert that a subsequent `sensor_data` message reports the
    requested `door_status` value.
    """
    expected = state.strip().lower()
    msg = wait_for(
        context,
        TOPIC_DATA,
        lambda m: isinstance(m, dict) and m.get("door_status") == expected,
        timeout=10,
    )
    assert msg is not None, f"door_status {expected} not observed"


@then('an error event should be published containing "{text}"')
def step_error_event(context, text):
    """Wait for an error event on `TOPIC_EVENTS` with `error` text that
    contains the provided substring. This verifies that the simulator
    publishes structured error messages instead of only printing to stdout.
    """
    msg = wait_for(
        context,
        TOPIC_EVENTS,
        lambda m: isinstance(m, dict) and text in m.get("error", ""),
        timeout=5,
    )
    assert msg is not None, f"Error event containing '{text}' not observed"


@then('no error event should be published within {seconds:d} seconds')
def step_no_error_event(context, seconds):
    """Ensure no new error event arrives within the given window."""
    start_len = len(context.mqtt_messages.get(TOPIC_EVENTS, []))
    end_time = time.time() + seconds
    while time.time() < end_time:
        events = context.mqtt_messages.get(TOPIC_EVENTS, [])
        if len(events) > start_len:
            # Check only the newly arrived events
            for event in events[start_len:]:
                if isinstance(event, dict) and event.get("error"):
                    raise AssertionError("Unexpected error event received")
            start_len = len(events)
        time.sleep(0.1)