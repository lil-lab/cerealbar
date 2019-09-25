"""A position in the map.

Classes:
    Position (dataclass): Defines x and y coordinates.

Functions:
    v3_pos_to_position: Converts from a position given from Unity to a position in the game map.
    get_neighbors: Gets the neighboring positions to a position.
"""

from dataclasses import dataclass
from typing import Tuple, List, Any


@dataclass
class Position:
    """ Defines an (x,y) hex coordinate.

    Members:
        x (int): The x coordinate.
        y (int): The y coordinate.
    """
    x: int
    y: int

    def __hash__(self):
        return (self.x, self.y).__hash__()

    def __lt__(self, other):
        return self.x + self.y < other.x + other.y


def v3_pos_to_position(v3_rep: Tuple[Any], hex_width: float, hex_depth: float) -> Position:
    """ Maps from the Unity-given tuple representing the position to a Position.

    Inputs:
        v3_rep (Tuple[str]): The Unity representation of the position (x, y, z).
        hex_width (float): The width of a hex in the Unity game.
        hex_depth (float): The depth of a hex in the Unity game.

    Returns:
        The corresponding position.
    """
    pos: Tuple[str] = v3_rep
    column: int = round(float(pos[0]) / hex_width)
    row: int = int(float(pos[2]) / hex_depth)

    return Position(column, row)


def get_neighbors(position: Position, env_width: int, env_depth: int) -> List[Position]:
    """Gets the neighbors for a position.

    Inputs:
        position (Position): The position to get a neighbor for.
        env_width (int): The width of the environment in hexes.
        env_depth (int): The depth of the environment in hexes.

    Returns:
        A list of neighboring positions.
    """
    x_pos: int = position.x
    y_pos: int = position.y

    if y_pos % 2 == 0:
        neighbors: List[Position] = [Position(x_pos - 1, y_pos + 1),
                                     Position(x_pos, y_pos + 1),
                                     Position(x_pos + 1, y_pos),
                                     Position(x_pos, y_pos - 1),
                                     Position(x_pos - 1, y_pos - 1),
                                     Position(x_pos - 1, y_pos)]
    else:
        neighbors: List[Position] = [Position(x_pos, y_pos + 1),
                                     Position(x_pos + 1, y_pos + 1),
                                     Position(x_pos + 1, y_pos),
                                     Position(x_pos + 1, y_pos - 1),
                                     Position(x_pos, y_pos - 1),
                                     Position(x_pos - 1, y_pos)]

    neighbors = [neighbor for neighbor in neighbors if 0 <= neighbor.x < env_width and 0 <= neighbor.y < env_depth]

    return neighbors
