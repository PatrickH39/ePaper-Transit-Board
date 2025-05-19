from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
from datetime import datetime
from time import time
import requests
import os
import re
from collections import defaultdict

# Initialize Flask
app = Flask(__name__)

# Load .env
load_dotenv()

# Globals
cached_data = None
last_fetch_time = 0
FETCH_INTERVAL = 30  # seconds
pst = ZoneInfo("America/Vancouver")

# API Config
API_URL = "https://external.transitapp.com/v3/public/nearby_routes?lat=49.224833&lon=-123.054777&max_distance=1000"
api_key = os.getenv("TRANSIT_API_KEY")
HEADERS = {"apiKey": api_key}

# Filtered target stops + routes
TARGETS = {
    "TSL:72887": ["49", "430"],
    "TSL:72919": ["49", "430"],
    "TSL:72752": ["R4", "41"],
    "TSL:72772": ["R4", "41"],
    "TSL:71932": ["20", "N20"],
    "TSL:72028": ["20", "N20"],
}

@app.route("/")
def home():
    last_updated = datetime.fromtimestamp(last_fetch_time, tz=pst).strftime("%I:%M:%S %p") if last_fetch_time else "Never"
    return render_template("index.html", last_updated=last_updated)

@app.route("/data")
def get_data():
    try:
        global cached_data, last_fetch_time

        now = time()
        if cached_data is None or now - last_fetch_time > FETCH_INTERVAL:
            response = requests.get(API_URL, headers=HEADERS)
            if response.status_code == 200:
                cached_data = response.json()
                last_fetch_time = now
            else:
                return jsonify({"error": "API error"}), 500

        data = cached_data
        routes = data.get("routes", [])
        grouped = defaultdict(list)

        for route in routes:
            short_name = route.get("route_short_name")
            for itinerary in route.get("itineraries", []):
                stop = itinerary.get("closest_stop", {})
                stop_id = stop.get("global_stop_id")

                if stop_id in TARGETS and short_name in TARGETS[stop_id]:
                    direction = itinerary.get("direction_headsign", "Unknown")
                    schedule_items = itinerary.get("schedule_items", [])[:3]

                    for item in schedule_items:
                        departure_ts = item.get("departure_time")
                        if departure_ts:
                            readable_time = datetime.fromtimestamp(departure_ts, tz=pst).strftime("%H:%M")
                        else:
                            readable_time = "-"

                        key = (short_name, stop.get("stop_name"), direction)
                        grouped[key].append({
                            "time": readable_time,
                            "real_time": item.get("is_real_time", False),
                            "cancelled": item.get("is_cancelled", False)
                        })

        output = []
        for (route, stop, direction), times in grouped.items():
            padded_times = times[:3]
            while len(padded_times) < 3:
                padded_times.append({"time": "-", "real_time": False, "cancelled": False})

            output.append({
                "route": route,
                "stop": stop,
                "direction": direction,
                "times": padded_times
            })

        def sort_key(entry):
            match = re.match(r"(\d+)", entry["route"])
            numeric_part = int(match.group(1)) if match else float('inf')
            return (numeric_part, entry["route"], entry["direction"])

        output.sort(key=sort_key)

        return jsonify(output)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0")
