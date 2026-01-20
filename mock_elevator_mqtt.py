import time
import json
import paho.mqtt.client as mqtt
import random

BROKER = "localhost"
PORT = 1883
TOPIC_DATA = "elevator/sensor_data"
TOPIC_COMMAND = "elevator/command"
TOPIC_EVENTS = "elevator/events"

elevator_state = {
    "position": 1,
    "door_status": "closed",
    "weight": 0,
    "maintenance_mode": False
}

def publish_error(client, command, error_message):
    payload = json.dumps({
        "type": "error",
        "error": error_message,
        "command": command,
        "ts": time.time()
    })
    client.publish(TOPIC_EVENTS, payload)

def on_message(client, userdata, message):
    command = message.payload.decode()
    if command == "MAINTENANCE_ON":
        elevator_state["maintenance_mode"] = True
        print("Elevator entered maintenance mode.")
    elif command == "MAINTENANCE_OFF":
        elevator_state["maintenance_mode"] = False
        print("Elevator exited maintenance mode.")
    elif command == "OPEN_DOOR":
        elevator_state["door_status"] = "open"
        print("Door opened.")
    elif command == "CLOSE_DOOR":
        elevator_state["door_status"] = "closed"
        print("Door closed.")
    elif command.startswith("MOVE_TO_"):
        if elevator_state.get("maintenance_mode"):
            err = "Elevator is in maintenance mode; MOVE_TO commands are not allowed."
            print(f"Error: {err}")
            publish_error(client, command, err)
            return
        try:
            floor = int(command.split("_")[-1])
            if floor < 1 or floor > 10:
                err = f"The 'MOVE_TO_' command only supports floors between 1 and 10. Command received: {floor}"
                print(f"Error: {err}")
                publish_error(client, command, err)
            else:
                print(f"Moving elevator to floor {floor}.")
                elevator_state["position"] = floor
        except ValueError:
            err = "Invalid floor value in 'MOVE_TO_' command."
            print(f"Error: {err}")
            publish_error(client, command, err)
    else:
        err = "Unknown command received"
        print(err)
        publish_error(client, command, err)

client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, PORT)
client.subscribe(TOPIC_COMMAND)
client.loop_start()

while True:
    elevator_state["weight"] = random.randint(0, 300)
    payload = json.dumps(elevator_state)
    client.publish(TOPIC_DATA, payload)
    print(f"Data sent: {payload}")
    time.sleep(5)