# To all: 除非你玩壞咗個 SQLite DB，如果唔係唔使理呢個 File。

import sqlite3

db = sqlite3.connect('aeroflow.db')
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
    gender TEXT,
    nationality TEXT,
    dob DATE,
    is_admin INTEGER NOT NULL DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS flights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_number TEXT UNIQUE NOT NULL,
    departure TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_time DATETIME NOT NULL,
    arrival_time DATETIME NOT NULL,
    standard_price REAL NOT NULL,
    classes_available TEXT
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
    FOREIGN KEY (flight_id) REFERENCES flights (id)
)
''')

db.commit()
db.close()
print("Done.")