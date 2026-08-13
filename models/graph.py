from models import Zone
from parsing import DataType
from models import Connection
from models import Drone
from collections import deque
from models.colors import Colors


class Graph:
    """Represents the graph, handling pathfinding and simulation."""

    def __init__(self, map_data: DataType):
        """
        Initializes the Graph instance with parsed map data.

        Args:
            map_data: The parsed configuration data containing hubs,
                connections, and constraints.
        """
        self.zones: dict[str, Zone] = {}
        self.nb_drone: int = map_data["nb_drones"]
        self.map_data = map_data
        self.start_hub: Zone
        self.end_hub: Zone
        self.drones: dict[str, Drone] = {}
        # Dictionary acting as a space-time reservation agenda
        self.agenda: dict[int, dict[Zone | Connection, int]] = {}

    def fill_zones(self, connections: set[tuple[str, str]]) -> None:
        """
        Creates Zone and Connection objects from the parsed data.

        Args:
            connections: A set of tuples representing all valid
                connections between zones.
        """
        # Creating Zones and store them without defining connections yet
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

        # Assign Zone object to start_zone and end_zone
        start_name = self.map_data["start_hub"]
        end_name = self.map_data["end_hub"]
        if start_name and end_name:
            self.start_hub = self.zones[start_name]
            self.end_hub = self.zones[end_name]

    def _respawn_drones(self) -> None:
        """Instantiates all drone objects and places them at the start."""
        for i in range(self.nb_drone):
            self.drones[f"{i+1}"] = Drone(f"{i+1}", self.start_hub)

    def _get_neighbors(self, hub: Zone) -> list[Zone]:
        """
        Retrieves all accessible neighboring zones for a given hub.

        Args:
            hub: The zone from which neighbors are searched.

        Returns:
            A list of neighboring Zone objects.
        """
        neighbors: list[Zone] = []
        for hub_name, _ in hub.connections.items():
            neighbors.append(self.zones[hub_name])
        return neighbors

    def _get_connection(self, z1: Zone, z2: Zone) -> Connection | None:
        """
        Retrieves the connection object between two specific zones.

        Args:
            z1: The starting zone.
            z2: The destination zone.

        Returns:
            The Connection object if it exists, otherwise None.
        """
        return z1.connections.get(z2.name)

    # This private methode will help me fill the agenda to use it in BFS
    def _book_space(self, turn: int, space: Zone | Connection) -> None:
        """
        Reserves a spot in a specific zone or connection at a given turn.

        Args:
            turn: The simulation turn index.
            space: The zone or connection to be reserved.
        """
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
        """
        Checks if a space has available capacity at a specific turn.

        Args:
            turn: The simulation turn index to check.
            space: The zone or connection to evaluate.

        Returns:
            True if there is available space, False otherwise.
        """
        # Evaporation principle at start and end hubs
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

        # Case for Connection capacity check
        if turn_reservations.get(space) is not None:
            return turn_reservations[space] < space.max_capacity
        else:
            return True

    def _calculate_path_for_drone(
        self, drone: Drone
    ) -> list[Zone | Connection]:
        """
        Calculates the optimal space-time path for a drone using BFS.

        Args:
            drone: The drone needing a computed path.

        Returns:
            A list of Zones and Connections representing the planned
            route over time.

        Raises:
            ValueError: If no valid path can be found.
        """
        queue: deque[tuple[Zone, int, list[Zone]]] = deque()
        visited: set[tuple[Zone, int]] = set()

        # Initializing BFS Data
        queue.append((self.start_hub, 0, [self.start_hub]))
        visited.add((self.start_hub, 0))

        # Looping over space and check over time the path
        while queue:
            zone, turn, path = queue.popleft()

            # Goal reached
            if path[-1] is self.end_hub:
                # Update our agenda space over time before returning
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
                        if connection is not None:
                            self._book_space(clock, connection)
                        time_line.append(path[i + 1])
                    elif path[i + 1].zone_type == "restricted":
                        clock += 1
                        connection = self._get_connection(path[i], path[i + 1])
                        if connection is not None:
                            self._book_space(clock - 1, connection)
                            self._book_space(clock, connection)
                            time_line.append(connection)
                        self._book_space(clock, path[i + 1])
                        time_line.append(path[i + 1])
                return time_line

            # Receive a list of neighbors sorted by zone priority
            neighbors = sorted(
                self._get_neighbors(zone),
                key=lambda x: x.zone_type == "priority",
                reverse=True,
            )

            # Case where the drone didn't find a valid zone to go in it
            # (Wait action)
            if (zone, turn + 1) not in visited:
                if self._is_free(turn + 1, zone):
                    new_path = path + [zone]
                    queue.append((zone, turn + 1, new_path))
                    visited.add((zone, turn + 1))

            # Move to neighboring zones
            for neighbor in neighbors:
                zone_type = neighbor.zone_type
                connection = self._get_connection(zone, neighbor)

                if zone_type in ("normal", "priority"):
                    if (neighbor, turn + 1) in visited:
                        continue
                    if (
                        self._is_free(turn + 1, neighbor)
                        and connection is not None
                        and self._is_free(turn + 1, connection)
                    ):
                        neighbor_path = path + [neighbor]
                        queue.append((neighbor, turn + 1, neighbor_path))
                        visited.add((neighbor, turn + 1))
                elif zone_type == "restricted":
                    if (neighbor, turn + 2) in visited:
                        continue
                    if (
                        connection is not None
                        and self._is_free(turn + 1, connection)
                        and self._is_free(turn + 2, connection)
                        and self._is_free(turn + 2, neighbor)
                    ):
                        neighbor_path = path + [neighbor]
                        queue.append((neighbor, turn + 2, neighbor_path))
                        visited.add((neighbor, turn + 2))

        raise ValueError(f"No path found for drone {drone.drone_id}")

    def _is_connected(self) -> bool:
        """
        Verifies if a physical path exists between start_hub and end_hub,
        ignoring time and capacities.

        Returns:
            True if the graph is physically connected, False otherwise.
        """
        # Fail-fast if either start or end is blocked
        if (
            self.start_hub.zone_type == "blocked"
            or self.end_hub.zone_type == "blocked"
        ):
            return False

        queue: deque[Zone] = deque()
        visited: set[Zone] = set()
        queue.append(self.start_hub)
        visited.add(self.start_hub)

        while queue:
            zone = queue.popleft()

            # Goal found
            if zone is self.end_hub:
                return True

            for neighbor in self._get_neighbors(zone):
                # Blocked zones cannot be traversed
                if neighbor.zone_type == "blocked":
                    continue
                if neighbor not in visited:
                    queue.append(neighbor)
                    visited.add(neighbor)

        return False

    def run_simulation(self) -> None:
        """
        Executes the main simulation loop, computing and printing paths.

        Raises:
            ValueError: If the graph is disconnected or blocked.
        """
        self._respawn_drones()
        color = Colors()

        if not self._is_connected():
            raise ValueError(
                "[Graph Error] The graph is disconnected or blocked"
            )

        # Compute optimal routes for all drones
        for _, drone in self.drones.items():
            drone.path = self._calculate_path_for_drone(drone)

        turn = 1

        # Advance turns until all drones reach the goal
        while not all(
            turn >= len(drone.path) for _, drone in self.drones.items()
        ):
            turn_mvt = []

            for _, drone in self.drones.items():
                if turn < len(drone.path):
                    # Record output only if the drone moved
                    if drone.path[turn] != drone.path[turn - 1]:
                        current_space = drone.path[turn]
                        if isinstance(current_space, Zone):
                            zone_color = current_space.color
                            destination = color.coloring_text(
                                current_space.name, zone_color
                            )
                        else:
                            destination = f"{current_space.zone_a}-"
                            destination += f"{current_space.zone_b}"

                        turn_mvt.append(f"D{drone.drone_id}-{destination}")
                    # Track current location for internal states
                    drone.current_location = drone.path[turn]

            # Display movements for the current turn if any occurred
            if turn_mvt:
                print(" ".join(turn_mvt))

            turn += 1
