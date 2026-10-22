/**
 * CoGo Urban Mobility Platform Controller
 * Handles Leaflet mapping, live SSE telemetry, place autocompletion,
 * fare calculations, dynamic coupons, audio cues, and driver interactions.
 */

const state = {
  map: null,
  pickup: null,          // { lat, lng, address }
  dropoff: null,         // { lat, lng, address }
  pickupMarker: null,
  dropoffMarker: null,
  routePolyline: null,
  driverMarkers: {},     // driver_id -> Leaflet Marker
  pickingTarget: null,   // 'pickup' | 'dropoff' | null
  vehicles: [],
  selectedVehicleId: 'swift',
  currentEstimates: null,
  activeTrip: null,
  eventSource: null,
  appliedPromo: null,
  selectedAddons: [],
  paymentMethod: 'UPI',
  isScheduled: false,
  scheduledTime: null,
  captainDutyOnline: true,
  selectedTip: 0,
  selectedRating: 5
};

// Preset Landmarks in Delhi-NCR
const PRESETS = {
  cp: { lat: 28.6315, lng: 77.2167, name: "Connaught Place, Central Delhi" },
  india_gate: { lat: 28.6129, lng: 77.2295, name: "India Gate, Kartavya Path" },
  t3: { lat: 28.5562, lng: 77.1000, name: "IGI Airport Terminal 3" },
  cyberhub: { lat: 28.4950, lng: 77.0895, name: "DLF CyberHub, Gurugram" }
};

// Web Audio API Synth Chimes
class SoundEffects {
  constructor() {
    this.ctx = null;
  }
  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
  }
  playMatchChime() {
    this.init();
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(523.25, now); // C5
    osc.frequency.exponentialRampToValueAtTime(659.25, now + 0.15); // E5
    osc.frequency.exponentialRampToValueAtTime(783.99, now + 0.3); // G5
    gain.gain.setValueAtTime(0.12, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.5);
  }
  playArrivalChime() {
    this.init();
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(440, now);
    osc.frequency.setValueAtTime(880, now + 0.2);
    gain.gain.setValueAtTime(0.15, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(now);
    osc.stop(now + 0.6);
  }
}
const sound = new SoundEffects();

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  initMap();
  loadVehicles();
  setupAutocomplete('input-pickup', 'pickup-autocomplete', 'pickup');
  setupAutocomplete('input-dropoff', 'dropoff-autocomplete', 'dropoff');
  setupEventListeners();
  connectSSE();

  // Set default initial trip to Connaught Place -> India Gate
  setTimeout(() => {
    setPresetLocation('cp_to_ig');
  }, 500);
});

/* ==========================================================================
   Map & Geospatial Layer
   ========================================================================== */
function initMap() {
  const defaultCenter = [28.6315, 77.2167]; // New Delhi
  state.map = L.map('map', { zoomControl: false }).setView(defaultCenter, 13);

  // Sleek CartoDB Voyager Map Tiles
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    maxZoom: 19
  }).addTo(state.map);

  L.control.zoom({ position: 'bottomright' }).addTo(state.map);

  state.map.on('click', (e) => {
    handleMapClick(e.latlng);
  });
}

function handleMapClick(latlng) {
  if (state.pickingTarget === 'pickup') {
    setPickupLocation(latlng.lat, latlng.lng, `Pinned (${latlng.lat.toFixed(4)}, ${latlng.lng.toFixed(4)})`);
    stopPicking();
  } else if (state.pickingTarget === 'dropoff') {
    setDropoffLocation(latlng.lat, latlng.lng, `Pinned (${latlng.lat.toFixed(4)}, ${latlng.lng.toFixed(4)})`);
    stopPicking();
  } else if (!state.pickup) {
    setPickupLocation(latlng.lat, latlng.lng, `Pickup (${latlng.lat.toFixed(4)}, ${latlng.lng.toFixed(4)})`);
    showToast("📍 Now tap on the map to set your Destination");
    state.pickingTarget = 'dropoff';
    updatePickerUI();
  } else if (!state.dropoff) {
    setDropoffLocation(latlng.lat, latlng.lng, `Destination (${latlng.lat.toFixed(4)}, ${latlng.lng.toFixed(4)})`);
    stopPicking();
  }
}

function setPickupLocation(lat, lng, address) {
  state.pickup = { lat, lng, address };
  document.getElementById('input-pickup').value = address;

  if (state.pickupMarker) {
    state.pickupMarker.setLatLng([lat, lng]);
  } else {
    const icon = L.divIcon({
      className: 'cogo-pin-pickup',
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    });
    state.pickupMarker = L.marker([lat, lng], { icon }).addTo(state.map);
  }
  updateRoute();
}

function setDropoffLocation(lat, lng, address) {
  state.dropoff = { lat, lng, address };
  document.getElementById('input-dropoff').value = address;

  if (state.dropoffMarker) {
    state.dropoffMarker.setLatLng([lat, lng]);
  } else {
    const icon = L.divIcon({
      className: 'cogo-pin-dropoff',
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    });
    state.dropoffMarker = L.marker([lat, lng], { icon }).addTo(state.map);
  }
  updateRoute();
}

/* ==========================================================================
   OSRM Real Road Routing Engine (100% Free & No API Key Required)
   ========================================================================== */
async function fetchOSRMRoute(startLat, startLng, endLat, endLng) {
  try {
    const url = `https://router.project-osrm.org/route/v1/driving/${startLng},${startLat};${endLng},${endLat}?overview=full&geometries=geojson`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("OSRM response not ok");
    const data = await res.json();
    if (data.routes && data.routes.length > 0) {
      const route = data.routes[0];
      const latlngs = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);
      const distanceKm = Math.round((route.distance / 1000) * 10) / 10;
      const durationMin = Math.max(Math.round(route.duration / 60), 3);
      return { latlngs, distanceKm, durationMin };
    }
  } catch (err) {
    console.warn("OSRM routing unavailable, using road detour factor:", err);
  }
  return null;
}

async function updateRoute() {
  if (!state.pickup || !state.dropoff) return;

  const directPoints = [
    [state.pickup.lat, state.pickup.lng],
    [state.dropoff.lat, state.dropoff.lng]
  ];

  // Draw initial path
  if (state.routePolyline) {
    state.routePolyline.setLatLngs(directPoints);
    state.routePolyline.setStyle({ color: '#0d1117', weight: 4, dashArray: '6, 6' });
  } else {
    state.routePolyline = L.polyline(directPoints, {
      color: '#0d1117',
      weight: 4,
      dashArray: '6, 6',
      opacity: 0.85
    }).addTo(state.map);
  }

  state.map.fitBounds(L.latLngBounds(directPoints), { padding: [70, 70] });

  // Query real street-snapped route from OSRM
  const osrm = await fetchOSRMRoute(state.pickup.lat, state.pickup.lng, state.dropoff.lat, state.dropoff.lng);
  if (osrm && osrm.latlngs.length > 0) {
    state.routeGeometry = osrm.latlngs;
    state.routePolyline.setLatLngs(osrm.latlngs);
    // Real solid road polyline with vibrant CoGo Emerald styling
    state.routePolyline.setStyle({ color: '#00c853', weight: 5, dashArray: null, opacity: 0.9 });
    state.map.fitBounds(L.latLngBounds(osrm.latlngs), { padding: [70, 70] });
  }

  fetchEstimates();
}

function setPresetLocation(presetKey) {
  stopPicking();
  if (presetKey === 'cp_to_ig') {
    setPickupLocation(PRESETS.cp.lat, PRESETS.cp.lng, PRESETS.cp.name);
    setDropoffLocation(PRESETS.india_gate.lat, PRESETS.india_gate.lng, PRESETS.india_gate.name);
  } else if (presetKey === 'cp_to_t3') {
    setPickupLocation(PRESETS.cp.lat, PRESETS.cp.lng, PRESETS.cp.name);
    setDropoffLocation(PRESETS.t3.lat, PRESETS.t3.lng, PRESETS.t3.name);
  } else if (presetKey === 'ig_to_cyber') {
    setPickupLocation(PRESETS.india_gate.lat, PRESETS.india_gate.lng, PRESETS.india_gate.name);
    setDropoffLocation(PRESETS.cyberhub.lat, PRESETS.cyberhub.lng, PRESETS.cyberhub.name);
  }
}

/* ==========================================================================
   Place Search Autocomplete
   ========================================================================== */
function setupAutocomplete(inputId, dropdownId, targetType) {
  const input = document.getElementById(inputId);
  const dropdown = document.getElementById(dropdownId);

  input.addEventListener('focus', () => fetchPlaces('', dropdown, targetType));
  input.addEventListener('input', (e) => fetchPlaces(e.target.value, dropdown, targetType));

  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.style.display = 'none';
    }
  });
}

async function fetchPlaces(query, dropdownEl, targetType) {
  try {
    let places = [];
    const res = await fetch(`/api/places?q=${encodeURIComponent(query)}`);
    places = await res.json();

    // Query Nominatim (100% Free OpenStreetMap Geocoder) if query >= 3 chars & local results sparse
    if (query && query.trim().length >= 3 && places.length < 3) {
      try {
        const nomRes = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=4&countrycodes=in`);
        if (nomRes.ok) {
          const nomData = await nomRes.json();
          nomData.forEach(item => {
            places.push({
              id: `nom_${item.place_id}`,
              name: item.display_name.split(',')[0],
              address: item.display_name,
              lat: parseFloat(item.lat),
              lng: parseFloat(item.lon)
            });
          });
        }
      } catch (nomErr) {
        // Fallback to local places if offline
      }
    }

    if (!places || places.length === 0) {
      dropdownEl.style.display = 'none';
      return;
    }

    dropdownEl.innerHTML = '';
    places.slice(0, 5).forEach(p => {
      const item = document.createElement('div');
      item.className = 'autocomplete-item';
      item.innerHTML = `
        <span class="item-name">📍 ${p.name}</span>
        <span class="item-addr">${p.address}</span>
      `;
      item.onclick = () => {
        if (targetType === 'pickup') {
          setPickupLocation(p.lat, p.lng, p.name);
        } else {
          setDropoffLocation(p.lat, p.lng, p.name);
        }
        dropdownEl.style.display = 'none';
      };
      dropdownEl.appendChild(item);
    });
    dropdownEl.style.display = 'block';
  } catch (err) {
    console.error("Autocomplete error:", err);
  }
}

/* ==========================================================================
   Estimates & Vehicle Carousel
   ========================================================================== */
async function loadVehicles() {
  try {
    const res = await fetch('/api/vehicles');
    state.vehicles = await res.json();
    renderVehicleCarousel();
  } catch (err) {
    console.error("Vehicle load failure:", err);
  }
}

async function fetchEstimates() {
  if (!state.pickup || !state.dropoff) return;

  try {
    const res = await fetch('/api/estimate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pickup: state.pickup,
        dropoff: state.dropoff,
        addons: state.selectedAddons,
        promo_code: state.appliedPromo
      })
    });

    const data = await res.json();
    state.currentEstimates = data;

    document.getElementById('route-metrics-bar').style.display = 'flex';
    document.getElementById('metric-distance').innerText = `${data.distance_km} km`;
    
    // Pick active vehicle duration
    const currentVeh = data.vehicles.find(v => v.vehicle_id === state.selectedVehicleId);
    if (currentVeh) {
      document.getElementById('metric-duration').innerText = `${currentVeh.duration_min} mins`;
    }

    renderVehicleCarousel();
    updateFareSummaryCard();
    document.getElementById('btn-request-cogo').disabled = false;
  } catch (err) {
    console.error("Estimate fetch error:", err);
  }
}

function renderVehicleCarousel() {
  const container = document.getElementById('vehicle-tier-list');
  container.innerHTML = '';

  state.vehicles.forEach(v => {
    let priceText = 'Calculating...';
    let fareObj = null;

    if (state.currentEstimates) {
      fareObj = state.currentEstimates.vehicles.find(item => item.vehicle_id === v.id);
      if (fareObj) {
        priceText = `₹${fareObj.total_fare.toFixed(0)}`;
      }
    }

    const isSelected = v.id === state.selectedVehicleId;
    const card = document.createElement('div');
    card.className = `cogo-vehicle-card ${isSelected ? 'selected' : ''}`;
    card.onclick = () => selectVehicle(v.id);

    card.innerHTML = `
      <div class="vc-left">
        <div class="vc-icon">${v.icon || '🚗'}</div>
        <div class="vc-info">
          <h4>${v.name} ${v.badge ? `<span class="vc-badge">${v.badge}</span>` : ''}</h4>
          <p class="vc-model">${v.model}</p>
          <div class="vc-specs">
            <span>👤 ${v.seats} seats</span>
            ${v.luggage ? `<span>🧳 ${v.luggage}</span>` : ''}
            ${v.has_ac ? `<span>❄️ AC</span>` : ''}
          </div>
        </div>
      </div>
      <div class="vc-right">
        <div class="vc-price">${priceText}</div>
        <div class="vc-eta">${fareObj ? `${fareObj.duration_min} min away` : '2 min away'}</div>
      </div>
    `;

    container.appendChild(card);
  });
}

function selectVehicle(id) {
  state.selectedVehicleId = id;
  renderVehicleCarousel();
  updateFareSummaryCard();
}

function updateFareSummaryCard() {
  const card = document.getElementById('fare-summary-card');
  if (!state.currentEstimates) {
    card.style.display = 'none';
    return;
  }

  const fare = state.currentEstimates.vehicles.find(v => v.vehicle_id === state.selectedVehicleId);
  if (!fare) return;

  card.style.display = 'block';
  document.getElementById('fs-base').innerText = `₹${fare.base_fare}`;
  document.getElementById('fs-km-rate').innerText = `₹${fare.cost_per_km}/km`;
  document.getElementById('fs-dist').innerText = `₹${fare.distance_fare}`;
  document.getElementById('fs-min-rate').innerText = `₹${fare.cost_per_min}/min`;
  document.getElementById('fs-time').innerText = `₹${fare.time_fare}`;

  const addonsRow = document.getElementById('fs-addons-row');
  if (fare.addons_cost > 0) {
    addonsRow.style.display = 'flex';
    document.getElementById('fs-addons').innerText = `+₹${fare.addons_cost}`;
  } else {
    addonsRow.style.display = 'none';
  }

  const discountRow = document.getElementById('fs-discount-row');
  if (fare.discount_amount > 0) {
    discountRow.style.display = 'flex';
    document.getElementById('fs-discount').innerText = `-₹${fare.discount_amount}`;
  } else {
    discountRow.style.display = 'none';
  }

  document.getElementById('fs-total').innerText = `₹${fare.total_fare.toFixed(2)}`;
}

/* ==========================================================================
   Addons & Promo Codes
   ========================================================================== */
function onAddonChange() {
  const selected = [];
  if (document.getElementById('addon-luggage').checked) selected.push('luggage_assist');
  if (document.getElementById('addon-quiet').checked) selected.push('quiet_ride');
  if (document.getElementById('addon-top-driver').checked) selected.push('top_rated_driver');
  state.selectedAddons = selected;
  fetchEstimates();
}

async function applyPromoCode() {
  const codeInput = document.getElementById('input-promo-code');
  const code = (codeInput.value || "").trim().toUpperCase();
  const msgEl = document.getElementById('promo-message');

  if (!code) {
    state.appliedPromo = null;
    msgEl.style.display = 'none';
    fetchEstimates();
    return;
  }

  try {
    const res = await fetch('/api/promos/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code, gross_fare: 150.0 })
    });
    const result = await res.json();

    msgEl.style.display = 'block';
    if (result.valid) {
      state.appliedPromo = code;
      msgEl.className = 'promo-feedback success';
      msgEl.innerText = `✓ ${result.description} applied!`;
      fetchEstimates();
    } else {
      state.appliedPromo = null;
      msgEl.className = 'promo-feedback error';
      msgEl.innerText = `✕ ${result.message}`;
    }
  } catch (err) {
    console.error("Promo validation error:", err);
  }
}

function onPaymentChange(radio) {
  state.paymentMethod = radio.value;
  document.querySelectorAll('.pay-option').forEach(el => el.classList.remove('selected'));
  radio.closest('.pay-option').classList.add('selected');
}

function toggleSchedule(isLater) {
  state.isScheduled = isLater;
  document.getElementById('btn-ride-now').classList.toggle('active', !isLater);
  document.getElementById('btn-ride-later').classList.toggle('active', isLater);
  document.getElementById('schedule-picker-box').style.display = isLater ? 'block' : 'none';
  document.getElementById('btn-cogo-text').innerText = isLater ? 'Confirm Scheduled CoGo' : 'Confirm & Request CoGo';
}

/* ==========================================================================
   Real-Time Server-Sent Events (SSE) & Moving Cabs
   ========================================================================== */
function connectSSE() {
  state.eventSource = new EventSource('/api/events');

  state.eventSource.addEventListener('init_drivers', (e) => {
    const drivers = JSON.parse(e.data);
    renderDriverMarkers(drivers);
  });

  state.eventSource.addEventListener('driver_moved', (e) => {
    const data = JSON.parse(e.data);
    const marker = state.driverMarkers[data.driver_id];
    if (marker) {
      marker.setLatLng([data.lat, data.lng]);
      // Rotate icon according to compass heading
      const iconEl = marker.getElement();
      if (iconEl && data.heading !== undefined) {
        iconEl.style.transform += ` rotate(${data.heading}deg)`;
      }
    }
    if (state.activeTrip && state.activeTrip.id === data.trip_id) {
      updateActiveProgress(data.progress);
    }
  });

  state.eventSource.addEventListener('trip_update', (e) => {
    const trip = JSON.parse(e.data);
    if (state.activeTrip && state.activeTrip.id === trip.id) {
      handleTripStatusUpdate(trip);
    }
  });
}

function renderDriverMarkers(drivers) {
  drivers.forEach(d => {
    if (state.driverMarkers[d.id]) {
      state.driverMarkers[d.id].setLatLng([d.lat, d.lng]);
    } else {
      const carIcon = L.divIcon({
        className: 'cogo-car-marker',
        html: d.icon || '🚗',
        iconSize: [40, 40],
        iconAnchor: [20, 20]
      });

      const marker = L.marker([d.lat, d.lng], { icon: carIcon }).addTo(state.map);
      marker.bindPopup(`
        <strong>${d.name}</strong> (${d.category})<br>
        Car: ${d.vehicle_model} [${d.plate}]<br>
        Rating: ★ ${d.rating} (${d.total_trips} rides)
      `);
      state.driverMarkers[d.id] = marker;
    }
  });
}

/* ==========================================================================
   Ride Lifecycle Management
   ========================================================================== */
async function requestCoGoRide() {
  if (!state.pickup || !state.dropoff) return;

  const btn = document.getElementById('btn-request-cogo');
  btn.disabled = true;
  btn.innerHTML = `<span>Matching with Nearest Captain...</span>`;

  try {
    const res = await fetch('/api/rides', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pickup: state.pickup,
        dropoff: state.dropoff,
        vehicle_id: state.selectedVehicleId,
        payment_method: state.paymentMethod,
        addons: state.selectedAddons,
        promo_code: state.appliedPromo,
        scheduled_at: state.isScheduled ? document.getElementById('input-schedule-time').value : null,
        rider_name: "Harshit"
      })
    });

    const trip = await res.json();
    state.activeTrip = trip;

    // Transition to Tracking View
    document.getElementById('stage-booking-setup').style.display = 'none';
    document.getElementById('stage-booking-active').style.display = 'block';

    document.getElementById('track-pickup-name').innerText = trip.pickup_address;
    document.getElementById('track-dropoff-name').innerText = trip.dropoff_address;
    document.getElementById('track-status-title').innerText = 'Searching for Captain...';
    document.getElementById('track-radar-box').style.display = 'block';
    document.getElementById('track-captain-card').style.display = 'none';
    document.getElementById('track-otp-pill').style.display = 'none';
    document.getElementById('track-progress-bar').style.width = '6%';

    showToast("🔍 Contacting nearest certified CoGo Captains...");
  } catch (err) {
    console.error("Booking error:", err);
    btn.disabled = false;
    btn.innerHTML = `<span>Confirm & Request CoGo</span>`;
    alert("Could not book ride. Please verify server connection.");
  }
}

function handleTripStatusUpdate(trip) {
  state.activeTrip = trip;
  const statusTitle = document.getElementById('track-status-title');
  const radarBox = document.getElementById('track-radar-box');
  const capCard = document.getElementById('track-captain-card');
  const otpPill = document.getElementById('track-otp-pill');

  if (trip.status === 'ACCEPTED') {
    sound.playMatchChime();
    statusTitle.innerText = 'Captain On The Way';
    radarBox.style.display = 'none';
    capCard.style.display = 'flex';
    otpPill.style.display = 'block';

    document.getElementById('track-cap-name').innerText = trip.driver_name;
    document.getElementById('track-cap-car').innerText = `${trip.vehicle_model} • ${trip.license_plate}`;
    document.getElementById('track-cap-rating').innerText = trip.driver_rating;
    document.getElementById('track-cap-avatar').innerText = trip.driver_avatar || '👨‍✈️';
    document.getElementById('track-otp-value').innerText = trip.otp;

    showToast(`🚕 Captain ${trip.driver_name} is arriving in a ${trip.vehicle_model}!`);
  } else if (trip.status === 'ARRIVED') {
    sound.playArrivalChime();
    statusTitle.innerText = 'Captain Arrived at Pickup';
    showToast("📍 Your Captain is at the pickup spot! Share your start PIN.");
  } else if (trip.status === 'IN_PROGRESS') {
    statusTitle.innerText = 'On Trip to Destination';
    showToast("🚀 Heading towards your destination...");
  } else if (trip.status === 'COMPLETED') {
    sound.playArrivalChime();
    showCompletedReceipt(trip);
  } else if (trip.status === 'CANCELLED') {
    alert("This ride was cancelled.");
    resetToNewBooking();
  }
}

function updateActiveProgress(percent) {
  const bar = document.getElementById('track-progress-bar');
  if (bar) bar.style.width = `${percent}%`;
}

function showCompletedReceipt(trip) {
  document.getElementById('stage-booking-active').style.display = 'none';
  document.getElementById('stage-booking-receipt').style.display = 'block';

  document.getElementById('rcpt-final-fare').innerText = `₹${trip.fare.toFixed(2)}`;
  document.getElementById('rcpt-distance').innerText = `${trip.distance_km} km`;
  document.getElementById('rcpt-time').innerText = `${trip.duration_min} mins`;
  document.getElementById('rcpt-car').innerText = `${trip.vehicle_model} (${trip.license_plate})`;
  document.getElementById('rcpt-captain').innerText = trip.driver_name;
  document.getElementById('rcpt-pay-method').innerText = trip.payment_method;

  const discRow = document.getElementById('rcpt-discount-row');
  if (trip.discount_amount > 0) {
    discRow.style.display = 'flex';
    document.getElementById('rcpt-discount').innerText = `-₹${trip.discount_amount}`;
  } else {
    discRow.style.display = 'none';
  }

  showToast("🎉 Arrived safely! Total fare: ₹" + trip.fare.toFixed(2));
}

async function cancelCurrentTrip() {
  if (!state.activeTrip) return;
  if (!confirm("Are you sure you want to cancel this ride?")) return;

  try {
    await fetch(`/api/rides/${state.activeTrip.id}/cancel`, { method: 'POST' });
    resetToNewBooking();
  } catch (err) {
    console.error("Cancel failed:", err);
  }
}

function resetToNewBooking() {
  state.activeTrip = null;
  document.getElementById('stage-booking-setup').style.display = 'block';
  document.getElementById('stage-booking-active').style.display = 'none';
  document.getElementById('stage-booking-receipt').style.display = 'none';

  const btn = document.getElementById('btn-request-cogo');
  btn.disabled = false;
  btn.innerHTML = `<span>Confirm & Request CoGo</span>`;
}

function setTip(amt, btn) {
  state.selectedTip = amt;
  document.querySelectorAll('.tip-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

function setRating(rating) {
  state.selectedRating = rating;
  const stars = document.querySelectorAll('#star-row .star');
  stars.forEach((s, idx) => {
    s.classList.toggle('active', idx < rating);
  });
}

async function submitRatingAndReset() {
  if (state.activeTrip) {
    const feedback = document.getElementById('input-feedback-note').value;
    try {
      await fetch(`/api/rides/${state.activeTrip.id}/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rating: state.selectedRating,
          tip: state.selectedTip,
          feedback: feedback
        })
      });
    } catch (e) {
      console.error(e);
    }
  }
  showToast("⭐ Rating submitted. Thank you!");
  resetToNewBooking();
}

/* ==========================================================================
   Safety & SOS Hub
   ========================================================================== */
function openSafetyModal() {
  document.getElementById('modal-sos').style.display = 'flex';
  if (state.pickup) {
    document.getElementById('sos-coords-text').innerText = `${state.pickup.lat.toFixed(4)}° N, ${state.pickup.lng.toFixed(4)}° E`;
  }
}

function closeSafetyModal() {
  document.getElementById('modal-sos').style.display = 'none';
}

function triggerSOS() {
  openSafetyModal();
}

function shareLiveTrip() {
  const tripUrl = window.location.href;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(tripUrl);
    showToast("📋 Live tracking link copied to clipboard!");
  } else {
    alert("Shareable Live Trip Link: " + tripUrl);
  }
}

/* ==========================================================================
   Map Pin Picking Helpers
   ========================================================================== */
function setupEventListeners() {
  document.getElementById('btn-pick-pickup').addEventListener('click', () => {
    state.pickingTarget = state.pickingTarget === 'pickup' ? null : 'pickup';
    updatePickerUI();
    if (state.pickingTarget) showToast("📍 Click on the map to set Pickup point");
  });

  document.getElementById('btn-pick-dropoff').addEventListener('click', () => {
    state.pickingTarget = state.pickingTarget === 'dropoff' ? null : 'dropoff';
    updatePickerUI();
    if (state.pickingTarget) showToast("📍 Click on the map to set Destination point");
  });
}

function updatePickerUI() {
  document.getElementById('btn-pick-pickup').classList.toggle('active', state.pickingTarget === 'pickup');
  document.getElementById('btn-pick-dropoff').classList.toggle('active', state.pickingTarget === 'dropoff');
}

function stopPicking() {
  state.pickingTarget = null;
  updatePickerUI();
  hideToast();
}

function showToast(msg) {
  const toast = document.getElementById('map-toast');
  document.getElementById('toast-text').innerText = msg;
  toast.style.opacity = '1';
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => {
    hideToast();
  }, 4000);
}

function hideToast() {
  document.getElementById('map-toast').style.opacity = '0';
}

/* ==========================================================================
   View Navigation & History
   ========================================================================== */
function switchMainTab(tab) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));

  if (tab === 'rider') {
    document.getElementById('tab-rider').classList.add('active');
    document.getElementById('panel-rider').classList.add('active');
  } else if (tab === 'driver') {
    document.getElementById('tab-driver').classList.add('active');
    document.getElementById('panel-driver').classList.add('active');
  } else if (tab === 'history') {
    document.getElementById('tab-history').classList.add('active');
    document.getElementById('panel-history').classList.add('active');
    loadHistory();
  }
}

async function loadHistory() {
  const container = document.getElementById('history-cards-list');
  container.innerHTML = '<p style="text-align:center; color:#94a3b8; padding:30px;">Loading trip history...</p>';

  try {
    const res = await fetch('/api/history');
    const trips = await res.json();
    if (!trips || trips.length === 0) {
      container.innerHTML = '<p style="text-align:center; color:#94a3b8; padding:30px;">No rides recorded yet.</p>';
      return;
    }

    container.innerHTML = '';
    trips.forEach(t => {
      const card = document.createElement('div');
      card.className = 'history-item-card';
      const dateStr = new Date(t.created_at).toLocaleDateString(undefined, {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
      });

      card.innerHTML = `
        <div class="h-top">
          <span class="h-car">${t.vehicle_model}</span>
          <span class="h-fare">${t.currency}${t.fare.toFixed(2)}</span>
        </div>
        <div class="h-route">
          <div>● From: ${t.pickup_address}</div>
          <div>■ To: ${t.dropoff_address}</div>
        </div>
        <div class="h-bottom">
          <span>${dateStr}</span>
          <span>Status: <strong>${t.status}</strong></span>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    container.innerHTML = '<p style="text-align:center; color:#ef4444; padding:30px;">Could not load past rides.</p>';
  }
}

/* ==========================================================================
   Captain Duty & Simulation
   ========================================================================== */
function toggleCaptainDuty() {
  state.captainDutyOnline = !state.captainDutyOnline;
  const dutyText = document.getElementById('captain-duty-text');
  const btn = document.getElementById('btn-toggle-captain-duty');

  if (state.captainDutyOnline) {
    dutyText.innerText = 'ONLINE & READY';
    dutyText.className = 'duty-state online';
    btn.innerText = 'GO OFFLINE';
    btn.className = 'duty-toggle-switch online';
    showToast("🟢 Duty: You are Online & receiving trips");
  } else {
    dutyText.innerText = 'OFFLINE';
    dutyText.className = 'duty-state offline';
    btn.innerText = 'GO ONLINE';
    btn.className = 'duty-toggle-switch offline';
    showToast("🔴 Duty: You are Offline");
  }
}
