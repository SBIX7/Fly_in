"""Main entry point for the Fly-in drone simulation project."""

from models import Graph
from parsing import Parser
import argparse
import sys

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="To support options")
    arg_parser.add_argument(
        "--map",
        type=str,
        nargs="?",
        help="Add path to map",
        default="./maps/map.txt",
    )
    args = arg_parser.parse_args()
    parser = Parser(args.map)

    # Protect the entire execution block to handle raised exception gracefully
    try:
        parser.parse()
        data = parser.data_parsed
        graph = Graph(data)
        graph.fill_zones(parser.connections)
        graph.run_simulation()
    except Exception as e:
        print(e)
        sys.exit(2)
