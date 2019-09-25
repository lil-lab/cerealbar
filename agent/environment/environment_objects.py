""" Contains definitions for objects in the environment.

Classes:
    ObjectType (Enum): Different types that objects can have.
    EnvironmentObject (ABC): Abstract class for a generic object environment.
    RotatableObject (EnvironmentObject): Abstract class for an object that has a rotation property.
"""
from abc import ABC
from enum import Enum
from typing import Optional

from agent.environment import position
from agent.environment import rotation


class ObjectType(Enum):
    """ Various types of objects in the environments. """
    CARD: str = 'CARD'
    TREE: str = 'TREE'
    HUT: str = 'HUT'
    LEADER: str = 'LEADER'
    FOLLOWER: str = 'FOLLOWER'
    WINDMILL: str = 'WINDMILL'
    TOWER: str = 'TOWER'
    PLANT: str = 'PLANT'
    LAMPPOST: str = 'STREET_LAMP'
    TENT: str = 'HOUSE_LVL1'

    def __str__(self) -> str:
        return self.value


class EnvironmentObject(ABC):
    """ A generic environment object type.

    Members:
        _position (Position): The position of the object.
        _type (ObjectType): The type of object.
    """

    def __init__(self, object_position: Optional[position.Position], object_type: ObjectType):
        self._position: Optional[position.Position] = object_position
        self._type: ObjectType = object_type

    def get_type(self) -> ObjectType:
        """ Returns the type of the object. """
        return self._type

    def get_position(self) -> position.Position:
        """ Returns the position of the object. """
        return self._position

    def __eq__(self, other) -> bool:
        """ Compares two objects in the environment by checking the classes, types, and positions. """
        if isinstance(other, self.__class__):
            return self._type == other.get_type() and self._position == other.get_position()
        else:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __str__(self):
        return str(self._type) + '\t' + str(self._position)


class RotatableObject(EnvironmentObject, ABC):
    """ An environment object that has a rotation property. Inherits from EnvironmentObject/

    Members:
        _rotation (Rotation): The rotation of the object.
    """

    def __init__(self, object_position: Optional[position.Position], object_rotation: Optional[rotation.Rotation],
                 object_type: ObjectType):
        super(RotatableObject, self).__init__(object_position, object_type)
        self._rotation: Optional[rotation.Rotation] = object_rotation

    def get_rotation(self) -> rotation.Rotation:
        """ Returns the rotation of the object. """
        return self._rotation

    def __eq__(self, other) -> bool:
        """ Equality operator also checks the rotation for the other object. """
        if isinstance(other, self.__class__):
            return self._position == other.get_position() and self._rotation == other.get_rotation()
        return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __str__(self):
        return super(RotatableObject, self).__str__() + '\t' + str(self._rotation)
