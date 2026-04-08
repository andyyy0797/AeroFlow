import json
import random
import secrets
from datetime import datetime, timedelta

target = 50000
startDate = datetime(2026, 5, 20)
endDate = datetime(2026, 8, 20)

destinations = {
    "Tier 1 (Popular)": ["Tokyo, Japan", "Osaka, Japan", "Seoul, Korea", "Taipei", "Fukuoka, Japan", "Sapporo, Japan", "Okinawa, Japan", "Beijing", "Shanghai"],
    "Tier 2 (Secondary)": ["Changi, Singapore", "Bangkok, Thailand", "Kuala Lumpur, Malaysia", "Da Nang, Vietnam"],
    "Tier 3 (Other)": ["London, UK", "New York, USA", "Rome, Italy", "Sydney, Australia", "Vancouver, Canada"]
}

domains = ["gmail.com", "outlook.com", "yahoo.com.hk", "icloud.com", "me.com", "live.hkmu.edu.hk"]

weighting = ([60] * len(destinations["Tier 1 (Popular)"]) + [30] * len(destinations["Tier 2 (Secondary)"]) + [10] * len(destinations["Tier 3 (Other)"]))

destinationSum = destinations["Tier 1 (Popular)"] + destinations["Tier 2 (Secondary)"] + destinations["Tier 3 (Other)"]

def normalizedNamePart(name: str) -> str:
    lowered = name.lower()
    return "".join(character for character in lowered if character.isalpha())

def birthdayNumberPart(dateOfBirth: str) -> str:
    year, month, day = dateOfBirth.split("-")
    mode = random.choice(["year", "monthDay", "all"])
    if mode == "year":
        components = [year]
    elif mode == "monthDay":
        components = [month, day]
    else:
        components = [year, month, day]
    random.shuffle(components)
    return "".join(components)

def randomNumberPart() -> str:
    length = random.randint(2, 4)
    number = random.randint(0, (10 ** length) - 1)
    return str(number).zfill(length)

def generateDummyEmail(profile: dict) -> str:
    firstName = normalizedNamePart(profile["firstName"])
    lastName = normalizedNamePart(profile["lastName"])
    domain = random.choice(domains)

    useLastName = random.choice([True, False])
    if useLastName:
        separator = random.choice(["_", "-"])
        localPart = f"{firstName}{separator}{lastName}"
    else:
        localPart = firstName

    addNumber = random.choice([True, False])
    if addNumber:
        useBirthday = random.choice([True, False])
        suffix = birthdayNumberPart(profile["dateOfBirth"]) if useBirthday else randomNumberPart()
        localPart = f"{localPart}{suffix}"

    return f"{localPart}@{domain}"

def generateBookingID(existingBookingIDs: set[str], hashLength: int = 12) -> str:
    while True:
        bookingID = secrets.token_hex(hashLength // 2)
        if bookingID not in existingBookingIDs:
            existingBookingIDs.add(bookingID)
            return bookingID

def generateProfile(ageRange):
    fName = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Andrew", "Mark"]
    lName = ["Wong", "Chan", "Lee", "Cheung", "Ng", "Lau", "Choi", "Ho", "Yiu", "WANG", "ZHANG", "Liu", "LIU", "Yung", "CHEN"]
    gender = random.choice(["M", "F"])
    age = random.randint(ageRange[0], ageRange[1])

    dobYear = 2026 - age
    dob = f"{dobYear}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    
    return {
        "firstName": random.choice(fName),
        "lastName": random.choice(lName),
        "gender": gender,
        "nationality": "Hong Kong, China",
        "dateOfBirth": dob,
        "age": age
    }

def genMockData():
    bookings = []
    existingBookingIDs = set()
    
    for i in range(target):
        deltaDays = (endDate - startDate).days
        departureDate = startDate + timedelta(days=random.randint(0, deltaDays))
        
        isGradTrip = departureDate.month <= 6
        
        subPassengers = []
        if isGradTrip:
            primaryAge = (17, 19)
            subTotal = random.randint(1, 4)
            primaryPassenger = generateProfile(primaryAge)
            for _ in range(subTotal):
                subPassengers.append(generateProfile((17, 19)))
        else:
            primaryAge = (35, 55)
            subTotal = random.randint(2, 4)
            primaryPassenger = generateProfile(primaryAge)

            subPassengers.append(generateProfile((35, 55)))

            for _ in range(subTotal - 1):
                subPassengers.append(generateProfile((5, 18)))

        dest = random.choices(destinationSum, weights=weighting, k=1)[0]
        
        returnDate = departureDate + timedelta(days=random.randint(5, 14))
        
        travelClass = random.choices(["economy", "premium_economy", "business"], weights=[80, 15, 5], k=1)[0]
        basePrice = random.randint(2000, 8000)
        totalPrice = basePrice * (1 + len(subPassengers))

        record = {
            "booking_id": generateBookingID(existingBookingIDs),
            "user_email": generateDummyEmail(primaryPassenger),
            "primary_passenger": primaryPassenger,
            "flight_info": {
                "departure": "Hong Kong",
                "destination": dest,
                "departure_time": departureDate.strftime("%Y-%m-%d 10:00"),
                "return_time": returnDate.strftime("%Y-%m-%d 18:00"),
            },
            "travelClass": travelClass,
            "totalPrice": totalPrice,
            "sub_passengers": subPassengers
        }
        bookings.append(record)

    with open("mockBookings.json", "w", encoding="utf-8") as f:
        json.dump(bookings, f, indent=4)
    
    print(f"Finished! Generated {target} records in mockBookings.json")

if __name__ == "__main__":
    genMockData()
