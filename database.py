"""
Database schema and initialization for BookMyShow Event Management System.
Uses local SQLite database: bookmyshow.db
"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bookmyshow.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Events Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL, -- Movies, Concerts, Comedy, Sports, Plays
        language TEXT DEFAULT 'English, Hindi',
        rating REAL DEFAULT 9.0,
        votes_count TEXT DEFAULT '25K+',
        duration TEXT DEFAULT '2h 30m',
        genre TEXT NOT NULL,
        release_date TEXT,
        banner_url TEXT,
        poster_url TEXT,
        description TEXT,
        cast_crew TEXT,
        city TEXT DEFAULT 'All'
    );
    """)

    # 2. Venues Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS venues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        address TEXT NOT NULL,
        screens_info TEXT DEFAULT 'Screen 1 (Dolby Atmos 7.1), Screen 2 (IMAX 4K)'
    );
    """)

    # 3. Shows Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        venue_id INTEGER NOT NULL,
        show_date TEXT NOT NULL, -- YYYY-MM-DD
        show_time TEXT NOT NULL, -- e.g. 10:30 AM, 02:15 PM, 06:45 PM, 10:00 PM
        format TEXT DEFAULT 'IMAX 3D',
        price_vip REAL DEFAULT 600.0,
        price_platinum REAL DEFAULT 350.0,
        price_gold REAL DEFAULT 200.0,
        FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE,
        FOREIGN KEY (venue_id) REFERENCES venues (id) ON DELETE CASCADE
    );
    """)

    # 4. Bookings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_code TEXT UNIQUE NOT NULL,
        show_id INTEGER NOT NULL,
        user_name TEXT NOT NULL,
        user_email TEXT NOT NULL,
        user_phone TEXT NOT NULL,
        seats TEXT NOT NULL, -- Comma separated seat codes: e.g. "A4, A5"
        seat_count INTEGER NOT NULL,
        snacks TEXT, -- JSON string or comma separated
        subtotal REAL NOT NULL,
        tax_and_fees REAL NOT NULL,
        total_amount REAL NOT NULL,
        payment_method TEXT DEFAULT 'UPI',
        status TEXT DEFAULT 'CONFIRMED', -- CONFIRMED, CANCELLED
        created_at TEXT NOT NULL,
        FOREIGN KEY (show_id) REFERENCES shows (id) ON DELETE CASCADE
    );
    """)

    # 5. Booked Seats Table (for rapid conflict checking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS booked_seats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        show_id INTEGER NOT NULL,
        seat_code TEXT NOT NULL,
        booking_id INTEGER NOT NULL,
        FOREIGN KEY (show_id) REFERENCES shows (id) ON DELETE CASCADE,
        FOREIGN KEY (booking_id) REFERENCES bookings (id) ON DELETE CASCADE,
        UNIQUE(show_id, seat_code)
    );
    """)

    conn.commit()
    conn.close()
    seed_sample_data_if_empty()

def seed_sample_data_if_empty():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM events")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    print("Seeding initial BookMyShow events, venues, and shows...")

    # Sample Venues
    venues = [
        ("PVR INOX: Phoenix Palladium", "Mumbai", "462 Senapati Bapat Marg, Lower Parel, Mumbai", "Screen 1 (IMAX with Laser), Screen 2 (PVR LUXE)"),
        ("Cinépolis: Grand Mall", "Mumbai", "Veera Desai Road, Andheri West, Mumbai", "Screen 4DX, Screen VIP Atmos"),
        ("PVR Director's Cut: Ambience Mall", "Delhi-NCR", "Vasant Kunj, Nelson Mandela Marg, New Delhi", "Audi 1 (Dolby Cinema), Audi 2 (Gold Class)"),
        ("Miraj Cinemas: Maximum Mall", "Delhi-NCR", "Sector 29, Gurugram, Delhi-NCR", "Screen 1 (Dolby 7.1), Screen 2 (RGB Laser)"),
        ("PVR: Forum Mall, Koramangala", "Bengaluru", "Hosur Road, Koramangala, Bengaluru", "Screen 1 (IMAX 3D), Screen 3 (P[XL] Atmos)"),
        ("Inox: Garuda Mall", "Bengaluru", "Magrath Road, Ashok Nagar, Bengaluru", "Screen 1 (Insignia), Screen 2 (Dolby Atmos)"),
        ("Prasads Multiplex & IMAX", "Hyderabad", "NTR Marg, Central Secretariat, Khairatabad, Hyderabad", "Large Screen 6 (Atmos 64-Channel), Screen 1"),
        ("PVR: Inorbit Mall, Madhapur", "Hyderabad", "Hitech City, Hyderabad", "Screen 1 (4K Laser), Screen 2 (Playhouse)"),
        ("Palazzo Cinemas: Nexus Vijaya", "Chennai", "Vadapalani, Chennai", "Screen 1 (Palazzo IMAX), Screen 3 (Dolby Atmos)"),
        ("INOX: Bund Garden", "Pune", "Central Mall, Bund Garden Road, Pune", "Screen 1 (MX4D), Screen 2 (Dolby 7.1)")
    ]

    cursor.executemany("""
    INSERT INTO venues (name, city, address, screens_info) VALUES (?, ?, ?, ?)
    """, venues)

    # Sample Events (Movies, Concerts, Standup Comedy, Sports, Plays)
    events = [
        (
            "Dune: Part Two",
            "Movies",
            "English, Hindi",
            9.3,
            "145K+",
            "2h 46m",
            "Sci-Fi, Action, Adventure",
            "2026-03-01",
            "https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=600&q=80",
            "Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family. Facing a choice between the love of his life and the fate of the known universe.",
            "Timothée Chalamet, Zendaya, Rebecca Ferguson, Javier Bardem | Directed by Denis Villeneuve",
            "All"
        ),
        (
            "Coldplay: Music of the Spheres World Tour",
            "Concerts",
            "English",
            9.8,
            "280K+",
            "3h 15m",
            "Stadium Rock, Pop, Spectacular",
            "2026-11-25",
            "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=600&q=80",
            "The world's most breathtaking stadium live show returns with hypnotic LED wristbands, cosmic pyrotechnics, and iconic anthems like 'Fix You', 'Yellow', 'Viva La Vida', and 'A Sky Full of Stars'.",
            "Chris Martin, Jonny Buckland, Guy Berryman, Will Champion",
            "All"
        ),
        (
            "Deadpool & Wolverine",
            "Movies",
            "English, Hindi, Tamil",
            8.9,
            "98K+",
            "2h 08m",
            "Action, Comedy, Superhero",
            "2026-07-26",
            "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&w=600&q=80",
            "Wolverine is recovering from his injuries when he crosses paths with the loudmouth, fourth-wall breaking Deadpool. They team up to defeat a common enemy threatening the multiverse.",
            "Ryan Reynolds, Hugh Jackman, Emma Corrin, Matthew Macfadyen | Directed by Shawn Levy",
            "All"
        ),
        (
            "Zakir Khan - Tathastu & Beyond Live",
            "Comedy",
            "Hindi",
            9.6,
            "75K+",
            "1h 45m",
            "Standup Comedy, Storytelling",
            "2026-11-28",
            "https://images.unsplash.com/photo-1585699324551-f6c309eedeca?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
            "India's beloved 'Sakht Launda' Zakir Khan delivers a brand new heartfelt stand-up special filled with nostalgic anecdotes, family drama, and gut-busting punchlines.",
            "Zakir Khan",
            "All"
        ),
        (
            "Diljit Dosanjh - Dil-Luminati Arena Tour",
            "Concerts",
            "Punjabi, Hindi",
            9.9,
            "310K+",
            "2h 45m",
            "Punjabi Beats, Hip Hop, Fusion",
            "2026-12-05",
            "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?auto=format&fit=crop&w=600&q=80",
            "The historic Dil-Luminati spectacle takes over major arenas! Experience electrifying energy, dazzling visuals, and viral chartbusters like 'Born to Shine', 'G.O.A.T.', and 'Lover'.",
            "Diljit Dosanjh & International Live Dancers",
            "All"
        ),
        (
            "Kalki 2898 AD: The Epic",
            "Movies",
            "Telugu, Hindi, Tamil, English",
            9.1,
            "160K+",
            "3h 01m",
            "Mythology, Sci-Fi, Action",
            "2026-06-27",
            "https://images.unsplash.com/photo-1578632767115-351597cf2477?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=600&q=80",
            "A modern avatar of Vishnu descends to Earth in a dystopian future to protect the world from evil forces. Groundbreaking VFX and high-octane battle sequences in stunning IMAX 3D.",
            "Prabhas, Amitabh Bachchan, Kamal Haasan, Deepika Padukone | Directed by Nag Ashwin",
            "All"
        ),
        (
            "Samay Raina: Unfiltered & Unhinged",
            "Comedy",
            "Hindi, English",
            9.4,
            "52K+",
            "1h 30m",
            "Dark Comedy, Crowd Work",
            "2026-11-22",
            "https://images.unsplash.com/photo-1527224857830-43a7acc85260?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1507676184212-d03ab07a01bf?auto=format&fit=crop&w=600&q=80",
            "Get ready for unfiltered roast sessions, razor-sharp crowd interaction, and dark humor that leaves the entire audience gasping for breath.",
            "Samay Raina",
            "All"
        ),
        (
            "IPL 2026: Grand Clash (MI vs CSK)",
            "Sports",
            "Live Commentary (Hindi & English)",
            9.7,
            "500K+",
            "4h 00m",
            "T20 Cricket, Stadium Experience",
            "2026-11-30",
            "https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1531415074968-036ba1b575da?auto=format&fit=crop&w=600&q=80",
            "The mother of all cricket rivalries! Mumbai Indians take on Chennai Super Kings in an explosive stadium atmosphere with cheerleaders, fireworks, and live DJ.",
            "Top World Cricket Stars, International Coaches & Umpires",
            "Mumbai"
        ),
        (
            "Mughal-e-Azam: The Grand Broadway Musical",
            "Plays",
            "Hindi, Urdu",
            9.5,
            "40K+",
            "2h 30m",
            "Historical Drama, Broadway, Classical Dance",
            "2026-12-10",
            "https://images.unsplash.com/photo-1507676184212-d03ab07a01bf?auto=format&fit=crop&w=1200&q=80",
            "https://images.unsplash.com/photo-1469488865564-c2de10f69f96?auto=format&fit=crop&w=600&q=80",
            "Feroz Abbas Khan's critically acclaimed stage adaptation featuring Manish Malhotra costumes, 30+ classical Kathak dancers, and mesmerizing live singing of classic songs.",
            "Directed by Feroz Abbas Khan | Costumes by Manish Malhotra",
            "All"
        )
    ]

    cursor.executemany("""
    INSERT INTO events (title, category, language, rating, votes_count, duration, genre, release_date, banner_url, poster_url, description, cast_crew, city)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, events)

    # Fetch inserted event IDs and venue IDs
    cursor.execute("SELECT id, title FROM events")
    event_rows = cursor.fetchall()

    cursor.execute("SELECT id, city FROM venues")
    venue_rows = cursor.fetchall()

    # Generate shows for the next 7 days for each event across venues
    today = datetime.now()
    show_times = ["10:15 AM", "01:45 PM", "05:30 PM", "09:00 PM", "11:15 PM"]
    formats = ["IMAX 3D Laser", "Dolby Atmos 7.1", "4DX Extreme", "2D Digital"]

    show_entries = []
    for ev in event_rows:
        ev_id = ev["id"]
        # select 2-3 venues
        for v in venue_rows[:4]:
            v_id = v["id"]
            for day_offset in range(5):
                show_date = (today + timedelta(days=day_offset)).strftime("%Y-%m-%d")
                for idx, t in enumerate(show_times[:3]):
                    fmt = formats[(ev_id + idx) % len(formats)]
                    vip_p = 600.0 if "Concerts" not in ev["title"] else 1500.0
                    plat_p = 350.0 if "Concerts" not in ev["title"] else 800.0
                    gold_p = 200.0 if "Concerts" not in ev["title"] else 450.0

                    show_entries.append((
                        ev_id,
                        v_id,
                        show_date,
                        t,
                        fmt,
                        vip_p,
                        plat_p,
                        gold_p
                    ))

    cursor.executemany("""
    INSERT INTO shows (event_id, venue_id, show_date, show_time, format, price_vip, price_platinum, price_gold)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, show_entries)

    # Let's seed some realistic pre-booked seats on the first few shows so the layout looks realistic
    cursor.execute("SELECT id FROM shows LIMIT 10")
    sample_shows = cursor.fetchall()

    sample_booked_seats = ["A4", "A5", "C7", "C8", "C9", "E1", "E2", "G10", "G11"]
    
    # We can insert a dummy booking for each of those shows
    for s in sample_shows:
        s_id = s["id"]
        cursor.execute("""
        INSERT INTO bookings (booking_code, show_id, user_name, user_email, user_phone, seats, seat_count, snacks, subtotal, tax_and_fees, total_amount, payment_method, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"BMS-SEED{s_id}",
            s_id,
            "Rahul Sharma",
            "rahul@example.com",
            "+91 98765 43210",
            ", ".join(sample_booked_seats[:4]),
            4,
            "Popcorn Large Combo",
            1400.0,
            126.0,
            1526.0,
            "UPI",
            "CONFIRMED",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        b_id = cursor.lastrowid
        for seat in sample_booked_seats[:4]:
            cursor.execute("""
            INSERT OR IGNORE INTO booked_seats (show_id, seat_code, booking_id)
            VALUES (?, ?, ?)
            """, (s_id, seat, b_id))

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    init_db()

