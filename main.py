from models import Graph
from parsing import Parser

# def get_hub_info(hub_name: str, )

if __name__ == "__main__":
    try:
        parser = Parser("./config.txt")
    except Exception:
        pass
    parser.parse()
    data = parser.data_parsed
    graph = Graph(data)
    graph.fill_zones(parser.connections)
    graph.run_simulation()
    # print(graph.start_hub)
    # print(graph.end_hub)
    # for name, info in graph.zones.items():
    #     print(name)
    #     print(f"{info.name}- {info.connections.keys()}\n\n")
