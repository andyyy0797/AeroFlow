import secrets
import curses

class User:
    def __init__(self, email, password, firstName, lastName, gender, nationality, dateOfBirth):
        self.email = email
        self.password = password
        self.firstName = firstName
        self.lastName = lastName
        self.gender = gender
        self.nationality = nationality
        self.dateOfBirth = dateOfBirth


class Admin(User):
    def __init__(self, email, password, firstName, lastName, gender, nationality, dateOfBirth):
        super().__init__(email, password, firstName, lastName, gender, nationality, dateOfBirth)


class Passenger(User):
    def __init__(self, email, password, firstName, lastName, gender, nationality, dateOfBirth):
        super().__init__(email, password, firstName, lastName, gender, nationality, dateOfBirth)
        self.passenger_id = secrets.token_hex(5)

class Flight:
    def __init__(self, flight_number, departure, destination, departure_time, arrival_time, classes_available, standard_price):
        self.flight_number = flight_number
        self.departure = departure
        self.destination = destination
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.classes_available = classes_available
        self.standard_price = standard_price


class Booking:
    def __init__(self, passenger, flight, travel_class, price):
        self.booking_id = secrets.token_hex(8)
        self.passenger = passenger
        self.flight = flight
        self.travel_class = travel_class
        self.price = price

default_classes = {
    "Economy": 1.0,
    "Premium Economy": 2.2,
    "Business": 3.0,
    "First Class": 6.0
}
def login_page(screen):
    screen.clear()
    screen.addstr(1, 2, "=== Login ===", curses.A_BOLD)
    screen.addstr(3, 2, "Login feature coming soon...")
    screen.addstr(5, 2, "[Press any key to go back]")
    screen.refresh()
    screen.getch()

def register_page(screen):
    screen.clear()
    screen.addstr(1, 2, "=== Register ===", curses.A_BOLD)
    screen.addstr(3, 2, "Registration form coming soon...")
    screen.addstr(5, 2, "[Press any key to go back]")
    screen.refresh()
    screen.getch()

def find_flights_page(screen):
    screen.clear()
    screen.addstr(1, 2, "=== Find Flights ===", curses.A_BOLD)
    screen.addstr(3, 2, "Search for flights here...")
    screen.addstr(5, 2, "[Press any key to go back]")
    screen.refresh()
    screen.getch()

def Menu(screen):
    curses.curs_set(0)
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    options = ["Login", "Register", "Find Flights", "Exit"]
    current_row = 0

    while True:
        screen.clear()
        
        title = "=== AeroFlow ==="
        screen.addstr(1, 2, title, curses.A_BOLD)
        screen.addstr(2, 2, "Use UP/DOWN arrows to navigate, and ENTER to select.", curses.A_DIM)

        for idx, row in enumerate(options):
            x = 4
            y = 4 + idx
            if idx == current_row:
                screen.attron(curses.color_pair(1) | curses.A_BOLD)
                screen.addstr(y, x, f"> {row}")
                screen.attroff(curses.color_pair(1) | curses.A_BOLD)
            else:
                screen.addstr(y, x, f"  {row}")
        
        screen.refresh()
        key = screen.getch()
        
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            if options[current_row] == "Exit":
                break
            elif options[current_row] == "Login":
                login_page(screen)
            elif options[current_row] == "Register":
                register_page(screen)
            elif options[current_row] == "Find Flights":
                find_flights_page(screen)

if __name__ == "__main__":
    curses.wrapper(Menu)