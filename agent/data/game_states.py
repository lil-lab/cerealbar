"""Saves all states for a particular game: hexes and static objects, and state deltas."""

from dataclasses import dataclass
from typing import List, Tuple

from agent.environment import state_delta
from agent.environment import environment_objects
from agent.environment import position
from agent.environment import terrain


@dataclass
class GameStates:
    """ Saves the environment information from an entire game, including hex, object info and state changes"""
    hexes: List[Tuple[terrain.Terrain, position.Position]]
    objects: List[environment_objects.EnvironmentObject]
    state_deltas: List[state_delta.StateDelta]
