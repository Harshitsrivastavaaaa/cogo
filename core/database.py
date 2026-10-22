"""
Database persistence layer for CoGo using SQLite.
Stores trips, payments, promo codes, driver tips, and ratings.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cogo_platform.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id TEXT PRIMARY KEY,
                rider_name TEXT,
                driver_id TEXT,
                driver_name TEXT,
                driver_avatar TEXT,
                vehicle_id TEXT,
                vehicle_name TEXT,
                vehicle_model TEXT,
                license_plate TEXT,
                pickup_address TEXT,
                pickup_lat REAL,
                pickup_lng REAL,
                dropoff_address TEXT,
                dropoff_lat REAL,
                dropoff_lng REAL,
                distance_km REAL,
                duration_min INTEGER,
                fare REAL,
                gross_fare REAL,
                discount_amount REAL,
                promo_code TEXT,
                payment_method TEXT,
                payment_status TEXT,
                addons_json TEXT,
                scheduled_at TEXT,
                tip_amount REAL,
                currency TEXT,
                status TEXT,
                otp TEXT,
                created_at TEXT,
                completed_at TEXT,
                rating INTEGER,
                feedback TEXT
            )
        """)
        conn.commit()

def save_trip(trip: Dict[str, Any]) -> str:
    with get_connection() as conn:
        cursor = conn.cursor()
        addons_str = json.dumps(trip.get("addons", []))
        cursor.execute("""
            INSERT OR REPLACE INTO trips (
                id, rider_name, driver_id, driver_name, driver_avatar, vehicle_id,
                vehicle_name, vehicle_model, license_plate, pickup_address, pickup_lat,
                pickup_lng, dropoff_address, dropoff_lat, dropoff_lng, distance_km,
                duration_min, fare, gross_fare, discount_amount, promo_code,
                payment_method, payment_status, addons_json, scheduled_at, tip_amount,
                currency, status, otp, created_at, completed_at, rating, feedback
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trip.get("id"),
            trip.get("rider_name", "Passenger"),
            trip.get("driver_id"),
            trip.get("driver_name"),
            trip.get("driver_avatar", "👨‍✈️"),
            trip.get("vehicle_id"),
            trip.get("vehicle_name"),
            trip.get("vehicle_model"),
            trip.get("license_plate"),
            trip.get("pickup_address", "Pickup Location"),
            trip.get("pickup_lat"),
            trip.get("pickup_lng"),
            trip.get("dropoff_address", "Dropoff Location"),
            trip.get("dropoff_lat"),
            trip.get("dropoff_lng"),
            trip.get("distance_km"),
            trip.get("duration_min"),
            trip.get("fare"),
            trip.get("gross_fare", trip.get("fare")),
            trip.get("discount_amount", 0.0),
            trip.get("promo_code"),
            trip.get("payment_method", "UPI"),
            trip.get("payment_status", "PAID"),
            addons_str,
            trip.get("scheduled_at"),
            trip.get("tip_amount", 0.0),
            trip.get("currency", "₹"),
            trip.get("status", "REQUESTED"),
            trip.get("otp"),
            trip.get("created_at", datetime.now().isoformat()),
            trip.get("completed_at"),
            trip.get("rating"),
            trip.get("feedback")
        ))
        conn.commit()
    return trip["id"]

def update_trip_status(trip_id: str, status: str, completed_at: Optional[str] = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if completed_at:
            cursor.execute("UPDATE trips SET status = ?, completed_at = ? WHERE id = ?", (status, completed_at, trip_id))
        else:
            cursor.execute("UPDATE trips SET status = ? WHERE id = ?", (status, trip_id))
        conn.commit()

def record_trip_rating(trip_id: str, rating: int, tip: float = 0.0, feedback: str = ""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE trips
            SET rating = ?, tip_amount = ?, feedback = ?
            WHERE id = ?
        """, (rating, tip, feedback, trip_id))
        conn.commit()

def get_trip_history(limit: int = 30) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trips ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("addons_json"):
                try:
                    d["addons"] = json.loads(d["addons_json"])
                except Exception:
                    d["addons"] = []
            result.append(d)
        return result

def get_trip_by_id(trip_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("addons_json"):
            try:
                d["addons"] = json.loads(d["addons_json"])
            except Exception:
                d["addons"] = []
        return d
