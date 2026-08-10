import json

class Event:
        def __init__(self, session_id, timestamp, brand, confidence, dwell_seconds):
            self.session_id = session_id
            self.timestamp = timestamp
            self.brand = brand
            self.confidence = confidence
            self.dwell_seconds = dwell_seconds

        def __repr__(self):
            return f"Event(session_id={self.session_id}, timestamp={self.timestamp}, brand={self.brand}, confidence={self.confidence}, dwell_seconds={self.dwell_seconds})"

        def to_dict(self):
            return {"session_id": self.session_id,
             "timestamp": self.timestamp,
             "brand": self.brand,
             "confidence": self.confidence,
             "dwell_seconds": self.dwell_seconds}

        def is_low_confidence(self, threshold = 0.7):
            return self.confidence < threshold
        
class Session:
    def __init__(self, events: list[Event]):
        self.events = events

    def confidence_filter(self):
        low_confidence_events = [e.to_dict() for e in self.events if e.is_low_confidence()]
        high_confidence_events = [e.to_dict() for e in self.events if not e.is_low_confidence()]

        with open("low_confidence.json", "w") as f:
            json.dump(low_confidence_events, f, indent=2)
       
        with open("high_confidence.json", "w") as f:
            json.dump(high_confidence_events, f, indent=2)
       
        print(f"Removed {len(low_confidence_events)} low confidence events.")

        return [Event(event["session_id"], event["timestamp"], event["brand"], event["confidence"], event["dwell_seconds"]) for event in high_confidence_events]

    def dwell_time_by_brand(self):
        dwell = {}
        for event in self.events:
            brand = event.brand
            dwell[brand] = dwell.get(brand,0) + event.dwell_seconds
        return dwell
        
    def report(self, dwell):
        with open("report.txt", "w") as f:
            for brand, total_dwell in dwell.items():
                f.write(f"{brand} dwell time: {total_dwell:.1f} seconds.\n")
        for brand, total_dwell in dwell.items():
            print(f"{brand} dwell time: {total_dwell:.1f} seconds.")

    def exposure_per_hour(self):
        exposure = {}
        for event in self.events:
            hour = event.timestamp[:13]
            seconds = event.dwell_seconds
            exposure[hour] = exposure.get(hour, 0) + seconds

        for hour, count in exposure.items():
            print(f"{hour}:00 - {count:.1f} dwell_seconds.")

    def top_brands(self, n):
        brand_seconds = {}
        for event in self.events:
            brand = event.brand
            brand_seconds[brand] = brand_seconds.get(brand, 0) + event.dwell_seconds  
        sorted_brands = sorted(brand_seconds.items(), key=lambda x: x[1], reverse=True)
        top_n_brands = [x[0] for x in sorted_brands[:n]]
        print(f"Top {n} brands by dwell time are {top_n_brands}")

    def heapq_top_brands(self, n):
        import heapq
        brand_seconds = {}
        for event in self.events:
            brand = event.brand
            brand_seconds[brand] = brand_seconds.get(brand, 0) + event.dwell_seconds
        top_n_brands = heapq.nlargest(n, brand_seconds.items(), key = lambda x: x[1])
        print(f"Top {n} brands in dwell time are {[x[0] for x in top_n_brands]}")
