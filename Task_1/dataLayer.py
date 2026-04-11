import secrets


class User:
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
