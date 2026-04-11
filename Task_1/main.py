from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Header, Footer, Button, Label, Input, Select, OptionList, DataTable, Checkbox
from textual.screen import Screen
import sqlite3
from datetime import datetime
from utils import DatePicker, hashPassword
from dataLayer import User, Admin, Passenger, SubPassenger, Flight, Booking, defaultClasses
from databaseManager import DatabaseManager


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
        overview = dbManager.fetchAdminOverview()
        yield Header()
        yield Vertical(
            Label("=== Admin Dashboard ===", classes="title"),
            Label(f"Welcome, {self.user.firstName} {self.user.lastName}", classes="subtitle"),
            Horizontal(
                Vertical(
                    Label(f"Total Flights: {overview['totalFlights']}"),
                    Label(f"Upcoming Flights: {overview['futureFlights']}"),
                    Label(f"Total Bookings: {overview['totalBookings']}"),
                    id="adminOverviewPanel",
                    classes="adminPanel adminOverviewPanel"
                ),
                Vertical(
                    Button("New Flight", id="newFlight", variant="primary"),
                    Button("Manage Flights", id="manageFlights"),
                    Button("Manage Bookings", id="manageAllBookings"),
                    Button("Create Admin Account", id="createAdminAccount"),
                    id="adminActionsPanel",
                    classes="adminPanel adminActionsPanel"
                ),
                classes="adminTopRow"
            ),
            Vertical(
                Horizontal(
                    Button("Update Profile", id="updateProfile"),
                    Button("Logout", id="logout", variant="error"),
                    classes="adminProfileButtons"
                ),
                id="adminProfilePanel",
                classes="adminBottomPanel"
            ),
            classes="adminDashboardRoot"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#adminOverviewPanel", Vertical).border_title = "Overview"
        self.query_one("#adminActionsPanel", Vertical).border_title = "Actions"
        self.query_one("#adminProfilePanel", Vertical).border_title = "Profile"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "logout":
            self.app.currentUser = None
            self.notify("Logged out")
            self.app.pop_screen()
        elif event.button.id == "updateProfile":
            self.app.push_screen(UpdateProfileScreen(self.user))
        elif event.button.id == "newFlight":
            self.app.push_screen(NewFlightScreen())
        elif event.button.id == "manageFlights":
            self.app.push_screen(ManageFlightsScreen())
        elif event.button.id == "manageAllBookings":
            self.app.push_screen(AdminManageBookingsScreen())
        elif event.button.id == "createAdminAccount":
            self.app.push_screen(CreateAdminScreen())

class AdminManageBookingsScreen(Screen):
    def __init__(self):
        super().__init__()
        self.bookingMap = {}
        self.selectedBookingID = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Manage Bookings ===", classes="title"),
            Label("Select one booking from the table.", classes="subtitle"),
            DataTable(id="adminBookingsTable"),
            Horizontal(
                Button("View Booking", id="viewBooking"),
                Button("Edit Booking", id="editBooking", variant="primary"),
                Button("Delete Booking", id="deleteBooking", variant="error"),
                Button("Refresh", id="refreshBookingList"),
                classes="detailActionRow"
            ),
            Button("Back", id="back")
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#adminBookingsTable", DataTable)
        table.cursor_type = "row"
        table.add_columns("Booking ID", "User Email", "Flight", "Route", "Takeoff", "Class", "Price")
        self.loadBookings()

    def on_screen_resume(self) -> None:
        self.loadBookings()

    def loadBookings(self):
        rows = dbManager.fetchAllActiveBookings()
        table = self.query_one("#adminBookingsTable", DataTable)
        table.clear(columns=False)
        self.bookingMap = {}
        self.selectedBookingID = None
        for row in rows:
            bookingID = str(row["booking_id"])
            self.bookingMap[bookingID] = row
            className = str(row["travel_class"]).replace("_", " ").title()
            route = f"{row['departure']} -> {row['destination']}"
            table.add_row(
                bookingID,
                str(row["user_email"]),
                str(row["flight_number"]),
                route,
                str(row["departure_time"])[:16],
                className,
                f"${float(row['price']):.2f}",
                key=bookingID
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.row_key is None:
            return
        self.selectedBookingID = str(event.row_key.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id == "refreshBookingList":
            self.loadBookings()
            return
        if not self.selectedBookingID:
            self.notify("Please select one booking first.", severity="warning")
            return
        if event.button.id == "viewBooking":
            self.app.push_screen(AdminBookingDetailScreen(self.selectedBookingID))
            return
        if event.button.id == "editBooking":
            self.app.push_screen(AdminEditBookingScreen(self.selectedBookingID))
            return
        if event.button.id == "deleteBooking":
            success, message = dbManager.deleteBookingByAdmin(self.selectedBookingID)
            self.notify(message, severity="information" if success else "error")
            if success:
                self.loadBookings()

class AdminEditBookingScreen(Screen):
    def __init__(self, bookingID):
        super().__init__()
        self.bookingID = bookingID
        self.bookingRow = None

    def classOptions(self):
        if self.bookingRow is None:
            return []
        classRatios = dbManager.parseClassRatios(self.bookingRow["classes_available"])
        options = []
        for className in classRatios.keys():
            options.append((className.replace("_", " ").title(), className))
        return options

    def compose(self) -> ComposeResult:
        self.bookingRow = dbManager.fetchActiveBookingByID(self.bookingID)
        yield Header()
        if self.bookingRow is None:
            yield Vertical(
                Label("=== Edit Booking ===", classes="title"),
                Label("Booking not found.", classes="subtitle"),
                Button("Back", id="back")
            )
            yield Footer()
            return

        options = self.classOptions()
        currentClass = str(self.bookingRow["travel_class"])
        defaultClass = currentClass if any(value == currentClass for _, value in options) else (options[0][1] if options else Select.BLANK)
        yield Vertical(
            VerticalScroll(
                Label("=== Edit Booking ===", classes="title"),
                Label(f"Booking ID: {self.bookingRow['booking_id']}"),
                Label(f"User: {self.bookingRow['user_email']}"),
                Label(f"Flight: {self.bookingRow['flight_number']}"),
                Label("Primary Passenger is fixed and cannot be edited.", classes="subtitle"),
                Label("Travel Class", classes="field_label"),
                Select(options, id="editTravelClass", allow_blank=False, value=defaultClass),
                Label("Number of Sub Passengers", classes="field_label"),
                Select([(str(count), str(count)) for count in range(0, 5)], id="editSubPassengerCount", allow_blank=False, value="0"),
                Label("Sub Passenger 1", classes="field_label"),
                Input(placeholder="First name", id="editSub1FirstName"),
                Input(placeholder="Last name", id="editSub1LastName"),
                Input(placeholder="Gender", id="editSub1Gender"),
                Input(placeholder="Nationality", id="editSub1Nationality"),
                DatePicker(id="editSub1Dob"),
                Label("Sub Passenger 2", classes="field_label"),
                Input(placeholder="First name", id="editSub2FirstName"),
                Input(placeholder="Last name", id="editSub2LastName"),
                Input(placeholder="Gender", id="editSub2Gender"),
                Input(placeholder="Nationality", id="editSub2Nationality"),
                DatePicker(id="editSub2Dob"),
                Label("Sub Passenger 3", classes="field_label"),
                Input(placeholder="First name", id="editSub3FirstName"),
                Input(placeholder="Last name", id="editSub3LastName"),
                Input(placeholder="Gender", id="editSub3Gender"),
                Input(placeholder="Nationality", id="editSub3Nationality"),
                DatePicker(id="editSub3Dob"),
                Label("Sub Passenger 4", classes="field_label"),
                Input(placeholder="First name", id="editSub4FirstName"),
                Input(placeholder="Last name", id="editSub4LastName"),
                Input(placeholder="Gender", id="editSub4Gender"),
                Input(placeholder="Nationality", id="editSub4Nationality"),
                DatePicker(id="editSub4Dob"),
                Label("Price will be recalculated by passenger count.", classes="subtitle"),
                Button("Save Changes", id="saveBooking", variant="primary"),
                Button("Back", id="back")
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        if self.bookingRow is None:
            return
        subPassengers = dbManager.fetchSubPassengersByBooking(self.bookingID)
        self.query_one("#editSubPassengerCount", Select).value = str(len(subPassengers))
        for index, sub in enumerate(subPassengers, start=1):
            if index > 4:
                break
            self.query_one(f"#editSub{index}FirstName", Input).value = str(sub["first_name"])
            self.query_one(f"#editSub{index}LastName", Input).value = str(sub["last_name"])
            self.query_one(f"#editSub{index}Gender", Input).value = str(sub["gender"])
            self.query_one(f"#editSub{index}Nationality", Input).value = str(sub["nationality"])
            dateOfBirth = str(sub["date_of_birth"])
            try:
                dateValue = datetime.strptime(dateOfBirth, "%Y-%m-%d")
            except ValueError:
                continue
            datePicker = self.query_one(f"#editSub{index}Dob", DatePicker)
            yearSelect = datePicker.query_one(".year-select", Select)
            monthSelect = datePicker.query_one(".month-select", Select)
            daySelect = datePicker.query_one(".day-select", Select)
            yearSelect.value = str(dateValue.year)
            monthSelect.value = f"{dateValue.month:02d}"
            datePicker.updateDayOptions()
            daySelect.value = f"{dateValue.day:02d}"

    def collectSubPassengers(self, count: int):
        subPassengers = []
        for index in range(1, count + 1):
            firstName = self.query_one(f"#editSub{index}FirstName", Input).value.strip()
            lastName = self.query_one(f"#editSub{index}LastName", Input).value.strip()
            gender = self.query_one(f"#editSub{index}Gender", Input).value.strip()
            nationality = self.query_one(f"#editSub{index}Nationality", Input).value.strip()
            dateOfBirth = self.query_one(f"#editSub{index}Dob", DatePicker).value
            requiredValues = [firstName, lastName, gender, nationality, dateOfBirth]
            if any(not value for value in requiredValues):
                return None, f"Please complete Sub Passenger {index} details."
            subPassengers.append(
                {
                    "firstName": firstName,
                    "lastName": lastName,
                    "gender": gender,
                    "nationality": nationality,
                    "dateOfBirth": dateOfBirth,
                }
            )
        return subPassengers, ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id != "saveBooking":
            return
        travelClass = self.query_one("#editTravelClass", Select).value
        if travelClass == Select.BLANK:
            self.notify("Please select a class.", severity="warning")
            return
        subCountValue = self.query_one("#editSubPassengerCount", Select).value
        if subCountValue == Select.BLANK:
            self.notify("Please select sub passenger count.", severity="warning")
            return
        subPassengerCount = int(subCountValue)
        subPassengers, errorMessage = self.collectSubPassengers(subPassengerCount)
        if subPassengers is None:
            self.notify(errorMessage, severity="warning")
            return
        success, message = dbManager.updateBookingTravelClass(self.bookingID, str(travelClass))
        self.notify(message, severity="information" if success else "error")
        if success:
            dbManager.replaceSubPassengersForBooking(self.bookingID, subPassengers)
            self.app.pop_screen()

class AdminBookingDetailScreen(Screen):
    def __init__(self, bookingID):
        super().__init__()
        self.bookingID = bookingID

    def compose(self) -> ComposeResult:
        booking = dbManager.fetchActiveBookingByID(self.bookingID)
        yield Header()
        if booking is None:
            yield Vertical(
                Label("=== Booking Details ===", classes="title"),
                Label("Booking not found.", classes="subtitle"),
                Button("Back", id="back")
            )
            yield Footer()
            return

        className = str(booking["travel_class"]).replace("_", " ").title()
        yield Vertical(
            Label("=== Booking Details ===", classes="title"),
            VerticalScroll(
                Horizontal(
                    Label("Booking ID", classes="detailHeader"),
                    Label(str(booking["booking_id"]), classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("User Email", classes="detailHeader"),
                    Label(str(booking["user_email"]), classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Flight Number", classes="detailHeader"),
                    Label(str(booking["flight_number"]), classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Departure", classes="detailHeader"),
                    Label(str(booking["departure"]), classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Destination", classes="detailHeader"),
                    Label(str(booking["destination"]), classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Date Time of Takeoff", classes="detailHeader"),
                    Label(str(booking["departure_time"]), classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Date Time of Landing", classes="detailHeader"),
                    Label(str(booking["arrival_time"]), classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Travel Class", classes="detailHeader"),
                    Label(className, classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Total Price", classes="detailHeader"),
                    Label(f"${float(booking['price']):.2f}", classes="detailValue"),
                    classes="detailRow"
                ),
                Label("Sub Passengers (if any): ", classes="field_label"),
                Vertical(id="adminSubPassengerList"),
                id="adminBookingDetailScroll"
            ),
            Button("Back", id="back")
        )
        yield Footer()

    def on_mount(self) -> None:
        if dbManager.fetchActiveBookingByID(self.bookingID) is None:
            return
        container = self.query_one("#adminSubPassengerList", Vertical)
        subPassengers = dbManager.fetchSubPassengersByBooking(self.bookingID)
        if not subPassengers:
            container.mount(Label("No sub passengers.", classes="subtitle"))
            return
        for index, sub in enumerate(subPassengers, start=1):
            container.mount(
                Label(
                    f"{index}. {sub['first_name']} {sub['last_name']} | {sub['gender']} | {sub['nationality']} | {sub['date_of_birth']}"
                )
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()

class NewFlightScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== New Flight ===", classes="title"),
            VerticalScroll(
                Input(placeholder="Flight Number", id="flightNumber"),
                Input(placeholder="Departure", id="departure"),
                Input(placeholder="Destination", id="destination"),
                Input(placeholder="Date Time of Takeoff (YYYY-MM-DD HH:MM)", id="departureTime"),
                Input(placeholder="Date Time of Landing (YYYY-MM-DD HH:MM)", id="arrivalTime"),
                Input(placeholder="Base Price", id="standardPrice"),
                Label("Class Configuration", classes="field_label"),
                Horizontal(
                    Checkbox("Economy", id="includeEconomy", value=True),
                    Input(value="1", placeholder="Ratio", id="economyRatio"),
                    classes="classRatioRow"
                ),
                Horizontal(
                    Checkbox("Premium Economy", id="includePremiumEconomy", value=True),
                    Input(value="2.2", placeholder="Ratio", id="premiumEconomyRatio"),
                    classes="classRatioRow"
                ),
                Horizontal(
                    Checkbox("Business", id="includeBusiness"),
                    Input(value="3", placeholder="Ratio", id="businessRatio"),
                    classes="classRatioRow"
                ),
                Horizontal(
                    Checkbox("First", id="includeFirst"),
                    Input(value="6", placeholder="Ratio", id="firstRatio"),
                    classes="classRatioRow"
                ),
                Button("Create Flight", id="createFlight", variant="primary"),
                Button("Back", id="back"),
                id="newFlightForm"
            )
        )
        yield Footer()

    def selectedClassRatios(self):
        classConfigs = [
            ("economy", "includeEconomy", "economyRatio"),
            ("premium_economy", "includePremiumEconomy", "premiumEconomyRatio"),
            ("business", "includeBusiness", "businessRatio"),
            ("first", "includeFirst", "firstRatio"),
        ]
        classRatios = {}
        for className, includeID, ratioID in classConfigs:
            includeClass = self.query_one(f"#{includeID}", Checkbox).value
            if not includeClass:
                continue
            ratioText = self.query_one(f"#{ratioID}", Input).value.strip()
            try:
                ratioValue = float(ratioText)
            except ValueError:
                return None
            if ratioValue <= 0:
                return None
            classRatios[className] = ratioValue
        return classRatios

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id != "createFlight":
            return

        flightNumber = self.query_one("#flightNumber", Input).value.strip().upper()
        departure = self.query_one("#departure", Input).value.strip()
        destination = self.query_one("#destination", Input).value.strip()
        departureTime = self.query_one("#departureTime", Input).value.strip()
        arrivalTime = self.query_one("#arrivalTime", Input).value.strip()
        standardPriceText = self.query_one("#standardPrice", Input).value.strip()

        requiredValues = [flightNumber, departure, destination, departureTime, arrivalTime, standardPriceText]
        if any(not value for value in requiredValues):
            self.notify("Please complete all required fields.", severity="warning")
            return

        try:
            datetime.strptime(departureTime, "%Y-%m-%d %H:%M")
            datetime.strptime(arrivalTime, "%Y-%m-%d %H:%M")
        except ValueError:
            self.notify("Date time must be in format YYYY-MM-DD HH:MM", severity="error")
            return

        try:
            standardPrice = float(standardPriceText)
        except ValueError:
            self.notify("Base price must be a number.", severity="error")
            return
        if standardPrice <= 0:
            self.notify("Base price must be greater than 0.", severity="error")
            return

        classRatios = self.selectedClassRatios()
        if classRatios is None:
            self.notify("Class ratio must be a positive number.", severity="error")
            return
        if not classRatios:
            self.notify("Please select at least one class.", severity="warning")
            return

        flight = Flight(
            flightNumber=flightNumber,
            departure=departure,
            destination=destination,
            departureTime=departureTime,
            arrivalTime=arrivalTime,
            classesAvailable=list(classRatios.keys()),
            classRatios=classRatios,
            standardPrice=standardPrice,
        )
        try:
            dbManager.newFlight(flight)
        except sqlite3.IntegrityError:
            self.notify("Flight number already exists.", severity="error")
            return

        self.notify("New flight created.", severity="information")
        self.app.pop_screen()

class ManageFlightsScreen(Screen):
    def __init__(self):
        super().__init__()
        self.flightMap = {}

    def flightSummaryText(self, row):
        return f"{row['flight_number']} | {row['departure']} -> {row['destination']} | {str(row['departure_time'])[:16]}"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Manage Flights ===", classes="title"),
            Label("Select a flight to view details.", classes="subtitle"),
            VerticalScroll(
                Vertical(id="flightList"),
                id="flightListScroll"
            ),
            Button("Back", id="back")
        )
        yield Footer()

    async def loadFlights(self):
        rows = dbManager.fetchAllFlights()
        flightList = self.query_one("#flightList", Vertical)
        await flightList.remove_children()
        self.flightMap = {}
        if not rows:
            flightList.mount(Label("No flights found.", classes="subtitle"))
            return
        for row in rows:
            flightID = str(row["flight_id"])
            self.flightMap[flightID] = row
            flightList.mount(
                Button(
                    self.flightSummaryText(row),
                    id=f"flight_{flightID}"
                )
            )

    async def on_mount(self) -> None:
        await self.loadFlights()

    async def on_screen_resume(self) -> None:
        await self.loadFlights()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if not event.button.id or not event.button.id.startswith("flight_"):
            return
        flightID = event.button.id.replace("flight_", "", 1)
        selectedFlight = self.flightMap.get(flightID)
        if selectedFlight is None:
            self.notify("Flight not found.", severity="error")
            return
        self.app.push_screen(FlightDetailScreen(flightID))

class FlightDetailScreen(Screen):
    def __init__(self, flightID):
        super().__init__()
        self.flightID = flightID

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Flight Details ===", classes="title"),
            VerticalScroll(
                Horizontal(
                    Label("Flight ID", classes="detailHeader"),
                    Label("", id="detailFlightID", classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Flight Number", classes="detailHeader"),
                    Label("", id="detailFlightNumber", classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Departure", classes="detailHeader"),
                    Label("", id="detailDeparture", classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Destination", classes="detailHeader"),
                    Label("", id="detailDestination", classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Date Time of Takeoff", classes="detailHeader"),
                    Label("", id="detailTakeoff", classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Date Time of Landing", classes="detailHeader"),
                    Label("", id="detailLanding", classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Base Price", classes="detailHeader"),
                    Label("", id="detailBasePrice", classes="detailValue"),
                    classes="detailRow"
                ),
                Horizontal(
                    Label("Class Ratios", classes="detailHeader"),
                    Label("", id="detailClassRatios", classes="detailValue"),
                    classes="detailRow"
                ),
                id="flightDetailScroll"
            ),
            Horizontal(
                Button("Edit Flight", id="editFlight", variant="primary"),
                Button("Delete Flight", id="deleteFlight", variant="error"),
                classes="detailActionRow"
            ),
            Button("Back", id="back")
        )
        yield Footer()

    def refreshDetail(self):
        flightRow = dbManager.fetchFlightByID(self.flightID)
        if flightRow is None:
            self.notify("Flight not found.", severity="error")
            self.app.pop_screen()
            return
        classRatios = dbManager.parseClassRatios(flightRow["classes_available"])
        classRatioText = ", ".join([f"{className}: {ratio:g}" for className, ratio in classRatios.items()]) if classRatios else "N/A"
        self.query_one("#detailFlightID", Label).update(str(flightRow["flight_id"]))
        self.query_one("#detailFlightNumber", Label).update(str(flightRow["flight_number"]))
        self.query_one("#detailDeparture", Label).update(str(flightRow["departure"]))
        self.query_one("#detailDestination", Label).update(str(flightRow["destination"]))
        self.query_one("#detailTakeoff", Label).update(str(flightRow["departure_time"]))
        self.query_one("#detailLanding", Label).update(str(flightRow["arrival_time"]))
        self.query_one("#detailBasePrice", Label).update(f"${float(flightRow['standard_price']):.2f}")
        self.query_one("#detailClassRatios", Label).update(classRatioText)

    def on_mount(self) -> None:
        self.refreshDetail()

    def on_screen_resume(self) -> None:
        self.refreshDetail()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "editFlight":
            self.app.push_screen(EditFlightScreen(self.flightID))
            return
        if event.button.id == "deleteFlight":
            success, message = dbManager.deleteFlight(self.flightID)
            self.notify(message, severity="information" if success else "error")
            if success:
                self.app.pop_screen()
            return
        if event.button.id == "back":
            self.app.pop_screen()

class EditFlightScreen(Screen):
    def __init__(self, flightID):
        super().__init__()
        self.flightID = flightID

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Edit Flight ===", classes="title"),
            VerticalScroll(
                Input(placeholder="Flight Number", id="flightNumber"),
                Input(placeholder="Departure", id="departure"),
                Input(placeholder="Destination", id="destination"),
                Input(placeholder="Date Time of Takeoff (YYYY-MM-DD HH:MM)", id="departureTime"),
                Input(placeholder="Date Time of Landing (YYYY-MM-DD HH:MM)", id="arrivalTime"),
                Input(placeholder="Base Price", id="standardPrice"),
                Label("Class Configuration", classes="field_label"),
                Horizontal(
                    Checkbox("Economy", id="includeEconomy"),
                    Input(placeholder="Ratio", id="economyRatio"),
                    classes="classRatioRow"
                ),
                Horizontal(
                    Checkbox("Premium Economy", id="includePremiumEconomy"),
                    Input(placeholder="Ratio", id="premiumEconomyRatio"),
                    classes="classRatioRow"
                ),
                Horizontal(
                    Checkbox("Business", id="includeBusiness"),
                    Input(placeholder="Ratio", id="businessRatio"),
                    classes="classRatioRow"
                ),
                Horizontal(
                    Checkbox("First", id="includeFirst"),
                    Input(placeholder="Ratio", id="firstRatio"),
                    classes="classRatioRow"
                ),
                Button("Save Changes", id="saveFlight", variant="primary"),
                Button("Back", id="back"),
                id="editFlightForm"
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        flightRow = dbManager.fetchFlightByID(self.flightID)
        if flightRow is None:
            self.notify("Flight not found.", severity="error")
            self.app.pop_screen()
            return

        self.query_one("#flightNumber", Input).value = str(flightRow["flight_number"])
        self.query_one("#departure", Input).value = str(flightRow["departure"])
        self.query_one("#destination", Input).value = str(flightRow["destination"])
        self.query_one("#departureTime", Input).value = str(flightRow["departure_time"])
        self.query_one("#arrivalTime", Input).value = str(flightRow["arrival_time"])
        self.query_one("#standardPrice", Input).value = str(flightRow["standard_price"])

        classRatios = dbManager.parseClassRatios(flightRow["classes_available"])
        classConfigs = [
            ("economy", "includeEconomy", "economyRatio"),
            ("premium_economy", "includePremiumEconomy", "premiumEconomyRatio"),
            ("business", "includeBusiness", "businessRatio"),
            ("first", "includeFirst", "firstRatio"),
        ]
        for className, includeID, ratioID in classConfigs:
            ratio = classRatios.get(className)
            includeWidget = self.query_one(f"#{includeID}", Checkbox)
            ratioWidget = self.query_one(f"#{ratioID}", Input)
            includeWidget.value = ratio is not None
            ratioWidget.value = f"{ratio:g}" if ratio is not None else str(defaultClasses.get(className, 1))

    def selectedClassRatios(self):
        classConfigs = [
            ("economy", "includeEconomy", "economyRatio"),
            ("premium_economy", "includePremiumEconomy", "premiumEconomyRatio"),
            ("business", "includeBusiness", "businessRatio"),
            ("first", "includeFirst", "firstRatio"),
        ]
        classRatios = {}
        for className, includeID, ratioID in classConfigs:
            includeClass = self.query_one(f"#{includeID}", Checkbox).value
            if not includeClass:
                continue
            ratioText = self.query_one(f"#{ratioID}", Input).value.strip()
            try:
                ratioValue = float(ratioText)
            except ValueError:
                return None
            if ratioValue <= 0:
                return None
            classRatios[className] = ratioValue
        return classRatios

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id != "saveFlight":
            return

        flightNumber = self.query_one("#flightNumber", Input).value.strip().upper()
        departure = self.query_one("#departure", Input).value.strip()
        destination = self.query_one("#destination", Input).value.strip()
        departureTime = self.query_one("#departureTime", Input).value.strip()
        arrivalTime = self.query_one("#arrivalTime", Input).value.strip()
        standardPriceText = self.query_one("#standardPrice", Input).value.strip()
        requiredValues = [flightNumber, departure, destination, departureTime, arrivalTime, standardPriceText]
        if any(not value for value in requiredValues):
            self.notify("Please complete all required fields.", severity="warning")
            return

        try:
            datetime.strptime(departureTime, "%Y-%m-%d %H:%M")
            datetime.strptime(arrivalTime, "%Y-%m-%d %H:%M")
        except ValueError:
            self.notify("Date time must be in format YYYY-MM-DD HH:MM", severity="error")
            return

        try:
            standardPrice = float(standardPriceText)
        except ValueError:
            self.notify("Base price must be a number.", severity="error")
            return
        if standardPrice <= 0:
            self.notify("Base price must be greater than 0.", severity="error")
            return

        classRatios = self.selectedClassRatios()
        if classRatios is None:
            self.notify("Class ratio must be a positive number.", severity="error")
            return
        if not classRatios:
            self.notify("Please select at least one class.", severity="warning")
            return

        flight = Flight(
            flightNumber=flightNumber,
            departure=departure,
            destination=destination,
            departureTime=departureTime,
            arrivalTime=arrivalTime,
            classesAvailable=list(classRatios.keys()),
            classRatios=classRatios,
            standardPrice=standardPrice,
            flightID=self.flightID,
        )
        try:
            dbManager.updateFlight(self.flightID, flight)
        except sqlite3.IntegrityError:
            self.notify("Flight number already exists.", severity="error")
            return
        self.notify("Flight updated.", severity="information")
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

class CreateAdminScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Create Admin Account ===", classes="title"),
            Input(placeholder="Email", id="email"),
            Input(placeholder="Password", password=True, id="password"),
            Input(placeholder="First name", id="first_name"),
            Input(placeholder="Last name", id="last_name"),
            Input(placeholder="Gender", id="gender"),
            Input(placeholder="Nationality", id="nationality"),
            Label("Date of birth", classes="field_label"),
            DatePicker(id="dob_row", defaultDate="1980-01-01"),
            Button("Create Admin", id="createAdmin", variant="primary"),
            Button("Back", id="back")
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id != "createAdmin":
            return

        dateOfBirth = self.query_one("#dob_row", DatePicker).value
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
        if not dateOfBirth:
            self.notify("Please select a complete date of birth", severity="warning")
            return

        try:
            datetime.strptime(dateOfBirth, "%Y-%m-%d")
        except ValueError:
            self.notify("Invalid date of birth", severity="error")
            return

        user = Admin(
            email=requiredValue["email"],
            password=requiredValue["password"],
            firstName=requiredValue["first_name"],
            lastName=requiredValue["last_name"],
            gender=requiredValue["gender"],
            nationality=requiredValue["nationality"],
            dateOfBirth=dateOfBirth,
        )
        success, message = dbManager.registerUser(user)
        self.notify(message, severity="information" if success else "error")
        if success:
            self.app.pop_screen()

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

    # Mock payment process (no credit card information required)
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
    # Styling of TUI
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
    .adminDashboardRoot {
        width: 120;
    }
    .adminTopRow {
        width: 100%;
        height: 21;
    }
    .adminPanel {
        width: 1fr;
        height: 1fr;
        padding: 1 2;
        border-title-align: center;
    }
    .adminOverviewPanel {
        border: solid round green;
        margin-right: 1;
    }
    .adminActionsPanel {
        border: solid round blue;
        margin-left: 1;
    }
    .adminBottomPanel {
        width: 100%;
        height: auto;
        border: solid round yellow;
        border-title-align: center;
        padding: 1;
        margin-top: 1;
    }
    .adminProfileButtons {
        width: 100%;
        height: auto;
    }
    .adminProfileButtons Button {
        width: 1fr;
        margin-right: 1;
    }
    .classRatioRow {
        width: 100%;
        height: auto;
    }
    .classRatioRow Input {
        width: 20;
    }
    .detailActionRow {
        width: 100%;
        height: auto;
        margin-top: 1;
    }
    .detailActionRow Button {
        width: 1fr;
        margin-right: 1;
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
