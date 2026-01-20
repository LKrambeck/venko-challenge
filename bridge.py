import json
import time
import os
import threading
import requests
import paho.mqtt.client as mqtt
import logging

BROKER = "localhost"
PORT = 1883
TOPIC_DATA = "elevator/sensor_data"
API_URL = os.getenv("API_URL", "http://localhost:5000/elevator-data")
QUEUE_FILE = os.getenv("QUEUE_FILE", "bridge_queue.jsonl")
FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL", "2.0"))

# basic logging to stdout (captured by environment.py)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [bridge] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

queue_lock = threading.Lock()
queue = []

def load_queue():
    if not os.path.exists(QUEUE_FILE):
        logger.info("Queue file not found: %s (starting empty)", QUEUE_FILE)
        return
    with open(QUEUE_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                queue.append(json.loads(line))
    logger.info("Loaded %d queued items from %s", len(queue), QUEUE_FILE)

def persist_queue():
    with open(QUEUE_FILE, "w") as f:
        for item in queue:
            f.write(json.dumps(item) + "\n")
    logger.info("Persisted %d queued items to %s", len(queue), QUEUE_FILE)

def enqueue(payload):
    with queue_lock:
        queue.append(payload)
        persist_queue()
    logger.warning("Enqueued payload (queue size=%d)", len(queue))

def try_send(payload):
    try:
        resp = requests.post(API_URL, json=payload, timeout=2)
        ok = resp.status_code == 200
        if ok:
            logger.info("Forwarded payload to API (200)")
        else:
            logger.warning("API returned %s", resp.status_code)
        return ok
    except requests.RequestException as e:
        logger.warning("API request failed: %s", e)
        return False

def flush_queue():
    while True:
        time.sleep(FLUSH_INTERVAL)
        with queue_lock:
            if not queue:
                continue
            remaining = []
            for item in queue:
                if not try_send(item):
                    remaining.append(item)
            queue.clear()
            queue.extend(remaining)
            persist_queue()
        logger.info("Flush complete (remaining=%d)", len(queue))

def on_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
    except json.JSONDecodeError:
        logger.warning("Invalid JSON received on %s", message.topic)
        return
    if not try_send(payload):
        enqueue(payload)

def main():
    load_queue()
    t = threading.Thread(target=flush_queue, daemon=True)
    t.start()

    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.subscribe(TOPIC_DATA)
    logger.info("Bridge connected to MQTT %s:%s, subscribed to %s", BROKER, PORT, TOPIC_DATA)
    client.loop_forever()

if __name__ == "__main__":
    logger.info("Starting bridge")
    main()