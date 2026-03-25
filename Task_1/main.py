import secrets
import subprocess
import sys
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Button, Label, Input, Select
from textual.screen import Screen
import sqlite3
from datetime import datetime


class User:
    def __init__(self, email, password, firstName, lastName, gender, nationality, dateOfBirth, userID=None, isAdmin=0):
        self.userID = userID if userID else secrets.token_hex(4)
        self.email = email
        self.password = password
        self.firstName = firstName
        self.lastName = lastName
        self.gender = gender
        self.nationality = nationality
        self.dateOfBirth = dateOfBirth
        self.isAdmin = isAdmin


class Admin(User):
    def __init__(self, email, password, firstName, lastName, gender, nationality, dateOfBirth, userID=None):
        super().__init__(email, password, firstName, lastName, gender, nationality, dateOfBirth, userID=userID, isAdmin=1)


class Passenger(User):
    def __init__(self, email, password, firstName, lastName, gender, nationality, dateOfBirth, userID=None):
        super().__init__(email, password, firstName, lastName, gender, nationality, dateOfBirth, userID=userID, isAdmin=0)

class Flight:
    def __init__(self, flightNumber, departure, destination, departureTime, arrivalTime, classesAvailable, standardPrice, flightID=None):
        self.flightID = flightID
        self.flightNumber = flightNumber
        self.departure = departure
        self.destination = destination
        self.departureTime = departureTime
        self.arrivalTime = arrivalTime
        self.classesAvailable = classesAvailable
        self.standardPrice = standardPrice


class Booking:
    def __init__(self, userID, flightID, travel_class, price, bookingID=None):
        self.bookingID = bookingID if bookingID else secrets.token_hex(4)
        self.userID = userID
        self.flightID = flightID
        self.travel_class = travel_class
        self.price = price

class DatabaseManager:
    def __init__(self, db_name="aeroflow.db"):
        self.base_dir = Path(__file__).parent
        self.db_path = self.base_dir / db_name
        self.db_name = str(self.db_path)
        self.checkDatabaseExists()

    def getConnection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def checkDatabaseExists(self):
        if self.db_path.exists():
            return

        create_db_script = self.base_dir / "legacy" / "create_db.py"
        if not create_db_script.exists():
            raise FileNotFoundError(f"Missing database bootstrap script: {create_db_script}")

        subprocess.run([sys.executable, str(create_db_script)], check=True)

    def registerUser(self, user):
        normalizedEmail = user.email.strip().lower()
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
                    user.password,
                    user.firstName,
                    user.lastName,
                    user.gender,
                    user.nationality,
                    user.dateOfBirth,
                    user.isAdmin,
                )
            )
            conn.commit()
        user.email = normalizedEmail
        return True, "User registered successfully"

    def authenticateUser(self, email, password):
        normalizedEmail = email.strip().lower()
        with self.getConnection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (normalizedEmail,)
            ).fetchone()

        if row is None:
            return None, "Email not registered"
        if row["password"] != password:
            return None, "Wrong password"

        user_class = Admin if row["is_admin"] else Passenger
        user = user_class(
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
        classesSerialized = ",".join(flight.classesAvailable)
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
            classesAvailable = [item.strip() for item in row["classes_available"].split(",") if item.strip()]
            results.append(
                Flight(
                    flightNumber=row["flight_number"],
                    departure=row["departure"],
                    destination=row["destination"],
                    departureTime=row["departure_time"],
                    arrivalTime=row["arrival_time"],
                    classesAvailable=classesAvailable,
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
            conn.commit()

    def fetchUserBookings(self, userID):
        with self.getConnection() as conn:
            rows = conn.execute(
                """
                  SELECT b.booking_id, b.user_id, b.flight_id, b.travel_class, b.price,
                      f.flight_number, f.departure, f.destination, f.departure_time, f.arrival_time
                FROM bookings b
                  JOIN flights f ON b.flight_id = f.flight_id
                  WHERE b.user_id = ?
                  ORDER BY f.departure_time ASC
                """,
                (userID,)
            ).fetchall()
        return rows

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

        with self.getConnection() as conn:
            conn.execute(
                f"UPDATE users SET {columnName} = ? WHERE user_id = ?",
                (newInfo, userID)
            )
            conn.commit()
        return True, "Profile updated"

    def cancelBooking(self, bookingID, userID=None):
        with self.getConnection() as conn:
            if userID:
                result = conn.execute(
                    "DELETE FROM bookings WHERE booking_id = ? AND user_id = ?",
                    (bookingID, userID)
                )
            else:
                result = conn.execute(
                    "DELETE FROM bookings WHERE booking_id = ?",
                    (bookingID,)
                )
            conn.commit()
        if result.rowcount == 0:
            return False, "Booking not found"
        return True, "Booking cancelled"

defaultClasses = {
    "economy": 1.0,
    "premium_economy": 2.2,
    "business": 3.0,
    "first": 6.0
}


db_manager = DatabaseManager()

class LoginScreen(Screen):
    def __init__(self, prefillEmail: str = ""):
        super().__init__()
        self.prefillEmail = prefillEmail

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== User Login ===", classes="title"),
            Input(placeholder="Email", id="email", value=self.prefillEmail),
            Input(placeholder="Password", password=True, id="password"),
            Button("Login", id="login", variant="primary"),
            Button("Back", id="back")
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "login":
            email = self.query_one("#email", Input).value
            password = self.query_one("#password", Input).value
            user, message = db_manager.authenticateUser(email, password)
            if user is None:
                self.notify(message, severity="error")
                return
            self.notify(f"{message}: {user.firstName} {user.lastName}")
            self.app.pop_screen()
            self.app.push_screen(DashboardScreen(user))


class DashboardScreen(Screen):
    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Dashboard ===", classes="title"),
            Label(f"Welcome, {self.user.firstName} {self.user.lastName}", classes="subtitle"),
            Button("Logout", id="logout", variant="error")
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "logout":
            self.notify("Logged out")
            self.app.pop_screen()

class RegisterScreen(Screen):
    MONTH_NAMES = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    def yearOptions(self):
        current_year = datetime.now().year
        return [(str(year), str(year)) for year in range(current_year - 100, current_year + 1)]

    def monthOptions(self):
        return [(f"{name} ({month:02d})", f"{month:02d}") for month, name in enumerate(self.MONTH_NAMES, start=1)]

    def isLeapYear(self, year: int) -> bool:
        return (year % 400 == 0) or (year % 4 == 0 and year % 100 != 0)

    def daysInMonth(self, year: int, month: int) -> int:
        if month in (1, 3, 5, 7, 8, 10, 12):
            return 31
        if month in (4, 6, 9, 11):
            return 30
        return 29 if self.isLeapYear(year) else 28

    def dayOptions(self, year: int, month: int):
        return [(f"{day:02d}", f"{day:02d}") for day in range(1, self.daysInMonth(year, month) + 1)]

    def selectedYearMonth(self) -> tuple[int, int]:
        year_select = self.query_one("#dob_year", Select)
        month_select = self.query_one("#dob_month", Select)

        year_value = year_select.value
        month_value = month_select.value
        current_year = datetime.now().year

        year = int(year_value) if year_value != Select.BLANK else current_year
        month = int(month_value) if month_value != Select.BLANK else 1
        return year, month

    def updateDayOptions(self):
        day_select = self.query_one("#dob_day", Select)
        current_day = day_select.value
        year, month = self.selectedYearMonth()
        max_day = self.daysInMonth(year, month)
        day_select.set_options(self.dayOptions(year, month))

        if current_day != Select.BLANK:
            clamped_day = min(int(current_day), max_day)
            day_select.value = f"{clamped_day:02d}"

    def on_mount(self) -> None:
        self.updateDayOptions()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id in {"dob_year", "dob_month"}:
            self.updateDayOptions()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Register ===", classes="title"),
            Input(placeholder="Email", id="email"),
            Input(placeholder="Password", password=True, id="password"),
            Input(placeholder="First name", id="first_name"),
            Input(placeholder="Last name", id="last_name"),
            Input(placeholder="Gender", id="gender"),
            Input(placeholder="Nationality", id="nationality"),
            Label("Date of birth", classes="field_label"),
            Horizontal(
                Select(self.yearOptions(), prompt="Year", id="dob_year", allow_blank=False, classes="dob_picker"),
                Select(self.monthOptions(), prompt="Month", id="dob_month", allow_blank=False, classes="dob_picker"),
                Select(self.dayOptions(datetime.now().year, 1), prompt="Day", id="dob_day", allow_blank=False, classes="dob_picker"),
                id="dob_row",
            ),
            Button("Register", id="register", variant="primary"),
            Button("Back", id="back")
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "register":
            dob_year = self.query_one("#dob_year", Select).value
            dob_month = self.query_one("#dob_month", Select).value
            dob_day = self.query_one("#dob_day", Select).value
            required_values = {
                "email": self.query_one("#email", Input).value.strip(),
                "password": self.query_one("#password", Input).value,
                "first_name": self.query_one("#first_name", Input).value.strip(),
                "last_name": self.query_one("#last_name", Input).value.strip(),
                "gender": self.query_one("#gender", Input).value.strip(),
                "nationality": self.query_one("#nationality", Input).value.strip(),
            }
            if any(not value for value in required_values.values()):
                self.notify("Please fill in all fields", severity="warning")
                return
            if dob_year == Select.BLANK or dob_month == Select.BLANK or dob_day == Select.BLANK:
                self.notify("Please select a complete date of birth", severity="warning")
                return

            date_of_birth = f"{dob_year}-{dob_month}-{dob_day}"
            try:
                datetime.strptime(date_of_birth, "%Y-%m-%d")
            except ValueError:
                self.notify("Invalid date of birth", severity="error")
                return

            user = Passenger(
                email=required_values["email"],
                password=required_values["password"],
                firstName=required_values["first_name"],
                lastName=required_values["last_name"],
                gender=required_values["gender"],
                nationality=required_values["nationality"],
                dateOfBirth=date_of_birth,
            )
            success, message = db_manager.registerUser(user)
            self.notify(message, severity="information" if success else "error")
            if success:
                self.app.pop_screen()
                self.app.push_screen(LoginScreen(prefillEmail=user.email))

class FindFlightsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Find Flights ===", classes="title"),
            Input(placeholder="Departure", id="departure"),
            Input(placeholder="Destination", id="destination"),
            Input(placeholder="Date (YYYY-MM-DD)", id="date"),
            Button("Search", id="search", variant="primary"),
            Label("", id="results"),
            Button("Back", id="back")
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "search":
            departure = self.query_one("#departure", Input).value
            destination = self.query_one("#destination", Input).value
            date = self.query_one("#date", Input).value
            flights = db_manager.searchFlights(departure, destination, date)
            results_label = self.query_one("#results", Label)

            if not flights:
                results_label.update("No flights found")
                return

            lines = []
            for flight in flights:
                lines.append(
                    f"{flight.flightNumber}: {flight.departure} -> {flight.destination} "
                    f"({flight.departureTime})"
                )
            results_label.update("\n".join(lines))

class MainMenu(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== AeroFlow ===", classes="title"),
            Label("Choose an function.", classes="subtitle"),
            Button("Login", id="login"),
            Button("Register", id="register"),
            Button("Find Flights", id="find_flights"),
            Button("Exit", id="exit", variant="error")
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login":
            self.app.push_screen(LoginScreen())
        elif event.button.id == "register":
            self.app.push_screen(RegisterScreen())
        elif event.button.id == "find_flights":
            self.app.push_screen(FindFlightsScreen())
        elif event.button.id == "exit":
            self.app.exit()

class AeroFlow(App):
    CSS = """
    Screen {
        align: center middle;
    }
    Vertical {
        width: 60;
        align: center middle;
    }
    Button {
        width: 100%;
        margin-top: 1;
    }
    .title {
        text-align: center;
        width: 100%;
        text-style: bold;
        margin-bottom: 1;
    }
    .subtitle {
        text-align: center;
        width: 100%;
        color: $text-muted;
        margin-bottom: 2;
    }
    #dob_row {
        width: 100%;
        height: auto;
    }
    .dob_picker {
        width: 1fr;
        margin-right: 1;
    }
    #dob_day {
        margin-right: 0;
    }
    """

    def on_mount(self) -> None:
        self.push_screen(MainMenu())

if __name__ == "__main__":
    app = AeroFlow()
    app.run()