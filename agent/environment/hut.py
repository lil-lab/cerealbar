""" Contains the hut environment object.

Classes:
    HutColor (Enum): The possible colors of huts.
    Hut (RotatableObject): The hut class.

Functions:
    get_hut_color: Maps from prop names to hut colors.
"""

from enum import Enum

from agent.environment import environment_objects
from agent.environment import position
from agent.environment import rotation


class HutColor(Enum):
    """ Various possible hut colors. """
    YELLOW: str = 'YELLOW'
    RED: str = 'RED'
    GREEN: str = 'GREEN'
    BLUE: str = 'BLUE'
    BLACK: str = 'BLACK'

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other) -> bool:
        assert isinstance(other, type(self))
        return self.value < other.value


def get_hut_color(prop_name: str) -> HutColor:
    """Returns the HutColor given a prop name.

    Input:
        prop_name: The prop name.

    Returns:
        The corresponding hut color.

    Raises:
        ValueError, if the color is not found.
    """
    color: str = prop_name.split('_')[-1]
    for data in HutColor:
        if data.value == color:
            return data
    raise ValueError('Hut color not found: %r' % prop_name)


class Hut(environment_objects.RotatableObject):
    """ The hut class.

    Members:
        _color (HutColor): The color of the hut.
    """

    def __init__(self,
                 hut_position: position.Position,
                 hut_rotation: rotation.Rotation,
                 color: HutColor):
        super(Hut, self).__init__(hut_position, hut_rotation, environment_objects.ObjectType.HUT)

        self._color: HutColor = color

    def get_color(self) -> HutColor:
        """ Returns the hut's color. """
        return self._color

    def __str__(self) -> str:
        return super(Hut, self).__str__() + '\t' + str(self._color)

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return self._color == other.get_color() and \
                   self._rotation == other.get_rotation() and \
                   self._position == other.get_position()
        return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

