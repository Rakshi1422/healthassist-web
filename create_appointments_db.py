import sqlite3

# Connect to users.db
conn = sqlite3.connect('database/users.db')
c = conn.cursor()

# Create users table (if not exists)
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    fingerprint_id TEXT NOT NULL UNIQUE
)
''')
conn.commit()
conn.close()

# Connect to appointments.db
conn = sqlite3.connect('database/appointments.db')
c = conn.cursor()

# Create appointments table (✅ doctor_name included now!)
c.execute('''
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_name TEXT NOT NULL,
    appointment_date TEXT NOT NULL,
    appointment_time TEXT NOT NULL,
    patient_id INTEGER NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES users(id)
)
''')
conn.commit()
conn.close()

print("✅ Databases created successfully!")
