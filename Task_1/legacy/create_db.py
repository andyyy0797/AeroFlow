# To all: 除非你玩壞咗個 SQLite DB，如果唔係唔使理呢個 File。

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "aeroflow.db"

db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

cursor.execute('DROP TABLE IF EXISTS users')
cursor.execute('DROP TABLE IF EXISTS flights')
cursor.execute('DROP TABLE IF EXISTS bookings')

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

cursor.execute(
    '''
    INSERT INTO users (
        user_id, email, password, first_name, last_name,
        gender, nationality, date_of_birth, is_admin
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''',
    (
        'admin',
        'admin@aeroflow.com',
        '12345678',
        'System',
        'Admin',
        'Prefer not to say',
        'N/A',
        '1990-01-01',
        1,
    )
)

demo_flights = [
    (
        'AF101',
        'Hong Kong (HKG)',
        'Tokyo, Japan (HND)',
        '2026-04-10 08:30',
        '2026-04-10 13:05',
        'economy,premium_economy,business,first',
        1280.0,
    ),
    (
        'AF202',
        'Hong Kong (HKG)',
        'Singapore (SIA)',
        '2026-04-11 09:15',
        '2026-04-11 13:05',
        'economy,premium_economy,business',
        920.0,
    ),
    (
        'AF303',
        'Hong Kong (HKG)',
        'London (LHR)',
        '2026-04-12 23:40',
        '2026-04-13 06:25',
        'economy,premium_economy,business,first',
        4680.0,
    ),
]

cursor.executemany(
    '''
    INSERT INTO flights (
        flight_number, departure, destination, departure_time,
        arrival_time, classes_available, standard_price
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''',
    demo_flights,
)

db.commit()
db.close()
print(f"Done. Database recreated at {DB_PATH}")