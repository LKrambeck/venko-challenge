from ast import Store
import time
import requests
import os
import json
from behave import given, when, then

# Base URL for the mock API. Tests assume the API is running on localhost:5000
API_BASE = "http://localhost:5000"
QUEUE_FILE = os.getenv("QUEUE_FILE", "/tmp/bridge_queue.jsonl")


def get_received():
    """Fetch all messages stored by the mock API."""
    resp = requests.get(f"{API_BASE}/received", timeout=2)
    resp.raise_for_status()
    return resp.json()

def read_queue_count():
    """Count JSONL items in the bridge queue file."""
    if not os.path.exists(QUEUE_FILE):
        return 0
    with open(QUEUE_FILE, "r") as f:
        return sum(1 for line in f if line.strip())

def wait_until(predicate, timeout=10, interval=0.2):
    """Poll a predicate until True or timeout; returns True/False."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


@given("API is up")
def step_api_up(context):
    """Tell the mock API to stop simulating failures.

    The mock API implements POST /simulate_failure {down: bool} which, when
    set to true, makes the API return 500 for /elevator-data. Tests toggle
    this to simulate network/server outages.
    """
    requests.post(f"{API_BASE}/simulate_failure", json={"down": False}, timeout=2)


@given("API is down")
def step_api_down(context):
    """Tell the mock API to simulate a failure (return 500 responses).

    This is used by offline-buffering scenarios to exercise the bridge's
    local queueing and retry behavior.
    """
    requests.post(f"{API_BASE}/simulate_failure", json={"down": True}, timeout=2)


@when("I wait {seconds:d} seconds")
def step_wait_seconds(context, seconds):
    time.sleep(seconds)


@given("I record current received count")
def step_record_received(context):
    """Store the current list of received messages on the shared context so
    subsequent steps can measure deltas.
    """
    context.received_before = get_received()

@then("cloud should have received at least {count:d} new messages")
def step_received_at_least(context, count):
    current = len(get_received())
    assert current >= context.received_count + count, (
        f"Expected at least {count} new messages, got {current - context.received_count}"
    )


@then("cloud should have received at least {count:d} new messages within {seconds:d} seconds")
def step_received_at_least_within(context, count, seconds):
    start = getattr(context, "received_count", 0)
    ok = wait_until(lambda: len(get_received()) >= start + count, timeout=seconds)
    assert ok, f"Did not receive {count} new messages within {seconds}s"

@when("I wait up to {seconds:d} seconds until queue has at least {count:d} items")
def step_wait_queue_at_least(context, seconds, count):
    ok = wait_until(lambda: read_queue_count() >= count, timeout=seconds)
    assert ok, f"Queue did not reach {count} items within {seconds}s"


@when('I POST invalid payload {payload}')
def step_post_invalid(context, payload):
    """POST the given JSON payload string to the API and store the
    response on `context.last_response` for later assertions.
    """
    data = json.loads(payload)
    context.last_response = requests.post(f"{API_BASE}/elevator-data", json=data, timeout=2)


@then('response status should be {status:d}')
def step_status(context, status):
    # Assert the HTTP status code from the last stored response
    assert context.last_response.status_code == status


@then('response error should contain "{text}"')
def step_error_contains(context, text):
    # Verify the API returned a JSON body with an 'error' field containing
    # the expected substring.
    body = context.last_response.json()
    assert text in body.get("error", "")
    

@then("bridge queue file should have at least {count:d} items")
def step_queue_at_least(context, count):
    assert read_queue_count() >= count, "Queue has fewer items than expected"



@then("bridge queue file should be empty within {seconds:d} seconds")
def step_queue_empty_within(context, seconds):
    ok = wait_until(lambda: read_queue_count() == 0, timeout=seconds)
    assert ok, f"Queue not empty after {seconds}s"