from flask import Flask, request, jsonify
import random
from datetime import datetime, timezone

app = Flask(__name__)

LOCATION_TO_SENSOR = {
    "Living Room": "1",
    "Bedroom": "2",
    "Kitchen": "3",
}

SENSOR_TO_LOCATION = {v: k for k, v in LOCATION_TO_SENSOR.items()}


@app.route('/temperature', methods=['GET'])
def get_temperature():
    location = request.args.get('location', '')
    sensor_id = request.args.get('sensor_id', '')
    
    if location == "":
        if sensor_id in SENSOR_TO_LOCATION:
            location = SENSOR_TO_LOCATION[sensor_id]
        else:
            location = "Unknown"
    
    if sensor_id == "":
        if location in LOCATION_TO_SENSOR:
            sensor_id = LOCATION_TO_SENSOR[location]
        else:
            sensor_id = "0"
    
    temperature = round(random.uniform(15, 30), 2)
    
    return jsonify({
        "value": temperature,
        "unit": "°C",
        "location": location,
        "sensor_id": sensor_id,
        "sensor_type": "temperature",
        "status": "active",
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "description": f"Temperature in {location}"
    })


@app.route('/temperature/<sensor_id>', methods=['GET'])
def get_temperature_by_id(sensor_id):
    location = SENSOR_TO_LOCATION.get(sensor_id, "Unknown")
    temperature = round(random.uniform(15, 30), 2)
    
    return jsonify({
        "value": temperature,
        "unit": "°C",
        "location": location,
        "sensor_id": sensor_id,
        "sensor_type": "temperature",
        "status": "active",
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "description": f"Temperature in {location}"
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)
