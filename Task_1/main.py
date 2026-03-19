import secrets
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Button, Label, Input
from textual.screen import Screen
import sqlite3

class User:
    def __init__(self, email, password, firstName, lastName, gender, nationality, dateOfBirth, user_id=None, is_admin=0):
        self.user_id = user_id if user_id else secrets.token_hex(4)
        self.email = email
        self.password = password
        self.firstName = firstName
        self.lastName = lastName
        self.gender = gender
        self.nationality = nationality
        self.dateOfBirth = dateOfBirth
        self.is_admin = is_admin


class Admin(User):
    def __init__(self, email, password, firstName, lastName, gender, nationality, dateOfBirth, user_id=None):
        super().__init__(email, password, firstName, lastName, gender, nationality, dateOfBirth, user_id=user_id, is_admin=1)


class Passenger(User):
    def __init__(self, email, password, firstName, lastName, gender, nationality, dateOfBirth, user_id=None):
        super().__init__(email, password, firstName, lastName, gender, nationality, dateOfBirth, user_id=user_id, is_admin=0)

class Flight:
    def __init__(self, flight_number, departure, destination, departure_time, arrival_time, classes_available, standard_price, flight_id=None):
        self.flight_id = flight_id
        self.flight_number = flight_number
        self.departure = departure
        self.destination = destination
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.classes_available = classes_available
        self.standard_price = standard_price


class Booking:
    def __init__(self, user_id, flight_id, travel_class, price, booking_id=None):
        self.booking_id = booking_id if booking_id else secrets.token_hex(4)
        self.user_id = user_id
        self.flight_id = flight_id
        self.travel_class = travel_class
        self.price = price

class DatabaseManager:
    def __init__(self, db_name="aeroflow.db"):
        self.db_name = db_name

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def register_user(self, user):
        pass

    def authenticate_user(self, email, password):
        pass

    def add_flight(self, flight):
        pass

    def search_flights(self, departure, destination, date):
        pass

    def create_booking(self, booking):
        pass

    def get_user_bookings(self, user_id):
        pass

default_classes = {
    "economy": 1.0,
    "premium_economy": 2.2,
    "business": 3.0,
    "first": 6.0
}

class LoginScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== User Login ===", classes="title"),
            Input(placeholder="Email", id="email"),
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
            self.notify(f"Logging in as '{email}'...")
            self.notify("[ Login Successful ]")
            self.app.pop_screen()

class RegisterScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Register ===", classes="title"),
            Label("Registration form coming soon..."),
            Button("Back", id="back")
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()

class FindFlightsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("=== Find Flights ===", classes="title"),
            Label("Search for flights here..."),
            Button("Back", id="back")
        )
        yield Footer()

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
        width: 40;
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
    """

    def on_mount(self) -> None:
        self.push_screen(MainMenu())

if __name__ == "__main__":
    app = AeroFlow()
    app.run()