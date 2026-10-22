"""
CoGo Multi-Modal Mobility Platform Server.
High-concurrency standard library server providing REST endpoints & Server-Sent Events (SSE).
"""

import os
import json
import queue
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, Any

from core.config import VEHICLE_CATALOG, DELHI_NCR_PLACES, PROMO_CODES, BOOKING_ADDONS
from core.fare_engine import get_all_estimates, calculate_fare, validate_promo_code
from core.database import init_db, get_trip_history, get_trip_by_id
from core.dispatch_engine import dispatch_engine

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class CoGoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. SSE Real-Time Stream
        if path == "/api/events":
            self._handle_sse_stream()
            return

        # 2. Vehicle Catalog
        if path == "/api/vehicles":
            self._send_json(list(VEHICLE_CATALOG.values()))
            return

        # 3. Searchable Places / Landmarks Autocomplete
        if path == "/api/places":
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get("q", [""])[0].lower()
            if q:
                matched = [
                    p for p in DELHI_NCR_PLACES
                    if q in p["name"].lower() or q in p["address"].lower() or q in p["category"].lower()
                ]
                self._send_json(matched)
            else:
                self._send_json(DELHI_NCR_PLACES)
            return

        # 4. Addons Catalog
        if path == "/api/addons":
            self._send_json(list(BOOKING_ADDONS.values()))
            return

        # 5. Active Drivers Fleet
        if path == "/api/drivers":
            self._send_json(dispatch_engine.get_drivers())
            return

        # 6. Trip History
        if path == "/api/history":
            self._send_json(get_trip_history())
            return

        # 7. Single Trip Lookup
        if path.startswith("/api/rides/"):
            trip_id = path.replace("/api/rides/", "")
            trip = dispatch_engine.get_trip(trip_id) or get_trip_by_id(trip_id)
            if trip:
                self._send_json(trip)
            else:
                self._send_json({"error": "Trip not found"}, 404)
            return

        # Static Assets
        if path == "/" or not path or path == "/index.html":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"

        try:
            body = json.loads(raw_body) if raw_body else {}
        except Exception:
            body = {}

        # 1. Estimate Fare
        if path == "/api/estimate":
            pickup = body.get("pickup", {})
            dropoff = body.get("dropoff", {})
            addons = body.get("addons", [])
            promo_code = body.get("promo_code")
            p_lat, p_lng = pickup.get("lat"), pickup.get("lng")
            d_lat, d_lng = dropoff.get("lat"), dropoff.get("lng")

            if None in (p_lat, p_lng, d_lat, d_lng):
                self._send_json({"error": "Invalid coordinates"}, 400)
                return

            estimates = get_all_estimates(
                pickup_lat=p_lat,
                pickup_lng=p_lng,
                dropoff_lat=d_lat,
                dropoff_lng=d_lng,
                addons=addons,
                promo_code=promo_code
            )
            self._send_json(estimates)
            return

        # 2. Validate Promo Code
        if path == "/api/promos/validate":
            code = body.get("code", "")
            gross_fare = float(body.get("gross_fare", 100.0))
            result = validate_promo_code(code, gross_fare)
            self._send_json(result)
            return

        # 3. Create Ride Request
        if path == "/api/rides":
            pickup = body.get("pickup", {})
            dropoff = body.get("dropoff", {})
            vehicle_id = body.get("vehicle_id", "swift")
            rider_name = body.get("rider_name", "CoGo Rider")
            payment_method = body.get("payment_method", "UPI")
            addons = body.get("addons", [])
            promo_code = body.get("promo_code")
            scheduled_at = body.get("scheduled_at")

            trip = dispatch_engine.create_ride_request(
                rider_name=rider_name,
                pickup_lat=pickup.get("lat"),
                pickup_lng=pickup.get("lng"),
                pickup_address=pickup.get("address", "Pickup Location"),
                dropoff_lat=dropoff.get("lat"),
                dropoff_lng=dropoff.get("lng"),
                dropoff_address=dropoff.get("address", "Dropoff Location"),
                vehicle_id=vehicle_id,
                payment_method=payment_method,
                addons=addons,
                promo_code=promo_code,
                scheduled_at=scheduled_at
            )
            self._send_json(trip, 201)
            return

        # 4. Cancel Ride
        if path.startswith("/api/rides/") and path.endswith("/cancel"):
            trip_id = path.split("/")[3]
            success = dispatch_engine.cancel_trip(trip_id)
            self._send_json({"success": success})
            return

        # 5. Rate & Tip Driver
        if path.startswith("/api/rides/") and path.endswith("/rate"):
            trip_id = path.split("/")[3]
            rating = int(body.get("rating", 5))
            tip = float(body.get("tip", 0.0))
            feedback = body.get("feedback", "")
            dispatch_engine.rate_trip(trip_id, rating, tip, feedback)
            self._send_json({"success": True})
            return

        # 6. Driver Status Toggle
        if path == "/api/driver/toggle-status":
            driver_id = body.get("driver_id", "driver_1")
            new_status = body.get("status", "ONLINE")
            success = dispatch_engine.set_driver_status(driver_id, new_status)
            self._send_json({"success": success, "status": new_status})
            return

        self._send_json({"error": "Endpoint not found"}, 404)

    def _handle_sse_stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        event_queue = queue.Queue(maxsize=100)

        def on_event(event_type: str, data: Any):
            try:
                event_queue.put_nowait({"type": event_type, "data": data})
            except queue.Full:
                pass

        dispatch_engine.subscribe(on_event)

        initial_msg = f"event: init_drivers\ndata: {json.dumps(dispatch_engine.get_drivers())}\n\n"
        try:
            self.wfile.write(initial_msg.encode("utf-8"))
            self.wfile.flush()
        except Exception:
            dispatch_engine.unsubscribe(on_event)
            return

        try:
            while True:
                try:
                    event = event_queue.get(timeout=15.0)
                    msg = f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"
                    self.wfile.write(msg.encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            dispatch_engine.unsubscribe(on_event)

def run():
    init_db()
    server_address = ("127.0.0.1", PORT)
    httpd = ThreadedHTTPServer(server_address, CoGoHandler)
    print("==================================================")
    print("  [+] CoGo Mobility Platform Live")
    print(f"  [+] Server running at: http://localhost:{PORT}")
    print("==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping CoGo server...")
        httpd.server_close()

if __name__ == "__main__":
    run()
