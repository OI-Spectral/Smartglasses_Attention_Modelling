import pytest
import z_generator
import random
from datetime import datetime, timedelta

def known_answer_test():
    nike_event_1 = 1
    nike_event_2 = 2
    nike_event_3 = 3

    total_nike_dwell = nike_event_1 + nike_event_2 + nike_event_3
    assert total_nike_dwell == 6, f"Expected total dwell time for Nike events to be 6, but got {total_nike_dwell}"

def test_empty_list():
    session = z_generator.Session([])
    result = session.dwell_time_by_brand()
    assert result == {}, f"Expected empty dictionary for empty list of events, but got {result}"

#def test_brand_missing(): #still need to decide if I want it to crash here
    #event = generator.Event(timestamp: "2026-06-16T12:00:00", confidence: 0.9, dwell_seconds: 5)
    #result = generator.Session.dwell_time_by_brand([event])
    #print(result)
    #assert result == {"": 5}, f"Expected dictionary with empty brand key and dwell time of 5, but got {result}"

def test_zero_dwell_event():
    event = z_generator.Event(timestamp="2026-06-16T12:00:00", brand="Nike", confidence=0.9, dwell_seconds=0)
    session = z_generator.Session([event])
    result = session.dwell_time_by_brand()
    assert result == {"Nike": 0}, f"Expected dictionary with Nike key and dwell time of 0, but got {result}"

@pytest.fixture
def sample_generator():
    random.seed(42)  # same "random" data every run — crucial for testing

    brands = ["Nike", "Adidas", "Coca-Cola", "Apple", "Spotify", "Red Bull"]
    events = []
    t = datetime(2026, 6, 16, 0, 0, 0)

    for _ in range(500):
        t += timedelta(seconds=random.randint(1, 100))
        events.append({
            "timestamp": t.isoformat(),
            "brand": random.choice(brands),
            "confidence": round(random.uniform(0.6, 0.99), 2),
            "dwell_seconds": round(random.uniform(0.5, 6.0), 1),
        })
        
    return events

if __name__ == "__main__":
    known_answer_test()
    test_empty_list()
    test_zero_dwell_event()


    