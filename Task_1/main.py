import secrets

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