from .connection import Connection


class Zone:
    """Represents a location in the network with specific capacities."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        color: str | None,
        zone_type: str,
        max_drones: int,
    ):
        """
        Initializes a new Zone instance.

        Args:
            name: The unique identifier of the zone.
            x: The x-coordinate on the map.
            y: The y-coordinate on the map.
            color: The visual color representation, or None.
            zone_type: The type of zone (normal, restricted, priority,
                blocked).
            max_drones: Maximum number of drones allowed simultaneously
                in this zone.
        """
        self.name = name
        self.x = x
        self.y = y
        self.color = color
        self.zone_type = zone_type
        self.max_drones = max_drones
        # Dictionary to store connected zones and their corresponding
        # connection objects
        self.connections: dict[str, Connection] = {}
