""" Code related to rotations in the environment.

Classes:
    Rotation (Enum): The possible rotations in the environment.

Methods:
    degree_to_rotation: Maps from an integer to a Rotation.
    rotate_clockwise: Gets the rotation one clockwise (top-down) from a given rotation.
    rotate_counterclockwise: Gets the rotation one counterclockwise (top-down) from a given rotation.
    rotate_with_actions: Returns the new rotation after executing a sequence of actions starting in a given rotation.
"""
import numpy as np

from enum import Enum
from agent.environment import agent_actions
from typing import List


class Rotation(Enum):
    """ Rotations in the environment. """
    NORTHEAST: str = 'NORTHEAST'
    NORTHWEST: str = 'NORTHWEST'
    SOUTHEAST: str = 'SOUTHEAST'
    SOUTHWEST: str = 'SOUTHWEST'
    EAST: str = 'EAST'
    WEST: str = 'WEST'

    def __int__(self) -> int:
        if self == Rotation.NORTHEAST:
            return 30
        elif self == Rotation.EAST:
            return 90
        elif self == Rotation.SOUTHEAST:
            return 150
        elif self == Rotation.SOUTHWEST:
            return 210
        elif self == Rotation.WEST:
            return 270
        elif self == Rotation.NORTHWEST:
            return 330
        else:
            raise ValueError('Could not convert: ' + str(self))

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other) -> bool:
        if self == Rotation.NORTHEAST:
            return False
        elif self == Rotation.EAST and other == Rotation.NORTHEAST:
            return False
        elif self == Rotation.SOUTHEAST and other in {Rotation.NORTHEAST, Rotation.EAST}:
            return False
        elif self == Rotation.SOUTHWEST and other in {Rotation.NORTHEAST, Rotation.EAST, Rotation.SOUTHEAST}:
            return False
        elif self == Rotation.WEST and \
                other in {Rotation.NORTHEAST, Rotation.EAST, Rotation.SOUTHEAST, Rotation.SOUTHWEST}:
            return False
        elif self == Rotation.NORTHWEST and other != Rotation.NORTHWEST:
            return False
        else:
            return True

    def to_radians(self) -> float:
        # First, make it point right
        offset_deg: int = (int(self) - 90 + 360) % 360

        # Then convert to radians
        return np.deg2rad(offset_deg)


def degree_to_rotation(degree: int) -> Rotation:
    """ Maps from an integer degree rotation given by Unity to a Rotation type.

    Input:
        degree (int): An integer degree rotation from Unity.

    Returns:
        The corresponding Rotation.

    Raises:
        ValueError, if the degree integer is not in the range (30 + 60x), where x is an integer in [0, 5].
    """
    if degree == 30:
        return Rotation.NORTHEAST
    elif degree == 90:
        return Rotation.EAST
    elif degree == 150:
        return Rotation.SOUTHEAST
    elif degree == 210:
        return Rotation.SOUTHWEST
    elif degree == 270:
        return Rotation.WEST
    elif degree == 330:
        return Rotation.NORTHWEST
    else:
        raise ValueError('Degree not in 30+60x; ' + str(degree))


def rotate_clockwise(rotation: Rotation) -> Rotation:
    """ Maps from a rotation to the one clockwise from it.

    Input:
        rotation (Rotation): The rotation to rotate.

    Returns:
        The resulting Rotation.

    Raises:
        ValueError, if the input rotation is not recognized.
    """
    if rotation == Rotation.NORTHEAST:
        return Rotation.EAST
    elif rotation == Rotation.EAST:
        return Rotation.SOUTHEAST
    elif rotation == Rotation.SOUTHEAST:
        return Rotation.SOUTHWEST
    elif rotation == Rotation.SOUTHWEST:
        return Rotation.WEST
    elif rotation == Rotation.WEST:
        return Rotation.NORTHWEST
    elif rotation == Rotation.NORTHWEST:
        return Rotation.NORTHEAST
    else:
        raise ValueError('Unrecognized rotation: ' + str(rotation))


def rotate_counterclockwise(rotation: Rotation) -> Rotation:
    """ Maps from a rotation to the one counterclockwise from it.

    Input:
        rotation (Rotation): The rotation to rotate.

    Returns:
        The resulting Rotation.

    Raises:
        ValueError, if the input rotation is not recognized.
    """
    if rotation == Rotation.NORTHEAST:
        return Rotation.NORTHWEST
    elif rotation == Rotation.EAST:
        return Rotation.NORTHEAST
    elif rotation == Rotation.SOUTHEAST:
        return Rotation.EAST
    elif rotation == Rotation.SOUTHWEST:
        return Rotation.SOUTHEAST
    elif rotation == Rotation.WEST:
        return Rotation.SOUTHWEST
    elif rotation == Rotation.NORTHWEST:
        return Rotation.WEST
    else:
        raise ValueError('Unrecognized rotation: ' + str(rotation))


def rotate_with_actions(initial_rotation: Rotation, actions: List[agent_actions.AgentAction]) -> Rotation:
    """ Maps from a rotation to another rotation given a list of actions to execute.

    Inputs:
        initial_rotation (Rotation): The starting rotation.
        actions (List[AgentAction]): The list of actions to execute starting in this rotation.

    Returns:
        The resulting Rotation.
    """
    new_rotation: Rotation = initial_rotation
    for action in actions:
        if action == agent_actions.AgentAction.RR:
            new_rotation = rotate_clockwise(new_rotation)
        elif action == agent_actions.AgentAction.RL:
            new_rotation = rotate_counterclockwise(new_rotation)
    return new_rotation
