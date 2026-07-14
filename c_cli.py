import argparse
from b_report import low_confidence, dwell_time_information, dataframe

def inputs():
    parser = argparse.ArgumentParser(description="Generate events and analyse dwell time by brand.")
    parser.add_argument("events_file", help = "Path to the events JSON file.")
    parser.add_argument("--top", type=int, default=3, help="Number of top brands to display.")

    args = parser.parse_args()
    print(args.events_file)
    print(args.top)
    return args

if __name__ == "__main__":
    args = inputs()
    low_confidence()
    dwell_time_information(args)
    dataframe()
    