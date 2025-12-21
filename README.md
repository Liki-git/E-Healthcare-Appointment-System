# E-Healthcare Appointment Booking System

A simple Flask-based web application that allows users to register, login, view doctors, and book or cancel healthcare appointments.

This project is intended for learning and demonstration purposes.

---

## Features

- User registration and login
- View available doctors
- Book appointments with reason and phone number
- Cancel appointments
- SQLite database (auto-created on first run)
- Responsive UI using Bootstrap

---

## Tech Stack

- Backend: Python, Flask
- Frontend: HTML, CSS, Bootstrap
- Database: SQLite
- Testing: Python Smoke Test
- Version Control: Git

---

## How to Clone the Project

```bash
git clone https://github.com/jaswanthhitman45/E-Healthcare-Appointment-Booking-System.git
cd E-Healthcare-Appointment-Booking-System
How to Set Up and Run (Windows)
1. Create Virtual Environment
powershell
Copy code
python -m venv .venv
Activate the virtual environment:

powershell
Copy code
.\\.venv\\Scripts\\Activate.ps1
2. Install Dependencies
powershell
Copy code
pip install -r requirements.txt
3. Run the Application
powershell
Copy code
python app.py
Open a browser and go to:

cpp
Copy code
http://127.0.0.1:5000/
The database is created automatically on first run.

Optional: Run Smoke Test
powershell
Copy code
python test_smoke.py
