from __future__ import annotations

import copy

from agent.environment import card
from agent.simulation import game
from agent.simulation import planner
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.config import game_args
    from agent.data import gameplay_action
    from agent.environment import agent
    from agent.environment import agent_actions
    from agent.environment import environment_objects
    from agent.environment import position
    from agent.environment import state_delta
    from agent.environment import terrain
    from typing import List, Tuple


class PythonGame(game.Game):
    def __init__(self,
                 args: game_args.GameArgs,
                 hexes: List[Tuple[terrain.Terrain, position.Position]],
                 env_objects: List[environment_objects.EnvironmentObject],
                 initial_state_delta: state_delta.StateDelta,
                 leader_actions: List[List[gameplay_action.GameplayAction]] = None,
                 expected_sets: List[Tuple[List[card.Card], List[card.Card]]] = None,
                 auto_end_turn: bool = True,
                 verbose: bool = False,
                 check_valid_state: bool = True):
        super(PythonGame, self).__init__(args, leader_actions, expected_sets, auto_end_turn, verbose, check_valid_state)

        self._hexes: List[Tuple[terrain.Terrain, position.Position]] = hexes
        self._objects: List[environment_objects.EnvironmentObject] = env_objects
        self._set_obstacles()
        self._current_state_delta: state_delta.StateDelta = copy.deepcopy(initial_state_delta)
        self._score: int = 0

        self._selected_cards: List[card.Card] = []
        for current_card in self._current_state_delta.cards:
            if current_card.get_selection() != card.CardSelection.UNSELECTED:
                self._selected_cards.append(current_card)

        if self._leader_actions:
            self._execute_leader_actions()

    def _execute_follower(self, action: agent_actions.AgentAction):
        raise NotImplementedError

    def _execute_leader(self, action: agent_actions.AgentAction):
        leader: agent.Agent = self._current_state_delta.leader
        new_position, new_rotation = planner.get_new_player_orientation(leader, action, self._obstacle_positions)

        # Set the follower's state
        self._current_state_delta.leader = agent.Agent(environment_objects.ObjectType.LEADER, new_position,
                                                       new_rotation)

        if action in {agent_actions.AgentAction.MB, agent_actions.AgentAction.MF}:
            self._update_cards_with_step(new_position)

    def send_command(self, command: str):
        raise NotImplementedError

    def _add_cards(self, new_cards: List[card.Card]):
        raise NotImplementedError

    def get_score(self) -> int:
        raise NotImplementedError

    def get_game_info(self, force_update: bool = False) -> state_delta.StateDelta:
        return self._current_state_delta

    def get_most_recent_game_info(self,
                                  prev_state_delta: state_delta.StateDelta,
                                  action: agent_actions.AgentAction,
                                  character: environment_objects.ObjectType,
                                  need_new_set_cards: bool = False) -> state_delta.StateDelta:
        raise NotImplementedError
