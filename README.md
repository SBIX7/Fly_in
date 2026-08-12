*This project has been created as part of the 42 curriculum by msbii.*

# Fly-in: Autonomous Drone Routing System

## Description
Fly-in is an advanced algorithmic simulation project focused on optimizing the routing of a fleet of autonomous drones through a complex network of zones. The primary objective is to navigate multiple drones from a central starting hub to a target destination in the absolute minimum number of simulation turns, while strictly adhering to movement constraints, zone capacities, and connection limits.

The project features a highly robust custom parser, an optimized pathfinding engine capable of solving extreme bottlenecks, and a dynamic visual representation system. It has been heavily benchmarked and successfully beats the reference records on the hardest maps, including completing the "Challenger: The Impossible Dream" map (25 drones) in just 43 turns (reference record: 45 turns).

## Technical Choices & Implementation Strategy
To achieve maximum throughput and avoid deadlocks, the core routing logic avoids naive pathfinding (which would cause traffic jams) and instead relies on a **Time-State Breadth-First Search (BFS)** combined with a **Turn-by-Turn Reservation Agenda**.

**Key algorithmic strategies implemented:**
* **Graph Traversal & Pathfinding:** A customized BFS algorithm computes the shortest paths while considering the specific movement cost of each zone type (`normal` = 1 turn, `restricted` = 2 turns, `priority` = 1 turn with precedence). 
* **State & Capacity Tracking:** Instead of just finding a path, the algorithm dynamically checks the availability of a zone or a connection at a specific future turn `T`. 
* **Conflict Resolution:** If a drone attempts to enter a zone that is at maximum capacity (defined by `max_drones`), or use a connection that has reached its `max_link_capacity`, the algorithm forces strategic waiting or reroutes the drone to an alternative path.
* **Multi-turn Movements:** The engine explicitly tracks drones in transit on connections toward `restricted` zones, ensuring they arrive exactly after the required number of turns without illegally waiting in the transition space.

## Visual Representation
To enhance the user experience and make debugging intuitive, a custom **ANSI Color Rendering Engine** was built directly into the terminal output. 
* **Dynamic Feedback:** Zones are visually color-coded based on their parsed metadata.
* **Readability:** Colors were mathematically adjusted (e.g., brightening pure blue or replacing absolute black with gray) to ensure maximum contrast and readability on dark terminal backgrounds.
* **The "Rainbow" Effect:** A custom text-formatting loop was implemented for the `rainbow` color attribute, applying a sequential, letter-by-letter color shift. This not only fulfills the visual representation requirement but drastically improves the simulation's aesthetics, making the final delivery of drones visually rewarding.

## Instructions

### Prerequisites
* Python 3.10 or later.
* A standard terminal supporting ANSI escape codes.

### Setup and Execution
The project includes a `Makefile` to automate common tasks:

1. **Install dependencies** (MyPy, Flake8):
   ```bash
   make install
   ```
2. **Run the simulation** (uses the default `./map.txt`):
   ```bash
   make run
   ```
3. **Run a specific map** (using the Python script directly):
   ```bash
   python main.py ./maps/challenger/01_the_impossible_dream.txt
   ```
4. **Run strict linting** (to verify absolute type-safety):
   ```bash
   make lint-strict
   ```
5. **Clean cache files**:
   ```bash
   make clean
   ```

## Resources
* Python official documentation for `typing`, `re` (Regular Expressions), and `argparse`.
* PEP 8 Style Guide and PEP 257 for Docstrings conventions.
* **AI Usage Disclosure:** Artificial Intelligence (Google Gemini) was used during the development of this project as an interactive peer-assistant. It was specifically utilized to:
  1. Brainstorm and stress-test edge cases in the Regex patterns used by the file parser to ensure no garbage data could silently corrupt the graph.
  2. Optimize the RGB-to-ANSI color conversion logic for the visual representation engine.
  3. Act as a sounding board to strictly verify MyPy type-hinting compliance across complex data structures like nested `TypedDict`. 
  All core algorithmic logic and architectural choices were independently engineered and fully understood before implementation.