from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import uuid

app = Flask(__name__)

def get_db():
    return psycopg2.connect(
        os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/telemetry'),
        cursor_factory=RealDictCursor
    )

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/api/v1/sensors/<sensor_id>', methods=['GET'])
def get_sensor(sensor_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM telemetry_data WHERE sensor_id = %s ORDER BY timestamp DESC LIMIT 1",
        (sensor_id,)
    )
    latest = cur.fetchone()
    conn.close()
    
    if latest:
        return jsonify({
            "id": sensor_id,
            "type": "TEMPERATURE",
            "value": latest['value'],
            "status": latest['status'] or 'active'
        })
    return jsonify({"id": sensor_id, "type": "TEMPERATURE", "value": 0, "status": "inactive"})

@app.route('/api/v1/sensors/<sensor_id>/telemetry', methods=['GET'])
def get_telemetry(sensor_id):
    from_time = request.args.get('from')
    to_time = request.args.get('to')
    
    conn = get_db()
    cur = conn.cursor()
    
    if from_time and to_time:
        cur.execute(
            "SELECT * FROM telemetry_data WHERE sensor_id = %s AND timestamp BETWEEN %s AND %s ORDER BY timestamp DESC",
            (sensor_id, from_time, to_time)
        )
    else:
        cur.execute(
            "SELECT * FROM telemetry_data WHERE sensor_id = %s ORDER BY timestamp DESC LIMIT 100",
            (sensor_id,)
        )
    
    data = cur.fetchall()
    conn.close()
    
    return jsonify({
        "sensorId": sensor_id,
        "data": [dict(row) for row in data]
    })

@app.route('/api/v1/telemetry', methods=['POST'])
def save_telemetry():
    data = request.json
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO telemetry_data (id, sensor_id, value, unit, timestamp, status, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (str(uuid.uuid4()), data['sensorId'], data['value'], data.get('unit', '°C'),
         data.get('timestamp', datetime.now()), data.get('status', 'active'), datetime.now())
    )
    
    if data['value'] > 30:
        cur.execute(
            """INSERT INTO alerts (id, sensor_id, type, severity, message, created_at, resolved)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (str(uuid.uuid4()), data['sensorId'], 'HIGH_TEMPERATURE', 'WARNING',
             f"Temperature {data['value']}°C exceeds 30°C", datetime.now(), False)
        )
    
    conn.commit()
    conn.close()
    
    return jsonify({"status": "saved"}), 201

@app.route('/api/v1/alerts', methods=['GET'])
def get_alerts():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts WHERE resolved = false ORDER BY created_at DESC LIMIT 50")
    alerts = cur.fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in alerts])

if __name__ == '__main__':
    import time
    time.sleep(5)
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8082)), debug=True)
