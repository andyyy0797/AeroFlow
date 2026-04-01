import os
import sqlite3
from pathlib import Path
from datetime import datetime

from dataLayer import Admin, Passenger, Flight, defaultClasses
from utils import hashPassword


class DatabaseManager:
    def __init__(self, db_name="aeroflow.db"):
        self.base_dir = Path(__file__).parent
        self.dbPath = self.base_dir / db_name
        self.db_name = str(self.dbPath)
        self.checkDatabaseExists()

    def getConnection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def checkDatabaseExists(self):
        if not self.dbPath.exists():
            createDbScript = self.base_dir / "legacy" / "create_db.py"
            if createDbScript.exists() == False:
                print("Error: Missing database script")
            else:
                os.system("uv run " + str(createDbScript))

        with self.getConnection() as conn:
            conn.execute('''
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
            bookingColumns = [row["name"] for row in conn.execute("PRAGMA table_info(bookings)").fetchall()]
            if "is_deleted" not in bookingColumns:
                conn.execute("ALTER TABLE bookings ADD COLUMN is_deleted INTEGER NOT NULL DEFAULT 0")
            conn.commit()

    def registerUser(self, user):
        normalizedEmail = user.email.strip().lower()
        hashedPassword = hashPassword(user.password)
        with self.getConnection() as conn:
            existing = conn.execute(
                "SELECT 1 FROM users WHERE email = ?",
                (normalizedEmail,)
            ).fetchone()
            if existing:
                return False, "Email already registered"

            conn.execute(
                """
                INSERT INTO users (
                    user_id, email, password, first_name, last_name,
                    gender, nationality, date_of_birth, is_admin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.userID,
                    normalizedEmail,
                    hashedPassword,
                    user.firstName,
                    user.lastName,
                    user.gender,
                    user.nationality,
                    user.dateOfBirth,
                    user.isAdmin,
                )
            )
            conn.commit()
        user.password = hashedPassword
        user.email = normalizedEmail
        return True, "User registered successfully"

    def authenticateUser(self, email, password):
        normalizedEmail = email.strip().lower()
        hashedPassword = hashPassword(password)
        with self.getConnection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (normalizedEmail,)
            ).fetchone()

        if row is None:
            return None, "Email not registered"
        if row["password"] != hashedPassword:
            return None, "Wrong password"

        userClass = Admin if row["is_admin"] else Passenger
        user = userClass(
            email=row["email"],
            password=row["password"],
            firstName=row["first_name"],
            lastName=row["last_name"],
            gender=row["gender"],
            nationality=row["nationality"],
            dateOfBirth=row["date_of_birth"],
            userID=row["user_id"],
        )
        return user, "Login successful"

    def newFlight(self, flight):
        classesSerialized = self.serializeClassRatios(flight.classRatios)
        with self.getConnection() as conn:
            conn.execute(
                """
                INSERT INTO flights (
                    flight_number, departure, destination, departure_time,
                    arrival_time, classes_available, standard_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    flight.flightNumber,
                    flight.departure,
                    flight.destination,
                    flight.departureTime,
                    flight.arrivalTime,
                    classesSerialized,
                    float(flight.standardPrice),
                )
            )
            conn.commit()

    def parseClassRatios(self, classesSerialized: str) -> dict[str, float]:
        classRatios = {}
        for rawItem in classesSerialized.split(","):
            item = rawItem.strip()
            if not item:
                continue
            if ":" in item:
                className, ratioText = item.split(":", 1)
                normalizedName = className.strip().lower()
                try:
                    ratio = float(ratioText.strip())
                except ValueError:
                    continue
            else:
                normalizedName = item.strip().lower()
                ratio = defaultClasses.get(normalizedName)
                if ratio is None:
                    continue
            if normalizedName:
                classRatios[normalizedName] = ratio
        return classRatios

    def serializeClassRatios(self, classRatios: dict[str, float]) -> str:
        return ",".join(f"{className}:{float(ratio):g}" for className, ratio in classRatios.items())

    def searchFlights(self, departure, destination, date):
        departure = departure.strip().lower()
        destination = destination.strip().lower()
        date = date.strip()
        with self.getConnection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM flights
                WHERE LOWER(departure) = ?
                  AND LOWER(destination) = ?
                  AND departure_time LIKE ?
                ORDER BY departure_time ASC
                """,
                (departure, destination, f"{date}%")
            ).fetchall()

        results = []
        for row in rows:
            classRatios = self.parseClassRatios(row["classes_available"])
            results.append(
                Flight(
                    flightNumber=row["flight_number"],
                    departure=row["departure"],
                    destination=row["destination"],
                    departureTime=row["departure_time"],
                    arrivalTime=row["arrival_time"],
                    classesAvailable=list(classRatios.keys()),
                    classRatios=classRatios,
                    standardPrice=row["standard_price"],
                    flightID=row["flight_id"],
                )
            )
        return results

    def createBooking(self, booking):
        with self.getConnection() as conn:
            conn.execute(
                """
                INSERT INTO bookings (booking_id, user_id, flight_id, travel_class, price)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    booking.bookingID,
                    booking.userID,
                    booking.flightID,
                    booking.travel_class,
                    float(booking.price),
                )
            )
            for sub in booking.sub_passengers:
                conn.execute(
                    """
                    INSERT INTO sub_passengers (booking_id, first_name, last_name, gender, nationality, date_of_birth)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        booking.bookingID,
                        sub.firstName,
                        sub.lastName,
                        sub.gender,
                        sub.nationality,
                        sub.dateOfBirth,
                    )
                )
            conn.commit()

    def fetchUserBookings(self, userID):
        with self.getConnection() as conn:
            rows = conn.execute(
                """
                  SELECT b.booking_id, b.user_id, b.flight_id, b.travel_class, b.price, b.is_deleted,
                      f.flight_number, f.departure, f.destination, f.departure_time, f.arrival_time
                FROM bookings b
                  JOIN flights f ON b.flight_id = f.flight_id
                  WHERE b.user_id = ?
                  AND b.is_deleted = 0
                  ORDER BY f.departure_time ASC
                """,
                (userID,)
            ).fetchall()
        return rows

    def fetchAllActiveBookings(self):
        with self.getConnection() as conn:
            rows = conn.execute(
                """
                SELECT b.booking_id, b.user_id, b.flight_id, b.travel_class, b.price, b.is_deleted,
                       u.email AS user_email, u.first_name, u.last_name,
                       f.flight_number, f.departure, f.destination, f.departure_time, f.arrival_time, f.classes_available, f.standard_price
                FROM bookings b
                  JOIN users u ON b.user_id = u.user_id
                  JOIN flights f ON b.flight_id = f.flight_id
                WHERE b.is_deleted = 0
                ORDER BY f.departure_time ASC
                """
            ).fetchall()
        return rows

    def fetchActiveBookingByID(self, bookingID):
        with self.getConnection() as conn:
            row = conn.execute(
                """
                SELECT b.booking_id, b.user_id, b.flight_id, b.travel_class, b.price, b.is_deleted,
                       u.email AS user_email, u.first_name, u.last_name,
                       f.flight_number, f.departure, f.destination, f.departure_time, f.arrival_time, f.classes_available, f.standard_price
                FROM bookings b
                  JOIN users u ON b.user_id = u.user_id
                  JOIN flights f ON b.flight_id = f.flight_id
                WHERE b.booking_id = ?
                  AND b.is_deleted = 0
                """,
                (bookingID,)
            ).fetchone()
        return row

    def fetchAllFlights(self):
        with self.getConnection() as conn:
            rows = conn.execute(
                """
                SELECT flight_id, flight_number, departure, destination, departure_time, arrival_time, classes_available, standard_price
                FROM flights
                ORDER BY departure_time ASC
                """
            ).fetchall()
        return rows

    def fetchFlightByID(self, flightID):
        with self.getConnection() as conn:
            row = conn.execute(
                """
                SELECT flight_id, flight_number, departure, destination, departure_time, arrival_time, classes_available, standard_price
                FROM flights
                WHERE flight_id = ?
                """,
                (flightID,)
            ).fetchone()
        return row

    def updateFlight(self, flightID, flight):
        classesSerialized = self.serializeClassRatios(flight.classRatios)
        with self.getConnection() as conn:
            conn.execute(
                """
                UPDATE flights
                SET flight_number = ?, departure = ?, destination = ?, departure_time = ?, arrival_time = ?, classes_available = ?, standard_price = ?
                WHERE flight_id = ?
                """,
                (
                    flight.flightNumber,
                    flight.departure,
                    flight.destination,
                    flight.departureTime,
                    flight.arrivalTime,
                    classesSerialized,
                    float(flight.standardPrice),
                    flightID,
                )
            )
            conn.commit()

    def hasBookingsForFlight(self, flightID):
        with self.getConnection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS total FROM bookings WHERE flight_id = ?",
                (flightID,)
            ).fetchone()
        return int(row["total"]) > 0

    def deleteFlight(self, flightID):
        if self.hasBookingsForFlight(flightID):
            return False, "Cannot delete a flight with existing bookings."
        with self.getConnection() as conn:
            result = conn.execute(
                "DELETE FROM flights WHERE flight_id = ?",
                (flightID,)
            )
            conn.commit()
        if result.rowcount == 0:
            return False, "Flight not found."
        return True, "Flight deleted."

    def fetchAdminOverview(self):
        today = datetime.now().strftime("%Y-%m-%d")
        with self.getConnection() as conn:
            totalFlights = conn.execute("SELECT COUNT(*) AS total FROM flights").fetchone()["total"]
            futureFlights = conn.execute(
                "SELECT COUNT(*) AS total FROM flights WHERE departure_time >= ?",
                (today,)
            ).fetchone()["total"]
            totalBookings = conn.execute("SELECT COUNT(*) AS total FROM bookings WHERE is_deleted = 0").fetchone()["total"]
        return {
            "totalFlights": totalFlights,
            "futureFlights": futureFlights,
            "totalBookings": totalBookings,
        }

    def fetchSubPassengersByBooking(self, bookingID):
        with self.getConnection() as conn:
            rows = conn.execute(
                """
                SELECT id, first_name, last_name, gender, nationality, date_of_birth
                FROM sub_passengers
                WHERE booking_id = ?
                ORDER BY id ASC
                """,
                (bookingID,)
            ).fetchall()
        return rows

    def replaceSubPassengersForBooking(self, bookingID, subPassengers):
        with self.getConnection() as conn:
            conn.execute(
                "DELETE FROM sub_passengers WHERE booking_id = ?",
                (bookingID,)
            )
            for sub in subPassengers:
                conn.execute(
                    """
                    INSERT INTO sub_passengers (booking_id, first_name, last_name, gender, nationality, date_of_birth)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        bookingID,
                        sub["firstName"],
                        sub["lastName"],
                        sub["gender"],
                        sub["nationality"],
                        sub["dateOfBirth"],
                    )
                )
            conn.commit()
        return True, "Sub passengers updated"

    def updateProfile(self, userID, updateField, newInfo):
        allowedFields = {
            "password": "password",
            "firstName": "first_name",
            "lastName": "last_name",
            "gender": "gender",
            "nationality": "nationality",
            "dateOfBirth": "date_of_birth",
        }
        columnName = allowedFields.get(updateField)
        if not columnName:
            return False, "Invalid profile field"
        valueToSave = hashPassword(newInfo) if updateField == "password" else newInfo

        with self.getConnection() as conn:
            conn.execute(
                f"UPDATE users SET {columnName} = ? WHERE user_id = ?",
                (valueToSave, userID)
            )
            conn.commit()
        return True, "Profile updated"

    def cancelBooking(self, bookingID, userID=None):
        with self.getConnection() as conn:
            if userID:
                result = conn.execute(
                    "UPDATE bookings SET is_deleted = 1 WHERE booking_id = ? AND user_id = ? AND is_deleted = 0",
                    (bookingID, userID)
                )
            else:
                result = conn.execute(
                    "UPDATE bookings SET is_deleted = 1 WHERE booking_id = ? AND is_deleted = 0",
                    (bookingID,)
                )
            conn.commit()
        if result.rowcount == 0:
            return False, "Booking not found"
        return True, "Booking cancelled"

    def deleteBookingByAdmin(self, bookingID):
        with self.getConnection() as conn:
            result = conn.execute(
                "UPDATE bookings SET is_deleted = 1 WHERE booking_id = ? AND is_deleted = 0",
                (bookingID,)
            )
            conn.commit()
        if result.rowcount == 0:
            return False, "Booking not found"
        return True, "Booking deleted"

    def updateBookingTravelClass(self, bookingID, newTravelClass):
        with self.getConnection() as conn:
            bookingRow = conn.execute(
                """
                SELECT b.booking_id, b.flight_id, b.travel_class, b.is_deleted, f.classes_available, f.standard_price
                FROM bookings b
                  JOIN flights f ON b.flight_id = f.flight_id
                WHERE b.booking_id = ? AND b.is_deleted = 0
                """,
                (bookingID,)
            ).fetchone()
            if bookingRow is None:
                return False, "Booking not found"

            classRatios = self.parseClassRatios(bookingRow["classes_available"])
            normalizedClass = newTravelClass.strip().lower()
            ratio = classRatios.get(normalizedClass)
            if ratio is None:
                return False, "Selected class is not available for this flight"

            subPassengerCount = conn.execute(
                "SELECT COUNT(*) AS total FROM sub_passengers WHERE booking_id = ?",
                (bookingID,)
            ).fetchone()["total"]
            passengerCount = 1 + int(subPassengerCount)
            newPrice = float(bookingRow["standard_price"]) * float(ratio) * passengerCount
            conn.execute(
                "UPDATE bookings SET travel_class = ?, price = ? WHERE booking_id = ? AND is_deleted = 0",
                (normalizedClass, float(newPrice), bookingID)
            )
            conn.commit()
        return True, f"Booking updated. New total: ${newPrice:.2f}"

    def getLocations(self):
        with self.getConnection() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT departure AS location FROM flights
                UNION
                SELECT DISTINCT destination AS location FROM flights
                """
            ).fetchall()
        return [row["location"].title() for row in rows if row["location"]]

    def getFutureLocations(self):
        today = datetime.now().strftime("%Y-%m-%d")
        with self.getConnection() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT departure AS location FROM flights WHERE departure_time >= ?
                UNION
                SELECT DISTINCT destination AS location FROM flights WHERE departure_time >= ?
                """,
                (today, today)
            ).fetchall()
        return [row["location"].title() for row in rows if row["location"]]
