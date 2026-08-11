from .zone import Zone
from .connection import Connection


class Drone:
    def __init__(self, drone_id: str, current_location: Zone | Connection):
        self.drone_id: str = drone_id
        self.current_location: Zone | Connection = current_location
        self.path: list[Zone | Connection] = []
        self.transit_time: int = 0
