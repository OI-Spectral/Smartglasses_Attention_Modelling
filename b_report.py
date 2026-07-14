import json
import pandas as pd 
import matplotlib.pyplot as plt
from a_models import Event, Session
from c_cli import inputs

def load_events(filetitle):
    try:    
        with open(filetitle, "r") as f:
            events = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {filetitle}")
        events = []
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {filetitle}")
        events = []
    return [Event(event["timestamp"], event["brand"], event["confidence"], event["dwell_seconds"]) for event in events]   

def low_confidence():
    events = load_events(filetitle = "events.json")

    low_confidence_events = [e.to_dict() for e in events if e.confidence < 0.7]
    high_confidence_events = [e.to_dict() for e in events if e.confidence >= 0.7]

    with open("low_confidence.json", "w") as f:
        json.dump(low_confidence_events, f, indent=2)

    with open("high_confidence.json", "w") as f:
        json.dump(high_confidence_events, f, indent=2)

    print(f"Removed {len(low_confidence_events)} low confidence events.")

def dwell_time_information(args):
    session = Session(load_events(filetitle = args.events_file))
    dwell = session.dwell_time_by_brand()
    session.report(dwell)
    session.top_brands(n = args.top)
    session.exposure_per_hour()

def dataframe():
    df = pd.read_json("high_confidence.json")

    grouped = df.groupby("brand")["dwell_seconds"].sum()

    x = grouped.index
    y = grouped.values

    plt.bar(x,y)
    plt.savefig("dwell_time_by_brand.png")

