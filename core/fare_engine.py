"""
CoGo Fare Calculation and Estimation Engine.
Handles road distance, ETA, surge pricing, addons, and promotional coupon discounts.
"""

import math
from typing import Dict, Any, List, Optional
from core.config import VEHICLE_CATALOG, PROMO_CODES, BOOKING_ADDONS

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two GPS coordinates in kilometers.
    Applies standard urban routing detour factor (~1.25x) to approximate road distance.
    """
    R = 6371.0  # Earth radius in kilometers
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    straight_line_km = R * c

    # Urban detour multiplier
    road_km = max(round(straight_line_km * 1.25, 2), 0.5)
    return road_km

def estimate_travel_time_minutes(distance_km: float, vehicle_id: str = "swift") -> int:
    """
    Estimates travel duration in minutes based on distance and vehicle type speed.
    Bikes and autos navigate traffic faster than larger SUVs.
    """
    speed_map = {
        "moto": 32.0,
        "auto": 26.0,
        "mini": 24.0,
        "swift": 24.0,
        "sedan": 23.0,
        "premier": 22.0,
        "xl": 20.0,
        "ev": 24.0
    }
    avg_speed = speed_map.get(vehicle_id, 24.0)
    hours = distance_km / avg_speed
    minutes = max(int(round(hours * 60)), 3)
    return minutes

def validate_promo_code(promo_code: str, gross_fare: float) -> Dict[str, Any]:
    """
    Validates a coupon code and calculates the discount amount.
    """
    clean_code = (promo_code or "").strip().upper()
    if not clean_code:
        return {"valid": False, "discount": 0.0, "message": "No code provided"}

    promo = PROMO_CODES.get(clean_code)
    if not promo:
        return {"valid": False, "discount": 0.0, "message": "Invalid coupon code"}

    min_fare = promo.get("min_fare", 0.0)
    if gross_fare < min_fare:
        return {
            "valid": False,
            "discount": 0.0,
            "message": f"Requires minimum fare of ₹{min_fare:.0f}"
        }

    if promo["type"] == "PERCENT":
        discount = (promo["value"] / 100.0) * gross_fare
        discount = min(discount, promo["max_discount"])
    else:  # FLAT
        discount = min(promo["value"], gross_fare)

    discount = round(discount, 2)
    return {
        "valid": True,
        "code": clean_code,
        "discount": discount,
        "description": promo["description"]
    }

def calculate_fare(
    vehicle_id: str,
    distance_km: float,
    duration_min: int,
    surge_multiplier: float = 1.0,
    addons: Optional[List[str]] = None,
    promo_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes complete transparent itemized fare for CoGo rides.
    """
    vehicle = VEHICLE_CATALOG.get(vehicle_id)
    if not vehicle:
        raise ValueError(f"Unknown vehicle category: {vehicle_id}")

    base_fare = vehicle["base_fare"]
    cost_per_km = vehicle["cost_per_km"]
    cost_per_min = vehicle["cost_per_min"]
    min_fare = vehicle["min_fare"]

    distance_fare = round(cost_per_km * distance_km, 2)
    time_fare = round(cost_per_min * duration_min, 2)
    standard_subtotal = base_fare + distance_fare + time_fare

    # Dynamic Surge calculation
    surged_subtotal = round(standard_subtotal * surge_multiplier, 2)
    fare_after_min = max(surged_subtotal, min_fare)

    # Addons calculation
    addons_cost = 0.0
    applied_addons = []
    if addons:
        for addon_id in addons:
            if addon_id in BOOKING_ADDONS:
                ad = BOOKING_ADDONS[addon_id]
                addons_cost += ad["price"]
                applied_addons.append(ad)

    gross_fare = fare_after_min + addons_cost

    # Promo discount calculation
    discount_amount = 0.0
    promo_info = None
    if promo_code:
        promo_res = validate_promo_code(promo_code, gross_fare)
        if promo_res["valid"]:
            discount_amount = promo_res["discount"]
            promo_info = promo_res

    final_fare = max(gross_fare - discount_amount, 20.0)

    return {
        "vehicle_id": vehicle_id,
        "vehicle_name": vehicle["name"],
        "vehicle_model": vehicle["model"],
        "category": vehicle["category"],
        "badge": vehicle.get("badge", ""),
        "seats": vehicle["seats"],
        "luggage": vehicle.get("luggage", ""),
        "icon": vehicle.get("icon", "🚗"),
        "base_fare": base_fare,
        "distance_km": distance_km,
        "cost_per_km": cost_per_km,
        "distance_fare": distance_fare,
        "duration_min": duration_min,
        "cost_per_min": cost_per_min,
        "time_fare": time_fare,
        "surge_multiplier": surge_multiplier,
        "minimum_fare": min_fare,
        "addons_cost": addons_cost,
        "applied_addons": applied_addons,
        "gross_fare": round(gross_fare, 2),
        "discount_amount": discount_amount,
        "promo_info": promo_info,
        "total_fare": round(final_fare, 2),
        "currency": "INR",
        "currency_symbol": "₹"
    }

def get_all_estimates(
    pickup_lat: float,
    pickup_lng: float,
    dropoff_lat: float,
    dropoff_lng: float,
    surge_multiplier: float = 1.0,
    addons: Optional[List[str]] = None,
    promo_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates estimates across all CoGo vehicle tiers.
    """
    distance_km = haversine_distance(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)

    estimates = []
    for vid in VEHICLE_CATALOG.keys():
        duration_min = estimate_travel_time_minutes(distance_km, vid)
        breakdown = calculate_fare(
            vehicle_id=vid,
            distance_km=distance_km,
            duration_min=duration_min,
            surge_multiplier=surge_multiplier,
            addons=addons,
            promo_code=promo_code
        )
        estimates.append(breakdown)

    return {
        "distance_km": distance_km,
        "surge_multiplier": surge_multiplier,
        "promo_code": promo_code,
        "vehicles": estimates
    }
