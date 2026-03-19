# Task 1: AeroFlow Main Program

## Data Structure

A SQLite database (`aeroflow.db`) was implemented in this project, it consists of three tables to manage **users**, **flights**, and **booking records**.

### `users` Table
Stores user information, differentiating between **Admins** and **Passengers** using the `is_admin` column. Both roles use a generated hash as their primary identifier.
* **`user_id`** (`TEXT`, `PRIMARY KEY`) - *A generated unique hash string.*
* **`email`** (`TEXT`, `UNIQUE`, `NOT NULL`)
* **`password`** (`TEXT`, `NOT NULL`)
* **`first_name`** (`TEXT`, `NOT NULL`)
* **`last_name`** (`TEXT`, `NOT NULL`)
* **`gender`** (`TEXT`)
* **`nationality`** (`TEXT`)
* **`dob`** (`DATE`)
* **`is_admin`** (`INTEGER`, `NOT NULL`, `DEFAULT 0`) - *`0` represents general passenger, `1` represents admin.*

---

### `flights` Table
Stores details of all available flights in the system.
* **`id`** (`INTEGER`, `PRIMARY KEY`, `AUTOINCREMENT`)
* **`flight_number`** (`TEXT`, `UNIQUE`, `NOT NULL`)
* **`departure`** (`TEXT`, `NOT NULL`)
* **`destination`** (`TEXT`, `NOT NULL`)
* **`departure_time`** (`DATETIME`, `NOT NULL`)
* **`arrival_time`** (`DATETIME`, `NOT NULL`)
* **`standard_price`** (`REAL`, `NOT NULL`)
* **`classes_available`** (`TEXT`)

---

### `bookings` Table
Links a specific user to a particular flight to record their reservation.
* **`booking_id`** (`TEXT`, `PRIMARY KEY`) - *A generated unique hash string.*
* **`user_id`** (`TEXT`, `NOT NULL`) - *Foreign Key referencing `users(user_id)`.*
* **`flight_id`** (`INTEGER`, `NOT NULL`) - *Foreign Key referencing `flights(id)`.*
* **`travel_class`** (`TEXT`, `NOT NULL`)
* **`price`** (`REAL`, `NOT NULL`)
