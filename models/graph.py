from models import Zone
from parsing import DataType
from models import Connection
from models import Drone
from collections import deque


class Graph:
    def __init__(self, map_data: DataType):
        self.zones: dict[str, Zone] = {}
        self.nb_drone: int = map_data["nb_drones"]
        self.map_data = map_data
        self.start_hub: Zone
        self.end_hub: Zone
        self.drones: dict[str, Drone] = {}
        self.agenda: dict[int, dict[str, int]] = {}

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
            self.drones[f"{i+1}"] = Drone(f"{i+1}", self.start_hub)

    def _get_neighbors(self, hub: Zone) -> list[Zone]:
        neighbors: list[Zone] = []
        for hub_name, _ in hub.connections.items():
            neighbors.append(self.zones[hub_name])
        return neighbors

    def _get_connection(self, zone1: Zone, zone2: Zone) -> Connection | None:
        return zone1.connections.get(zone2.name)

    # This private methode will help me fill the agenda to use it in BFS 3D
    def _book_space(self, turn: int, space: Zone | Connection):
        if turn in self.agenda.keys():
            if self.agenda[turn].get(space) is None:
                self.agenda[turn][space] = 1
            else:
                self.agenda[turn][space] += 1
        else:
            self.agenda[turn] = {}
            self.agenda[turn][space] = 1

    # Check in certain turn that a certain place is free or not
    def _is_free(self, turn: int, space: Zone | Connection) -> bool:
        if space in (self.start_hub, self.end_hub):
            return True
        turn_reservations = self.agenda.get(turn, {})
        if isinstance(space, Zone):
            if space.zone_type == "blocked":
                return False
            if turn_reservations.get(space) is not None:
                return turn_reservations[space] < space.max_drones
            else:
                return True
        if turn_reservations.get(space) is not None:
            return turn_reservations[space] < space.max_capacity
        else:
            return True

    def _calculate_path_for_drone(
        self, drone: Drone
    ) -> list[Zone | Connection]:
        queue: deque[tuple[Zone, int, list[Zone]]] = deque()
        visited: set[tuple[Zone, int]] = set()
        # Initializing BFS Data
        queue.append((drone.current_location, 0, [drone.current_location]))
        visited.add((drone.current_location, 0))
        # Looping over space and check over time the path
        while queue:
            zone, turn, path = queue.popleft()
            if path[-1] is self.end_hub:
                # Before return we should update our agenda space over time
                time_line: list[Zone | Connection] = [path[0]]
                clock = 0
                for i in range(len(path) - 1):
                    # Case where drone should wait
                    clock += 1
                    if path[i] == path[i + 1]:
                        self._book_space(clock, path[i])
                        time_line.append(path[i])
                    elif path[i + 1].zone_type in (
                        "normal",
                        "priority",
                    ):
                        connection = self._get_connection(path[i], path[i + 1])
                        self._book_space(clock, path[i + 1])
                        self._book_space(clock, connection)
                        time_line.append(path[i + 1])
                    elif path[i + 1].zone_type == "restricted":
                        clock += 1
                        connection = self._get_connection(path[i], path[i + 1])
                        self._book_space(clock - 1, connection)
                        self._book_space(clock, path[i + 1])
                        self._book_space(clock, connection)
                        time_line.append(connection)
                        time_line.append(path[i + 1])
                return time_line
            # Receive a list of neighbors sorted based on zone priority
            neighbors = sorted(
                self._get_neighbors(zone),
                key=lambda x: x.zone_type == "priority",
                reverse=True,
            )
            # Case where the drone didn't find a valid zone to go in it
            if (zone, turn + 1) not in visited:
                if self._is_free(turn + 1, zone):
                    new_path = path + [zone]
                    queue.append((zone, turn + 1, new_path))
                    visited.add((zone, turn + 1))
            for neighbor in neighbors:
                zone_type = neighbor.zone_type
                connection = self._get_connection(zone, neighbor)
                if zone_type in ("normal", "priority"):
                    if (neighbor, turn + 1) in visited:
                        continue
                    if self._is_free(turn + 1, neighbor) and self._is_free(
                        turn + 1, connection
                    ):
                        neighbor_path = path + [neighbor]
                        queue.append((neighbor, turn + 1, neighbor_path))
                        visited.add((neighbor, turn + 1))
                elif zone_type == "restricted":
                    if (neighbor, turn + 2) in visited:
                        continue
                    if (
                        self._is_free(turn + 1, connection)
                        and self._is_free(turn + 2, connection)
                        and self._is_free(turn + 2, neighbor)
                    ):
                        neighbor_path = path + [neighbor]
                        queue.append((neighbor, turn + 2, neighbor_path))
                        visited.add((neighbor, turn + 2))

    def run_simulation(self):
        self._respawn_drones()
        for _, drone in self.drones.items():
            drone.path = self._calculate_path_for_drone(drone)
        turn = 1

        while not all(
            turn >= len(drone.path) for _, drone in self.drones.items()
        ):
            turn_mvt = []

            for _, drone in self.drones.items():
                if turn < len(drone.path):
                    if drone.path[turn] != drone.path[turn - 1]:
                        if isinstance(drone.path[turn], Zone):
                            destination = drone.path[turn].name
                        else:
                            destination = f"{drone.path[turn].zone_a}-{drone.path[turn].zone_b}"

                        turn_mvt.append(f"D{drone.drone_id}-{destination}")

            if turn_mvt:
                print(" ".join(turn_mvt))

            turn += 1
