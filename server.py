"""
High-Performance Local Server for BookMyShow Clone
Built using standard library Python (http.server + sqlite3)
Supports multi-threading, REST API, JSON serialization, and Static File Serving.
"""
import http.server
import socketserver
import json
import os
import re
import random
import string
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import database

PORT = int(os.environ.get("PORT", 5000))
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class BookMyShowHandler(http.server.BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        response_bytes = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def parse_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {}
        return {}

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        # 1. API Routes
        if path.startswith("/api/"):
            self.handle_api_get(path, query)
            return

        # 2. Static File Serving
        self.serve_static(path)

    def handle_api_get(self, path, query):
        conn = database.get_connection()
        cursor = conn.cursor()

        try:
            # GET /api/cities
            if path == "/api/cities":
                cursor.execute("SELECT DISTINCT city FROM venues ORDER BY city ASC")
                cities = [row["city"] for row in cursor.fetchall()]
                self.send_json({"cities": cities})
                return

            # GET /api/events
            if path == "/api/events":
                category = query.get("category", ["All"])[0]
                city = query.get("city", ["All"])[0]
                search = query.get("search", [""])[0].strip()

                sql = "SELECT * FROM events WHERE 1=1"
                params = []

                if category and category != "All":
                    sql += " AND category = ?"
                    params.append(category)

                if search:
                    sql += " AND (title LIKE ? OR genre LIKE ? OR cast_crew LIKE ?)"
                    search_wild = f"%{search}%"
                    params.extend([search_wild, search_wild, search_wild])

                sql += " ORDER BY rating DESC, id DESC"
                cursor.execute(sql, params)
                events = [dict(row) for row in cursor.fetchall()]
                self.send_json({"events": events, "count": len(events)})
                return

            # GET /api/events/<id>
            match_event = re.match(r"^/api/events/(\d+)$", path)
            if match_event:
                event_id = int(match_event.group(1))
                cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
                event = cursor.fetchone()
                if not event:
                    self.send_json({"error": "Event not found"}, 404)
                    return
                self.send_json({"event": dict(event)})
                return

            # GET /api/events/<id>/shows
            match_event_shows = re.match(r"^/api/events/(\d+)/shows$", path)
            if match_event_shows:
                event_id = int(match_event_shows.group(1))
                date_filter = query.get("date", [""])[0]
                city_filter = query.get("city", ["All"])[0]

                sql = """
                SELECT s.*, v.name as venue_name, v.city as venue_city, v.address as venue_address, v.screens_info
                FROM shows s
                JOIN venues v ON s.venue_id = v.id
                WHERE s.event_id = ?
                """
                params = [event_id]

                if date_filter:
                    sql += " AND s.show_date = ?"
                    params.append(date_filter)

                if city_filter and city_filter != "All":
                    sql += " AND v.city = ?"
                    params.append(city_filter)

                sql += " ORDER BY s.show_date ASC, s.show_time ASC"
                cursor.execute(sql, params)
                rows = cursor.fetchall()

                # Group shows by venue for BookMyShow UX
                venues_dict = {}
                for r in rows:
                    v_id = r["venue_id"]
                    if v_id not in venues_dict:
                        venues_dict[v_id] = {
                            "venue_id": v_id,
                            "venue_name": r["venue_name"],
                            "venue_city": r["venue_city"],
                            "venue_address": r["venue_address"],
                            "screens_info": r["screens_info"],
                            "shows": []
                        }
                    venues_dict[v_id]["shows"].append({
                        "show_id": r["id"],
                        "show_date": r["show_date"],
                        "show_time": r["show_time"],
                        "format": r["format"],
                        "price_vip": r["price_vip"],
                        "price_platinum": r["price_platinum"],
                        "price_gold": r["price_gold"]
                    })

                self.send_json({
                    "event_id": event_id,
                    "date": date_filter,
                    "venues": list(venues_dict.values())
                })
                return

            # GET /api/shows/<id> (seat map & show details)
            match_show = re.match(r"^/api/shows/(\d+)$", path)
            if match_show:
                show_id = int(match_show.group(1))
                cursor.execute("""
                SELECT s.*, e.title as event_title, e.category, e.poster_url, e.duration, e.language,
                       v.name as venue_name, v.city as venue_city, v.address as venue_address
                FROM shows s
                JOIN events e ON s.event_id = e.id
                JOIN venues v ON s.venue_id = v.id
                WHERE s.id = ?
                """, (show_id,))
                show = cursor.fetchone()
                if not show:
                    self.send_json({"error": "Show not found"}, 404)
                    return

                # Get all booked seats for this show
                cursor.execute("SELECT seat_code FROM booked_seats WHERE show_id = ?", (show_id,))
                booked_seats = [row["seat_code"] for row in cursor.fetchall()]

                self.send_json({
                    "show": dict(show),
                    "booked_seats": booked_seats
                })
                return

            # GET /api/bookings
            if path == "/api/bookings":
                cursor.execute("""
                SELECT b.*, e.title as event_title, e.poster_url, s.show_date, s.show_time, s.format,
                       v.name as venue_name, v.city as venue_city, v.address as venue_address
                FROM bookings b
                JOIN shows s ON b.show_id = s.id
                JOIN events e ON s.event_id = e.id
                JOIN venues v ON s.venue_id = v.id
                ORDER BY b.id DESC
                """)
                bookings = [dict(row) for row in cursor.fetchall()]
                self.send_json({"bookings": bookings})
                return

            # GET /api/bookings/<id_or_code>
            match_booking = re.match(r"^/api/bookings/([^/]+)$", path)
            if match_booking:
                param = match_booking.group(1)
                if param.isdigit():
                    cursor.execute("""
                    SELECT b.*, e.title as event_title, e.poster_url, e.duration, e.language,
                           s.show_date, s.show_time, s.format,
                           v.name as venue_name, v.city as venue_city, v.address as venue_address
                    FROM bookings b
                    JOIN shows s ON b.show_id = s.id
                    JOIN events e ON s.event_id = e.id
                    JOIN venues v ON s.venue_id = v.id
                    WHERE b.id = ?
                    """, (int(param),))
                else:
                    cursor.execute("""
                    SELECT b.*, e.title as event_title, e.poster_url, e.duration, e.language,
                           s.show_date, s.show_time, s.format,
                           v.name as venue_name, v.city as venue_city, v.address as venue_address
                    FROM bookings b
                    JOIN shows s ON b.show_id = s.id
                    JOIN events e ON s.event_id = e.id
                    JOIN venues v ON s.venue_id = v.id
                    WHERE b.booking_code = ?
                    """, (param,))
                booking = cursor.fetchone()
                if not booking:
                    self.send_json({"error": "Booking not found"}, 404)
                    return
                self.send_json({"booking": dict(booking)})
                return

            # GET /api/stats (Admin Stats)
            if path == "/api/stats":
                cursor.execute("SELECT COUNT(*) FROM events")
                total_events = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'CONFIRMED'")
                total_bookings = cursor.fetchone()[0]

                cursor.execute("SELECT COALESCE(SUM(seat_count), 0) FROM bookings WHERE status = 'CONFIRMED'")
                total_tickets = cursor.fetchone()[0]

                cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM bookings WHERE status = 'CONFIRMED'")
                total_revenue = cursor.fetchone()[0]

                self.send_json({
                    "total_events": total_events,
                    "total_bookings": total_bookings,
                    "total_tickets": total_tickets,
                    "total_revenue": round(total_revenue, 2)
                })
                return

            self.send_json({"error": "Endpoint not found"}, 404)

        finally:
            conn.close()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        body = self.parse_body()

        conn = database.get_connection()
        cursor = conn.cursor()

        try:
            # POST /api/bookings (Book seats)
            if path == "/api/bookings":
                show_id = body.get("show_id")
                seats = body.get("seats", [])
                user_name = body.get("user_name", "").strip()
                user_email = body.get("user_email", "").strip()
                user_phone = body.get("user_phone", "").strip()
                snacks = body.get("snacks", "")
                subtotal = float(body.get("subtotal", 0.0))
                tax_and_fees = float(body.get("tax_and_fees", 0.0))
                total_amount = float(body.get("total_amount", 0.0))
                payment_method = body.get("payment_method", "UPI")

                if not show_id or not seats or not user_name or not user_phone:
                    self.send_json({"error": "Missing required fields (show, seats, name, phone)"}, 400)
                    return

                # Atomic seat conflict check
                placeholders = ",".join("?" for _ in seats)
                check_sql = f"SELECT seat_code FROM booked_seats WHERE show_id = ? AND seat_code IN ({placeholders})"
                cursor.execute(check_sql, [show_id] + seats)
                conflicts = [row["seat_code"] for row in cursor.fetchall()]

                if conflicts:
                    self.send_json({
                        "error": f"Seats already booked: {', '.join(conflicts)}. Please select other seats."
                    }, 409)
                    return

                # Generate unique booking reference code (e.g. BMS-7X82A4)
                code_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
                booking_code = f"BMS-{code_suffix}"
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                seats_str = ", ".join(seats)
                seat_count = len(seats)

                cursor.execute("""
                INSERT INTO bookings (
                    booking_code, show_id, user_name, user_email, user_phone,
                    seats, seat_count, snacks, subtotal, tax_and_fees,
                    total_amount, payment_method, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?)
                """, (
                    booking_code, show_id, user_name, user_email, user_phone,
                    seats_str, seat_count, str(snacks), subtotal, tax_and_fees,
                    total_amount, payment_method, created_at
                ))
                booking_id = cursor.lastrowid

                # Lock seats in booked_seats table
                for seat in seats:
                    cursor.execute("""
                    INSERT INTO booked_seats (show_id, seat_code, booking_id)
                    VALUES (?, ?, ?)
                    """, (show_id, seat, booking_id))

                conn.commit()

                # Fetch full details for receipt
                cursor.execute("""
                SELECT b.*, e.title as event_title, e.poster_url, e.duration, e.language,
                       s.show_date, s.show_time, s.format,
                       v.name as venue_name, v.city as venue_city, v.address as venue_address
                FROM bookings b
                JOIN shows s ON b.show_id = s.id
                JOIN events e ON s.event_id = e.id
                JOIN venues v ON s.venue_id = v.id
                WHERE b.id = ?
                """, (booking_id,))
                confirmed_booking = cursor.fetchone()

                self.send_json({
                    "success": True,
                    "message": "Booking confirmed successfully!",
                    "booking": dict(confirmed_booking)
                }, 201)
                return

            # POST /api/bookings/<id>/cancel
            match_cancel = re.match(r"^/api/bookings/(\d+)/cancel$", path)
            if match_cancel:
                booking_id = int(match_cancel.group(1))
                cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
                booking = cursor.fetchone()
                if not booking:
                    self.send_json({"error": "Booking not found"}, 404)
                    return

                if booking["status"] == "CANCELLED":
                    self.send_json({"error": "Booking is already cancelled"}, 400)
                    return

                # Delete from booked_seats to free up seats for others
                cursor.execute("DELETE FROM booked_seats WHERE booking_id = ?", (booking_id,))
                # Mark as cancelled
                cursor.execute("UPDATE bookings SET status = 'CANCELLED' WHERE id = ?", (booking_id,))
                conn.commit()

                self.send_json({
                    "success": True,
                    "message": "Booking cancelled and seats released successfully."
                })
                return

            # POST /api/events (Admin: Create new event)
            if path == "/api/events":
                title = body.get("title", "").strip()
                category = body.get("category", "Movies").strip()
                language = body.get("language", "English, Hindi").strip()
                genre = body.get("genre", "Drama").strip()
                duration = body.get("duration", "2h 15m").strip()
                rating = float(body.get("rating", 8.5))
                poster_url = body.get("poster_url", "").strip() or "https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?auto=format&fit=crop&w=600&q=80"
                banner_url = body.get("banner_url", "").strip() or "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80"
                description = body.get("description", "").strip()
                cast_crew = body.get("cast_crew", "").strip()
                city = body.get("city", "All").strip()
                price_vip = float(body.get("price_vip", 500.0))
                price_plat = float(body.get("price_platinum", 300.0))
                price_gold = float(body.get("price_gold", 180.0))

                if not title:
                    self.send_json({"error": "Event title is required"}, 400)
                    return

                cursor.execute("""
                INSERT INTO events (title, category, language, rating, votes_count, duration, genre, release_date, banner_url, poster_url, description, cast_crew, city)
                VALUES (?, ?, ?, ?, '1K+', ?, ?, date('now'), ?, ?, ?, ?, ?)
                """, (title, category, language, rating, duration, genre, banner_url, poster_url, description, cast_crew, city))
                new_event_id = cursor.lastrowid

                # Generate shows for next 5 days across venues
                cursor.execute("SELECT id FROM venues LIMIT 3")
                v_rows = cursor.fetchall()
                today = datetime.now()
                show_times = ["11:00 AM", "03:30 PM", "07:00 PM", "10:30 PM"]

                for v in v_rows:
                    for day_offset in range(5):
                        s_date = (today + timedelta(days=day_offset)).strftime("%Y-%m-%d")
                        for st in show_times:
                            cursor.execute("""
                            INSERT INTO shows (event_id, venue_id, show_date, show_time, format, price_vip, price_platinum, price_gold)
                            VALUES (?, ?, ?, ?, '2D / Dolby Atmos', ?, ?, ?)
                            """, (new_event_id, v["id"], s_date, st, price_vip, price_plat, price_gold))

                conn.commit()
                self.send_json({
                    "success": True,
                    "message": "Event and schedule created successfully!",
                    "event_id": new_event_id
                }, 201)
                return

            self.send_json({"error": "Endpoint not found"}, 404)

        finally:
            conn.close()

    def serve_static(self, path):
        if path == "/" or path == "":
            path = "/index.html"

        # Sanitize path
        path = path.lstrip("/")
        full_path = os.path.normpath(os.path.join(PUBLIC_DIR, path))

        # Security check: must be inside PUBLIC_DIR
        if not full_path.startswith(PUBLIC_DIR):
            self.send_json({"error": "Forbidden"}, 403)
            return

        if not os.path.isfile(full_path):
            # Fallback to index.html for SPA feel
            full_path = os.path.join(PUBLIC_DIR, "index.html")
            if not os.path.isfile(full_path):
                self.send_json({"error": "File not found"}, 404)
                return

        # Determine MIME type
        ext = os.path.splitext(full_path)[1].lower()
        mime_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".woff": "font/woff",
            ".woff2": "font/woff2"
        }
        content_type = mime_types.get(ext, "application/octet-stream")

        try:
            with open(full_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

def run():
    database.init_db()
    server_address = ("0.0.0.0", PORT)
    httpd = ThreadedHTTPServer(server_address, BookMyShowHandler)
    print(f"==================================================")
    print(f"🎬 BookMyShow Event Management Server Running!")
    print(f"🔗 Access URL: http://localhost:{PORT}")
    print(f"💾 Local Database: bookmyshow.db (SQLite)")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        httpd.server_close()

if __name__ == "__main__":
    run()

