import secrets
import os
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Button, Label, Input, Select, OptionList, DataTable, Checkbox
from textual.screen import Screen
import sqlite3
from datetime import datetime
from modules import DatePicker, hashPassword


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
    def __init__(self, flightNumber, departure, destination, departureTime, arrivalTime, classesAvailable, standardPrice, classRatios=None, flightID=None):
        self.flightID = flightID
        self.flightNumber = flightNumber
        self.departure = departure
        self.destination = destination
        self.departureTime = departureTime
        self.arrivalTime = arrivalTime
        normalizedRatios = {}
        if classRatios is not None:
            for className, ratio in classRatios.items():
                normalizedName = str(className).strip().lower()
                if not normalizedName:
                    continue
                normalizedRatios[normalizedName] = float(ratio)
        else:
            for className in classesAvailable:
                normalizedName = str(className).strip().lower()
                if not normalizedName:
                    continue
                ratio = defaultClasses.get(normalizedName, 1.0)
                normalizedRatios[normalizedName] = float(ratio)
        self.classRatios = normalizedRatios
        self.classesAvailable = list(self.classRatios.keys())
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

    def fetchSubPassengersByBooking(self, bookingID):
        with self.getConnection() as conn:
            rows = conn.execute(
                """
                SELECT first_name, last_name, gender, nationality, date_of_birth
                FROM sub_passengers
                WHERE booking_id = ?
                ORDER BY id ASC
                """,
                (bookingID,)
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
            self.app.currentUser = user
            self.notify(f"{message}: {user.firstName} {user.lastName}")
            self.app.pop_screen()
            if user.isAdmin:
                self.app.push_screen(AdminDashboardScreen(user))
            else:
                self.app.push_screen(PassengerDashboardScreen(user))


class UpdateProfileScreen(Screen):
    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Update Profile ===", classes="title"),
            Input(value=self.user.firstName, placeholder="First name", id="firstName"),
            Input(value=self.user.lastName, placeholder="Last name", id="lastName"),
            Input(placeholder="Password", password=True, id="password"),
            Input(value=self.user.gender, placeholder="Gender", id="gender"),
            Input(value=self.user.nationality, placeholder="Nationality", id="nationality"),
            Label("Date of birth", classes="field_label"),
            DatePicker(id="dobRow", defaultDate=self.user.dateOfBirth),
            Button("Save Changes", id="save", variant="primary"),
            Button("Back", id="back")
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "save":
            firstName = self.query_one("#firstName", Input).value.strip()
            lastName = self.query_one("#lastName", Input).value.strip()
            password = self.query_one("#password", Input).value
            gender = self.query_one("#gender", Input).value.strip()
            nationality = self.query_one("#nationality", Input).value.strip()
            dateOfBirth = self.query_one("#dobRow", DatePicker).value

            requiredValues = [firstName, lastName, password, gender, nationality, dateOfBirth]
            if any(not value for value in requiredValues):
                self.notify("All fields are required.", severity="error")
                return

            if firstName != self.user.firstName:
                dbManager.updateProfile(self.user.userID, "firstName", firstName)
                self.user.firstName = firstName
            if lastName != self.user.lastName:
                dbManager.updateProfile(self.user.userID, "lastName", lastName)
                self.user.lastName = lastName
            hashedPassword = hashPassword(password)
            if hashedPassword != self.user.password:
                dbManager.updateProfile(self.user.userID, "password", password)
                self.user.password = hashedPassword
            if gender != self.user.gender:
                dbManager.updateProfile(self.user.userID, "gender", gender)
                self.user.gender = gender
            if nationality != self.user.nationality:
                dbManager.updateProfile(self.user.userID, "nationality", nationality)
                self.user.nationality = nationality
            if dateOfBirth != self.user.dateOfBirth:
                dbManager.updateProfile(self.user.userID, "dateOfBirth", dateOfBirth)
                self.user.dateOfBirth = dateOfBirth

            self.notify("Profile updated successfully!", severity="information")
            self.app.pop_screen()
            
            dashboard = self.app.screen
            if isinstance(dashboard, PassengerDashboardScreen):
                welcomeLabel = dashboard.query_one("#welcomeLabel", Label)
                welcomeLabel.update(f"Welcome, {self.user.firstName} {self.user.lastName}")


class PassengerDashboardScreen(Screen):
    def __init__(self, user: User):
        super().__init__()
        self.user = user

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Passenger Dashboard ===", classes="title"),
            Label(f"Welcome, {self.user.firstName} {self.user.lastName}", id="welcomeLabel", classes="subtitle"),
            Button("Book Flight", id="bookFlight", variant="primary"),
            Button("Manage Bookings", id="manageBookings"),
            Button("Update Profile", id="updateProfile"),
            Button("Logout", id="logout", variant="error")
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "logout":
            self.app.currentUser = None
            self.notify("Logged out")
            self.app.pop_screen()
        elif event.button.id == "bookFlight":
            self.app.push_screen(FindFlightsScreen())
        elif event.button.id == "updateProfile":
            self.app.push_screen(UpdateProfileScreen(self.user))
        elif event.button.id == "manageBookings":
            self.app.push_screen(ManageBookingsScreen(self.user))

class ManageBookingsScreen(Screen):
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.bookingMap = {}

    def bookingSummaryText(self, booking):
        className = str(booking["travel_class"]).replace("_", " ").title()
        departureTime = str(booking["departure_time"])[:16]
        return f"{booking['flight_number']} | {booking['departure']} -> {booking['destination']} | {departureTime} | {className} | ${float(booking['price']):.2f}"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Manage Bookings ===", classes="title"),
            Label("Select a booking to view details.", classes="subtitle"),
            VerticalScroll(
                Vertical(id="bookingList"),
                id="bookingListScroll"
            ),
            Button("Back", id="back")
        )
        yield Footer()

    def on_mount(self) -> None:
        bookings = dbManager.fetchUserBookings(self.user.userID)
        bookingList = self.query_one("#bookingList", Vertical)
        if not bookings:
            bookingList.mount(Label("No bookings found.", classes="subtitle"))
            return

        for booking in bookings:
            bookingID = str(booking["booking_id"])
            self.bookingMap[bookingID] = booking
            bookingList.mount(
                Button(
                    self.bookingSummaryText(booking),
                    id=f"booking_{bookingID}"
                )
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if not event.button.id or not event.button.id.startswith("booking_"):
            return
        bookingID = event.button.id.replace("booking_", "", 1)
        selectedBooking = self.bookingMap.get(bookingID)
        if selectedBooking is None:
            self.notify("Booking not found.", severity="error")
            return
        self.app.push_screen(BookingDetailScreen(selectedBooking))

class BookingDetailScreen(Screen):
    def __init__(self, booking):
        super().__init__()
        self.booking = booking

    def compose(self) -> ComposeResult:
        className = str(self.booking["travel_class"]).replace("_", " ").title()
        yield Header()
        yield Vertical(
            Label("=== Booking Details ===", classes="title"),
            VerticalScroll(
                Horizontal(
                    Label("Booking ID", classes="detailHeader"),
                    Label(str(self.booking["booking_id"]), classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Flight Number", classes="detailHeader"),
                    Label(str(self.booking["flight_number"]), classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Departure", classes="detailHeader"),
                    Label(str(self.booking["departure"]), classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Destination", classes="detailHeader"),
                    Label(str(self.booking["destination"]), classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Date Time of Takeoff", classes="detailHeader"),
                    Label(str(self.booking["departure_time"]), classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Date Time of Landing", classes="detailHeader"),
                    Label(str(self.booking["arrival_time"]), classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Travel Class", classes="detailHeader"),
                    Label(className, classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Total Price", classes="detailHeader"),
                    Label(f"${float(self.booking['price']):.2f}", classes="detailValue"),
                    classes="detailRow"
                ),
                Label("Sub Passengers (if any): ", classes="field_label"),
                Vertical(id="subPassengerList"),
                id="bookingDetailScroll"
            ),
            Button("Back", id="back")
        )
        yield Footer()

    def on_mount(self) -> None:
        subPassengers = dbManager.fetchSubPassengersByBooking(self.booking["booking_id"])
        subPassengerList = self.query_one("#subPassengerList", Vertical)
        if not subPassengers:
            subPassengerList.mount(Label("No sub passengers.", classes="subtitle"))
            return
        for index, sub in enumerate(subPassengers, start=1):
            subPassengerList.mount(
                Label(
                    f"{index}. {sub['first_name']} {sub['last_name']} | {sub['gender']} | {sub['nationality']} | {sub['date_of_birth']}"
                )
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
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
            self.app.currentUser = None
            self.notify("Logged out")
            self.app.pop_screen()

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
            self.query_one("#date", DatePicker).focus()

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
        self.lastSelectedFlightID = None
        self.lastSelectedTime = None

    def getFlightByID(self, flightID):
        for flight in self.flights:
            if str(flight.flightID) == str(flightID):
                return flight
        return None

    def classPriceText(self, flight: Flight, className: str) -> str:
        normalizedClassName = className.strip().lower()
        ratio = flight.classRatios.get(normalizedClassName)
        if ratio is None:
            return "N/A"
        price = float(flight.standardPrice) * ratio
        return f"${price:.2f}"

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
        table.add_columns(
            "Flight Number",
            "Departure",
            "Destination",
            "Date Time of Takeoff",
            "Date Time of Landing",
            "Economy",
            "Premium Economy",
            "Business",
            "First",
        )
        for flight in self.flights:
            table.add_row(
                flight.flightNumber,
                flight.departure,
                flight.destination,
                flight.departureTime,
                flight.arrivalTime,
                self.classPriceText(flight, "economy"),
                self.classPriceText(flight, "premium_economy"),
                self.classPriceText(flight, "business"),
                self.classPriceText(flight, "first"),
                key=flight.flightID
            )
            
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        flightID = event.row_key.value
        nowTime = datetime.now()
        if self.lastSelectedFlightID == flightID and self.lastSelectedTime and (nowTime - self.lastSelectedTime).total_seconds() <= 0.6:
            selectedFlight = self.getFlightByID(flightID)
            if selectedFlight is None:
                self.notify("Selected flight not found.", severity="error")
                return
            if self.app.currentUser is None:
                self.notify("Please login before booking.", severity="warning")
                self.app.push_screen(LoginScreen())
                return
            self.app.push_screen(BookingScreen(self.app.currentUser, selectedFlight))
            self.lastSelectedFlightID = None
            self.lastSelectedTime = None
            return
        self.lastSelectedFlightID = flightID
        self.lastSelectedTime = nowTime
        self.notify("Double click row to book this flight.")

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

class BookingScreen(Screen):
    def __init__(self, user: User, flight: Flight):
        super().__init__()
        self.user = user
        self.flight = flight
        self.subPassengerCount = 0

    def classOptions(self):
        optionLabels = {
            "economy": "Economy",
            "premium_economy": "Premium Economy",
            "business": "Business",
            "first": "First",
        }
        options = []
        for className in self.flight.classesAvailable:
            ratio = self.flight.classRatios.get(className)
            if ratio is None:
                continue
            price = float(self.flight.standardPrice) * ratio
            label = optionLabels.get(className, className.replace("_", " ").title())
            options.append((f"{label} (${price:.2f})", className))
        return options

    def on_mount(self) -> None:
        self.updateSubPassengerVisibility()

    def updateSubPassengerVisibility(self):
        counterLabel = self.query_one("#subPassengerCountLabel", Label)
        counterLabel.update(str(self.subPassengerCount))
        for index in range(1, 5):
            group = self.query_one(f"#subPassenger{index}Group", Vertical)
            group.display = index <= self.subPassengerCount

    def compose(self) -> ComposeResult:
        classOptions = self.classOptions()
        defaultClass = classOptions[0][1] if classOptions else Select.BLANK
        yield Header()
        yield Vertical(
            VerticalScroll(
                Label("=== Flight Booking ===", classes="title"),
                Label(f"Flight: {self.flight.flightNumber}", classes="subtitle"),
                Label(f"Route: {self.flight.departure} -> {self.flight.destination}"),
                Label(f"Primary Passenger: {self.user.firstName} {self.user.lastName}"),
                Label("Travel Class (same for all passengers)", classes="field_label"),
                Select(classOptions, id="travelClass", allow_blank=False, value=defaultClass),
                Label("Number of Sub Passengers", classes="field_label"),
                Horizontal(
                    Button("-", id="decreaseSubPassenger", classes="counterButton"),
                    Button("+", id="increaseSubPassenger", classes="counterButton"),
                    Label("0", id="subPassengerCountLabel", classes="subtitle"),
                    id="subPassengerCounter"
                ),
                Vertical(
                    Label("Sub Passenger 1", classes="field_label"),
                    Input(placeholder="First name", id="sub1FirstName"),
                    Input(placeholder="Last name", id="sub1LastName"),
                    Input(placeholder="Gender", id="sub1Gender"),
                    Input(placeholder="Nationality", id="sub1Nationality"),
                    DatePicker(id="sub1Dob"),
                    id="subPassenger1Group"
                ),
                Vertical(
                    Label("Sub Passenger 2", classes="field_label"),
                    Input(placeholder="First name", id="sub2FirstName"),
                    Input(placeholder="Last name", id="sub2LastName"),
                    Input(placeholder="Gender", id="sub2Gender"),
                    Input(placeholder="Nationality", id="sub2Nationality"),
                    DatePicker(id="sub2Dob"),
                    id="subPassenger2Group"
                ),
                Vertical(
                    Label("Sub Passenger 3", classes="field_label"),
                    Input(placeholder="First name", id="sub3FirstName"),
                    Input(placeholder="Last name", id="sub3LastName"),
                    Input(placeholder="Gender", id="sub3Gender"),
                    Input(placeholder="Nationality", id="sub3Nationality"),
                    DatePicker(id="sub3Dob"),
                    id="subPassenger3Group"
                ),
                Vertical(
                    Label("Sub Passenger 4", classes="field_label"),
                    Input(placeholder="First name", id="sub4FirstName"),
                    Input(placeholder="Last name", id="sub4LastName"),
                    Input(placeholder="Gender", id="sub4Gender"),
                    Input(placeholder="Nationality", id="sub4Nationality"),
                    DatePicker(id="sub4Dob"),
                    id="subPassenger4Group"
                ),
                Checkbox("I agree to the Terms and Conditions", id="agreeTerms"),
                Button("Confirm and Proceed to Payment", id="confirmBooking", variant="primary"),
                Button("Back", id="back"),
                id="bookingForm"
            )
        )
        yield Footer()

    def subPassengerFromIndex(self, passengerIndex: int):
        firstName = self.query_one(f"#sub{passengerIndex}FirstName", Input).value.strip()
        lastName = self.query_one(f"#sub{passengerIndex}LastName", Input).value.strip()
        gender = self.query_one(f"#sub{passengerIndex}Gender", Input).value.strip()
        nationality = self.query_one(f"#sub{passengerIndex}Nationality", Input).value.strip()
        dateOfBirth = self.query_one(f"#sub{passengerIndex}Dob", DatePicker).value
        requiredValues = [firstName, lastName, gender, nationality, dateOfBirth]
        if any(not value for value in requiredValues):
            return None
        return SubPassenger(firstName, lastName, gender, nationality, dateOfBirth)

    def bookingTotalPrice(self, travelClass: str, passengerCount: int):
        ratio = self.flight.classRatios.get(travelClass)
        if ratio is None:
            return None
        return float(self.flight.standardPrice) * float(ratio) * passengerCount

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "increaseSubPassenger":
            if self.subPassengerCount < 4:
                self.subPassengerCount += 1
                self.updateSubPassengerVisibility()
            return
        if event.button.id == "decreaseSubPassenger":
            if self.subPassengerCount > 0:
                self.subPassengerCount -= 1
                self.updateSubPassengerVisibility()
            return
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id != "confirmBooking":
            return

        travelClass = self.query_one("#travelClass", Select).value
        agreedTerms = self.query_one("#agreeTerms", Checkbox).value

        if travelClass == Select.BLANK:
            self.notify("Please select a travel class.", severity="warning")
            return
        if not agreedTerms:
            self.notify("You must agree to the Terms and Conditions.", severity="warning")
            return

        subPassengers = []
        for index in range(1, self.subPassengerCount + 1):
            subPassenger = self.subPassengerFromIndex(index)
            if subPassenger is None:
                self.notify(f"Please complete Sub Passenger {index} details.", severity="warning")
                return
            subPassengers.append(subPassenger)

        totalPassengers = 1 + len(subPassengers)
        totalPrice = self.bookingTotalPrice(str(travelClass), totalPassengers)
        if totalPrice is None:
            self.notify("Selected class is not available.", severity="error")
            return

        booking = Booking(
            userID=self.user.userID,
            flightID=self.flight.flightID,
            travel_class=str(travelClass),
            price=totalPrice,
            sub_passengers=subPassengers,
        )
        self.app.push_screen(PaymentScreen(booking))

class PaymentScreen(Screen):
    def __init__(self, booking: Booking):
        super().__init__()
        self.booking = booking
        self.countdownSeconds = 5
        self.paymentTimer = None
        self.paymentCompleted = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Payment ===", classes="title"),
            Label(f"Booking ID: {self.booking.bookingID}"),
            Label(f"Total Amount: ${float(self.booking.price):.2f}", classes="subtitle"),
            Label("", id="paymentStatusLabel"),
            Button("Confirm Payment", id="confirmPayment", variant="primary"),
            Button("Back", id="back"),
            Button("Finish", id="finish", variant="success")
        )
        yield Footer()

    def on_mount(self) -> None:
        finishButton = self.query_one("#finish", Button)
        finishButton.display = False

    def returnToDashboard(self):
        if self.app.currentUser and self.app.currentUser.isAdmin:
            self.app.push_screen(AdminDashboardScreen(self.app.currentUser))
            return
        if self.app.currentUser:
            self.app.push_screen(PassengerDashboardScreen(self.app.currentUser))
            return
        self.app.push_screen(MainMenu())

    def completePayment(self):
        if self.paymentCompleted:
            return
        self.paymentCompleted = True
        dbManager.createBooking(self.booking)
        statusLabel = self.query_one("#paymentStatusLabel", Label)
        statusLabel.update("Payment Successful")
        statusLabel.styles.color = "green"
        confirmButton = self.query_one("#confirmPayment", Button)
        backButton = self.query_one("#back", Button)
        finishButton = self.query_one("#finish", Button)
        confirmButton.display = False
        backButton.display = False
        finishButton.display = True
        self.notify("Booking created successfully.", severity="information")

    def processPaymentTick(self):
        statusLabel = self.query_one("#paymentStatusLabel", Label)
        if self.countdownSeconds > 0:
            statusLabel.update(f"Processing Payment, Please wait ({self.countdownSeconds})")
            self.countdownSeconds -= 1
            return
        if self.paymentTimer is not None:
            self.paymentTimer.stop()
            self.paymentTimer = None
        self.completePayment()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "finish":
            self.returnToDashboard()
            return
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id != "confirmPayment":
            return
        if self.paymentCompleted:
            return
        if self.paymentTimer is not None:
            return
        confirmButton = self.query_one("#confirmPayment", Button)
        confirmButton.disabled = True
        self.processPaymentTick()
        self.paymentTimer = self.set_interval(1, self.processPaymentTick)

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
    #bookingForm {
        height: 1fr;
        width: 100%;
    }
    #subPassengerCounter {
        height: auto;
        width: 100%;
        align: center middle;
    }
    #subPassengerCounter Button {
        width: 8;
        margin-right: 1;
    }
    .counterButton {
        width: 8 !important;
        margin-top: 0;
    }
    .detailRow {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    .detailHeader {
        width: 22;
        text-style: bold;
    }
    .detailValue {
        width: 1fr;
    }
    """

    def on_mount(self) -> None:
        self.currentUser = None
        self.push_screen(MainMenu())

if __name__ == "__main__":
    app = AeroFlow()
    app.run()
