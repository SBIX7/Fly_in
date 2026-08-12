import random


class Colors:
    def __init__(self) -> None:
        self.colors: dict[
            str, tuple[int, int, int] | list[tuple[int, int, int]]
        ] = {
            "green": (46, 204, 113),
            "red": (255, 69, 0),
            "blue": (100, 149, 237),
            "orange": (255, 165, 0),
            "yellow": (255, 255, 0),
            "cyan": (0, 255, 255),
            "purple": (170, 100, 255),
            "brown": (205, 133, 63),
            "gold": (255, 215, 0),
            "lime": (50, 205, 50),
            "magenta": (255, 0, 255),
            "black": (128, 128, 128),
            "maroon": (176, 48, 96),
            "darkred": (178, 34, 34),
            "violet": (238, 130, 238),
            "crimson": (220, 20, 60),
            "rainbow": [
                (255, 69, 0),
                (255, 165, 0),
                (255, 255, 0),
                (46, 204, 113),
                (100, 149, 237),
                (138, 43, 226),
                (238, 130, 238),
            ],
        }

    def coloring_text(self, text: str, color: str | None) -> str:
        """Return text colored with ANSI escape codes.
        Returns standard text if color is None or unknown.
        """
        if not color:
            return text

        rgb_color = self.colors.get(color.lower())

        if rgb_color is None:
            return text

        if isinstance(rgb_color, list):
            colored_text = ""
            for char in text:
                r, g, b = random.choice(rgb_color)
                colored_text += f"\033[38;2;{r};{g};{b}m{char}\033[0m"
            return colored_text
        else:
            r, g, b = rgb_color

        return f"\033[38;2;{r};{g};{b}m{text}\033[0m"
