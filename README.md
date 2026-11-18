# 🎟️ ShowSphere - Online Event & Ticket Booking System (BookMyShow Clone)

A high-performance, responsive online event management and ticket booking platform built with modern, cinematic UI styling inspired by **BookMyShow**.

**100% Local & Self-Contained:** Uses a local **SQLite database (`bookmyshow.db`)** and Python's built-in multi-threaded HTTP server. **No external databases or third-party cloud services are required.**

---

## ✨ Key Features

1. **🎬 Event & Show Discovery:**
   - Browse across 5 categories: **Movies**, **Music Concerts**, **Standup Comedy**, **Live Sports**, and **Plays & Theater**.
   - Real-time search across titles, cast, artists, and genres.
   - City selector (Mumbai, Delhi-NCR, Bengaluru, Hyderabad, Chennai, Pune).
   - Rich movie/event cards with ratings, vote counts, format badges (IMAX 3D, 4DX, Dolby Atmos), and duration.

2. **📅 Date & Venue Picker:**
   - Interactive date ribbon (Today, Tomorrow, and upcoming 5 days).
   - Filter by theater / venue with screen technical specifications (IMAX with Laser, Dolby Atmos 7.1, 4DX).
   - Color-coded showtimes with instant availability feedback.

3. **🪑 Interactive Seat Map (True BookMyShow Experience):**
   - Curved silver projection screen visualizer with glowing light projection beam (*"Cinema Screen This Way"*).
   - **Distinct Seat Tiers:**
     - 👑 **VIP Recliner** (Rows A, B — Plush leather styling, ₹600)
     - 💎 **Platinum Club** (Rows C, D, E — ₹350)
     - ⭐ **Gold Executive** (Rows F, G, H, J, K — ₹200)
   - Left aisle, center section, and right aisle layout with row numbers (1 to 16).
   - Real-time status legend: **Available**, **Selected** (Ruby red glow), and **Sold/Booked** (disabled).
   - Dynamic floating summary bar calculating ticket count and total bill in real time.

4. **🍿 Food & Beverage (F&B) Combos:**
   - Pre-order Caramel Popcorn, Mexican Cheese Nachos, Chilled Beverages, and Blockbuster Tub Combos with quantity controls (+ / -).
   - Optional "Skip" or "Add & Proceed" options.

5. **💳 Checkout & Simulated Payment Gateway:**
   - Itemized bill: Ticket subtotal, F&B snacks, convenience fee, and 18% GST.
   - Contact details form (Name, Email, Mobile).
   - Realistic payment methods:
     - ⚡ **UPI** (Google Pay, PhonePe, Paytm, BHIM)
     - 💳 **Credit / Debit Cards** (with Card number, Expiry, CVV)
     - 🏦 **Net Banking** (HDFC, ICICI, SBI, Axis Bank, Kotak)

6. **🎫 Confirmed Digital E-Ticket with Local QR Code:**
   - High-tech boarding pass cinema ticket with perforated divider.
   - Real dynamically generated **SVG QR Code** (zero external CDNs required).
   - Booking reference ID (e.g. `BMS-8X492A`) and entry barcode.
   - One-click **Print / Save PDF Ticket** formatted for clean printing (`@media print`).

7. **📋 "My Bookings" & Cancellation:**
   - Persistent booking history stored in SQLite.
   - "View Ticket" button to re-open and reprint tickets anytime.
   - "Cancel Booking" feature that automatically frees up the booked seats in SQLite so they become immediately available for other users.

8. **🛠️ Admin / Event Organizer Hub:**
   - Built-in form to add new events with title, category, language, genre, poster URL, cast, and custom VIP/Platinum/Gold seat prices.
   - Automatically populates showtimes across venues for the next 5 days.

---

## 🚀 How to Run the Website

### Method 1: Double-Click the Launcher (Windows)
Double-click **`run.bat`** in the project folder.

### Method 2: Command Line (PowerShell / Terminal)
```bash
python server.py
```

Then open your browser and navigate to:
```
http://localhost:5000
```

---

## 📁 Project Structure

```
website/
├── database.py         # SQLite schema initialization and seed data generator
├── server.py           # Multi-threaded REST API server & static asset handler
├── bookmyshow.db       # Local SQLite Database (auto-created on first run)
├── run.bat             # One-click Windows launcher
├── README.md           # Documentation
└── public/
    ├── index.html      # Main BookMyShow application HTML
    ├── css/
    │   └── style.css   # Dark cinematic BookMyShow stylesheet & seat styling
    └── js/
        ├── app.js      # Frontend controller, seat selection & checkout logic
        └── qrcode.js   # Pure JS standalone SVG QR Code generator (no CDN needed)
```

---

## 🗄️ Local Database Schema (`bookmyshow.db`)

- **`events`**: Catalog of movies, concerts, comedy, and sports with ratings and posters.
- **`venues`**: Theaters, auditoriums, and stadiums with address and screen formats.
- **`shows`**: Scheduled showtimes per event per venue across dates with tier prices.
- **`bookings`**: Confirmed customer transactions, booking references, attendee info, and status.
- **`booked_seats`**: Real-time seat occupancy locking table preventing duplicate bookings.

