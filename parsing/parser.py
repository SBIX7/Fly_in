from typing import Match, TypedDict
import re

# import pprint


class DataError(Exception):
    pass


class MetaHub(TypedDict):
    color: str | None
    zone: str
    max_drones: int


class HubData(TypedDict):
    x: int
    y: int
    metadata: MetaHub


class ConnectionCapcity(TypedDict):
    max_link_capacity: int


class DataType(TypedDict):
    nb_drones: int
    start_hub: str | None
    end_hub: str | None
    hubs: dict[str, HubData]
    connections: dict[tuple[str, str], ConnectionCapcity]


class Parser:
    def __init__(self, config_file_path: str):
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
        self, meta_data: str | None
    ) -> MetaHub:
        meta_hub_param: set[str] = {"zone", "color", "max_drones"}
        ret_dict: MetaHub = {"zone": "normal", "color": None, "max_drones": 1}
        if meta_data is None:
            return ret_dict
        match: list[tuple[str, str]] = re.findall(
            r"(\w+)\s?=\s?(\w+)", meta_data
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
                        if max_drone < 0:
                            raise ValueError
                    except ValueError:
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "Invalid meta data. Max drone must be "
                            "positive integer.",
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
                meta_hub_param.discard(param)
                if param == "color":
                    ret_dict["color"] = value
                elif param == "zone":
                    ret_dict["zone"] = value
                elif param == "max_drones":
                    ret_dict["max_drones"] = max_drone
        return ret_dict

    def _connection_validator(self, match_objet: Match[str]):
        if match_objet is None:
            raise DataError(
                f"[Parse Error] line {self.line_number}:",
                "Invalid connection format. "
                "Expected <hub_a>-<hub_b> [metadata].",
            )
        hub_a: str = match_objet.group(1)
        hub_b: str = match_objet.group(2)
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
            match = re.search(
                r"\s?max_link_capacity\s?=\s?(-?\d+)", match_objet.group(3)
            )
            if match is None:
                raise DataError(
                    f"[Parse Error] line {self.line_number}:",
                    "Invalid connection meta_data. "
                    "Must be max_link_capacity=x (x is a positive integer).",
                )
            link_cap = int(match.group(1))
            if link_cap < 0:
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
    ):
        if match_objet is None:
            raise DataError(
                f"[Parse Error] line {self.line_number}:",
                "Invalid hub format. Expected <name> <x> <y> [metadata].",
            )
        name = match_objet.group(1)
        x = int(match_objet.group(2))
        y = int(match_objet.group(3))
        # if x < 0 or y < 0:
        #     raise DataError(
        #         f"[Parse Error] line {self.line_number}:",
        #         "Invalid coordinates for hub. Expected (x,y) in N*N",
        #     )
        if (
            (name in self.data_parsed["hubs"])
            or (name is self.data_parsed["start_hub"])
            or (name is self.data_parsed["end_hub"])
        ):
            raise DataError(
                f"[Parse Error] line {self.line_number}:",
                f"Invalid name for hub. {name} already exist",
            )
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
        meta_data = self._valid_meta_hub_(match_objet.group(4))
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
        match = re.search(r"nb_drones\s*:\s*(-?\d+)(?:(.*))?", string)
        return match

    def _parse_start_hub(self, string: str) -> Match[str] | None:
        match = re.search(
            r"start_hub\s*:\s*([^\s-]+)\s+(-?\d+)\s+(-?\d+)\s*(?:\[(.*)\])?$",
            string,
        )
        return match

    def _parse_end_hub(self, string: str) -> Match[str] | None:
        match = re.match(
            r"end_hub\s*:\s*([^\s-]+)\s+(-?\d+)\s+(-?\d+)\s*(?:\[(.*)\])?$",
            string,
        )
        return match

    def _parse_hub(self, string: str) -> Match[str] | None:
        match = re.match(
            r"hub\s*:\s*([^\s-]+)\s+(-?\d+)\s+(-?\d+)\s*(?:\[(.*)\])?$",
            string,
        )
        return match

    def _parse_connection(self, string: str) -> Match[str] | None:
        match = re.search(
            r"connection\s*:\s*([^\s-]+)\s*-\s*([^\s-]+)\s*(?:\[(.*)\])?$",
            string,
        )
        return match

    def parse(self):
        with open(self.config_file_path) as f:
            for line in f:
                self.line_number += 1
                line = line.strip()
                if line.startswith("#") or line == "":
                    continue
                # Extracting number of drones
                if line.startswith("nb_drones"):
                    match = self._parse_drone_number(line)
                    if match.group(2):
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "Extra inputs are not permitted",
                        )
                    self.data_parsed["nb_drones"] = int(match.group(1))
                    if self.data_parsed["nb_drones"] < 0:
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "Negative numbers are not permitted",
                        )
                # Extracting start_hub
                elif line.startswith("start_hub"):
                    match = self._parse_start_hub(line)
                    if self.data_parsed["start_hub"] is not None:
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "Start hub is already initialized",
                        )
                    self._hub_validator(match, "start_hub")
                # Extracting end_hub
                elif line.startswith("end_hub"):
                    match = self._parse_end_hub(line)
                    if self.data_parsed["end_hub"] is not None:
                        raise DataError(
                            f"[Parse Error] line {self.line_number}:",
                            "End hub is already initialized",
                        )
                    self._hub_validator(match, "end_hub")
                # Extracting hub
                elif line.startswith("hub"):
                    match = self._parse_hub(line)
                    self._hub_validator(match, None)
                # Extracting connection
                elif line.startswith("connection"):
                    match = self._parse_connection(line)
                    self._connection_validator(match)
                else:
                    raise DataError(
                        f"[Parse Error] line {self.line_number}:",
                        "Data is not valid or not accomplished",
                    )


# def testing_the_parser():
#     parser = Parser("./config.txt")
#     parser.parse()
#     pprint.pprint(parser.data_parsed, indent=2)


# if __name__ == "__main__":
#     testing_the_parser()
