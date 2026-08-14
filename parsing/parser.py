"""Parser module for reading and validating map configuration files."""

from typing import Match, TypedDict
import re


class DataError(Exception):
    """Custom exception for parsing errors."""

    pass


class MetaHub(TypedDict):
    """Type definition for hub metadata."""

    color: str | None
    zone: str
    max_drones: int


class HubData(TypedDict):
    """Type definition for hub coordinates and metadata."""

    x: int
    y: int
    metadata: MetaHub


class ConnectionCapcity(TypedDict):
    """Type definition for connection capacity."""

    max_link_capacity: int


class DataType(TypedDict):
    """Type definition for the completely parsed data structure."""

    nb_drones: int
    start_hub: str | None
    end_hub: str | None
    hubs: dict[str, HubData]
    connections: dict[tuple[str, str], ConnectionCapcity]


class Parser:
    """Parses the map configuration file and validates its contents."""

    def __init__(self, config_file_path: str):
        """Initializes the parser with the given file path."""
        self.config_file_path = config_file_path
        self.data_parsed: DataType = {
            "nb_drones": -1,
            "start_hub": None,
            "end_hub": None,
            "hubs": {},
            "connections": {},
        }
        self.line_number: int = 0
        self.connections: set[tuple[str, str]] = set()

    def _valid_meta_hub_(
        self, meta_data: str | None, hub_type: str | None = None
    ) -> MetaHub:
        """Validates and extracts hub metadata."""
        meta_hub_param: set[str] = {"zone", "color", "max_drones"}
        ret_dict: MetaHub = {"zone": "normal", "color": None, "max_drones": 1}

        # Return default metadata if nothing is provided
        if meta_data is None:
            return ret_dict

        # Check for garbage data to avoid silent bugs
        cleaned_meta = re.sub(
            r"\w+\s*=\s*[a-zA-Z0-9_-]+", "", meta_data
        ).strip()

        if cleaned_meta != "":
            raise DataError(
                f"[Parse Error] line {self.line_number}:",
                f"Invalid syntax or garbage in metadata: '{cleaned_meta}'",
            )

        # We use \s* to handle multiple spaces safely
        match: list[tuple[str, str]] = re.findall(
            r"(\w+)\s*=\s*([a-zA-Z0-9_-]+)", meta_data
        )

        if match != []:
            for param, value in match:
                param = param.lower()
                value = value.lower()

                if param not in meta_hub_param:
                    raise DataError(
                        f"[Parse Error] line {self.line_number}:",
                        f"Invalid meta data. {param} not valid or duplicated.",
                    )

                if param == "max_drones":
                    try:
                        max_drone = int(value)
                        # Allow zero or negative capacity for start/end hubs
                        if max_drone <= 0 and hub_type not in (
                            "start_hub",
                            "end_hub",
                        ):
                            raise ValueError
                    except ValueError:
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "Invalid meta data. Max drone must be in N*.",
                        )

                if param == "zone":
                    if value not in (
                        "normal",
                        "blocked",
                        "restricted",
                        "priority",
                    ):
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "Invalid meta data. Zone can be 'normal',"
                            " 'blocked', 'restricted', or 'priority'.",
                        )

                # Remove the parameter from the set to avoid duplicates
                meta_hub_param.discard(param)

                if param == "color":
                    ret_dict["color"] = value
                elif param == "zone":
                    ret_dict["zone"] = value
                elif param == "max_drones":
                    ret_dict["max_drones"] = max_drone

        return ret_dict

    def _connection_validator(self, match_objet: Match[str]) -> None:
        """Validates a parsed connection and updates the data structure."""
        if match_objet is None:
            raise DataError(
                f"[Parse Error] line {self.line_number}:",
                "Invalid connection format. "
                "Expected <hub_a>-<hub_b> [metadata].",
            )

        hub_a: str = match_objet.group(1)
        hub_b: str = match_objet.group(2)

        # Prevent a zone from connecting to itself
        if hub_a == hub_b:
            raise DataError(
                f"[Parse Error] line {self.line_number}:",
                f"Invalid connection. Self connection ({hub_a}-{hub_b}).",
            )

        # Both hubs must exist before creating a connection
        if hub_a not in self.data_parsed["hubs"]:
            raise DataError(
                f"[Parse Error] line {self.line_number}:",
                f"Invalid connection. '{hub_a}' doesn't exist.",
            )

        if hub_b not in self.data_parsed["hubs"]:
            raise DataError(
                f"[Parse Error] line {self.line_number}:",
                f"Invalid connection. '{hub_b}' doesn't exist.",
            )

        # Sort the hubs to easily find duplicate connections
        connection_list = [hub_a, hub_b]
        connection_list.sort()
        connection = (connection_list[0], connection_list[1])

        if connection in self.connections:
            raise DataError(
                f"[Parse Error] line {self.line_number}:",
                f"Invalid connection. {connection} already defined",
            )

        self.connections.add(connection)

        link_cap = 1
        if match_objet.group(3) is not None:
            # We use \s* here too to be safe with spaces
            cleaned_meta = re.sub(
                r"\s*max_link_capacity\s*=\s*(-?\d+)", "", match_objet.group(3)
            ).strip()
            if cleaned_meta != "":
                raise DataError(
                    f"[Parse Error] line {self.line_number}:",
                    "Invalid syntax/garbage in connection metadata: "
                    f"'{cleaned_meta}'",
                )
            match = re.search(
                r"\s*max_link_capacity\s*=\s*(-?\d+)", match_objet.group(3)
            )
            if match is None:
                raise DataError(
                    f"[Parse Error] line {self.line_number}:",
                    "Invalid connection meta_data. "
                    "Must be max_link_capacity=x (x is a positive integer).",
                )
            link_cap = int(match.group(1))
            # Capacity must be strictly positive
            if link_cap <= 0:
                raise DataError(
                    f"[Parse Error] line {self.line_number}:",
                    "Invalid connection meta_data. "
                    "Must be max_link_capacity=x (x is a positive integer).",
                )

        self.data_parsed["connections"][connection] = {
            "max_link_capacity": link_cap
        }

    def _hub_validator(
        self, match_objet: Match[str], hub_type: str | None = None
    ) -> None:
        """Validates a parsed hub and updates the data structure."""
        if match_objet is None:
            raise DataError(
                f"[Parse Error] line {self.line_number}:",
                "Invalid hub format. Expected <name> <x> <y> [metadata].",
            )

        name = match_objet.group(1)
        x = int(match_objet.group(2))
        y = int(match_objet.group(3))

        # Check if the name is already taken
        if (
            (name in self.data_parsed["hubs"])
            or (name is self.data_parsed["start_hub"])
            or (name is self.data_parsed["end_hub"])
        ):
            raise DataError(
                f"[Parse Error] line {self.line_number}:",
                f"Invalid name for hub. {name} already exist",
            )

        # Check for coordinate overlaps with existing hubs
        for _, data in self.data_parsed["hubs"].items():
            if (x == data["x"]) and (y == data["y"]):
                raise DataError(
                    f"[Parse Error] line {self.line_number}:",
                    "Invalid coordinates for hub. Overlap",
                )

        if self.data_parsed["start_hub"] is not None:
            start_hub = self.data_parsed["hubs"].get(
                self.data_parsed["start_hub"]
            )
            if start_hub is not None:
                start_x = start_hub.get("x")
                start_y = start_hub.get("y")
                if x == start_x and y == start_y:
                    raise DataError(
                        f"[Parse Error] line {self.line_number}:",
                        "Invalid coordinates for hub. Overlap",
                    )

        if self.data_parsed["end_hub"] is not None:
            end_hub = self.data_parsed["hubs"].get(self.data_parsed["end_hub"])
            if end_hub is not None:
                end_x = end_hub.get("x")
                end_y = end_hub.get("y")
                if x == end_x and y == end_y:
                    raise DataError(
                        f"[Parse Error] line {self.line_number}:",
                        "Invalid coordinates for hub. Overlap",
                    )

        meta_data = self._valid_meta_hub_(match_objet.group(4), hub_type)

        # Assign the hub to the right category
        if hub_type == "start_hub":
            self.data_parsed["start_hub"] = name
            self.data_parsed["hubs"][name] = {
                "x": x,
                "y": y,
                "metadata": meta_data,
            }
        elif hub_type == "end_hub":
            self.data_parsed["end_hub"] = name
            self.data_parsed["hubs"][name] = {
                "x": x,
                "y": y,
                "metadata": meta_data,
            }
        elif hub_type is None:
            self.data_parsed["hubs"][name] = {
                "x": x,
                "y": y,
                "metadata": meta_data,
            }

    def _parse_drone_number(self, string: str) -> Match[str] | None:
        """Parses the line containing the number of drones."""
        match = re.search(r"nb_drones\s*:\s*(-?\d+)(?:(.*))?", string)
        return match

    def _parse_start_hub(self, string: str) -> Match[str] | None:
        """Parses the line defining the start hub."""
        match = re.search(
            r"start_hub\s*:\s*([^\s-]+)\s+(-?\d+)\s+(-?\d+)\s*(?:\[(.*)\])?$",
            string,
        )
        return match

    def _parse_end_hub(self, string: str) -> Match[str] | None:
        """Parses the line defining the end hub."""
        match = re.match(
            r"end_hub\s*:\s*([^\s-]+)\s+(-?\d+)\s+(-?\d+)\s*(?:\[(.*)\])?$",
            string,
        )
        return match

    def _parse_hub(self, string: str) -> Match[str] | None:
        """Parses a standard hub line."""
        match = re.match(
            r"hub\s*:\s*([^\s-]+)\s+(-?\d+)\s+(-?\d+)\s*(?:\[(.*)\])?$",
            string,
        )
        return match

    def _parse_connection(self, string: str) -> Match[str] | None:
        """Parses a connection line."""
        match = re.search(
            r"connection\s*:\s*([^\s-]+)\s*-\s*([^\s-]+)\s*(?:\[(.*)\])?$",
            string,
        )
        return match

    def parse(self) -> None:
        """Reads the config file line by line and parses its contents."""
        first_valid_line_parsed = False
        with open(self.config_file_path) as f:
            for line in f:
                self.line_number += 1
                line = line.strip()

                # Ignore empty lines and comments
                if line.startswith("#") or line == "":
                    continue

                # Ignore inline comments
                if "#" in line:
                    line = line.split("#")[0].strip()
                    if line == "":
                        continue

                # Enforce that nb_drones is the very first configuration line
                if not first_valid_line_parsed:
                    if not line.startswith("nb_drones"):
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "The first valid line must define nb_drones.",
                        )
                    first_valid_line_parsed = True
                else:
                    if line.startswith("nb_drones"):
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "nb_drones is already defined.",
                        )

                # Extracting number of drones
                if line.startswith("nb_drones"):
                    match = self._parse_drone_number(line)
                    if match is None:
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "Syntax error or invalid format.",
                        )
                    if match.group(2):
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "Extra inputs are not permitted",
                        )
                    self.data_parsed["nb_drones"] = int(match.group(1))
                    if self.data_parsed["nb_drones"] <= 0:
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "Negative/Null numbers are not permitted",
                        )

                # Extracting start_hub
                elif line.startswith("start_hub"):
                    match = self._parse_start_hub(line)
                    if match is None:
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "Syntax error or invalid format.",
                        )
                    if self.data_parsed["start_hub"] is not None:
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "Start hub is already initialized",
                        )
                    self._hub_validator(match, "start_hub")

                # Extracting end_hub
                elif line.startswith("end_hub"):
                    match = self._parse_end_hub(line)
                    if match is None:
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "Syntax error or invalid format.",
                        )
                    if self.data_parsed["end_hub"] is not None:
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "End hub is already initialized",
                        )
                    self._hub_validator(match, "end_hub")

                # Extracting hub
                elif line.startswith("hub"):
                    match = self._parse_hub(line)
                    if match is None:
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "Syntax error or invalid format.",
                        )
                    self._hub_validator(match, None)

                # Extracting connection
                elif line.startswith("connection"):
                    match = self._parse_connection(line)
                    if match is None:
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "Syntax error or invalid format.",
                        )
                    self._connection_validator(match)
                else:
                    raise DataError(
                        f"[Parse Error] line {self.line_number}:",
                        "Data is not valid or not accomplished",
                    )

        # Final integrity checks after the whole file is read
        if self.data_parsed["nb_drones"] <= 0:
            raise DataError(
                "[Parse Error]",
                "Missing or invalid nb_drones definition.",
            )
        if self.data_parsed["start_hub"] is None:
            raise DataError(
                "[Parse Error]",
                "Missing exactly one start_hub definition.",
            )
        if self.data_parsed["end_hub"] is None:
            raise DataError(
                "[Parse Error]",
                "Missing exactly one end_hub definition.",
            )
