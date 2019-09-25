"""Defines the kinds of plants in the environment.

Classes:
    PlantType(Enum): Different kinds of plants.
    Plant(EnvironmentObject): A plant object.
"""
from enum import Enum

from agent.environment import environment_objects
from agent.environment import position


class PlantType(Enum):
    BUSH: str = 'BUSH'  # Short green bush.
    YELLOW_BUSH: str = 'BUSH_YW'  # Short yellowish-gold bush.

    GRASS: str = 'GRASS'  # Tall green grass.

    RED_FLOWER: str = 'FLOW_RD'  # Bright pink/red flower with distinct petals.
    PURPLE_FLOWER: str = 'FLOW_PRP'  # Short flower with big green leaves and light purple petals inside.
    BLUE_FLOWER: str = 'FLOW_BL'  # Small, short flower with petals larger than the leaves. Petals are purple.

    def __str__(self):
        return self.value

    def __lt__(self, other) -> bool:
        return self.value < other.value


class Plant(environment_objects.EnvironmentObject):
    def __init__(self,
                 plant_position: position.Position,
                 rot_degree: int,
                 plant_type: PlantType):
        super(Plant, self).__init__(plant_position, environment_objects.ObjectType.PLANT)

        if not rot_degree == 0:
            raise ValueError('Expected a plant to be rotated with 0 degrees, but got %r' % rot_degree)

        self.plant_type = plant_type

    def get_plant_type(self) -> PlantType:
        return self.plant_type

    def __str__(self):
        return super(Plant, self).__str__() + '\t' + str(self.plant_type)

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return super(Plant, self).__eq__(other) and self.plant_type == other.get_plant_type()
        return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

