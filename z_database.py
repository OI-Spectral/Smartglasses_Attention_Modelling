# import sqlite3
# import json
# from a_models import Event

# def create_database(args):
#     conn = sqlite3.connect('events.db')
#     cursor = conn.cursor()
#     cursor.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, brand_id INTEGER NOT NULL, confidence REAL NOT NULL, dwell_seconds REAL NOT NULL)")
#     cursor.execute("CREATE TABLE IF NOT EXISTS brands (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE)")
#     cursor.execute("DELETE FROM events")

#     with open(args.events_file, "r") as f:
#         events = json.load(f)
#     for event in events:
#         cursor.execute("INSERT OR IGNORE INTO brands (name) VALUES (?)", (event["brand"],))
#         cursor.execute("SELECT id FROM brands WHERE name = ?", (event["brand"],))
#         brand_id = cursor.fetchone()[0]
#         cursor.execute("INSERT INTO events (timestamp, brand_id, confidence, dwell_seconds) VALUES (?, ?, ?, ?)", (event["timestamp"], brand_id, event["confidence"], event["dwell_seconds"]))
    
#     cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
#     cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_brand ON events(brand_id)") 

#     conn.commit()

#     #cursor.execute("SELECT * FROM events")
#     #rows = cursor.fetchall()
#     #print(rows)
#     conn.close()

# def load_database():
#     conn = sqlite3.connect('events.db')
#     conn.row_factory = sqlite3.Row #to make tuple accessible by column name
#     cursor = conn.cursor()
#     cursor.execute("""SELECT events.timestamp, brands.name AS brand, events.confidence, events.dwell_seconds 
#     FROM events 
#     JOIN brands ON events.brand_id = brands.id""")
#     rows = cursor.fetchall()
#     conn.close()

#     return [Event(event["timestamp"], event["brand"], event["confidence"], event["dwell_seconds"]) for event in rows]

# def total_dwell_per_brand():
#     conn = sqlite3.connect('events.db')
#     cursor = conn.cursor()
#     cursor.execute("""SELECT brands.name AS brand, SUM(dwell_seconds) 
#     FROM events
#     JOIN brands ON events.brand_id = brands.id
#     GROUP BY brand 
#     ORDER BY SUM(dwell_seconds) DESC""")
#     results = cursor.fetchall()
#     print("Total dwell time per brand:")
#     for row in results:
#         print(f"{row[0]}: {row[1]} seconds")
#     conn.close()

# if __name__ == "__main__":
#     import argparse
#     parser = argparse.ArgumentParser(description="Load events from a JSON file into events.db.")
#     parser.add_argument("events_file", help="Path to the events JSON file.")
#     args = parser.parse_args()

#     create_database(args)
#     load_database()
#     total_dwell_per_brand()
