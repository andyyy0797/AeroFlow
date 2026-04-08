# AeroFlow (Task 1)

## 1) Project Introduction

AeroFlow is a terminal flight booking app built with Python and Textual.

Features for Passenger:
- Search flights by departure, destination, and date
- Book flights with up to 4 sub-passengers (5 people total)
- Payment simulation flow
- Passenger booking management

Features for Admin:
- Create flight
- Flights management (edit, delete)
- Create admin account
- Manage passenger's bookings

This project uses a SQLite database (`aeroflow.db`) for data storage.

## 2) How to Execute?

Please make sure that you are located in the `Task_1` folder and have `uv` installed, if not, execute the following command:

```bash
pip install uv
```

Step 0 (Optional): Execute these two commands to initialize the SQLite database with preset demo data:

```bash
uv run python tools/create_db.py
```

Step 1: Execute this command to install all required dependencies with `uv`:

```bash
uv sync
```

Step 2: Execute this command to start the application:

```bash
uv run python main.py
```

## 3) Demo Login Accounts

Use the following demo accounts to test AeroFlow:

### Admin
- Email: `admin@aeroflow.com`
- Password: `12345678`

### Passengers
- Email: `andywong@gmail.com`
- Password: `12345678`
- Note: this account has past booking records in database.

- Email: `johndoe@me.com`
- Password: `12345678`
- Note: this account is an empty passenger account (without any booking record).

## 4) Data Structure

The database has 4 tables:
- `users`
- `flights`
- `bookings`
- `sub_passengers`

### `users`
Stores account and profile data.
- `user_id` (`TEXT`, `PRIMARY KEY`)
- `email` (`TEXT`, `UNIQUE`, `NOT NULL`)
- `password` (`TEXT`, `NOT NULL`) - SHA-256 hash
- `first_name` (`TEXT`, `NOT NULL`)
- `last_name` (`TEXT`, `NOT NULL`)
- `gender` (`TEXT`)
- `nationality` (`TEXT`)
- `date_of_birth` (`TEXT`)
- `is_admin` (`INTEGER`, `NOT NULL`, `DEFAULT 0`)

### `flights`
Stores flight details and pricing data.
- `flight_id` (`INTEGER`, `PRIMARY KEY`, `AUTOINCREMENT`)
- `flight_number` (`TEXT`, `UNIQUE`, `NOT NULL`)
- `departure` (`TEXT`, `NOT NULL`)
- `destination` (`TEXT`, `NOT NULL`)
- `departure_time` (`TEXT`, `NOT NULL`)
- `arrival_time` (`TEXT`, `NOT NULL`)
- `classes_available` (`TEXT`, `NOT NULL`) - format like `economy:1,premium_economy:2.2,business:3`
- `standard_price` (`REAL`, `NOT NULL`)

### `bookings`
Stores booking records.
- `booking_id` (`TEXT`, `PRIMARY KEY`)
- `user_id` (`TEXT`, `NOT NULL`) - Foreign key to `users.user_id`
- `flight_id` (`INTEGER`, `NOT NULL`) - Foreign key to `flights.flight_id`
- `travel_class` (`TEXT`, `NOT NULL`)
- `price` (`REAL`, `NOT NULL`)
- `is_deleted` (`INTEGER`, `NOT NULL`, `DEFAULT 0`)

### `sub_passengers`
Stores extra passengers under one booking.
- `id` (`INTEGER`, `PRIMARY KEY`, `AUTOINCREMENT`)
- `booking_id` (`TEXT`, `NOT NULL`) - Foreign key to `bookings.booking_id`
- `first_name` (`TEXT`, `NOT NULL`)
- `last_name` (`TEXT`, `NOT NULL`)
- `gender` (`TEXT`, `NOT NULL`)
- `nationality` (`TEXT`, `NOT NULL`)
- `date_of_birth` (`TEXT`, `NOT NULL`)
