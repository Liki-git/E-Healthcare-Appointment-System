import requests
from datetime import date, timedelta
import random

BASE = 'http://127.0.0.1:5000'

def run():
    s = requests.Session()

    # Register
    name = 'Test User'
    email = f'test{random.randint(1000,9999)}@example.com'
    password = 'password123'
    print('Registering', email)
    r = s.post(BASE + '/register', data={'name': name, 'email': email, 'password': password}, allow_redirects=True)
    print('Register status', r.status_code)

    # Login
    r = s.post(BASE + '/login', data={'email': email, 'password': password}, allow_redirects=True)
    print('Login status', r.status_code)

    # Book appointment for tomorrow at 10:00 with doctor 1
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    payload = {'doctor': '1', 'date': tomorrow, 'time': '10:00'}
    r = s.post(BASE + '/book', data=payload, allow_redirects=True)
    print('Book status', r.status_code)

    # Get appointments
    r = s.get(BASE + '/appointments')
    print('Appointments page status', r.status_code)
    if 'No appointments' in r.text:
        print('No appointments found in response (unexpected).')
    else:
        # crude display
        start = r.text.find('<table')
        snippet = r.text[start:start+800]
        print('Appointments page snippet:\n', snippet)

if __name__ == '__main__':
    run()
