# To all: 除非你玩壞咗個 SQLite DB，如果唔係唔使理呢個 File。

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "aeroflow.db"

db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

cursor.execute('DROP TABLE IF EXISTS users')
cursor.execute('DROP TABLE IF EXISTS flights')
cursor.execute('DROP TABLE IF EXISTS bookings')
cursor.execute('DROP TABLE IF EXISTS sub_passengers')

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT NOT NULL,
    nationality TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS flights (
    flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_number TEXT UNIQUE NOT NULL,
    departure TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_time TEXT NOT NULL,
    arrival_time TEXT NOT NULL,
    classes_available TEXT NOT NULL,
    standard_price REAL NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS bookings (
    booking_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    flight_id INTEGER NOT NULL,
    travel_class TEXT NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (flight_id) REFERENCES flights (flight_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS sub_passengers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT NOT NULL,
    nationality TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings (booking_id) ON DELETE CASCADE
)
''')

demo_users = [
    (
        'admin',
        'admin@aeroflow.com',
        'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f',
        'System',
        'Admin',
        'Prefer not to say',
        'N/A',
        '1990-01-01',
        1,
    ),
    (
        'demouser1',
        'johndoe@me.com',
        'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f',
        'John',
        'Doe',
        'M',
        'Hong Kong, China',
        '1990-09-01',
        0,
    ),
    (
        'demouser2',
        'andywong@gmail.com',
        'ef797c8118f02dfb649607dd5d3f8c7623048c9c063d532cc95c5ed7a898a64f',
        'Andy',
        'Wong',
        'M',
        'Hong Kong, China',
        '2007-01-30',
        0,
    ),
]

cursor.executemany(
    '''
    INSERT OR IGNORE INTO users (
        user_id, email, password, first_name, last_name,
        gender, nationality, date_of_birth, is_admin
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''',
    demo_users,
)

demo_flights = [
    (
        'UO854',
        'Hong Kong (HKG)',
        'Tokyo Narita (NRT)',
        '2026-04-13 01:15',
        '2026-04-13 05:45',
        'economy:1,premium_economy:2.2',
        1350.0,
    ),
    (
        'UO653',
        'Tokyo Narita (NRT)',
        'Hong Kong (HKG)',
        '2026-04-13 21:35',
        '2026-04-14 00:30',
        'economy:1,premium_economy:2.2,business:3',
        1350.0,
    ),
    (
        'UO854',
        'Hong Kong (HKG)',
        'Tokyo Narita (NRT)',
        '2026-04-14 01:15',
        '2026-04-14 05:45',
        'economy:1,premium_economy:2.2',
        1350.0,
    ),
    (
        'UO653',
        'Tokyo Narita (NRT)',
        'Hong Kong (HKG)',
        '2026-04-14 21:35',
        '2026-04-15 00:30',
        'economy:1,premium_economy:2.2,business:3',
        1350.0,
    ),
]

cursor.executemany(
    '''
    INSERT OR IGNORE INTO flights (
        flight_number, departure, destination, departure_time,
        arrival_time, classes_available, standard_price
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''',
    demo_flights,
)

db.commit()
db.close()
print(f"Done. Database recreated at {DB_PATH}")
