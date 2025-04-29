from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import random
import string
import os
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

USER_DB = 'database/users.db'
APPOINTMENT_DB = 'database/appointments.db'

def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        fingerprint_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        conn = get_db_connection(USER_DB)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (first_name, last_name, email, phone, fingerprint_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (first_name, last_name, email, phone, fingerprint_id))
            conn.commit()
            flash(f"✅ Registered! Your Fingerprint ID: {fingerprint_id}", 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('⚠️ Email already exists.', 'danger')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        first_name = request.form['first_name']
        fingerprint_id = request.form['fingerprint_id']

        conn = get_db_connection(USER_DB)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE first_name = ? AND fingerprint_id = ?', (first_name, fingerprint_id))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            flash('✅ Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('❌ Invalid credentials.', 'danger')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection(APPOINTMENT_DB)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT doctor_name, appointment_date, appointment_time
    FROM appointments
    WHERE patient_id = ?
    ''', (session['user_id'],))
    rows = cursor.fetchall()
    conn.close()

    appointments = [{
        'doctor_name': row['doctor_name'],
        'appointment_date': row['appointment_date'],
        'appointment_time': row['appointment_time']
    } for row in rows]

    return render_template('dashboard.html', appointments=appointments, first_name=session['first_name'], last_name=session['last_name'])

@app.route('/book', methods=['GET', 'POST'])
def book_appointment():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        doctor_name = request.form['doctor_name']
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']

        conn = get_db_connection(APPOINTMENT_DB)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (patient_id, doctor_name, appointment_date, appointment_time)
            VALUES (?, ?, ?, ?)
        ''', (session['user_id'], doctor_name, appointment_date, appointment_time))
        conn.commit()
        conn.close()

        flash('✅ Appointment booked!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('book.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('✅ Logged out.', 'info')
    return redirect(url_for('home'))

# --- WebAuthn Touch ID Routes ---
@app.route('/webauthn/register/start', methods=['POST'])
def webauthn_register_start():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    credential_id = base64.urlsafe_b64encode(os.urandom(32)).decode()

    conn = get_db_connection(USER_DB)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET credential_id = ? WHERE id = ?", (credential_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({'status': 'ok', 'credential_id': credential_id})

@app.route('/webauthn/login/start', methods=['POST'])
def webauthn_login_start():
    data = request.get_json()
    credential_id = data.get('credential_id')

    conn = get_db_connection(USER_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, first_name, last_name FROM users WHERE credential_id = ?", (credential_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user_id'] = user['id']
        session['first_name'] = user['first_name']
        session['last_name'] = user['last_name']
        return jsonify({'status': 'authenticated'})
    else:
        return jsonify({'error': 'No matching credential'}), 401

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', message="Page not found!"), 404

if __name__ == '__main__':
    app.run(debug=True, port=5001)
