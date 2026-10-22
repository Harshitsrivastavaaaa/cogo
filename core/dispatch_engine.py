"""
CoGo Real-Time Dispatch and Matching Engine.
Handles active driver fleet, trip lifecycle state machine, and interactive driver responses.
"""

import time
import math
import random
import uuid
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.config import INITIAL_DRIVERS, VEHICLE_CATALOG
from core.fare_engine import haversine_distance, calculate_fare, estimate_travel_time_minutes
from core.database import save_trip, update_trip_status, record_trip_rating

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes compass heading in degrees from point 1 to point 2 for realistic car rotation.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    y = math.sin(dlambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360

class DispatchEngine:
    def __init__(self):
        self.lock = threading.Lock()
        self.drivers: Dict[str, Dict[str, Any]] = {}
        for d in INITIAL_DRIVERS:
            self.drivers[d["id"]] = d.copy()

        self.active_trips: Dict[str, Dict[str, Any]] = {}
        self.pending_offers: Dict[str, Dict[str, Any]] = {}
        self.subscribers: List[Any] = []
        self.auto_pilot_enabled = True

    def get_drivers(self) -> List[Dict[str, Any]]:
        with self.lock:
            driver_list = []
            for d in self.drivers.values():
                d_copy = d.copy()
                veh = VEHICLE_CATALOG.get(d["vehicle_id"], {})
                d_copy["vehicle_name"] = veh.get("name", "CoGo Ride")
                d_copy["vehicle_model"] = veh.get("model", "Car")
                d_copy["category"] = veh.get("category", "Standard")
                d_copy["icon"] = veh.get("icon", "🚗")
                driver_list.append(d_copy)
            return driver_list

    def set_driver_status(self, driver_id: str, status: str) -> bool:
        with self.lock:
            driver = self.drivers.get(driver_id)
            if driver:
                driver["status"] = status
                self._notify_subscribers("driver_status_changed", {"driver_id": driver_id, "status": status})
                return True
            return False

    def find_nearest_driver(self, pickup_lat: float, pickup_lng: float, vehicle_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with self.lock:
            # 1. Exact vehicle category match
            matching_online = [
                d for d in self.drivers.values()
                if d["status"] == "ONLINE" and d["vehicle_id"] == vehicle_id
            ]

            # 2. If no exact category match is online, fallback to any available driver
            candidates = matching_online if matching_online else [
                d for d in self.drivers.values() if d["status"] == "ONLINE"
            ]

            if not candidates:
                return None

            best_driver = None
            min_dist = float("inf")
            for d in candidates:
                dist = haversine_distance(pickup_lat, pickup_lng, d["lat"], d["lng"])
                if dist < min_dist:
                    min_dist = dist
                    best_driver = d

            return best_driver

    def create_ride_request(
        self,
        rider_name: str,
        pickup_lat: float,
        pickup_lng: float,
        pickup_address: str,
        dropoff_lat: float,
        dropoff_lng: float,
        dropoff_address: str,
        vehicle_id: str,
        payment_method: str = "UPI",
        addons: Optional[List[str]] = None,
        promo_code: Optional[str] = None,
        scheduled_at: Optional[str] = None
    ) -> Dict[str, Any]:
        with self.lock:
            trip_id = f"cogo_{uuid.uuid4().hex[:8]}"
            distance_km = haversine_distance(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)
            duration_min = estimate_travel_time_minutes(distance_km, vehicle_id)
            fare_breakdown = calculate_fare(
                vehicle_id=vehicle_id,
                distance_km=distance_km,
                duration_min=duration_min,
                addons=addons,
                promo_code=promo_code
            )

            otp = str(random.randint(1000, 9999))
            trip = {
                "id": trip_id,
                "rider_name": rider_name or "Rider",
                "driver_id": None,
                "driver_name": None,
                "driver_avatar": "👨‍✈️",
                "driver_phone": None,
                "driver_rating": 4.9,
                "vehicle_id": vehicle_id,
                "vehicle_name": fare_breakdown["vehicle_name"],
                "vehicle_model": fare_breakdown["vehicle_model"],
                "license_plate": "Pending Match",
                "pickup_address": pickup_address or "Selected on Map",
                "pickup_lat": pickup_lat,
                "pickup_lng": pickup_lng,
                "dropoff_address": dropoff_address or "Destination",
                "dropoff_lat": dropoff_lat,
                "dropoff_lng": dropoff_lng,
                "distance_km": distance_km,
                "duration_min": duration_min,
                "fare": fare_breakdown["total_fare"],
                "gross_fare": fare_breakdown["gross_fare"],
                "discount_amount": fare_breakdown["discount_amount"],
                "promo_code": promo_code,
                "payment_method": payment_method,
                "payment_status": "PAID" if payment_method != "CASH" else "CASH_PENDING",
                "addons": addons or [],
                "scheduled_at": scheduled_at,
                "currency": "₹",
                "status": "SEARCHING",
                "otp": otp,
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
                "driver_lat": None,
                "driver_lng": None,
                "heading": 0.0,
                "progress": 0
            }

            self.active_trips[trip_id] = trip
            save_trip(trip)
            self._notify_subscribers("trip_created", trip)

        # Trigger automatic search and assignment
        threading.Thread(target=self._dispatch_lifecycle, args=(trip_id,), daemon=True).start()
        return trip

    def _dispatch_lifecycle(self, trip_id: str):
        time.sleep(1.2)
        with self.lock:
            trip = self.active_trips.get(trip_id)
            if not trip or trip["status"] == "CANCELLED":
                return

            driver = self.find_nearest_driver(trip["pickup_lat"], trip["pickup_lng"], trip["vehicle_id"])
            if not driver:
                trip["status"] = "NO_DRIVERS_FOUND"
                self._notify_subscribers("trip_update", trip)
                return

            # Offer to driver
            driver["status"] = "BUSY"
            trip["driver_id"] = driver["id"]
            trip["driver_name"] = driver["name"]
            trip["driver_avatar"] = driver.get("avatar", "👨‍✈️")
            trip["driver_phone"] = driver["phone"]
            trip["driver_rating"] = driver["rating"]
            trip["license_plate"] = driver.get("plate", "DL 01 AB 1234")
            trip["driver_lat"] = driver["lat"]
            trip["driver_lng"] = driver["lng"]
            trip["status"] = "ACCEPTED"

            update_trip_status(trip_id, "ACCEPTED")
            self._notify_subscribers("trip_update", trip)

        # Phase 1: Driver approaches Pickup location
        start_lat, start_lng = trip["driver_lat"], trip["driver_lng"]
        dest_lat, dest_lng = trip["pickup_lat"], trip["pickup_lng"]
        heading = calculate_bearing(start_lat, start_lng, dest_lat, dest_lng)
        steps = 9

        for i in range(1, steps + 1):
            time.sleep(1.0)
            with self.lock:
                if trip.get("status") == "CANCELLED":
                    driver["status"] = "ONLINE"
                    return
                ratio = i / steps
                current_lat = start_lat + (dest_lat - start_lat) * ratio
                current_lng = start_lng + (dest_lng - start_lng) * ratio
                driver["lat"] = current_lat
                driver["lng"] = current_lng
                trip["driver_lat"] = current_lat
                trip["driver_lng"] = current_lng
                trip["heading"] = heading
                trip["progress"] = int(ratio * 50)
                self._notify_subscribers("driver_moved", {
                    "driver_id": driver["id"],
                    "trip_id": trip_id,
                    "lat": current_lat,
                    "lng": current_lng,
                    "heading": heading,
                    "progress": trip["progress"],
                    "status": "ACCEPTED"
                })

        # Phase 2: Driver Arrived at Pickup
        with self.lock:
            trip["status"] = "ARRIVED"
            update_trip_status(trip_id, "ARRIVED")
            self._notify_subscribers("trip_update", trip)

        time.sleep(2.0)  # Waiting for rider boarding & OTP verification

        # Phase 3: In Trip (Pickup -> Dropoff)
        with self.lock:
            trip["status"] = "IN_PROGRESS"
            update_trip_status(trip_id, "IN_PROGRESS")
            self._notify_subscribers("trip_update", trip)

        trip_start_lat, trip_start_lng = trip["pickup_lat"], trip["pickup_lng"]
        trip_end_lat, trip_end_lng = trip["dropoff_lat"], trip["dropoff_lng"]
        trip_heading = calculate_bearing(trip_start_lat, trip_start_lng, trip_end_lat, trip_end_lng)
        trip_steps = 14

        for i in range(1, trip_steps + 1):
            time.sleep(1.0)
            with self.lock:
                if trip.get("status") == "CANCELLED":
                    driver["status"] = "ONLINE"
                    return
                ratio = i / trip_steps
                current_lat = trip_start_lat + (trip_end_lat - trip_start_lat) * ratio
                current_lng = trip_start_lng + (trip_end_lng - trip_start_lng) * ratio
                driver["lat"] = current_lat
                driver["lng"] = current_lng
                trip["driver_lat"] = current_lat
                trip["driver_lng"] = current_lng
                trip["heading"] = trip_heading
                trip["progress"] = 50 + int(ratio * 50)
                self._notify_subscribers("driver_moved", {
                    "driver_id": driver["id"],
                    "trip_id": trip_id,
                    "lat": current_lat,
                    "lng": current_lng,
                    "heading": trip_heading,
                    "progress": trip["progress"],
                    "status": "IN_PROGRESS"
                })

        # Phase 4: Trip Completed
        with self.lock:
            now_iso = datetime.now().isoformat()
            trip["status"] = "COMPLETED"
            trip["completed_at"] = now_iso
            trip["progress"] = 100
            trip["payment_status"] = "PAID"
            driver["status"] = "ONLINE"
            driver["total_trips"] += 1
            update_trip_status(trip_id, "COMPLETED", completed_at=now_iso)
            self._notify_subscribers("trip_update", trip)

    def cancel_trip(self, trip_id: str) -> bool:
        with self.lock:
            trip = self.active_trips.get(trip_id)
            if not trip:
                return False
            trip["status"] = "CANCELLED"
            if trip.get("driver_id"):
                driver = self.drivers.get(trip["driver_id"])
                if driver:
                    driver["status"] = "ONLINE"
            update_trip_status(trip_id, "CANCELLED")
            self._notify_subscribers("trip_update", trip)
            return True

    def get_trip(self, trip_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            return self.active_trips.get(trip_id)

    def rate_trip(self, trip_id: str, rating: int, tip: float = 0.0, feedback: str = ""):
        record_trip_rating(trip_id, rating, tip, feedback)

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def unsubscribe(self, callback):
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    def _notify_subscribers(self, event_type: str, data: Any):
        dead = []
        for sub in self.subscribers:
            try:
                sub(event_type, data)
            except Exception:
                dead.append(sub)
        for d in dead:
            self.unsubscribe(d)

dispatch_engine = DispatchEngine()
