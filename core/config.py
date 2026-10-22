"""
CoGo Platform Configuration & Real Vehicle Fleet Catalog.
Defines real automotive models, pricing rules, driver fleet, and promotional coupons.
"""

# Real Automotive Catalog across diverse ride categories
VEHICLE_CATALOG = {
    "moto": {
        "id": "moto",
        "name": "CoGo Moto",
        "model": "Honda Activa 6G / Hero Splendor",
        "category": "Bike Taxi",
        "seats": 1,
        "luggage": "1 Backpack",
        "base_fare": 35.0,
        "cost_per_km": 6.5,
        "cost_per_min": 1.2,
        "min_fare": 25.0,
        "icon": "🛵",
        "badge": "Fastest in Traffic",
        "description": "Beat the traffic quickly on a two-wheeler with helmet provided",
        "has_ac": False
    },
    "auto": {
        "id": "auto",
        "name": "CoGo Auto",
        "model": "Bajaj Compact 4S (CNG)",
        "category": "Auto Rickshaw",
        "seats": 3,
        "luggage": "2 Bags",
        "base_fare": 45.0,
        "cost_per_km": 8.5,
        "cost_per_min": 1.8,
        "min_fare": 30.0,
        "icon": "🛺",
        "badge": "Affordable & Direct",
        "description": "Doorstep pickup in iconic 3-wheelers at metered-style low rates",
        "has_ac": False
    },
    "mini": {
        "id": "mini",
        "name": "CoGo Mini",
        "model": "Maruti Suzuki WagonR 1.2L DualJet",
        "category": "Compact Hatchback",
        "seats": 4,
        "luggage": "2 Small Bags",
        "base_fare": 80.0,
        "cost_per_km": 9.5,
        "cost_per_min": 2.0,
        "min_fare": 40.0,
        "icon": "🚗",
        "badge": "Everyday Value",
        "description": "Affordable AC hatchbacks for budget-friendly daily commute",
        "has_ac": True
    },
    "swift": {
        "id": "swift",
        "name": "CoGo Go",
        "model": "Maruti Suzuki Swift ZXi",
        "category": "Premium Hatchback",
        "seats": 4,
        "luggage": "2 Suitcases",
        "base_fare": 90.0,
        "cost_per_km": 11.0,
        "cost_per_min": 2.2,
        "min_fare": 45.0,
        "icon": "🚗",
        "badge": "Most Popular",
        "description": "High-rated drivers in clean, agile hatchbacks",
        "has_ac": True
    },
    "sedan": {
        "id": "sedan",
        "name": "CoGo Sedan",
        "model": "Maruti Suzuki Dzire VXi / Honda Amaze",
        "category": "Sedan",
        "seats": 4,
        "luggage": "3 Large Bags",
        "base_fare": 110.0,
        "cost_per_km": 13.0,
        "cost_per_min": 2.5,
        "min_fare": 50.0,
        "icon": "🚘",
        "badge": "Extra Comfort",
        "description": "Spacious sedans with generous trunk space and legroom",
        "has_ac": True
    },
    "premier": {
        "id": "premier",
        "name": "CoGo Premier",
        "model": "Maruti Suzuki Ciaz Alpha / Hyundai Verna",
        "category": "Executive Sedan",
        "seats": 4,
        "luggage": "3 Large Bags",
        "base_fare": 150.0,
        "cost_per_km": 16.0,
        "cost_per_min": 3.0,
        "min_fare": 70.0,
        "icon": "✨",
        "badge": "Top Rated Captains",
        "description": "Luxury ride with experienced chauffeurs and quiet cabin",
        "has_ac": True
    },
    "xl": {
        "id": "xl",
        "name": "CoGo XL (6-Seater)",
        "model": "Toyota Innova Crysta 2.4 VX",
        "category": "Premium SUV/MUV",
        "seats": 6,
        "luggage": "5 Bags",
        "base_fare": 220.0,
        "cost_per_km": 20.0,
        "cost_per_min": 3.5,
        "min_fare": 100.0,
        "icon": "🚙",
        "badge": "Group & Airport",
        "description": "Roomy 6-seater SUV for family trips, luggage, and team travel",
        "has_ac": True
    },
    "ev": {
        "id": "ev",
        "name": "CoGo Green (EV)",
        "model": "Tata Nexon EV Max / MG ZS EV",
        "category": "Electric SUV",
        "seats": 4,
        "luggage": "3 Bags",
        "base_fare": 120.0,
        "cost_per_km": 13.5,
        "cost_per_min": 2.5,
        "min_fare": 60.0,
        "icon": "⚡",
        "badge": "Zero Emissions",
        "description": "100% Electric eco-friendly rides with whisper-quiet cruising",
        "has_ac": True
    }
}

# Real landmarks and searchable locations in Delhi-NCR
DELHI_NCR_PLACES = [
    {
        "id": "loc_cp",
        "name": "Connaught Place (Inner Circle)",
        "address": "Connaught Place, Block A, Central Delhi, 110001",
        "category": "Shopping & Business Hub",
        "lat": 28.6315,
        "lng": 77.2167
    },
    {
        "id": "loc_ig",
        "name": "India Gate & Kartavya Path",
        "address": "Rajpath, India Gate, New Delhi, 110001",
        "category": "National Landmark",
        "lat": 28.6129,
        "lng": 77.2295
    },
    {
        "id": "loc_igi_t3",
        "name": "Indira Gandhi International Airport (Terminal 3)",
        "address": "Terminal 3 Departures, IGI Airport, New Delhi, 110037",
        "category": "Airport Terminal",
        "lat": 28.5562,
        "lng": 77.1000
    },
    {
        "id": "loc_cyberhub",
        "name": "DLF CyberHub & Cyber City",
        "address": "DLF Phase 2, Sector 24, Gurugram, Haryana 122002",
        "category": "Corporate & Dining Hub",
        "lat": 28.4950,
        "lng": 77.0895
    },
    {
        "id": "loc_aerocity",
        "name": "Worldmark & Aerocity Hospitality District",
        "address": "Asset Area 11, Aerocity, New Delhi, 110037",
        "category": "Business District",
        "lat": 28.5505,
        "lng": 77.1215
    },
    {
        "id": "loc_ndls",
        "name": "New Delhi Railway Station (Ajmeri Gate)",
        "address": "Paharganj / Ajmeri Gate, New Delhi, 110002",
        "category": "Railway Station",
        "lat": 28.6429,
        "lng": 77.2205
    },
    {
        "id": "loc_hauzkhas",
        "name": "Hauz Khas Village & Social",
        "address": "Deer Park, Hauz Khas, New Delhi, 110016",
        "category": "Nightlife & Heritage",
        "lat": 28.5494,
        "lng": 77.1937
    },
    {
        "id": "loc_noida_sec18",
        "name": "Sector 18 Atta Market & Mall of India",
        "address": "Sector 18, Noida, Uttar Pradesh, 201301",
        "category": "Shopping Mall",
        "lat": 28.5700,
        "lng": 77.3200
    }
]

# Active Captains / Drivers Fleet stationed across the city
INITIAL_DRIVERS = [
    {
        "id": "driver_1",
        "name": "Rajesh Sharma",
        "phone": "+91 98765 43210",
        "rating": 4.93,
        "total_trips": 2840,
        "vehicle_id": "swift",
        "plate": "DL 3C CC 4920",
        "lat": 28.6360,
        "lng": 77.2210,
        "status": "ONLINE",
        "avatar": "👨‍✈️"
    },
    {
        "id": "driver_2",
        "name": "Amit Verma",
        "phone": "+91 98111 22334",
        "rating": 4.88,
        "total_trips": 1920,
        "vehicle_id": "mini",
        "plate": "DL 1R CA 8887",
        "lat": 28.6270,
        "lng": 77.2110,
        "status": "ONLINE",
        "avatar": "👨‍💼"
    },
    {
        "id": "driver_3",
        "name": "Suresh Patel",
        "phone": "+91 98222 33445",
        "rating": 4.96,
        "total_trips": 3410,
        "vehicle_id": "sedan",
        "plate": "DL 9C BD 2356",
        "lat": 28.6390,
        "lng": 77.2140,
        "status": "ONLINE",
        "avatar": "🧑‍✈️"
    },
    {
        "id": "driver_4",
        "name": "Vikram Rathore",
        "phone": "+91 98333 44556",
        "rating": 4.98,
        "total_trips": 4150,
        "vehicle_id": "premier",
        "plate": "DL 2C AX 6789",
        "lat": 28.6230,
        "lng": 77.2260,
        "status": "ONLINE",
        "avatar": "🧔"
    },
    {
        "id": "driver_5",
        "name": "Mohammad Aslam",
        "phone": "+91 98444 55667",
        "rating": 4.91,
        "total_trips": 1600,
        "vehicle_id": "auto",
        "plate": "DL 1R AB 9942",
        "lat": 28.6330,
        "lng": 77.2180,
        "status": "ONLINE",
        "avatar": "🛺"
    },
    {
        "id": "driver_6",
        "name": "Priya Nair",
        "phone": "+91 98555 66778",
        "rating": 4.99,
        "total_trips": 1120,
        "vehicle_id": "ev",
        "plate": "DL 8C EV 3310",
        "lat": 28.6290,
        "lng": 77.2230,
        "status": "ONLINE",
        "avatar": "👩‍✈️"
    },
    {
        "id": "driver_7",
        "name": "Gurpreet Singh",
        "phone": "+91 98666 77889",
        "rating": 4.95,
        "total_trips": 5200,
        "vehicle_id": "xl",
        "plate": "HR 26 DQ 7700",
        "lat": 28.6340,
        "lng": 77.2080,
        "status": "ONLINE",
        "avatar": "👳‍♂️"
    },
    {
        "id": "driver_8",
        "name": "Deepak Kumar",
        "phone": "+91 98777 88990",
        "rating": 4.90,
        "total_trips": 890,
        "vehicle_id": "moto",
        "plate": "DL 5S MK 1024",
        "lat": 28.6300,
        "lng": 77.2150,
        "status": "ONLINE",
        "avatar": "🛵"
    }
]

# Promotional Discount Coupons
PROMO_CODES = {
    "COGO50": {
        "code": "COGO50",
        "type": "PERCENT",
        "value": 50,
        "max_discount": 100.0,
        "description": "50% off up to ₹100 on any ride"
    },
    "FIRSTTRIP": {
        "code": "FIRSTTRIP",
        "type": "FLAT",
        "value": 50.0,
        "max_discount": 50.0,
        "description": "Flat ₹50 off on your first CoGo ride"
    },
    "AIRPORT100": {
        "code": "AIRPORT100",
        "type": "FLAT",
        "value": 100.0,
        "max_discount": 100.0,
        "min_fare": 250.0,
        "description": "Flat ₹100 off on rides above ₹250"
    }
}

# Add-on amenities available during booking
BOOKING_ADDONS = {
    "luggage_assist": {
        "id": "luggage_assist",
        "name": "Driver Luggage Assistance",
        "price": 30.0,
        "icon": "🧳"
    },
    "quiet_ride": {
        "id": "quiet_ride",
        "name": "Quiet / Silent Ride",
        "price": 0.0,
        "icon": "🤫"
    },
    "top_rated_driver": {
        "id": "top_rated_driver",
        "name": "Top-Rated Captain Only (★ 4.9+)",
        "price": 25.0,
        "icon": "⭐"
    }
}
