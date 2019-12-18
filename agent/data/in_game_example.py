"""Keeps minimally-required information for running inference on an example (starting in a potentially incorrect
state.)"""

from __future__ import annotations

import numpy as np

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.data import partial_observation
    from agent.environment import card
    from agent.environment import environment_objects
    from agent.environment import position
    from agent.environment import state_delta
    from agent.environment import terrain

    from typing import List, Tuple


class InGameExample:
    def __init__(self,
                 initial_state: state_delta.StateDelta,
                 hex_info: List[Tuple[terrain.Terrain, position.Position]],
                 object_info: List[environment_objects.EnvironmentObject],
                 current_instruction: List[str],
                 initial_partial_observation: partial_observation.PartialObservation = None,
                 goal_cards: List[card.Card] = None):
        self._initial_state: state_delta.StateDelta = initial_state
        self._hex_info: List[Tuple[terrain.Terrain, position.Position]] = hex_info
        self._object_info: List[environment_objects.EnvironmentObject] = object_info
        self._current_instruction: List[str] = current_instruction

        self._static_indices: np.array = None
        self._partial_observation: partial_observation = initial_partial_observation

        self._goal_cards: List[card.Card] = goal_cards

    def get_touched_cards(self) -> List[card.Card]:
        # ONLY Should be used for bookkeeping/logging.
        return self._goal_cards

    def get_first_partial_observation(self) -> partial_observation.PartialObservation:
        return self._partial_observation

    def get_initial_state(self) -> state_delta.StateDelta:
        return self._initial_state

    def get_instruction(self) -> List[str]:
        return self._current_instruction

    def get_state_deltas(self) -> List[state_delta.StateDelta]:
        return [self._initial_state]

    def get_initial_cards(self) -> List[card.Card]:
        return self.get_initial_state().cards

    def get_static_indices(self, state_representation) -> np.array:
        if self._static_indices is None:
            self._static_indices = state_representation.static_indices(self)
        return self._static_indices

    def get_hexes(self) -> List[Tuple[terrain.Terrain, position.Position]]:
        return self._hex_info

    def get_objects(self) -> List[environment_objects.EnvironmentObject]:
        return self._object_info
