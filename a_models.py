class Event:
        def __init__(self, timestamp, brand, confidence, dwell_seconds):
            self.timestamp = timestamp
            self.brand = brand
            self.confidence = confidence
            self.dwell_seconds = dwell_seconds

        def __repr__(self):
            return f"Event(timestamp={self.timestamp}, brand={self.brand}, confidence={self.confidence}, dwell_seconds={self.dwell_seconds})"
        
        def to_dict(self):
            return {"timestamp": self.timestamp, 
             "brand": self.brand, 
             "confidence": self.confidence, 
             "dwell_seconds": self.dwell_seconds}

class Session:
    def __init__(self, events: list[Event]):
        self.events = events
    
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
