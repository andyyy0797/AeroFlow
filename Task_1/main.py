import secrets
import os
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Button, Label, Input, Select, OptionList, DataTable
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


class SubPassenger:
    def __init__(self, firstName, lastName, gender, nationality, dateOfBirth):
        self.firstName = firstName
        self.lastName = lastName
        self.gender = gender
        self.nationality = nationality
        self.dateOfBirth = dateOfBirth


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
    def __init__(self, userID, flightID, travel_class, price, bookingID=None, sub_passengers=None):
        self.bookingID = bookingID if bookingID else secrets.token_hex(4)
        self.userID = userID
        self.flightID = flightID
        self.travel_class = travel_class
        self.price = price
        self.sub_passengers = sub_passengers if sub_passengers else []
        if len(self.sub_passengers) + 1 > 5:
            raise ValueError("A booking can have a maximum of 5 passengers.")

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
            conn.commit()

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
                    flightID=row["flightID"],
                )
            )
        return results

    def createBooking(self, booking):
        with self.getConnection() as conn:
            conn.execute(
                """
                INSERT INTO bookings (booking_id, user_id, flightID, travel_class, price)
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
                  SELECT b.booking_id, b.user_id, b.flightID, b.travel_class, b.price,
                      f.flight_number, f.departure, f.destination, f.departure_time, f.arrival_time
                FROM bookings b
                  JOIN flights f ON b.flightID = f.flightID
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

defaultClasses = {
    "economy": 1.0,
    "premium_economy": 2.2,
    "business": 3.0,
    "first": 6.0
}


dbManager = DatabaseManager()

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
            user, message = dbManager.authenticateUser(email, password)
            if user is None:
                self.notify(message, severity="error")
                return
            self.notify(f"{message}: {user.firstName} {user.lastName}")
            self.app.pop_screen()
            if user.isAdmin:
                self.app.push_screen(AdminDashboardScreen(user))
            else:
                self.app.push_screen(PassengerDashboardScreen(user))


class PassengerDashboardScreen(Screen):
    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Passenger Dashboard ===", classes="title"),
            Label(f"Welcome, {self.user.firstName} {self.user.lastName}", classes="subtitle"),
            Button("Logout", id="logout", variant="error")
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "logout":
            self.notify("Logged out")
            self.app.pop_screen()

class AdminDashboardScreen(Screen):
    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Admin Dashboard ===", classes="title"),
            Label(f"Welcome, {self.user.firstName} {self.user.lastName}", classes="subtitle"),
            Button("Logout", id="logout", variant="error")
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "logout":
            self.notify("Logged out")
            self.app.pop_screen()

class DatePicker(Horizontal):
    MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December",]

    def __init__(self, id: str = None, classes: str = None, defaultDate: str = ""):
        super().__init__(id=id, classes=classes)
        if defaultDate:
            try:
                dt = datetime.strptime(defaultDate, "%Y-%m-%d")
            except ValueError:
                dt = datetime.now()
        else:
            dt = datetime.now()
            
        self.default_year = str(dt.year)
        self.default_month = f"{dt.month:02d}"
        self.default_day = f"{dt.day:02d}"

    def yearOptions(self):
        currentYear = datetime.now().year
        return [(str(year), str(year)) for year in range(currentYear - 100, currentYear + 10)]

    def monthOptions(self):
        return [(f"{name}", f"{month:02d}") for month, name in enumerate(self.MONTH_NAMES, start=1)]

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
        yearSelect = self.query_one(".year-select", Select)
        monthSelect = self.query_one(".month-select", Select)

        yearValue = yearSelect.value
        monthValue = monthSelect.value

        year = int(yearValue) if yearValue != Select.BLANK else int(self.default_year)
        month = int(monthValue) if monthValue != Select.BLANK else int(self.default_month)
        return year, month

    def updateDayOptions(self):
        day_select = self.query_one(".day-select", Select)
        current_day = day_select.value
        year, month = self.selectedYearMonth()
        max_day = self.daysInMonth(year, month)
        day_select.set_options(self.dayOptions(year, month))

        if current_day != Select.BLANK:
            clamped_day = min(int(current_day), max_day)
            day_select.value = f"{clamped_day:02d}"

    def compose(self) -> ComposeResult:
        yield Select(self.yearOptions(), prompt="Year", classes="dob_picker year-select", allow_blank=False, value=self.default_year)
        yield Select(self.monthOptions(), prompt="Month", classes="dob_picker month-select", allow_blank=False, value=self.default_month)
        yield Select(self.dayOptions(int(self.default_year), int(self.default_month)), prompt="Day", classes="dob_picker day-select", allow_blank=False, value=self.default_day)

    def on_mount(self) -> None:
        self.updateDayOptions()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.has_class("year-select") or event.select.has_class("month-select"):
            self.updateDayOptions()

    @property
    def value(self):
        year = self.query_one(".year-select", Select).value
        month = self.query_one(".month-select", Select).value
        day = self.query_one(".day-select", Select).value
        if year == Select.BLANK or month == Select.BLANK or day == Select.BLANK:
            return None
        return f"{year}-{month}-{day}"


class RegisterScreen(Screen):
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
            DatePicker(id="dob_row", defaultDate="1980-01-01"),
            Button("Register", id="register", variant="primary"),
            Button("Back", id="back")
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "register":
            date_of_birth = self.query_one("#dob_row", DatePicker).value
            requiredValue = {
                "email": self.query_one("#email", Input).value.strip(),
                "password": self.query_one("#password", Input).value,
                "first_name": self.query_one("#first_name", Input).value.strip(),
                "last_name": self.query_one("#last_name", Input).value.strip(),
                "gender": self.query_one("#gender", Input).value.strip(),
                "nationality": self.query_one("#nationality", Input).value.strip(),
            }
            if any(not value for value in requiredValue.values()):
                self.notify("Please fill in all fields", severity="warning")
                return
            if not date_of_birth:
                self.notify("Please select a complete date of birth", severity="warning")
                return

            try:
                datetime.strptime(date_of_birth, "%Y-%m-%d")
            except ValueError:
                self.notify("Invalid date of birth", severity="error")
                return

            user = Passenger(
                email=requiredValue["email"],
                password=requiredValue["password"],
                firstName=requiredValue["first_name"],
                lastName=requiredValue["last_name"],
                gender=requiredValue["gender"],
                nationality=requiredValue["nationality"],
                dateOfBirth=date_of_birth,
            )
            success, message = dbManager.registerUser(user)
            self.notify(message, severity="information" if success else "error")
            if success:
                self.app.pop_screen()
                self.app.push_screen(LoginScreen(prefillEmail=user.email))

class FindFlightsScreen(Screen):
    def on_mount(self) -> None:
        self.locations = dbManager.getFutureLocations()
        self.query_one("#departure_list").display = False
        self.query_one("#destination_list").display = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Find Flights ===", classes="title"),
            Input(placeholder="Departure", id="departure"),
            OptionList(id="departure_list", classes="autocomplete_list"),
            Input(placeholder="Destination", id="destination"),
            OptionList(id="destination_list", classes="autocomplete_list"),
            Label("Date", classes="field_label"),
            DatePicker(id="date"),
            Button("Search", id="search", variant="primary"),
            Label("", id="results"),
            Button("Back", id="back")
        )
        yield Footer()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id in {"departure", "destination"}:
            val = event.input.value.strip().lower()
            list_id = f"#{event.input.id}_list"
            option_list = self.query_one(list_id, OptionList)
            
            if not val:
                option_list.display = False
                return
                
            matches = [loc for loc in self.locations if val in loc.lower()]
            if matches:
                option_list.clear_options()
                for match in matches:
                    option_list.add_option(match)
                option_list.display = True
            else:
                option_list.display = False

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "departure_list":
            self.query_one("#departure", Input).value = str(event.option.prompt)
            event.option_list.display = False
            self.query_one("#destination", Input).focus()
        elif event.option_list.id == "destination_list":
            self.query_one("#destination", Input).value = str(event.option.prompt)
            event.option_list.display = False
            self.query_one("#date", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "search":
            departure = self.query_one("#departure", Input).value
            destination = self.query_one("#destination", Input).value
            date = self.query_one("#date", DatePicker).value
            
            if not date:
                self.notify("Please select a valid date", severity="warning")
                return
                
            flights = dbManager.searchFlights(departure, destination, date)
            results_label = self.query_one("#results", Label)

            if not flights:
                results_label.update("No flights found")
                return

            self.app.push_screen(SearchResultScreen(flights))

class SearchResultScreen(Screen):
    def __init__(self, flights):
        super().__init__()
        self.flights = flights

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Search Results ===", classes="title"),
            Label("Select a flight to continue.", classes="subtitle"),
            DataTable(id="flights_table"),
            Button("Back", id="back")
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.addColumns("Flight", "Departure", "Destination", "Time", "Price")
        for flight in self.flights:
            timeStr = f"{flight.departureTime[:16]} -> {flight.arrivalTime[-8:-3] if ' ' in flight.arrivalTime else flight.arrivalTime}"
            table.add_row(
                flight.flightNumber,
                flight.departure,
                flight.destination,
                timeStr,
                f"${flight.standardPrice}",
                key=flight.flightID
            )
            
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        flightID = event.row_key.value
        self.notify(f"Proceeding to book flight: {flightID}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()

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
    #dobDay {
        margin-right: 0;
    }
    .autocomplete_list {
        height: auto;
        max-height: 5;
        display: none;
        border: solid round $primary;
        margin-top: 1;
        margin-bottom: 1;
    }
    #flights_table {
        height: auto;
        max-height: 20;
        margin-top: 1;
        margin-bottom: 1;
    }
    """

    def on_mount(self) -> None:
        self.push_screen(MainMenu())

if __name__ == "__main__":
    app = AeroFlow()
    app.run()