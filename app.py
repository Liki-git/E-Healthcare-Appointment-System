from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import re
from datetime import date

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET', 'dev_secret_for_demo_only')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    """Create database tables and seed a static doctors list if needed."""
    if not os.path.exists(DB_PATH):
        conn = get_db()
        cur = conn.cursor()
        cur.executescript(
            '''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );

            CREATE TABLE doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialization TEXT
            );

            CREATE TABLE appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
            );
            '''
        )
        # Seed doctors
        doctors = [
            ('Dr. Aisha Khan', 'General Physician'),
            ('Dr. Rajesh Iyer', 'Cardiologist'),
            ('Dr. Emily Stone', 'Dermatologist'),
            ('Dr. Michael Brown', 'Pediatrics')
        ]
        cur.executemany('INSERT INTO doctors (name, specialization) VALUES (?, ?)', doctors)
        conn.commit()
        conn.close()


init_db()


def ensure_doctors_and_schema():
    """Ensure a wider list of doctors exists and appointments schema has extra columns."""
    conn = get_db()
    cur = conn.cursor()

    # Telugu and other local names to ensure in doctors table
    doctors_needed = [
        ('Dr. Anil Reddy', 'General Physician'),
        ('Dr. Kalyani Rao', 'Gynecologist'),
        ('Dr. Suresh Kumar', 'Orthopedics'),
        ('Dr. Ramesh Babu', 'Pediatrics'),
        ('Dr. Lakshmi Devi', 'Dermatologist'),
        ('Dr. Prasad V', 'Cardiologist'),
        ('Dr. Roja Srinivas', 'ENT'),
        ('Dr. Naveen Teja', 'General Physician'),
        ('Dr. Kavya Naidu', 'Endocrinologist'),
        ('Dr. Sridhar Reddy', 'Nephrologist')
    ]

    for name, spec in doctors_needed:
        cur.execute('SELECT id FROM doctors WHERE name = ? AND specialization = ?', (name, spec))
        if cur.fetchone() is None:
            cur.execute('INSERT INTO doctors (name, specialization) VALUES (?, ?)', (name, spec))

    # Ensure appointments table has 'reason', 'phone' and 'status' columns (SQLite supports ADD COLUMN)
    cur.execute("PRAGMA table_info(appointments)")
    cols = [r[1] for r in cur.fetchall()]
    if 'reason' not in cols:
        cur.execute("ALTER TABLE appointments ADD COLUMN reason TEXT")
    if 'phone' not in cols:
        cur.execute("ALTER TABLE appointments ADD COLUMN phone TEXT")
    if 'status' not in cols:
        cur.execute("ALTER TABLE appointments ADD COLUMN status TEXT DEFAULT 'Scheduled'")

    # Ensure existing rows have a status value
    cur.execute("UPDATE appointments SET status = 'Scheduled' WHERE status IS NULL OR status = ''")

    conn.commit()
    conn.close()


# Run the ensure step to add doctors and migrate schema when needed
ensure_doctors_and_schema()


def query_db(query, args=(), one=False):
    conn = get_db()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    conn.close()
    return (rv[0] if rv else None) if one else rv


def login_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*a, **kw):
        if 'user_id' not in session:
            flash('Please log in to view that page.', 'warning')
            return redirect(url_for('login'))
        return fn(*a, **kw)

    return wrapper


@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = query_db('SELECT id, name, email FROM users WHERE id = ?', (user_id,), one=True)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))

        # Validate username uniqueness (case-insensitive)
        existing_name = query_db('SELECT id FROM users WHERE lower(name) = ?', (name.lower(),), one=True)
        if existing_name:
            flash('Username is already taken.', 'danger')
            return redirect(url_for('register'))

        # Password complexity: at least 8 chars, contains letter and number
        if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            flash('Password must be at least 8 characters and include letters and numbers.', 'danger')
            return redirect(url_for('register'))

        # Check existing email
        existing = query_db('SELECT id FROM users WHERE email = ?', (email,), one=True)
        if existing:
            flash('Email is already registered.', 'danger')
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
                        (name, email, password_hash))
            conn.commit()
        except sqlite3.IntegrityError:
            # Catch any unexpected UNIQUE constraint failure
            flash('An account with that email or username already exists.', 'danger')
            conn.close()
            return redirect(url_for('register'))
        finally:
            conn.close()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = query_db('SELECT * FROM users WHERE email = ?', (email,), one=True)
        if user is None:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

        if not check_password_hash(user['password_hash'], password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

        # Successful login
        session.clear()
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        flash('Logged in successfully.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=g.user)


@app.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    doctors = query_db('SELECT * FROM doctors')

    if request.method == 'POST':
        doctor_id = request.form.get('doctor')
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        reason = request.form.get('reason', '').strip()
        phone = request.form.get('phone', '').strip()

        # Basic validation
        if not doctor_id or not date_str or not time_str:
            flash('All fields are required.', 'danger')
            return redirect(url_for('book'))

        try:
            appt_date = date.fromisoformat(date_str)
        except Exception:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('book'))

        if appt_date < date.today():
            flash('Cannot book an appointment in the past.', 'danger')
            return redirect(url_for('book'))

        # Prevent double booking
        exists = query_db('''
            SELECT id FROM appointments
            WHERE doctor_id = ? AND date = ? AND time = ?
        ''', (doctor_id, date_str, time_str), one=True)

        if exists:
            flash('This slot is already booked for the chosen doctor.', 'danger')
            return redirect(url_for('book'))

        conn = get_db()
        cur = conn.cursor()
        cur.execute('INSERT INTO appointments (user_id, doctor_id, date, time, reason, phone) VALUES (?, ?, ?, ?, ?, ?)',
                (session['user_id'], doctor_id, date_str, time_str, reason, phone))
        conn.commit()
        conn.close()

        flash('Appointment booked successfully.', 'success')
        return redirect(url_for('appointments'))

    return render_template('book_appointment.html', doctors=doctors)


@app.route('/appointments')
@login_required
def appointments():
    appts = query_db('''
        SELECT a.id, a.date, a.time, a.reason, a.phone, a.status, d.name as doctor_name, d.specialization
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.user_id = ?
        ORDER BY a.date, a.time
    ''', (session['user_id'],))

    return render_template('my_appointments.html', appointments=appts)


@app.route('/cancel/<int:appointment_id>', methods=['POST'])
@login_required
def cancel(appointment_id):
    appt = query_db('SELECT * FROM appointments WHERE id = ?', (appointment_id,), one=True)
    if not appt:
        flash('Appointment not found.', 'danger')
        return redirect(url_for('appointments'))

    if appt['user_id'] != session['user_id']:
        flash('You are not authorized to cancel this appointment.', 'danger')
        return redirect(url_for('appointments'))

    conn = get_db()
    cur = conn.cursor()
    # Soft-delete by setting status to 'Cancelled' for auditability
    cur.execute("UPDATE appointments SET status = 'Cancelled' WHERE id = ?", (appointment_id,))
    conn.commit()
    conn.close()

    flash('Appointment cancelled successfully.', 'success')
    return redirect(url_for('appointments'))


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)