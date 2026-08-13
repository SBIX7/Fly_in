class Connection:
    """Represents a bidirectional link between two zones."""

    def __init__(self, zone_a: str, zone_b: str, max_capacity: int):
        """
        Initializes a new Connection instance.

        Args:
            zone_a: The name of the first connected zone.
            zone_b: The name of the second connected zone.
            max_capacity: The maximum number of drones that can traverse
                this connection simultaneously.
        """
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_capacity = max_capacity
