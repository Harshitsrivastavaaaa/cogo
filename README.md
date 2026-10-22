# 🚗 CoGo Mobility — Smarter, Faster Urban Mobility

**CoGo** is a full-featured, real-time ride-hailing and urban mobility platform. Built with a multi-threaded Python backend and an interactive web application, it brings a production-grade ride-hailing experience with real automotive fleets, geospatial routing, live cab telemetry, and safety tools.

---

## ⚡ What Makes CoGo Special

### 🚘 Real Automotive Fleet & Diverse Ride Tiers
Choose from 8 distinct, real-world mobility tiers tailored for Indian urban transit:

| Tier | Real Vehicle Model | Category | Base Fare | Km Rate | Minute Rate | Capacity & Features |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **🛵 CoGo Moto** | Honda Activa 6G / Hero Splendor | Bike Taxi | ₹35 | ₹6.5/km | ₹1.2/min | 1 Rider, Helmet included, fastest in traffic |
| **🛺 CoGo Auto** | Bajaj Compact 4S (CNG) | Auto Rickshaw | ₹45 | ₹8.5/km | ₹1.8/min | 3 Seats, doorstep pickup, metered value |
| **🚗 CoGo Mini** | Maruti Suzuki WagonR 1.2L DualJet | Compact Hatchback | ₹80 | ₹9.5/km | ₹2.0/min | 4 Seats, AC, affordable daily commute |
| **🚗 CoGo Go** | Maruti Suzuki Swift ZXi | Premium Hatchback | ₹90 | ₹11.0/km | ₹2.2/min | 4 Seats, AC, highly popular & agile |
| **🚘 CoGo Sedan** | Maruti Suzuki Dzire VXi / Honda Amaze | Comfort Sedan | ₹110 | ₹13.0/km | ₹2.5/min | 4 Seats, AC, 3 large suitcases trunk space |
| **✨ CoGo Premier** | Maruti Suzuki Ciaz Alpha / Hyundai Verna | Executive Sedan | ₹150 | ₹16.0/km | ₹3.0/min | 4 Seats, luxury cabin, top-rated captains |
| **🚙 CoGo XL** | Toyota Innova Crysta 2.4 / Ertiga | Premium 6-Seater SUV | ₹220 | ₹20.0/km | ₹3.5/min | 6 Seats, family trips, airport & heavy luggage |
| **⚡ CoGo Green (EV)**| Tata Nexon EV Max / MG ZS EV | Electric SUV | ₹120 | ₹13.5/km | ₹2.5/min | 4 Seats, 100% Electric, silent zero emissions |

---

### 🌟 Features & Addons

1. **📍 Place Autocomplete & Interactive Geospatial Map**:
   - Integrated with Leaflet & CartoDB maps.
   - Live autocomplete for major Delhi-NCR landmarks (IGI Airport Terminal 3, Connaught Place, DLF CyberHub, Hauz Khas, Aerocity, New Delhi Railway Station, Sector 18 Noida).
   - Tap directly on the map to set custom pickup and destination pins.

2. **🏷️ Coupon Codes & Discounts**:
   - `COGO50`: 50% discount up to ₹100.
   - `FIRSTTRIP`: Flat ₹50 discount on your first booking.
   - `AIRPORT100`: Flat ₹100 off on long rides (above ₹250).

3. **🧳 Trip Addons & Preferences**:
   - **Driver Luggage Assistance**: Captain assists with heavy baggage (+₹30).
   - **Quiet / Silent Ride**: Request a conversation-free, peaceful ride (Free).
   - **Top-Rated Captain Only**: Automatically pair only with ★ 4.9+ drivers (+₹25).

4. **💳 Multiple Payment Options**:
   - **UPI / QR**: Google Pay, PhonePe, Paytm, BHIM.
   - **CoGo Wallet**: Instant one-tap checkout with loaded balance.
   - **Cash to Captain**: Traditional cash-on-trip option.

5. **📅 Reserve for Later**:
   - Toggle between **Ride Now** and **Reserve for Later** with a date-time picker.

6. **🚨 Comprehensive Safety Hub**:
   - One-tap emergency dialog with one-click dialer:
     - **112**: National Police Emergency
     - **1091**: Women Safety Helpline
     - **102**: Medical Ambulance
   - Real-time GPS coordinate display.
   - Shareable live tracking link to send to family and friends.

7. **🔒 4-Digit Ride Start OTP**:
   - Prevents boarding the wrong vehicle and confirms passenger authentication.

8. **🚖 Captain Console (Driver Mode)**:
   - Online/Offline duty toggle switch.
   - Live incoming ride request alerts with countdown and audio chimes.
   - Accept/Decline trips and collect fares.
   - Daily earnings tracker and trip counters.

9. **💾 Persistent SQLite Storage (`cogo_platform.db`)**:
   - Every trip, route, payment status, rating, tip, and feedback note is permanently saved.

---

## 🚀 How to Run CoGo

CoGo runs completely on **Python Standard Library** (Python 3.10+) with **zero external dependencies**:

```bash
# Start the CoGo Mobility server
python app.py
```

Open your browser and navigate to:
```
http://localhost:8000
```
