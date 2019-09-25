""" Classes for structures in the environment.

Constants:
    LAMPPOST_ROTATION (int): The expected rotation for the lamppost structure.

Classes:
    Windmill (RotatableObject): A windmill structure.
    Tower (RotatableObject): A tower structure.
    Tent (RotatableObject): A tent structure.
    Lamppost (EnvironmentObject): A lamppost.
"""
from agent.environment import environment_objects
from agent.environment import position
from agent.environment import rotation

LAMPPOST_ROTATION: int = 0


class Windmill(environment_objects.RotatableObject):
    """ A windmill object. """

    def __init__(self,
                 object_position: position.Position,
                 object_rotation: rotation.Rotation):
        super(Windmill, self).__init__(object_position, object_rotation, environment_objects.ObjectType.WINDMILL)

    def __str__(self) -> str:
        return super(Windmill, self).__str__()


class Tower(environment_objects.RotatableObject):
    """ A tower object. """

    def __init__(self,
                 object_position: position.Position,
                 object_rotation: rotation.Rotation):
        super(Tower, self).__init__(object_position, object_rotation, environment_objects.ObjectType.TOWER)

    def __str__(self) -> str:
        return super(Tower, self).__str__()


class Tent(environment_objects.RotatableObject):
    """ A tent object. """

    def __init__(self,
                 object_position: position.Position,
                 object_rotation: rotation.Rotation):
        super(Tent, self).__init__(object_position, object_rotation, environment_objects.ObjectType.TENT)

    def __str__(self):
        return super(Tent, self).__str__()


class Lamppost(environment_objects.EnvironmentObject):
    """ A lamppost object (does not have multiple object_rotations). """

    def __init__(self,
                 object_position: position.Position,
                 rot_degree: int):
        super(Lamppost, self).__init__(object_position, environment_objects.ObjectType.LAMPPOST)

        if not rot_degree == LAMPPOST_ROTATION:
            raise ValueError('Expected lamppost to have object_rotation of ' + str(LAMPPOST_ROTATION)
                             + '; got' + str(rot_degree))

    def __str__(self) -> str:
        return super(Lamppost, self).__str__()

