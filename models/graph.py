from models import Zone
from parsing import DataType
from models import Connection
from models import Drone


class Graph:
    def __init__(self, map_data: DataType):
        self.zones: dict[str, Zone] = {}
        self.nb_drone: int = map_data["nb_drones"]
        self.map_data = map_data
        self.start_hub: Zone
        self.end_hub: Zone
        self.drones: dict[str, Drone] = {}

    def fill_zones(self, connections: set[tuple[str, str]]):
        # Creating Zones and store them in zones without defining connections
        for hub, hub_data in self.map_data["hubs"].items():
            name = hub
            x = hub_data["x"]
            y = hub_data["y"]
            color = hub_data["metadata"]["color"]
            zone_type = hub_data["metadata"]["zone"]
            max_drones = hub_data["metadata"]["max_drones"]
            self.zones[name] = Zone(name, x, y, color, zone_type, max_drones)
        # Assigning same connection object to connected self.zones
        for connection in connections:
            hub_a, hub_b = connection
            max_link_cap = self.map_data["connections"][connection][
                "max_link_capacity"
            ]
            connection_object = Connection(hub_a, hub_b, max_link_cap)
            self.zones[hub_a].connections[hub_b] = connection_object
            self.zones[hub_b].connections[hub_a] = connection_object
        # Assigne Zone object to start_zone and end_zone
        start_name = self.map_data["start_hub"]
        end_name = self.map_data["end_hub"]
        if start_name and end_name:
            self.start_hub = self.zones[start_name]
            self.end_hub = self.zones[end_name]

    def _respawn_drones(self):
        for i in range(self.nb_drone):
            self.drones[f"D{i+1}"] = Drone(f"D{i+1}", self.start_hub)

    def run_simulation(self):
        self._respawn_drones()
        # for drone, _ in self.drones.items():
        #     print(drone)
