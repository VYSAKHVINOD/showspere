/**
 * ShowSphere (BookMyShow Clone) - Interactive Frontend Engine
 * Zero external library dependencies - 100% Local & Fast
 */

const API_BASE = "/api";

// Application State
const state = {
  events: [],
  cities: [],
  selectedCategory: "All",
  selectedCity: "All",
  searchQuery: "",
  
  // Current Active Booking Flow
  currentEvent: null,
  availableDates: [],
  selectedDate: "",
  currentShow: null,
  bookedSeats: new Set(),
  selectedSeats: [], // Array of { code: 'A4', tier: 'VIP', price: 600 }
  
  // F&B Addons
  snacks: [
    { id: "s1", name: "Large Caramel Popcorn", price: 340, img: "https://images.unsplash.com/photo-1578849278619-e73505e9610f?auto=format&fit=crop&w=400&q=80" },
    { id: "s2", name: "Mexican Cheese Nachos", price: 280, img: "https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?auto=format&fit=crop&w=400&q=80" },
    { id: "s3", name: "Chilled Pepsi Duo (500ml)", price: 180, img: "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=400&q=80" },
    { id: "s4", name: "Blockbuster Combo (Tub + 2 Drinks)", price: 590, img: "https://images.unsplash.com/photo-1585647347483-22b66260dfff?auto=format&fit=crop&w=400&q=80" }
  ],
  selectedSnacks: {}, // { s1: 1, s2: 2 }

  // My Bookings
  myBookings: []
};

// Seat Layout Configuration
const SEAT_LAYOUT = {
  VIP: {
    name: "VIP Recliner",
    rows: ["A", "B"],
    priceKey: "price_vip",
    defaultPrice: 600,
    seatsPerRow: 14,
    aisles: [3, 11] // Aisle gap after seat 3 and seat 11
  },
  PLATINUM: {
    name: "Platinum Club",
    rows: ["C", "D", "E"],
    priceKey: "price_platinum",
    defaultPrice: 350,
    seatsPerRow: 16,
    aisles: [4, 12]
  },
  GOLD: {
    name: "Gold Executive",
    rows: ["F", "G", "H", "J", "K"],
    priceKey: "price_gold",
    defaultPrice: 200,
    seatsPerRow: 16,
    aisles: [4, 12]
  }
};

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  initDateRibbon();
  setupEventListeners();
  loadCities();
  loadEvents();
  loadBookingsCount();
});

function initDateRibbon() {
  const dates = [];
  const today = new Date();
  const dayNames = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  const monthNames = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

  for (let i = 0; i < 6; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    
    // Format YYYY-MM-DD
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    const dateStr = `${yyyy}-${mm}-${dd}`;

    let label = dayNames[d.getDay()];
    if (i === 0) label = "TODAY";
    else if (i === 1) label = "TOM";

    dates.push({
      dateStr,
      label,
      dayNum: d.getDate(),
      month: monthNames[d.getMonth()]
    });
  }
  state.availableDates = dates;
  state.selectedDate = dates[0].dateStr;
}

// ==========================================================================
// API Handlers
// ==========================================================================
async function loadCities() {
  try {
    const res = await fetch(`${API_BASE}/cities`);
    const data = await res.json();
    if (data.cities) {
      state.cities = data.cities;
      renderCitySelector();
    }
  } catch (err) {
    console.error("Failed to load cities", err);
  }
}

async function loadEvents() {
  try {
    let url = `${API_BASE}/events?category=${encodeURIComponent(state.selectedCategory)}&city=${encodeURIComponent(state.selectedCity)}`;
    if (state.searchQuery) {
      url += `&search=${encodeURIComponent(state.searchQuery)}`;
    }
    const res = await fetch(url);
    const data = await res.json();
    state.events = data.events || [];
    renderEvents();
  } catch (err) {
    console.error("Failed to load events", err);
    showToast("Error loading events", "error");
  }
}

async function loadEventShows(eventId, date) {
  try {
    const res = await fetch(`${API_BASE}/events/${eventId}/shows?date=${encodeURIComponent(date)}&city=${encodeURIComponent(state.selectedCity)}`);
    return await res.json();
  } catch (err) {
    console.error("Failed to load shows", err);
    return { venues: [] };
  }
}

async function loadShowDetails(showId) {
  try {
    const res = await fetch(`${API_BASE}/shows/${showId}`);
    return await res.json();
  } catch (err) {
    console.error("Failed to load show details", err);
    return null;
  }
}

async function loadBookingsCount() {
  try {
    const res = await fetch(`${API_BASE}/bookings`);
    const data = await res.json();
    const count = (data.bookings || []).filter(b => b.status === "CONFIRMED").length;
    const badge = document.getElementById("navBookingsCount");
    if (badge) badge.textContent = count;
  } catch (err) {
    console.error("Failed to load bookings count", err);
  }
}

// ==========================================================================
// Event Listeners
// ==========================================================================
function setupEventListeners() {
  // Search Bar with debounce
  const searchInput = document.getElementById("searchInput");
  let debounceTimer;
  searchInput.addEventListener("input", (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      state.searchQuery = e.target.value.trim();
      loadEvents();
    }, 250);
  });

  // City Selector
  const citySelect = document.getElementById("citySelect");
  citySelect.addEventListener("change", (e) => {
    state.selectedCity = e.target.value;
    loadEvents();
  });

  // Category Pills
  const pills = document.querySelectorAll(".pill-item");
  pills.forEach(pill => {
    pill.addEventListener("click", () => {
      pills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      state.selectedCategory = pill.getAttribute("data-category");
      loadEvents();
    });
  });

  // My Bookings Button
  document.getElementById("btnMyBookings").addEventListener("click", () => {
    openMyBookingsModal();
  });

  // Admin / Add Event Button
  document.getElementById("btnAddEvent").addEventListener("click", () => {
    openModal("adminModal");
  });

  // Admin Form Submit
  const addEventForm = document.getElementById("addEventForm");
  if (addEventForm) {
    addEventForm.addEventListener("submit", handleAddEventSubmit);
  }

  // Checkout Form Submit
  const checkoutForm = document.getElementById("checkoutForm");
  if (checkoutForm) {
    checkoutForm.addEventListener("submit", handleBookingSubmit);
  }

  // Payment Tabs
  document.querySelectorAll(".payment-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".payment-tab-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const method = btn.getAttribute("data-method");
      document.getElementById("paymentMethodInput").value = method;
      document.querySelectorAll(".payment-method-panel").forEach(p => p.style.display = "none");
      const panel = document.getElementById(`payPanel_${method}`);
      if (panel) panel.style.display = "block";
    });
  });

  // Modal Closers
  document.querySelectorAll(".modal-close-btn, [data-close-modal]").forEach(btn => {
    btn.addEventListener("click", () => {
      const modal = btn.closest(".modal-overlay");
      if (modal) closeModal(modal.id);
    });
  });

  // Close modal on background click
  document.querySelectorAll(".modal-overlay").forEach(overlay => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        closeModal(overlay.id);
      }
    });
  });
}

// ==========================================================================
// UI Rendering
// ==========================================================================
function renderCitySelector() {
  const select = document.getElementById("citySelect");
  select.innerHTML = '<option value="All">All Cities</option>';
  state.cities.forEach(city => {
    const opt = document.createElement("option");
    opt.value = city;
    opt.textContent = city;
    select.appendChild(opt);
  });
}

function renderEvents() {
  const grid = document.getElementById("eventsGrid");
  const countLabel = document.getElementById("eventsCountLabel");
  countLabel.textContent = `(${state.events.length} ${state.events.length === 1 ? 'Event' : 'Events'})`;

  if (!state.events.length) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--text-muted);">
        <p style="font-size: 18px; font-weight: 600; margin-bottom: 8px;">No events found</p>
        <p style="font-size: 13px;">Try selecting another category or city.</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = state.events.map(ev => `
    <div class="event-card">
      <div class="card-poster-wrap">
        <img class="card-poster" src="${ev.poster_url}" alt="${ev.title}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=600&q=80'"/>
        <div class="card-category-badge">${ev.category}</div>
        <div class="card-rating-badge">
          <span class="rating-score">★ ${ev.rating}/10</span>
          <span class="rating-votes">${ev.votes_count} votes</span>
        </div>
      </div>
      <div class="card-info">
        <h3 class="card-title" title="${ev.title}">${ev.title}</h3>
        <p class="card-genre">${ev.genre}</p>
        <div class="card-meta-row">
          <span>${ev.language}</span>
          <span>${ev.duration}</span>
        </div>
        <button class="btn-card-book" onclick="openEventDetailsModal(${ev.id})">
          Book Tickets
        </button>
      </div>
    </div>
  `).join("");
}

// ==========================================================================
// Event Details & Shows Flow
// ==========================================================================
async function openEventDetailsModal(eventId) {
  const event = state.events.find(e => e.id === eventId);
  if (!event) return;
  state.currentEvent = event;

  // Set Hero & Info in Modal
  const hero = document.getElementById("modalEventHero");
  hero.style.backgroundImage = `url(${event.banner_url || event.poster_url})`;
  document.getElementById("modalPosterThumb").src = event.poster_url;
  document.getElementById("modalHeroTitle").textContent = event.title;
  document.getElementById("modalHeroTags").textContent = `${event.category} • ${event.language} • ${event.duration} • ★ ${event.rating}/10`;
  document.getElementById("modalEventDesc").textContent = event.description || "";
  document.getElementById("modalEventCast").textContent = event.cast_crew ? `Cast & Crew: ${event.cast_crew}` : "";

  // Render Date Ribbon
  renderDateRibbon();

  // Load Shows for first date
  await loadAndRenderShowsForCurrentDate();

  openModal("eventDetailsModal");
}

function renderDateRibbon() {
  const ribbon = document.getElementById("dateRibbon");
  ribbon.innerHTML = state.availableDates.map(d => `
    <div class="date-pill ${d.dateStr === state.selectedDate ? 'active' : ''}" onclick="selectShowDate('${d.dateStr}')">
      <span class="day-name">${d.label}</span>
      <span class="day-num">${d.dayNum}</span>
      <span class="day-name">${d.month}</span>
    </div>
  `).join("");
}

async function selectShowDate(dateStr) {
  state.selectedDate = dateStr;
  renderDateRibbon();
  await loadAndRenderShowsForCurrentDate();
}

async function loadAndRenderShowsForCurrentDate() {
  const container = document.getElementById("showsContainer");
  container.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted);">Finding available theaters and showtimes...</div>`;

  const data = await loadEventShows(state.currentEvent.id, state.selectedDate);
  const venues = data.venues || [];

  if (!venues.length) {
    container.innerHTML = `
      <div style="text-align: center; padding: 40px; color: var(--text-muted);">
        <p style="font-size: 16px; font-weight: 600;">No shows available on this date</p>
        <p style="font-size: 13px;">Please select another date from the ribbon above.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = venues.map(v => `
    <div class="venue-card">
      <div class="venue-header">
        <div>
          <h4 class="venue-title">🏢 ${v.venue_name}</h4>
          <p class="venue-address">${v.venue_address}</p>
        </div>
        <span style="font-size: 11px; color: var(--text-muted); background: rgba(255,255,255,0.06); padding: 4px 8px; border-radius: 4px;">
          ${v.screens_info || 'M-Ticket Available'}
        </span>
      </div>
      <div class="showtimes-wrap">
        ${v.shows.map(s => `
          <button class="showtime-pill" onclick="openSeatSelectionModal(${s.show_id})">
            <span>${s.show_time}</span>
            <span class="format-tag">${s.format}</span>
          </button>
        `).join("")}
      </div>
    </div>
  `).join("");
}

// ==========================================================================
// Interactive Seat Map Logic
// ==========================================================================
async function openSeatSelectionModal(showId) {
  closeModal("eventDetailsModal");
  state.selectedSeats = [];
  state.selectedSnacks = {};

  const data = await loadShowDetails(showId);
  if (!data || !data.show) {
    showToast("Failed to load show details", "error");
    return;
  }

  state.currentShow = data.show;
  state.bookedSeats = new Set(data.booked_seats || []);

  // Update Header
  document.getElementById("seatmapEventTitle").textContent = state.currentShow.event_title;
  document.getElementById("seatmapVenueDetails").textContent = `${state.currentShow.venue_name} | ${state.currentShow.show_date} at ${state.currentShow.show_time} (${state.currentShow.format})`;

  // Render Seat Grid
  renderSeatMap();
  updateSeatSummaryBar();

  openModal("seatmapModal");
}

function renderSeatMap() {
  const container = document.getElementById("seatTiersContainer");
  let html = "";

  const tiers = [
    { key: "VIP", config: SEAT_LAYOUT.VIP, price: state.currentShow.price_vip || 600 },
    { key: "PLATINUM", config: SEAT_LAYOUT.PLATINUM, price: state.currentShow.price_platinum || 350 },
    { key: "GOLD", config: SEAT_LAYOUT.GOLD, price: state.currentShow.price_gold || 200 }
  ];

  tiers.forEach(tier => {
    html += `
      <div class="tier-section">
        <div class="tier-header ${tier.key.toLowerCase()}">
          <span>${tier.config.name}</span>
          <span>₹${tier.price}</span>
        </div>
    `;

    tier.config.rows.forEach(rowLetter => {
      html += `
        <div class="seat-row">
          <span class="row-letter">${rowLetter}</span>
          <div class="seat-block">
      `;

      for (let seatNum = 1; seatNum <= tier.config.seatsPerRow; seatNum++) {
        const seatCode = `${rowLetter}${seatNum}`;
        const isBooked = state.bookedSeats.has(seatCode);
        const isSelected = state.selectedSeats.some(s => s.code === seatCode);

        let seatClass = "seat";
        if (tier.key === "VIP") seatClass += " vip-seat";
        if (isBooked) seatClass += " booked";
        if (isSelected) seatClass += " selected";

        html += `
          <div class="${seatClass}" 
               data-code="${seatCode}" 
               data-tier="${tier.key}" 
               data-price="${tier.price}"
               onclick="toggleSeatSelection('${seatCode}', '${tier.key}', ${tier.price})">
            ${seatNum}
          </div>
        `;

        // Check if we need an aisle gap
        if (tier.config.aisles.includes(seatNum)) {
          html += `<div class="aisle-gap"></div>`;
        }
      }

      html += `
          </div>
          <span class="row-letter">${rowLetter}</span>
        </div>
      `;
    });

    html += `</div>`;
  });

  container.innerHTML = html;
}

function toggleSeatSelection(seatCode, tierKey, price) {
  if (state.bookedSeats.has(seatCode)) {
    showToast(`Seat ${seatCode} is already booked!`, "error");
    return;
  }

  const existingIndex = state.selectedSeats.findIndex(s => s.code === seatCode);

  if (existingIndex > -1) {
    // Deselect
    state.selectedSeats.splice(existingIndex, 1);
  } else {
    // Check Max Limit (8 tickets)
    if (state.selectedSeats.length >= 8) {
      showToast("Maximum 8 seats can be selected per booking", "error");
      return;
    }
    state.selectedSeats.push({ code: seatCode, tier: tierKey, price: price });
  }

  // Update visually without full re-render for speed
  const seatElem = document.querySelector(`.seat[data-code="${seatCode}"]`);
  if (seatElem) {
    seatElem.classList.toggle("selected");
  }

  updateSeatSummaryBar();
}

function updateSeatSummaryBar() {
  const summarySeats = document.getElementById("summarySeats");
  const summaryPrice = document.getElementById("summaryPrice");
  const btnProceed = document.getElementById("btnProceedToSnacks");

  if (state.selectedSeats.length === 0) {
    summarySeats.innerHTML = "No seats selected";
    summaryPrice.textContent = "₹0";
    btnProceed.disabled = true;
    btnProceed.style.opacity = "0.5";
    btnProceed.style.cursor = "not-allowed";
    return;
  }

  btnProceed.disabled = false;
  btnProceed.style.opacity = "1";
  btnProceed.style.cursor = "pointer";

  const seatCodes = state.selectedSeats.map(s => s.code).join(", ");
  const totalPrice = state.selectedSeats.reduce((sum, s) => sum + s.price, 0);

  summarySeats.innerHTML = `Seats: <span>${seatCodes}</span> (${state.selectedSeats.length} ${state.selectedSeats.length === 1 ? 'Ticket' : 'Tickets'})`;
  summaryPrice.textContent = `₹${totalPrice}`;
}

// ==========================================================================
// Food & Beverages (F&B) Step
// ==========================================================================
function openSnacksModal() {
  if (state.selectedSeats.length === 0) return;
  closeModal("seatmapModal");

  const grid = document.getElementById("snacksGrid");
  grid.innerHTML = state.snacks.map(snack => {
    const qty = state.selectedSnacks[snack.id] || 0;
    return `
      <div class="snack-card">
        <img class="snack-img" src="${snack.img}" alt="${snack.name}"/>
        <h4 class="snack-name">${snack.name}</h4>
        <span class="snack-price">₹${snack.price}</span>
        <div class="snack-qty-controls">
          <button class="btn-qty" onclick="changeSnackQty('${snack.id}', -1)">-</button>
          <span id="snackQty_${snack.id}" style="font-weight:700; font-size:14px;">${qty}</span>
          <button class="btn-qty" onclick="changeSnackQty('${snack.id}', 1)">+</button>
        </div>
      </div>
    `;
  }).join("");

  openModal("snacksModal");
}

function changeSnackQty(snackId, delta) {
  const current = state.selectedSnacks[snackId] || 0;
  const updated = Math.max(0, current + delta);
  if (updated === 0) {
    delete state.selectedSnacks[snackId];
  } else {
    state.selectedSnacks[snackId] = updated;
  }
  const elem = document.getElementById(`snackQty_${snackId}`);
  if (elem) elem.textContent = updated;
}

// ==========================================================================
// Checkout & Payment Simulation
// ==========================================================================
function proceedToCheckout() {
  closeModal("snacksModal");

  // Calculate Totals
  const ticketsSubtotal = state.selectedSeats.reduce((sum, s) => sum + s.price, 0);
  
  let snacksTotal = 0;
  const snackDetails = [];
  for (const [id, qty] of Object.entries(state.selectedSnacks)) {
    const item = state.snacks.find(s => s.id === id);
    if (item && qty > 0) {
      const lineCost = item.price * qty;
      snacksTotal += lineCost;
      snackDetails.push(`${item.name} x${qty}`);
    }
  }

  const convenienceFee = Math.round(state.selectedSeats.length * 28.5);
  const gst = Math.round((ticketsSubtotal + snacksTotal + convenienceFee) * 0.18);
  const grandTotal = ticketsSubtotal + snacksTotal + convenienceFee + gst;

  // Render Checkout Breakdown
  document.getElementById("checkoutMovieTitle").textContent = state.currentShow.event_title;
  document.getElementById("checkoutVenueMeta").textContent = `${state.currentShow.venue_name} • ${state.currentShow.show_date} at ${state.currentShow.show_time}`;
  document.getElementById("checkoutSeatsList").textContent = `${state.selectedSeats.map(s => s.code).join(", ")} (${state.selectedSeats.length} Tickets)`;
  document.getElementById("checkoutTicketsPrice").textContent = `₹${ticketsSubtotal}`;
  
  const snacksRow = document.getElementById("checkoutSnacksRow");
  if (snacksTotal > 0) {
    snacksRow.style.display = "flex";
    document.getElementById("checkoutSnacksPrice").textContent = `₹${snacksTotal}`;
  } else {
    snacksRow.style.display = "none";
  }

  document.getElementById("checkoutFee").textContent = `₹${convenienceFee}`;
  document.getElementById("checkoutGst").textContent = `₹${gst}`;
  document.getElementById("checkoutGrandTotal").textContent = `₹${grandTotal}`;
  document.getElementById("btnPaySubmit").textContent = `Pay ₹${grandTotal}`;

  // Store for submission
  state.checkoutCalculations = {
    subtotal: ticketsSubtotal + snacksTotal,
    tax_and_fees: convenienceFee + gst,
    total_amount: grandTotal,
    snacks_summary: snackDetails.join(", ")
  };

  openModal("checkoutModal");
}

async function handleBookingSubmit(e) {
  e.preventDefault();

  const name = document.getElementById("userNameInput").value.trim();
  const email = document.getElementById("userEmailInput").value.trim();
  const phone = document.getElementById("userPhoneInput").value.trim();
  const paymentMethod = document.getElementById("paymentMethodInput").value || "UPI";

  if (!name || !phone) {
    showToast("Please enter your name and phone number", "error");
    return;
  }

  const btn = document.getElementById("btnPaySubmit");
  btn.disabled = true;
  btn.innerHTML = `<span>Processing Secure Payment...</span>`;

  try {
    const payload = {
      show_id: state.currentShow.id,
      seats: state.selectedSeats.map(s => s.code),
      user_name: name,
      user_email: email,
      user_phone: phone,
      snacks: state.checkoutCalculations.snacks_summary,
      subtotal: state.checkoutCalculations.subtotal,
      tax_and_fees: state.checkoutCalculations.tax_and_fees,
      total_amount: state.checkoutCalculations.total_amount,
      payment_method: paymentMethod
    };

    const res = await fetch(`${API_BASE}/bookings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
      showToast(data.error || "Booking failed", "error");
      btn.disabled = false;
      btn.textContent = `Pay ₹${state.checkoutCalculations.total_amount}`;
      return;
    }

    // Success! Show Confirmed E-Ticket
    closeModal("checkoutModal");
    showToast("Ticket booked successfully!", "success");
    loadBookingsCount();
    displayTicket(data.booking);

  } catch (err) {
    console.error("Booking error", err);
    showToast("Network error during booking", "error");
  } finally {
    btn.disabled = false;
    btn.textContent = `Pay ₹${state.checkoutCalculations?.total_amount || 0}`;
  }
}

// ==========================================================================
// Digital E-Ticket View & QR Generator
// ==========================================================================
function displayTicket(booking) {
  document.getElementById("ticketBookingId").textContent = booking.booking_code;
  document.getElementById("ticketPosterImg").src = booking.poster_url || "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=600&q=80";
  document.getElementById("ticketMovieTitle").textContent = booking.event_title;
  document.getElementById("ticketMovieFormat").textContent = `${booking.format || 'Standard'} • ${booking.language || 'English'}`;
  
  document.getElementById("ticketShowDate").textContent = booking.show_date;
  document.getElementById("ticketShowTime").textContent = booking.show_time;
  document.getElementById("ticketVenueName").textContent = booking.venue_name;
  document.getElementById("ticketSeatsList").textContent = booking.seats;
  document.getElementById("ticketAttendeeName").textContent = booking.user_name;
  document.getElementById("ticketTotalAmount").textContent = `₹${booking.total_amount}`;
  document.getElementById("ticketBarcodeText").textContent = booking.booking_code;

  // Generate Real QR Code locally via QRCode SVG generator
  const qrBox = document.getElementById("ticketQrBox");
  const qrData = `SHOWSPHERE-TICKET:${booking.booking_code}|SHOW:${booking.show_id}|SEATS:${booking.seats}|PAID:${booking.total_amount}`;
  if (window.QRCode && window.QRCode.generateSVG) {
    qrBox.innerHTML = window.QRCode.generateSVG(qrData, 140);
  } else {
    qrBox.innerHTML = `<div style="font-weight:bold; font-size:12px; text-align:center;">${booking.booking_code}</div>`;
  }

  openModal("ticketModal");
}

function printTicket() {
  window.print();
}

// ==========================================================================
// My Bookings Management Panel
// ==========================================================================
async function openMyBookingsModal() {
  const container = document.getElementById("myBookingsContainer");
  container.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted);">Loading your bookings...</div>`;
  openModal("myBookingsModal");

  try {
    const res = await fetch(`${API_BASE}/bookings`);
    const data = await res.json();
    state.myBookings = data.bookings || [];

    if (!state.myBookings.length) {
      container.innerHTML = `
        <div style="text-align:center; padding:50px 20px; color:var(--text-muted);">
          <p style="font-size:16px; font-weight:600; margin-bottom:8px;">No bookings found yet</p>
          <p style="font-size:13px;">Book your favorite movies, concerts or sports events now!</p>
        </div>
      `;
      return;
    }

    container.innerHTML = state.myBookings.map(b => `
      <div class="booking-item-card">
        <div class="booking-item-main">
          <img class="booking-item-poster" src="${b.poster_url}" alt="${b.event_title}" onerror="this.src='https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=600&q=80'"/>
          <div class="booking-item-info">
            <h4>${b.event_title}</h4>
            <p>🏢 ${b.venue_name}</p>
            <p>📅 ${b.show_date} • ⏰ ${b.show_time}</p>
            <p>🎟️ Seats: <strong>${b.seats}</strong> • ₹${b.total_amount}</p>
            <span class="booking-status-tag ${b.status === 'CONFIRMED' ? 'status-confirmed' : 'status-cancelled'}">
              ${b.status}
            </span>
          </div>
        </div>
        <div class="booking-item-actions">
          <button class="btn-secondary" style="font-size:12px; padding:6px 14px;" onclick="viewPastTicket('${b.booking_code}')">
            View Ticket
          </button>
          ${b.status === 'CONFIRMED' ? `
            <button class="btn-secondary" style="font-size:12px; padding:6px 14px; color:#f87171; border-color:rgba(248,113,113,0.3);" onclick="cancelBooking(${b.id})">
              Cancel
            </button>
          ` : ''}
        </div>
      </div>
    `).join("");

  } catch (err) {
    console.error("Failed to fetch bookings", err);
    container.innerHTML = `<div style="text-align:center; padding:30px; color:#ef4444;">Failed to load bookings.</div>`;
  }
}

async function viewPastTicket(bookingCode) {
  closeModal("myBookingsModal");
  try {
    const res = await fetch(`${API_BASE}/bookings/${bookingCode}`);
    const data = await res.json();
    if (data.booking) {
      displayTicket(data.booking);
    } else {
      showToast("Ticket not found", "error");
    }
  } catch (err) {
    showToast("Error retrieving ticket", "error");
  }
}

async function cancelBooking(bookingId) {
  if (!confirm("Are you sure you want to cancel this booking? Your seats will be released.")) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/bookings/${bookingId}/cancel`, {
      method: "POST"
    });
    const data = await res.json();

    if (!res.ok) {
      showToast(data.error || "Failed to cancel booking", "error");
      return;
    }

    showToast("Booking cancelled and seats released", "success");
    loadBookingsCount();
    openMyBookingsModal(); // Refresh list

  } catch (err) {
    console.error("Cancellation error", err);
    showToast("Error cancelling booking", "error");
  }
}

// ==========================================================================
// Admin: Add New Event
// ==========================================================================
async function handleAddEventSubmit(e) {
  e.preventDefault();

  const title = document.getElementById("adminTitle").value.trim();
  const category = document.getElementById("adminCategory").value;
  const language = document.getElementById("adminLanguage").value.trim();
  const genre = document.getElementById("adminGenre").value.trim();
  const duration = document.getElementById("adminDuration").value.trim();
  const rating = parseFloat(document.getElementById("adminRating").value) || 8.5;
  const posterUrl = document.getElementById("adminPosterUrl").value.trim();
  const description = document.getElementById("adminDesc").value.trim();
  const cast = document.getElementById("adminCast").value.trim();
  const vipPrice = parseFloat(document.getElementById("adminVipPrice").value) || 500;
  const platPrice = parseFloat(document.getElementById("adminPlatPrice").value) || 300;
  const goldPrice = parseFloat(document.getElementById("adminGoldPrice").value) || 180;

  if (!title) {
    showToast("Please enter event title", "error");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        category,
        language,
        genre,
        duration,
        rating,
        poster_url: posterUrl,
        description,
        cast_crew: cast,
        price_vip: vipPrice,
        price_platinum: platPrice,
        price_gold: goldPrice
      })
    });

    const data = await res.json();
    if (!res.ok) {
      showToast(data.error || "Failed to add event", "error");
      return;
    }

    showToast("New Event created & shows scheduled!", "success");
    closeModal("adminModal");
    document.getElementById("addEventForm").reset();
    loadEvents();

  } catch (err) {
    console.error("Add event error", err);
    showToast("Error adding event", "error");
  }
}

// ==========================================================================
// Modal Helpers & Toasts
// ==========================================================================
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add("active");
    document.body.style.overflow = "hidden";
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove("active");
    if (!document.querySelector(".modal-overlay.active")) {
      document.body.style.overflow = "auto";
    }
  }
}

function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type === 'success' ? 'toast-success' : type === 'error' ? 'toast-error' : ''}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

