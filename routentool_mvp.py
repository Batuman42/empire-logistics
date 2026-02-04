from flask import Flask, request, jsonify, render_template, redirect, url_for, Response
import sqlite3
import random
import io
import csv
from datetime import datetime, timedelta

app = Flask(__name__)

# --- 1. BASIS SETUP ---
def get_db_connection():
    conn = sqlite3.connect('lastmile.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def upgrade_db():
    db = get_db_connection()
    # Tabelle für Missionen
    db.execute('''CREATE TABLE IF NOT EXISTS sendungen 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, kunde TEXT, adresse TEXT, status TEXT)''')
    
    # Tabelle für KI-Gedächtnis (Machine Learning Basis)
    db.execute('''CREATE TABLE IF NOT EXISTS mission_log 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, v_type TEXT, wetter TEXT, erfolg INTEGER, profit REAL)''')
    
    # Fuhrpark/Garage
    db.execute('''CREATE TABLE IF NOT EXISTS garage 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, v_type TEXT, status TEXT, last_service TEXT)''')
    
    # Flotte initialisieren
    check = db.execute('SELECT count(*) as count FROM garage').fetchone()
    if check['count'] == 0:
        assets = [('Eco-1', '🚲 Lastenrad'), ('Trans-1', '🚐 Sprinter'), ('Heavy-1', '🚚 LKW'), ('Sky-1', '🚁 Drohne'), ('Rail-1', '🚆 Güterzug')]
        db.executemany('INSERT INTO garage (name, v_type, status, last_service) VALUES (?, ?, "Bereit", "2024-01-01")', assets)

    # Spalten-Updates (Empire-Features)
    columns = [
        ("maut", "REAL DEFAULT 0"), ("speed_factor", "REAL DEFAULT 0.0015"),
        ("profit", "REAL DEFAULT 0"), ("wetter", "TEXT DEFAULT 'Sonnig'"),
        ("type", "TEXT DEFAULT '🚚 LKW'"), ("priority", "TEXT DEFAULT 'Normal'"),
        ("lat_ziel", "REAL DEFAULT 51.0"), ("lon_ziel", "REAL DEFAULT 10.0"),
        ("distanz", "INTEGER DEFAULT 0"), ("eta", "TEXT DEFAULT '--:--'"),
        ("current_lat", "REAL"), ("current_lon", "REAL")
    ]
    for col, type_info in columns:
        try: db.execute(f"ALTER TABLE sendungen ADD COLUMN {col} {type_info}")
        except: pass
    db.commit()
    db.close()

upgrade_db()

# --- 2. KI GEDÄCHTNIS & PHYSIK ---

def get_ai_experience(v_type, wetter):
    db = get_db_connection()
    stats = db.execute('''SELECT AVG(erfolg) as rate FROM mission_log 
                          WHERE v_type = ? AND wetter = ?''', (v_type, wetter)).fetchone()
    db.close()
    # Wenn keine Erfahrung vorhanden, geben wir 1.0 (Neutral) zurück
    return stats['rate'] if stats['rate'] is not None else 1.0

def calculate_empire_logistics(dist, v_type, prio, kunde_name):
    db = get_db_connection()
    aktive = db.execute("SELECT COUNT(*) FROM sendungen WHERE status = 'Aktiv'").fetchone()[0]
    surge = 1.5 if aktive > 5 else 1.0
    db.close()

    wetter = random.choice(["Sonnig", "Regen", "Schnee", "Sturm"])
    wetter_multi = {"Sonnig": 1.0, "Regen": 1.1, "Schnee": 1.3, "Sturm": 1.6}[wetter]
    
    physics = {
        "🚲 Lastenrad": {"speed": 0.0008, "maut": 0.00, "rate": 2.5},
        "🚐 Sprinter":  {"speed": 0.0025, "maut": 0.05, "rate": 2.0},
        "🚚 LKW":       {"speed": 0.0015, "maut": 0.19, "rate": 1.8},
        "🚁 Drohne":    {"speed": 0.0060, "maut": 0.02, "rate": 4.5},
        "🚆 Güterzug":  {"speed": 0.0010, "maut": 0.10, "rate": 1.2}
    }.get(v_type, {"speed": 0.0015, "maut": 0.19, "rate": 1.8})

    maut = round(dist * physics['maut'], 2)
    profit = round(((dist * physics['rate']) * wetter_multi * surge - maut), 2)
    return maut, profit, physics['speed'], wetter

def add_delivery(kunde, adresse, v_type, prio):
    dist = random.randint(50, 800)
    maut, profit, speed, wetter = calculate_empire_logistics(dist, v_type, prio, kunde)
    
    db = get_db_connection()
    db.execute('''INSERT INTO sendungen 
                  (kunde, adresse, status, distanz, type, priority, profit, maut, speed_factor, wetter, lat_ziel, lon_ziel) 
                  VALUES (?, ?, 'Aktiv', ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
               (kunde, adresse, dist, v_type, prio, profit, maut, speed, wetter, random.uniform(48.5, 53.5), random.uniform(7.5, 12.5)))
    
    # Machine Learning: Wir loggen den Start der Mission als Erfahrung
    db.execute('INSERT INTO mission_log (v_type, wetter, erfolg, profit) VALUES (?, ?, ?, ?)', 
               (v_type, wetter, 1, profit)) # Wir nehmen erstmal Erfolg an
    db.commit()
    db.close()

# --- 3. ROUTES ---

@app.route('/ai_auto_dispatch', methods=['POST'])
def ai_dispatch():
    wetter = random.choice(["Sonnig", "Regen", "Schnee", "Sturm"])
    choices = ["🚲 Lastenrad", "🚐 Sprinter", "🚚 LKW", "🚁 Drohne", "🚆 Güterzug"]
    
    best_v = None
    best_score = -1
    
    for v in choices:
        # KI prüft Erfahrungswerte aus der DB
        experience = get_ai_experience(v, wetter)
        # Score basiert auf Erfahrung kombiniert mit etwas Zufall (Exploration)
        score = experience * random.uniform(0.7, 1.3)
        if score > best_score:
            best_score = score
            best_v = v

    add_delivery("AI-Learning-Agent", "Dynamic Hub", best_v, "Normal")
    return jsonify({"reply": f"KI lernt: Bei {wetter} ist {best_v} am effizientesten (Score: {best_score:.2f}). Mission gestartet!"})

@app.route('/dashboard')
def dashboard():
    db = get_db_connection()
    sendungen = db.execute('SELECT * FROM sendungen ORDER BY id DESC').fetchall()
    total_km = sum(s['distanz'] for s in sendungen) if sendungen else 0
    profit = sum(s['profit'] for s in sendungen) if sendungen else 0
    total_maut = sum(s['maut'] for s in sendungen) if sendungen else 0
    db.close()
    return render_template('index.html', sendungen=sendungen, total_km=total_km, active=len(sendungen), profit=profit, total_maut=total_maut)

# ... Restliche Routes (add_manual, export) wie gehabt ...

if __name__ == "__main__":
    app.run(debug=True)