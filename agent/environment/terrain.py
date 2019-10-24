""" Contains the terrain class and functions.

Constants:
    TERRAIN_DEPTHS (Dict[Terrain, float]): Maps from terrains to the expected depth in the environment.
    OBSTACLE_TERRAINS (Set[Terrain]): The terrains considered obstacles to the agents.

Classes:
    Terrain (Enum): Different environment terrains.

Methods:
    cell_name_to_terrain: Returns a Terrain given a raw string value and the depth of a hex.
"""
from enum import Enum
from typing import Dict, Set


class Terrain(Enum):
    """ Terrains in the environment.

    Grass: green hexes.
    Path: brown/tan hexes.
    Water: blue hexes; lower than grass and path.
    Deep water: Deeper water.
    Hill: white hexes; higher than grass and path.
    Short hill: A short mountain.
    """
    GRASS: str = 'GRASS'
    PATH: str = 'PATH'
    WATER: str = 'WATER'
    DEEP_WATER: str = 'DEEP_WATER'
    HILL: str = 'HILL'
    SHORT_HILL: str = 'SHORT_HILL'
    UNOBSERVABLE: str = 'UNOBSERVABLE'

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other) -> bool:
        return self.value < other.value


TERRAIN_DEPTHS: Dict[Terrain, float] = {Terrain.GRASS: 0.,
                                        Terrain.PATH: 0.,
                                        Terrain.WATER: -5.,
                                        Terrain.DEEP_WATER: -10.,
                                        Terrain.HILL: 20.,
                                        Terrain.SHORT_HILL: 15.}

OBSTACLE_TERRAINS: Set[Terrain] = {Terrain.WATER, Terrain.HILL, Terrain.SHORT_HILL, Terrain.DEEP_WATER}


def cell_name_to_terrain(name: str, depth: float) -> Terrain:
    """ Maps from a cell name to a terrain.

    Inputs:
        name (str): The cell/prop name.
        depth (float): The integer value of the depth of the terrain.

    Returns:
        The corresponding terrain.

    Raises:
        ValueError, if no terrain name is found in the prop name or if the depth of the hex was not expected for the
            terrain.
    """
    for data in Terrain:
        if str(data).lower() in name.lower():
            if data == Terrain.HILL:
                if depth == TERRAIN_DEPTHS[data]:
                    return data
                elif depth == TERRAIN_DEPTHS[Terrain.SHORT_HILL]:
                    return Terrain.SHORT_HILL
            elif data == Terrain.WATER:
                if depth == TERRAIN_DEPTHS[data]:
                    return data
                elif depth == TERRAIN_DEPTHS[Terrain.DEEP_WATER]:
                    return Terrain.DEEP_WATER
            else:
                expected_depth: float = TERRAIN_DEPTHS[data]
                if depth != expected_depth:
                    raise ValueError("Terrain was " + str(data) + " but depth was not expected; " +
                                     "expected " + str(expected_depth) + " but got " + str(depth))

                return data
    raise ValueError('Terrain name not recognized: ' + str(name))
