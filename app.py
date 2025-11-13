# app.py
# Flask backend with REST endpoints and SSE streaming for real-time dashboard
import json
import threading
import time
from queue import Queue, Empty

from flask import Flask, jsonify, Response, request, stream_with_context
from flask_cors import CORS

from config import POLL_INTERVAL, ALERT_THRESHOLD, EVENT_QUEUE_MAX
from sensor import UltrasonicSensor
import storage
from notify import send_alert_for_bin
from route_planner import plan_route
# Optional: from mqtt_client import connect_mqtt, publish_reading

# Setup
app = Flask(__name__, static_folder="frontend", static_url_path="/")
CORS(app)
storage.init_db()

# event queue for SSE listeners
event_queue = Queue(maxsize=EVENT_QUEUE_MAX)

# Setup sensors mapping: bin_code -> sensor instance & metadata
# In practice configure per-bin pins. For demo we map a single BIN with default pins.
# You can add multiple entries here or populate from DB.
SENSORS = {
    # Example: "BIN-001": {"sensor": UltrasonicSensor(trig_pin=23, echo_pin=24), "bin_code":"BIN-001", "height_cm":40}
}

def load_bins_and_setup_sensors():
    # On startup, ensure DB bins exist and initialize SENSORS mapping if desired.
    bins = storage.get_bins()
    if not bins:
        # create a sample bin if none exist
        storage.add_or_update_bin("BIN-001", name="Main Gate Bin", latitude=None, longitude=None, height_cm=40)
        bins = storage.get_bins()
    # Setup default sensors mapping for each bin (use same GPIO pins unless configured)
    for b in bins:
        code = b['bin_code']
        if code not in SENSORS:
            # Use simulator/default pins unless you configure per-bin PINs
            SENSORS[code] = {"sensor": UltrasonicSensor(), "bin_code": code, "height_cm": b.get("height_cm") or 40, "bin_id": b.get("bin_id")}

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/api/bins", methods=["GET"])
def api_get_bins():
    bins = storage.get_bins()
    # attach latest reading if exists
    for b in bins:
        r = storage.get_latest_reading(b['bin_id'])
        b['latest'] = r
    return jsonify(bins)

@app.route("/api/bin/<int:bin_id>/latest", methods=["GET"])
def api_bin_latest(bin_id):
    r = storage.get_latest_reading(bin_id)
    return jsonify(r or {})

@app.route("/api/route", methods=["POST"])
def api_route():
    """
    Expects JSON:
    {
      "start": {"lat": 17.45, "lon": 78.36},
      "bin_ids": [1,2,3],
      "top_n": 10
    }
    """
    payload = request.get_json() or {}
    start = payload.get("start")
    bin_ids = payload.get("bin_ids")
    top_n = payload.get("top_n")
    if not start or not bin_ids:
        return jsonify({"error":"start and bin_ids required"}), 400
    bins = []
    for bid in bin_ids:
        b = storage.get_bin(bid)
        if b:
            latest = storage.get_latest_reading(b['bin_id'])
            bins.append({
                "bin_id": b['bin_id'],
                "bin_code": b['bin_code'],
                "latitude": b.get('latitude'),
                "longitude": b.get('longitude'),
                "fill_percent": latest['fill_percent'] if latest else 0
            })
    route = plan_route((start['lat'], start['lon']), bins, top_n=top_n)
    return jsonify({"route": route})

@app.route("/api/simulate/<bin_code>/<float:level>", methods=["POST"])
def api_simulate(bin_code, level):
    # Manual simulate: insert reading for bin_code (find bin_id)
    bins = storage.get_bins()
    bin_row = next((b for b in bins if b['bin_code']==bin_code), None)
    if not bin_row:
        return jsonify({"error":"bin not found"}), 404
    storage.insert_reading(bin_row['bin_id'], float(level), distance_cm=0.0)
    event = {"type":"update","bin_code":bin_code,"bin_id":bin_row['bin_id'],"level":float(level),"timestamp":int(time.time())}
    try:
        event_queue.put_nowait(event)
    except:
        pass
    return jsonify({"ok":True})

@app.route("/stream")
def stream():
    def sse_format(d: dict):
        return f"data: {json.dumps(d)}\n\n"

    def event_stream():
        # initial snapshot
        bins = storage.get_bins()
        snapshot = {"type":"snapshot","bins":bins}
        yield sse_format(snapshot)
        while True:
            try:
                evt = event_queue.get(timeout=15)
                yield sse_format(evt)
            except Empty:
                # send ping to keep connection alive
                yield ":\n\n"
            except GeneratorExit:
                break

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")

def sensor_poller():
    """Background thread to poll all sensors periodically and emit events."""
    while True:
        for code, meta in list(SENSORS.items()):
            try:
                sensor = meta["sensor"]
                height = meta.get("height_cm", 40)
                distance = sensor.get_distance_cm()
                fill = sensor.get_fill_level_percent(height)
                bin_id = meta.get("bin_id")
                storage.insert_reading(bin_id, fill, distance)

                evt = {"type":"update","bin_code":code,"bin_id":bin_id,"level":fill,"distance_cm":distance,"timestamp":int(time.time())}
                try:
                    event_queue.put_nowait(evt)
                except:
                    pass

                # optionally publish to MQTT (uncomment if using mqtt_client)
                # mqtt_client.publish_reading(mqtt, code, evt)

                # alerting
                if fill >= ALERT_THRESHOLD:
                    # log and send notification once per reading (or implement dedupe)
                    storage.log_alert(bin_id, "BIN_FULL", f"Bin {code} at {fill}%")
                    send_alert_for_bin({"bin_code": code, "name": meta.get("bin_code")}, fill)

            except Exception as e:
                app.logger.exception(f"Error polling sensor {code}: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    # initialize bins + sensors
    load_bins_and_setup_sensors()

    # start background poller thread
    poller = threading.Thread(target=sensor_poller, daemon=True)
    poller.start()

    app.run(host="0.0.0.0", port=5000, debug=True)
