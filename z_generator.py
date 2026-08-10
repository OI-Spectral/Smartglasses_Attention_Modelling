# import json, random
# from datetime import datetime, timedelta

# def generate_events():
#     random.seed()  # same "random" data every run — crucial for testing, if I place seed value inside random.seed()

#     brands = ["Nike", "Adidas", "Coca-Cola", "Apple", "Spotify", "Red Bull"]
#     events = []
#     t = datetime(2026, 6, 16, 0, 0, 0)

#     for _ in range(500):
#         t += timedelta(seconds=random.randint(1, 100))
#         events.append({
#             "timestamp": t.isoformat(),
#             "brand": random.choice(brands),
#             "confidence": round(random.uniform(0.6, 0.99), 2),
#             "dwell_seconds": round(random.uniform(0.5, 6.0), 1),
#         })    

#     with open("events.json", "w") as f:
#         json.dump(events, f, indent=2)

#     print(f"Wrote {len(events)} events.")

# if __name__ == "__main__":
#     generate_events()