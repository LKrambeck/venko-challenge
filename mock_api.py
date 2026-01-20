from flask import Flask, request, jsonify
import time

app = Flask(__name__)

received_messages = []
simulate_failure = {"down": False}

@app.route("/elevator-data", methods=["POST"])
def receive_data():
    if simulate_failure["down"]:
        return jsonify({"error": "Simulated failure"}), 500

    data = request.json
    if not data or not all(k in data for k in ("position", "door_status", "weight")):
        return jsonify({"error": "Missing fields"}), 400

    if not isinstance(data["position"], int) or not (1 <= data["position"] <= 10):
        return jsonify({"error": "Invalid position"}), 400

    if data["door_status"] not in ["open", "closed"]:
        return jsonify({"error": "Invalid door_status"}), 400

    if not isinstance(data["weight"], int) or not (0 <= data["weight"] <= 1000):
        return jsonify({"error": "Invalid weight"}), 400

    received_messages.append({"data": data, "ts": time.time()})
    return jsonify({"message": "Data received"}), 200

@app.route("/received", methods=["GET"])
def get_received():
    return jsonify(received_messages), 200

@app.route("/simulate_failure", methods=["POST"])
def toggle_failure():
    payload = request.get_json(silent=True) or {}
    simulate_failure["down"] = bool(payload.get("down", False))
    return jsonify({"down": simulate_failure["down"]}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)