from .zone import Zone
from .connection import Connection


class Drone:
    """Represents a drone navigating through the network."""

    def __init__(self, drone_id: str, current_location: Zone | Connection):
        """
        Initializes a new Drone instance.

        Args:
            drone_id: The unique identifier for the drone.
            current_location: The starting zone or connection of the drone.
        """
        self.drone_id: str = drone_id
        self.current_location: Zone | Connection = current_location
        # Initialize an empty path for the drone
        self.path: list[Zone | Connection] = []
