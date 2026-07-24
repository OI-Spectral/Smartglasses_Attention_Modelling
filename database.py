import sqlite3
import json
from a_models import Event

def create_database(args):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, brand TEXT NOT NULL, confidence REAL NOT NULL, dwell_seconds REAL NOT NULL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS brands (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)")
    cursor.execute("DELETE FROM events")

    with open(args.events_file, "r") as f:
        events = json.load(f)
    for event in events:
        cursor.execute("INSERT INTO events (timestamp, brand, confidence, dwell_seconds) VALUES (?, ?, ?, ?)", (event["timestamp"], event["brand"], event["confidence"], event["dwell_seconds"]))
        cursor.execute("INSERT OR IGNORE INTO brands (name) VALUES (?)", (event["brand"],))
    conn.commit()

    #cursor.execute("SELECT * FROM events")
    #rows = cursor.fetchall()
    #print(rows)
    conn.close()

def load_database():
    conn = sqlite3.connect('events.db')
    conn.row_factory = sqlite3.Row #to make tuple accessible by column name
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()
    
    conn.close()
    return [Event(event["timestamp"], event["brand"], event["confidence"], event["dwell_seconds"]) for event in rows]

def total_dwell_per_brand():
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    cursor.execute("SELECT brand, SUM(dwell_seconds) FROM events GROUP BY brand ORDER BY SUM(dwell_seconds) DESC")
    results = cursor.fetchall()
    print("Total dwell time per brand:")
    for row in results:
        print(f"{row[0]}: {row[1]} seconds")
    conn.close()

if __name__ == "__main__":
    create_database()
    load_database()
    total_dwell_per_brand()
