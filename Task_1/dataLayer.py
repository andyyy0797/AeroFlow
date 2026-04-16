import secrets
from abc import ABC, abstractmethod

class User(ABC):
    def __init__(self, email, password, firstName, lastName, gender, nationality, dateOfBirth, userID=None, isAdmin=0):
        self.userID = userID if userID else secrets.token_hex(4)
        self.email = email
        self.__password = password
        self.firstName = firstName
        self.lastName = lastName
        self.gender = gender
        self.nationality = nationality
        self.dateOfBirth = dateOfBirth
        self.isAdmin = isAdmin

    def getPassword(self):
        return self.__password

    def setPassword(self, password):
        self.__password = password

    # Encapsulation for password, a sensitive data
    @property
    def password(self):
        return self.getPassword()

    @password.setter
    def password(self, password):
        self.setPassword(password)

    # Abstraction: subclasses must declare their role
    @abstractmethod
    def getRole(self) -> str:
        pass

    def __str__(self):
        return f"{self.firstName} {self.lastName} <{self.email}> [{self.getRole()}]"


class Admin(User):
    def __init__(self, email, password, firstName, lastName, gender, nationality, dateOfBirth, userID=None):
        super().__init__(email, password, firstName, lastName, gender, nationality, dateOfBirth, userID=userID, isAdmin=1)

    def getRole(self) -> str:
        return "admin"


class Passenger(User):
    def __init__(self, email, password, firstName, lastName, gender, nationality, dateOfBirth, userID=None):
        super().__init__(email, password, firstName, lastName, gender, nationality, dateOfBirth, userID=userID, isAdmin=0)

    def getRole(self) -> str:
        return "passenger"


class SubPassenger:
    def __init__(self, firstName, lastName, gender, nationality, dateOfBirth):
        self.firstName = firstName
        self.lastName = lastName
        self.gender = gender
        self.nationality = nationality
        self.dateOfBirth = dateOfBirth

    def __str__(self):
        return f"{self.firstName} {self.lastName} ({self.dateOfBirth})"


defaultClasses = {
    "economy": 1.0,
    "premium_economy": 2.2,
    "business": 3.0,
    "first": 6.0
}


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

    def __str__(self):
        return f"[{self.flightNumber}] {self.departure} -> {self.destination} @ {self.departureTime}"


# ADT: a bounded collection of sub-passengers (max 4, so total passengers <= 5)
class PassengerList:
    MAX_CAPACITY = 4

    def __init__(self):
        self._items = []

    def add(self, passenger: SubPassenger):
        if len(self._items) >= self.MAX_CAPACITY:
            raise ValueError("A booking can have a maximum of 5 passengers.")
        self._items.append(passenger)

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def __repr__(self):
        return f"PassengerList({self._items!r})"


class Booking:
    def __init__(self, userID, flightID, travel_class, price, bookingID=None, sub_passengers=None):
        self.bookingID = bookingID if bookingID else secrets.token_hex(4)
        self.userID = userID
        self.flightID = flightID
        self.travel_class = travel_class
        self.price = price
        self.sub_passengers = PassengerList()
        for sp in (sub_passengers or []):
            self.sub_passengers.add(sp)

    def __str__(self):
        return f"Booking {self.bookingID}: Flight {self.flightID} [{self.travel_class}] ${float(self.price):.2f}"
