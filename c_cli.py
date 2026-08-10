import argparse
from b_report import dwell_time_information, dataframe
from database_upgraded import load_database, write_to_database
from e_algorithmns import adjacency_list, bfs
from a_models import Session

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
    write_to_database(args)
    dwell_time_information(args)
    dataframe() 
    bfs(adjacency_list(Session(load_database())), "Adidas", 1)

    