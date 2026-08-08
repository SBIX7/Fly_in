from .connection import Connection


class Zone:
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        color: str | None,
        zone_type: str,
        max_drones: int,
    ):
        self.name = name
        self.x = x
        self.y = y
        self.color = color
        self.zone_type = zone_type
        self.max_drones = max_drones
        self.connections: dict[str, Connection] = {}
