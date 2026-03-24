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





user_db = {}
flight_db = {}
booking_db = {}

def input_loop(text):
  while True:
    try:
      user_input = str(input(text))
      if user_input != "":
        return user_input
        break
      else:
        print("Please enter a value.")
    except Exception as e:
      print('\nAn unexpected error occurred:', e, 'Please try again.')

def register_user():
  input_email = input_loop("Email: ")
  input_pw = input_loop("Password: ")
  input_Fname = input_loop("First name: ")
  inputLname = input_loop("Last name: ")
  inputGender = input_loop("Gender: ")
  inputNationality = input_loop("Nationality: ")
  inputDOB = input_loop("Date of birth: ")
  user = Passenger(input_email, input_pw, input_Fname, inputLname, inputGender, inputNationality, inputDOB)
  user_db[user.email.strip().lower()] = user

def authenticate_user(input_email, input_pw):
  if input_email.strip().low() in user_db:
    if user_db[input_email.strip().lower()].password == input_pw:
      return True
    else
      return "Wrong password"
  else
    return "Email not registered"

def get_booking_history(user_id):
  for booking_id, booking in booking_db.items():
    if getattr(booking, 'user_id', None) == user_id:
      print(f"ID: {booking_id}\n{booking.__dict__}\n\n")

def update_profile(user_id, update_field, new_info):
  settr(user_db[user_id], update_field, new_info)
  print("Profile updated")

def add_flight():
  flight_number = input_loop("Flight number: ")
  departure = input_loop("Departure: ")
  destination = input_loop("Destination: ")
  departure_time = input_loop("Departure time: ")
  arrival_time = input_loop("Arrival time: ")
  classes_available = input_loop("Classes available: ")
  standard_price = input_loop("Standard price: ")
  flight = Flight(flight_number, departure, destination, departure_time, arrival_time, classes_available, standard_price)
  flight_db[flight.flight_id] = flight
  print(f"Flight {flight.flight_number} is added. ID: {flight.flight_id}")

def search_flights(origin, dest, date):
  found = False
  for flight_id, flight in flight_db.items():
    if flight.departure == origin and flight.destination == dest;
      print(f"ID: {flight_id}\n{flight.__dict__}\n\n")
      found = True
    else:
      print("No flights found")


def display_flight_details(flight_id):
  for flight_id, flight in flight_db.items():
    if getattr(flight, 'user_id', None) == flight_id:
      print(f"ID: {flight_id}\n{flight.__dict__}\n\n")

def cancel_booking(booking_id):
  if booking_id in booking_db:
    del booking_db[booking_id]

register_user()
#for email, user in user_db.items():
  #print(f"{email}: {user.__dict__}")
